import { create } from 'zustand'

export interface SignalValue {
  type: 'signal'
  ts: number
  pgn: number
  pgn_name: string
  spn: number
  spn_name: string
  value: number | null
  unit: string
  raw_hex: string
  source_address: number
  source: 'user_dbc' | 'j1939_standard' | 'unknown'
  channel: number
  // stats (populated from server)
  session_min?: number
  session_max?: number
  session_avg?: number
  rate_hz?: number
}

export interface UnknownFrame {
  type: 'unknown'
  ts: number
  arbitration_id: number
  arbitration_id_hex: string
  pgn: number
  pgn_hex: string
  source_address: number
  dlc: number
  data_hex: string
}

export interface StatusMessage {
  type: 'status'
  event: string
  detail: string
}

type SignalKey = string  // `${pgn}:${spn}:${sa}`

interface SignalStore {
  // Live signal values — keyed for O(1) updates
  signals: Record<SignalKey, SignalValue>
  // Unknown frames (last 50)
  unknownFrames: UnknownFrame[]
  // Status events log (last 20)
  statusLog: StatusMessage[]
  // DBC/J1939 signal definitions from backend
  definitions: any[]
  // Replay state
  replayRunning: boolean
  replayFile: string | null
  // Actions
  onMessage: (data: any) => void
  clearSession: () => void
  setDefinitions: (defs: any[]) => void
  setReplayRunning: (running: boolean, file?: string) => void
}

function signalKey(s: SignalValue): SignalKey {
  return `${s.pgn}:${s.spn}:${s.source_address}`
}

export const useSignalStore = create<SignalStore>((set, get) => ({
  signals: {},
  unknownFrames: [],
  statusLog: [],
  definitions: [],
  replayRunning: false,
  replayFile: null,

  onMessage: (data: any) => {
    const { type } = data
    if (!type) return

    if (type === 'signal') {
      const s = data as SignalValue
      const key = signalKey(s)
      set((state) => ({
        signals: { ...state.signals, [key]: s },
      }))
      return
    }

    if (type === 'unknown') {
      set((state) => ({
        unknownFrames: [data, ...state.unknownFrames].slice(0, 50),
      }))
      return
    }

    if (type === 'status') {
      const msg = data as StatusMessage
      set((state) => ({
        statusLog: [msg, ...state.statusLog].slice(0, 20),
        replayRunning:
          msg.event === 'replay_start'
            ? true
            : msg.event === 'replay_complete' || msg.event === 'replay_stopped' || msg.event === 'replay_error'
            ? false
            : state.replayRunning,
      }))
      return
    }

    if (type === 'heartbeat' || type === 'ping' || type === 'pong') {
      return  // silently ignore
    }
  },

  clearSession: () => {
    set({ signals: {}, unknownFrames: [], statusLog: [] })
  },

  setDefinitions: (defs) => {
    set({ definitions: defs })
  },

  setReplayRunning: (running, file) => {
    set({ replayRunning: running, replayFile: file ?? get().replayFile })
  },
}))

// Selector helpers
export const selectSignalList = (s: SignalStore) => Object.values(s.signals)
export const selectSignalCount = (s: SignalStore) => Object.keys(s.signals).length
export const selectByPGN = (pgn: number) => (s: SignalStore) =>
  Object.values(s.signals).filter((v) => v.pgn === pgn)
