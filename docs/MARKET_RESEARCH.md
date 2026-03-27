# OpenSpeakers — TTS Market Research & Competitive Analysis

> Last updated: 2026-03-24 (Liquid AI LFM2.5-Audio added)
> Purpose: Track the open-source TTS model landscape, feature comparisons, and competitive positioning.

---

## 1. Complete Open-Source TTS Model Registry (2025–2026)

| Model | Org | HF Model ID | VRAM | Params | Voice Cloning | Streaming | Languages | Quality | RTF | License | Unique Capability |
|-------|-----|-------------|------|--------|--------------|-----------|-----------|---------|-----|---------|-------------------|
| **Kokoro 82M** | Hexgrad | hexgrad/Kokoro-82M | 0.5GB | 82M | ✗ | ✓ | 8 | ⭐⭐⭐⭐⭐ | <0.5x | Apache 2.0 | Ultra-light, TTS Arena #1 |
| **VibeVoice 0.5B** | Microsoft | microsoft/VibeVoice-Realtime-0.5B | 4.5GB | 500M | ✗ | ✓ | 12 | ⭐⭐⭐⭐ | ~1x | Research | Real-time streaming |
| **VibeVoice 1.5B** | Microsoft | microsoft/VibeVoice-1.5B | 12GB | 1.5B | ✓ zero-shot | Partial | 10 | ⭐⭐⭐⭐⭐ | ~0.8x | Research | 90-min long-form, 4 speakers |
| **Fish Audio S2-Pro** | Fish Audio | fishaudio/s2-pro | 22GB | 1B+ | ✓ zero-shot | ✓ | 80+ | ⭐⭐⭐⭐⭐ | ~0.8x | MIT | 15K emotion tags |
| **Qwen3 TTS 1.7B** | Alibaba | Qwen/Qwen3-TTS | 10GB | 1.7B | ✓ zero-shot | ✓ | 10 | ⭐⭐⭐⭐⭐ | ~0.9x | Apache 2.0 | Voice design from text description |
| **F5-TTS** | SWivid | SWivid/F5-TTS | 2–4GB | ~300M | ✓ zero-shot | ✓ | EN/ZH/multi | ⭐⭐⭐⭐⭐ | **0.15x** | MIT | Flow matching, 3–5s generation |
| **Chatterbox** | Resemble AI | resemble-ai/chatterbox | 4–6GB | 600M | ✓ 5s ref | ✓ | 23 | ⭐⭐⭐⭐⭐ | ~0.8x | MIT | Emotion control, Perth watermarking |
| **Chatterbox Turbo** | Resemble AI | resemble-ai/chatterbox-turbo | 2–3GB | 350M | ✗ | ✓ | 23 | ⭐⭐⭐⭐⭐ | >1x | MIT | `[laugh]`, `[cough]` paralinguistic tags |
| **Orpheus 3B** | Canopy Labs | canopylabs/orpheus-3b-0.1-ft | 6–8GB | 3B | ✓ zero-shot | ✓ | EN | ⭐⭐⭐⭐⭐ | ~0.8x | Apache 2.0 | Emotion/intonation tags, Llama backbone |
| **Orpheus 1B** | Canopy Labs | canopylabs/orpheus-1b | 2–3GB | 1B | ✓ zero-shot | ✓ | EN | ⭐⭐⭐⭐ | ~0.9x | Apache 2.0 | Faster variant of Orpheus |
| **CosyVoice 2.0** | FunAudioLLM | FunAudioLLM/CosyVoice2-0.5B | 4–6GB | 500M | ✓ zero-shot | ✓ | Multi | ⭐⭐⭐⭐⭐ | **0.15x** | Apache 2.0 | 150ms latency, MOS 5.53 (best measured) |
| **XTTS v2** | Coqui | coqui/XTTS-v2 | 6–8GB | 467M | ✓ 6s ref | ✓ | **17** | ⭐⭐⭐⭐⭐ | ~1x | MPL 2.0 | Best multilingual open-source model |
| **Parler TTS Mini** | Parler/Stability | parler-tts/parler-tts-mini-v1 | 2–3GB | 500M | ✗ | ✓ | EN | ⭐⭐⭐⭐ | ~0.6x | Apache 2.0 | **Text description → voice** (no ref audio needed) |
| **Dia 1.6B** | Nari Labs | nari-labs/Dia-1.6B | 10GB | 1.6B | ✓ | ✓ | EN | ⭐⭐⭐⭐⭐ | ~0.8x | Apache 2.0 | **[S1]/[S2] dialogue generation**, nonverbal sounds |
| **Bark** | Suno | suno/bark | 10–12GB | 1.1B | Partial | Partial | Multi | ⭐⭐⭐⭐ | ~0.8x | MIT | **Music, sound effects**, laughter |
| **Higgs Audio V2** | Boson AI | bosonai/higgs-audio-v2-generation-3B | 8–12GB | 3B | ✓ zero-shot | ✓ | Multi | ⭐⭐⭐⭐⭐ | ~1x | Apache 2.0 | **Sound effects + speech**, multi-speaker |
| **StyleTTS2** | yl4579 | yl4579/StyleTTS2-LibriTTS | 4–6GB | 600M | ✓ 5–10s | ✗ | EN | ⭐⭐⭐⭐⭐ | ~0.7x | MIT | Human-level naturalness, diffusion style |
| **OpenVoice v2** | MyShell | myshell-ai/OpenVoiceV2 | 2–4GB | 200M | ✓ **1–5s** | ✗ | Multi | ⭐⭐⭐⭐⭐ | ~0.5x | MIT | **Instant cloning**, accent/emotion transfer |
| **MeloTTS** | MyShell | myshell-ai/MeloTTS-English | 1–2GB | 250M | ✗ | ✓ | EN/ZH/JA/KO/ES/FR | ⭐⭐⭐⭐ | **<0.5x** | MIT | CPU capable, 4 EN accent variants |
| **TADA** | Hume AI | HumeAI/tada-1b | 2–4GB | 1–3B | ✓ | ✓ | EN+7 | ⭐⭐⭐⭐⭐ | **0.09x** | MIT | Zero hallucinations, **11x realtime** |
| **Spark-TTS 0.5B** | SparkAudio | SparkAudio/Spark-TTS-0.5B | 2–3GB | 500M | ✓ zero-shot | ✓ | EN/ZH/multi | ⭐⭐⭐⭐⭐ | ~0.8x | MIT | BiCodec, pitch/rate/gender params |
| **MetaVoice 1B** | MetaVoice | metavoiceio/metavoice-1B-v0.1 | 4–6GB | 1.2B | ✓ 30s ref | ✓ | EN/multi | ⭐⭐⭐⭐⭐ | <1x | Apache 2.0 | Emotional speech, zero-shot |
| **ChatTTS** | 2noise | 2noise/ChatTTS | 2–4GB | 300M | ✗ | ✓ | EN/ZH | ⭐⭐⭐⭐ | ~0.5x | MIT | Dialogue prosody, interjections, pauses |
| **Mars5-TTS** | CAMB-AI | CAMB-AI/MARS5-TTS | 6–8GB | 1.2B | ✓ 5s ref | Partial | EN | ⭐⭐⭐⭐⭐ | ~0.7x | Custom | Shallow/deep clone modes |
| **VoiceCraft** | MIT/Jason | jasonppy/VoiceCraft | 6–8GB | 800M | ✓ | ✗ | EN | ⭐⭐⭐⭐ | ~0.5x | CC-BY-NC | **Speech editing** (insert/replace on existing audio) |
| **OuteTTS 0.3** | OuteAI | OuteAI/OuteTTS-0.3-1B | 2–4GB | 1B | ✓ (profiles) | ✓ | EN/JA/KO/ZH/FR/DE | ⭐⭐⭐⭐ | ~0.8x | MIT | JSON speaker profiles |
| **GPT-SoVITS** | RVC-Boss | RVC-Boss/GPT-SoVITS | 4–8GB | 500M+ | ✓ few-shot | ✗ | EN/ZH/JA/KO | ⭐⭐⭐⭐ | ~0.6x | MIT | Fine-tune adaptation, cross-lingual |
| **Piper** | Rhasspy | rhasspy/piper-voices | <2GB | 50–150M | ✗ | ✓ | 40+ | ⭐⭐⭐ | **<0.3x** | MIT | ONNX, CPU/edge, 900+ voices |
| **Matcha-TTS** | S. Mehta | shivammehta25/Matcha-TTS | 2–4GB | 200M | ✗ | ✗ | EN/multi | ⭐⭐⭐⭐ | ~0.3x | MIT | Flow matching, minimal memory |
| **LFM2.5-Audio-1.5B** | Liquid AI | LiquidAI/LFM2.5-Audio-1.5B | 5GB | 1.5B | ✗ | ✓ | EN | ⭐⭐⭐⭐⭐ | ~0.1x | LFM Open v1.0¹ | **Unified TTS+ASR+S2S**, 4 built-in voices, sub-100ms latency |

