import React, { useRef, useState } from 'react'
import { useSignalStore } from '../stores/signalStore'

interface UploadedFile {
  file_id: string
  filename: string
  format: string
  size_bytes: number
}

export function FileUpload() {
  const dropRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [speed, setSpeed] = useState(1.0)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { replayRunning, clearSession } = useSignalStore()

  async function uploadFile(file: File) {
    setUploading(true)
    setError(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')
      const info: UploadedFile = {
        file_id: data.file_id,
        filename: data.filename,
        format: data.format,
        size_bytes: data.size_bytes,
      }
      setFiles((prev) => [info, ...prev])
      setSelectedFile(info.file_id)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  async function startReplay() {
    if (!selectedFile) return
    clearSession()
    setError(null)
    try {
      const res = await fetch('/api/replay/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: selectedFile, speed }),
      })
      if (!res.ok) {
        const d = await res.json()
        throw new Error(d.detail)
      }
    } catch (e: any) {
      setError(e.message)
    }
  }

  async function stopReplay() {
    await fetch('/api/replay/stop', { method: 'POST' })
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  }

  function formatSize(bytes: number) {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="fu-container">
      {/* Drop zone */}
      <div
        ref={dropRef}
        className={`fu-dropzone ${dragging ? 'fu-drag-over' : ''} ${uploading ? 'fu-uploading' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".trc,.log,.asc,.blf,.mf4,.mdf"
          style={{ display: 'none' }}
          onChange={(e) => { if (e.target.files?.[0]) uploadFile(e.target.files[0]) }}
        />
        <div className="fu-icon">📁</div>
        <div className="fu-label">
          {uploading ? 'Uploading...' : 'Drop CAN log file or click to browse'}
        </div>
        <div className="fu-hint">.trc .log .asc .blf .mf4 .mdf</div>
      </div>

      {error && <div className="fu-error">⚠ {error}</div>}

      {/* File list */}
      {files.length > 0 && (
        <div className="fu-files">
          <div className="fu-files-label">Uploaded files</div>
          {files.map((f) => (
            <div
              key={f.file_id}
              className={`fu-file-row ${selectedFile === f.file_id ? 'fu-selected' : ''}`}
              onClick={() => setSelectedFile(f.file_id)}
            >
              <span className="fu-format-badge">{f.format.toUpperCase()}</span>
              <span className="fu-filename">{f.filename}</span>
              <span className="fu-filesize">{formatSize(f.size_bytes)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Replay controls */}
      {selectedFile && (
        <div className="fu-replay">
          <div className="fu-speed-row">
            <label className="fu-speed-label">Speed</label>
            <input
              type="range"
              min={0.1}
              max={10}
              step={0.1}
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="fu-speed-slider"
              disabled={replayRunning}
            />
            <span className="fu-speed-val">{speed.toFixed(1)}x</span>
          </div>
          <div className="fu-actions">
            {!replayRunning ? (
              <button className="fu-btn fu-btn-start" onClick={startReplay}>
                ▶ Start Replay
              </button>
            ) : (
              <button className="fu-btn fu-btn-stop" onClick={stopReplay}>
                ⏹ Stop
              </button>
            )}
            <button className="fu-btn fu-btn-clear" onClick={clearSession} disabled={replayRunning}>
              Clear Session
            </button>
          </div>
        </div>
      )}

      <style>{`
        .fu-container { display: flex; flex-direction: column; gap: 12px; padding: 12px; }
        .fu-dropzone { border: 2px dashed #d1d5db; border-radius: 10px; padding: 24px; text-align: center; cursor: pointer; transition: all 0.15s; background: #fafafa; }
        .fu-dropzone:hover, .fu-drag-over { border-color: #3b82f6; background: #eff6ff; }
        .fu-uploading { opacity: 0.6; cursor: wait; }
        .fu-icon { font-size: 28px; margin-bottom: 8px; }
        .fu-label { font-size: 14px; font-weight: 500; color: #374151; }
        .fu-hint { font-size: 11px; color: #9ca3af; margin-top: 4px; }
        .fu-error { background: #fef2f2; border: 1px solid #fca5a5; color: #dc2626; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
        .fu-files { display: flex; flex-direction: column; gap: 4px; }
        .fu-files-label { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px; }
        .fu-file-row { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 6px; cursor: pointer; border: 1px solid transparent; }
        .fu-file-row:hover { background: #f3f4f6; }
        .fu-selected { background: #eff6ff !important; border-color: #bfdbfe !important; }
        .fu-format-badge { font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; background: #1e40af22; color: #1e40af; }
        .fu-filename { font-size: 13px; color: #111827; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .fu-filesize { font-size: 11px; color: #9ca3af; }
        .fu-replay { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
        .fu-speed-row { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
        .fu-speed-label { font-size: 12px; color: #6b7280; font-weight: 500; }
        .fu-speed-slider { flex: 1; }
        .fu-speed-val { font-size: 12px; font-weight: 600; color: #111827; min-width: 32px; text-align: right; }
        .fu-actions { display: flex; gap: 8px; }
        .fu-btn { padding: 7px 14px; border-radius: 6px; border: none; font-size: 13px; font-weight: 500; cursor: pointer; transition: opacity 0.1s; }
        .fu-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .fu-btn-start { background: #3b82f6; color: white; flex: 1; }
        .fu-btn-start:hover:not(:disabled) { background: #2563eb; }
        .fu-btn-stop { background: #ef4444; color: white; flex: 1; }
        .fu-btn-stop:hover { background: #dc2626; }
        .fu-btn-clear { background: #f3f4f6; color: #374151; }
        .fu-btn-clear:hover:not(:disabled) { background: #e5e7eb; }
      `}</style>
    </div>
  )
}
