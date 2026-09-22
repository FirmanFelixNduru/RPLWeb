'use client';

import React from 'react';
import { Award, Zap } from 'lucide-react';

export default function ScoreBadge({ score, size = 'md', showLabel = false, label = 'Match Score' }) {
  const numScore = typeof score === 'number' ? Math.round(score * 10) / 10 : parseFloat(score) || 0;

  // Determine dynamic gradient badge colors based on score
  let colorClasses = 'from-emerald-500 to-teal-600 text-white shadow-emerald-500/25';
  let badgeText = 'Superb';

  if (numScore >= 90) {
    colorClasses = 'from-emerald-500 to-teal-600 text-white shadow-emerald-500/30';
    badgeText = 'Sangat Direkomendasikan';
  } else if (numScore >= 80) {
    colorClasses = 'from-indigo-500 to-blue-600 text-white shadow-indigo-500/30';
    badgeText = 'Pilihan Unggul';
  } else if (numScore >= 70) {
    colorClasses = 'from-amber-500 to-orange-600 text-white shadow-amber-500/30';
    badgeText = 'Layak Dipertimbangkan';
  } else {
    colorClasses = 'from-slate-500 to-gray-600 text-white shadow-slate-500/20';
    badgeText = 'Standar';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 font-semibold',
    md: 'text-sm px-3 py-1 font-bold',
    lg: 'text-lg px-4 py-1.5 font-extrabold',
  };

  return (
    <div className="inline-flex items-center gap-1.5">
      <span
        className={`inline-flex items-center gap-1 rounded-full bg-gradient-to-r ${colorClasses} ${sizeClasses[size]} shadow-md`}
      >
        <Zap className="w-3.5 h-3.5 fill-current" />
        <span>{numScore}</span>
        <span className="opacity-80 text-[10px]">/100</span>
      </span>
      {showLabel && (
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
          {label} ({badgeText})
        </span>
      )}
    </div>
  );
}
