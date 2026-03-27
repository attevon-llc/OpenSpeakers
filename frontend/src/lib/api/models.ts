import axiosInstance from '$lib/axios';

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  supports_voice_cloning: boolean;
  supports_streaming: boolean;
  supported_languages: string[];
  hf_repo: string;
  vram_gb_estimate: number;
  is_loaded: boolean;
  status: 'loaded' | 'available' | 'loading' | 'unknown';
  supports_speed: boolean;
  supports_pitch: boolean;
}

export async function listModels(): Promise<ModelInfo[]> {
  const res = await axiosInstance.get<ModelInfo[]>('/models');
  return res.data;
}

export async function getModel(modelId: string): Promise<ModelInfo> {
  const res = await axiosInstance.get<ModelInfo>(`/models/${modelId}`);
  return res.data;
}
