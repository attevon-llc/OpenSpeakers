<!-- Settings Page -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { models, refreshModels } from '$stores/models';
  import type { ModelInfo } from '$api/models';
  import axiosInstance from '$lib/axios';

  interface SystemInfo {
    current_model: string | null;
    registered_models: string[];
    gpu: {
      available: boolean;
      device_id?: number;
      device_name?: string;
      vram_total_gb?: number;
      vram_used_gb?: number;
      vram_reserved_gb?: number;
      note?: string;
    };
    disk: {
      total_gb: number;
      used_gb: number;
      free_gb: number;
    };
    audio_output_dir: string;
    model_cache_dir: string;
  }

  let systemInfo: SystemInfo | null = null;
  let loadingInfo = false;

  onMount(async () => {
    await refreshModels();
    loadSystemInfo();
  });

  async function loadSystemInfo(): Promise<void> {
    loadingInfo = true;
    try {
      const res = await axiosInstance.get<SystemInfo>('/system/info');
      systemInfo = res.data;
    } catch {
      // Non-fatal
    } finally {
      loadingInfo = false;
    }
  }

  function vramPct(info: SystemInfo): number {
    if (!info.gpu.vram_total_gb || !info.gpu.vram_used_gb) return 0;
    return Math.round((info.gpu.vram_used_gb / info.gpu.vram_total_gb) * 100);
  }
</script>

<div class="p-6 max-w-3xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-bold">Settings</h1>
    <p class="text-gray-500 dark:text-gray-400 mt-1 text-sm">GPU info, model status, and system configuration.</p>
  </div>

  <!-- GPU status -->
  <div class="card p-5 space-y-3">
    <h2 class="font-semibold">GPU Status</h2>
    {#if loadingInfo}
      <p class="text-sm text-gray-400">Loading…</p>
    {:else if systemInfo?.gpu.available}
      <dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt class="text-gray-500">Device</dt>
        <dd>{systemInfo.gpu.device_name} (GPU {systemInfo.gpu.device_id})</dd>
        <dt class="text-gray-500">VRAM total</dt>
        <dd>{systemInfo.gpu.vram_total_gb} GB</dd>
        <dt class="text-gray-500">VRAM used</dt>
        <dd>
          {systemInfo.gpu.vram_used_gb} GB
          <span class="text-gray-400">({vramPct(systemInfo)}%)</span>
        </dd>
        <dt class="text-gray-500">Current model</dt>
        <dd>{systemInfo.current_model ?? 'None loaded'}</dd>
      </dl>

      <!-- VRAM bar -->
      <div>
        <div class="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden mt-2">
          <div
            class="h-full rounded-full transition-all {vramPct(systemInfo) > 80 ? 'bg-orange-500' : 'bg-primary-500'}"
            style="width: {vramPct(systemInfo)}%"
          ></div>
        </div>
        <p class="text-xs text-gray-400 mt-1">{vramPct(systemInfo)}% VRAM in use</p>
      </div>
    {:else if systemInfo}
      <p class="text-sm text-gray-500">
        No NVIDIA GPU detected.
        {systemInfo.gpu.note ?? ''}
        Models will run on CPU (slow).
      </p>
    {/if}
  </div>

  <!-- Models -->
  <div class="card p-5 space-y-3">
    <div class="flex items-center justify-between">
      <h2 class="font-semibold">Registered Models</h2>
      <button on:click={refreshModels} class="btn-secondary text-xs px-3 py-1.5">Refresh</button>
    </div>

    <ul class="divide-y divide-gray-100 dark:divide-gray-700">
      {#each $models as model (model.id)}
        <li class="py-3 flex items-start gap-3">
          <div class="mt-1 w-2 h-2 rounded-full flex-shrink-0
            {model.status === 'loaded' ? 'bg-green-500' :
             model.status === 'loading' ? 'bg-yellow-500 animate-pulse' : 'bg-gray-400'}">
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-medium text-sm">{model.name}</span>
              <span class="text-xs text-gray-400">{model.status}</span>
              {#if model.supports_voice_cloning}
                <span class="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">cloning</span>
              {/if}
            </div>
            <p class="text-xs text-gray-400 mt-0.5">{model.description}</p>
            <div class="flex gap-3 mt-1 text-xs text-gray-400">
              <span>~{model.vram_gb_estimate} GB VRAM</span>
              <span>{model.supported_languages.join(', ')}</span>
            </div>
          </div>
        </li>
      {/each}
    </ul>
  </div>

  <!-- Disk / Storage -->
  {#if systemInfo?.disk}
    <div class="card p-5 space-y-3">
      <h2 class="font-semibold">Storage</h2>
      <dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt class="text-gray-500">Audio output dir</dt>
        <dd class="font-mono text-xs truncate">{systemInfo.audio_output_dir}</dd>
        <dt class="text-gray-500">Model cache dir</dt>
        <dd class="font-mono text-xs truncate">{systemInfo.model_cache_dir}</dd>
        <dt class="text-gray-500">Disk free</dt>
        <dd>{systemInfo.disk.free_gb} GB of {systemInfo.disk.total_gb} GB</dd>
      </dl>
    </div>
  {/if}
</div>
