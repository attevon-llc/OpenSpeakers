<!-- Landing Page -->
<script lang="ts">
  import { models } from '$stores/models';

  const features = [
    {
      icon: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z',
      title: 'Multi-Model TTS',
      description: '11 open-source models in one interface. Switch models on-the-fly with hot-swap GPU management — only one model occupies VRAM at a time.',
    },
    {
      icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
      title: 'Voice Cloning',
      description: 'Clone any voice from 5–30 seconds of reference audio. Zero-shot cloning across 7 models including Fish Audio S2-Pro, VibeVoice 1.5B, and CosyVoice 2.0.',
    },
    {
      icon: 'M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z',
      title: 'Real-time Streaming',
      description: 'Hear audio as it generates with VibeVoice 0.5B streaming. Web Audio API scheduling ensures gapless playback from the very first chunk.',
    },
    {
      icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
      title: 'Batch Generation',
      description: 'Paste a text file and generate audio for every line simultaneously. Download all completed files as a single ZIP archive.',
    },
    {
      icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      title: 'Model Comparison',
      description: 'Generate the same text across multiple models side-by-side. Compare quality, latency, and style to choose the right model for your use case.',
    },
    {
      icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
      title: 'Full Job History',
      description: 'Every generation is stored with searchable history, status tracking, and one-click replay. Filter by model, status, or text content.',
    },
  ];

  const modelSummary = [
    { id: 'kokoro', name: 'Kokoro 82M', org: 'hexgrad', vram: '<1 GB', tags: ['50+ voices', 'fastest'] },
    { id: 'vibevoice', name: 'VibeVoice 0.5B', org: 'Microsoft', vram: '~4.5 GB', tags: ['streaming', '12 voices'] },
    { id: 'vibevoice-1.5b', name: 'VibeVoice 1.5B', org: 'Microsoft', vram: '~12 GB', tags: ['cloning', 'multi-speaker'] },
    { id: 'fish-speech-s2', name: 'Fish Audio S2-Pro', org: 'Fish Audio', vram: '~22 GB', tags: ['cloning', '80+ langs'] },
    { id: 'qwen3-tts', name: 'Qwen3 TTS 1.7B', org: 'Alibaba', vram: '~10 GB', tags: ['cloning', 'instruct'] },
    { id: 'f5-tts', name: 'F5-TTS', org: 'SWivid', vram: '~3 GB', tags: ['cloning', '0.15x RTF'] },
    { id: 'chatterbox', name: 'Chatterbox', org: 'Resemble AI', vram: '~5 GB', tags: ['cloning', 'emotion'] },
    { id: 'orpheus-3b', name: 'Orpheus 3B', org: 'Canopy Labs', vram: '~7 GB', tags: ['streaming', 'emotion tags'] },
    { id: 'cosyvoice-2', name: 'CosyVoice 2.0', org: 'Alibaba', vram: '~5 GB', tags: ['cloning', '150ms latency'] },
    { id: 'parler-tts', name: 'Parler TTS', org: 'Parler/Stability', vram: '~2 GB', tags: ['text-to-voice'] },
    { id: 'dia-1b', name: 'Dia 1.6B', org: 'Nari Labs', vram: '~10 GB', tags: ['dialogue', '[S1]/[S2]'] },
  ];

  const techStack = [
    { name: 'SvelteKit 2', role: 'Frontend' },
    { name: 'FastAPI', role: 'Backend API' },
    { name: 'Celery', role: 'Task Queue' },
    { name: 'Redis', role: 'Broker / Pub-Sub' },
    { name: 'PostgreSQL', role: 'Database' },
    { name: 'Docker', role: 'Containers' },
  ];
</script>

<svelte:head><title>OpenSpeakers — Open-Source TTS Platform</title></svelte:head>

