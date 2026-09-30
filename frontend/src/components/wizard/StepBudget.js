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

      {/* Integrated Dual-Thumb Range Slider */}
      <div className="bg-white dark:bg-slate-900 p-6 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-8">
        <div className="text-center">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            Geser kedua tuas untuk menentukan batas minimum & maksimum anggaran:
          </span>
        </div>

        {/* Slider Container with Floating Tooltips */}
        <div className="relative pt-8 pb-4 px-2">
          {/* Floating Bubble for Min Thumb */}
          <div
            className="absolute top-0 -translate-x-1/2 transition-all duration-75 pointer-events-none z-20 flex flex-col items-center"
            style={{
              left: `${Math.min(95, Math.max(5, ((budgetMin - 0) / (35000000 - 0)) * 100))}%`,
            }}
          >
            <span className="px-2.5 py-1 rounded-lg bg-indigo-600 text-white text-[11px] font-bold shadow-md whitespace-nowrap">
              Min: Rp {(budgetMin / 1000000).toFixed(budgetMin >= 1000000 ? 1 : 0)} Jt
            </span>
            <div className="w-1.5 h-1.5 bg-indigo-600 rotate-45 -mt-0.5" />
          </div>

          {/* Floating Bubble for Max Thumb */}
          <div
            className="absolute top-0 -translate-x-1/2 transition-all duration-75 pointer-events-none z-20 flex flex-col items-center"
            style={{
              left: `${Math.min(95, Math.max(5, ((budgetMax - 0) / (35000000 - 0)) * 100))}%`,
            }}
          >
            <span className="px-2.5 py-1 rounded-lg bg-purple-600 text-white text-[11px] font-bold shadow-md whitespace-nowrap">
              Max: Rp {(budgetMax / 1000000).toFixed(0)} Jt
            </span>
            <div className="w-1.5 h-1.5 bg-purple-600 rotate-45 -mt-0.5" />
          </div>

          {/* Unified Track */}
          <div className="relative h-2.5 w-full rounded-full bg-slate-200 dark:bg-slate-800">
            {/* Active Range Highlight */}
            <div
              className="absolute h-full bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full"
              style={{
                left: `${((budgetMin - 0) / (35000000 - 0)) * 100}%`,
                width: `${(((budgetMax - budgetMin) - 0) / (35000000 - 0)) * 100}%`,
              }}
            />

            {/* Min Range Input */}
            <input
              type="range"
              min={0}
              max={35000000}
              step={500000}
              value={budgetMin}
              onChange={(e) => {
                const val = Number(e.target.value);
                if (val <= budgetMax - 500000) {
                  onChangeMin(val);
                }
              }}
              className="absolute left-0 top-0 w-full h-full appearance-none bg-transparent pointer-events-none z-30 cursor-pointer
                [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-indigo-600 [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white dark:[&::-webkit-slider-thumb]:border-slate-900 [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform
                [&::-moz-range-thumb]:pointer-events-auto [&::-moz-range-thumb]:w-6 [&::-moz-range-thumb]:h-6 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-indigo-600 [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-white dark:[&::-moz-range-thumb]:border-slate-900 [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:hover:scale-110 [&::-moz-range-thumb]:transition-transform"
              aria-label="Batas Minimum Anggaran"
            />

            {/* Max Range Input */}
            <input
              type="range"
              min={0}
              max={35000000}
              step={500000}
              value={budgetMax}
              onChange={(e) => {
                const val = Number(e.target.value);
                if (val >= budgetMin + 500000) {
                  onChangeMax(val);
                }
              }}
              className="absolute left-0 top-0 w-full h-full appearance-none bg-transparent pointer-events-none z-30 cursor-pointer
                [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-purple-600 [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white dark:[&::-webkit-slider-thumb]:border-slate-900 [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform
                [&::-moz-range-thumb]:pointer-events-auto [&::-moz-range-thumb]:w-6 [&::-moz-range-thumb]:h-6 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-purple-600 [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-white dark:[&::-moz-range-thumb]:border-slate-900 [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:hover:scale-110 [&::-moz-range-thumb]:transition-transform"
              aria-label="Batas Maksimum Anggaran"
            />
          </div>

          <div className="flex justify-between items-center text-[11px] font-semibold text-slate-400 mt-5">
            <span>Rp 0 (Entry Level)</span>
            <span>Rp 35.000.000+ (Ultra High-End)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
