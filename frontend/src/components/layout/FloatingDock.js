'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Scale, X, Trash2, ArrowRight } from 'lucide-react';
import { useCompare } from '@/context/CompareContext';
import PriceTag from '@/components/ui/PriceTag';

export default function FloatingDock() {
  const pathname = usePathname();
  const { compareList, removeFromCompare, clearCompare } = useCompare();

  // Hide dock if empty or when user is already on the comparison page
  if (pathname === '/compare' || compareList.length === 0) {
    return null;
  }

  const renderProductChip = (product, isMobile = false) => (
    <div
      key={product.id}
      className={`group relative flex items-center gap-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500 transition-all flex-shrink-0 ${
        isMobile ? 'pl-2 pr-0.5 py-1 max-w-[170px]' : 'pl-2.5 pr-1 py-1.5 max-w-[175px]'
      }`}
    >
      <div className={`${isMobile ? 'w-7 h-7' : 'w-8 h-8'} rounded-lg bg-white dark:bg-slate-700 overflow-hidden relative flex-shrink-0 border border-slate-200/60 dark:border-slate-700/60`}>
        <img
          src={product.image}
          alt={product.name}
          className="w-full h-full object-cover"
        />
      </div>
      <div className="flex flex-col min-w-0 max-w-[65px] sm:max-w-[80px]">
        <span className="text-[11px] font-bold text-slate-800 dark:text-slate-200 truncate leading-tight">
          {product.name}
        </span>
        <PriceTag price={product.price} size="sm" className="text-[10px] font-medium opacity-80" />
      </div>
      <button
        type="button"
        onClick={() => removeFromCompare(product.id)}
        aria-label={`Hapus ${product.name} dari perbandingan`}
        className="min-w-[40px] min-h-[40px] sm:min-w-[44px] sm:min-h-[44px] flex items-center justify-center rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors flex-shrink-0 focus:outline-none focus:ring-1 focus:ring-rose-400"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );

  return (
    <aside
      aria-label="Floating Comparison Dock"
      className="fixed inset-x-0 z-50 pointer-events-none flex justify-center px-2.5 sm:px-6"
      style={{ bottom: 'calc(12px + env(safe-area-inset-bottom, 0px))' }}
    >
      <div className="pointer-events-auto w-full max-w-4xl glass-panel bg-white/95 dark:bg-slate-900/95 rounded-2xl shadow-2xl shadow-indigo-950/20 dark:shadow-black/60 border border-indigo-200/70 dark:border-indigo-900/50 p-2.5 sm:p-4 backdrop-blur-xl animate-slide-up">
        {/* Mobile: 2-Row Layout (< sm, includes 320px - 420px viewports) */}
        <div className="flex flex-col gap-2 sm:hidden">
          {/* Row 1: Title, Counter, and Controls */}
          <div className="flex items-center justify-between gap-1.5 pb-2 border-b border-slate-200/60 dark:border-slate-800/60">
            <div className="flex items-center gap-1.5 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-indigo-600/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
                <Scale className="w-3.5 h-3.5" />
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white truncate">
                Komparasi
              </span>
              <span className="text-[11px] font-bold px-1.5 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 flex-shrink-0">
                {compareList.length}/4
              </span>
            </div>

            <div className="flex items-center gap-1.5 flex-shrink-0">
              <button
                type="button"
                onClick={clearCompare}
                className="min-h-[40px] px-2.5 py-1 text-xs font-semibold text-rose-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-xl transition-colors flex items-center gap-1"
                title="Kosongkan Semua"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>

              <Link
                href="/compare"
                className="min-h-[40px] inline-flex items-center gap-1 px-3 py-1 text-xs font-bold rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-md shadow-indigo-600/30 transition-all active:scale-95"
              >
                <span>Bandingkan</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Row 2: Horizontal Scrollable Product Strip */}
          <div className="flex items-center gap-2 overflow-x-auto w-full py-0.5 scrollbar-thin">
            {compareList.map((product) => renderProductChip(product, true))}
          </div>
        </div>

        {/* Desktop / Laptop: 1-Row 3-Zone Layout (>= sm) */}
        <div className="hidden sm:flex items-center justify-between gap-3 md:gap-4">
          {/* Zone 1: Header Info */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
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
              <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden lg:block">
                Pilih hingga 4 gadget untuk dibandingkan langsung
              </p>
            </div>
          </div>

          {/* Zone 2: Product Thumbnails (flex-1 min-w-0 for robust laptop responsiveness) */}
          <div className="flex-1 min-w-0 flex items-center gap-2 overflow-x-auto py-1 scrollbar-thin">
            {compareList.map((product) => renderProductChip(product, false))}
          </div>

          {/* Zone 3: Action Buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              type="button"
              onClick={clearCompare}
              className="min-h-[40px] px-2.5 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors flex items-center gap-1"
              title="Kosongkan Semua"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>

            <Link
              href="/compare"
              className="min-h-[40px] inline-flex items-center gap-1.5 px-4 py-2 text-xs sm:text-sm font-bold rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/40 transition-all active:scale-95"
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
