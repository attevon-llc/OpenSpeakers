export type Theme = 'dark' | 'light';

const STORAGE_KEY = 'openspeakers-theme';

// Private $state — exposed via getter function (never exported directly since it is reassigned)
let _theme: Theme = $state('dark');

export function theme(): Theme { return _theme; }

export function initTheme(): void {
  const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
  const t = stored === 'light' ? 'light' : 'dark';
  _theme = t;
  applyTheme(t);
}

export function toggleTheme(): void {
  const next: Theme = _theme === 'dark' ? 'light' : 'dark';
  _theme = next;
  localStorage.setItem(STORAGE_KEY, next);
  applyTheme(next);
}

function applyTheme(t: Theme): void {
  if (t === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}
