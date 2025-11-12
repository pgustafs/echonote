/**
 * Sync Indicator Component
 * Shows online/offline status and pending recordings count
 */

import { SyncStatus } from '../utils/syncManager';

interface SyncIndicatorProps {
  isOnline: boolean;
  syncStatus: SyncStatus;
  pendingCount: number;
  onSyncClick?: () => void;
}

export default function SyncIndicator({
  isOnline,
  syncStatus,
  pendingCount,
  onSyncClick,
}: SyncIndicatorProps) {
  // Don't show if online and no pending recordings
  if (isOnline && pendingCount === 0 && syncStatus === 'idle') {
    return null;
  }

  const getStatusInfo = () => {
    if (!isOnline) {
      return {
        icon: '📴',
        text: 'Offline',
        color: 'text-gray-400',
        bgColor: 'bg-gray-900/80',
        borderColor: 'border-gray-600',
      };
    }

    if (syncStatus === 'syncing') {
      return {
        icon: '🔄',
        text: 'Syncing...',
        color: 'text-blue-400',
        bgColor: 'bg-blue-900/80',
        borderColor: 'border-blue-500',
      };
    }

    if (pendingCount > 0) {
      return {
        icon: '⏳',
        text: `${pendingCount} pending`,
        color: 'text-orange-400',
        bgColor: 'bg-orange-900/80',
        borderColor: 'border-orange-500',
      };
    }

    return {
      icon: '✓',
      text: 'Synced',
      color: 'text-green-400',
      bgColor: 'bg-green-900/80',
      borderColor: 'border-green-500',
    };
  };

  const { icon, text, color, bgColor, borderColor } = getStatusInfo();

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 flex items-center space-x-2 px-4 py-3 rounded-2xl border ${bgColor} ${borderColor} backdrop-blur-sm shadow-lg transition-all duration-300`}
      style={{ minWidth: '150px' }}
    >
      {/* Status Icon */}
      <span className={`text-xl ${syncStatus === 'syncing' ? 'animate-spin' : ''}`}>
        {icon}
      </span>

      {/* Status Text */}
      <div className="flex flex-col flex-1">
        <span className={`text-sm font-semibold ${color}`}>{text}</span>
        {pendingCount > 0 && isOnline && syncStatus !== 'syncing' && (
          <button
            onClick={onSyncClick}
            className="text-xs text-blue-300 hover:text-blue-200 underline mt-1 text-left"
          >
            Sync now
          </button>
        )}
      </div>

      {/* Saved Offline Badge */}
      {!isOnline && (
        <div className="flex items-center space-x-1">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"
            />
          </svg>
          <span className="text-xs text-gray-400">Saved locally</span>
        </div>
      )}
    </div>
  );
}