---

## 2. VRAM Categorization

### Ultra-Light (<2GB) — Edge / CPU-capable
- Kokoro 82M (0.5GB)
- MeloTTS (1–2GB)
- Piper (0.5–2GB)
- OuteTTS 0.1-350M (<1GB)

### Light (2–8GB) — Fast, practical deployment
- Chatterbox Turbo (2–3GB) — Best quality in tier
- F5-TTS (2–4GB) — State-of-the-art speed
- Parler TTS (2–3GB) — Text description control
- Qwen3-TTS-VC-Flash (2–4GB)
- TADA (2–4GB) — Revolutionary RTF
- Spark-TTS (2–3GB)
- OpenVoice v2 (2–4GB)
- ChatTTS (2–4GB)
- Orpheus 1B (2–3GB)

- LFM2.5-Audio-1.5B (5GB) — unified TTS/ASR/S2S

### Medium (8–16GB) — Quality/speed balance
- Chatterbox (4–6GB)
- XTTS v2 (6–8GB)
- Qwen3-TTS (6–10GB) ✓
- VibeVoice 0.5B (4.5GB) ✓
- CosyVoice 2.0 (4–6GB)
- StyleTTS2 (4–6GB)
- GPT-SoVITS (4–8GB)
- MetaVoice 1B (4–6GB)
- Orpheus 3B (6–8GB)

