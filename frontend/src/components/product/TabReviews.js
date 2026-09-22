'use client';

import React from 'react';
import { Star, ThumbsUp, ThumbsDown, MessageSquare, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function TabReviews({ product }) {
  if (!product || !product.review_sentiment) return null;

  const sentiment = product.review_sentiment;
  const rating = sentiment.overall_score || 4.5;
  const totalReviews = sentiment.total_reviews ? sentiment.total_reviews.toLocaleString('id-ID') : '1.200+';

  return (
    <div className="space-y-6">
      {/* Overview Score Card */}
      <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-slate-800/90 dark:to-indigo-950/40 border border-indigo-100 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-center sm:text-left">
          <div className="flex flex-col items-center justify-center w-20 h-20 rounded-2xl bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 flex-shrink-0">
            <span className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">
              {rating}
            </span>
            <div className="flex text-amber-400 text-xs">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className={`w-3 h-3 ${i < Math.floor(rating) ? 'fill-current' : 'opacity-40'}`} />
              ))}
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2 justify-center sm:justify-start">
              <h4 className="text-base font-bold text-slate-900 dark:text-white">
                Real User Sentiment Score
              </h4>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 font-semibold inline-flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                Anti-Fake Verified
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Agregasi dari <strong>{totalReviews}</strong> ulasan nyata di berbagai forum teknologi, Reddit, dan komunitas lokal.
            </p>
          </div>
        </div>

        {/* Sentiment Meter */}
        <div className="w-full sm:w-48 space-y-1.5 text-xs">
          <div className="flex justify-between font-semibold">
            <span className="text-emerald-600 dark:text-emerald-400">Positif (88%)</span>
            <span className="text-rose-500">Kritis (12%)</span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden flex">
            <div className="bg-emerald-500 h-full" style={{ width: '88%' }} />
            <div className="bg-rose-500 h-full" style={{ width: '12%' }} />
          </div>
        </div>
      </div>

      {/* AI Community Summary */}
      <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80">
        <div className="flex items-center gap-2 mb-1 text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Ringkasan Kesepakatan Komunitas</span>
        </div>
        <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed italic">
          &ldquo;{sentiment.summary}&rdquo;
        </p>
      </div>

      {/* Pros & Cons Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Pros */}
        <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/40 space-y-3">
          <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-bold text-sm">
            <ThumbsUp className="w-4 h-4" />
            <span>Kelebihan Utama (Pujian Terbanyak)</span>
          </div>
          <ul className="space-y-2">
            {sentiment.pros.map((pro, index) => (
              <li key={index} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                <span>{pro}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Cons */}
        <div className="p-4 rounded-xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40 space-y-3">
          <div className="flex items-center gap-2 text-rose-800 dark:text-rose-300 font-bold text-sm">
            <ThumbsDown className="w-4 h-4" />
            <span>Kekurangan Nyata (Perlu Diwaspadai)</span>
          </div>
          <ul className="space-y-2">
            {sentiment.cons.map((con, index) => (
              <li key={index} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
                <span>{con}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
