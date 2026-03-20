<!-- Voice Cloning Page -->
<script lang="ts">
  import { onMount } from 'svelte';
  import ModelSelector from '$components/ModelSelector.svelte';
  import AudioPlayer from '$components/AudioPlayer.svelte';
  import { models, voiceCloningModels, refreshModels } from '$stores/models';
  import { createVoiceProfile, listVoices, deleteVoiceProfile, type VoiceProfile } from '$api/voices';
  import { generateTTS, getAudioUrl, pollJob } from '$api/tts';

  let selectedModel = '';
  let voiceName = '';
  let referenceFile: File | null = null;
  let referenceAudioPreview = '';
  let uploading = false;
  let uploadError = '';
  let clonedVoices: VoiceProfile[] = [];
  let loadingVoices = false;

  // Preview generation
  let previewText = 'Hello, this is a test of my cloned voice.';
  let previewJob: { id: string; status: string } | null = null;
  let previewAudioUrl = '';
  let previewVoiceId: string | null = null;
  let generatingPreview = false;

  onMount(async () => {
    await refreshModels();
    await loadVoices();
    // Default to first cloning-capable model
    if ($voiceCloningModels.length > 0 && !selectedModel) {
      selectedModel = $voiceCloningModels[0].id;
    }
  });

  async function loadVoices(): Promise<void> {
    loadingVoices = true;
    try {
      const result = await listVoices(selectedModel || undefined);
      clonedVoices = result.voices;
    } finally {
      loadingVoices = false;
    }
  }

  function handleFileChange(e: Event): void {
    const input = e.currentTarget as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    referenceFile = file;
    if (file) {
      referenceAudioPreview = URL.createObjectURL(file);
    } else {
      referenceAudioPreview = '';
    }
  }

  async function handleCreate(): Promise<void> {
    if (!selectedModel || !voiceName.trim() || !referenceFile || uploading) return;
    uploading = true;
    uploadError = '';
    try {
      const profile = await createVoiceProfile(voiceName.trim(), selectedModel, referenceFile);
      clonedVoices = [profile, ...clonedVoices];
      voiceName = '';
      referenceFile = null;
      referenceAudioPreview = '';
    } catch (err) {
      uploadError = err instanceof Error ? err.message : 'Upload failed';
    } finally {
      uploading = false;
    }
  }

  async function handleDelete(voiceId: string): Promise<void> {
    if (!confirm('Delete this voice profile?')) return;
    await deleteVoiceProfile(voiceId);
    clonedVoices = clonedVoices.filter((v) => v.id !== voiceId);
  }

  async function handlePreview(voice: VoiceProfile): Promise<void> {
    if (generatingPreview) return;
    generatingPreview = true;
    previewVoiceId = voice.id;
    previewAudioUrl = '';
    try {
      const resp = await generateTTS({
        model_id: voice.model_id,
        text: previewText,
        voice_id: voice.id,
      });
      previewJob = { id: resp.job_id, status: resp.status };
      const finalJob = await pollJob(resp.job_id, () => {});
      if (finalJob.status === 'complete') {
        previewAudioUrl = getAudioUrl(finalJob.id);
      }
    } finally {
      generatingPreview = false;
    }
  }
</script>

<div class="p-6 max-w-3xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-bold">Voice Cloning</h1>
    <p class="text-gray-500 dark:text-gray-400 mt-1 text-sm">Upload reference audio to create a reusable cloned voice.</p>
  </div>

  <!-- Create new voice -->
  <div class="card p-5 space-y-4">
    <h2 class="font-semibold">Clone a New Voice</h2>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="label" for="voice-name">Voice name</label>
        <input id="voice-name" type="text" bind:value={voiceName}
          placeholder="e.g. My Voice" class="input" disabled={uploading} />
      </div>
      <div>
        <label class="label">Model</label>
        <ModelSelector models={$voiceCloningModels} bind:value={selectedModel} disabled={uploading} />
      </div>
    </div>

    <div>
      <label class="label" for="ref-audio">Reference audio (WAV / MP3 / FLAC, 3–30 sec recommended)</label>
      <input id="ref-audio" type="file" accept="audio/wav,audio/mpeg,audio/flac"
        on:change={handleFileChange} disabled={uploading}
        class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4
               file:rounded-lg file:border-0 file:font-medium
               file:bg-primary-50 file:text-primary-700
               dark:file:bg-primary-900/30 dark:file:text-primary-400
               hover:file:bg-primary-100 dark:hover:file:bg-primary-900/50" />
    </div>

    {#if referenceAudioPreview}
      <div>
        <p class="label">Preview reference audio:</p>
        <AudioPlayer src={referenceAudioPreview} />
      </div>
    {/if}

    {#if uploadError}
      <p class="text-sm text-red-600 dark:text-red-400">{uploadError}</p>
    {/if}

    <button
      on:click={handleCreate}
      disabled={!selectedModel || !voiceName.trim() || !referenceFile || uploading}
      class="btn-primary"
    >
      {#if uploading}Creating voice…{:else}Create Voice Profile{/if}
    </button>
  </div>

  <!-- Saved voices -->
  <div class="card p-5 space-y-3">
    <h2 class="font-semibold">Saved Voices</h2>

    {#if loadingVoices}
      <p class="text-sm text-gray-400">Loading…</p>
    {:else if clonedVoices.length === 0}
      <p class="text-sm text-gray-400">No cloned voices yet. Upload reference audio above to create one.</p>
    {:else}
      <!-- Preview text input -->
      <div>
        <label class="label" for="preview-text">Preview text</label>
        <input id="preview-text" type="text" bind:value={previewText}
          class="input" placeholder="Text to preview with each voice" />
      </div>

      <ul class="divide-y divide-gray-100 dark:divide-gray-700">
        {#each clonedVoices as voice (voice.id)}
          <li class="py-3 flex items-center gap-3">
            <div class="flex-1 min-w-0">
              <p class="font-medium text-sm">{voice.name}</p>
              <p class="text-xs text-gray-400">{voice.model_id} · {new Date(voice.created_at).toLocaleDateString()}</p>
              {#if voice.id === previewVoiceId && previewAudioUrl}
                <div class="mt-2">
                  <AudioPlayer src={previewAudioUrl} />
                </div>
              {/if}
            </div>
            <div class="flex gap-2 flex-shrink-0">
              <button
                on:click={() => handlePreview(voice)}
                disabled={generatingPreview}
                class="btn-secondary text-xs px-3 py-1.5"
              >
                {generatingPreview && previewVoiceId === voice.id ? 'Generating…' : 'Preview'}
              </button>
              <button
                on:click={() => handleDelete(voice.id)}
                class="btn-danger text-xs px-3 py-1.5"
              >
                Delete
              </button>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>
