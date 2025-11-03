/**
 * Audio recording component with modern UI
 */

import { useEffect, useRef, useState } from 'react'

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob, url?: string) => void
  isTranscribing: boolean
}

/**
 * Convert audio blob to WAV format using Web Audio API
 */
async function convertToWav(blob: Blob): Promise<Blob> {
  // Create audio context
  const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()

  // Read the blob as array buffer
  const arrayBuffer = await blob.arrayBuffer()

  // Decode audio data
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

  // Convert to WAV format
  const wavBuffer = audioBufferToWav(audioBuffer)

  return new Blob([wavBuffer], { type: 'audio/wav' })
}

/**
 * Convert AudioBuffer to WAV format
 */
function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
  const length = buffer.length * buffer.numberOfChannels * 2 + 44
  const arrayBuffer = new ArrayBuffer(length)
  const view = new DataView(arrayBuffer)
  const channels: Float32Array[] = []
  let offset = 0
  let pos = 0

  // Write WAV header
  const setUint16 = (data: number) => {
    view.setUint16(pos, data, true)
    pos += 2
  }
  const setUint32 = (data: number) => {
    view.setUint32(pos, data, true)
    pos += 4
  }

  // RIFF identifier
  setUint32(0x46464952) // "RIFF"
  setUint32(length - 8) // file length - 8
  setUint32(0x45564157) // "WAVE"

  // fmt chunk
  setUint32(0x20746d66) // "fmt "
  setUint32(16) // chunk length
  setUint16(1) // PCM
  setUint16(buffer.numberOfChannels)
  setUint32(buffer.sampleRate)
  setUint32(buffer.sampleRate * 2 * buffer.numberOfChannels) // avg bytes/sec
  setUint16(buffer.numberOfChannels * 2) // block align
  setUint16(16) // 16-bit

  // data chunk
  setUint32(0x61746164) // "data"
  setUint32(length - pos - 4) // chunk length

  // Get channel data
  for (let i = 0; i < buffer.numberOfChannels; i++) {
    channels.push(buffer.getChannelData(i))
  }

  // Interleave channels and convert to 16-bit PCM
  while (pos < length) {
    for (let i = 0; i < buffer.numberOfChannels; i++) {
      let sample = Math.max(-1, Math.min(1, channels[i][offset]))
      sample = sample < 0 ? sample * 0x8000 : sample * 0x7fff
      view.setInt16(pos, sample, true)
      pos += 2
    }
    offset++
  }

  return arrayBuffer
}

export default function AudioRecorder({ onRecordingComplete, isTranscribing }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const [includeUrl, setIncludeUrl] = useState(false)
  const [url, setUrl] = useState('')

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Try to use WAV format if supported, otherwise fall back to webm
      let mimeType = 'audio/webm;codecs=opus'
      let blobType = 'audio/webm'

      if (MediaRecorder.isTypeSupported('audio/wav')) {
        mimeType = 'audio/wav'
        blobType = 'audio/wav'
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm;codecs=opus'
        blobType = 'audio/webm'
      }

      const mediaRecorder = new MediaRecorder(stream, { mimeType })

      chunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: blobType })

        // Get the URL if checkbox is checked
        const finalUrl = includeUrl && url.trim() ? url.trim() : undefined

        // If we recorded in webm, convert to WAV in the browser
        if (blobType === 'audio/webm') {
          try {
            const wavBlob = await convertToWav(audioBlob)
            onRecordingComplete(wavBlob, finalUrl)
          } catch (error) {
            console.error('WAV conversion failed, sending original:', error)
            onRecordingComplete(audioBlob, finalUrl)
          }
        } else {
          onRecordingComplete(audioBlob, finalUrl)
        }

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)

      // Start timer
      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1)
      }, 1000)
    } catch (error) {
      console.error('Error accessing microphone:', error)
      alert('Could not access microphone. Please check your permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsPaused(false)

      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }

  const togglePause = () => {
    if (mediaRecorderRef.current) {
      if (isPaused) {
        mediaRecorderRef.current.resume()
        timerRef.current = window.setInterval(() => {
          setRecordingTime((prev) => prev + 1)
        }, 1000)
      } else {
        mediaRecorderRef.current.pause()
        if (timerRef.current) {
          clearInterval(timerRef.current)
        }
      }
      setIsPaused(!isPaused)
    }
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="glass-card-solid p-10">
      <div className="flex flex-col items-center space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white mb-2">
            Record Voice Message
          </h2>
          <p className="text-slate-300">
            Click the button below to start recording
          </p>
        </div>

        {/* Recording Indicator */}
        {isRecording && (
          <div className="glass-card px-6 py-3 rounded-full">
            <div className="flex items-center space-x-4">
              <div className={`w-3 h-3 rounded-full ${isPaused ? 'bg-yellow-400' : 'bg-red-500 animate-pulse'}`} />
              <span className="text-3xl font-mono font-bold text-white tabular-nums">
                {formatTime(recordingTime)}
              </span>
            </div>
          </div>
        )}

        {/* Microphone Icon / Animation */}
        <div className="relative">
          {/* Pulse rings */}
          {isRecording && !isPaused && (
            <>
              <div className="absolute inset-0 rounded-full bg-red-500/20 animate-ping" />
              <div className="absolute inset-0 rounded-full bg-red-500/10 animate-pulse" />
            </>
          )}
          <div
            className={`relative w-40 h-40 rounded-full flex items-center justify-center transition-all duration-500 ${
              isRecording
                ? 'bg-gradient-to-br from-red-500 to-pink-500 shadow-2xl shadow-red-500/50 scale-110'
                : 'bg-gradient-to-br from-vite-600 to-electric-600 shadow-2xl shadow-vite-500/50 hover:scale-105'
            }`}
          >
            <svg
              className="w-20 h-20 text-white drop-shadow-lg"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
          </div>
        </div>

        {/* URL Input Section */}
        {!isRecording && !isTranscribing && (
          <div className="w-full max-w-md space-y-3">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeUrl}
                onChange={(e) => setIncludeUrl(e.target.checked)}
                className="w-5 h-5 rounded border-2 border-vite-500 text-vite-600 focus:ring-2 focus:ring-vite-500/50 bg-slate-700"
              />
              <span className="text-white font-medium">Add URL to voice note</span>
            </label>

            {includeUrl && (
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-4 py-3 rounded-xl bg-slate-700/50 text-white border-2 border-vite-500/30 focus:outline-none focus:ring-2 focus:ring-vite-500/50 focus:border-vite-500 placeholder-slate-400"
              />
            )}
          </div>
        )}

        {/* Control Buttons */}
        <div className="flex flex-wrap gap-4 justify-center">
          {!isRecording ? (
            <button
              onClick={startRecording}
              disabled={isTranscribing}
              className="btn-vite px-10 py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              <span className="flex items-center space-x-3">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>Start Recording</span>
              </span>
            </button>
          ) : (
            <>
              <button
                onClick={togglePause}
                className="btn-ghost"
              >
                {isPaused ? (
                  <span className="flex items-center space-x-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>Resume</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>Pause</span>
                  </span>
                )}
              </button>
              <button
                onClick={stopRecording}
                className="btn-danger"
              >
                <span className="flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>Stop & Transcribe</span>
                </span>
              </button>
            </>
          )}
        </div>

        {isTranscribing && (
          <div className="glass-card px-8 py-4 rounded-full">
            <div className="flex items-center space-x-4">
              <div className="relative w-6 h-6">
                <div className="absolute inset-0 rounded-full border-2 border-white/20"></div>
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-white animate-spin"></div>
              </div>
              <span className="font-semibold text-white">Transcribing your voice...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
