<script lang="ts">
  let { open = $bindable(false) }: { open: boolean } = $props();

  function close() { open = false; }

  const shortcuts = [
    { key: '?', action: 'Open keyboard shortcuts help' },
    { key: 'Esc', action: 'Close modal' },
    { key: 'Ctrl+Enter', action: 'Submit generation (TTS page)' },
    { key: 'Space / Enter', action: 'Play/pause audio player' },
    { key: '← / →', action: 'Seek audio ±5 seconds' },
    { key: 'Home', action: 'Jump to audio start' },
    { key: 'End', action: 'Jump to audio end' },
  ];
</script>

{#if open}
  <!-- Backdrop — purely visual; click closes modal -->
  <div
    class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center"
    onclick={close}
    role="none"
  >
    <!-- Modal -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div
      class="bg-gray-800 rounded-xl shadow-2xl p-6 max-w-md w-full mx-4 border border-gray-700"
      onclick={(e) => e.stopPropagation()}
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      tabindex={-1}
    >
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-white">Keyboard Shortcuts</h2>
        <button
          onclick={close}
          class="text-gray-400 hover:text-white transition-colors text-xl leading-none"
          aria-label="Close"
        >×</button>
      </div>
      <table class="w-full text-sm">
        <tbody>
          {#each shortcuts as { key, action }}
            <tr class="border-b border-gray-700 last:border-0">
              <td class="py-2 pr-4">
                <kbd class="bg-gray-700 text-gray-200 px-2 py-0.5 rounded text-xs font-mono">{key}</kbd>
              </td>
              <td class="py-2 text-gray-300">{action}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}

<svelte:window
  onkeydown={(e) => { if (open && e.key === 'Escape') close(); }}
/>
