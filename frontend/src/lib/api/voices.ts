import axiosInstance from '$lib/axios';

export interface VoiceProfile {
  id: string;
  name: string;
  model_id: string;
  reference_audio_path: string;
  embedding_path: string | null;
  metadata: Record<string, unknown> | null;
  description?: string;
  tags?: string[];
  created_at: string;
}

export interface VoiceProfileUpdate {
  name?: string;
  description?: string;
  tags?: string[];
}

export interface VoiceListResponse {
  voices: VoiceProfile[];
  total: number;
}

export interface BuiltinVoice {
  id: string;
  name: string;
  language: string;
  gender: string | null;
  model_id: string;
}

export async function listVoices(modelId?: string): Promise<VoiceListResponse> {
  const res = await axiosInstance.get<VoiceListResponse>('/voices', {
    params: modelId ? { model_id: modelId } : undefined,
  });
  return res.data;
}

export async function getVoice(voiceId: string): Promise<VoiceProfile> {
  const { data } = await axiosInstance.get<VoiceProfile>(`/voices/${voiceId}`);
  return data;
}

export async function createVoiceProfile(
  name: string,
  modelId: string,
  referenceAudio: File
): Promise<VoiceProfile> {
  const form = new FormData();
  form.append('name', name);
  form.append('model_id', modelId);
  form.append('reference_audio', referenceAudio);
  const res = await axiosInstance.post<VoiceProfile>('/voices', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function updateVoice(voiceId: string, update: VoiceProfileUpdate): Promise<VoiceProfile> {
  const { data } = await axiosInstance.patch<VoiceProfile>(`/voices/${voiceId}`, update);
  return data;
}

export async function deleteVoiceProfile(voiceId: string): Promise<void> {
  await axiosInstance.delete(`/voices/${voiceId}`);
}

export async function listBuiltinVoices(modelId: string): Promise<BuiltinVoice[]> {
  const res = await axiosInstance.get<BuiltinVoice[]>(`/voices/builtin/${modelId}`);
  return res.data;
}

export function getVoiceAudioUrl(voiceId: string): string {
  return `/api/voices/${voiceId}/audio`;
}
