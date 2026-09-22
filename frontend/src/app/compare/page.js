'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Scale, Plus, Trash2, ArrowLeft, Loader2, Sparkles, Layers } from 'lucide-react';
import { useCompare } from '@/context/CompareContext';
import { compareProducts } from '@/lib/api';
import ComparisonMatrix from '@/components/compare/ComparisonMatrix';
import { PRODUCTS } from '@/data/products';

export default function ComparePage() {
  const { compareList, clearCompare, addToCompare } = useCompare();
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAddDropdown, setShowAddDropdown] = useState(false);

  // Fetch comparison data whenever compareList changes
  useEffect(() => {
    async function loadMatrix() {
      if (compareList.length === 0) {
        setComparisonData(null);
        return;
      }

      setLoading(true);
      try {
        const ids = compareList.map((p) => p.id);
        const data = await compareProducts(ids);
        setComparisonData(data);
      } catch (err) {
        console.error('Failed to load comparison data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadMatrix();
  }, [compareList]);

  // Products available to add (not already in compare)
  const availableToAdd = PRODUCTS.filter(
    (p) => !compareList.some((cp) => cp.id === p.id)
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider">
            <Scale className="w-4 h-4" />
            <span>Matriks Komparasi Multi-Perangkat</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-black text-slate-900 dark:text-white mt-1">
            Perbandingan Side-by-Side
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Penanda otomatis (Auto-Highlighting) membantu melihat keunggulan riil di setiap sektor spesifikasi.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2.5 self-start sm:self-center">
          {compareList.length > 0 && (
            <button
              type="button"
              onClick={clearCompare}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-semibold text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Kosongkan Matriks</span>
            </button>
          )}

          {compareList.length < 4 && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowAddDropdown(!showAddDropdown)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>Tambah Produk ({compareList.length}/4)</span>
              </button>

              {/* Add Dropdown */}
              {showAddDropdown && (
                <div className="absolute right-0 mt-2 w-72 max-h-80 overflow-y-auto rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-2 z-50 animate-slide-up">
                  <span className="text-[11px] font-bold text-slate-400 px-3 py-1.5 block uppercase tracking-wider">
                    Pilih Produk untuk Ditambahkan:
                  </span>
                  {availableToAdd.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => {
                        addToCompare(p);
                        setShowAddDropdown(false);
                      }}
                      className="w-full p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-left flex items-center gap-2.5 transition-colors"
                    >
                      <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 overflow-hidden flex-shrink-0">
                        <img
                          src={p.image}
                          alt={p.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="truncate">
                        <div className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">
                          {p.name}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Rp {p.price.toLocaleString('id-ID')}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Content Matrix */}
      {loading ? (
        <div className="text-center py-20 space-y-4">
          <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mx-auto" />
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Menganalisis Spesifikasi & Menentukan Auto-Highlighting...
          </h3>
        </div>
      ) : (
        <ComparisonMatrix
          products={comparisonData?.products || compareList}
          highlights={comparisonData?.highlights || []}
        />
      )}
    </div>
  );
}
