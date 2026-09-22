'use client';

import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';

export default function ThemeToggle({ className = '' }) {
  const { theme, toggleTheme, mounted } = useTheme();

  if (!mounted) {
    return <div className="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-800 animate-pulse" />;
  }

  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      id="theme-toggle-btn"
      onClick={toggleTheme}
      aria-label={`Ubah ke ${isDark ? 'Mode Terang' : 'Mode Gelap'}`}
      className={`relative inline-flex items-center justify-center w-10 h-10 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-brand-500 hover:scale-105 active:scale-95 ${
        isDark
          ? 'bg-slate-800/80 text-amber-400 hover:bg-slate-700/80 border border-slate-700'
          : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200'
      } ${className}`}
    >
      {isDark ? (
        <Sun className="w-5 h-5 transition-transform duration-300 rotate-0 hover:rotate-45" />
      ) : (
        <Moon className="w-5 h-5 transition-transform duration-300 -rotate-12 hover:rotate-0" />
      )}
    </button>
  );
}
