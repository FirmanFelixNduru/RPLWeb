'use client';

import React, { useEffect, useState } from 'react';
import { ShoppingBag, ExternalLink, RefreshCw, Sparkles, TrendingDown, DollarSign, CheckCircle2 } from 'lucide-react';
import { getLiveMarketplacePrices } from '@/lib/api';
import PriceTag from '@/components/ui/PriceTag';

export default function TabValue({ product }) {
  const [pricingData, setPricingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPrices = async () => {
    if (!product) return;
    try {
      const data = await getLiveMarketplacePrices(product.id);
      setPricingData(data);
    } catch (e) {
      console.error('Failed to load prices:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPrices();
  }, [product?.id]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchPrices();
  };

  if (!product) return null;

  // MSRP vs Best Marketplace Deal
  const prices = pricingData?.prices || [];
  const lowestPrice = prices.length > 0 ? Math.min(...prices.map((p) => p.price)) : product.price;
  const potentialSavings = Math.max(0, product.price - lowestPrice);

  return (
    <div className="space-y-6">
      {/* Live Scraping Status Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between p-3.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 gap-2">
        <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
          <span>
            Scraper Engine Live: Terakhir diperbarui{' '}
            <strong>{pricingData?.last_updated || 'Baru saja'}</strong>
          </span>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Memindai Harga...' : 'Refresh Harga Live'}</span>
        </button>
      </div>

      {/* MSRP vs Best Deal Highlight */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block mb-1">
            Harga Ritel Resmi (MSRP Indonesia)
          </span>
          <PriceTag price={product.price} size="lg" className="text-slate-600 dark:text-slate-400" />
        </div>

        <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/20 border border-emerald-300 dark:border-emerald-800/80">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-emerald-800 dark:text-emerald-300">
              Penawaran Terbaik Live
            </span>
            {potentialSavings > 0 && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500 text-white">
                Hemat Rp {potentialSavings.toLocaleString('id-ID')}
              </span>
            )}
          </div>
          <PriceTag price={lowestPrice} size="lg" className="text-emerald-700 dark:text-emerald-300" />
        </div>
      </div>

      {/* Live Marketplace Comparison Cards */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
          <ShoppingBag className="w-4 h-4 text-indigo-500" />
          <span>Harga Real-Time dari Marketplace Terkemuka</span>
        </h4>

        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-16 rounded-xl bg-slate-200 dark:bg-slate-800 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2.5">
            {prices.map((item, idx) => {
              const isLowest = item.price === lowestPrice;

              // Marketplace brand colors
              let badgeColor = 'bg-emerald-500 text-white';
              if (item.marketplace.toLowerCase().includes('shopee')) {
                badgeColor = 'bg-orange-500 text-white';
              } else if (item.marketplace.toLowerCase().includes('lazada')) {
                badgeColor = 'bg-blue-600 text-white';
              }

              return (
                <div
                  key={idx}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between p-3.5 sm:p-4 rounded-xl border transition-all ${
                    isLowest
                      ? 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-400 dark:border-emerald-700 ring-1 ring-emerald-400/30'
                      : 'bg-white dark:bg-slate-800/80 border-slate-200 dark:border-slate-700 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2 sm:mb-0">
                    <span
                      className={`text-xs font-bold px-2.5 py-1 rounded-lg shadow-sm ${badgeColor}`}
                    >
                      {item.marketplace}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                          {item.seller}
                        </span>
                        {isLowest && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-700">
                            Harga Termurah
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400">
                        {item.available ? 'Stok Terkonfirmasi Tersedia' : 'Cek Stok di Toko'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-4">
                    <PriceTag price={item.price} size="md" className={isLowest ? 'text-emerald-600 dark:text-emerald-400' : ''} />
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm ${
                        isLowest
                          ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20'
                          : 'bg-slate-900 hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 text-white'
                      }`}
                    >
                      <span>Kunjungi Toko</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Value Breakdown Insights */}
      <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40 text-xs space-y-2 text-indigo-950 dark:text-indigo-200">
        <h5 className="font-bold flex items-center gap-1.5 text-indigo-900 dark:text-indigo-300">
          <Sparkles className="w-4 h-4 text-indigo-500" />
          <span>Analisis Value Retention CompareBuy:</span>
        </h5>
        <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
          Skor Value for Money produk ini berada di angka <strong>{product.score_value}/100</strong>. Perangkat ini diprediksi memiliki tingkat depresiasi harga stabil sekitar 15-20% per tahun pertama berkat popularitas merek dan ketersediaan suku cadang yang melimpah.
        </p>
      </div>
    </div>
  );
}
