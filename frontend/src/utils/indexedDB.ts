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
  errorMessage?: string;
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
 * Validate that a Blob is not empty or corrupted
 */
async function validateBlob(blob: Blob): Promise<boolean> {
  // Check size
  if (blob.size === 0) {
    console.error('[IndexedDB] Blob validation failed: size is 0');
    return false;
  }

  // Try to read the blob to ensure it's not corrupted
  try {
    const arrayBuffer = await blob.arrayBuffer();
    if (arrayBuffer.byteLength === 0) {
      console.error('[IndexedDB] Blob validation failed: arrayBuffer is empty');
      return false;
    }
    console.log(`[IndexedDB] Blob validation passed: ${blob.size} bytes`);
    return true;
  } catch (error) {
    console.error('[IndexedDB] Blob validation failed: error reading blob', error);
    return false;
  }
}

/**
 * Save recording to IndexedDB for later sync
 */
export async function savePendingRecording(
  recording: Omit<PendingRecording, 'id' | 'timestamp' | 'status'>
): Promise<number> {
  // Validate blob before saving
  const isValid = await validateBlob(recording.blob);
  if (!isValid) {
    throw new Error('Cannot save recording: audio blob is empty or corrupted');
  }

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
      console.log(`[IndexedDB] Successfully saved recording. Assigned ID: ${request.result}`);
      resolve(request.result as number);
    };

    request.onerror = () => {
      console.error('[IndexedDB] Error saving recording:', {
        error: request.error,
        recording: {
          filename: recordingWithMeta.filename,
          size: recordingWithMeta.blob.size,
          type: recordingWithMeta.blob.type,
        }
      });
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
 * Get the first (oldest) pending recording from the queue
 * Only returns recordings with status 'pending' - skips 'failed' and 'syncing' recordings
 */
export async function getFirstPendingRecording(): Promise<PendingRecording | undefined> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index('timestamp'); // Use timestamp index to get the oldest
    const request = index.openCursor();

    request.onsuccess = () => {
      const cursor = request.result;
      if (cursor) {
        const recording = cursor.value;
        // Only return recordings with 'pending' status
        // Skip 'failed' and 'syncing' recordings to prevent blocking the queue
        if (recording.status === 'pending') {
          resolve(recording);
        } else {
          // Move to next recording
          cursor.continue();
        }
      } else {
        // No pending recordings found
        resolve(undefined);
      }
    };

    request.onerror = () => {
      console.error('Failed to get first pending recording:', request.error);
      reject(request.error);
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Get count of pending recordings (only status 'pending', excludes 'failed')
 */
export async function getPendingCount(): Promise<number> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = () => {
      // Count only recordings with 'pending' status
      const pendingRecordings = request.result.filter(r => r.status === 'pending');
      resolve(pendingRecordings.length);
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
 * Update recording status and error message
 */
export async function updateRecordingError(
  id: number,
  errorMessage: string
): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const getRequest = store.get(id);

    getRequest.onsuccess = () => {
      const recording = getRequest.result;
      if (recording) {
        recording.status = 'failed';
        recording.errorMessage = errorMessage;
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

/**
 * Get all failed recordings
 */
export async function getFailedRecordings(): Promise<PendingRecording[]> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = () => {
      const failedRecordings = request.result.filter(r => r.status === 'failed');
      resolve(failedRecordings);
    };

    request.onerror = () => {
      console.error('Failed to get failed recordings:', request.error);
      reject(request.error);
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Retry a failed recording by setting its status back to 'pending'
 */
export async function retryFailedRecording(id: number): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const getRequest = store.get(id);

    getRequest.onsuccess = () => {
      const recording = getRequest.result;
      if (recording) {
        recording.status = 'pending';
        recording.errorMessage = undefined; // Clear error message
        const updateRequest = store.put(recording);

        updateRequest.onsuccess = () => {
          console.log('[IndexedDB] Retrying failed recording:', id);
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
