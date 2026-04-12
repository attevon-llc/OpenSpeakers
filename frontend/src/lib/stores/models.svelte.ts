import { listModels, type ModelInfo } from '$api/models';

// Array state — exported const, mutated in-place (never reassigned)
export const models: ModelInfo[] = $state([]);

// Primitive state — private, exposed through getter functions (Svelte 5 module pattern)
let _loading = $state(false);
let _error: string | null = $state(null);

export function modelsLoading(): boolean { return _loading; }
export function modelsError(): string | null { return _error; }

export function loadedModel(): ModelInfo | null {
  return models.find((m) => m.status === 'loaded') ?? null;
}

export function voiceCloningModels(): ModelInfo[] {
  return models.filter((m) => m.supports_voice_cloning);
}

// Dedupe concurrent calls — multiple components calling refreshModels at the same time
// share a single in-flight request instead of racing.
let _pending: Promise<void> | null = null;

export function refreshModels(): Promise<void> {
  if (_pending) return _pending;
  _pending = (async () => {
    _loading = true;
    _error = null;
    try {
      const list = await listModels();
      models.splice(0, Infinity, ...list);
    } catch (err) {
      _error = err instanceof Error ? err.message : 'Failed to load models';
    } finally {
      _loading = false;
      _pending = null;
    }
  })();
  return _pending;
}
