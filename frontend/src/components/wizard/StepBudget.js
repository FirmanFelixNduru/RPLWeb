'use client';

import React from 'react';
import { DollarSign, Sparkles, TrendingUp } from 'lucide-react';
import PriceTag from '@/components/ui/PriceTag';

export default function StepBudget({ category, budgetMin, budgetMax, onChangeMin, onChangeMax }) {
  // Category-specific presets for realistic guidance
  const presetsByCategory = {
    smartphone: [
      { label: 'Budget Pelajar', min: 2000000, max: 4500000 },
      { label: 'Mid-Range Terbaik', min: 4500000, max: 8000000 },
      { label: 'Flagship & Premium', min: 8000000, max: 25000000 },
    ],
    laptop: [
      { label: 'Pelajar & Mahasiswa', min: 5000000, max: 10000000 },
      { label: 'Kerja & Desain Grafis', min: 10000000, max: 20000000 },
      { label: 'Workstation & Gaming', min: 20000000, max: 35000000 },
    ],
    tablet: [
      { label: 'Catatan & Hiburan', min: 3000000, max: 7000000 },
      { label: 'Kreativitas & Desain', min: 7000000, max: 15000000 },
      { label: 'Tablet Pro Flagship', min: 15000000, max: 25000000 },
    ],
    tws: [
      { label: 'Entry ANC', min: 300000, max: 1000000 },
      { label: 'Mid-Range Harian', min: 1000000, max: 2500000 },
      { label: 'Audiophile & Flagship', min: 2500000, max: 5000000 },
    ],
    smartwatch: [
      { label: 'Fitness & Baterai Awet', min: 1500000, max: 3500000 },
      { label: 'Smart Health 3nm', min: 3500000, max: 7000000 },
      { label: 'Ultra Adventure Titanium', min: 7000000, max: 16000000 },
    ],
  };

  const currentPresets = presetsByCategory[category] || presetsByCategory.smartphone;

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <div className="text-center">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
          Langkah 2 dari 4
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
          Tentukan Batasan Anggaran (Budget)
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
          CompareBuy akan memprioritaskan rekomendasi yang paling bernilai tinggi di dalam batas anggaran ini.
        </p>
      </div>

      {/* Preset Quick Buttons */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block text-center">
          Pilih Cepat Berdasarkan Segmen Pasar:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {currentPresets.map((preset, idx) => {
            const isMatch = budgetMin === preset.min && budgetMax === preset.max;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  onChangeMin(preset.min);
                  onChangeMax(preset.max);
                }}
                className={`p-3 rounded-xl border text-xs text-left transition-all ${
                  isMatch
                    ? 'border-indigo-600 bg-indigo-50/80 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-bold shadow-sm'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:border-slate-300'
                }`}
              >
                <div className="font-bold">{preset.label}</div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  Rp {(preset.min / 1000000).toFixed(preset.min >= 1000000 ? 1 : 0)} - {(preset.max / 1000000).toFixed(0)} Jt
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Current Range Display Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-500/5 via-purple-500/5 to-slate-100 dark:from-indigo-950/30 dark:to-slate-900/60 border border-indigo-100 dark:border-indigo-900/40 text-center space-y-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Rentang Anggaran Terpilih
        </span>
        <div className="flex items-center justify-center gap-3 text-lg sm:text-2xl font-black text-slate-900 dark:text-white">
          <PriceTag price={budgetMin} size="lg" className="text-indigo-600 dark:text-indigo-400" />
          <span className="text-slate-400 font-normal">s/d</span>
          <PriceTag price={budgetMax} size="lg" className="text-purple-600 dark:text-purple-400" />
        </div>
      </div>

      {/* Sliders */}
      <div className="space-y-5 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
            <span>Batas Minimum Anggaran:</span>
            <span className="text-indigo-600 dark:text-indigo-400 font-bold">
              Rp {budgetMin.toLocaleString('id-ID')}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={budgetMax - 500000}
            step={500000}
            value={budgetMin}
            onChange={(e) => onChangeMin(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />
        </div>

        <div>
          <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
            <span>Batas Maksimum Anggaran:</span>
            <span className="text-purple-600 dark:text-purple-400 font-bold">
              Rp {budgetMax.toLocaleString('id-ID')}
            </span>
          </div>
          <input
            type="range"
            min={budgetMin + 500000}
            max={35000000}
            step={500000}
            value={budgetMax}
            onChange={(e) => onChangeMax(Number(e.target.value))}
            className="w-full accent-purple-600 cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
}
