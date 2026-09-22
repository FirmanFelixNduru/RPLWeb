'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Scale, X, Trash2, ArrowRight } from 'lucide-react';
import { useCompare } from '@/context/CompareContext';
import PriceTag from '@/components/ui/PriceTag';

export default function FloatingDock() {
  const { compareList, removeFromCompare, clearCompare } = useCompare();

  if (compareList.length === 0) {
    return null;
  }

  return (
    <aside aria-label="Floating Comparison Dock" className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 w-[94%] max-w-4xl animate-slide-up">
      <div className="glass-panel bg-white/95 dark:bg-slate-900/95 rounded-2xl shadow-2xl shadow-indigo-950/20 dark:shadow-black/60 border border-indigo-200/60 dark:border-indigo-900/40 p-3 sm:p-4 backdrop-blur-xl">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4">
          {/* Header info */}
          <div className="flex items-center gap-2.5 self-start sm:self-center">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <Scale className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                  Komparasi Produk
                </span>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300">
                  {compareList.length} / 4
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">
                Pilih hingga 4 gadget untuk dibandingkan langsung
              </p>
            </div>
          </div>

          {/* Product Thumbnails */}
          <div className="flex items-center gap-2 overflow-x-auto max-w-full py-1">
            {compareList.map((product) => (
              <div
                key={product.id}
                className="group relative flex items-center gap-2 pr-6 pl-1.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500 transition-all flex-shrink-0"
              >
                <div className="w-8 h-8 rounded-lg bg-white dark:bg-slate-700 overflow-hidden relative flex-shrink-0">
                  <img
                    src={product.image}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="flex flex-col max-w-[100px] sm:max-w-[120px]">
                  <span className="text-[11px] font-bold text-slate-800 dark:text-slate-200 truncate leading-tight">
                    {product.name}
                  </span>
                  <PriceTag price={product.price} size="sm" className="text-[10px] font-medium opacity-80" />
                </div>
                <button
                  type="button"
                  onClick={() => removeFromCompare(product.id)}
                  aria-label={`Hapus ${product.name} dari perbandingan`}
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1 rounded-full text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 self-end sm:self-center">
            <button
              type="button"
              onClick={clearCompare}
              className="px-2.5 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-1"
              title="Kosongkan Semua"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Reset</span>
            </button>

            <Link
              href="/compare"
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs sm:text-sm font-bold rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/40 transition-all active:scale-95"
            >
              <span>Bandingkan</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </aside>
  );
}
