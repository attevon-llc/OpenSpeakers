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

export async function refreshModels(): Promise<void> {
  _loading = true;
  _error = null;
  try {
    const list = await listModels();
    models.splice(0, Infinity, ...list);
  } catch (err) {
    _error = err instanceof Error ? err.message : 'Failed to load models';
  } finally {
    _loading = false;
  }
}