<div class="min-h-screen">
  <!-- Hero -->
  <div class="px-6 py-16 md:py-24 max-w-5xl mx-auto text-center">
    <div class="flex justify-center mb-6">
      <img src="/logo.svg" alt="OpenSpeakers" class="w-20 h-20 md:w-24 md:h-24" />
    </div>
    <h1 class="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
      Open<span class="text-primary-400">Speakers</span>
    </h1>
    <p class="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-8 leading-relaxed">
      The most complete open-source TTS platform. 11 models, voice cloning, real-time streaming,
      and batch generation — all from one unified interface with hot-swap GPU management.
    </p>
    <div class="flex flex-wrap justify-center gap-3">
      <a href="/tts" class="px-6 py-3 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-semibold transition-colors text-sm">
        Start Generating →
      </a>
      <a href="/clone" class="px-6 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white font-semibold transition-colors text-sm">
        Clone a Voice
      </a>
      <a href="/batch" class="px-6 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white font-semibold transition-colors text-sm">
        Batch Generate
      </a>
    </div>
  </div>

  <!-- Stats bar -->
  <div class="border-y border-gray-800 bg-gray-900/50">
    <div class="max-w-5xl mx-auto px-6 py-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
      {#each [
        { value: '11', label: 'TTS Models' },
        { value: '7', label: 'Support Voice Cloning' },
        { value: '4', label: 'Support Streaming' },
        { value: '80+', label: 'Languages Supported' },
      ] as stat}
        <div>
          <p class="text-2xl font-bold text-primary-400">{stat.value}</p>
          <p class="text-xs text-gray-500 mt-0.5">{stat.label}</p>
        </div>
      {/each}
    </div>
  </div>

  <!-- Features -->
  <div class="max-w-5xl mx-auto px-6 py-14">
    <h2 class="text-xl font-bold text-white mb-2 text-center">Everything You Need</h2>
    <p class="text-sm text-gray-500 text-center mb-8">Built on a production-grade stack, not a Gradio prototype.</p>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each features as f}
        <div class="bg-gray-800/60 border border-gray-700/60 rounded-xl p-5 space-y-2">
          <div class="w-9 h-9 rounded-lg bg-primary-600/20 border border-primary-500/20 flex items-center justify-center">
            <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d={f.icon} />
            </svg>
          </div>
          <h3 class="font-semibold text-white text-sm">{f.title}</h3>
          <p class="text-xs text-gray-400 leading-relaxed">{f.description}</p>
        </div>
      {/each}
    </div>
  </div>

  <!-- Model grid -->
  <div class="border-t border-gray-800 bg-gray-900/30">
    <div class="max-w-5xl mx-auto px-6 py-14">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-white">11 Production Models</h2>
          <p class="text-sm text-gray-500 mt-1">From ultra-fast 82M to expressive 3B+ parameter models</p>
        </div>
        <a href="/models" class="text-sm text-primary-400 hover:text-primary-300 transition-colors">
          View all →
        </a>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {#each modelSummary as m}
          {@const live = models.find((lm) => lm.id === m.id)}
          <div class="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 flex items-start gap-3">
            <!-- Status dot -->
            <div class="mt-1 w-2 h-2 rounded-full flex-shrink-0
              {live?.status === 'loaded' ? 'bg-green-400' : live?.status === 'loading' ? 'bg-blue-400 animate-pulse' : 'bg-gray-600'}">
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-white truncate">{m.name}</p>
              <p class="text-xs text-gray-500">{m.org} · {m.vram}</p>
              <div class="flex flex-wrap gap-1 mt-1.5">
                {#each m.tags as tag}
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">{tag}</span>
                {/each}
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- How it works -->
  <div class="max-w-5xl mx-auto px-6 py-14">
    <h2 class="text-xl font-bold text-white mb-8 text-center">How It Works</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      {#each [
        { step: '1', title: 'Choose a Model', desc: 'Pick from 11 models — from ultra-fast Kokoro 82M to expressive Orpheus 3B. GPU hot-swap handles model loading automatically.' },
        { step: '2', title: 'Enter Your Text', desc: 'Type or paste your text. Add emotion tags, choose a voice, set language, and configure model-specific parameters.' },
        { step: '3', title: 'Get Your Audio', desc: 'Jobs run on Celery workers with real-time WebSocket progress. Download WAV, MP3, or OGG when complete.' },
      ] as s}
        <div class="text-center space-y-3">
          <div class="w-12 h-12 rounded-full bg-primary-600 text-white font-bold text-lg flex items-center justify-center mx-auto">
            {s.step}
          </div>
          <h3 class="font-semibold text-white">{s.title}</h3>
          <p class="text-sm text-gray-400 leading-relaxed">{s.desc}</p>
        </div>
      {/each}
    </div>
  </div>

  <!-- Tech stack -->
  <div class="border-t border-gray-800 bg-gray-900/30">
    <div class="max-w-5xl mx-auto px-6 py-10">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider text-center mb-6">Built on a production stack</h2>
      <div class="flex flex-wrap justify-center gap-3">
        {#each techStack as t}
          <div class="px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-center min-w-[100px]">
            <p class="text-sm font-medium text-white">{t.name}</p>
            <p class="text-xs text-gray-500">{t.role}</p>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- Bottom CTA -->
  <div class="max-w-5xl mx-auto px-6 py-16 text-center">
    <h2 class="text-2xl font-bold text-white mb-3">Ready to start?</h2>
    <p class="text-gray-400 text-sm mb-8">Open source. Self-hosted. Your audio, your GPU.</p>
    <div class="flex flex-wrap justify-center gap-3">
      <a href="/tts" class="px-6 py-3 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-semibold transition-colors text-sm">
        Generate Speech →
      </a>
      <a href="/clone" class="px-6 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white font-semibold transition-colors text-sm">
        Clone a Voice
      </a>
      <a href="/compare" class="px-6 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white font-semibold transition-colors text-sm">
        Compare Models
      </a>
      <a href="/about" class="px-6 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white font-semibold transition-colors text-sm">
        Learn More
      </a>
    </div>
  </div>
</div>
