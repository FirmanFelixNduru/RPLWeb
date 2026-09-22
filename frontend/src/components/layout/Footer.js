'use client';

import React from 'react';
import Link from 'next/link';
import { Scale, Heart, Shield, Cpu, ExternalLink } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-950/60 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                <Scale className="w-4 h-4" />
              </div>
              <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-300 bg-clip-text text-transparent">
                CompareBuy
              </span>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-md">
              Platform Cerdas Perbandingan & Rekomendasi Gadget Teknologi. Membantu mahasiswa, profesional, dan masyarakat menemukan produk paling <em>worth-it</em> bebas dari jebakan <em>analysis paralysis</em> dan ulasan manipulatif.
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
              <span className="inline-flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-emerald-500" />
                Indeks Garansi Terverifikasi
              </span>
              <span className="inline-flex items-center gap-1">
                <Cpu className="w-3.5 h-3.5 text-indigo-500" />
                Algoritma MCDA Akurat
              </span>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white mb-3">
              Fitur Platform
            </h3>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>
                <Link href="/wizard" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Smart Recommendation Wizard
                </Link>
              </li>
              <li>
                <Link href="/compare" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Side-by-Side Comparison Matrix
                </Link>
              </li>
              <li>
                <Link href="/catalog" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Katalog Gadget Terkurasi
                </Link>
              </li>
            </ul>
          </div>

          {/* Supported Marketplaces */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white mb-3">
              Marketplace Live
            </h3>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Tokopedia Indonesia</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                <span>Shopee Mall Indonesia</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                <span>Lazada LazMall</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-slate-200 dark:border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 dark:text-slate-400 gap-4">
          <p>© {new Date().getFullYear()} CompareBuy Platform. All rights reserved.</p>
          <p className="flex items-center gap-1">
            Dibuat untuk Indonesia dengan Next.js App Router & FastAPI
          </p>
        </div>
      </div>
    </footer>
  );
}
