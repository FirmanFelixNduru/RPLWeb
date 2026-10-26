'use client';

import React from 'react';
import {
  Shield,
  ShieldCheck,
  MapPin,
  Clock,
  Wrench,
  Battery,
  Zap,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Info,
  HelpCircle,
  Truck
} from 'lucide-react';
import ScoreBadge from '@/components/ui/ScoreBadge';

export default function TabWarranty({ product }) {
  if (!product || !product.warranty) return null;

  const {
    duration_months,
    coverage,
    claim_ease,
    official_service_centers,
    score,
    parts_warranty_months,
    labor_warranty_months,
    warranty_type,
    battery_warranty_months,
    charger_warranty_months,
    service_type,
    warranty_source_url,
    verification_status
  } = product.warranty;

  const wTypeLower = (warranty_type || '').toLowerCase();
  const isImportNonAtpm = wTypeLower.includes('impor') || wTypeLower.includes('non-atpm');
  const isDistributorResmi = wTypeLower.includes('distributor') && (wTypeLower.includes('resmi') || wTypeLower.includes('authorized reseller'));
  const isSellerDistributor = wTypeLower.includes('penjual') || (wTypeLower.includes('distributor') && !wTypeLower.includes('resmi'));

  const vStatusLower = (verification_status || '').toLowerCase();
  const isSpecificSkuVerified = vStatusLower.includes('spesifik sku terverifikasi');
  const isSkuUnverifiedNotice = vStatusLower.includes('ketentuan sku belum terverifikasi');
  const isDistributorOrSellerNotice = vStatusLower.includes('distributor') || vStatusLower.includes('penjual');

  return (
    <div className="space-y-6 animate-fade-in text-slate-800 dark:text-slate-200">
      {/* 1. Warranty Index Banner */}
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
              Skor transparansi garansi, ketersediaan suku cadang resmi, dan kemudahan klaim di wilayah Indonesia.
            </p>
          </div>
        </div>
      </div>

      {/* 2. Warranty Classification Badges */}
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-slate-500 dark:text-slate-400">Tipe Garansi:</span>
          <span
            className={`px-2.5 py-1 rounded-lg font-bold flex items-center gap-1.5 ${
              isImportNonAtpm
                ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800'
                : isSellerDistributor
                ? 'bg-orange-100 text-orange-800 dark:bg-orange-950/60 dark:text-orange-300 border border-orange-200 dark:border-orange-800'
                : isDistributorResmi
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
                : 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800'
            }`}
          >
            {isImportNonAtpm || isSellerDistributor ? <AlertTriangle className="w-3.5 h-3.5" /> : <Shield className="w-3.5 h-3.5" />}
            {warranty_type || 'Belum Terverifikasi'}
          </span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-slate-500 dark:text-slate-400">Status Validitas:</span>
          <span
            className={`px-2.5 py-1 rounded-lg font-semibold flex items-center gap-1.5 ${
              isSpecificSkuVerified
                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                : isSkuUnverifiedNotice
                ? 'bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300 border border-sky-200 dark:border-sky-800'
                : isDistributorOrSellerNotice || isImportNonAtpm
                ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800'
                : 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
            }`}
          >
            {isSpecificSkuVerified ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            ) : isSkuUnverifiedNotice ? (
              <Info className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            )}
            {verification_status || 'Belum Terverifikasi'}
          </span>
        </div>
      </div>

      {/* 3. Primary Warranty Duration Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Card 1: Catalog Baseline / General Duration */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 text-xs font-semibold mb-1">
              <Clock className="w-4 h-4" />
              <span>{isImportNonAtpm ? 'Acuan Durasi Katalog' : 'Masa Garansi Acuan'}</span>
            </div>
            <p className="text-2xl font-black text-slate-900 dark:text-white">
              {duration_months !== null && duration_months !== undefined ? (
                <>
                  {duration_months} <span className="text-sm font-semibold text-slate-500">Bulan</span>
                </>
              ) : (
                <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Belum Terverifikasi</span>
              )}
            </p>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
            {isImportNonAtpm
              ? 'Acuan pembanding katalog (bukan garansi resmi ATPM lokal)'
              : (duration_months || 0) >= 24
              ? 'Masa pertanggungan panjang standar manufaktur'
              : 'Standar periode acuan industri'}
          </p>
        </div>

        {/* Card 2: Spare Parts Duration */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-teal-600 dark:text-teal-400 text-xs font-semibold mb-1">
              <Shield className="w-4 h-4" />
              <span>Garansi Suku Cadang (Parts)</span>
            </div>
            <p className="text-2xl font-black text-slate-900 dark:text-white">
              {parts_warranty_months !== null && parts_warranty_months !== undefined ? (
                <>
                  {parts_warranty_months} <span className="text-sm font-semibold text-slate-500">Bulan</span>
                </>
              ) : isImportNonAtpm ? (
                <span className="text-sm font-bold text-amber-600 dark:text-amber-400">Tidak Berlaku Resmi</span>
              ) : (
                <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Mengikuti Garansi Unit</span>
              )}
            </p>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
            {parts_warranty_months !== null
              ? 'Penggantian suku cadang akibat cacat pabrik'
              : isImportNonAtpm
              ? 'Pusat servis lokal tidak menjamin suku cadang resmi'
              : 'Durasi suku cadang tidak dibedakan dari garansi utama'}
          </p>
        </div>

        {/* Card 3: Labor / Service Duration */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-semibold mb-1">
              <Wrench className="w-4 h-4" />
              <span>Garansi Jasa Servis (Labor)</span>
            </div>
            <p className="text-2xl font-black text-slate-900 dark:text-white">
              {labor_warranty_months !== null && labor_warranty_months !== undefined ? (
                <>
                  {labor_warranty_months} <span className="text-sm font-semibold text-slate-500">Bulan</span>
                </>
              ) : isImportNonAtpm ? (
                <span className="text-sm font-bold text-amber-600 dark:text-amber-400">Tergantung Penjual</span>
              ) : (
                <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Mengikuti Garansi Unit</span>
              )}
            </p>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
            {labor_warranty_months !== null
              ? 'Bebas biaya teknisi perbaikan di service center resmi'
              : isImportNonAtpm
              ? 'Klaim servis bergantung pada ketentuan toko penjual'
              : 'Biaya jasa tercakup dalam periode garansi utama'}
          </p>
        </div>
      </div>

      {/* 4. Service Channels & Specific Components */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        {/* Service Type */}
        <div className="p-3.5 rounded-xl bg-slate-100/70 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-semibold mb-1">
            <Truck className="w-3.5 h-3.5" />
            <span>Layanan Purna Jual</span>
          </div>
          <p className="font-bold text-slate-900 dark:text-white text-sm">
            {service_type || 'Belum Terverifikasi'}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            {service_type === 'On-site'
              ? 'Teknisi datang ke lokasi Anda'
              : service_type === 'Carry-in'
              ? 'Unit dibawa ke pusat servis resmi'
              : service_type === 'Carry-in & On-site'
              ? 'Carry-in (On-site di kota tertentu)'
              : 'Sistem pengiriman klaim ke distributor/toko'}
          </span>
        </div>

        {/* Battery Warranty */}
        <div className="p-3.5 rounded-xl bg-slate-100/70 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold mb-1">
            <Battery className="w-3.5 h-3.5" />
            <span>Garansi Baterai</span>
          </div>
          <p className="font-bold text-slate-900 dark:text-white text-sm">
            {battery_warranty_months !== null && battery_warranty_months !== undefined ? (
              `${battery_warranty_months} Bulan`
            ) : (
              <span className="font-normal text-slate-500">Belum Terverifikasi</span>
            )}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            {battery_warranty_months !== null
              ? 'Cacat pabrik (penurunan kapasitas wajar dikecualikan)'
              : 'Tidak ada durasi terpisah dari klausul resmi'}
          </span>
        </div>

        {/* Charger / Adapter Warranty */}
        <div className="p-3.5 rounded-xl bg-slate-100/70 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-semibold mb-1">
            <Zap className="w-3.5 h-3.5" />
            <span>Garansi Charger/Adaptor</span>
          </div>
          <p className="font-bold text-slate-900 dark:text-white text-sm">
            {charger_warranty_months !== null && charger_warranty_months !== undefined ? (
              `${charger_warranty_months} Bulan`
            ) : (
              <span className="font-normal text-slate-500">Tidak Ada / Belum Terverifikasi</span>
            )}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            {charger_warranty_months !== null
              ? 'Adaptor pengisi daya bawaan dalam kotak resmi'
              : 'Adaptor dijual terpisah atau belum ada klausul'}
          </span>
        </div>

        {/* Service Centers & Ease */}
        <div className="p-3.5 rounded-xl bg-slate-100/70 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 font-semibold mb-1">
            <MapPin className="w-3.5 h-3.5" />
            <span>Jaringan Servis Resmi</span>
          </div>
          <p className="font-bold text-slate-900 dark:text-white text-sm">
            {official_service_centers} Lokasi{' '}
            <span className="text-xs font-normal text-slate-500">({claim_ease}/10 kemudahan)</span>
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            Jaringan titik purna jual di kota-kota Indonesia
          </span>
        </div>
      </div>

      {/* 5. Special Transparency Notices (for Acer, ASUS, Pixel, Xiaomi 14 Ultra) */}
      {isSkuUnverifiedNotice && (
        <div className="p-4 rounded-xl bg-sky-50/80 dark:bg-sky-950/30 border border-sky-200 dark:border-sky-800/60 text-xs space-y-1 text-sky-950 dark:text-sky-200">
          <div className="flex items-center gap-1.5 font-bold text-sky-800 dark:text-sky-300">
            <Info className="w-4 h-4 flex-shrink-0" />
            <span>Transparansi Ketentuan SKU & Kebijakan Produsen:</span>
          </div>
          <p className="leading-relaxed text-slate-700 dark:text-slate-300">
            Durasi dan program purna jual di atas merujuk pada ketentuan resmi produsen untuk lini keluarga model ini di Indonesia. Penerapan masa servis ekstra atau program proteksi kelalaian pada varian/SKU acuan tertentu dapat bergantung pada stiker distributor resmi atau registrasi kartu garansi.
          </p>
        </div>
      )}

      {isImportNonAtpm && (
        <div className="p-4 rounded-xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60 text-xs space-y-1 text-amber-950 dark:text-amber-200">
          <div className="flex items-center gap-1.5 font-bold text-amber-800 dark:text-amber-300">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>Peringatan Produk Pasar Impor (Non-ATPM):</span>
          </div>
          <p className="leading-relaxed text-slate-700 dark:text-slate-300">
            Model ini tidak didistribusikan secara resmi oleh ATPM prinsipal di Indonesia. {duration_months !== null && duration_months !== undefined ? `Angka ${duration_months} bulan` : 'Durasi yang tercantum'} merupakan acuan katalog; klaim garansi bergantung sepenuhnya pada penawaran toko/penjual marketplace, dan pusat servis resmi lokal tidak menjamin ketersediaan suku cadang resmi.
          </p>
        </div>
      )}

      {/* 6. Comprehensive Coverage Details */}
      <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-2">
        <div className="flex items-center justify-between">
          <h5 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-indigo-500" />
            <span>Lingkup Perlindungan Garansi</span>
          </h5>
          {warranty_source_url && (
            <a
              href={warranty_source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
            >
              <span>Ketentuan Resmi</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
          {coverage}
        </p>
      </div>

      {/* 7. Consumer Claim Guide Tips */}
      <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 text-xs space-y-2 text-amber-900 dark:text-amber-200">
        <span className="font-bold flex items-center gap-1.5">
          <HelpCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
          Tips Klaim Garansi untuk Konsumen Cerdas:
        </span>
        <ul className="list-disc list-inside space-y-1 text-slate-700 dark:text-slate-300">
          <li>Simpan bukti invoice pembelian marketplace digital dan nota fisik di kotak kemasan asli.</li>
          <li>Pastikan nomor IMEI / Serial Number di bodi perangkat sesuai dengan kartu garansi resmi.</li>
          <li>Lakukan unboxing video tanpa jeda saat barang pertama kali diterima untuk perlindungan komplain toko 7 hari.</li>
        </ul>
      </div>
    </div>
  );
}
