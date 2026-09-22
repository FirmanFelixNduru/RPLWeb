'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Sparkles,
  Scale,
  ShieldCheck,
  Zap,
  ShoppingBag,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
  Star,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { PRODUCTS, CATEGORIES } from '@/data/products';
import ProductCard from '@/components/catalog/ProductCard';

export default function HomePage() {
  const [activeCategory, setActiveCategory] = useState('smartphone');

  const featuredProducts = PRODUCTS.filter(
    (p) => p.category === activeCategory
  ).slice(0, 3);

  const pillars = [
    {
      icon: Sparkles,
      color: 'from-indigo-500 to-purple-600',
      title: 'Smart Recommendation Wizard',
      desc: '4 langkah panduan interaktif menganalisis kategori, anggaran, skenario harian, dan prioritas trade-off Anda.',
    },
    {
      icon: Zap,
      color: 'from-emerald-500 to-teal-600',
      title: 'Weighted Dynamic Scoring Engine',
      desc: 'Algoritma Multi-Criteria Decision Analysis (MCDA) di FastAPI yang menghitung skor personal secara matematis.',
    },
    {
      icon: Scale,
      color: 'from-blue-500 to-indigo-600',
      title: 'Side-by-Side Comparison Matrix',
      desc: 'Bandingkan hingga 4 produk sekaligus dengan penanda visual otomatis (Auto-Highlighting) untuk spesifikasi paling unggul.',
    },
    {
      icon: Star,
      color: 'from-amber-500 to-orange-600',
      title: 'Real User Sentiment Aggregator',
      desc: 'Kelebihan dan kekurangan nyata dari ribuan ulasan komunitas, bukan rekayasa promosi atau ulasan berbayar.',
    },
    {
      icon: ShieldCheck,
      color: 'from-purple-500 to-pink-600',
      title: 'After-Sales & Warranty Index',
      desc: 'Transparansi durasi garansi resmi, kemudahan proses klaim, dan sebaran service center di Indonesia.',
    },
    {
      icon: ShoppingBag,
      color: 'from-rose-500 to-red-600',
      title: 'Live Marketplace Price Scraping',
      desc: 'Pemantauan harga langsung dari Tokopedia, Shopee, dan Lazada secara real-time untuk menemukan deal termurah.',
    },
  ];

  return (
    <div className="space-y-16 sm:space-y-24 pb-16">
      {/* ── HERO SECTION ── */}
      <section className="relative overflow-hidden pt-12 sm:pt-20 pb-16 sm:pb-24 border-b border-slate-200/80 dark:border-slate-800/80">
        {/* Glow ambient backgrounds */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-indigo-500/20 via-purple-500/20 to-teal-500/10 rounded-full blur-3xl pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          {/* Top pill badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800/80 text-indigo-700 dark:text-indigo-300 text-xs font-bold shadow-sm">
            <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse" />
            <span>Platform Cerdas Penasihat Teknologi Generasi Baru</span>
          </div>

          {/* Main Title */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 dark:text-white max-w-4xl mx-auto leading-[1.15]">
            Bebas dari{' '}
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Analysis Paralysis.
            </span>{' '}
            Pilih Gadget yang Paling <em>Worth It</em>.
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Tidak ada lagi kebingungan membaca puluhan tabel spesifikasi dan ulasan palsu. CompareBuy menghitung rekomendasi objektif sesuai budget dan gaya hidup Anda.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-4">
            <Link
              href="/wizard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm sm:text-base shadow-xl shadow-indigo-600/25 hover:shadow-indigo-600/40 transition-all active:scale-95"
            >
              <Sparkles className="w-5 h-5" />
              <span>Mulai Smart Wizard (4 Langkah)</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              href="/catalog"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-2xl bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-800 font-bold text-sm sm:text-base transition-all"
            >
              <Layers className="w-5 h-5 text-indigo-500" />
              <span>Jelajahi Katalog Gadget</span>
            </Link>
          </div>

          {/* Trust stats pill */}
          <div className="pt-8 flex flex-wrap items-center justify-center gap-6 sm:gap-12 text-xs font-semibold text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Algoritma Skor Multi-Kriteria (MCDA)</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Auto-Highlight Spesifikasi Terbaik</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Live Scraping Tokopedia, Shopee, Lazada</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── 6 CORE FEATURE PILLARS ── */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
            Fitur Inti yang Dirancang untuk Anda
          </span>
          <h2 className="text-2xl sm:text-4xl font-black text-slate-900 dark:text-white">
            Solusi Menyeluruh dari Analisis Hingga Pembelian
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Setiap modul dirancang untuk memecahkan friksi nyata yang dihadapi konsumen teknologi di Indonesia.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pillars.map((pillar, idx) => {
            const Icon = pillar.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-600/80 shadow-sm hover:shadow-xl hover:shadow-indigo-500/5 transition-all duration-300 space-y-4"
              >
                <div
                  className={`w-12 h-12 rounded-2xl bg-gradient-to-tr ${pillar.color} text-white flex items-center justify-center shadow-md`}
                >
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {pillar.title}
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  {pillar.desc}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── FEATURED PRODUCTS PREVIEW ── */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
              Pilihan Paling Populer
            </span>
            <h2 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white mt-1">
              Rekomendasi Terkurasi Pasar Indonesia
            </h2>
          </div>

          {/* Category tabs */}
          <div className="flex flex-wrap gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
            {CATEGORIES.slice(0, 4).map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setActiveCategory(cat.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeCategory === cat.id
                    ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featuredProducts.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>

        <div className="text-center pt-4">
          <Link
            href="/catalog"
            className="inline-flex items-center gap-2 text-sm font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            <span>Lihat Semua 20 Perangkat Terkurasi di Katalog</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ── CTA BANNER ── */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-700 text-white shadow-2xl shadow-indigo-700/30 overflow-hidden flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-3 text-center md:text-left max-w-xl">
            <span className="text-xs font-extrabold uppercase tracking-widest text-indigo-200">
              Coba Sekarang Secara Gratis
            </span>
            <h3 className="text-2xl sm:text-4xl font-black leading-tight">
              Siap Menemukan Gadget Pilihan Terbaik Tanpa Ragu?
            </h3>
            <p className="text-sm text-indigo-100 leading-relaxed">
              Jalankan Smart Recommendation Wizard sekarang. Hanya butuh 60 detik untuk mendapatkan rekomendasi objektif bertenaga AI Scoring.
            </p>
          </div>

          <Link
            href="/wizard"
            className="px-8 py-4 rounded-2xl bg-white hover:bg-slate-100 text-indigo-950 font-extrabold text-sm sm:text-base shadow-xl shadow-black/20 transition-all flex items-center gap-2 flex-shrink-0 active:scale-95"
          >
            <span>Jalankan Smart Wizard</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
