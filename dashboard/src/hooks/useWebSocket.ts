import { useEffect, useRef, useCallback, useState } from 'react'

export type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseWebSocketOptions {
  url: string
  onMessage: (data: any) => void
  reconnectDelay?: number
  maxReconnects?: number
}

export function useWebSocket({
  url,
  onMessage,
  reconnectDelay = 2000,
  maxReconnects = 10,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCount = useRef(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [status, setStatus] = useState<WSStatus>('disconnected')
  const mountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!mountedRef.current) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setStatus('connecting')
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (!mountedRef.current) return
      setStatus('connected')
      reconnectCount.current = 0
    }

    ws.onmessage = (event) => {
      if (!mountedRef.current) return
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onerror = () => {
      if (!mountedRef.current) return
      setStatus('error')
    }

    ws.onclose = () => {
      if (!mountedRef.current) return
      setStatus('disconnected')
      wsRef.current = null

      if (reconnectCount.current < maxReconnects) {
        reconnectCount.current++
        reconnectTimer.current = setTimeout(() => {
          if (mountedRef.current) connect()
        }, reconnectDelay)
      }
    }
  }, [url, onMessage, reconnectDelay, maxReconnects])

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }
    reconnectCount.current = maxReconnects // stop auto-reconnect
    wsRef.current?.close()
    wsRef.current = null
    setStatus('disconnected')
  }, [maxReconnects])

  const send = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      disconnect()
    }
  }, [connect, disconnect])

  return { status, connect, disconnect, send }
}
