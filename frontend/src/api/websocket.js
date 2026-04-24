import { WS_URL, WS_RECONNECT_DELAY_MS, WS_MAX_RECONNECT_ATTEMPTS } from '../config'

export class LiveSocket {
  constructor({ onEvent, onStatusChange } = {}) {
    this.onEvent = onEvent || (() => {})
    this.onStatusChange = onStatusChange || (() => {})
    this.ws = null
    this.reconnectAttempts = 0
    this.shouldReconnect = true
    this.pingInterval = null
  }

  connect() {
    this.shouldReconnect = true
    this._open()
  }

  _open() {
    this.onStatusChange('connecting')
    try {
      this.ws = new WebSocket(WS_URL)
    } catch {
      this.onStatusChange('error')
      this._scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.onStatusChange('connected')
      this.pingInterval = setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) this.ws.send('ping')
      }, 25000)
    }

    this.ws.onmessage = (e) => {
      if (e.data === 'pong') return
      try {
        const event = JSON.parse(e.data)
        this.onEvent(event)
      } catch (err) {
        console.warn('WS parse error', err)
      }
    }

    this.ws.onclose = () => {
      this._cleanupPing()
      this.onStatusChange('disconnected')
      if (this.shouldReconnect) this._scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.onStatusChange('error')
    }
  }

  _scheduleReconnect() {
    if (this.reconnectAttempts >= WS_MAX_RECONNECT_ATTEMPTS) {
      this.onStatusChange('failed')
      return
    }
    this.reconnectAttempts++
    const delay = WS_RECONNECT_DELAY_MS * Math.min(this.reconnectAttempts, 5)
    setTimeout(() => this._open(), delay)
  }

  _cleanupPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  disconnect() {
    this.shouldReconnect = false
    this._cleanupPing()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}
