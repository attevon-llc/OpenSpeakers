<script lang="ts">
  export let src: string = '';
  export let duration: number | null = null;
  export let disabled: boolean = false;

  let audio: HTMLAudioElement;
  let playing = false;
  let currentTime = 0;
  let totalDuration = 0;
  let volume = 1;

  $: if (src && audio) {
    audio.load();
    playing = false;
    currentTime = 0;
  }

  function toggle(): void {
    if (!audio || !src) return;
    if (playing) {
      audio.pause();
    } else {
      audio.play();
    }
  }

  function seek(e: MouseEvent): void {
    if (!audio || !totalDuration) return;
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const x = e.clientX - rect.left;
    const pct = x / rect.width;
    audio.currentTime = pct * totalDuration;
  }

  function formatTime(s: number): string {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
  }

  $: progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;
</script>

<div class="space-y-2">
  {#if src}
    <!-- svelte-ignore a11y-media-has-caption -->
    <audio
      bind:this={audio}
      bind:currentTime
      bind:duration={totalDuration}
      bind:paused={playing}
      on:play={() => (playing = true)}
      on:pause={() => (playing = false)}
      on:ended={() => (playing = false)}
      preload="metadata"
    >
      <source {src} type="audio/wav" />
    </audio>

    <div class="flex items-center gap-3">
      <!-- Play/Pause button -->
      <button
        on:click={toggle}
        class="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-full
               bg-primary-600 hover:bg-primary-700 text-white transition-colors"
        aria-label={playing ? 'Pause' : 'Play'}
      >
        {#if playing}
          <!-- Pause icon -->
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        {:else}
          <!-- Play icon -->
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
          </svg>
        {/if}
      </button>

      <!-- Progress bar -->
      <div class="flex-1 group">
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div
          class="relative h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer"
          on:click={seek}
          role="slider"
          aria-label="Seek"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(progress)}
          tabindex="0"
        >
          <div
            class="absolute inset-y-0 left-0 bg-primary-500 rounded-full transition-all"
            style="width: {progress}%"
          ></div>
        </div>
      </div>

      <!-- Time -->
      <span class="text-xs text-gray-500 dark:text-gray-400 tabular-nums flex-shrink-0 w-16 text-right">
        {formatTime(currentTime)} / {formatTime(duration ?? totalDuration)}
      </span>

      <!-- Download -->
      <a
        href={src}
        download="tts_output.wav"
        class="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        aria-label="Download audio"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </a>
    </div>
  {:else}
    <!-- Placeholder state -->
    <div class="flex items-center gap-3 opacity-40">
      <div class="flex-shrink-0 w-9 h-9 rounded-full bg-gray-300 dark:bg-gray-600"></div>
      <div class="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
      <span class="text-xs text-gray-400 w-16 text-right">0:00 / 0:00</span>
    </div>
  {/if}
</div>
