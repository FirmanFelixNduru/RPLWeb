'use client';

import React from 'react';
import { Cpu, Smartphone, Battery, Camera, Wifi, HardDrive, ShieldAlert, Sparkles, Monitor, Layers } from 'lucide-react';

export default function TabSpecs({ product }) {
  if (!product) return null;

  const specRows = [
    { label: 'Layar & Resolusi', value: product.specs.display, icon: Monitor },
    { label: 'Refresh Rate', value: product.specs.refresh_rate, icon: Sparkles },
    { label: 'Prosesor / Chipset', value: product.specs.processor, icon: Cpu },
    { label: 'RAM / Memori', value: product.specs.ram, icon: Layers },
    { label: 'Penyimpanan Internal', value: product.specs.storage, icon: HardDrive },
    { label: 'Kapasitas Baterai', value: product.specs.battery, icon: Battery },
    { label: 'Konfigurasi Kamera', value: product.specs.camera, icon: Camera },
    { label: 'Sistem Operasi', value: product.specs.os, icon: Smartphone },
    { label: 'Bobot Perangkat', value: product.specs.weight, icon: Layers },
    { label: 'Konektivitas', value: product.specs.connectivity, icon: Wifi },
    { label: 'Sertifikasi Tahan Air', value: product.specs.water_resistance, icon: ShieldAlert },
    { label: 'Material Rangka', value: product.specs.build_material, icon: Layers },
    { label: 'Fitur Khusus', value: product.specs.special_features, icon: Sparkles },
  ].filter((row) => row.value && row.value !== 'N/A');

  return (
    <div className="space-y-4">
      <div className="p-3 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40 text-xs text-indigo-700 dark:text-indigo-300">
        Spesifikasi teknis terverifikasi resmi per rilis Indonesia ({product.release_year}).
      </div>

      <div className="divide-y divide-slate-200 dark:divide-slate-800 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        {specRows.map((row, idx) => {
          const Icon = row.icon;
          return (
            <div
              key={idx}
              className="grid grid-cols-1 sm:grid-cols-3 p-3.5 sm:p-4 text-sm hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
            >
              <div className="flex items-center gap-2 font-medium text-slate-500 dark:text-slate-400 mb-1 sm:mb-0">
                <Icon className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                <span>{row.label}</span>
              </div>
              <div className="sm:col-span-2 font-semibold text-slate-900 dark:text-white">
                {row.value}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
