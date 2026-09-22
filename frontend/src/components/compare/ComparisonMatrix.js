'use client';

import React from 'react';
import Link from 'next/link';
import { X, Check, Award, Sparkles, Scale, ExternalLink, ShieldCheck, Eye } from 'lucide-react';
import PriceTag from '@/components/ui/PriceTag';
import ScoreBadge from '@/components/ui/ScoreBadge';
import { useCompare } from '@/context/CompareContext';

export default function ComparisonMatrix({ products = [], highlights = [] }) {
  const { removeFromCompare, openProductModal } = useCompare();

  if (!products || products.length === 0) {
    return (
      <div className="text-center py-16 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 space-y-4 max-w-xl mx-auto shadow-sm">
        <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-950/80 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto">
          <Scale className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-bold text-slate-900 dark:text-white">
          Belum Ada Produk yang Dipilih untuk Dibandingkan
        </h3>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
          Pilih 2 hingga 4 gadget dari Katalog atau gunakan Smart Wizard untuk melihat perbandingan side-by-side dengan penanda otomatis spesifikasi terbaik.
        </p>
        <div className="pt-2">
          <Link
            href="/catalog"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20"
          >
            Buka Katalog Gadget
          </Link>
        </div>
      </div>
    );
  }

  // Spec comparison rows mapping
  const specDefinitions = [
    { key: 'display', label: 'Layar & Panel' },
    { key: 'refresh_rate', label: 'Refresh Rate' },
    { key: 'resolution', label: 'Resolusi' },
    { key: 'processor', label: 'Prosesor / SoC' },
    { key: 'ram', label: 'Kapasitas RAM' },
    { key: 'storage', label: 'Penyimpanan (Storage)' },
    { key: 'battery', label: 'Kapasitas Baterai' },
    { key: 'camera', label: 'Konfigurasi Kamera' },
    { key: 'os', label: 'Sistem Operasi' },
    { key: 'weight', label: 'Bobot Perangkat' },
    { key: 'water_resistance', label: 'Ketahanan Air / IP Rating' },
    { key: 'build_material', label: 'Material Sasis & Rangka' },
    { key: 'special_features', label: 'Fitur Spesial' },
  ];

  // Helper to determine best product for each row
  const getHighlightForSpec = (label) => {
    return highlights.find((h) => h.spec_name.toLowerCase() === label.toLowerCase());
  };

  // Find lowest price
  const lowestPrice = Math.min(...products.map((p) => p.price));

  // Find longest warranty
  const longestWarrantyMonths = Math.max(...products.map((p) => p.warranty?.duration_months || 12));

  return (
    <div className="space-y-6">
      {/* Legend & Summary Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between p-4 rounded-2xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/40 gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-indigo-900 dark:text-indigo-300">
          <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm" />
          <span>
            <strong>Auto-Highlighting Aktif:</strong> Sel berwarna hijau emerald menandakan spesifikasi paling unggul di baris tersebut.
          </span>
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          Membandingkan {products.length} perangkat sekaligus
        </span>
      </div>

      {/* Comparison Table Container */}
      <div className="overflow-x-auto rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left border-collapse">
          {/* Header Row with Product Cards */}
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80">
              <th className="p-4 sm:p-6 w-48 min-w-[180px] align-top text-xs font-bold uppercase tracking-wider text-slate-400">
                Spesifikasi & Fitur
              </th>
              {products.map((p) => (
                <th
                  key={p.id}
                  className="p-4 sm:p-6 min-w-[240px] max-w-[280px] align-top border-l border-slate-200 dark:border-slate-800"
                >
                  <div className="space-y-3">
                    <div className="relative aspect-video rounded-xl bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <img
                        src={p.image}
                        alt={p.name}
                        className="w-full h-full object-cover"
                      />
                      <button
                        type="button"
                        onClick={() => removeFromCompare(p.id)}
                        className="absolute top-2 right-2 p-1.5 rounded-full bg-slate-900/80 text-white hover:bg-rose-600 transition-colors"
                        title="Hapus dari perbandingan"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                        {p.brand}
                      </span>
                      <h4 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white leading-tight">
                        {p.name}
                      </h4>
                      <div className="mt-1">
                        <PriceTag price={p.price} size="md" />
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => openProductModal(p)}
                      className="w-full py-1.5 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 text-xs font-bold transition-colors flex items-center justify-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Rincian Lengkap</span>
                    </button>
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs sm:text-sm">
            {/* 1. Price Comparison Row */}
            <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
              <td className="p-4 font-bold text-slate-900 dark:text-white bg-slate-50/50 dark:bg-slate-950/20">
                Harga Resmi (MSRP)
              </td>
              {products.map((p) => {
                const isBestPrice = p.price === lowestPrice;
                return (
                  <td
                    key={p.id}
                    className={`p-4 border-l border-slate-200 dark:border-slate-800 font-bold ${
                      isBestPrice
                        ? 'bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 font-extrabold'
                        : 'text-slate-800 dark:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span>Rp {p.price.toLocaleString('id-ID')}</span>
                      {isBestPrice && (
                        <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-emerald-500 text-white shadow-sm">
                          Termurah
                        </span>
                      )}
                    </div>
                  </td>
                );
              })}
            </tr>

            {/* 2. Warranty Row */}
            <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
              <td className="p-4 font-bold text-slate-900 dark:text-white bg-slate-50/50 dark:bg-slate-950/20">
                Garansi Resmi
              </td>
              {products.map((p) => {
                const isBestWarranty = p.warranty?.duration_months === longestWarrantyMonths;
                return (
                  <td
                    key={p.id}
                    className={`p-4 border-l border-slate-200 dark:border-slate-800 ${
                      isBestWarranty
                        ? 'bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 font-bold'
                        : 'text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span>{p.warranty?.duration_months || 12} Bulan</span>
                      {isBestWarranty && products.length > 1 && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500 text-white shadow-sm">
                          Terlama
                        </span>
                      )}
                    </div>
                  </td>
                );
              })}
            </tr>

            {/* 3. Specs Rows */}
            {specDefinitions.map((spec) => {
              const highlight = getHighlightForSpec(spec.label);

              return (
                <tr key={spec.key} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="p-4 font-semibold text-slate-600 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-950/20">
                    {spec.label}
                  </td>
                  {products.map((p) => {
                    const val = p.specs[spec.key] || '—';
                    const isBest = highlight && highlight.best_product_id === p.id && val !== '—';

                    return (
                      <td
                        key={p.id}
                        className={`p-4 border-l border-slate-200 dark:border-slate-800 ${
                          isBest
                            ? 'bg-emerald-500/10 text-emerald-900 dark:text-emerald-200 font-bold'
                            : 'text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="leading-snug">{val}</span>
                          {isBest && products.length > 1 && (
                            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500 text-white flex-shrink-0">
                              Unggul
                            </span>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