### Heavy (16–30GB) — Best quality / multi-speaker
- VibeVoice 1.5B (12GB) ✓
- Bark (10–12GB)
- Dia 1.6B (10GB)
- Fish Audio S2-Pro (22GB) ✓ — largest

---

## 3. Unique Capability Matrix

| Capability | Models |
|-----------|--------|
| **Sound effects / music** | Bark, Higgs Audio V2, Fish S2-Pro (limited), MOSS-SoundEffect |
| **Text description → voice** (no reference audio) | Parler TTS, Qwen3 TTS (instruct mode), Higgs Audio V2 |
| **Two-speaker dialogue** | Dia 1.6B ([S1]/[S2]), VibeVoice 1.5B (Speaker 0/1), Higgs Audio V2 |
| **Emotional speech with fine control** | Fish S2-Pro (15K tags), Orpheus (emotion tags), ChatTTS (prosody), Chatterbox (exaggeration) |
| **Ultra-fast RTF (>10x realtime)** | TADA (0.09x), LFM2.5-Audio (~0.1x), CosyVoice 2.0 (0.15x), F5-TTS (0.15x), Kokoro (<0.5x) |
| **Unified audio model (TTS+ASR+S2S)** | LFM2.5-Audio-1.5B (Liquid AI) — single model handles all three tasks |
| **Long-form (>10 min)** | VibeVoice 1.5B (90 min), TADA (700s context) |
| **Voice conversion / transfer** | VoiceCraft (edit existing audio), OpenVoice v2 (tone transfer), VALL-E X |
| **Instant cloning (<5s reference)** | OpenVoice v2 (1s), Qwen3 TTS (3s), CosyVoice 2.0 (zero-shot) |

