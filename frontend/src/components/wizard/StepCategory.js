'use client';

import React from 'react';
import { Smartphone, Laptop, Tablet, Headphones, Watch, Check } from 'lucide-react';
import { CATEGORIES } from '@/data/products';

const iconMap = {
  Smartphone,
  Laptop,
  Tablet,
  Headphones,
  Watch,
};

export default function StepCategory({ selectedCategory, onSelect }) {
  return (
    <div className="space-y-6">
      <div className="text-center max-w-xl mx-auto">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
          Langkah 1 dari 4
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
          Pilih Kategori Gadget yang Anda Butuhkan
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
          Pilih salah satu segmen teknologi yang ingin Anda bandingkan dan evaluasi secara objektif.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 max-w-3xl mx-auto">
        {CATEGORIES.map((cat) => {
          const Icon = iconMap[cat.icon] || Smartphone;
          const isSelected = selectedCategory === cat.id;

          return (
            <div
              key={cat.id}
              onClick={() => onSelect(cat.id)}
              className={`relative p-5 rounded-2xl border-2 cursor-pointer transition-all duration-200 flex flex-col justify-between group ${
                isSelected
                  ? 'border-indigo-600 dark:border-indigo-400 bg-indigo-50/60 dark:bg-indigo-950/40 shadow-lg shadow-indigo-500/10'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700'
              }`}
            >
              {isSelected && (
                <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center">
                  <Check className="w-4 h-4" />
                </div>
              )}

              <div className="space-y-3">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${
                    isSelected
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 group-hover:bg-indigo-50 dark:group-hover:bg-slate-700'
                  }`}
                >
                  <Icon className="w-6 h-6" />
                </div>

                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    {cat.label}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {cat.desc}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
