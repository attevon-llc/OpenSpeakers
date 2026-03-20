/**
 * WebSocket client for real-time TTS job progress updates.
 *
 * Connects to ws://<host>/ws/jobs/<job_id> and streams progress events:
 *   - { type: "status", status: "running", detail: "Loading model..." }
 *   - { type: "progress", step: "model_loading", percent: 45, eta_seconds: 12 }
 *   - { type: "progress", step: "generating", percent: 72, eta_seconds: 3 }
 *   - { type: "complete", job_id: "...", audio_url: "/api/tts/jobs/.../audio", duration: 4.2 }
 *   - { type: "error", message: "..." }
 */

export type ProgressStep = 'queued' | 'model_loading' | 'generating' | 'complete' | 'error';

export interface ProgressEvent {
  type: 'status' | 'progress' | 'complete' | 'error';
  step?: ProgressStep;
  status?: string;
  detail?: string;
  percent?: number;
  eta_seconds?: number;
  job_id?: string;
  audio_url?: string;
  duration?: number;
  message?: string;
}

export type ProgressCallback = (event: ProgressEvent) => void;

export class JobProgressSocket {
  private ws: WebSocket | null = null;
  private jobId: string;
  private onProgress: ProgressCallback;
  private reconnectAttempts = 0;
  private maxReconnects = 3;

  constructor(jobId: string, onProgress: ProgressCallback) {
    this.jobId = jobId;
    this.onProgress = onProgress;
  }

  connect(): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/jobs/${this.jobId}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ProgressEvent;
        this.onProgress(data);
        if (data.type === 'complete' || data.type === 'error') {
          this.disconnect();
        }
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = (event) => {
      if (!event.wasClean && this.reconnectAttempts < this.maxReconnects) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
      }
    };

    this.ws.onerror = () => {
      this.onProgress({ type: 'error', message: 'WebSocket connection failed' });
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
