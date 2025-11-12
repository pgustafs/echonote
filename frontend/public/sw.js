/**
 * EchoNote Service Worker
 * Provides offline caching, background sync, and PWA functionality
 */

const CACHE_NAME = 'echonote-v1';
const RUNTIME_CACHE = 'echonote-runtime';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/config.js',
  '/econote_logo.png',
  '/manifest.json'
];

/**
 * Install event - cache core assets
 */
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Precaching app shell');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE;
            })
            .map((cacheName) => {
              console.log('[ServiceWorker] Removing old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

/**
 * Fetch event - serve from cache, fallback to network
 * Network-first strategy for API calls, cache-first for assets
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // API requests - network first with offline fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone the response before caching
          const responseToCache = response.clone();

          caches.open(RUNTIME_CACHE)
            .then((cache) => {
              cache.put(request, responseToCache);
            });

          return response;
        })
        .catch(() => {
          // Try to serve from cache if network fails
          return caches.match(request)
            .then((cachedResponse) => {
              if (cachedResponse) {
                return cachedResponse;
              }
              // Return offline response for transcription endpoints
              if (url.pathname === '/api/models') {
                return new Response(
                  JSON.stringify({ models: [], default: '' }),
                  {
                    headers: { 'Content-Type': 'application/json' },
                    status: 200
                  }
                );
              }
              throw new Error('Offline and no cached data');
            });
        })
    );
    return;
  }

  // Static assets - cache first
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type === 'error') {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            caches.open(RUNTIME_CACHE)
              .then((cache) => {
                cache.put(request, responseToCache);
              });

            return response;
          });
      })
  );
});

/**
 * Background Sync event - sync pending recordings
 */
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync event:', event.tag);

  if (event.tag === 'sync-recordings') {
    event.waitUntil(syncRecordings());
  }
});

/**
 * Sync pending recordings to backend
 */
async function syncRecordings() {
  try {
    // Get pending recordings from IndexedDB
    const db = await openDB();
    const tx = db.transaction('pendingRecordings', 'readonly');
    const store = tx.objectStore('pendingRecordings');
    const recordings = await getAll(store);

    console.log('[ServiceWorker] Found recordings to sync:', recordings.length);

    for (const recording of recordings) {
      try {
        // Upload recording
        const formData = new FormData();
        formData.append('file', recording.blob, recording.filename);
        if (recording.url) formData.append('url', recording.url);
        if (recording.model) formData.append('model', recording.model);
        if (recording.enableDiarization) formData.append('enable_diarization', 'true');
        if (recording.numSpeakers) formData.append('num_speakers', recording.numSpeakers.toString());

        const token = await getAuthToken();
        const response = await fetch('/api/transcribe', {
          method: 'POST',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          body: formData
        });

        if (response.ok) {
          // Remove from pending queue
          const deleteTx = db.transaction('pendingRecordings', 'readwrite');
          const deleteStore = deleteTx.objectStore('pendingRecordings');
          await deleteRecord(deleteStore, recording.id);
          console.log('[ServiceWorker] Synced recording:', recording.id);
        }
      } catch (error) {
        console.error('[ServiceWorker] Failed to sync recording:', error);
      }
    }
  } catch (error) {
    console.error('[ServiceWorker] Sync error:', error);
    throw error; // Retry sync
  }
}

/**
 * Helper: Open IndexedDB
 */
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('echonote-db', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pendingRecordings')) {
        db.createObjectStore('pendingRecordings', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

/**
 * Helper: Get all records from object store
 */
function getAll(store) {
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Helper: Delete record from object store
 */
function deleteRecord(store, id) {
  return new Promise((resolve, reject) => {
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

/**
 * Helper: Get auth token from clients
 */
async function getAuthToken() {
  const clients = await self.clients.matchAll();
  if (clients.length > 0) {
    // Try to get token from localStorage via message
    return new Promise((resolve) => {
      const messageChannel = new MessageChannel();
      messageChannel.port1.onmessage = (event) => {
        resolve(event.data);
      };
      clients[0].postMessage({ type: 'GET_TOKEN' }, [messageChannel.port2]);

      // Timeout after 1 second
      setTimeout(() => resolve(null), 1000);
    });
  }
  return null;
}
