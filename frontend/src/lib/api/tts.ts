import axiosInstance from '$lib/axios';

export type JobStatus = 'pending' | 'running' | 'complete' | 'failed';

export interface GenerateRequest {
  model_id: string;
  text: string;
  voice_id?: string | null;
  speed?: number;
  pitch?: number;
  language?: string;
  extra?: Record<string, unknown>;
}

export interface GenerateResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface TTSJob {
  id: string;
  model_id: string;
  text: string;
  voice_id: string | null;
  voice_profile_id: string | null;
  parameters: Record<string, unknown> | null;
  status: JobStatus;
  error_message: string | null;
  output_path: string | null;
  duration_seconds: number | null;
  processing_time_ms: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface JobListResponse {
  jobs: TTSJob[];
  total: number;
  page: number;
  page_size: number;
}

export async function generateTTS(request: GenerateRequest): Promise<GenerateResponse> {
  const res = await axiosInstance.post<GenerateResponse>('/tts/generate', request);
  return res.data;
}

export async function getJob(jobId: string): Promise<TTSJob> {
  const res = await axiosInstance.get<TTSJob>(`/tts/jobs/${jobId}`);
  return res.data;
}

export function getAudioUrl(jobId: string): string {
  return `/api/tts/jobs/${jobId}/audio`;
}

export async function listJobs(params?: {
  page?: number;
  page_size?: number;
  model_id?: string;
  status?: JobStatus;
}): Promise<JobListResponse> {
  const res = await axiosInstance.get<JobListResponse>('/tts/jobs', { params });
  return res.data;
}

/** Poll a job until it reaches a terminal state (complete or failed). */
export async function pollJob(
  jobId: string,
  onUpdate: (job: TTSJob) => void,
  intervalMs = 1000,
  timeoutMs = 300_000
): Promise<TTSJob> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const job = await getJob(jobId);
    onUpdate(job);
    if (job.status === 'complete' || job.status === 'failed') {
      return job;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`Job ${jobId} timed out after ${timeoutMs}ms`);
}
