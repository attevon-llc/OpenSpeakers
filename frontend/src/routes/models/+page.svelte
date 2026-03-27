<!-- Model Browser Page -->
<script lang="ts">
  import { onMount } from 'svelte';
  import type { ModelInfo } from '$lib/api/models';
  import { models, modelsLoading, modelsError, refreshModels } from '$stores/models';

  let filterStreaming = $state(false);
  let filterCloning = $state(false);
  let searchQuery = $state('');

  onMount(() => {
    // Always refresh on direct navigation (layout may not have loaded yet)
    refreshModels();
  });

  const filteredModels = $derived(
    models.filter((m) => {
      if (filterStreaming && !m.supports_streaming) return false;
      if (filterCloning && !m.supports_voice_cloning) return false;
      if (
        searchQuery &&
        !m.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !m.id.toLowerCase().includes(searchQuery.toLowerCase())
      ) return false;
      return true;
    })
  );

  const loadedModel = $derived(models.find((m) => m.status === 'loaded'));

  function getStatusBadge(status: string): string {
    if (status === 'loaded') return 'bg-green-900/50 text-green-300 border border-green-700';
    if (status === 'loading') return 'bg-blue-900/50 text-blue-300 border border-blue-700 animate-pulse';
    return 'bg-gray-700/50 text-gray-400 border border-gray-600';
  }

  function vramColor(gb: number): string {
    if (gb <= 4) return 'bg-green-500';
    if (gb <= 12) return 'bg-yellow-500';
    return 'bg-red-500';
  }
</script>

<svelte:head><title>Models — OpenSpeakers</title></svelte:head>

<div class="max-w-5xl mx-auto p-6">
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold text-white">Models</h1>
      {#if loadedModel}
        <p class="text-sm text-gray-400 mt-1">Currently loaded: <span class="text-green-400">{loadedModel.name}</span></p>
      {:else}
        <p class="text-sm text-gray-400 mt-1">No model currently loaded in GPU</p>
      {/if}
    </div>
    <div class="flex items-center gap-3">
      <span class="text-sm text-gray-500">{models.length} registered model{models.length !== 1 ? 's' : ''}</span>
      <button
        onclick={refreshModels}
        disabled={modelsLoading()}
        class="px-3 py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-white text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
      >
        {#if modelsLoading()}
          <span class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block"></span>
        {:else}
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        {/if}
        Refresh
      </button>
    </div>
  </div>

  {#if modelsError()}
    <div class="mb-4 flex items-center gap-3 p-3 rounded-lg bg-red-900/20 border border-red-700/50 text-sm text-red-300">
      <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {modelsError()}
      <button onclick={refreshModels} class="ml-auto text-xs underline hover:no-underline">Retry</button>
    </div>
  {/if}

  <!-- Filters -->
  <div class="flex flex-wrap gap-3 mb-6">
    <input
      type="text"
      placeholder="Search models…"
      bind:value={searchQuery}
      class="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 focus:border-primary-500 focus:outline-none"
    />
    <label class="flex items-center gap-2 text-sm text-gray-300 cursor-pointer select-none">
      <input type="checkbox" bind:checked={filterStreaming} class="accent-primary-500" />
      Streaming
    </label>
    <label class="flex items-center gap-2 text-sm text-gray-300 cursor-pointer select-none">
      <input type="checkbox" bind:checked={filterCloning} class="accent-primary-500" />
      Voice Cloning
    </label>
  </div>

  {#if modelsLoading() && models.length === 0}
    <div class="flex justify-center py-12 text-gray-400 gap-2">
      <span class="w-4 h-4 border-2 border-gray-400/30 border-t-gray-400 rounded-full animate-spin inline-block"></span>
      Loading models…
    </div>
  {:else if filteredModels.length === 0}
    <div class="text-center py-12 text-gray-400">
      {#if models.length === 0}
        No models found. <button onclick={refreshModels} class="text-primary-400 hover:text-primary-300 underline">Try refreshing</button>
      {:else}
        No models match your filters
      {/if}
    </div>
  {:else}
    <div class="grid gap-4 md:grid-cols-2">
      {#each filteredModels as model (model.id)}
        <div class="bg-gray-800 rounded-xl border border-gray-700 p-5 flex flex-col gap-3">
          <!-- Header -->
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <h2 class="font-semibold text-white truncate">{model.name}</h2>
              <p class="text-xs text-gray-500 font-mono">{model.id}</p>
            </div>
            <span class="text-xs px-2 py-0.5 rounded shrink-0 {getStatusBadge(model.status)}">{model.status}</span>
          </div>

          <!-- Description -->
          <p class="text-sm text-gray-400 leading-relaxed">{model.description}</p>

          <!-- VRAM bar -->
          <div>
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>VRAM</span>
              <span>{model.vram_gb_estimate} GB</span>
            </div>
            <div class="h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all {vramColor(model.vram_gb_estimate)}"
                style="width: {Math.min(100, (model.vram_gb_estimate / 24) * 100)}%"
              ></div>
            </div>
          </div>

          <!-- Capability chips -->
          <div class="flex flex-wrap gap-1.5">
            {#if model.supports_streaming}
              <span class="text-xs bg-blue-900/40 text-blue-300 border border-blue-700/50 px-2 py-0.5 rounded-full">Streaming</span>
            {/if}
            {#if model.supports_voice_cloning}
              <span class="text-xs bg-teal-900/40 text-teal-300 border border-teal-700/50 px-2 py-0.5 rounded-full">Voice Cloning</span>
            {/if}
            {#if (model as ModelInfo & { supports_speed?: boolean }).supports_speed}
              <span class="text-xs bg-gray-700 text-gray-300 border border-gray-600 px-2 py-0.5 rounded-full">Speed Control</span>
            {/if}
            {#if (model as ModelInfo & { supports_pitch?: boolean }).supports_pitch}
              <span class="text-xs bg-gray-700 text-gray-300 border border-gray-600 px-2 py-0.5 rounded-full">Pitch Control</span>
            {/if}
          </div>

          <!-- Languages -->
          {#if model.supported_languages?.length > 0}
            <p class="text-xs text-gray-500">
              Languages: {model.supported_languages.slice(0, 5).join(', ')}{model.supported_languages.length > 5 ? ` +${model.supported_languages.length - 5} more` : ''}
            </p>
          {/if}

          <!-- HF link -->
          {#if model.hf_repo}
            <a
              href="https://huggingface.co/{model.hf_repo}"
              target="_blank"
              rel="noopener noreferrer"
              class="text-xs text-primary-400 hover:text-primary-300 transition-colors"
            >HuggingFace: {model.hf_repo} ↗</a>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
