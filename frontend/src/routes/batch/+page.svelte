<!-- Batch Generation Page -->
<script lang="ts">
  import { batchGenerate, getBatchStatus, getBatchZipUrl, getAudioUrl } from '$lib/api/tts';
  import { models } from '$stores/models';
  import AudioPlayer from '$components/AudioPlayer.svelte';
  import { addToast } from '$lib/stores/toasts';

  let textInput = $state('');
  let selectedModelId = $state('');
  let outputFormat = $state('wav');
  let language = $state('en');

  let batchId = $state<string | null>(null);
  let batchJobs = $state<Array<{
    id: string;
    text: string;
    status: string;
    duration_seconds: number | null;
    processing_time_ms: number | null;
  }>>([]);
  let batchComplete = $state(false);
  let generating = $state(false);
  let pollInterval: ReturnType<typeof setInterval>;

  let fileInputEl = $state<HTMLInputElement | undefined>(undefined);

  const lines = $derived(
    textInput.split('\n').map((l) => l.trim()).filter((l) => l.length > 0)
  );

  // Initialize selectedModelId from first available model
  $effect(() => {
    if (models.length > 0 && !selectedModelId) {
      selectedModelId = models[0].id;
    }
  });

  async function handleFileUpload(file: File | null | undefined) {
    if (!file) return;
    const text = await file.text();
    textInput = text;
  }

  async function handleGenerate() {
    if (lines.length === 0) {
      addToast('warning', 'Enter at least one line of text');
      return;
    }
    if (lines.length > 100) {
      addToast('error', 'Maximum 100 lines per batch');
      return;
    }
    generating = true;
    batchComplete = false;
    batchJobs = lines.map((text, i) => ({
      id: `pending-${i}`,
      text,
      status: 'pending',
      duration_seconds: null,
      processing_time_ms: null,
    }));

    try {
      const result = await batchGenerate({
        lines,
        model_id: selectedModelId,
        language,
        output_format: outputFormat as 'wav' | 'mp3' | 'ogg',
      });
      batchId = result.batch_id;
      pollInterval = setInterval(pollBatch, 2000);
    } catch {
      addToast('error', 'Failed to start batch generation');
      generating = false;
    }
  }

  async function pollBatch() {
    if (!batchId) return;
    try {
      const status = await getBatchStatus(batchId);
      batchJobs = status.jobs.map((j: { id: string; text: string; status: string; duration_seconds: number | null; processing_time_ms: number | null }) => ({
        id: j.id,
        text: j.text,
        status: j.status,
        duration_seconds: j.duration_seconds,
        processing_time_ms: j.processing_time_ms,
      }));
      const allDone = status.jobs.every((j: { status: string }) =>
        j.status === 'complete' || j.status === 'failed' || j.status === 'cancelled'
      );
      if (allDone) {
        clearInterval(pollInterval);
        generating = false;
        batchComplete = true;
        const completed = (status.status_counts as Record<string, number>)['complete'] ?? 0;
        addToast('success', `Batch complete: ${completed}/${status.total} succeeded`);
      }
    } catch {
      // Non-fatal polling error — keep trying
    }
  }

  function reset() {
    batchId = null;
    batchJobs = [];
    batchComplete = false;
    generating = false;
    clearInterval(pollInterval);
  }

  const completedCount = $derived(batchJobs.filter((j) => j.status === 'complete').length);

  const STATUS_COLORS: Record<string, string> = {
    complete: 'text-green-400',
    running: 'text-blue-400',
    pending: 'text-yellow-400',
    failed: 'text-red-400',
    cancelled: 'text-gray-500',
  };
</script>

<svelte:head><title>Batch Generation — OpenSpeakers</title></svelte:head>

