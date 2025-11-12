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
    await syncManager.syncPendingRecordings();
  };

  return {
    isOnline,
    syncStatus,
    pendingCount,
    saveOfflineRecording,
    triggerSync,
  };
}
