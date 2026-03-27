<script lang="ts">
  import { fly } from 'svelte/transition';
  import { toasts, removeToast } from '$stores/toasts';

  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
    warning: '⚠',
  };

  const borderColors = {
    success: 'border-green-500',
    error: 'border-red-500',
    info: 'border-blue-500',
    warning: 'border-yellow-500',
  };

  const textColors = {
    success: 'text-green-400',
    error: 'text-red-400',
    info: 'text-blue-400',
    warning: 'text-yellow-400',
  };
</script>

<div class="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm" aria-live="polite">
  {#each toasts as toast (toast.id)}
    <div
      transition:fly={{ y: -20, duration: 200 }}
      class="flex items-center gap-3 bg-gray-800 border-l-4 {borderColors[toast.type]} rounded-lg px-4 py-3 shadow-xl"
      role="alert"
    >
      <span class="text-lg {textColors[toast.type]}" aria-hidden="true">{icons[toast.type]}</span>
      <p class="flex-1 text-sm text-gray-200 break-words">{toast.message}</p>
      <button
        onclick={() => removeToast(toast.id)}
        class="text-gray-500 hover:text-gray-300 transition-colors ml-2 text-lg leading-none"
        aria-label="Dismiss notification"
      >×</button>
    </div>
  {/each}
</div>
