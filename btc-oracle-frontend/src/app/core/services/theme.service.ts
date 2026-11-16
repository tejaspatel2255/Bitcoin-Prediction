import { Injectable, signal, effect } from '@angular/core';

export type ThemeMode = 'dark' | 'light';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  readonly currentTheme = signal<ThemeMode>('dark');

  constructor() {
    // Initialize theme from localStorage or default to dark
    const savedTheme = (localStorage.getItem('btc_oracle_theme') as ThemeMode) || 'dark';
    this.setTheme(savedTheme);

    // Apply attribute change whenever theme signal updates
    effect(() => {
      const mode = this.currentTheme();
      document.documentElement.setAttribute('data-theme', mode);
      localStorage.setItem('btc_oracle_theme', mode);
    });
  }

  setTheme(mode: ThemeMode) {
    this.currentTheme.set(mode);
  }

  toggleTheme() {
    this.currentTheme.update(mode => (mode === 'dark' ? 'light' : 'dark'));
  }
}
