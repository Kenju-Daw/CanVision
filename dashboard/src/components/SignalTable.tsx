import React, { useState, useMemo } from 'react'
import { useSignalStore, selectSignalList, SignalValue } from '../stores/signalStore'

const SOURCE_COLORS: Record<string, string> = {
  user_dbc: '#3b82f6',
  j1939_standard: '#10b981',
  unknown: '#6b7280',
}

const SOURCE_LABELS: Record<string, string> = {
  user_dbc: 'DBC',
  j1939_standard: 'J1939',
  unknown: '?',
}

type SortKey = 'pgn_name' | 'spn_name' | 'value' | 'rate_hz' | 'pgn' | 'spn'

function formatValue(v: number | null | undefined, unit: string): string {
  if (v === null || v === undefined) return '—'
  const rounded = Math.round(v * 1000) / 1000
  return `${rounded} ${unit}`.trim()
}

export function SignalTable() {
  const signals = useSignalStore(selectSignalList)
  const [filter, setFilter] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('pgn_name')
  const [sortAsc, setSortAsc] = useState(true)

  const filtered = useMemo(() => {
    const q = filter.toLowerCase()
    return signals
      .filter((s) =>
        !q ||
        s.pgn_name.toLowerCase().includes(q) ||
        s.spn_name.toLowerCase().includes(q) ||
        s.pgn.toString().includes(q) ||
        s.spn.toString().includes(q) ||
        s.unit.toLowerCase().includes(q)
      )
      .sort((a, b) => {
        let av: any = a[sortKey as keyof SignalValue]
        let bv: any = b[sortKey as keyof SignalValue]
        if (typeof av === 'string') av = av.toLowerCase()
        if (typeof bv === 'string') bv = bv.toLowerCase()
        if (av === bv) return 0
        const cmp = av < bv ? -1 : 1
        return sortAsc ? cmp : -cmp
      })
  }, [signals, filter, sortKey, sortAsc])

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((a) => !a)
    } else {
      setSortKey(key)
      setSortAsc(true)
    }
  }

  const SortIcon = ({ col }: { col: SortKey }) => (
    <span style={{ opacity: sortKey === col ? 1 : 0.3, marginLeft: 4 }}>
      {sortKey === col ? (sortAsc ? '↑' : '↓') : '↕'}
    </span>
  )

  return (
    <div className="signal-table-container">
      {/* Toolbar */}
      <div className="st-toolbar">
        <input
          className="st-search"
          type="text"
          placeholder="Filter by PGN, signal name, unit..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <span className="st-count">
          {filtered.length} / {signals.length} signals
        </span>
      </div>

      {/* Table */}
      <div className="st-scroll">
        <table className="st-table">
          <thead>
            <tr>
              <th onClick={() => toggleSort('pgn_name')} className="st-th">
                PGN <SortIcon col="pgn_name" />
              </th>
              <th onClick={() => toggleSort('spn')} className="st-th" style={{ textAlign: 'right' }}>
                SPN <SortIcon col="spn" />
              </th>
              <th onClick={() => toggleSort('spn_name')} className="st-th">
                Signal <SortIcon col="spn_name" />
              </th>
              <th style={{ textAlign: 'right' }}>SA</th>
              <th onClick={() => toggleSort('value')} className="st-th" style={{ textAlign: 'right' }}>
                Value <SortIcon col="value" />
              </th>
              <th style={{ textAlign: 'right' }}>Min</th>
              <th style={{ textAlign: 'right' }}>Max</th>
              <th style={{ textAlign: 'right' }}>Avg</th>
              <th onClick={() => toggleSort('rate_hz')} className="st-th" style={{ textAlign: 'right' }}>
                Hz <SortIcon col="rate_hz" />
              </th>
              <th style={{ textAlign: 'center' }}>Src</th>
              <th>Raw</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={11} className="st-empty">
                  {signals.length === 0
                    ? 'No signals yet. Upload a log file and start replay.'
                    : 'No signals match the filter.'}
                </td>
              </tr>
            )}
            {filtered.map((s) => {
              const key = `${s.pgn}:${s.spn}:${s.source_address}`
              const isWarning = false // TODO: connect thresholds
              return (
                <tr key={key} className={`st-row ${isWarning ? 'st-row-warn' : ''}`}>
                  <td className="st-pgn">{s.pgn_name}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace', fontSize: 12 }}>
                    {s.spn}
                  </td>
                  <td className="st-signal-name">{s.spn_name}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace', fontSize: 12 }}>
                    0x{s.source_address.toString(16).toUpperCase().padStart(2, '0')}
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: '#111' }}>
                    {formatValue(s.value, s.unit)}
                  </td>
                  <td style={{ textAlign: 'right', color: '#666', fontSize: 12 }}>
                    {formatValue(s.session_min, '')}
                  </td>
                  <td style={{ textAlign: 'right', color: '#666', fontSize: 12 }}>
                    {formatValue(s.session_max, '')}
                  </td>
                  <td style={{ textAlign: 'right', color: '#666', fontSize: 12 }}>
                    {formatValue(s.session_avg, '')}
                  </td>
                  <td style={{ textAlign: 'right', color: '#666', fontSize: 12 }}>
                    {s.rate_hz !== undefined ? (Math.round(s.rate_hz * 10) / 10).toFixed(1) : '—'}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span
                      className="st-source-badge"
                      style={{
                        background: SOURCE_COLORS[s.source] + '22',
                        color: SOURCE_COLORS[s.source],
                        border: `1px solid ${SOURCE_COLORS[s.source]}44`,
                      }}
                    >
                      {SOURCE_LABELS[s.source]}
                    </span>
                  </td>
                  <td className="st-raw">{s.raw_hex}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <style>{`
        .signal-table-container { display: flex; flex-direction: column; height: 100%; }
        .st-toolbar { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 1px solid #e5e7eb; background: #f9fafb; }
        .st-search { flex: 1; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; outline: none; }
        .st-search:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px #3b82f620; }
        .st-count { font-size: 12px; color: #6b7280; white-space: nowrap; }
        .st-scroll { flex: 1; overflow: auto; }
        .st-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .st-table th { position: sticky; top: 0; background: #f3f4f6; padding: 8px 10px; text-align: left; font-weight: 500; color: #374151; border-bottom: 2px solid #e5e7eb; white-space: nowrap; user-select: none; }
        .st-th { cursor: pointer; }
        .st-th:hover { background: #e9eaec; }
        .st-table td { padding: 6px 10px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; white-space: nowrap; }
        .st-row:hover { background: #f0f9ff; }
        .st-row-warn td { background: #fef9c3; }
        .st-pgn { font-weight: 500; color: #1e40af; font-size: 12px; }
        .st-signal-name { color: #111827; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
        .st-raw { font-family: monospace; font-size: 11px; color: #9ca3af; }
        .st-source-badge { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
        .st-empty { text-align: center; padding: 40px; color: #9ca3af; font-size: 14px; }
      `}</style>
    </div>
  )
}
