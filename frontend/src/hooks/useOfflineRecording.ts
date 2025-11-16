/**
 * Hook for handling offline recording and synchronization
 */

import { useState, useEffect } from 'react';
import { savePendingRecording, getPendingCount } from '../utils/indexedDB';
import { syncManager, SyncStatus } from '../utils/syncManager';

export function useOfflineRecording() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle');
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    // Subscribe to sync manager updates
    const unsubscribe = syncManager.subscribe((status, count) => {
      setSyncStatus(status);
      setPendingCount(count);
    });

    // Listen for online/offline events
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initialize pending count
    getPendingCount().then(setPendingCount);

    return () => {
      unsubscribe();
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  /**
   * Save recording for offline sync
   */
  const saveOfflineRecording = async (
    audioBlob: Blob,
    url?: string,
    model?: string,
    enableDiarization?: boolean,
    numSpeakers?: number
  ): Promise<void> => {
    const extension = audioBlob.type.includes('wav') ? 'wav' : 'webm';
    const filename = `recording-${Date.now()}.${extension}`;

    console.log('[useOfflineRecording] Saving blob to IndexedDB:', {
      size: audioBlob.size,
      type: audioBlob.type,
      filename,
    });

    if (audioBlob.size === 0) {
      console.error('[useOfflineRecording] Attempted to save an empty audio blob. Aborting.');
      // Optionally, you could set an error state here to inform the user.
      return;
    }

    await savePendingRecording({
      blob: audioBlob,
      filename,
      url,
      model,
      enableDiarization,
      numSpeakers,
    });

    // Update count
    const count = await getPendingCount();
    setPendingCount(count);

    // Register background sync if online
    if (isOnline) {
      await syncManager.registerBackgroundSync();
      // Trigger immediate sync
      await syncManager.syncPendingRecordings();
    }
  };

  /**
   * Manually trigger sync
   */
  const triggerSync = async (): Promise<void> => {
    console.log('[useOfflineRecording] triggerSync called');
    try {
      await syncManager.syncPendingRecordings();
      console.log('[useOfflineRecording] Sync completed');
      // Update pending count after sync
      const count = await getPendingCount();
      setPendingCount(count);
      console.log('[useOfflineRecording] Updated pending count:', count);
    } catch (error) {
      console.error('[useOfflineRecording] Sync error:', error);
    }
  };

  return {
    isOnline,
    syncStatus,
    pendingCount,
    saveOfflineRecording,
    triggerSync,
  };
}
