'use client';

import React from 'react';
import Link from 'next/link';
import { X, Trophy, Sparkles, Scale, ShieldCheck, Eye, Cpu, Camera, Battery, Monitor, Layers, DollarSign, Volume2, Smartphone } from 'lucide-react';
import PriceTag from '@/components/ui/PriceTag';
import { useCompare } from '@/context/CompareContext';

/**
 * Helper to determine if price comparison is eligible for "MSRP Termurah" highlight.
 * Rule Revisi 5 & Poin 3:
 * 1. Must be same category.
 * 2. Source status must be verified official (rejects lp-004 unverified SKU, sm-003/sm-004 import).
 * 3. Compared configurations must be comparable (RAM & Storage tiers must be equal).
 */
export function checkPriceHighlightEligibility(products = [], isSameCategory = true) {
  if (!isSameCategory || !products || products.length <= 1) {
    return { eligible: false, reason: 'cross_category', comparableConfigs: false };
  }

  // 1. Status sumber terverifikasi
  const hasUnverifiedOrImport = products.some((p) => {
    if (p.id === 'lp-004' || p.id === 'sm-003' || p.id === 'sm-004') return true;
    const variantsNote = (p.specs?.variants_note || '').toLowerCase();
    if (variantsNote.includes('belum terverifikasi') || variantsNote.includes('impor')) return true;
    const wStatus = (p.warranty?.verification_status || '').toLowerCase();
    if (wStatus.includes('sku belum terverifikasi') || wStatus.includes('impor')) return true;
    return false;
  });
  if (hasUnverifiedOrImport) {
    return { eligible: false, reason: 'unverified_or_import', comparableConfigs: false };
  }

  // 2. Konfigurasi pembanding harus sebanding
  const getCapacity = (p) => {
    const cfg = (p.specs?.base_configuration || '').toLowerCase();
    const ramSpec = (p.specs?.ram || '').toLowerCase();
    const storageSpec = (p.specs?.storage || '').toLowerCase();

    const ramMatch = cfg.match(/(\d+)\s*gb\s*ram/i) || ramSpec.match(/(\d+)\s*gb/i);
    const ram = ramMatch ? parseInt(ramMatch[1], 10) : null;

    // Strip RAM portion to prevent false storage match
    const cfgWithoutRam = cfg.replace(/(\d+)\s*gb\s*ram/i, '');

    let storage = null;
    const tbMatch = cfgWithoutRam.match(/(\d+(?:\.\d+)?)\s*tb\b/i) || storageSpec.match(/(\d+(?:\.\d+)?)\s*tb\b/i);
    if (tbMatch) {
      storage = parseFloat(tbMatch[1]) * 1024;
    } else {
      const gbMatch = cfgWithoutRam.match(/(\d+)\s*gb\b/i) || storageSpec.match(/(\d+)\s*gb\b/i);
      if (gbMatch) storage = parseInt(gbMatch[1], 10);
    }
    return { ram, storage };
  };

  const caps = products.map(getCapacity);
  const first = caps[0];
  const hasMemorySpecs = caps.some((c) => c.ram !== null || c.storage !== null);

  if (!hasMemorySpecs) {
    return { eligible: true, reason: 'comparable', comparableConfigs: true };
  }

  const comparableConfigs = caps.every(
    (c) => c.ram === first.ram && c.storage === first.storage
  );

  return {
    eligible: comparableConfigs,
    reason: comparableConfigs ? 'comparable' : 'different_configurations',
    comparableConfigs,
  };
}

