'use client';

import React from 'react';

export default function PriceTag({ price, size = 'md', className = '' }) {
  const formatted = new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(price || 0);

  const sizeClasses = {
    sm: 'text-sm font-semibold',
    md: 'text-lg font-bold',
    lg: 'text-2xl font-extrabold',
    xl: 'text-3xl font-black',
  };

  return (
    <span className={`text-slate-900 dark:text-white tracking-tight ${sizeClasses[size]} ${className}`}>
      {formatted}
    </span>
  );
}
