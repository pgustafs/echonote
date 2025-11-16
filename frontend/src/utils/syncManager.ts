/**
 * Sync Manager for handling offline/online state and background sync
 */

import { transcribeAudio } from '../api';
import {
  deletePendingRecording,
  updateRecordingStatus,
  getPendingCount,
  updateRecordingError,
  getFirstPendingRecording,
} from './indexedDB';

export type SyncStatus = 'idle' | 'syncing' | 'offline';

export class SyncManager {
  private listeners: Set<(status: SyncStatus, count: number) => void> = new Set();
  private syncStatus: SyncStatus = 'idle';
  private syncInProgress = false;
  private registration: ServiceWorkerRegistration | null = null;

  constructor() {
    // Listen for online/offline events
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());

    // Listen for page visibility changes to handle mobile devices coming back online
    document.addEventListener('visibilitychange', () => this.handleVisibilityChange());

    // Set initial status
    this.syncStatus = navigator.onLine ? 'idle' : 'offline';

    // Listen for messages from service worker
    navigator.serviceWorker?.addEventListener('message', (event) => {
      if (event.data.type === 'GET_TOKEN') {
        // Send token back to service worker
        const token = localStorage.getItem('echonote_token');
        event.ports[0].postMessage(token);
      }
    });
  }

  /**
   * Set service worker registration for background sync
   */
  setRegistration(registration: ServiceWorkerRegistration) {
    this.registration = registration;
  }

  /**
   * Check if device is online
   */
  isOnline(): boolean {
    return navigator.onLine;
  }

  /**
   * Get current sync status
   */
  getStatus(): SyncStatus {
    return this.syncStatus;
  }

  /**
   * Subscribe to sync status changes
   */
  subscribe(callback: (status: SyncStatus, count: number) => void): () => void {
    this.listeners.add(callback);

    // Send initial status
    this.notifyListeners();

    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Notify all listeners of status change
   */
  private async notifyListeners() {
    const count = await getPendingCount();
    this.listeners.forEach((callback) => {
      callback(this.syncStatus, count);
    });
  }

  /**
   * Handle device coming online
   */
  private async handleOnline() {
    console.log('[SyncManager] Device is online');
    this.syncStatus = 'idle';
    await this.notifyListeners();

    // Trigger sync
    await this.syncPendingRecordings();
  }

  /**
   * Handle device going offline
   */
  private async handleOffline() {
    console.log('[SyncManager] Device is offline');
    this.syncStatus = 'offline';
    await this.notifyListeners();
  }

  /**
   * Handle page visibility change, especially for mobile devices
   * When app is brought to foreground, check for connectivity and sync if needed
   */
  private handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      console.log('[SyncManager] App became visible, checking network status.');
      if (this.isOnline()) {
        console.log('[SyncManager] App is online, triggering sync on visibility change.');
        // Treat as an online event to ensure status is updated and sync is triggered
        this.handleOnline();
      }
    }
  }

  /**
   * Manually trigger sync of pending recordings.
   * This function processes one recording at a time to prevent a single
   * corrupted blob from crashing the entire sync process.
   * Failed recordings are marked as 'failed' and skipped on subsequent syncs.
   */
  async syncPendingRecordings(): Promise<void> {
    console.log('[SyncManager] Attempting to sync pending recordings...');
    if (this.syncInProgress) {
      console.log('[SyncManager] Sync already in progress, aborting.');
      return;
    }

    if (!navigator.onLine) {
      console.log('[SyncManager] Device is offline, skipping sync.');
      this.handleOffline();
      return;
    }

    this.syncInProgress = true;
    this.syncStatus = 'syncing';
    await this.notifyListeners();

    let syncedCount = 0;
    let failedCount = 0;

    // Process recordings one by one in a loop
    while (true) {
      if (!navigator.onLine) {
        console.log('[SyncManager] Went offline during sync, stopping.');
        this.handleOffline();
        break;
      }

      let recording;
      try {
        // Fetch the next pending recording from the queue (status = 'pending')
        // This will skip any 'failed' or 'syncing' recordings
        recording = await getFirstPendingRecording();

        // If no more pending recordings, break the loop
        if (!recording) {
          console.log(`[SyncManager] No more pending recordings. Synced: ${syncedCount}, Failed: ${failedCount}`);
          break;
        }

        console.log(`[SyncManager] Processing recording ID ${recording.id} (${recording.filename})`);

        // Validate blob before attempting upload
        if (!recording.blob || recording.blob.size === 0) {
          console.error(`[SyncManager] Recording ID ${recording.id} has empty or missing blob - deleting corrupted recording`);
          await deletePendingRecording(recording.id!);
          failedCount++;
          console.warn(`[SyncManager] ✗ Deleted corrupted recording ID ${recording.id} (${failedCount} failed total)`);
          continue; // Skip to next recording
        }

        // Try to read the blob to ensure it's not corrupted
        try {
          await recording.blob.arrayBuffer();
        } catch (blobError) {
          console.error(`[SyncManager] Recording ID ${recording.id} has corrupted blob - deleting`, blobError);
          await deletePendingRecording(recording.id!);
          failedCount++;
          console.warn(`[SyncManager] ✗ Deleted corrupted recording ID ${recording.id} (${failedCount} failed total)`);
          continue; // Skip to next recording
        }

        // Try to update status - if blob is corrupted, this might fail
        try {
          await updateRecordingStatus(recording.id!, 'syncing');
        } catch (statusError) {
          console.error(`[SyncManager] Failed to update status for recording ID ${recording.id} - blob may be corrupted, deleting`, statusError);
          await deletePendingRecording(recording.id!);
          failedCount++;
          console.warn(`[SyncManager] ✗ Deleted corrupted recording ID ${recording.id} (${failedCount} failed total)`);
          continue; // Skip to next recording
        }

        // Upload the recording
        await transcribeAudio(
          recording.blob,
          recording.filename,
          recording.url,
          recording.model,
          recording.enableDiarization,
          recording.numSpeakers
        );

        // If successful, delete from the queue
        await deletePendingRecording(recording.id!);
        syncedCount++;
        console.log(`[SyncManager] ✓ Successfully synced recording ID ${recording.id} (${syncedCount} synced total)`);

      } catch (error) {
        failedCount++;
        console.error(`[SyncManager] ✗ Failed to sync recording ID ${recording?.id}:`, error);

        if (recording && recording.id) {
          // If any error occurs (Network, Blob, Unknown), mark the recording as permanently failed
          // This prevents a corrupted recording from blocking the queue forever
          // Next sync will skip this recording and process the next pending one
          const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred.';
          await updateRecordingError(
            recording.id,
            `Sync failed: ${errorMessage}`
          );
          console.warn(`[SyncManager] Marked recording ${recording.id} as 'failed' - will be skipped on next sync`);
        } else {
          // If the error happened before we could even get a recording, stop the sync
          console.error('[SyncManager] Error fetching a recording from the database, stopping sync.');
          break;
        }
      } finally {
        // Notify listeners after each attempt to keep the UI count updated
        await this.notifyListeners();
      }
    }

    // Once the loop is finished, reset the status
    this.syncStatus = 'idle';
    this.syncInProgress = false;
    await this.notifyListeners();
    console.log(`[SyncManager] Sync completed. Total synced: ${syncedCount}, Total failed: ${failedCount}`);
  }

  /**
   * Register for background sync (if supported)
   */
  async registerBackgroundSync(): Promise<void> {
    if (!this.registration || !('sync' in this.registration)) {
      console.log('[SyncManager] Background sync not supported');
      return;
    }

    try {
      // Type assertion for BackgroundSync API
      await (this.registration as any).sync.register('sync-recordings');
      console.log('[SyncManager] Registered background sync');
    } catch (error) {
      console.error('[SyncManager] Failed to register background sync:', error);
    }
  }
}

// Create singleton instance
export const syncManager = new SyncManager();
