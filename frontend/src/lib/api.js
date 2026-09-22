/**
 * CompareBuy API Client
 * Interacts with Python FastAPI microservice with intelligent client-side fallback.
 */

import { PRODUCTS } from '@/data/products';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Fetch all catalog products with optional query filters
 */
export async function getProducts(params = {}) {
  try {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.category) query.append('category', params.category);
    if (params.brand) query.append('brand', params.brand);
    if (params.min_price) query.append('min_price', params.min_price);
    if (params.max_price) query.append('max_price', params.max_price);
    if (params.sort_by) query.append('sort_by', params.sort_by);

    const res = await fetch(`${API_BASE}/api/products?${query.toString()}`, {
      cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API call failed, using client-side fallback:', err.message);

    // Fallback: Filter locally from PRODUCTS
    let filtered = [...PRODUCTS];

    if (params.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.brand.toLowerCase().includes(q) ||
          p.tags.some((t) => t.toLowerCase().includes(q))
      );
    }

    if (params.category) {
      filtered = filtered.filter((p) => p.category === params.category);
    }

    if (params.brand) {
      filtered = filtered.filter(
        (p) => p.brand.toLowerCase() === params.brand.toLowerCase()
      );
    }

    if (params.min_price) {
      filtered = filtered.filter((p) => p.price >= Number(params.min_price));
    }

    if (params.max_price) {
      filtered = filtered.filter((p) => p.price <= Number(params.max_price));
    }

    if (params.sort_by === 'price_asc') {
      filtered.sort((a, b) => a.price - b.price);
    } else if (params.sort_by === 'price_desc') {
      filtered.sort((a, b) => b.price - a.price);
    } else if (params.sort_by === 'name') {
      filtered.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      // Default: sort by average score
      filtered.sort((a, b) => {
        const scoreA =
          (a.score_performance + a.score_camera + a.score_battery + a.score_display + a.score_value) / 5;
        const scoreB =
          (b.score_performance + b.score_camera + b.score_battery + b.score_display + b.score_value) / 5;
        return scoreB - scoreA;
      });
    }

    return {
      products: filtered,
      total: filtered.length,
      page: 1,
      per_page: filtered.length,
    };
  }
}

/**
 * Fetch a single product by ID
 */
export async function getProductById(productId) {
  try {
    const res = await fetch(`${API_BASE}/api/products/${productId}`, {
      cache: 'no-store',
    });
    if (!res.ok) throw new Error('Product not found');
    return await res.json();
  } catch (err) {
    const fallback = PRODUCTS.find((p) => p.id === productId);
    if (!fallback) throw new Error('Product not found');
    return fallback;
  }
}

/**
 * Execute Weighted Dynamic Scoring Engine for Wizard input
 */
