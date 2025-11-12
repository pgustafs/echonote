/**
 * Audio recording component with modern UI
 */

import { useEffect, useRef, useState } from 'react'

// Logging utility for debugging audio recording issues
const log = {
  info: (...args: any[]) => console.log('[AudioRecorder]', ...args),
  warn: (...args: any[]) => console.warn('[AudioRecorder]', ...args),
  error: (...args: any[]) => console.error('[AudioRecorder]', ...args),
}

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob, url?: string, model?: string, enableDiarization?: boolean, numSpeakers?: number) => void
  isTranscribing: boolean
  availableModels: string[]
  defaultModel: string
}

// WAV conversion functions removed - we send WebM directly like production apps
// This avoids conversion overhead and potential quality issues

export default function AudioRecorder({ onRecordingComplete, isTranscribing, availableModels, defaultModel }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [includeUrl, setIncludeUrl] = useState(false)
  const [url, setUrl] = useState('')
  const [selectedModel, setSelectedModel] = useState(defaultModel)
  const [enableDiarization, setEnableDiarization] = useState(false)
  const [numSpeakers, setNumSpeakers] = useState<number | undefined>(undefined)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const stopPromiseRef = useRef<{
    resolve: (blob: Blob) => void
    reject: (error: Error) => void
  } | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const isStoppingRef = useRef<boolean>(false)

  // Update selected model when default changes
  useEffect(() => {
    if (defaultModel && !selectedModel) {
      setSelectedModel(defaultModel)
    }
  }, [defaultModel, selectedModel])

  useEffect(() => {
    return () => {
      log.info('Component unmounting, cleaning up...')

      // Clean up timer
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }

      // Stop recorder if still recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        log.warn('Stopping active recorder on unmount')
        mediaRecorderRef.current.stop()
      }

      // Stop all tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => {
          log.info('Stopping track on unmount:', track.kind)
          track.stop()
        })
      }
    }
  }, [])

  const startRecording = async () => {
    try {
      log.info('Starting recording...')

      // Reuse existing stream if available (prevents intermittent silence bug)
      // Only request new stream on first recording or if stream was lost
      let stream = streamRef.current

      if (!stream || !stream.active || stream.getTracks().length === 0 || stream.getTracks()[0].readyState !== 'live') {
        log.info('Requesting new microphone stream (first recording or stream lost)')

        // Based on production app research (RecordRTC, react-mic, opus-media-recorder):
        // - echoCancellation: reduces feedback, safe to enable
        // - noiseSuppression: reduces background noise, safe to enable
        // - autoGainControl: disabled to prevent volume fluctuations
        // - channelCount: 1 (mono) for voice notes - smaller file size
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: false,
            channelCount: 1
          }
        })
        streamRef.current = stream
      } else {
        log.info('Reusing existing microphone stream (prevents intermittent silence)')
      }

      log.info('MediaStream obtained', {
        tracks: stream.getTracks().length,
        audioTracks: stream.getAudioTracks().map(t => ({
          kind: t.kind,
          label: t.label,
          enabled: t.enabled,
          muted: t.muted,
          readyState: t.readyState
        }))
      })

      // Store stream reference for cleanup
      streamRef.current = stream

      // Check track health
      const audioTrack = stream.getAudioTracks()[0]
      if (!audioTrack) {
        throw new Error('No audio track available')
      }

      if (audioTrack.readyState !== 'live') {
        log.error('Audio track is not live!', audioTrack.readyState)
        throw new Error(`Audio track state is ${audioTrack.readyState}`)
      }

      // Create audio analyzer for real-time monitoring
      try {
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
        const analyser = audioContext.createAnalyser()
        const microphone = audioContext.createMediaStreamSource(stream)

        analyser.fftSize = 256
        analyser.smoothingTimeConstant = 0.8
        microphone.connect(analyser)

        audioContextRef.current = audioContext
        analyserRef.current = analyser

        // Start monitoring audio levels
        const dataArray = new Uint8Array(analyser.frequencyBinCount)
        let maxLevelSeen = 0
        let samplesChecked = 0

        const checkAudioLevel = () => {
          if (!analyserRef.current || !isRecording) return

          analyser.getByteFrequencyData(dataArray)
          const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
          const normalized = average / 255

          maxLevelSeen = Math.max(maxLevelSeen, normalized)
          samplesChecked++

          // Log every 2 seconds
          if (samplesChecked % 60 === 0) {
            log.info('Audio level check', {
              current: normalized.toFixed(3),
              max: maxLevelSeen.toFixed(3),
              samples: samplesChecked
            })

            if (maxLevelSeen < 0.01 && samplesChecked > 120) {
              log.warn('Very low audio levels detected - microphone may not be working!')
            }
          }

          requestAnimationFrame(checkAudioLevel)
        }

        checkAudioLevel()
        log.info('Audio level monitoring started')
      } catch (error) {
        log.warn('Could not create audio analyzer:', error)
        // Continue anyway - monitoring is optional
      }

      // Detect supported MIME types
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4'
      ]

      let mimeType = 'audio/webm;codecs=opus' // default
      for (const type of mimeTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type
          log.info('Selected MIME type:', type)
          break
        }
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000 // Good quality for speech
      })

      log.info('MediaRecorder created', {
        mimeType: mediaRecorder.mimeType,
        state: mediaRecorder.state,
        audioBitsPerSecond: 128000
      })

      // Reset chunks
      chunksRef.current = []

      // Handle data available with logging
      mediaRecorder.ondataavailable = (event) => {
        log.info('dataavailable event', {
          size: event.data.size,
          type: event.data.type,
          timestamp: event.timeStamp
        })

        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
          log.info('Chunk added, total chunks:', chunksRef.current.length)
        } else {
          log.warn('Received empty chunk (size: 0)')
        }
      }

      // Handle errors
      mediaRecorder.onerror = (event: any) => {
        log.error('MediaRecorder error:', event.error)
        if (stopPromiseRef.current) {
          stopPromiseRef.current.reject(event.error)
          stopPromiseRef.current = null
        }
      }

      // Handle stop event
      mediaRecorder.onstop = async () => {
        log.info('MediaRecorder stopped', {
          totalChunks: chunksRef.current.length,
          chunkSizes: chunksRef.current.map(c => c.size)
        })

        // Normalize MIME type for backend (remove codecs parameter)
        // Backend expects "audio/webm" not "audio/webm;codecs=opus"
        const normalizedMimeType = mimeType.split(';')[0]

        const audioBlob = new Blob(chunksRef.current, { type: normalizedMimeType })
        log.info('Created blob from chunks', {
          size: audioBlob.size,
          type: audioBlob.type,
          originalMimeType: mimeType
        })

        // Resolve the promise if waiting
        if (stopPromiseRef.current) {
          stopPromiseRef.current.resolve(audioBlob)
          stopPromiseRef.current = null
        }

        // Get the URL if checkbox is checked
        const finalUrl = includeUrl && url.trim() ? url.trim() : undefined

        // Check if blob has data
        if (audioBlob.size === 0) {
          log.error('CRITICAL: Final blob is empty! No audio was recorded.')
          alert('Recording failed: No audio data captured. Please try again.')
          return
        }

        // Send WebM directly - like all modern production apps
        // No conversion needed - backend supports audio/webm natively
        log.info('Sending WebM blob directly to backend', {
          size: audioBlob.size,
          type: audioBlob.type
        })
        onRecordingComplete(audioBlob, finalUrl, selectedModel, enableDiarization, numSpeakers)

        // IMPORTANT: Keep stream alive for next recording (prevents intermittent silence bug)
        // Stream will be cleaned up only on component unmount
        log.info('Keeping microphone stream alive for next recording')

        // Close audio context (will be recreated on next recording)
        if (audioContextRef.current) {
          audioContextRef.current.close()
          audioContextRef.current = null
          analyserRef.current = null
        }
      }

      mediaRecorderRef.current = mediaRecorder

      // Start recording with a timeslice to ensure regular data events
      // This helps avoid the "no data" issue on quick stop
      mediaRecorder.start(250) // Fire dataavailable every 250ms
      log.info('MediaRecorder.start(250) called')

      setIsRecording(true)
      setRecordingTime(0)

      // Start timer
      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1)
      }, 1000)

      log.info('Recording started successfully')
    } catch (error) {
      log.error('Error starting recording:', error)
      alert('Could not access microphone. Please check your permissions.')
    }
  }

  const stopRecording = async () => {
    if (!mediaRecorderRef.current || !isRecording) {
      log.warn('stopRecording called but not recording')
      return
    }

    // Prevent multiple simultaneous stop calls
    if (isStoppingRef.current) {
      log.warn('stopRecording already in progress, ignoring duplicate call')
      return
    }

    // Mark that we're stopping
    isStoppingRef.current = true
    setIsStopping(true)

    log.info('Stopping recording...', {
      state: mediaRecorderRef.current.state,
      chunksCollected: chunksRef.current.length
    })

    // Create a promise to wait for the final dataavailable + onstop
    const waitForStop = new Promise<Blob>((resolve, reject) => {
      stopPromiseRef.current = { resolve, reject }

      // Timeout after 5 seconds to prevent hanging
      setTimeout(() => {
        if (stopPromiseRef.current) {
          log.error('Stop timeout - forcing resolution')
          const audioBlob = new Blob(chunksRef.current, {
            type: mediaRecorderRef.current?.mimeType || 'audio/webm'
          })
          stopPromiseRef.current.resolve(audioBlob)
          stopPromiseRef.current = null
        }
      }, 5000)
    })

    try {
      // Request final data and stop
      if (mediaRecorderRef.current.state !== 'inactive') {
        // Request any buffered data before stopping
        if (mediaRecorderRef.current.state === 'paused') {
          log.info('Resuming before stop to capture final data')
          mediaRecorderRef.current.resume()
        }

        mediaRecorderRef.current.stop()
        log.info('MediaRecorder.stop() called, waiting for onstop event...')

        // Wait for the onstop event to fire and process the blob
        await waitForStop
        log.info('Stop completed successfully')
      }
    } catch (error) {
      log.error('Error during stop:', error)
      // On error, still reset states
      setIsRecording(false)
      setIsPaused(false)
      setIsStopping(false)
      isStoppingRef.current = false
      return
    }

    setIsRecording(false)
    setIsPaused(false)
    setIsStopping(false)

    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    // Reset stopping flag
    isStoppingRef.current = false
  }

  const togglePause = () => {
    if (!mediaRecorderRef.current) {
      log.warn('togglePause called but no mediaRecorder')
      return
    }

    if (isPaused) {
      log.info('Resuming recording')
      mediaRecorderRef.current.resume()
      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1)
      }, 1000)
    } else {
      log.info('Pausing recording')
      mediaRecorderRef.current.pause()
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
    setIsPaused(!isPaused)
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="enterprise-card-dark p-6 sm:p-8 lg:p-10 relative overflow-hidden">
      {/* Animated Background Effect - DNA Spiral with Crossing Lines */}
      <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 0 }}>
        <svg
          className="w-full h-full"
          viewBox="0 0 800 400"
          preserveAspectRatio="xMidYMid slice"
          style={{ opacity: 0.6 }}
        >
          <defs>
            {/* Gradient for line 1 (blue to cyan) */}
            <linearGradient id="lineGradient1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#5C7CFA" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#4ADEDE" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#9775FA" stopOpacity="0.8" />
            </linearGradient>

            {/* Gradient for line 2 (purple to cyan) */}
            <linearGradient id="lineGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#9775FA" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#4ADEDE" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#5C7CFA" stopOpacity="0.8" />
            </linearGradient>

            {/* Glow filter for the line */}
            <filter id="lineGlow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>

            {/* Glow filter for cold dots (cyan/blue) */}
            <filter id="dotGlowCold">
              <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>

            {/* Glow filter for warm dot (orange/yellow) */}
            <filter id="dotGlowWarm">
              <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>

            {/* Radial gradient for traveling glow effect */}
            <radialGradient id="travelGlow">
              <stop offset="0%" stopColor="white" stopOpacity="0.8"/>
              <stop offset="50%" stopColor="white" stopOpacity="0.4"/>
              <stop offset="100%" stopColor="white" stopOpacity="0"/>
            </radialGradient>
          </defs>

          {/* First curved path - DNA helix top strand (positioned higher y=150) */}
          <path
            d="M -50 150 Q 100 110, 200 140 Q 300 170, 400 150 Q 500 130, 600 160 Q 700 190, 850 160"
            stroke="url(#lineGradient1)"
            strokeWidth="1"
            fill="none"
            filter="url(#lineGlow)"
            opacity="0.7"
          />

          {/* Second curved path - DNA helix bottom strand (inverse curve, crosses first) */}
          <path
            d="M -50 160 Q 100 190, 200 160 Q 300 130, 400 150 Q 500 170, 600 140 Q 700 110, 850 140"
            stroke="url(#lineGradient2)"
            strokeWidth="1"
            fill="none"
            filter="url(#lineGlow)"
            opacity="0.7"
          />

          {/* Traveling glow circles on first path (2 cold dots) */}
          {[0, 0.5].map((offset, index) => (
            <g key={`glow1-${index}`}>
              {/* Glow area behind/in front of dot */}
              <circle
                r="20"
                fill="url(#travelGlow)"
                opacity="0.3"
              >
                <animateMotion
                  dur="12s"
                  repeatCount="indefinite"
                  begin={`${offset * 12}s`}
                  keyPoints="0;0.7;1"
                  keyTimes="0;0.7;1"
                  calcMode="spline"
                  keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"
                >
                  <mpath href="#motionPath1" />
                </animateMotion>
              </circle>
              {/* Cold colored dot (cyan) */}
              <circle
                r="2.5"
                fill="#4ADEDE"
                filter="url(#dotGlowCold)"
              >
                <animateMotion
                  dur="12s"
                  repeatCount="indefinite"
                  begin={`${offset * 12}s`}
                  keyPoints="0;0.7;1"
                  keyTimes="0;0.7;1"
                  calcMode="spline"
                  keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"
                >
                  <mpath href="#motionPath1" />
                </animateMotion>
                <animate
                  attributeName="opacity"
                  values="0.4;1;1;0.4"
                  dur="12s"
                  repeatCount="indefinite"
                  begin={`${offset * 12}s`}
                  keyTimes="0;0.3;0.7;1"
                />
              </circle>
            </g>
          ))}

          {/* Traveling glow on second path (1 warm dot) */}
          <g>
            {/* Glow area behind/in front of dot */}
            <circle
              r="20"
              fill="url(#travelGlow)"
              opacity="0.3"
            >
              <animateMotion
                dur="12s"
                repeatCount="indefinite"
                begin="0s"
                keyPoints="0;0.7;1"
                keyTimes="0;0.7;1"
                calcMode="spline"
                keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"
              >
                <mpath href="#motionPath2" />
              </animateMotion>
            </circle>
            {/* Warm colored dot (orange/amber) */}
            <circle
              r="2.5"
              fill="#F9A826"
              filter="url(#dotGlowWarm)"
            >
              <animateMotion
                dur="12s"
                repeatCount="indefinite"
                begin="0s"
                keyPoints="0;0.7;1"
                keyTimes="0;0.7;1"
                calcMode="spline"
                keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"
              >
                <mpath href="#motionPath2" />
              </animateMotion>
              <animate
                attributeName="opacity"
                values="0.4;1;1;0.4"
                dur="12s"
                repeatCount="indefinite"
                keyTimes="0;0.3;0.7;1"
              />
            </circle>
          </g>

          {/* Hidden paths for motion */}
          <path
            id="motionPath1"
            d="M -50 150 Q 100 110, 200 140 Q 300 170, 400 150 Q 500 130, 600 160 Q 700 190, 850 160"
            fill="none"
            stroke="none"
          />
          <path
            id="motionPath2"
            d="M -50 160 Q 100 190, 200 160 Q 300 130, 400 150 Q 500 170, 600 140 Q 700 110, 850 140"
            fill="none"
            stroke="none"
          />
        </svg>
      </div>

      <div className="flex flex-col items-center space-y-6 sm:space-y-8 relative" style={{ zIndex: 1 }}>
        <div className="text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-2 flex items-center justify-center space-x-3" style={{ color: '#E6E8EB' }}>
            <svg className="w-7 h-7 sm:w-8 sm:h-8" style={{ color: '#5C7CFA' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            <span>Record Voice Message</span>
          </h2>
          <p className="text-sm sm:text-base" style={{ color: '#9BA4B5' }}>
            Adjust options below, then press the microphone to start.
          </p>
        </div>

        {/* Recording Indicator */}
        {isRecording && (
          <div className="bg-slate-700/50 backdrop-blur-sm px-6 sm:px-8 py-3 sm:py-4 rounded-lg border border-slate-600">
            <div className="flex items-center space-x-3 sm:space-x-4">
              <div className={`w-3 h-3 sm:w-4 sm:h-4 rounded-full ${isPaused ? 'bg-yellow-400' : 'bg-red-500 animate-pulse'}`} />
              <span className="text-2xl sm:text-3xl font-mono font-bold text-white tabular-nums">
                {formatTime(recordingTime)}
              </span>
              <span className="text-sm text-slate-400 hidden sm:inline">
                {isPaused ? 'Paused' : 'Recording'}
              </span>
            </div>
          </div>
        )}

        {/* Microphone Icon / Animation */}
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isTranscribing || isStopping}
          className="relative group"
          aria-label={isRecording ? 'Stop recording and transcribe' : 'Start recording'}
        >
          {/* Pulse rings */}
          {isRecording && !isPaused && (
            <>
              <div className="absolute inset-0 rounded-full bg-red-500/20 animate-ping" />
              <div className="absolute inset-0 rounded-full bg-red-500/10 animate-pulse" />
            </>
          )}
          <div
            className="relative w-32 h-32 sm:w-40 sm:h-40 rounded-full flex items-center justify-center transition-all duration-300"
            style={
              isRecording
                ? { background: '#E44C65', boxShadow: '0 8px 24px rgba(228, 76, 101, 0.4)', transform: 'scale(1.05)', cursor: 'pointer' }
                : isTranscribing
                ? { background: 'rgba(255, 255, 255, 0.2)', cursor: 'not-allowed' }
                : { background: 'linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%)', boxShadow: '0 8px 24px rgba(92, 124, 250, 0.4)', cursor: 'pointer' }
            }
            onMouseEnter={(e) => {
              if (!isTranscribing && !isStopping) {
                if (isRecording) {
                  e.currentTarget.style.boxShadow = '0 12px 32px rgba(228, 76, 101, 0.6)'
                  e.currentTarget.style.transform = 'scale(1.1)'
                } else {
                  e.currentTarget.style.boxShadow = '0 12px 32px rgba(92, 124, 250, 0.6)'
                  e.currentTarget.style.transform = 'scale(1.05)'
                }
              }
            }}
            onMouseLeave={(e) => {
              if (!isTranscribing && !isStopping) {
                if (isRecording) {
                  e.currentTarget.style.boxShadow = '0 8px 24px rgba(228, 76, 101, 0.4)'
                  e.currentTarget.style.transform = 'scale(1.05)'
                } else {
                  e.currentTarget.style.boxShadow = '0 8px 24px rgba(92, 124, 250, 0.4)'
                  e.currentTarget.style.transform = 'scale(1)'
                }
              }
            }}
            onMouseDown={(e) => {
              if (!isTranscribing && !isStopping) {
                if (isRecording) {
                  e.currentTarget.style.transform = 'scale(1)'
                } else {
                  e.currentTarget.style.transform = 'scale(0.95)'
                }
              }
            }}
            onMouseUp={(e) => {
              if (!isTranscribing && !isStopping) {
                if (isRecording) {
                  e.currentTarget.style.transform = 'scale(1.1)'
                } else {
                  e.currentTarget.style.transform = 'scale(1.05)'
                }
              }
            }}
          >
            <svg
              className="w-16 h-16 sm:w-20 sm:h-20 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
          </div>
        </button>

        {/* Model Selector & URL Input Section */}
        {!isRecording && !isTranscribing && (
          <div className="w-full max-w-2xl space-y-4 sm:space-y-5">
            {/* Model Selector */}
            {availableModels.length > 0 && (
              <div className="space-y-2">
                <label className="block text-white font-semibold text-sm sm:text-base flex items-center space-x-2">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                  <span>Transcription Model</span>
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="input-field-dark"
                >
                  {availableModels.map((model) => (
                    <option key={model} value={model} className="bg-slate-800">
                      {model}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* URL Checkbox */}
            <label className="flex items-center space-x-3 cursor-pointer group touch-manipulation">
              <input
                type="checkbox"
                checked={includeUrl}
                onChange={(e) => setIncludeUrl(e.target.checked)}
                className="w-5 h-5 rounded border-2 border-blue-500 text-blue-600 focus:ring-2 focus:ring-blue-500 bg-slate-700 cursor-pointer"
              />
              <span className="text-white font-medium text-sm sm:text-base group-hover:text-blue-300 transition-colors">Add URL to voice note</span>
            </label>

            {/* URL Input */}
            {includeUrl && (
              <div className="space-y-2">
                <label className="block text-white font-semibold text-sm sm:text-base flex items-center space-x-2">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <span>URL</span>
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="input-field-dark"
                />
              </div>
            )}

            {/* Diarization Checkbox */}
            <label className="flex items-center space-x-3 cursor-pointer group touch-manipulation">
              <input
                type="checkbox"
                checked={enableDiarization}
                onChange={(e) => {
                  setEnableDiarization(e.target.checked)
                  if (!e.target.checked) {
                    setNumSpeakers(undefined)
                  }
                }}
                className="w-5 h-5 rounded border-2 border-purple-500 text-purple-600 focus:ring-2 focus:ring-purple-500 bg-slate-700 cursor-pointer"
              />
              <div className="flex-1">
                <span className="text-white font-medium text-sm sm:text-base group-hover:text-purple-300 transition-colors block">
                  Enable speaker diarization
                </span>
                <span className="text-xs text-slate-400">Detect and label different speakers</span>
              </div>
            </label>

            {/* Number of Speakers Input */}
            {enableDiarization && (
              <div className="space-y-2 pl-8 border-l-2 border-purple-500/30">
                <label className="block text-white font-semibold text-sm sm:text-base flex items-center space-x-2">
                  <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <span>Number of Speakers (optional)</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={numSpeakers ?? ''}
                  onChange={(e) => {
                    const value = e.target.value
                    setNumSpeakers(value ? parseInt(value) : undefined)
                  }}
                  placeholder="Auto-detect"
                  className="input-field-dark"
                />
                <p className="text-xs sm:text-sm text-slate-400 flex items-start space-x-2">
                  <svg className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <span>Leave empty to automatically detect (2-10 speakers)</span>
                </p>
              </div>
            )}
          </div>
        )}

        {/* Pause/Resume Button - Only shown during recording */}
        {isRecording && (
          <div className="flex justify-center w-full sm:w-auto">
            <button
              onClick={togglePause}
              className="btn-secondary px-6 sm:px-8 py-3 text-base flex items-center"
            >
              {isPaused ? (
                <>
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>Resume</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>Pause</span>
                </>
              )}
            </button>
          </div>
        )}

        {isTranscribing && (
          <div className="bg-blue-50 border border-blue-200 px-6 sm:px-8 py-4 rounded-lg shadow-sm w-full sm:w-auto">
            <div className="flex items-center justify-center space-x-3 sm:space-x-4">
              <div className="w-5 h-5 sm:w-6 sm:h-6 spinner"></div>
              <span className="font-semibold text-blue-900 text-sm sm:text-base">Transcribing your voice...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
