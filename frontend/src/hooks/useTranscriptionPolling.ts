/**
 * React hook for polling transcription status in the background.
 *
 * This hook polls the backend API for transcription status updates
 * for pending or processing transcriptions. It automatically stops
 * polling when all transcriptions are completed or failed.
 *
 * Usage:
 *   const { statuses, isPolling } = useTranscriptionPolling(transcriptionIds)
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { getBulkTranscriptionStatus, TranscriptionStatus } from '../api'

export function useTranscriptionPolling(
  transcriptionIds: number[],
  enabled: boolean = true,
  onComplete?: (id: number) => void,
  onStatusUpdate?: (statuses: Map<number, TranscriptionStatus>) => void
) {
  const [statuses, setStatuses] = useState<Map<number, TranscriptionStatus>>(new Map())
  const [isPolling, setIsPolling] = useState(false)
  const pollIntervalRef = useRef<number | null>(null)

  const pollStatuses = useCallback(async () => {
    if (transcriptionIds.length === 0 || !enabled) {
      console.log('[useTranscriptionPolling] Polling disabled or no IDs:', { transcriptionIds, enabled })
      setIsPolling(false)
      return
    }

    console.log('[useTranscriptionPolling] Starting poll for IDs:', transcriptionIds)
    setIsPolling(true)

    try {
      // Poll ALL transcription IDs to detect status changes
      const response = await getBulkTranscriptionStatus(transcriptionIds)
      console.log('[useTranscriptionPolling] Poll response:', response)

      // Build the new statuses map first, before updating state
      const newStatuses = new Map<number, TranscriptionStatus>()

      setStatuses(prevStatuses => {
        response.statuses.forEach(status => {
          const oldStatus = prevStatuses.get(status.id)
          const newStatus: TranscriptionStatus = {
            id: status.id,
            status: status.status as 'pending' | 'processing' | 'completed' | 'failed',
            progress: status.progress,
            task_id: null,
            error_message: status.error_message
          }
          newStatuses.set(status.id, newStatus)

          // Trigger callback if status is completed and either:
          // 1. This is the first time we're seeing this transcription (oldStatus is undefined)
          // 2. The status changed from non-completed to completed
          if (onComplete && newStatus.status === 'completed') {
            if (!oldStatus || oldStatus.status !== 'completed') {
              onComplete(status.id)
            }
          }
        })

        // Check if all are done
        const allDone = Array.from(newStatuses.values()).every(
          s => s.status === 'completed' || s.status === 'failed'
        )

        if (allDone) {
          setIsPolling(false)
        }

        return newStatuses
      })

      // Notify parent component of status updates AFTER setStatuses completes
      // We built newStatuses outside the callback, so it has the current values
      // This prevents React state batching issues when onStatusUpdate calls setState in parent
      if (onStatusUpdate && newStatuses.size > 0) {
        console.log('[useTranscriptionPolling] Calling onStatusUpdate with:', Array.from(newStatuses.entries()))
        onStatusUpdate(newStatuses)
      } else {
        console.log('[useTranscriptionPolling] Not calling onStatusUpdate:', { hasCallback: !!onStatusUpdate, statusCount: newStatuses.size })
      }
    } catch (error) {
      console.error('[useTranscriptionPolling] Error polling transcription status:', error)
      // Continue polling even on error (might be temporary network issue)
    }
  }, [transcriptionIds, enabled, onComplete, onStatusUpdate])

  useEffect(() => {
    if (!enabled) {
      // Clear interval if polling is disabled
      if (pollIntervalRef.current !== null) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
      setIsPolling(false)
      return
    }

    // Poll immediately on mount or when IDs change
    pollStatuses()

    // Set up polling interval (every 2 seconds)
    if (pollIntervalRef.current !== null) {
      clearInterval(pollIntervalRef.current)
    }

    pollIntervalRef.current = window.setInterval(pollStatuses, 2000)

    // Cleanup on unmount
    return () => {
      if (pollIntervalRef.current !== null) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [pollStatuses, enabled, onStatusUpdate])

  return {
    statuses,
    isPolling,
    refreshStatuses: pollStatuses
  }
}
