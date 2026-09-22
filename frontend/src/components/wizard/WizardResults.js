'use client';

import React from 'react';
import { Sparkles, Trophy, ArrowRight, RotateCcw, Scale, Check, Eye, HelpCircle, ShieldCheck } from 'lucide-react';
import ScoreBadge from '@/components/ui/ScoreBadge';
import PriceTag from '@/components/ui/PriceTag';
import { useCompare } from '@/context/CompareContext';

export default function WizardResults({ results = [], onReset, wizardInput }) {
  const { addToCompare, isInCompare, openProductModal } = useCompare();

  if (!results || results.length === 0) {
    return (
      <div className="text-center py-12 space-y-4 max-w-md mx-auto">
        <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
          <HelpCircle className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          Tidak Ada Perangkat yang Ditemukan
        </h3>
        <p className="text-xs text-slate-500">
          Coba perlebar rentang anggaran Anda atau sesuaikan preferensi trade-off.
        </p>
        <button
          type="button"
          onClick={onReset}
          className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold"
        >
          Ulangi Wizard
        </button>
      </div>
    );
  }

  const topPick = results[0];

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header Summary */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 text-xs font-bold border border-indigo-200 dark:border-indigo-800">
          <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
          <span>Hasil Kalkulasi Dynamic Scoring Engine</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white">
          Rekomendasi Gadget Paling Cocok untuk Anda
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
          Dievaluasi dari {results.length} perangkat di kategori{' '}
          <strong className="capitalize text-indigo-600 dark:text-indigo-400">
            {wizardInput?.category}
          </strong>{' '}
          berdasarkan bobot matematis skenario & prioritas Anda.
        </p>

        <div className="pt-2">
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Ubah Preferensi & Hitung Ulang</span>
          </button>
        </div>
      </div>

      {/* #1 Top Pick Hero Card */}
      {topPick && (
        <div className="relative p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-950 text-white shadow-2xl shadow-indigo-950/40 border border-indigo-700/50 overflow-hidden">
          {/* Decorative badge */}
          <div className="absolute top-4 right-4 flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black uppercase tracking-wider shadow-lg">
            <Trophy className="w-3.5 h-3.5" />
            <span>Pilihan Nomor 1</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            {/* Image */}
            <div className="md:col-span-4 aspect-square rounded-2xl bg-white/10 p-2 overflow-hidden backdrop-blur-md border border-white/10">
              <img
                src={topPick.product.image}
                alt={topPick.product.name}
                className="w-full h-full object-cover rounded-xl"
              />
            </div>

            {/* Content */}
            <div className="md:col-span-8 space-y-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                  {topPick.product.brand} • {topPick.product.category}
                </span>
                <h3 className="text-xl sm:text-3xl font-black text-white mt-0.5">
                  {topPick.product.name}
                </h3>
                <div className="flex items-center gap-3 mt-2">
                  <PriceTag price={topPick.product.price} size="lg" className="text-white" />
                  <ScoreBadge score={topPick.total_score} size="md" showLabel={true} />
                </div>
              </div>

              {/* Contextual Narrative: Why this product */}
              <div className="p-4 rounded-xl bg-white/10 backdrop-blur-md border border-white/15 text-xs sm:text-sm text-indigo-100 leading-relaxed whitespace-pre-line">
                {topPick.why_this_product}
              </div>

              {/* Actions */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => addToCompare(topPick.product)}
                  className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                    isInCompare(topPick.product.id)
                      ? 'bg-emerald-500 text-white'
                      : 'bg-white/20 hover:bg-white/30 text-white'
                  }`}
                >
                  {isInCompare(topPick.product.id) ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Scale className="w-4 h-4" />
                  )}
                  <span>{isInCompare(topPick.product.id) ? 'Tersimpan di Dock' : 'Tambah ke Komparasi'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => openProductModal(topPick.product)}
                  className="px-5 py-2.5 rounded-xl text-xs font-bold bg-white text-indigo-950 hover:bg-indigo-50 shadow-lg transition-all flex items-center gap-2"
                >
                  <Eye className="w-4 h-4" />
                  <span>Lihat Rincian & Harga Live</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Ranked List for Remaining Results */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <span>Alternatif Peringkat Selanjutnya</span>
          <span className="text-xs text-slate-500 font-normal">
            (Peringkat 2 hingga {results.length})
          </span>
        </h3>

        <div className="space-y-3">
          {results.slice(1).map((item) => {
            const inComp = isInCompare(item.product.id);

            return (
              <div
                key={item.product.id}
                className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-600 transition-all shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="flex items-center gap-4">
                  {/* Rank badge */}
                  <div className="w-9 h-9 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-black text-sm flex items-center justify-center flex-shrink-0">
                    #{item.rank}
                  </div>

                  <div className="w-14 h-14 rounded-xl bg-slate-100 dark:bg-slate-800 overflow-hidden flex-shrink-0">
                    <img
                      src={item.product.image}
                      alt={item.product.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      {item.product.brand}
                    </span>
                    <h4
                      onClick={() => openProductModal(item.product)}
                      className="text-sm sm:text-base font-bold text-slate-900 dark:text-white hover:text-indigo-600 cursor-pointer"
                    >
                      {item.product.name}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                      <PriceTag price={item.product.price} size="sm" />
                      <span className="text-[11px] text-slate-500">
                        • {item.budget_fit === 'within' ? 'Sesuai Budget' : item.budget_fit === 'below' ? 'Hemat Budget' : 'Di atas Budget'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-3 w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100 dark:border-slate-800">
                  <ScoreBadge score={item.total_score} size="md" />

                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => addToCompare(item.product)}
                      className={`p-2 rounded-xl text-xs font-bold transition-all ${
                        inComp
                          ? 'bg-emerald-600 text-white'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-indigo-50'
                      }`}
                      title={inComp ? 'Tersimpan di Dock' : 'Tambah ke Komparasi'}
                    >
                      {inComp ? <Check className="w-4 h-4" /> : <Scale className="w-4 h-4" />}
                    </button>

                    <button
                      type="button"
                      onClick={() => openProductModal(item.product)}
                      className="px-3 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                    >
                      Rincian
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
