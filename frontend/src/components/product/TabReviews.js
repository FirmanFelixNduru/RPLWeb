'use client';

import React from 'react';
import { Star, ThumbsUp, ThumbsDown, MessageSquare, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function TabReviews({ product }) {
  const sentiment = product?.review_sentiment;
  const hasReviewCount = Number.isInteger(sentiment?.total_reviews) && sentiment.total_reviews > 0;
  const hasRating = hasReviewCount && Number.isFinite(sentiment?.overall_score) &&
    sentiment.overall_score >= 0 && sentiment.overall_score <= 5;
  const pros = Array.isArray(sentiment?.pros)
    ? sentiment.pros.filter((item) => typeof item === 'string' && item.trim()) : [];
  const cons = Array.isArray(sentiment?.cons)
    ? sentiment.cons.filter((item) => typeof item === 'string' && item.trim()) : [];
  const summary = typeof sentiment?.summary === 'string' ? sentiment.summary.trim() : '';

  return (
    <div className="space-y-6">
      {/* Overview Score Card */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-center sm:text-left">
          {hasRating && (
            <div className="flex flex-col items-center justify-center w-20 h-20 rounded-2xl bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 flex-shrink-0">
              <span className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">
                {sentiment.overall_score}
              </span>
              <div className="flex text-amber-400 text-xs">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className={`w-3 h-3 ${i < Math.floor(sentiment.overall_score) ? 'fill-current' : 'opacity-40'}`} />
                ))}
              </div>
            </div>
          )}
          <div>
            <div className="flex items-center gap-2 justify-center sm:justify-start">
              <h4 className="text-base font-bold text-slate-900 dark:text-white">
                Ulasan produk
              </h4>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              {hasReviewCount
                ? <><strong>{sentiment.total_reviews.toLocaleString('id-ID')}</strong> ulasan tercatat dalam data katalog.</>
                : 'Data ulasan belum tersedia'}
            </p>
            {hasReviewCount && !hasRating && (
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Rating belum tersedia</p>
            )}
          </div>
        </div>
      </div>

      {/* Supplied review summary */}
      {summary && (
        <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80">
          <div className="flex items-center gap-2 mb-1 text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Ringkasan ulasan</span>
          </div>
          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed italic">
            &ldquo;{summary}&rdquo;
          </p>
        </div>
      )}

      {/* Pros & Cons Columns */}
      {(pros.length > 0 || cons.length > 0) && (
        <div className={`grid grid-cols-1 ${pros.length > 0 && cons.length > 0 ? 'md:grid-cols-2' : ''} gap-4`}>
          {/* Pros */}
          {pros.length > 0 && (
            <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/40 space-y-3">
              <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-bold text-sm">
                <ThumbsUp className="w-4 h-4" />
                <span>Kelebihan yang dicatat</span>
              </div>
              <ul className="space-y-2">
                {pros.map((pro, index) => (
                  <li key={index} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>{pro}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Cons */}
          {cons.length > 0 && (
            <div className="p-4 rounded-xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40 space-y-3">
              <div className="flex items-center gap-2 text-rose-800 dark:text-rose-300 font-bold text-sm">
                <ThumbsDown className="w-4 h-4" />
                <span>Kekurangan yang dicatat</span>
              </div>
              <ul className="space-y-2">
                {cons.map((con, index) => (
                  <li key={index} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                    <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
                    <span>{con}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
