/**
 * ShopStream WebSocket Client
 *
 * WebSocket client for receiving real-time metrics updates.
 * Automatically reconnects on disconnection.
 */

const WS_BASE_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace('http', 'ws')
  : 'ws://localhost:8000';

class WebSocketClient {
  constructor() {
    this.ws = null;
    this.url = `${WS_BASE_URL}/ws/metrics`;
    this.listeners = new Set();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 2000; // 2 seconds
    this.heartbeatInterval = null;
    this.isConnecting = false;
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      console.log('WebSocket: Already connected or connecting');
      return;
    }

    this.isConnecting = true;
    console.log(`WebSocket: Connecting to ${this.url}...`);

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket: Connected ✅');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.startHeartbeat();

        // Notify listeners of connection
        this.notifyListeners({
          type: 'connection',
          status: 'connected',
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket: Message received', data.type);

          // Notify all listeners
          this.notifyListeners(data);
        } catch (error) {
          console.error('WebSocket: Error parsing message', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket: Error', error);
        this.isConnecting = false;
      };

      this.ws.onclose = () => {
        console.log('WebSocket: Disconnected');
        this.isConnecting = false;
        this.stopHeartbeat();

        // Notify listeners of disconnection
        this.notifyListeners({
          type: 'connection',
          status: 'disconnected',
        });

        // Attempt to reconnect
        this.reconnect();
      };
    } catch (error) {
      console.error('WebSocket: Connection error', error);
      this.isConnecting = false;
      this.reconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stopHeartbeat();
  }

  /**
   * Reconnect with exponential backoff
   */
  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket: Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);

    console.log(`WebSocket: Reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Start sending heartbeat pings to keep connection alive
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // 30 seconds
  }

  /**
   * Stop heartbeat interval
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Send message to server
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket: Cannot send message, not connected');
    }
  }

  /**
   * Add listener for WebSocket messages
   */
  addListener(callback) {
    this.listeners.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Remove all listeners
   */
  removeAllListeners() {
    this.listeners.clear();
  }

  /**
   * Notify all listeners of new data
   */
  notifyListeners(data) {
    this.listeners.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error('WebSocket: Error in listener callback', error);
      }
    });
  }

  /**
   * Request immediate update from server
   */
  requestUpdate() {
    this.send({ type: 'request_update' });
  }
}

// Singleton instance
const wsClient = new WebSocketClient();

export default wsClient;
