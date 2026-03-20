<!-- TTS Generation Page -->
<script lang="ts">
  import { onMount } from 'svelte';
  import ModelSelector from '$components/ModelSelector.svelte';
  import AudioPlayer from '$components/AudioPlayer.svelte';
  import JobProgress from '$components/JobProgress.svelte';
  import { models, refreshModels } from '$stores/models';
  import { recentJobs, addOrUpdateJob } from '$stores/jobs';
  import { generateTTS, getAudioUrl, pollJob, type TTSJob } from '$api/tts';
  import { listBuiltinVoices, listVoices, type BuiltinVoice, type VoiceProfile } from '$api/voices';

  let selectedModel = '';
  let text = '';
  let selectedVoiceId: string | null = null;
  let speed = 1.0;
  let pitch = 0.0;
  let language = 'en';

  let generating = false;
  let currentJob: TTSJob | null = null;
  let audioUrl = '';
  let audioDuration: number | null = null;
  let errorMessage = '';

  let builtinVoices: BuiltinVoice[] = [];
  let clonedVoices: VoiceProfile[] = [];

  const LANGUAGES = [
    { code: 'en', name: 'English' }, { code: 'de', name: 'German' },
    { code: 'fr', name: 'French' }, { code: 'es', name: 'Spanish' },
    { code: 'it', name: 'Italian' }, { code: 'pt', name: 'Portuguese' },
    { code: 'ja', name: 'Japanese' }, { code: 'ko', name: 'Korean' },
    { code: 'zh', name: 'Chinese' }, { code: 'nl', name: 'Dutch' },
  ];

  onMount(() => refreshModels());

  $: if (selectedModel) {
    loadVoices(selectedModel);
  }

  async function loadVoices(modelId: string): Promise<void> {
    const [builtin, cloned] = await Promise.all([
      listBuiltinVoices(modelId).catch(() => []),
      listVoices(modelId).then((r) => r.voices).catch(() => []),
    ]);
    builtinVoices = builtin;
    clonedVoices = cloned;
    selectedVoiceId = null;
  }

  async function handleGenerate(): Promise<void> {
    if (!selectedModel || !text.trim() || generating) return;

    generating = true;
    errorMessage = '';
    audioUrl = '';
    audioDuration = null;
    currentJob = null;

    try {
      const resp = await generateTTS({
        model_id: selectedModel,
        text: text.trim(),
        voice_id: selectedVoiceId,
        speed,
        pitch,
        language,
      });

      // Seed a minimal job object so progress component can connect immediately
      currentJob = {
        id: resp.job_id,
        model_id: selectedModel,
        text: text.trim(),
        voice_id: selectedVoiceId,
        voice_profile_id: null,
        parameters: { speed, pitch, language },
        status: 'pending',
        error_message: null,
        output_path: null,
        duration_seconds: null,
        processing_time_ms: null,
        created_at: new Date().toISOString(),
        completed_at: null,
      };
      addOrUpdateJob(currentJob);

      // WebSocket handles progress; fallback-poll in case WS fails
      await pollJob(resp.job_id, (job) => {
        currentJob = job;
        addOrUpdateJob(job);
      });
    } catch (err) {
      errorMessage = err instanceof Error ? err.message : 'Generation failed';
    } finally {
      generating = false;
    }
  }

  function handleProgressComplete(url: string, dur: number): void {
    audioUrl = url;
    audioDuration = dur;
    if (currentJob) currentJob = { ...currentJob, status: 'complete' };
  }

  function handleProgressError(msg: string): void {
    errorMessage = msg;
    generating = false;
  }
</script>

