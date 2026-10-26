'use client';

import React from 'react';
import { Check, Filter, RotateCcw } from 'lucide-react';
import { CATEGORIES } from '@/data/products';

export default function FilterPanel({
  selectedCategory,
  onSelectCategory,
  selectedBrand,
  onSelectBrand,
  selectedPriceRange,
  onSelectPriceRange,
  sortBy,
  onSelectSort,
  onResetFilters,
  brands = [],
  totalFound = 0,
}) {
  const priceRanges = [
    { label: 'Semua Budget', min: 0, max: null },
    { label: '< Rp 5 Juta', min: 0, max: 5000000 },
    { label: 'Rp 5 - 15 Juta', min: 5000000, max: 15000000 },
    { label: 'Rp 15 - 25 Juta', min: 15000000, max: 25000000 },
    { label: '> Rp 25 Juta', min: 25000000, max: null },
  ];

  return (
    <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2 min-w-0">
          <Filter className="w-4 h-4 text-indigo-500" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            Filter & Pengurutan
          </h3>
          <span className="text-xs text-slate-600 dark:text-slate-300">({totalFound} Produk)</span>
        </div>

        <button
          type="button"
          onClick={onResetFilters}
          aria-label="Reset semua filter dan pengurutan"
          className="min-w-[44px] min-h-[44px] rounded-lg text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      {/* Categories */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block">
          Kategori Gadget
        </span>
        <div role="group" aria-label="Kategori Gadget" className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => onSelectCategory('')}
            aria-pressed={selectedCategory === ''}
            className={`min-w-[44px] min-h-[44px] inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 ${
              selectedCategory === ''
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            {selectedCategory === '' && <Check aria-hidden="true" className="w-3.5 h-3.5 flex-shrink-0" />}
            Semua
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelectCategory(cat.id)}
              aria-pressed={selectedCategory === cat.id}
              className={`min-w-[44px] min-h-[44px] inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 ${
                selectedCategory === cat.id
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {selectedCategory === cat.id && <Check aria-hidden="true" className="w-3.5 h-3.5 flex-shrink-0" />}
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Brands Filter */}
      {brands.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block">
            Merek / Brand
          </span>
          <div role="group" aria-label="Merek / Brand" className="flex flex-wrap gap-1.5">
            <button
              type="button"
              onClick={() => onSelectBrand('')}
              aria-pressed={selectedBrand === ''}
              className={`min-w-[44px] min-h-[44px] inline-flex items-center justify-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 ${
                selectedBrand === ''
                  ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {selectedBrand === '' && <Check aria-hidden="true" className="w-3.5 h-3.5 flex-shrink-0" />}
              Semua Brand
            </button>
            {brands.map((b) => (
              <button
                key={b}
                type="button"
                onClick={() => onSelectBrand(b)}
                aria-pressed={selectedBrand === b}
                className={`min-w-[44px] min-h-[44px] inline-flex items-center justify-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 ${
                  selectedBrand === b
                    ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {selectedBrand === b && <Check aria-hidden="true" className="w-3.5 h-3.5 flex-shrink-0" />}
                {b}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Price Range */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block">
          Rentang Anggaran (Budget)
        </span>
        <div role="group" aria-label="Rentang Anggaran (Budget)" className="flex flex-wrap gap-1.5">
          {priceRanges.map((range, idx) => {
            const isSelected =
              selectedPriceRange.min === range.min && selectedPriceRange.max === range.max;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectPriceRange(range)}
                aria-pressed={isSelected}
                className={`min-w-[44px] min-h-[44px] inline-flex items-center justify-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 ${
                  isSelected
                    ? 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-700 font-bold'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {isSelected && <Check aria-hidden="true" className="w-3.5 h-3.5 flex-shrink-0" />}
                {range.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sorting */}
      <label className="block space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block">
          Urutkan Berdasarkan
        </span>
        <select
          value={sortBy}
          onChange={(e) => onSelectSort(e.target.value)}
          className="w-full min-h-[44px] p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-500 text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-600 dark:focus:ring-indigo-400"
        >
          <option value="score">Rekomendasi Skor Tertinggi</option>
          <option value="price_asc">Harga Terendah → Tertinggi</option>
          <option value="price_desc">Harga Tertinggi → Terendah</option>
          <option value="name">Nama Produk (A-Z)</option>
        </select>
      </label>
    </div>
  );
}
