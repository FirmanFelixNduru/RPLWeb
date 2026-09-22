'use client';

import React from 'react';
import { Check, Flame, Briefcase, Camera, Video, GraduationCap, Dumbbell, Film, Compass } from 'lucide-react';
import { SCENARIOS } from '@/data/products';

const iconMap = {
  gaming: Flame,
  productivity: Briefcase,
  photography: Camera,
  content_creation: Video,
  business: Briefcase,
  student: GraduationCap,
  fitness: Dumbbell,
  multimedia: Film,
  casual: Compass,
};

export default function StepScenario({ selectedScenarios = [], onToggleScenario }) {
  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="text-center">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
          Langkah 3 dari 4
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
          Bagaimana Skenario Penggunaan Utama Anda?
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
          Pilih 1 atau lebih skenario aktivitas harian Anda. Algoritma CompareBuy akan menyesuaikan bobot kalkulasi perangkat secara spesifik.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {SCENARIOS.map((sc) => {
          const Icon = iconMap[sc.id] || Compass;
          const isSelected = selectedScenarios.includes(sc.id);

          return (
            <div
              key={sc.id}
              onClick={() => onToggleScenario(sc.id)}
              className={`relative p-4 rounded-2xl border-2 cursor-pointer transition-all duration-200 flex flex-col justify-between group ${
                isSelected
                  ? 'border-indigo-600 dark:border-indigo-400 bg-indigo-50/70 dark:bg-indigo-950/40 shadow-md shadow-indigo-500/10'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center transition-colors ${
                    isSelected
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 group-hover:bg-indigo-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                </div>

                <div
                  className={`w-5 h-5 rounded-full border flex items-center justify-center transition-colors ${
                    isSelected
                      ? 'bg-indigo-600 border-indigo-600 text-white'
                      : 'border-slate-300 dark:border-slate-700'
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3" />}
                </div>
              </div>

              <div className="mt-3">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  {sc.label}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">
                  {sc.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {selectedScenarios.length > 0 && (
        <div className="text-center text-xs font-semibold text-indigo-600 dark:text-indigo-400">
          ✓ {selectedScenarios.length} skenario terpilih untuk penyesuaian bobot scoring
        </div>
      )}
    </div>
  );
}