<div class="p-6 max-w-4xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-bold">Text to Speech</h1>
    <p class="text-gray-500 dark:text-gray-400 mt-1 text-sm">Generate speech from text using open-source models.</p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Left: controls -->
    <div class="lg:col-span-2 space-y-4">

      <!-- Model selection -->
      <div class="card p-4 space-y-3">
        <h2 class="font-semibold text-sm text-gray-700 dark:text-gray-300">Model</h2>
        <ModelSelector models={$models} bind:value={selectedModel} disabled={generating} />
      </div>

      <!-- Text input -->
      <div class="card p-4 space-y-2">
        <label class="label" for="tts-text">Text</label>
        <textarea
          id="tts-text"
          bind:value={text}
          rows={5}
          placeholder="Enter the text you want to synthesize…"
          disabled={generating}
          class="input resize-none"
          maxlength={4096}
        ></textarea>
        <div class="text-xs text-gray-400 text-right">{text.length} / 4096</div>
      </div>

      <!-- Voice selection -->
      {#if builtinVoices.length > 0 || clonedVoices.length > 0}
        <div class="card p-4 space-y-2">
          <label class="label" for="voice-select">Voice</label>
          <select id="voice-select" bind:value={selectedVoiceId} disabled={generating} class="input">
            <option value={null}>Default voice</option>
            {#if builtinVoices.length > 0}
              <optgroup label="Built-in voices">
                {#each builtinVoices as v}
                  <option value={v.id}>{v.name} ({v.language}{v.gender ? ', ' + v.gender : ''})</option>
                {/each}
              </optgroup>
            {/if}
            {#if clonedVoices.length > 0}
              <optgroup label="My cloned voices">
                {#each clonedVoices as v}
                  <option value={v.id}>{v.name}</option>
                {/each}
              </optgroup>
            {/if}
          </select>
        </div>
      {/if}

      <!-- Parameters -->
      <div class="card p-4 space-y-4">
        <h2 class="font-semibold text-sm text-gray-700 dark:text-gray-300">Parameters</h2>
        <div class="grid grid-cols-3 gap-4">
          <!-- Speed -->
          <div>
            <label class="label" for="speed">Speed: {speed.toFixed(1)}×</label>
            <input id="speed" type="range" min="0.5" max="2.0" step="0.1"
              bind:value={speed} disabled={generating} class="w-full accent-primary-500" />
          </div>
          <!-- Pitch -->
          <div>
            <label class="label" for="pitch">Pitch: {pitch > 0 ? '+' : ''}{pitch} st</label>
            <input id="pitch" type="range" min="-12" max="12" step="1"
              bind:value={pitch} disabled={generating} class="w-full accent-primary-500" />
          </div>
          <!-- Language -->
          <div>
            <label class="label" for="language">Language</label>
            <select id="language" bind:value={language} disabled={generating} class="input">
              {#each LANGUAGES as lang}
                <option value={lang.code}>{lang.name}</option>
              {/each}
            </select>
          </div>
        </div>
      </div>

      <!-- Generate button -->
      <button
        on:click={handleGenerate}
        disabled={!selectedModel || !text.trim() || generating}
        class="btn-primary w-full py-3 text-base"
      >
        {#if generating}
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Generating…
        {:else}
          Generate Speech
        {/if}
      </button>
    </div>

    <!-- Right: result + history -->
    <div class="space-y-4">

      <!-- Result / Progress -->
      <div class="card p-4 space-y-3">
        <h2 class="font-semibold text-sm text-gray-700 dark:text-gray-300">Output</h2>

        {#if errorMessage}
          <div class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            {errorMessage}
          </div>
        {/if}

        <!-- Live progress via WebSocket -->
        <JobProgress
          job={currentJob}
          onComplete={handleProgressComplete}
          onError={handleProgressError}
        />

        <!-- Audio player (shown once complete) -->
        <AudioPlayer src={audioUrl} duration={audioDuration} />

        {#if audioDuration}
          <p class="text-xs text-gray-400">
            Duration: {audioDuration.toFixed(1)}s
            {#if currentJob?.processing_time_ms}
              · Generated in {(currentJob.processing_time_ms / 1000).toFixed(1)}s
            {/if}
          </p>
        {/if}
      </div>

      <!-- Job history -->
      <div class="card p-4 space-y-2">
        <h2 class="font-semibold text-sm text-gray-700 dark:text-gray-300">Recent Jobs</h2>
        {#if $recentJobs.length === 0}
          <p class="text-xs text-gray-400">No jobs yet.</p>
        {:else}
          <ul class="space-y-1.5">
            {#each $recentJobs.slice(0, 8) as job (job.id)}
              <li class="flex items-center gap-2 text-xs">
                <span class="w-2 h-2 rounded-full flex-shrink-0
                  {job.status === 'complete' ? 'bg-green-500' :
                   job.status === 'failed' ? 'bg-red-500' :
                   job.status === 'running' ? 'bg-yellow-500 animate-pulse' : 'bg-gray-400'}">
                </span>
                <span class="flex-1 truncate text-gray-600 dark:text-gray-300">{job.text.slice(0, 40)}{job.text.length > 40 ? '…' : ''}</span>
                {#if job.status === 'complete'}
                  <a href={getAudioUrl(job.id)} class="text-primary-500 hover:underline flex-shrink-0">play</a>
                {/if}
              </li>
            {/each}
          </ul>
        {/if}
      </div>
    </div>
  </div>
</div>
