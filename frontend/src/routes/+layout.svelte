<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { type Snippet } from 'svelte';
  import { page } from '$app/stores';
  import { refreshModels } from '$stores/models';
  import { initTheme } from '$stores/theme';
  import ThemeToggle from '$components/ThemeToggle.svelte';
  import ToastContainer from '$components/ToastContainer.svelte';
  import KeyboardShortcutsModal from '$components/KeyboardShortcutsModal.svelte';

  let { children }: { children: Snippet } = $props();

  let sidebarOpen = $state(false);
  let shortcutsOpen = $state(false);

  function closeSidebar(): void { sidebarOpen = false; }

  const navLinks = [
    { href: '/tts', label: 'TTS', icon: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z' },
    { href: '/clone', label: 'Clone Voice', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
    { href: '/compare', label: 'Compare', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
    { href: '/history', label: 'History', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
    { href: '/batch', label: 'Batch', icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
    { href: '/models', label: 'Models', icon: 'M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18' },
    { href: '/settings', label: 'Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
  ];

  let currentPath = $derived($page.url.pathname);

  function handleGlobalKeydown(e: KeyboardEvent): void {
    const target = e.target as Element;
    const isInput =
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      (target as HTMLElement).isContentEditable;
    if (e.key === '?' && !isInput && !e.ctrlKey && !e.altKey) {
      shortcutsOpen = true;
    }
  }

  onMount(() => {
    initTheme();
    refreshModels();
  });
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<!-- Mobile top bar -->
<div class="md:hidden fixed top-0 left-0 right-0 z-40 flex items-center gap-3 px-4 py-3
            bg-white dark:bg-[#111113] border-b border-gray-200 dark:border-[#1e1e22]">
  <button onclick={() => (sidebarOpen = !sidebarOpen)}
    class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors"
    aria-label="Toggle navigation">
    <svg class="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  </button>
  <a href="/" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
    <img src="/logo.svg" alt="OpenSpeakers" class="w-6 h-6 flex-shrink-0" />
    <span class="sidebar-title text-base">OpenSpeakers</span>
  </a>
  <div class="ml-auto"><ThemeToggle /></div>
</div>

{#if sidebarOpen}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="md:hidden fixed inset-0 z-40 bg-black/50 transition-opacity"
    onclick={closeSidebar}
    role="presentation">
  </div>
{/if}

<div class="min-h-screen flex">
  <!-- Sidebar nav -->
  <nav class="sidebar fixed inset-y-0 left-0 z-50 transition-transform duration-200
            md:static md:translate-x-0
            {sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}">
    <div class="sidebar-header">
      <a href="/" onclick={closeSidebar} class="flex items-center gap-2.5 mb-0.5 hover:opacity-80 transition-opacity">
        <img src="/logo.svg" alt="OpenSpeakers" class="w-8 h-8 flex-shrink-0" />
        <h1 class="sidebar-title">OpenSpeakers</h1>
      </a>
      <p class="sidebar-subtitle">TTS & Voice Cloning</p>
    </div>
    <ul class="flex-1 p-2 space-y-0.5">
      {#each navLinks as link}
        <li>
          <a
            href={link.href}
            onclick={closeSidebar}
            class="nav-link {currentPath.startsWith(link.href) ? 'nav-link-active' : ''}"
          >
            <svg class="w-[18px] h-[18px] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d={link.icon} />
            </svg>
            {link.label}
          </a>
        </li>
      {/each}
    </ul>
    <div class="sidebar-footer">
      <div class="flex items-center justify-between">
        <a
          href="/docs"
          target="_blank"
          rel="noopener"
          class="text-xs text-gray-500 dark:text-gray-500 hover:text-gray-300 transition-colors"
        >
          API Docs ↗
        </a>
        <ThemeToggle />
      </div>
    </div>
  </nav>

  <!-- Main content -->
  <main class="flex-1 overflow-auto pt-14 md:pt-0">
    {@render children()}
  </main>
</div>

<!-- Toast notifications -->
<ToastContainer />

<!-- Keyboard shortcuts modal -->
<KeyboardShortcutsModal bind:open={shortcutsOpen} />
