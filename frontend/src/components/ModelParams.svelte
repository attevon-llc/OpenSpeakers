<!-- Per-model parameter controls -->
<script lang="ts">
  import type { ModelInfo } from '$api/models';

  let {
    modelId = '',
    disabled = false,
    extras = $bindable({}),
    model = undefined,
    onInsertTag = undefined,
  }: {
    modelId?: string;
    disabled?: boolean;
    extras?: Record<string, unknown>;
    model?: ModelInfo;
    onInsertTag?: (tag: string) => void;
  } = $props();

  // VibeVoice 0.5B defaults
  let cfgScale = $state(1.5);
  let ddpmSteps = $state(5);
  // VibeVoice 1.5B defaults
  let cfgScale1p5b = $state(3.0);
  let speakerId = $state(0);
  // Fish Speech defaults
  let temperature = $state(0.7);
  let topP = $state(0.8);
  let repPenalty = $state(1.1);
  // Qwen3 TTS
  let instruct = $state('');
  // Chatterbox defaults
  let exaggeration = $state(0.5);
  let cfgWeight = $state(0.5);
  // Orpheus defaults
  let orpheusTemperature = $state(0.6);
  let orpheusTopP = $state(0.95);
  // F5-TTS defaults
  let f5RefText = $state('');
  // CosyVoice 2.0 defaults
  let cosyRefText = $state('');
  let cosyInstruct = $state('');

  // Reset all params to defaults when model changes
  $effect(() => {
    const _m = modelId;
    cfgScale = 1.5;
    ddpmSteps = 5;
    cfgScale1p5b = 3.0;
    speakerId = 0;
    temperature = 0.7;
    topP = 0.8;
    repPenalty = 1.1;
    instruct = '';
    exaggeration = 0.5;
    cfgWeight = 0.5;
    orpheusTemperature = 0.6;
    orpheusTopP = 0.95;
    f5RefText = '';
    cosyRefText = '';
    cosyInstruct = '';
  });

  // Sync extras from internal state
  $effect(() => {
    switch (modelId) {
      case 'vibevoice':
        extras = { cfg_scale: cfgScale, ddpm_steps: ddpmSteps };
        break;
      case 'vibevoice-1.5b':
        extras = { cfg_scale: cfgScale1p5b, speaker_id: speakerId };
        break;
      case 'fish-speech-s2':
        extras = { temperature, top_p: topP, repetition_penalty: repPenalty };
        break;
      case 'qwen3-tts':
        extras = instruct ? { instruct } : {};
        break;
      case 'chatterbox':
        extras = { exaggeration, cfg_weight: cfgWeight };
        break;
      case 'orpheus-3b':
        extras = { temperature: orpheusTemperature, top_p: orpheusTopP };
        break;
      case 'f5-tts':
        extras = f5RefText ? { ref_text: f5RefText } : {};
        break;
      case 'cosyvoice-2':
        extras = {
          ...(cosyRefText ? { ref_text: cosyRefText } : {}),
          ...(cosyInstruct ? { instruct: cosyInstruct } : {}),
        };
        break;
      default:
        extras = {};
    }
  });
</script>

