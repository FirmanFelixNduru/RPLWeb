'use client';

import React from 'react';
import { Sliders, Sparkles, Zap, Award } from 'lucide-react';
import { TRADE_OFF_FACTORS } from '@/data/products';

export default function StepPriority({ priorities = {}, onChangePriority }) {
  const getLevelLabel = (val) => {
    switch (val) {
      case 1:
        return { text: 'Tidak Terlalu Penting', color: 'text-slate-400 bg-slate-100 dark:bg-slate-800' };
      case 2:
        return { text: 'Penting Biasa', color: 'text-slate-600 bg-slate-200 dark:bg-slate-700' };
      case 3:
        return { text: 'Cukup Penting', color: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-950/60' };
      case 4:
        return { text: 'Sangat Penting', color: 'text-purple-600 bg-purple-50 dark:bg-purple-950/60' };
      case 5:
        return { text: 'Prioritas Tertinggi (Mutlak)', color: 'text-emerald-700 bg-emerald-100 dark:bg-emerald-950/70' };
      default:
        return { text: 'Cukup Penting', color: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-950/60' };
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
          Langkah 4 dari 4
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
          Atur Prioritas & Trade-Off Pribadi Anda
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
          Tidak ada gadget yang sempurna di segala aspek. Berikan skala prioritas (1 - 5) untuk setiap faktor penentu kepuasan Anda.
        </p>
      </div>

      <div className="space-y-4 bg-white dark:bg-slate-900 p-5 sm:p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        {TRADE_OFF_FACTORS.map((factor) => {
          const currentValue = priorities[factor.id] || 3;
          const level = getLevelLabel(currentValue);

          return (
            <div
              key={factor.id}
              className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60 space-y-2"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-bold text-slate-900 dark:text-white block">
                    {factor.label}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {factor.desc}
                  </span>
                </div>

                <span
                  className={`text-xs font-bold px-2.5 py-1 rounded-full whitespace-nowrap ${level.color}`}
                >
                  {level.text} ({currentValue}/5)
                </span>
              </div>

              {/* Slider */}
              <div className="flex items-center gap-3 pt-1">
                <span className="text-xs font-bold text-slate-400">1</span>
                <input
                  type="range"
                  min={1}
                  max={5}
                  step={1}
                  value={currentValue}
                  onChange={(e) => onChangePriority(factor.id, Number(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
                <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">5</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
