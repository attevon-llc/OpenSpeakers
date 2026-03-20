<!-- Model Comparison Page — generate the same text with multiple models side-by-side -->
<script lang="ts">
  import { onMount } from 'svelte';
  import AudioPlayer from '$components/AudioPlayer.svelte';
  import { models, refreshModels } from '$stores/models';
  import { generateTTS, getAudioUrl, pollJob, type TTSJob } from '$api/tts';
  import type { ModelInfo } from '$api/models';

  let text = 'The quick brown fox jumps over the lazy dog.';
  let selectedModelIds: string[] = [];
  let speed = 1.0;
  let language = 'en';

  interface ComparisonResult {
    model: ModelInfo;
    status: 'idle' | 'pending' | 'running' | 'complete' | 'failed';
    audioUrl: string;
    duration: number | null;
    processingMs: number | null;
    error: string | null;
  }

  let results: ComparisonResult[] = [];
  let generating = false;

  onMount(refreshModels);

  $: allModels = $models;

  function toggleModel(modelId: string): void {
    if (selectedModelIds.includes(modelId)) {
      selectedModelIds = selectedModelIds.filter((id) => id !== modelId);
    } else if (selectedModelIds.length < 4) {
      selectedModelIds = [...selectedModelIds, modelId];
    }
  }

  async function handleCompare(): Promise<void> {
    if (!text.trim() || selectedModelIds.length < 1 || generating) return;
    generating = true;

    results = selectedModelIds
      .map((id) => allModels.find((m) => m.id === id)!)
      .filter(Boolean)
      .map((model) => ({
        model,
        status: 'pending' as const,
        audioUrl: '',
        duration: null,
        processingMs: null,
        error: null,
      }));

    // Launch all generations in parallel
    await Promise.all(
      results.map(async (_, idx) => {
        try {
          const resp = await generateTTS({
            model_id: results[idx].model.id,
            text: text.trim(),
            speed,
            language,
          });
          results[idx] = { ...results[idx], status: 'running' };
          results = [...results];

          const finalJob = await pollJob(resp.job_id, (job) => {
            results[idx] = { ...results[idx], status: job.status as ComparisonResult['status'] };
            results = [...results];
          });

          results[idx] = {
            ...results[idx],
            status: 'complete',
            audioUrl: getAudioUrl(finalJob.id),
            duration: finalJob.duration_seconds,
            processingMs: finalJob.processing_time_ms,
          };
          results = [...results];
        } catch (err) {
          results[idx] = {
            ...results[idx],
            status: 'failed',
            error: err instanceof Error ? err.message : 'Failed',
          };
          results = [...results];
        }
      })
    );

    generating = false;
  }
</script>

<div class="p-6 max-w-5xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-bold">Model Comparison</h1>
    <p class="text-gray-500 dark:text-gray-400 mt-1 text-sm">Generate the same text with multiple models to compare quality.</p>
  </div>

  <!-- Setup -->
  <div class="card p-5 space-y-4">
    <div>
      <label class="label" for="compare-text">Text (shared across all models)</label>
      <textarea id="compare-text" bind:value={text} rows={3}
        class="input resize-none" disabled={generating}></textarea>
    </div>

    <div>
      <p class="label">Select models to compare (up to 4)</p>
      <div class="flex flex-wrap gap-2 mt-1">
        {#each allModels as model}
          <button
            on:click={() => toggleModel(model.id)}
            class="px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors
              {selectedModelIds.includes(model.id)
                ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-gray-300'}"
            disabled={generating || (!selectedModelIds.includes(model.id) && selectedModelIds.length >= 4)}
          >
            {model.name}
          </button>
        {/each}
      </div>
    </div>

    <div class="flex gap-6 items-end">
      <div>
        <label class="label" for="cmp-speed">Speed: {speed.toFixed(1)}×</label>
        <input id="cmp-speed" type="range" min="0.5" max="2.0" step="0.1"
          bind:value={speed} disabled={generating} class="w-32 accent-primary-500" />
      </div>
      <button
        on:click={handleCompare}
        disabled={!text.trim() || selectedModelIds.length === 0 || generating}
        class="btn-primary"
      >
        {#if generating}
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Generating…
        {:else}
          Compare {selectedModelIds.length} Model{selectedModelIds.length !== 1 ? 's' : ''}
        {/if}
      </button>
    </div>
  </div>

  <!-- Results grid -->
  {#if results.length > 0}
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {#each results as result (result.model.id)}
        <div class="card p-4 space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">{result.model.name}</h3>
            <span class="text-xs px-2 py-0.5 rounded-full
              {result.status === 'complete' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
               result.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
               'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'}">
              {result.status}
            </span>
          </div>

          {#if result.status === 'running' || result.status === 'pending'}
            <div class="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div class="h-full bg-primary-500 rounded-full animate-pulse" style="width: 60%"></div>
            </div>
          {/if}

          {#if result.status === 'complete'}
            <AudioPlayer src={result.audioUrl} duration={result.duration} />
            <div class="flex gap-4 text-xs text-gray-400">
              {#if result.duration}<span>{result.duration.toFixed(1)}s audio</span>{/if}
              {#if result.processingMs}<span>{(result.processingMs / 1000).toFixed(1)}s generation</span>{/if}
            </div>
          {:else if result.status === 'failed'}
            <p class="text-sm text-red-500">{result.error}</p>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
