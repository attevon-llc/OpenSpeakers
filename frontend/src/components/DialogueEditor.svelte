<!-- Structured multi-speaker dialogue editor for models like Dia and VibeVoice 1.5B -->
<script lang="ts">
  import { tick } from 'svelte';

  let {
    dialogueFormat = '',
    value = $bindable(''),
    disabled = false,
  }: {
    dialogueFormat?: string;
    value?: string;
    disabled?: boolean;
  } = $props();

  interface Turn {
    id: number;
    speaker: number; // 1-indexed (speaker 1, speaker 2)
    text: string;
  }

  const FORMATS: Record<string, {
    speakers: string[];
    wrap: (speaker: string, text: string) => string;
    join: string;
    label: string;
    nonverbals?: string[];
  }> = {
    dia: {
      speakers: ['S1', 'S2'],
      wrap: (s, t) => `[${s}] ${t}`,
      join: ' ',
      label: 'Speaker',
      nonverbals: ['(laughs)', '(sighs)', '(coughs)', '(clears throat)', '(whispers)'],
    },
    vibevoice: {
      speakers: ['Speaker 0', 'Speaker 1'],
      wrap: (s, t) => `${s}: ${t}`,
      join: '\n',
      label: 'Speaker',
      nonverbals: undefined,
    },
  };

  let turns = $state<Turn[]>([
    { id: 0, speaker: 1, text: '' },
    { id: 1, speaker: 2, text: '' },
  ]);
  let nextId = $state(2);

  const fmt = $derived(FORMATS[dialogueFormat]);

  // Sync formatted text to parent
  $effect(() => {
    if (!fmt) return;
    const formatted = turns
      .filter((t) => t.text.trim().length > 0)
      .map((t) => fmt.wrap(fmt.speakers[t.speaker - 1], t.text.trim()))
      .join(fmt.join);
    value = formatted;
  });

  function addTurn() {
    if (turns.length >= 50) return;
    // Alternate speaker from the last turn
    const lastSpeaker = turns.length > 0 ? turns[turns.length - 1].speaker : 1;
    const newSpeaker = lastSpeaker === 1 ? 2 : 1;
    turns = [...turns, { id: nextId++, speaker: newSpeaker, text: '' }];
    // Focus the new textarea
    tick().then(() => {
      const textareas = document.querySelectorAll<HTMLTextAreaElement>('[data-dialogue-turn]');
      textareas[textareas.length - 1]?.focus();
    });
  }

  function removeTurn(id: number) {
    if (turns.length <= 1) return;
    turns = turns.filter((t) => t.id !== id);
  }

  function moveTurn(id: number, direction: -1 | 1) {
    const idx = turns.findIndex((t) => t.id === id);
    const target = idx + direction;
    if (target < 0 || target >= turns.length) return;
    const copy = [...turns];
    [copy[idx], copy[target]] = [copy[target], copy[idx]];
    turns = copy;
  }

  function insertNonverbal(turnId: number, tag: string) {
    const turn = turns.find((t) => t.id === turnId);
    if (!turn) return;
    turn.text = turn.text ? `${turn.text} ${tag}` : tag;
    turns = turns; // trigger reactivity
  }

  // Speaker colors for visual distinction
  function speakerColor(speaker: number): string {
    return speaker === 1
      ? 'border-l-blue-500'
      : 'border-l-emerald-500';
  }

  function speakerBgColor(speaker: number): string {
    return speaker === 1
      ? 'bg-blue-500/10'
      : 'bg-emerald-500/10';
  }
</script>

{#if fmt}
  <div class="space-y-2">
    <!-- Info banner -->
    <div class="flex items-start gap-2 p-3 rounded-lg bg-amber-900/20 border border-amber-700/30 text-xs text-amber-300">
      <svg class="w-4 h-4 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>
        Dialogue mode — add turns for each speaker. The text will be formatted as
        {#if dialogueFormat === 'dia'}
          <code class="bg-amber-900/40 px-1 rounded">[S1] text [S2] text</code> tags.
        {:else}
          <code class="bg-amber-900/40 px-1 rounded">Speaker 0: text</code> prefixes.
        {/if}
      </span>
    </div>

    <!-- Turns list -->
    {#each turns as turn, i (turn.id)}
      <div class="rounded-lg border-l-4 {speakerColor(turn.speaker)} {speakerBgColor(turn.speaker)} border border-gray-700 p-3">
        <div class="flex items-center gap-2 mb-2">
          <!-- Speaker selector -->
          <select
            bind:value={turn.speaker}
            {disabled}
            class="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-white text-xs focus:border-primary-500 focus:outline-none"
          >
            {#each fmt.speakers as spk, si}
              <option value={si + 1}>{fmt.label} {si + 1}</option>
            {/each}
          </select>

          <span class="text-xs text-gray-500 flex-1">Turn {i + 1}</span>

          <!-- Move / remove controls -->
          <div class="flex items-center gap-1">
            <button
              onclick={() => moveTurn(turn.id, -1)}
              disabled={disabled || i === 0}
              class="p-1 text-gray-500 hover:text-gray-300 disabled:opacity-20 disabled:cursor-not-allowed"
              aria-label="Move turn up"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
              </svg>
            </button>
            <button
              onclick={() => moveTurn(turn.id, 1)}
              disabled={disabled || i === turns.length - 1}
              class="p-1 text-gray-500 hover:text-gray-300 disabled:opacity-20 disabled:cursor-not-allowed"
              aria-label="Move turn down"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <button
              onclick={() => removeTurn(turn.id)}
              disabled={disabled || turns.length <= 1}
              class="p-1 text-gray-500 hover:text-red-400 disabled:opacity-20 disabled:cursor-not-allowed"
              aria-label="Remove turn"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Text input -->
        <textarea
          data-dialogue-turn
          bind:value={turn.text}
          {disabled}
          placeholder="{fmt.label} {turn.speaker} says…"
          rows={2}
          class="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none resize-none text-sm"
        ></textarea>

        <!-- Nonverbal quick-insert buttons (Dia only) -->
        {#if fmt.nonverbals}
          <div class="flex flex-wrap gap-1.5 mt-2">
            {#each fmt.nonverbals as nv}
              <button
                onclick={() => insertNonverbal(turn.id, nv)}
                {disabled}
                class="text-xs px-2 py-0.5 rounded-full bg-gray-700/60 text-gray-400 hover:text-amber-300 hover:bg-amber-900/20 transition-colors border border-gray-600/50 disabled:opacity-40"
              >{nv}</button>
            {/each}
          </div>
        {/if}
      </div>
    {/each}

    <!-- Add turn button -->
    <button
      onclick={addTurn}
      {disabled}
      class="w-full py-2 rounded-lg border-2 border-dashed border-gray-600 text-gray-400 hover:border-primary-500 hover:text-primary-400 transition-colors text-sm disabled:opacity-30 disabled:cursor-not-allowed"
    >
      + Add speaker turn
    </button>

    <!-- Preview of formatted output -->
    {#if value.trim()}
      <details class="text-xs">
        <summary class="text-gray-500 cursor-pointer hover:text-gray-400 select-none">Preview formatted text</summary>
        <pre class="mt-1 p-2 bg-gray-900 rounded-lg text-gray-400 overflow-x-auto whitespace-pre-wrap break-words">{value}</pre>
      </details>
    {/if}
  </div>
{:else}
  <p class="text-sm text-gray-500">Unknown dialogue format: {dialogueFormat}</p>
{/if}