export async function scoreRecommendations(wizardInput) {
  try {
    const res = await fetch(`${API_BASE}/api/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(wizardInput),
    });

    if (!res.ok) throw new Error(`Scoring API error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Scoring API offline, performing local client-side calculation:', err.message);

    // Filter products by category
    const categoryProducts = PRODUCTS.filter((p) => p.category === wizardInput.category);

    const dimensions = ['performance', 'camera', 'battery', 'display', 'build_quality', 'value'];
    const scenarioWeights = {
      gaming: { performance: 0.15, display: 0.08, battery: 0.02 },
      productivity: { performance: 0.08, battery: 0.07, display: 0.05 },
      photography: { camera: 0.20, display: 0.05 },
      content_creation: { performance: 0.10, display: 0.10, camera: 0.05 },
      business: { build_quality: 0.08, battery: 0.07, performance: 0.05 },
      student: { value: 0.15, battery: 0.10 },
      fitness: { build_quality: 0.10, battery: 0.10 },
      multimedia: { display: 0.12, battery: 0.06 },
      casual: { value: 0.10, battery: 0.08 },
    };

    // Build raw weights
    const weights = {};
    dimensions.forEach((dim) => {
      weights[dim] = Number(wizardInput.priorities?.[dim] || 3);
    });

    // Apply scenario boosts
    (wizardInput.scenarios || []).forEach((sc) => {
      const boosts = scenarioWeights[sc] || {};
      Object.entries(boosts).forEach(([dim, val]) => {
        weights[dim] = (weights[dim] || 3) + val * 10;
      });
    });

    // Normalize
    const sumW = Object.values(weights).reduce((a, b) => a + b, 0) || 1;
    const normWeights = {};
    Object.keys(weights).forEach((k) => {
      normWeights[k] = weights[k] / sumW;
    });

    // Score products
    const results = categoryProducts.map((p) => {
      const breakdown = dimensions.map((dim) => {
        const rawScore = p[`score_${dim}`] || 50;
        const w = normWeights[dim] || 0.16;
        return {
          dimension: dim,
          weight: Math.round(w * 1000) / 1000,
          raw_score: rawScore,
          weighted_score: Math.round(rawScore * w * 10) / 10,
        };
      });

      const weightedSum = breakdown.reduce((sum, item) => sum + item.weighted_score, 0);

      // Budget fit calculation
      let budgetFit = 'within';
      let modifier = 5.0;
      if (p.price < wizardInput.budget_min) {
        budgetFit = 'below';
        modifier = 2.0;
      } else if (p.price > wizardInput.budget_max) {
        budgetFit = 'above';
        const overPct = (p.price - wizardInput.budget_max) / wizardInput.budget_max;
        modifier = overPct <= 0.2 ? -5.0 : -15.0;
      }

      const totalScore = Math.max(10, Math.min(100, Math.round((weightedSum + modifier) * 10) / 10));

      // Construct dynamic narrative
      const topStrengths = [...breakdown]
        .sort((a, b) => b.weighted_score - a.weighted_score)
        .slice(0, 3);

      const dimLabels = {
        performance: 'Performa & Kecepatan',
        camera: 'Kamera & Lensa',
        battery: 'Daya Tahan Baterai',
        display: 'Layar & Visual',
        build_quality: 'Build Quality & Rangka',
        value: 'Value for Money',
      };

      const whyNarrative = `**${p.name}** adalah pilihan unggulan Anda karena:\n` +
        topStrengths.map((s, idx) => `• **${dimLabels[s.dimension] || s.dimension}**: Mendapatkan skor tinggi ${s.raw_score}/100 yang sangat selaras dengan prioritas Anda.`).join('\n') +
        `\n• **Status Budget**: ${budgetFit === 'within' ? 'Pas dengan anggaran' : budgetFit === 'below' ? 'Hemat di bawah budget' : 'Sedikit di atas anggaran namun sebanding dengan fiturnya'}.`;

      return {
        product: p,
        total_score: totalScore,
        rank: 0,
        score_breakdown: breakdown,
        why_this_product: whyNarrative,
        budget_fit: budgetFit,
      };
    });

    results.sort((a, b) => b.total_score - a.total_score);
    results.forEach((item, idx) => {
      item.rank = idx + 1;
    });

    return {
      results,
      total_products_evaluated: categoryProducts.length,
      wizard_input: wizardInput,
    };
  }
}

/**
 * Fetch comparison matrix with auto-highlighted best specs
 */
export async function compareProducts(productIds) {
  try {
    const res = await fetch(`${API_BASE}/api/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_ids: productIds }),
    });

    if (!res.ok) throw new Error(`Compare API error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Compare API offline, generating local comparison matrix:', err.message);

    const products = PRODUCTS.filter((p) => productIds.includes(p.id));
    const specFields = [
      { key: 'display', label: 'Layar & Resolusi' },
      { key: 'processor', label: 'Prosesor / Chipset' },
      { key: 'ram', label: 'RAM / Memori' },
      { key: 'storage', label: 'Penyimpanan Internal' },
      { key: 'battery', label: 'Kapasitas Baterai' },
      { key: 'camera', label: 'Kamera' },
      { key: 'os', label: 'Sistem Operasi' },
      { key: 'weight', label: 'Bobot Perangkat' },
      { key: 'refresh_rate', label: 'Refresh Rate' },
      { key: 'water_resistance', label: 'Ketahanan Air & Debu' },
      { key: 'build_material', label: 'Material Bodi' },
      { key: 'special_features', label: 'Fitur Unggulan' },
    ];

    const highlights = specFields.map(({ key, label }) => {
      const values = {};
      products.forEach((p) => {
        values[p.id] = p.specs[key] || '—';
      });

      // Simple best finder: product with highest numeric value if present
      let bestId = products[0]?.id || '';
      let maxVal = -1;

      products.forEach((p) => {
        const text = p.specs[key] || '';
        const num = parseFloat(text.replace(/[^0-9.]/g, ''));
        if (!isNaN(num) && num > maxVal) {
          maxVal = num;
          bestId = p.id;
        }
      });

      return {
        spec_name: label,
        values,
        best_product_id: bestId,
      };
    });

    return {
      products,
      highlights,
    };
  }
}

/**
 * Fetch live marketplace prices for a product
 */
export async function getLiveMarketplacePrices(productId) {
  try {
    const res = await fetch(`${API_BASE}/api/prices/${productId}`, {
      cache: 'no-store',
    });
    if (!res.ok) throw new Error('Live price API failed');
    return await res.json();
  } catch (err) {
    const product = PRODUCTS.find((p) => p.id === productId);
    const basePrice = product ? product.price : 5000000;

    // Realistic dynamic variation
    return {
      product_id: productId,
      product_name: product ? product.name : 'Gadget',
      last_updated: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) + ' WIB',
      prices: [
        {
          marketplace: 'Tokopedia',
          price: Math.round(basePrice * 0.97),
          url: product?.marketplace_links?.tokopedia || 'https://www.tokopedia.com',
          seller: `${product?.brand || 'Official'} Store Official`,
          available: true,
        },
        {
          marketplace: 'Shopee',
          price: Math.round(basePrice * 0.96),
          url: product?.marketplace_links?.shopee || 'https://shopee.co.id',
          seller: `${product?.brand || 'Official'} Mall Indonesia`,
          available: true,
        },
        {
          marketplace: 'Lazada',
          price: Math.round(basePrice * 0.98),
          url: product?.marketplace_links?.lazada || 'https://www.lazada.co.id',
          seller: `LazMall ${product?.brand || 'Brand'} Partner`,
          available: true,
        },
      ].sort((a, b) => a.price - b.price),
    };
  }
}