---

## 4. Competitor Platform Comparison

| Project | Models | Voice Cloning | Streaming | Batch | Waveform | Dark Mode | Mobile | Async Queue | Job History | Model Browser |
|---------|--------|--------------|-----------|-------|----------|-----------|--------|-------------|-------------|---------------|
| **AllTalk V2** | 6 | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| **GPT-SoVITS** | 1 | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Kokoro-FastAPI** | 1 | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Fish Speech WebUI** | 1 | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Coqui TTS Server** | 3 | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **OpenSpeakers v1** | 5 | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ⚠️ | ✗ |
| **OpenSpeakers v2** | **13** | ✓ | ✓ | **✓** | **✓** | ✓ | ✓ | ✓ | **✓** | **✓** |

### AllTalk V2 Full Model List
1. F5-TTS — fastest, limited cloning
2. XTTS v2 — best quality, multilingual cloning
3. Piper — lightweight/CPU
4. Parler TTS — text description control
5. Coqui VITS — flexible
6. Custom model loading

---

## 5. Feature Gaps vs. Competitors

### Already Implemented (OpenSpeakers advantage)
- ✅ Multiple model support with hot-swap GPU management (only project with this)
- ✅ Streaming audio via WebSocket (only AllTalk has this besides us)
- ✅ Voice cloning for 3/5 models
- ✅ Full async job queue (Celery + Redis) — no other open-source TTS has this
- ✅ Real-time GPU stats via WebSocket
- ✅ Dark mode + mobile responsive (unique in the field)
- ✅ Per-model parameter UI

### Gaps to Close (this plan)
- 🔲 WaveSurfer.js waveform visualization (no competitor has this)
- 🔲 Batch generation from text file
- 🔲 Full job history with search/filter
- 🔲 Toast notifications
- 🔲 Output format selection (MP3/OGG)
- 🔲 Job cancellation
- 🔲 Voice profile rename/metadata
- 🔲 Emotion tag helper UI for Fish/Chatterbox/Orpheus
- 🔲 Model browser page with install/uninstall
- 🔲 OpenAI-compatible `/v1/audio/speech` API

### New Models to Add (Phase 5)
Priority 1: F5-TTS, Chatterbox, Orpheus 3B, CosyVoice 2.0
Priority 2: Parler TTS, Dia 1.6B, XTTS v2, MeloTTS
Priority 3: Bark, Higgs Audio V2, OpenVoice v2, TADA

---

## 6. Key Differentiators After Full Plan

1. **Only TTS UI with both streaming audio AND waveform visualization**
2. **Best-in-class job management** — async queue + WebSocket + cancel + full history
3. **Most models** — 13 vs AllTalk's 6, including unique models not in any other UI
4. **Only modern reactive frontend** — SvelteKit/Svelte 5 runes vs Gradio/vanilla JS
5. **OpenAI API drop-in** — works with Continue.dev, SillyTavern, OpenWebUI, AnythingLLM
6. **Voice metadata management** — unique: rename/tag/describe cloned voices
7. **Dialogue generation UI** — Dia 1.6B with visual [S1]/[S2] composer
8. **Text-to-voice design** — Parler TTS with natural language speaker description

---

## 7. Liquid AI — LFM2.5-Audio-1.5B Deep Dive

**Model:** `LiquidAI/LFM2.5-Audio-1.5B`
**Install:** `pip install liquid-audio`
**HuggingFace:** https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B
**GitHub:** https://github.com/Liquid4All/liquid-audio
**Blog:** https://www.liquid.ai/blog/lfm2-audio-an-end-to-end-audio-foundation-model

