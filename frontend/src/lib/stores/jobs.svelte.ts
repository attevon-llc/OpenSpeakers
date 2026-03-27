import type { TTSJob } from '$api/tts';

// Array state — exported const, mutated in-place (never reassigned)
export const recentJobs: TTSJob[] = $state([]);

export function addOrUpdateJob(job: TTSJob): void {
  const idx = recentJobs.findIndex((j) => j.id === job.id);
  if (idx >= 0) {
    recentJobs[idx] = job;
  } else {
    recentJobs.unshift(job);
    if (recentJobs.length > 50) recentJobs.splice(50);
  }
}
