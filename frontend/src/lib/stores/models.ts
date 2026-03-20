import { writable, derived } from 'svelte/store';
import { listModels, type ModelInfo } from '$api/models';

export const models = writable<ModelInfo[]>([]);
export const modelsLoading = writable(false);
export const modelsError = writable<string | null>(null);

export const loadedModel = derived(models, ($models) =>
  $models.find((m) => m.status === 'loaded') ?? null
);

export const voiceCloningModels = derived(models, ($models) =>
  $models.filter((m) => m.supports_voice_cloning)
);

export async function refreshModels(): Promise<void> {
  modelsLoading.set(true);
  modelsError.set(null);
  try {
    const list = await listModels();
    models.set(list);
  } catch (err) {
    modelsError.set(err instanceof Error ? err.message : 'Failed to load models');
  } finally {
    modelsLoading.set(false);
  }
}
