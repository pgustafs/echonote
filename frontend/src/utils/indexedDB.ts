/**
 * IndexedDB utilities for offline recording storage
 */

const DB_NAME = 'echonote-db';
const DB_VERSION = 1;
const STORE_NAME = 'pendingRecordings';

export interface PendingRecording {
  id?: number;
  blob: Blob;
  filename: string;
  url?: string;
  model?: string;
  enableDiarization?: boolean;
  numSpeakers?: number;
  timestamp: number;
  status: 'pending' | 'syncing' | 'failed';
}

/**
 * Open IndexedDB connection
 */
export function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      console.error('IndexedDB error:', request.error);
      reject(request.error);
    };

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      // Create object store for pending recordings
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, {
          keyPath: 'id',
          autoIncrement: true,
        });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('status', 'status', { unique: false });
        console.log('Created IndexedDB object store:', STORE_NAME);
      }
    };
  });
}

/**
 * Save recording to IndexedDB for later sync
 */
export async function savePendingRecording(
  recording: Omit<PendingRecording, 'id' | 'timestamp' | 'status'>
): Promise<number> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);

    const recordingWithMeta: Omit<PendingRecording, 'id'> = {
      ...recording,
      timestamp: Date.now(),
      status: 'pending',
    };

    const request = store.add(recordingWithMeta);

    request.onsuccess = () => {
      console.log('Saved pending recording with ID:', request.result);
      resolve(request.result as number);
    };

    request.onerror = () => {
      console.error('Failed to save pending recording:', request.error);
      reject(request.error);
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Get all pending recordings
 */
export async function getPendingRecordings(): Promise<PendingRecording[]> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      console.error('Failed to get pending recordings:', request.error);
      reject(request.error);
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Get count of pending recordings
 */
export async function getPendingCount(): Promise<number> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.count();

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      console.error('Failed to count pending recordings:', request.error);
      reject(request.error);
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Update recording status
 */
export async function updateRecordingStatus(
  id: number,
  status: PendingRecording['status']
): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const getRequest = store.get(id);

    getRequest.onsuccess = () => {
      const recording = getRequest.result;
      if (recording) {
        recording.status = status;
        const updateRequest = store.put(recording);

        updateRequest.onsuccess = () => {
          resolve();
        };

        updateRequest.onerror = () => {
          reject(updateRequest.error);
        };
      } else {
        reject(new Error('Recording not found'));
      }
    };

    getRequest.onerror = () => {
      reject(getRequest.error);
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Delete recording from IndexedDB
 */
export async function deletePendingRecording(id: number): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.delete(id);

    request.onsuccess = () => {
      console.log('Deleted pending recording:', id);
      resolve();
    };

    request.onerror = () => {
      console.error('Failed to delete pending recording:', request.error);
      reject(request.error);
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Clear all pending recordings
 */
export async function clearPendingRecordings(): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.clear();

    request.onsuccess = () => {
      console.log('Cleared all pending recordings');
      resolve();
    };

    request.onerror = () => {
      console.error('Failed to clear pending recordings:', request.error);
      reject(request.error);
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}
