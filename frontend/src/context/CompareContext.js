'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

const MAX_COMPARE = 4;

const CompareContext = createContext({
  compareList: [],
  addToCompare: () => {},
  removeFromCompare: () => {},
  isInCompare: () => false,
  clearCompare: () => {},
  activeProductModal: null,
  openProductModal: () => {},
  closeProductModal: () => {},
});

export function CompareProvider({ children }) {
  const [compareList, setCompareList] = useState([]);
  const [activeProductModal, setActiveProductModal] = useState(null);

  // Load saved comparison from session/local storage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('comparebuy_dock');
      if (saved) {
        setCompareList(JSON.parse(saved));
      }
    } catch (e) {
      console.warn('Failed to parse saved compare dock items:', e);
    }
  }, []);

  const saveToStorage = (items) => {
    try {
      localStorage.setItem('comparebuy_dock', JSON.stringify(items));
    } catch (e) {
      console.warn('Failed to save compare dock items:', e);
    }
  };

  const addToCompare = (product) => {
    if (compareList.some((p) => p.id === product.id)) {
      // Already in list, remove it (toggle behavior)
      removeFromCompare(product.id);
      return false;
    }

    if (compareList.length >= MAX_COMPARE) {
      alert(`Maksimal perbandingan adalah ${MAX_COMPARE} produk sekaligus. Hapus salah satu produk terlebih dahulu.`);
      return false;
    }

    const updated = [...compareList, product];
    setCompareList(updated);
    saveToStorage(updated);
    return true;
  };

  const removeFromCompare = (productId) => {
    const updated = compareList.filter((p) => p.id !== productId);
    setCompareList(updated);
    saveToStorage(updated);
  };

  const isInCompare = (productId) => {
    return compareList.some((p) => p.id === productId);
  };

  const clearCompare = () => {
    setCompareList([]);
    saveToStorage([]);
  };

  const openProductModal = (product) => {
    setActiveProductModal(product);
  };

  const closeProductModal = () => {
    setActiveProductModal(null);
  };

  return (
    <CompareContext.Provider
      value={{
        compareList,
        addToCompare,
        removeFromCompare,
        isInCompare,
        clearCompare,
        activeProductModal,
        openProductModal,
        closeProductModal,
      }}
    >
      {children}
    </CompareContext.Provider>
  );
}

export function useCompare() {
  const context = useContext(CompareContext);
  if (!context) {
    throw new Error('useCompare must be used within a CompareProvider');
  }
  return context;
}
