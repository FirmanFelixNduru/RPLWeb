'use client';

import React from 'react';
import { Scale, Check, Star, ShieldCheck, Eye, Cpu, Battery, Smartphone } from 'lucide-react';
import { useCompare } from '@/context/CompareContext';
import PriceTag from '@/components/ui/PriceTag';
import ScoreBadge from '@/components/ui/ScoreBadge';

export default function ProductCard({ product }) {
  const { addToCompare, isInCompare, openProductModal } = useCompare();
  const inCompare = isInCompare(product.id);

  // Compute aggregate visual score (0-100)
  const averageScore = Math.round(
    ((product.score_performance || 50) +
      (product.score_camera || 50) +
      (product.score_battery || 50) +
      (product.score_display || 50) +
      (product.score_value || 50)) / 5
  );

  return (
    <div className="group relative rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-600 shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 dark:hover:shadow-black/40 transition-all duration-300 flex flex-col overflow-hidden">
      {/* Top Image & Floating Badges */}
      <div className="relative aspect-[4/3] bg-slate-50 dark:bg-slate-800/60 overflow-hidden">
        <img
          src={product.image}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />

        {/* Brand & Category Badges */}
        <div className="absolute top-3 left-3 flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-slate-900/85 backdrop-blur-md text-white shadow-sm uppercase tracking-wide">
            {product.brand}
          </span>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white/90 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 shadow-sm uppercase">
            {product.category}
          </span>
        </div>

        {/* Score Badge Floating */}
        <div className="absolute top-3 right-3">
          <ScoreBadge score={averageScore} size="sm" />
        </div>
      </div>

      {/* Card Content Body */}
      <div className="p-4 sm:p-5 flex-1 flex flex-col justify-between space-y-4">
        <div className="space-y-2">
          {/* Title */}
          <h3
            onClick={() => openProductModal(product)}
            className="text-base sm:text-lg font-bold text-slate-900 dark:text-white line-clamp-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 cursor-pointer transition-colors"
          >
            {product.name}
          </h3>

          {/* Price */}
          <div className="flex items-baseline gap-2">
            <PriceTag price={product.price} size="md" />
            <span className="text-[11px] text-slate-400">MSRP</span>
          </div>

          {/* Description snippet */}
          <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
            {product.description}
          </p>

          {/* Key Quick Specs Pills */}
          <div className="grid grid-cols-2 gap-1.5 pt-2 text-[11px] text-slate-600 dark:text-slate-300">
            {product.specs.processor && (
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800/60 px-2 py-1 rounded-md truncate">
                <Cpu className="w-3 h-3 text-indigo-500 flex-shrink-0" />
                <span className="truncate">{product.specs.processor}</span>
              </div>
            )}
            {product.specs.battery && (
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800/60 px-2 py-1 rounded-md truncate">
                <Battery className="w-3 h-3 text-emerald-500 flex-shrink-0" />
                <span className="truncate">{product.specs.battery}</span>
              </div>
            )}
          </div>

          {/* Social Proof & Warranty Indicators */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/80 text-xs">
            <div className="flex items-center gap-1 text-amber-500 font-semibold">
              <Star className="w-3.5 h-3.5 fill-current" />
              <span>{product.review_sentiment?.overall_score || 4.5}</span>
              <span className="text-slate-400 font-normal text-[10px]">
                ({product.review_sentiment?.total_reviews ? (product.review_sentiment.total_reviews > 999 ? (product.review_sentiment.total_reviews / 1000).toFixed(1) + 'k' : product.review_sentiment.total_reviews) : '1k+'})
              </span>
            </div>
            <div className="flex items-center gap-1 text-slate-500 dark:text-slate-400 text-[11px]">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-500" />
              <span>Garansi {product.warranty?.duration_months || 12} Bln</span>
            </div>
          </div>
        </div>

        {/* Card Actions */}
        <div className="grid grid-cols-2 gap-2 pt-2">
          <button
            type="button"
            onClick={() => addToCompare(product)}
            className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-bold transition-all ${
              inCompare
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400'
            }`}
          >
            {inCompare ? <Check className="w-3.5 h-3.5" /> : <Scale className="w-3.5 h-3.5" />}
            <span>{inCompare ? 'Bandingkan' : '+ Komparasi'}</span>
          </button>

          <button
            type="button"
            onClick={() => openProductModal(product)}
            className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition-all"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Lihat Detail</span>
          </button>
        </div>
      </div>
    </div>
  );
}
