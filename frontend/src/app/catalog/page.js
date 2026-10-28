'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Layers, Filter, X } from 'lucide-react';
import { getProducts } from '@/lib/api';
import { getCatalogScore } from '@/lib/catalogScore';
import ProductCard from '@/components/catalog/ProductCard';
import SearchBar from '@/components/catalog/SearchBar';
import FilterPanel from '@/components/catalog/FilterPanel';
import { useCompare } from '@/context/CompareContext';
import { useModalDialog } from '@/lib/useModalDialog';

export default function CatalogPage() {
  const { compareList } = useCompare();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedPriceRange, setSelectedPriceRange] = useState({ min: 0, max: null });
  const [sortBy, setSortBy] = useState('score');
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);
  const searchContainerRef = useRef(null);
  const hasBudgetFilter = selectedPriceRange.min > 0 || selectedPriceRange.max != null;
  const { dialogRef: filterDialogRef, titleRef: filterTitleRef } = useModalDialog(
    mobileFilterOpen, () => setMobileFilterOpen(false)
  );

  useEffect(() => {
    if (!mobileFilterOpen) return;
    const desktop = window.matchMedia('(min-width: 1024px)');
    const closeOnDesktop = () => {
      if (desktop.matches) setMobileFilterOpen(false);
    };
    desktop.addEventListener('change', closeOnDesktop);
    closeOnDesktop();
    return () => desktop.removeEventListener('change', closeOnDesktop);
  }, [mobileFilterOpen]);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await getProducts();
        setProducts(res.products || []);
      } catch (err) {
        console.error('Failed to load catalog products:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Compute all available brands from current products
  const brands = useMemo(() => {
    return Array.from(new Set(products.map((p) => p.brand))).sort();
  }, [products]);

  // Client-side instant filtering and sorting
  const filteredProducts = useMemo(() => {
    let list = [...products];

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.brand.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          p.tags.some((t) => t.toLowerCase().includes(q))
      );
    }

    // Category
    if (selectedCategory) {
      list = list.filter((p) => p.category === selectedCategory);
    }

    // Brand
    if (selectedBrand) {
      list = list.filter((p) => p.brand.toLowerCase() === selectedBrand.toLowerCase());
    }

    // Price range
    if (selectedPriceRange.min) {
      list = list.filter((p) => p.price >= selectedPriceRange.min);
    }
    if (selectedPriceRange.max) {
      list = list.filter((p) => p.price <= selectedPriceRange.max);
    }

    // Sorting
    if (sortBy === 'price_asc') {
      list.sort((a, b) => a.price - b.price);
    } else if (sortBy === 'price_desc') {
      list.sort((a, b) => b.price - a.price);
    } else if (sortBy === 'name') {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      // Match the displayed card score; resolve ties by stable product ID.
      list.sort((a, b) =>
        getCatalogScore(b) - getCatalogScore(a) || a.id.localeCompare(b.id)
      );
    }

    return list;
  }, [products, searchQuery, selectedCategory, selectedBrand, selectedPriceRange, sortBy]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('');
    setSelectedBrand('');
    setSelectedPriceRange({ min: 0, max: null });
    setSortBy('score');
  };

  return (
    <div className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8 ${compareList.length > 0 ? 'pb-32 sm:pb-24' : ''}`}>
      {/* Header Title */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider">
            <Layers className="w-4 h-4" />
            <span>Koleksi Database Gadget</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-black text-slate-900 dark:text-white mt-1">
            Katalog Gadget Terkurasi
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Telusuri spesifikasi lengkap, sentimen ulasan asli, garansi resmi, dan perbandingan harga live.
          </p>
        </div>

        {/* Mobile Filter Toggle */}
        <button
          type="button"
          onClick={(event) => {
            event.currentTarget.focus({ preventScroll: true });
            setMobileFilterOpen(!mobileFilterOpen);
          }}
          aria-expanded={mobileFilterOpen}
          aria-controls={mobileFilterOpen ? 'catalog-mobile-filters' : undefined}
          className="lg:hidden min-h-[44px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white text-xs font-bold self-start focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400"
        >
          <Filter className="w-4 h-4" />
          <span>Filter & Kategori ({filteredProducts.length})</span>
        </button>
      </div>

      {/* Search Bar */}
      <div ref={searchContainerRef} className="w-full max-w-3xl">
        <SearchBar
          value={searchQuery}
          onChange={setSearchQuery}
          onClear={() => setSearchQuery('')}
        />
      </div>

      {/* Main Content Layout: Sidebar Filter + Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Desktop Sidebar Filter */}
        <div className="hidden lg:block lg:col-span-4 sticky top-24">
          <FilterPanel
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            selectedBrand={selectedBrand}
            onSelectBrand={setSelectedBrand}
            selectedPriceRange={selectedPriceRange}
            onSelectPriceRange={setSelectedPriceRange}
            sortBy={sortBy}
            onSelectSort={setSortBy}
            onResetFilters={handleResetFilters}
            brands={brands}
            totalFound={filteredProducts.length}
          />
        </div>

        {/* Mobile Filter Drawer / Modal */}
        {mobileFilterOpen && (
          <dialog
            id="catalog-mobile-filters"
            ref={filterDialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="catalog-filter-title"
            className="fixed inset-0 z-50 m-0 h-full w-full max-h-none max-w-none border-0 text-inherit bg-slate-950/70 backdrop:bg-transparent p-4 overflow-y-auto"
          >
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 max-w-md mx-auto space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h2 id="catalog-filter-title" ref={filterTitleRef} tabIndex={-1} className="font-bold text-sm">Filter & Pengurutan</h2>
                <button
                  type="button"
                  onClick={() => setMobileFilterOpen(false)}
                  aria-label="Tutup filter dan pengurutan"
                  className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center p-1 rounded-lg text-slate-600 dark:text-slate-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-300">
                Perubahan filter langsung diterapkan.
              </p>

              <FilterPanel
                selectedCategory={selectedCategory}
                onSelectCategory={setSelectedCategory}
                selectedBrand={selectedBrand}
                onSelectBrand={setSelectedBrand}
                selectedPriceRange={selectedPriceRange}
                onSelectPriceRange={setSelectedPriceRange}
                sortBy={sortBy}
                onSelectSort={setSortBy}
                onResetFilters={handleResetFilters}
                brands={brands}
                totalFound={filteredProducts.length}
              />

              <button
                type="button"
                onClick={() => setMobileFilterOpen(false)}
                className="w-full min-h-[44px] px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400"
              >
                Lihat hasil ({filteredProducts.length} produk)
              </button>
            </div>
          </dialog>
        )}

        {/* Product Grid Area */}
        <div className="lg:col-span-8 space-y-6">
          {/* Active filters badges */}
          {(selectedCategory || selectedBrand || hasBudgetFilter || searchQuery) && (
            <div className="flex items-center gap-2 flex-wrap text-xs">
              <span className="text-slate-600 dark:text-slate-300 font-semibold">Filter Aktif:</span>
              {selectedCategory && (
                <span className="px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold flex items-center gap-1">
                  Kategori: {selectedCategory}
                  <button type="button" onClick={() => setSelectedCategory('')}
                    aria-label={`Hapus filter kategori: ${selectedCategory}`}
                    className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {selectedBrand && (
                <span className="px-2.5 py-1 rounded-full bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-300 font-bold flex items-center gap-1">
                  Brand: {selectedBrand}
                  <button type="button" onClick={() => setSelectedBrand('')}
                    aria-label={`Hapus filter merek: ${selectedBrand}`}
                    className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {hasBudgetFilter && (
                <span className="px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold flex items-center gap-1">
                  Anggaran: {selectedPriceRange.label}
                  <button type="button" onClick={() => {
                    setSelectedPriceRange({ min: 0, max: null });
                    searchContainerRef.current?.querySelector('input')?.focus({ preventScroll: true });
                  }}
                    aria-label={`Hapus filter anggaran: ${selectedPriceRange.label}`}
                    className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {searchQuery && (
                <span className="px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 font-bold flex items-center gap-1">
                  Pencarian: &ldquo;{searchQuery}&rdquo;
                  <button type="button" onClick={() => setSearchQuery('')}
                    aria-label="Hapus filter pencarian"
                    className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
            </div>
          )}

          {/* Grid Cards */}
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="aspect-[3/4] rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse"
                />
              ))}
            </div>
          ) : filteredProducts.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <div className="text-center py-16 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 space-y-4">
              <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
                <Layers className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Tidak Menemukan Gadget yang Sesuai
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-300 max-w-sm mx-auto">
                Coba ubah kata kunci pencarian atau reset filter kategori dan rentang harga Anda.
              </p>
              <button
                type="button"
                onClick={handleResetFilters}
                className="min-h-[44px] px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400"
              >
                Reset Semua Filter
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
