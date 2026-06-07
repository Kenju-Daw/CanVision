import React from 'react'
import { useWebSocket, WSStatus } from './hooks/useWebSocket'
import { useSignalStore, selectSignalCount } from './stores/signalStore'
import { SignalTable } from './components/SignalTable'
import { FileUpload } from './components/FileUpload'

const WS_URL = import.meta.env.PROD
  ? `ws://${window.location.host}/ws`
  : 'ws://localhost:8000/ws'

const STATUS_COLORS: Record<WSStatus, string> = {
  connected: '#10b981',
  connecting: '#f59e0b',
  disconnected: '#6b7280',
  error: '#ef4444',
}

const STATUS_LABELS: Record<WSStatus, string> = {
  connected: 'Connected',
  connecting: 'Connecting…',
  disconnected: 'Disconnected',
  error: 'Error',
}

export default function App() {
  const onMessage = useSignalStore((s) => s.onMessage)
  const statusLog = useSignalStore((s) => s.statusLog)
  const replayRunning = useSignalStore((s) => s.replayRunning)
  const signalCount = useSignalStore(selectSignalCount)

  const { status } = useWebSocket({ url: WS_URL, onMessage })

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="app-title">
          <span className="app-logo">📡</span>
          <span className="app-name">CAN Vision</span>
          <span className="app-mode">Offline Analyzer</span>
        </div>
        <div className="app-status-bar">
          {replayRunning && (
            <span className="app-replay-badge">
              <span className="app-pulse" /> Replaying
            </span>
          )}
          <span className="app-signal-count">{signalCount} signals</span>
          <span className="app-ws-status" style={{ color: STATUS_COLORS[status] }}>
            <span
              className="app-ws-dot"
              style={{ background: STATUS_COLORS[status] }}
            />
            {STATUS_LABELS[status]}
          </span>
        </div>
      </header>

      {/* Body */}
      <div className="app-body">
        {/* Left: File upload + status log */}
        <aside className="app-sidebar">
          <div className="panel">
            <div className="panel-title">Log File</div>
            <FileUpload />
          </div>

          <div className="panel panel-log">
            <div className="panel-title">Event Log</div>
            <div className="log-list">
              {statusLog.length === 0 && (
                <div className="log-empty">No events yet</div>
              )}
              {statusLog.map((s, i) => (
                <div key={i} className="log-entry">
                  <span className="log-event">{s.event}</span>
                  {s.detail && <span className="log-detail">{s.detail}</span>}
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Main: Signal table */}
        <main className="app-main">
          <div className="panel panel-signals">
            <div className="panel-title">
              Decoded Signals
              <span className="panel-subtitle">
                J1939 + DBC — live values from replay
              </span>
            </div>
            <SignalTable />
          </div>
        </main>
      </div>

      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html, body, #root { height: 100%; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f3f4f6; color: #111827; }

        .app { display: flex; flex-direction: column; height: 100vh; }

        .app-header { display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 52px; background: #111827; color: white; flex-shrink: 0; }
        .app-title { display: flex; align-items: center; gap: 10px; }
        .app-logo { font-size: 20px; }
        .app-name { font-size: 16px; font-weight: 700; letter-spacing: -0.02em; }
        .app-mode { font-size: 12px; color: #9ca3af; background: #374151; padding: 2px 8px; border-radius: 4px; }

        .app-status-bar { display: flex; align-items: center; gap: 16px; font-size: 12px; }
        .app-signal-count { color: #9ca3af; }
        .app-ws-status { display: flex; align-items: center; gap: 5px; font-weight: 500; }
        .app-ws-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
        .app-replay-badge { display: flex; align-items: center; gap: 5px; color: #fbbf24; font-weight: 500; }
        .app-pulse { width: 7px; height: 7px; border-radius: 50%; background: #fbbf24; animation: blink 1s ease-in-out infinite; display: inline-block; }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

        .app-body { display: flex; flex: 1; overflow: hidden; gap: 12px; padding: 12px; }

        .app-sidebar { display: flex; flex-direction: column; gap: 12px; width: 300px; flex-shrink: 0; overflow-y: auto; }
        .app-main { flex: 1; overflow: hidden; }

        .panel { background: white; border-radius: 10px; border: 1px solid #e5e7eb; overflow: hidden; display: flex; flex-direction: column; }
        .panel-signals { height: 100%; }
        .panel-log { flex: 1; min-height: 120px; }

        .panel-title { padding: 10px 16px; font-size: 13px; font-weight: 600; color: #374151; border-bottom: 1px solid #f3f4f6; display: flex; align-items: baseline; gap: 10px; background: #fafafa; flex-shrink: 0; }
        .panel-subtitle { font-size: 11px; color: #9ca3af; font-weight: 400; }

        .log-list { padding: 8px 12px; display: flex; flex-direction: column; gap: 4px; overflow-y: auto; flex: 1; }
        .log-empty { font-size: 12px; color: #9ca3af; text-align: center; padding: 12px 0; }
        .log-entry { font-size: 11px; line-height: 1.4; }
        .log-event { font-weight: 600; color: #1e40af; margin-right: 4px; }
        .log-detail { color: #6b7280; }
      `}</style>
    </div>
  )
}