<div class="max-w-4xl mx-auto p-6">
  <h1 class="text-2xl font-bold text-white mb-2">Batch Generation</h1>
  <p class="text-gray-400 text-sm mb-6">Generate audio for multiple lines of text at once. One line = one job.</p>

  {#if !batchId}
    <!-- Input form -->
    <div class="space-y-4">
      <!-- Text input area -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label for="batch-text" class="text-sm font-medium text-gray-300">Text lines</label>
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-500">{lines.length} line{lines.length !== 1 ? 's' : ''}</span>
            <button
              onclick={() => fileInputEl?.click()}
              class="text-xs text-primary-400 hover:text-primary-300 transition-colors"
            >Upload .txt file</button>
            <input
              bind:this={fileInputEl}
              type="file"
              accept=".txt"
              class="hidden"
              onchange={(e) => handleFileUpload(e.currentTarget.files?.[0])}
            />
          </div>
        </div>
        <textarea
          id="batch-text"
          bind:value={textInput}
          placeholder="Enter one line of text per audio file to generate...&#10;&#10;Line 1 becomes audio file 1&#10;Line 2 becomes audio file 2&#10;(Maximum 100 lines)"
          rows={10}
          class="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none resize-none font-mono text-sm"
        ></textarea>
      </div>

      <!-- Controls row -->
      <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
        <!-- Model -->
        <div>
          <label for="batch-model" class="text-xs text-gray-400 mb-1 block">Model</label>
          <select
            id="batch-model"
            bind:value={selectedModelId}
            class="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none"
          >
            {#each models as m}
              <option value={m.id}>{m.name}</option>
            {/each}
          </select>
        </div>

        <!-- Language -->
        <div>
          <label for="batch-language" class="text-xs text-gray-400 mb-1 block">Language</label>
          <select
            id="batch-language"
            bind:value={language}
            class="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none"
          >
            <option value="en">English</option>
            <option value="de">German</option>
            <option value="fr">French</option>
            <option value="es">Spanish</option>
            <option value="it">Italian</option>
            <option value="pt">Portuguese</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="zh">Chinese</option>
          </select>
        </div>

        <!-- Output format -->
        <div>
          <label for="batch-format" class="text-xs text-gray-400 mb-1 block">Format</label>
          <select
            id="batch-format"
            bind:value={outputFormat}
            class="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none"
          >
            <option value="wav">WAV</option>
            <option value="mp3">MP3</option>
            <option value="ogg">OGG</option>
          </select>
        </div>
      </div>

      <button
        disabled={lines.length === 0 || lines.length > 100}
        onclick={handleGenerate}
        class="w-full py-3 rounded-xl font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed bg-primary-600 hover:bg-primary-700 text-white"
      >Generate {lines.length} Audio File{lines.length !== 1 ? 's' : ''}</button>
    </div>
  {:else}
    <!-- Progress table -->
    <div class="mb-4 flex items-center justify-between">
      <div class="text-sm text-gray-400">
        {completedCount} / {batchJobs.length} complete
        {#if generating}<span class="text-blue-400 ml-2">● Generating…</span>{/if}
      </div>
      <div class="flex gap-2">
        {#if batchComplete && completedCount > 0}
          <a
            href={getBatchZipUrl(batchId)}
            download
            class="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
          >Download All as ZIP</a>
        {/if}
        <button
          onclick={reset}
          class="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white text-sm transition-colors"
        >New Batch</button>
      </div>
    </div>

    <div class="space-y-2">
      {#each batchJobs as job, i (job.id)}
        <div class="bg-gray-800 rounded-xl border border-gray-700 p-4">
          <div class="flex items-start gap-3">
            <span class="text-xs text-gray-500 shrink-0 w-6 text-right pt-0.5">{i + 1}</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-gray-300 break-words">{job.text}</p>
              {#if job.status === 'complete' && job.id && !job.id.startsWith('pending-')}
                <div class="mt-2">
                  <AudioPlayer src={getAudioUrl(job.id)} />
                </div>
              {/if}
            </div>
            <div class="shrink-0 text-right">
              <span class="text-xs font-medium {STATUS_COLORS[job.status] ?? 'text-gray-400'}">{job.status}</span>
              {#if job.duration_seconds}
                <p class="text-xs text-gray-500">{job.duration_seconds.toFixed(1)}s audio</p>
              {/if}
              {#if job.status === 'complete' && job.id && !job.id.startsWith('pending-')}
                <a
                  href={getAudioUrl(job.id)}
                  download
                  class="text-xs text-primary-400 hover:text-primary-300 transition-colors block mt-1"
                >Download</a>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
