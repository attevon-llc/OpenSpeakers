<!-- Real-time job progress using WebSocket.
     Shows spinner -> model loading bar -> generation bar -> complete.
     Never shows a blank "waiting" state to the user. -->
<script lang="ts">
  import { JobProgressSocket, type ProgressEvent, type ProgressStep } from '$lib/api/ws';
  import type { TTSJob } from '$api/tts';

  let {
    job = null,
    onComplete = (_audioUrl: string, _duration: number) => {},
    onError = (_message: string) => {},
    onChunk = (_data: string, _sampleRate: number, _index: number) => {},
    onCancel = undefined,
  }: {
    job?: TTSJob | null;
    onComplete?: (audioUrl: string, duration: number) => void;
    onError?: (message: string) => void;
    onChunk?: (data: string, sampleRate: number, index: number) => void;
    onCancel?: () => void;
  } = $props();

  let step: ProgressStep = $state('queued');
  let percent = $state(0);
  let etaSeconds: number | null = $state(null);
  let detail = $state('Job queued, waiting for worker...');
  // Not $state — socket is internal lifecycle management only, not used in the template.
  // Using $state here caused Effect 2 to track it (via startSocket reading socket?.disconnect()),
  // creating an infinite re-run loop every time the socket was set.
  let socket: JobProgressSocket | null = null;

  // Tracks which job the socket is currently open for.
  // Only changes when a genuinely new job arrives — NOT on every status update.
  let socketJobId = $state<string | null>(null);

  // Effect 1: detect a new job ID (ignores status-only updates from pollJob).
  $effect(() => {
    const id = job?.id ?? null;
    if (id && id !== socketJobId && job?.status !== 'complete' && job?.status !== 'failed') {
      socketJobId = id;
    }
  });

  // Effect 2: open/close the socket only when the job ID itself changes.
  // socket is NOT $state so reading it here does not create a tracking dependency.
  $effect(() => {
    const id = socketJobId;
    if (!id) return;

    startSocket(id);
    return () => {
      socket?.disconnect();
    };
  });

  // Effect 3: fallback — fire onComplete/onError from the job prop when WS misses it.
  $effect(() => {
    if (!job) return;
    if (job.status === 'complete' && step !== 'complete') {
      step = 'complete';
      percent = 100;
      detail = 'Generation complete!';
      onComplete(`/api/tts/jobs/${job.id}/audio`, job.duration_seconds ?? 0);
    } else if (job.status === 'failed' && step !== 'error') {
      step = 'error';
      detail = job.error_message ?? 'Generation failed';
      onError(detail);
    }
  });

  function startSocket(jobId: string): void {
    socket?.disconnect();
    step = 'queued';
    percent = 0;
    detail = 'Job queued, waiting for worker...';

    socket = new JobProgressSocket(jobId, handleProgress);
    socket.connect();
  }

  function handleProgress(event: ProgressEvent): void {
    if (event.type === 'progress') {
      step = event.step ?? 'generating';
      percent = event.percent ?? percent;
      etaSeconds = event.eta_seconds ?? null;
      detail = stepLabel(step, percent);
    } else if (event.type === 'status') {
      detail = event.detail ?? stepLabel(step, percent);
    } else if (event.type === 'audio_chunk' && event.chunk_data) {
      onChunk(event.chunk_data, event.sample_rate ?? 24000, event.chunk_index ?? 0);
    } else if (event.type === 'complete') {
      step = 'complete';
      percent = 100;
      detail = 'Generation complete!';
      const audioUrl = event.audio_url ?? `/api/tts/jobs/${job?.id}/audio`;
      onComplete(audioUrl, event.duration ?? 0);
    } else if (event.type === 'error') {
      step = 'error';
      detail = event.message ?? 'Generation failed';
      onError(detail);
    }
  }

  function stepLabel(s: ProgressStep, pct: number): string {
    if (s === 'queued') return 'Job queued, waiting for worker...';
    if (s === 'model_loading') return `Loading model... ${pct}%`;
    if (s === 'generating') return `Generating audio... ${pct}%`;
    if (s === 'complete') return 'Generation complete!';
    if (s === 'error') return 'Generation failed';
    return 'Processing...';
  }

  function barColor(s: ProgressStep): string {
    if (s === 'error') return 'bg-red-500';
    if (s === 'complete') return 'bg-green-500';
    return 'bg-primary-500';
  }
</script>

{#if job && job.status !== 'complete' && job.status !== 'failed'}
  <div class="space-y-2" role="status" aria-live="polite">
    <!-- Status line -->
    <div class="flex items-center gap-2 text-sm">
      {#if step !== 'complete' && step !== 'error'}
        <svg class="w-4 h-4 animate-spin text-primary-500 flex-shrink-0" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      {/if}
      <span class="text-gray-600 dark:text-gray-300 flex-1">{detail}</span>
      {#if etaSeconds !== null && etaSeconds > 0}
        <span class="text-gray-400 text-xs">~{etaSeconds}s</span>
      {/if}
      {#if onCancel && (job?.status === 'pending' || job?.status === 'running' || step === 'queued' || step === 'model_loading' || step === 'generating')}
        <button
          type="button"
          onclick={onCancel}
          class="flex-shrink-0 ml-1 px-2 py-0.5 text-xs font-medium rounded
                 bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300
                 border border-red-500/20 hover:border-red-500/40 transition-colors"
          aria-label="Cancel job"
        >
          Cancel
        </button>
      {/if}
    </div>

    <!-- Progress bar -->
    <div class="h-1.5 bg-gray-200 dark:bg-[#2a2a2f] rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-300 {barColor(step)}"
        style="width: {step === 'queued' ? 3 : percent}%"
      ></div>
    </div>

    <!-- Step indicators -->
    <div class="flex flex-wrap items-center gap-x-1 gap-y-0.5 text-xs text-gray-400 dark:text-gray-600">
      {#each ([ ['queued','Queue'], ['model_loading','Load'], ['generating','Generate'], ['complete','Done'] ] as const) as [s, label], i}
        {#if i > 0}<span class="text-gray-300 dark:text-gray-700 select-none">›</span>{/if}
        <span
          class:text-primary-500={step === s && s !== 'complete'}
          class:text-green-500={s === 'complete' && step === 'complete'}
          class:font-medium={step === s}
        >{label}</span>
      {/each}
    </div>
  </div>
{/if}