export default function ComparisonMatrix({
  products = [],
  highlights = [],
  winSummary: propWinSummary = null,
  isSameCategory: propIsSameCategory = null,
  tiedSectorsSummary: propTiedSectorsSummary = null,
}) {
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

  // Category consistency check
  const categories = Array.from(new Set(products.map((p) => p.category)));
  const isSameCategory = propIsSameCategory !== null
    ? propIsSameCategory
    : categories.length === 1;
  const currentCategory = isSameCategory ? categories[0] : null;

  // Category relevant dimensions definition
  const CATEGORY_RELEVANT_DIMENSIONS = {
    smartphone: ['performance', 'camera', 'battery', 'display', 'build_quality', 'value', 'audio', 'software'],
    laptop: ['performance', 'camera', 'battery', 'display', 'build_quality', 'value', 'audio', 'software'],
    tablet: ['performance', 'camera', 'battery', 'display', 'build_quality', 'value', 'audio', 'software'],
    smartwatch: ['performance', 'battery', 'display', 'build_quality', 'value', 'audio', 'software'],
    tws: ['performance', 'battery', 'build_quality', 'value', 'audio', 'software'],
  };

  const applicableDimensions = isSameCategory
    ? (CATEGORY_RELEVANT_DIMENSIONS[currentCategory] || [])
    : [];

  // Helper to determine best product for each row by key or label
  const getHighlightForSpec = (key, label) => {
    if (!highlights || highlights.length === 0) return null;
    const cleanKey = (key || '').toLowerCase().trim();
    const cleanLabel = (label || '').toLowerCase().trim();
    return highlights.find((h) => {
      const hName = (h.spec_name || '').toLowerCase().trim();
      return hName === cleanKey || hName === cleanLabel;
    });
  };

  // 8 Dimensions Definitions with Icons
  const dimensionDefinitions = [
    { key: 'performance', attr: 'score_performance', label: 'Skor Performa', icon: Cpu },
    { key: 'camera', attr: 'score_camera', label: 'Skor Kamera', icon: Camera },
    { key: 'battery', attr: 'score_battery', label: 'Skor Baterai', icon: Battery },
    { key: 'display', attr: 'score_display', label: 'Skor Layar', icon: Monitor },
    { key: 'build_quality', attr: 'score_build_quality', label: 'Skor Build Quality', icon: Layers },
    { key: 'value', attr: 'score_value', label: 'Skor Value for Money', icon: DollarSign },
    { key: 'audio', attr: 'score_audio', label: 'Skor Audio', icon: Volume2 },
    { key: 'software', attr: 'score_software', label: 'Skor Software & Update', icon: Smartphone },
  ];

  // Win-count calculation (use prop if provided, else compute reliably)
  let winSummary = propWinSummary;
  let tiedSectorsSummary = propTiedSectorsSummary || [];

  if (!winSummary && isSameCategory) {
    const counts = {};
    const wins = {};
    const ties = {};
    products.forEach((p) => {
      counts[p.id] = 0;
      wins[p.id] = [];
      ties[p.id] = [];
    });

    dimensionDefinitions.forEach((dim) => {
      if (!applicableDimensions.includes(dim.key)) return;
      const highlight = getHighlightForSpec(dim.key, dim.label);
      if (!highlight) return;

      const bestIds = highlight.best_product_ids && highlight.best_product_ids.length > 0
        ? highlight.best_product_ids
        : (highlight.best_product_id ? [highlight.best_product_id] : []);

      if (highlight.is_tie && bestIds.length > 1) {
        bestIds.forEach((pid) => {
          if (counts[pid] !== undefined) {
            counts[pid] += 1;
            ties[pid].push(`${dim.label} (Seri)`);
          }
        });
        const tiedNames = bestIds.map((pid) => products.find((p) => p.id === pid)?.name || pid);
        tiedSectorsSummary.push(`${dim.label}: Seri antara ${tiedNames.join(', ')}`);
      } else if (bestIds.length === 1) {
        const winnerId = bestIds[0];
        if (counts[winnerId] !== undefined) {
          counts[winnerId] += 1;
          wins[winnerId].push(dim.label);
        }
      }
    });

    winSummary = products.map((p) => ({
      product_id: p.id,
      product_name: p.name,
      win_count: counts[p.id],
      winning_sectors: wins[p.id],
      tied_sectors: ties[p.id],
      solo_wins: wins[p.id].length,
      shared_wins: ties[p.id].length,
    }));
  }

  // Find lowest price among comparable products
  const lowestPrice = Math.min(...products.map((p) => p.price));
  // Strict price rule (Revisi 5 & Poin 3): Verify source status and configuration comparability
  const priceEligibility = checkPriceHighlightEligibility(products, isSameCategory);
  const isPriceHighlightEligible = priceEligibility.eligible;
  const hasComparableConfigs = priceEligibility.comparableConfigs;

  // Strict warranty rule (Revisi 6): Do not award longest warranty if any product has unverified SKU or is import/non-ATPM
  const hasUnverifiedWarranty = products.some((p) => {
    const w = p.warranty;
    const vStatus = (w?.verification_status || '').toLowerCase();
    const wType = (w?.warranty_type || '').toLowerCase();
    return (
      p.id === 'lp-004' ||
      p.id === 'lp-002' ||
      vStatus.includes('sku belum terverifikasi') ||
      wType.includes('impor') ||
      wType.includes('non-atpm')
    );
  });

  const validWarrantyDurations = !hasUnverifiedWarranty
    ? products
        .map((p) => p.warranty?.parts_warranty_months || p.warranty?.duration_months)
        .filter((d) => typeof d === 'number' && d > 0)
    : [];
  const longestWarrantyMonths = validWarrantyDurations.length > 0 ? Math.max(...validWarrantyDurations) : null;

  // Complete spec definitions (matching Revisi 8 and categories)
  const allSpecDefinitions = [
    { key: 'display', label: 'Layar & Resolusi' },
    { key: 'refresh_rate', label: 'Refresh Rate' },
    { key: 'resolution', label: 'Resolusi' },
    { key: 'processor', label: 'Prosesor / Chipset' },
    { key: 'gpu', label: 'Kartu Grafis / GPU' },
    { key: 'ram', label: 'RAM / Memori' },
    { key: 'storage', label: 'Penyimpanan Internal' },
    { key: 'battery', label: 'Kapasitas Baterai' },
    { key: 'charging', label: 'Pengisian Daya / Charger' },
    { key: 'ports', label: 'Port & Konektor I/O' },
    { key: 'driver_size', label: 'Ukuran Driver Audio' },
    { key: 'anc', label: 'Peredam Bising (ANC)' },
    { key: 'codec', label: 'Dukungan Codec Audio' },
    { key: 'sensors', label: 'Sensor & Pelacakan' },
    { key: 'camera', label: 'Konfigurasi Kamera' },
    { key: 'os', label: 'Sistem Operasi' },
    { key: 'weight', label: 'Bobot Perangkat' },
    { key: 'water_resistance', label: 'Sertifikasi Tahan Air' },
    { key: 'build_material', label: 'Material Rangka' },
    { key: 'special_features', label: 'Fitur Khusus' },
  ];

  // Filter out spec rows where all compared products have "—" or are undefined
  const activeSpecDefinitions = allSpecDefinitions.filter((spec) => {
    return products.some((p) => {
      const val = p.specs ? p.specs[spec.key] : null;
      return val && val !== '—' && val !== 'N/A';
    });
  });

  return (
    <div className="space-y-6">
      {/* Legend & Summary Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between p-4 rounded-2xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/40 gap-3">
        <div className="flex flex-wrap items-center gap-3 text-xs font-semibold text-indigo-900 dark:text-indigo-300">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm" />
            <span>
              <strong>Auto-Highlighting Aktif:</strong> Sel hijau emerald menandakan keunggulan di sektor/spesifikasi tersebut.
            </span>
          </div>
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          Membandingkan {products.length} perangkat {isSameCategory ? `kategori ${currentCategory}` : 'lintas kategori'}
        </span>
      </div>

      {/* Evaluation / Win-Count Section */}
      {isSameCategory && winSummary && winSummary.length > 0 ? (
        <div className="p-5 sm:p-6 rounded-3xl bg-gradient-to-br from-indigo-900/10 via-slate-50 to-white dark:from-indigo-950/40 dark:via-slate-900 dark:to-slate-900 border border-indigo-200/80 dark:border-indigo-800/40 space-y-4 shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600 text-white shadow-md shadow-indigo-600/30">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
                Evaluasi Sektor Kinerja (Win-Count Matrix)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Menilai keunggulan masing-masing perangkat pada {applicableDimensions.length} sektor performa ({currentCategory}). Setiap hasil seri memberikan +1 shared win kepada setiap produk yang berbagi skor tertinggi (sehingga total akumulasi kemenangan dapat melampaui {applicableDimensions.length} sektor fisik).
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
            {winSummary.map((item) => {
              const prod = products.find((p) => p.id === item.product_id);
              const isLead = item.win_count > 0 && item.win_count === Math.max(...winSummary.map((w) => w.win_count));
              const soloCount = item.solo_wins ?? item.winning_sectors.length;
              const sharedCount = item.shared_wins ?? item.tied_sectors.length;

              return (
                <div
                  key={item.product_id}
                  className={`p-4 rounded-2xl border transition-all ${
                    isLead
                      ? 'bg-emerald-500/10 border-emerald-500/30 dark:bg-emerald-950/20 dark:border-emerald-700/50 shadow-sm'
                      : 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 truncate">
                      {prod?.brand || ''}
                    </span>
                    <span
                      className={`text-xs font-black px-2.5 py-0.5 rounded-full ${
                        isLead
                          ? 'bg-emerald-500 text-white shadow-sm'
                          : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      {item.win_count} Kemenangan Sektor
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white mt-1 truncate">
                    {item.product_name}
                  </h4>
                  <div className="flex items-center gap-1.5 mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      {soloCount} unggul mutlak
                    </span>
                    <span>•</span>
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                      {sharedCount} shared win (seri)
                    </span>
                  </div>

                  <div className="mt-3 space-y-2 text-[11px]">
                    {item.winning_sectors.length > 0 && (
                      <div>
                        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                          Unggul Mutlak ({item.winning_sectors.length}):
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {item.winning_sectors.map((sec, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-semibold"
                            >
                              {sec.replace('Skor ', '')}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {item.tied_sectors.length > 0 && (
                      <div>
                        <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider block mb-1">
                          Shared Win / Seri ({item.tied_sectors.length}):
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {item.tied_sectors.map((sec, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 rounded-md bg-emerald-100/90 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-medium border border-emerald-500/20"
                            >
                              {sec.replace('Skor ', '')}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {item.winning_sectors.length === 0 && item.tied_sectors.length === 0 && (
                      <span className="text-slate-400 dark:text-slate-500 italic block py-0.5">
                        Belum memenangkan sektor performa utama
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {tiedSectorsSummary && tiedSectorsSummary.length > 0 && (
            <div className="p-3.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-300 flex items-start gap-2.5">
              <span className="font-bold text-emerald-600 dark:text-emerald-400 flex-shrink-0">Catatan Sektor Seri (Shared Win):</span>
              <div className="space-y-1">
                <span className="leading-relaxed block">{tiedSectorsSummary.join(' • ')}</span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 block italic">
                  *Setiap sektor yang seri memberikan +1 shared win kepada setiap produk yang berbagi skor tertinggi.
                </span>
              </div>
            </div>
          )}
        </div>
      ) : !isSameCategory ? (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-xs text-amber-800 dark:text-amber-300 flex items-center gap-3">
          <Scale className="w-5 h-5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
          <span>
            <strong>Perbandingan Lintas Kategori ({categories.join(' vs ')}):</strong> Perangkat memiliki arsitektur, form-factor, dan peruntukan fungsi yang berbeda. Sistem tidak menetapkan pemenang universal ataupun menjumlahkan win-count antarkategori. Silakan tinjau spesifikasi faktual yang sepadan di bawah.
          </span>
        </div>
      ) : null}

      {/* Comparison Table Container */}
      <div className="overflow-x-auto rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left border-collapse">
          {/* Header Row with Product Cards */}
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80">
              <th className="p-4 sm:p-6 w-52 min-w-[200px] align-top text-xs font-bold uppercase tracking-wider text-slate-400">
                Spesifikasi & Sektor Penilai
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
                        {p.brand} • {p.category}
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
            {/* Section Header: 8 Dimensi Kinerja */}
            <tr className="bg-slate-100/70 dark:bg-slate-800/60">
              <td
                colSpan={products.length + 1}
                className="p-3.5 px-4 font-black uppercase tracking-wider text-[11px] text-indigo-700 dark:text-indigo-300"
              >
                1. Penilaian 8 Sektor Kinerja (Skala 0–100)
              </td>
            </tr>

            {dimensionDefinitions.map((dim) => {
              const highlight = getHighlightForSpec(dim.key, dim.label);
              const isApplicable = !isSameCategory || applicableDimensions.includes(dim.key);
              const Icon = dim.icon;

              return (
                <tr key={dim.key} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="p-4 font-semibold text-slate-700 dark:text-slate-300 bg-slate-50/50 dark:bg-slate-950/20">
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                      <span>{dim.label}</span>
                    </div>
                  </td>
                  {products.map((p) => {
                    const score = p[dim.attr];
                    const isApplicableForProduct =
                      !(p.category === 'tws' && (dim.key === 'camera' || dim.key === 'display')) &&
                      !(p.category === 'smartwatch' && dim.key === 'camera');

                    if (!isApplicableForProduct) {
                      return (
                        <td
                          key={p.id}
                          className="p-4 border-l border-slate-200 dark:border-slate-800 text-slate-400 dark:text-slate-500 italic"
                        >
                          — (Tidak Berlaku)
                        </td>
                      );
                    }

                    const bestIds = highlight?.best_product_ids && highlight.best_product_ids.length > 0
                      ? highlight.best_product_ids
                      : (highlight?.best_product_id ? [highlight.best_product_id] : []);
                    const isBest = isSameCategory && bestIds.includes(p.id) && score !== undefined && score !== null;
                    const isTie = highlight?.is_tie;

                    return (
                      <td
                        key={p.id}
                        className={`p-4 border-l border-slate-200 dark:border-slate-800 ${
                          isBest
                            ? 'bg-emerald-500/10 text-emerald-950 dark:text-emerald-200 font-bold'
                            : 'text-slate-800 dark:text-slate-200'
                        }`}
                      >
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="font-extrabold text-sm">{score} <span className="text-[10px] opacity-70 font-normal">/ 100</span></span>
                            {isBest && products.length > 1 && (
                              <span
                                className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full shadow-sm ${
                                  isTie
                                    ? 'bg-emerald-600 text-white border border-emerald-400/40'
                                    : 'bg-emerald-500 text-white'
                                }`}
                              >
                                {isTie ? 'Unggul (Seri)' : 'Unggul'}
                              </span>
                            )}
                          </div>
                          {/* Mini Progress Bar */}
                          <div className="w-full h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                isBest
                                  ? 'bg-emerald-500'
                                  : 'bg-indigo-600 dark:bg-indigo-400'
                              }`}
                              style={{ width: `${Math.min(Math.max(score, 0), 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}

            {/* Section Header: Harga & Garansi */}
            <tr className="bg-slate-100/70 dark:bg-slate-800/60">
              <td
                colSpan={products.length + 1}
                className="p-3.5 px-4 font-black uppercase tracking-wider text-[11px] text-indigo-700 dark:text-indigo-300"
              >
                2. Nilai & Perlindungan Garansi
              </td>
            </tr>

            {/* Price Comparison Row (Revisi 5) */}
            <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
              <td className="p-4 font-bold text-slate-900 dark:text-white bg-slate-50/50 dark:bg-slate-950/20">
                <div>
                  <span>Harga Acuan Konfigurasi Dasar</span>
                  <span className="block text-[10px] font-normal text-slate-500 dark:text-slate-400">
                    MSRP resmi atau harga acuan katalog
                  </span>
                </div>
              </td>
              {products.map((p) => {
                const isBestPrice = isPriceHighlightEligible && p.price === lowestPrice;
                const isAcer = p.id === 'lp-004';
                const isImport = p.id === 'sm-003' || p.id === 'sm-004';

                return (
                  <td
                    key={p.id}
                    className={`p-4 border-l border-slate-200 dark:border-slate-800 ${
                      isBestPrice
                        ? 'bg-emerald-500/10 text-emerald-900 dark:text-emerald-200 font-extrabold'
                        : 'text-slate-800 dark:text-slate-200'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-extrabold">Rp {p.price.toLocaleString('id-ID')}</span>
                        {isBestPrice && products.length > 1 && (
                          <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-emerald-500 text-white shadow-sm">
                            MSRP Termurah
                          </span>
                        )}
                      </div>
                      {p.specs?.base_configuration && (
                        <div className="text-[11px] font-medium text-indigo-600 dark:text-indigo-400">
                          {p.specs.base_configuration}
                        </div>
                      )}
                      <div className="text-[10px] text-slate-500 dark:text-slate-400">
                        {isAcer ? (
                          <span className="text-amber-600 dark:text-amber-400">(Harga Acuan Katalog - Belum Terverifikasi)</span>
                        ) : isImport ? (
                          <span className="text-amber-600 dark:text-amber-400">(Acuan Pasar Impor / Toko)</span>
                        ) : !hasComparableConfigs && isSameCategory ? (
                          <span className="text-slate-500 dark:text-slate-400">(MSRP Resmi - Konfigurasi Berbeda)</span>
                        ) : (
                          <span>(MSRP Resmi Terverifikasi)</span>
                        )}
                      </div>
                    </div>
                  </td>
                );
              })}
            </tr>

            {/* Warranty Row (Revisi 6) */}
            <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
              <td className="p-4 font-bold text-slate-900 dark:text-white bg-slate-50/50 dark:bg-slate-950/20">
                <div>
                  <span>Garansi Purna Jual</span>
                  <span className="block text-[10px] font-normal text-slate-500 dark:text-slate-400">
                    Cakupan suku cadang & jasa servis
                  </span>
                </div>
              </td>
              {products.map((p) => {
                const w = p.warranty;
                const status = (w?.verification_status || '').toLowerCase();
                const type = (w?.warranty_type || '').toLowerCase();
                const isSkuUnverified = status.includes('sku belum terverifikasi');
                const isImport = type.includes('impor') || type.includes('non-atpm');
                const isAcer = p.id === 'lp-004' && w?.labor_warranty_months === 36;
                const isAsus = p.id === 'lp-002';
                const isBestWarranty =
                  !hasUnverifiedWarranty &&
                  longestWarrantyMonths !== null &&
                  (w?.parts_warranty_months || w?.duration_months) === longestWarrantyMonths;

                return (
                  <td
                    key={p.id}
                    className={`p-4 border-l border-slate-200 dark:border-slate-800 ${
                      isBestWarranty
                        ? 'bg-emerald-500/10 text-emerald-900 dark:text-emerald-200 font-bold'
                        : 'text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold">
                          {w?.parts_warranty_months !== null && w?.parts_warranty_months !== undefined && w?.labor_warranty_months
                            ? `${w.parts_warranty_months} Bln Parts / ${w.labor_warranty_months} Bln Servis`
                            : w?.duration_months !== null && w?.duration_months !== undefined
                            ? `${w.duration_months} Bulan`
                            : 'Belum Terverifikasi'}
                        </span>
                        {isBestWarranty && products.length > 1 && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500 text-white shadow-sm">
                            Resmi Terlama
                          </span>
                        )}
                      </div>
                      <div className="text-[10px]">
                        {isAcer ? (
                          <span className="text-teal-600 dark:text-teal-400 font-semibold">
                            (Program Acer Care, SKU Belum Terverifikasi)*
                          </span>
                        ) : isAsus ? (
                          <span className="text-sky-600 dark:text-sky-400 font-medium">
                            (24 Bln Standar + VIP Perfect Warranty 1 Thn, SKU Belum Terverifikasi)
                          </span>
                        ) : isSkuUnverified ? (
                          <span className="text-sky-600 dark:text-sky-400 font-medium">
                            (Resmi - SKU Belum Terverifikasi)
                          </span>
                        ) : isImport ? (
                          <span className="text-amber-600 dark:text-amber-400 font-medium">
                            (Acuan Pasar Impor / Toko Non-ATPM)
                          </span>
                        ) : (
                          <span className="text-slate-500 dark:text-slate-400">
                            (Garansi Resmi Produsen Terverifikasi)
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                );
              })}
            </tr>

            {/* Section Header: Spesifikasi Teknis */}
            <tr className="bg-slate-100/70 dark:bg-slate-800/60">
              <td
                colSpan={products.length + 1}
                className="p-3.5 px-4 font-black uppercase tracking-wider text-[11px] text-indigo-700 dark:text-indigo-300"
              >
                3. Spesifikasi Teknis & Fitur
              </td>
            </tr>

            {/* Specs Rows with Key-Based Matching */}
            {activeSpecDefinitions.map((spec) => {
              const highlight = getHighlightForSpec(spec.key, spec.label);
              // Cross-category rule: do not highlight weight or non-comparable specs across categories
              const isEligibleForHighlight = isSameCategory || spec.key !== 'weight';

              return (
                <tr key={spec.key} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="p-4 font-semibold text-slate-600 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-950/20">
                    {spec.label}
                  </td>
                  {products.map((p) => {
                    const val = (p.specs && p.specs[spec.key]) || '—';
                    const bestIds = highlight?.best_product_ids && highlight.best_product_ids.length > 0
                      ? highlight.best_product_ids
                      : (highlight?.best_product_id ? [highlight.best_product_id] : []);

                    const isBest =
                      isEligibleForHighlight &&
                      bestIds.includes(p.id) &&
                      val !== '—' &&
                      !val.includes('Tidak Berlaku');
                    const isTie = highlight?.is_tie;

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
                            <span
                              className={`text-[10px] font-bold px-1.5 py-0.5 rounded flex-shrink-0 ${
                                isTie
                                  ? 'bg-emerald-600 text-white border border-emerald-400/40'
                                  : 'bg-emerald-500 text-white'
                              }`}
                            >
                              {isTie ? 'Unggul (Seri)' : 'Unggul'}
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
