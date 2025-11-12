/**
 * Sync Manager for handling offline/online state and background sync
 */

import { transcribeAudio } from '../api';
import {
  getPendingRecordings,
  deletePendingRecording,
  updateRecordingStatus,
  getPendingCount,
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
   * Manually trigger sync of pending recordings
   */
  async syncPendingRecordings(): Promise<void> {
    if (this.syncInProgress) {
      console.log('[SyncManager] Sync already in progress');
      return;
    }

    if (!navigator.onLine) {
      console.log('[SyncManager] Device is offline, skipping sync');
      return;
    }

    this.syncInProgress = true;
    this.syncStatus = 'syncing';
    await this.notifyListeners();

    try {
      const recordings = await getPendingRecordings();
      console.log('[SyncManager] Syncing', recordings.length, 'pending recordings');

      for (const recording of recordings) {
        try {
          // Update status to syncing
          if (recording.id) {
            await updateRecordingStatus(recording.id, 'syncing');
          }

          // Upload recording
          await transcribeAudio(
            recording.blob,
            recording.filename,
            recording.url,
            recording.model,
            recording.enableDiarization,
            recording.numSpeakers
          );

          // Delete from pending queue
          if (recording.id) {
            await deletePendingRecording(recording.id);
          }

          console.log('[SyncManager] Successfully synced recording');
        } catch (error) {
          console.error('[SyncManager] Failed to sync recording:', error);
          // Update status to failed
          if (recording.id) {
            await updateRecordingStatus(recording.id, 'failed');
          }
        }
      }

      this.syncStatus = 'idle';
    } catch (error) {
      console.error('[SyncManager] Sync error:', error);
      this.syncStatus = 'idle';
    } finally {
      this.syncInProgress = false;
      await this.notifyListeners();
    }
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
