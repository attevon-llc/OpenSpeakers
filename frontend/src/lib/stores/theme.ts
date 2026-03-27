// Re-exports Svelte 5 $state and getter functions from theme.svelte.ts.
// theme is a getter function — call it as theme() to get the current value.
export { theme, initTheme, toggleTheme, type Theme } from './theme.svelte';
