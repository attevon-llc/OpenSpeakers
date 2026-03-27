export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration: number;
}

// Array state — exported const, mutated in-place (never reassigned)
export const toasts: Toast[] = $state([]);

export function addToast(type: ToastType, message: string, duration = 4000): void {
  const id = (() => {
    try { return crypto.randomUUID(); } catch { /* non-secure context */ }
    const buf = new Uint8Array(16);
    crypto.getRandomValues(buf);
    return Array.from(buf, (b) => b.toString(16).padStart(2, '0')).join('');
  })();
  toasts.push({ id, type, message, duration });
  setTimeout(() => removeToast(id), duration);
}

export function removeToast(id: string): void {
  const idx = toasts.findIndex((toast) => toast.id === id);
  if (idx >= 0) toasts.splice(idx, 1);
}
