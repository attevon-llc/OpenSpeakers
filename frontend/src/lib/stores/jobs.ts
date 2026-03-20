import { writable } from 'svelte/store';
import type { TTSJob } from '$api/tts';

/** Recent jobs shown in the history panel, keyed by job_id. */
export const recentJobs = writable<TTSJob[]>([]);

export function addOrUpdateJob(job: TTSJob): void {
  recentJobs.update((jobs) => {
    const idx = jobs.findIndex((j) => j.id === job.id);
    if (idx >= 0) {
      const updated = [...jobs];
      updated[idx] = job;
      return updated;
    }
    return [job, ...jobs].slice(0, 50); // keep last 50
  });
}