### What It Is

LFM2.5-Audio is a **unified end-to-end audio foundation model** — not a dedicated TTS model. A single 1.5B parameter model handles:
- **Text-to-Speech (TTS)**: Natural speech from text with 4 built-in voices
- **Speech Recognition (ASR)**: ~7.53% WER across 9 benchmark datasets
- **Speech-to-Speech (S2S)**: Real-time voice conversation with integrated reasoning
- **Audio Function Calling**: Voice-controlled tool use

Architecture: 1.2B language model + 115M FastConformer audio encoder. Output sample rate: 24 kHz. Context window: 32K tokens.

### Two Generation Modes

| Mode | Input | Output | Use Case |
|------|-------|--------|----------|
| **Sequential** | Text **or** Speech | Audio (or text for ASR) | TTS / ASR — model decides modality transitions |
| **Interleaved** | Text or Speech | Interleaved text+audio tokens | Real-time S2S conversation |

**The sequential mode is straightforward TTS**: pass text in, get audio out. The model accepts either text or speech audio as input and produces speech audio as output. This is the right mode for OpenSpeakers integration — no conversational scaffolding needed.

### Python Usage (TTS — Sequential Mode)

```python
from liquid_audio import LFM2AudioModel, LFM2AudioProcessor, ChatState

processor = LFM2AudioProcessor.from_pretrained("LiquidAI/LFM2.5-Audio-1.5B").eval()
model = LFM2AudioModel.from_pretrained("LiquidAI/LFM2.5-Audio-1.5B").eval()

chat = ChatState(processor)
chat.new_turn("system")
chat.add_text("Perform TTS. Use the US female voice.")
chat.end_turn()

chat.new_turn("user")
chat.add_text("Hello, this is a test of Liquid AI speech synthesis.")
chat.end_turn()

# Sequential mode: text in → audio tokens out
audio_tokens = model.generate_sequential(**chat, max_new_tokens=512)
# Decode audio tokens → PCM waveform
audio_pcm = processor.decode_audio(audio_tokens)
```

Input can also be an audio file (for S2S or ASR):
```python
chat.add_audio("path/to/input.wav")  # speech input instead of text
```

**4 built-in voices** (no reference audio needed — selected via system prompt):
- `US Male Voice`
- `US Female Voice`
- `UK Male Voice`
- `UK Female Voice`

### Performance

| Metric | Value |
|--------|-------|
| VRAM | ~5 GB |
| Parameters | 1.5B (1.2B LM + 115M audio encoder) |
| Latency | Sub-100ms end-to-end |
| Inference speed | 10x+ faster than competing S2S models |
| ASR WER | 7.53% average across 9 datasets |
| VoiceBench Score | 54.92 (outperforms 5–7B models) |
| Output sample rate | 24 kHz |

### License

**LFM Open License v1.0** (based on Apache 2.0 with revenue restriction):
- Free for individuals, researchers, nonprofits
- Free for companies with **< $10M annual revenue**
- Commercial license required (contact sales@liquid.ai) for larger companies
- No copyleft — proprietary fine-tunes allowed
- Attribution required

### Formats Available

- Standard HuggingFace weights (bfloat16)
- **GGUF quantized** — CPU inference via llama.cpp (`LiquidAI/LFM2.5-Audio-1.5B-GGUF`)
- **ONNX** — cross-platform deployment (`LiquidAI/LFM2.5-Audio-1.5B-ONNX`)
- MLX 4-bit quantized for Apple Silicon (`mlx-community/LFM2.5-Audio-1.5B-4bit`)

### OpenSpeakers Integration Assessment

