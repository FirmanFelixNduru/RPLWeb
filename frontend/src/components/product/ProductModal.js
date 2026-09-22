'use client';

import React, { useState } from 'react';
import { X, Scale, Check, Sliders, MessageSquare, Shield, ShoppingBag, ArrowRight } from 'lucide-react';
import { useCompare } from '@/context/CompareContext';
import PriceTag from '@/components/ui/PriceTag';
import TabSpecs from './TabSpecs';
import TabReviews from './TabReviews';
import TabWarranty from './TabWarranty';
import TabValue from './TabValue';

export default function ProductModal() {
  const { activeProductModal, closeProductModal, addToCompare, isInCompare } = useCompare();
  const [activeTab, setActiveTab] = useState('specs');

  if (!activeProductModal) return null;

  const product = activeProductModal;
  const inCompare = isInCompare(product.id);

  const tabs = [
    { id: 'specs', label: 'Spesifikasi', icon: Sliders },
    { id: 'reviews', label: 'User Experience & Review', icon: MessageSquare },
    { id: 'warranty', label: 'Garansi & Purna Jual', icon: Shield },
    { id: 'value', label: 'Marketplace Live & Value', icon: ShoppingBag },
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-fade-in">
      <div
        className="relative w-full max-w-4xl bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-4 sm:p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/90 flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-1 flex-shrink-0 overflow-hidden">
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-full object-cover rounded-xl"
              />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                  {product.brand}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold uppercase">
                  {product.category}
                </span>
              </div>
              <h3 className="text-lg sm:text-2xl font-extrabold text-slate-900 dark:text-white leading-tight">
                {product.name}
              </h3>
              <div className="flex items-center gap-2 mt-1">
                <PriceTag price={product.price} size="md" />
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  (MSRP Indonesia)
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => addToCompare(product)}
              className={`hidden sm:inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                inCompare
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                  : 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100'
              }`}
            >
              {inCompare ? <Check className="w-3.5 h-3.5" /> : <Scale className="w-3.5 h-3.5" />}
              <span>{inCompare ? 'Tersimpan di Dock' : 'Tambah ke Komparasi'}</span>
            </button>

            <button
              type="button"
              onClick={closeProductModal}
              aria-label="Tutup Modal"
              className="p-2 rounded-full text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 overflow-x-auto bg-white dark:bg-slate-900">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-3 px-3.5 sm:px-4 text-xs sm:text-sm font-bold border-b-2 whitespace-nowrap transition-all ${
                  isActive
                    ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-4 sm:p-6 overflow-y-auto flex-1">
          {activeTab === 'specs' && <TabSpecs product={product} />}
          {activeTab === 'reviews' && <TabReviews product={product} />}
          {activeTab === 'warranty' && <TabWarranty product={product} />}
          {activeTab === 'value' && <TabValue product={product} />}
        </div>

        {/* Modal Footer (Mobile compare toggle) */}
        <div className="sm:hidden p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex justify-between items-center">
          <button
            type="button"
            onClick={() => addToCompare(product)}
            className={`w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
              inCompare
                ? 'bg-emerald-600 text-white'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white'
            }`}
          >
            {inCompare ? <Check className="w-4 h-4" /> : <Scale className="w-4 h-4" />}
            <span>{inCompare ? 'Tersimpan di Dock Komparasi' : 'Tambah ke Komparasi'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
