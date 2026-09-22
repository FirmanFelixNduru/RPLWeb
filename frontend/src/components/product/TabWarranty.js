'use client';

import React from 'react';
import { Shield, ShieldCheck, MapPin, Clock, Wrench, CheckCircle, HelpCircle } from 'lucide-react';
import ScoreBadge from '@/components/ui/ScoreBadge';

export default function TabWarranty({ product }) {
  if (!product || !product.warranty) return null;

  const { duration_months, coverage, claim_ease, official_service_centers, score } = product.warranty;

  return (
    <div className="space-y-6">
      {/* Warranty Index Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-teal-500/10 via-emerald-500/10 to-indigo-500/10 dark:from-teal-950/40 dark:to-indigo-950/40 border border-emerald-200 dark:border-emerald-800/60 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-center sm:text-left">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center flex-shrink-0">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center gap-2 justify-center sm:justify-start">
              <h4 className="text-base font-bold text-slate-900 dark:text-white">
                After-Sales & Warranty Index
              </h4>
              <ScoreBadge score={score} size="sm" />
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
              Skor transparansi garansi, ketersediaan suku cadang, dan kemudahan klaim di wilayah Indonesia.
            </p>
          </div>
        </div>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Metric 1: Duration */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 text-xs font-semibold mb-1">
            <Clock className="w-4 h-4" />
            <span>Masa Garansi Resmi</span>
          </div>
          <p className="text-2xl font-black text-slate-900 dark:text-white">
            {duration_months} <span className="text-sm font-semibold text-slate-500">Bulan</span>
          </p>
          <span className="text-[11px] text-slate-500 dark:text-slate-400">
            {duration_months >= 24 ? 'Garansi Panjang Eksklusif' : 'Standar Industri Elektronik'}
          </span>
        </div>

        {/* Metric 2: Claim Ease */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-semibold mb-1">
            <Wrench className="w-4 h-4" />
            <span>Tingkat Kemudahan Klaim</span>
          </div>
          <p className="text-2xl font-black text-slate-900 dark:text-white">
            {claim_ease} <span className="text-sm font-semibold text-slate-500">/ 10</span>
          </p>
          <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden mt-1.5">
            <div
              className="bg-emerald-500 h-full rounded-full"
              style={{ width: `${claim_ease * 10}%` }}
            />
          </div>
        </div>

        {/* Metric 3: Service Centers */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 text-xs font-semibold mb-1">
            <MapPin className="w-4 h-4" />
            <span>Titik Service Center Resmi</span>
          </div>
          <p className="text-2xl font-black text-slate-900 dark:text-white">
            {official_service_centers}{' '}
            <span className="text-sm font-semibold text-slate-500">Lokasi</span>
          </p>
          <span className="text-[11px] text-slate-500 dark:text-slate-400">
            Tersebar di kota-kota besar Indonesia
          </span>
        </div>
      </div>

      {/* Coverage Details */}
      <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-2">
        <h5 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-indigo-500" />
          <span>Lingkup Perlindungan Garansi</span>
        </h5>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
          {coverage}
        </p>
      </div>

      {/* Consumer Claim Guide Tips */}
      <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 text-xs space-y-2 text-amber-900 dark:text-amber-200">
        <span className="font-bold flex items-center gap-1.5">
          <HelpCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
          Tips Klaim Garansi untuk Konsumen Cerdas:
        </span>
        <ul className="list-disc list-inside space-y-1 text-slate-700 dark:text-slate-300">
          <li>Simpan bukti invoice pembelian marketplace digital dan nota fisik di kotak kemasan asli.</li>
          <li>Pastikan nomor IMEI / Serial Number di bodi perangkat sesuai dengan kartu garansi resmi.</li>
          <li>Lakukan unboxing video tanpa jeda saat barang pertama kali diterima untuk perlindungan garansi toko 7 hari.</li>
        </ul>
      </div>
    </div>
  );
}