{#if !modelId}
  <p class="text-xs text-gray-400 dark:text-gray-500 text-center py-2">
    Select a model above to see its settings.
  </p>
{/if}

<!-- Kokoro: no extra params (speed + language handled by parent) -->

<!-- VibeVoice 0.5B -->
{#if modelId === 'vibevoice'}
  <div class="grid grid-cols-2 gap-4">
    <!-- Voice Clarity -->
    <div>
      <label class="label" for="cfg-scale">
        Voice Clarity: {cfgScale.toFixed(1)}
        {#if cfgScale === 1.5}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Lower values sound more natural with slight variation. Higher values are more precise but can sound mechanical."
        >&#9432;</span>
      </label>
      <input
        id="cfg-scale"
        type="range"
        min="1.0"
        max="3.0"
        step="0.1"
        bind:value={cfgScale}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        How closely the voice follows the style preset
      </p>
    </div>

    <!-- Quality Steps -->
    <div>
      <label class="label" for="ddpm-steps">
        Quality Steps: {ddpmSteps}
        {#if ddpmSteps === 5}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Each step refines the audio. 3-4 for fast previews, 5 for balanced, 8-10 for final output."
        >&#9432;</span>
      </label>
      <input
        id="ddpm-steps"
        type="range"
        min="3"
        max="10"
        step="1"
        bind:value={ddpmSteps}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        More steps = better quality, slower generation
      </p>
    </div>
  </div>
{/if}

<!-- VibeVoice 1.5B -->
{#if modelId === 'vibevoice-1.5b'}
  <div>
    <label class="label" for="cfg-scale-1p5b">
      Voice Clarity: {cfgScale1p5b.toFixed(1)}
      {#if cfgScale1p5b === 3.0}<span class="label-hint">(default)</span>{/if}
      <span
        class="label-hint cursor-help"
        title="Lower = more creative variation. Higher = closer match to reference voice."
      >&#9432;</span>
    </label>
    <input
      id="cfg-scale-1p5b"
      type="range"
      min="1.0"
      max="5.0"
      step="0.1"
      bind:value={cfgScale1p5b}
      {disabled}
      class="w-full"
    />
    <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
      How closely the output follows the voice reference
    </p>
  </div>

  <!-- Speaker ID selector -->
  <div class="mt-3">
    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" for="speaker-id">
      Speaker ID
      <span class="text-xs text-gray-500 ml-1">(multi-speaker)</span>
    </label>
    <select
      id="speaker-id"
      bind:value={speakerId}
      {disabled}
      class="input"
    >
      <option value={0}>Speaker 0 (default)</option>
      <option value={1}>Speaker 1</option>
    </select>
    <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
      Prefix text with "Speaker 0: " or "Speaker 1: " to assign dialogue to different speakers.
    </p>
  </div>

  <div class="flex items-start gap-2 p-2.5 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-xs text-blue-700 dark:text-blue-300 mt-2">
    <svg class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <p>
      Tip: For multiple speakers, start each line with "Speaker 0:" or "Speaker 1:".
      Add [pause_0.5s] for pauses.
    </p>
  </div>
{/if}

<!-- Fish Speech S2-Pro -->
{#if modelId === 'fish-speech-s2'}
  <div class="grid grid-cols-3 gap-4">
    <!-- Expressiveness -->
    <div>
      <label class="label" for="fish-temperature">
        Expressiveness: {temperature.toFixed(2)}
        {#if temperature === 0.7}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Low (0.1-0.3): steady, consistent. Medium (0.5-0.7): natural. High (0.8-1.0): dramatic."
        >&#9432;</span>
      </label>
      <input
        id="fish-temperature"
        type="range"
        min="0.1"
        max="1.0"
        step="0.05"
        bind:value={temperature}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        How dynamic and varied the speech sounds
      </p>
    </div>

    <!-- Variation -->
    <div>
      <label class="label" for="fish-top-p">
        Variation: {topP.toFixed(2)}
        {#if topP === 0.8}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Lower = more predictable and consistent. Higher = more varied and natural-sounding."
        >&#9432;</span>
      </label>
      <input
        id="fish-top-p"
        type="range"
        min="0.5"
        max="1.0"
        step="0.05"
        bind:value={topP}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Range of vocal patterns to use
      </p>
    </div>

    <!-- Anti-Repetition -->
    <div>
      <label class="label" for="fish-rep-penalty">
        Anti-Repetition: {repPenalty.toFixed(1)}
        {#if repPenalty === 1.1}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Increase to 1.3-1.5 if output sounds repetitive. Don't go above 1.8."
        >&#9432;</span>
      </label>
      <input
        id="fish-rep-penalty"
        type="range"
        min="0.9"
        max="2.0"
        step="0.1"
        bind:value={repPenalty}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Prevents the voice from getting stuck in loops
      </p>
    </div>
  </div>

  <div class="flex items-start gap-2 p-2.5 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-xs text-blue-700 dark:text-blue-300 mt-2">
    <svg class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <p>
      Tip: Add emotion tags in your text: [happy], [sad], [angry], [whisper], [excited]
    </p>
  </div>

  <!-- Emotion tag quick-insert (Fish S2-Pro) -->
  <div class="mt-3">
    <p class="text-xs text-gray-400 dark:text-gray-400 mb-1">Emotion tags (click to insert into text):</p>
    <div class="flex flex-wrap gap-1">
      {#each ['[whisper]', '[excited]', '[angry]', '[sad]', '[laughs]', '[sighs]', '[breathes heavily]'] as tag}
        <button
          type="button"
          class="text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-primary-600 transition-colors font-mono cursor-pointer"
          onclick={() => onInsertTag?.(tag)}
        >{tag}</button>
      {/each}
    </div>
  </div>
{/if}

<!-- Qwen3 TTS -->
{#if modelId === 'qwen3-tts'}
  <div>
    <label class="label" for="qwen3-instruct">
      Speaking Style
      <span
        class="label-hint cursor-help"
        title="You can describe any speaking style: speed, emotion, accent, formality. The model interprets natural language instructions."
      >&#9432;</span>
    </label>
    <input
      id="qwen3-instruct"
      type="text"
      bind:value={instruct}
      {disabled}
      maxlength={200}
      placeholder={'e.g. "speak cheerfully and with enthusiasm" or "read slowly as a bedtime story"'}
      class="input"
    />
    <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
      Describe how the voice should sound &mdash; leave empty for a natural tone
    </p>

    <!-- Example prompts quick-fill -->
    <select
      class="input mt-2 text-sm"
      onchange={(e) => {
        if (e.currentTarget.value) {
          instruct = e.currentTarget.value;
          e.currentTarget.value = '';
        }
      }}
    >
      <option value="">— Insert example style —</option>
      <option value="Speak in a warm, friendly tone">Warm and friendly</option>
      <option value="Speak excitedly with high energy">Excited</option>
      <option value="Speak slowly and clearly, with careful enunciation">Slow and clear</option>
      <option value="Speak softly and gently, almost whispering">Gentle whisper</option>
      <option value="Speak with a serious, authoritative tone">Authoritative</option>
    </select>
  </div>
{/if}

<!-- Chatterbox -->
{#if modelId === 'chatterbox'}
  <div class="grid grid-cols-2 gap-4">
    <!-- Exaggeration -->
    <div>
      <label class="label" for="chatterbox-exaggeration">
        Exaggeration: {exaggeration.toFixed(2)}
        {#if exaggeration === 0.5}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Controls emotion exaggeration. Lower = neutral, Higher = more expressive."
        >&#9432;</span>
      </label>
      <input
        id="chatterbox-exaggeration"
        type="range"
        min="0.0"
        max="1.0"
        step="0.05"
        bind:value={exaggeration}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Emotion exaggeration level
      </p>
    </div>

    <!-- CFG Weight -->
    <div>
      <label class="label" for="chatterbox-cfg">
        CFG Weight: {cfgWeight.toFixed(2)}
        {#if cfgWeight === 0.5}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Controls pacing and adherence. Lower = more natural pacing, Higher = more controlled."
        >&#9432;</span>
      </label>
      <input
        id="chatterbox-cfg"
        type="range"
        min="0.0"
        max="1.0"
        step="0.05"
        bind:value={cfgWeight}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Pacing / style control
      </p>
    </div>
  </div>

  <!-- Emotion tag helpers for Chatterbox -->
  <div class="mt-3">
    <p class="text-xs text-gray-400 dark:text-gray-400 mb-1">Paralinguistic tags (click to insert into text):</p>
    <div class="flex flex-wrap gap-1">
      {#each ['[laugh]', '[cough]', '[sigh]', '[gasp]'] as tag}
        <button
          type="button"
          class="text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-primary-600 transition-colors font-mono cursor-pointer"
          onclick={() => onInsertTag?.(tag)}
        >{tag}</button>
      {/each}
    </div>
  </div>
{/if}

<!-- F5-TTS -->
{#if modelId === 'f5-tts'}
  <div>
    <label class="label" for="f5-ref-text">
      Reference Transcript
      <span
        class="label-hint cursor-help"
        title="Optional: provide the text spoken in the reference audio file. Improves cloning accuracy. Leave empty to auto-transcribe."
      >&#9432;</span>
    </label>
    <input
      id="f5-ref-text"
      type="text"
      bind:value={f5RefText}
      {disabled}
      maxlength={300}
      placeholder="Optional: transcript of the reference audio (e.g. 'The quick brown fox...')"
      class="input"
    />
    <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
      Only used when a voice profile is selected. Leave empty for auto-transcription.
    </p>
  </div>
{/if}

<!-- Orpheus 3B -->
{#if modelId === 'orpheus-3b'}
  <div class="grid grid-cols-2 gap-4">
    <!-- Temperature -->
    <div>
      <label class="label" for="orpheus-temperature">
        Temperature: {orpheusTemperature.toFixed(2)}
        {#if orpheusTemperature === 0.6}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Controls randomness and expressiveness. 0.6 is a good balance."
        >&#9432;</span>
      </label>
      <input
        id="orpheus-temperature"
        type="range"
        min="0.0"
        max="1.0"
        step="0.05"
        bind:value={orpheusTemperature}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Speech variation and expressiveness
      </p>
    </div>

    <!-- Top-p -->
    <div>
      <label class="label" for="orpheus-top-p">
        Top-p: {orpheusTopP.toFixed(2)}
        {#if orpheusTopP === 0.95}<span class="label-hint">(default)</span>{/if}
        <span
          class="label-hint cursor-help"
          title="Nucleus sampling parameter. Higher = more diverse outputs."
        >&#9432;</span>
      </label>
      <input
        id="orpheus-top-p"
        type="range"
        min="0.0"
        max="1.0"
        step="0.05"
        bind:value={orpheusTopP}
        {disabled}
        class="w-full"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Token selection diversity
      </p>
    </div>
  </div>

  <!-- Emotion tag helpers for Orpheus -->
  <div class="mt-3">
    <p class="text-xs text-gray-400 dark:text-gray-400 mb-1">Emotion tags (click to insert into text):</p>
    <div class="flex flex-wrap gap-1">
      {#each ['<laugh>', '<chuckle>', '<sigh>', '<cough>', '<sniffle>', '<groan>', '<yawn>', '<gasp>'] as tag}
        <button
          type="button"
          class="text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-primary-600 transition-colors font-mono cursor-pointer"
          onclick={() => onInsertTag?.(tag)}
        >{tag}</button>
      {/each}
    </div>
  </div>
{/if}

<!-- Dia 1.6B -->
{#if modelId === 'dia-1b'}
  <div class="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-xs text-blue-700 dark:text-blue-300">
    <svg class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <div class="space-y-1">
      <p class="font-medium">Dialogue mode: Use [S1] and [S2] speaker tags</p>
      <p>Example: <code class="bg-blue-100 dark:bg-blue-900/40 px-1 rounded font-mono">[S1] Hello there! [S2] How are you? [S1] I'm doing great!</code></p>
      <p>Nonverbal sounds: <code class="bg-blue-100 dark:bg-blue-900/40 px-1 rounded font-mono">(laughs)</code> <code class="bg-blue-100 dark:bg-blue-900/40 px-1 rounded font-mono">(sighs)</code> <code class="bg-blue-100 dark:bg-blue-900/40 px-1 rounded font-mono">(coughs)</code> <code class="bg-blue-100 dark:bg-blue-900/40 px-1 rounded font-mono">(whispers)</code></p>
    </div>
  </div>

  <!-- Nonverbal sound chips for Dia -->
  <div class="mt-3">
    <p class="text-xs text-gray-400 dark:text-gray-400 mb-1">Nonverbal sounds (click to insert):</p>
    <div class="flex flex-wrap gap-1">
      {#each ['[S1] ', '[S2] ', '(laughs)', '(sighs)', '(coughs)', '(clears throat)', '(whispers)'] as tag}
        <button
          type="button"
          class="text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-primary-600 transition-colors font-mono cursor-pointer"
          onclick={() => onInsertTag?.(tag)}
        >{tag}</button>
      {/each}
    </div>
  </div>
{/if}

<!-- CosyVoice 2.0 -->
{#if modelId === 'cosyvoice-2'}
  <div class="space-y-3">
    <div class="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-xs text-blue-700 dark:text-blue-300">
      <svg class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="space-y-0.5">
        <p><strong>No voice:</strong> cross-lingual synthesis with default speaker</p>
        <p><strong>Voice only:</strong> zero-shot cloning (add transcript below to improve quality)</p>
        <p><strong>Voice + Style:</strong> voice design mode — shape characteristics with the style field</p>
      </div>
    </div>

    <div>
      <label class="label" for="cosy-ref-text">
        Reference Transcript
        <span
          class="label-hint cursor-help"
          title="Transcript of what's spoken in the reference audio. Improves zero-shot cloning accuracy."
        >&#9432;</span>
      </label>
      <input
        id="cosy-ref-text"
        type="text"
        bind:value={cosyRefText}
        {disabled}
        maxlength={300}
        placeholder="Optional: transcript of the reference audio"
        class="input"
      />
    </div>

    <div>
      <label class="label" for="cosy-instruct">
        Speaking Style
        <span
          class="label-hint cursor-help"
          title="Natural language instruction to shape the voice. Requires a voice profile to be selected."
        >&#9432;</span>
      </label>
      <input
        id="cosy-instruct"
        type="text"
        bind:value={cosyInstruct}
        {disabled}
        maxlength={200}
        placeholder="e.g. 'speak softly and gently' or 'sound excited and energetic'"
        class="input"
      />
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Describe how the voice should sound — only used when a voice profile is selected
      </p>
      <select
        class="input mt-2 text-sm"
        onchange={(e) => {
          if (e.currentTarget.value) {
            cosyInstruct = e.currentTarget.value;
            e.currentTarget.value = '';
          }
        }}
      >
        <option value="">— Insert example style —</option>
        <option value="Speak in a warm, friendly tone">Warm and friendly</option>
        <option value="Speak softly and gently">Soft and gentle</option>
        <option value="Speak excitedly with high energy">Excited</option>
        <option value="Speak slowly and clearly">Slow and clear</option>
        <option value="Speak with a serious, authoritative tone">Authoritative</option>
      </select>
    </div>
  </div>
{/if}

<!-- Parler TTS -->
{#if modelId === 'parler-tts'}
  <div>
    <label class="label" for="parler-description">
      Voice Description
      <span
        class="label-hint cursor-help"
        title="Parler TTS generates a voice based on a text description — no reference audio needed."
      >&#9432;</span>
    </label>
    <textarea
      id="parler-description"
      bind:value={extras.description as string}
      {disabled}
      rows={3}
      maxlength={400}
      placeholder="Describe the speaker's voice, e.g. 'A female speaker with a slightly expressive voice delivers a clear, engaging speech at a moderate pace in a quiet room.'"
      class="input resize-none"
    ></textarea>
    <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
      Describe the speaker's voice — no reference audio needed
    </p>

    <!-- Example prompts quick-fill -->
    <select
      class="input mt-2 text-sm"
      onchange={(e) => {
        if (e.currentTarget.value) {
          extras = { ...extras, description: e.currentTarget.value };
          e.currentTarget.value = '';
        }
      }}
    >
      <option value="">— Insert example description —</option>
      <option value="A female speaker with a warm, expressive voice speaking clearly at a moderate pace in a quiet studio.">Warm female voice</option>
      <option value="A deep male voice, slightly gravelly, speaking slowly in a quiet studio.">Deep male voice</option>
      <option value="A young energetic female voice speaking fast with excitement.">Energetic female</option>
      <option value="An older male voice with a calm, authoritative tone reading at a measured pace.">Authoritative male</option>
      <option value="A child's voice speaking clearly and cheerfully at a moderate pace.">Child's voice</option>
    </select>
  </div>
{/if}