| Factor | Assessment |
|--------|-----------|
| VRAM fit | ✅ 5GB — fits on main worker |
| Install | ✅ `pip install liquid-audio` |
| Voice quality | ✅ Excellent (competitive with much larger models) |
| Voice cloning | ❌ No — 4 fixed voices only |
| Languages | ❌ English only |
| Input modes | ✅ Text **or** speech → audio out (sequential mode is clean TTS) |
| API complexity | ✅ Sequential mode is straightforward — `generate_sequential()` → `decode_audio()` → WAV |
| License | ⚠️ LFM Open v1.0 — free for personal/small-company use, not Apache/MIT |
| Primary use case | ⚠️ Conversational S2S — TTS is a secondary mode (sequential inference) |

**Recommendation:** Good candidate for a future model (`lfm2-audio` model_id). With sequential mode confirmed as a direct text→audio path, the implementation is no more complex than other HuggingFace-based models. The adapter needs to:
1. Build a `ChatState` with the voice system prompt + user text
2. Call `model.generate_sequential()` → audio tokens
3. Call `processor.decode_audio()` → PCM array
4. Pack into WAV buffer via `wave` module → `GenerateResult`

The 4-voice-only limitation and English-only support are the main reasons to keep it lower priority versus adding Chatterbox or XTTS v2 first.

> ¹ LFM Open License v1.0 — see https://www.liquid.ai/lfm-license for full terms.

---

## 8. Industry Trends (2025–2026)

1. **Efficiency focus**: Shift to sub-5GB models maintaining quality (F5-TTS, CosyVoice 2.0)
2. **LLM-based TTS**: TADA, Spark-TTS, Orpheus, CosyVoice 2.0 use LLM backbones
3. **Emotion/prosody control**: Moving from reference-only to fine-grained text tags
4. **Multilingual native**: Most new models support 10–80+ languages from the start
5. **Streaming native**: Real-time synthesis now standard (<150ms first-chunk latency)
6. **Voice design from text**: Parler, Qwen3 enable style without reference audio
7. **Sound effects integration**: Bark, Higgs, MOSS expand beyond pure TTS

---

## 9. Sources

- [F5-TTS GitHub](https://github.com/SWivid/F5-TTS)
- [XTTS v2 HuggingFace](https://huggingface.co/coqui/XTTS-v2)
- [Chatterbox — Resemble AI](https://www.resemble.ai/chatterbox/)
- [Fish Audio S2-Pro](https://fish.audio/s2/)
- [Qwen3-TTS GitHub](https://github.com/QwenLM/Qwen3-TTS)
- [VibeVoice — Microsoft](https://microsoft.github.io/VibeVoice/)
- [CosyVoice 2.0](https://cosyvoice.org/)
- [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M)
- [Bark — Suno](https://github.com/suno-ai/bark)
- [StyleTTS2](https://github.com/yl4579/StyleTTS2)
- [MeloTTS — MyShell](https://github.com/myshell-ai/MeloTTS)
- [OpenVoice v2](https://github.com/myshell-ai/OpenVoice)
- [VoiceCraft](https://github.com/jasonppy/VoiceCraft)
- [Orpheus TTS — Canopy Labs](https://github.com/canopyai/Orpheus-TTS)
- [AllTalk TTS](https://github.com/erew123/alltalk_tts)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)
- [WaveSurfer.js](https://wavesurfer.xyz/)
- [TADA — Hume AI](https://www.hume.ai/blog/opensource-tada)
- [Spark-TTS](https://github.com/SparkAudio/Spark-TTS)
- [Dia — Nari Labs](https://github.com/nari-labs/dia)
- [Higgs Audio V2 — Boson AI](https://github.com/boson-ai/higgs-audio)
- [Liquid AI LFM2.5-Audio-1.5B](https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B)
- [Liquid AI LFM2-Audio Blog Post](https://www.liquid.ai/blog/lfm2-audio-an-end-to-end-audio-foundation-model)
- [liquid-audio GitHub](https://github.com/Liquid4All/liquid-audio)
- [LFM Open License v1.0](https://www.liquid.ai/lfm-license)
- [BentoML TTS overview](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)
- [Modal TTS overview](https://modal.com/blog/open-source-tts)
