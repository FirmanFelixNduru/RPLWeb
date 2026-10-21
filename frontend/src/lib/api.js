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
    if (params.min_price != null) query.append('min_price', params.min_price);
    if (params.max_price != null) query.append('max_price', params.max_price);
    if (params.tags) query.append('tags', Array.isArray(params.tags) ? params.tags.join(',') : params.tags);
    if (params.sort_by) query.append('sort_by', params.sort_by);
    if (params.page) query.append('page', params.page);
    if (params.per_page) query.append('per_page', params.per_page);

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
          p.description.toLowerCase().includes(q) ||
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

    if (params.min_price != null) {
      filtered = filtered.filter((p) => p.price >= Number(params.min_price));
    }

    if (params.max_price != null) {
      filtered = filtered.filter((p) => p.price <= Number(params.max_price));
    }

    if (params.tags) {
      const requestedTags = (Array.isArray(params.tags) ? params.tags : params.tags.split(','))
        .map((tag) => tag.trim().toLowerCase())
        .filter(Boolean);
      filtered = filtered.filter((product) =>
        requestedTags.some((tag) => product.tags.some((productTag) => productTag.toLowerCase() === tag))
      );
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
        const scoreA = [
          a.score_performance, a.score_camera, a.score_battery, a.score_display,
          a.score_build_quality, a.score_value, a.score_audio, a.score_software,
        ].reduce((sum, score) => sum + score, 0) / 8;
        const scoreB = [
          b.score_performance, b.score_camera, b.score_battery, b.score_display,
          b.score_build_quality, b.score_value, b.score_audio, b.score_software,
        ].reduce((sum, score) => sum + score, 0) / 8;
        return scoreB - scoreA;
      });
    }

    const page = Number(params.page) || 1;
    const perPage = Number(params.per_page) || 20;
    const start = (page - 1) * perPage;

    return {
      products: filtered.slice(start, start + perPage),
      total: filtered.length,
      page,
      per_page: perPage,
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

    const dimensions = [
      'performance', 'camera', 'battery', 'display',
      'build_quality', 'value', 'audio', 'software',
    ];
    const scenarioWeights = {
      gaming: { performance: 0.15, display: 0.08, audio: 0.05, battery: 0.02 },
      productivity: { performance: 0.08, software: 0.10, display: 0.05, battery: 0.07 },
      photography: { camera: 0.20, display: 0.05, software: 0.03 },
      social_media: { camera: 0.10, display: 0.05, battery: 0.05 },
      content_creation: { performance: 0.10, display: 0.10, camera: 0.05, software: 0.05 },
      business: { software: 0.10, build_quality: 0.08, battery: 0.07, performance: 0.05 },
      student: { value: 0.15, battery: 0.10, software: 0.05 },
      fitness: { build_quality: 0.10, battery: 0.10, software: 0.05 },
      multimedia: { display: 0.12, audio: 0.12, battery: 0.06 },
      casual: { value: 0.10, battery: 0.08, build_quality: 0.05, software: 0.05 },
    };

    // Build raw weights
    const weights = {};
    dimensions.forEach((dim) => {
      weights[dim] = Number(wizardInput.priorities?.[dim] ?? 3);
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
        const rawScore = p[`score_${dim}`] ?? 50;
        const w = normWeights[dim] ?? 0;
        return {
          dimension: dim,
          weight: Math.round(w * 10000) / 10000,
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
        const overPct = (p.price - wizardInput.budget_max) / Math.max(wizardInput.budget_max, 1);
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
        audio: 'Kualitas Audio',
        software: 'Software & Update',
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

    // Determine category consistency
    const categories = new Set(products.map((p) => p.category));
    const isSameCategory = categories.size === 1;
    const currentCategory = isSameCategory ? products[0]?.category : null;

    const CATEGORY_RELEVANT_DIMENSIONS = {
      smartphone: ['performance', 'camera', 'battery', 'display', 'build_quality', 'value', 'audio', 'software'],
      laptop: ['performance', 'camera', 'battery', 'display', 'build_quality', 'value', 'audio', 'software'],
      tablet: ['performance', 'camera', 'battery', 'display', 'build_quality', 'value', 'audio', 'software'],
      smartwatch: ['performance', 'battery', 'display', 'build_quality', 'value', 'audio', 'software'],
      tws: ['performance', 'battery', 'build_quality', 'value', 'audio', 'software'],
    };

    const applicableDimensions = isSameCategory
      ? (CATEGORY_RELEVANT_DIMENSIONS[currentCategory] || [])
      : [];

    const DESCRIPTIVE_FIELDS = new Set([
      'processor', 'os', 'ports', 'connectivity', 'sensors',
      'build_material', 'special_features',
    ]);

    const specFields = [
      { key: 'display', label: 'Layar & Resolusi' },
      { key: 'refresh_rate', label: 'Refresh Rate' },
      { key: 'resolution', label: 'Resolusi' },
      { key: 'processor', label: 'Prosesor / Chipset' },
      { key: 'gpu', label: 'Kartu Grafis / GPU' },
      { key: 'ram', label: 'RAM / Memori' },
      { key: 'storage', label: 'Penyimpanan Internal' },
      { key: 'battery', label: 'Kapasitas Baterai' },
      { key: 'charging', label: 'Pengisian Daya / Charger' },
      { key: 'ports', label: 'Port & Konektor I/O' },
      { key: 'driver_size', label: 'Ukuran Driver Audio' },
      { key: 'anc', label: 'Peredam Bising (ANC)' },
      { key: 'codec', label: 'Dukungan Codec Audio' },
      { key: 'sensors', label: 'Sensor & Pelacakan' },
      { key: 'camera', label: 'Konfigurasi Kamera' },
      { key: 'os', label: 'Sistem Operasi' },
      { key: 'weight', label: 'Bobot Perangkat' },
      { key: 'water_resistance', label: 'Sertifikasi Tahan Air' },
      { key: 'build_material', label: 'Material Rangka' },
      { key: 'special_features', label: 'Fitur Khusus' },
    ];

    const extractNum = (val, key) => {
      if (!val || val === 'N/A' || val === '—' || val === '-') return null;
      if (DESCRIPTIVE_FIELDS.has(key)) return null;

      const str = String(val).trim();
      // Storage TB -> GB
      if (key === 'storage' || /\btb\b/i.test(str)) {
        const tbMatch = str.match(/(\d+(?:\.\d+)?)\s*tb\b/i);
        if (tbMatch) return parseFloat(tbMatch[1]) * 1024;
        const gbMatch = str.match(/(\d+(?:\.\d+)?)\s*gb\b/i);
        if (gbMatch) return parseFloat(gbMatch[1]);
      }
      // Weight kg -> g
      if (key === 'weight' || /\bkg\b/i.test(str)) {
        const kgMatch = str.match(/(\d+(?:\.\d+)?)\s*kg\b/i);
        if (kgMatch) return parseFloat(kgMatch[1]) * 1000;
        const gMatch = str.match(/(\d+(?:\.\d+)?)\s*g\b/i);
        if (gMatch) return parseFloat(gMatch[1]);
      }
      // Standard number
      const numMatch = str.replace(/,/g, '').match(/(\d+(?:\.\d+)?)/);
      if (numMatch) return parseFloat(numMatch[1]);
      return null;
    };

    const highlights = specFields.map(({ key }) => {
      const values = {};
      let hasValue = false;
      products.forEach((p) => {
        const val = p.specs ? p.specs[key] : null;
        if (val && val !== 'N/A') {
          values[p.id] = val;
          hasValue = true;
        } else {
          values[p.id] = '—';
        }
      });

      // Battery unit comparability
      if (key === 'battery') {
        const vals = Object.values(values).map((v) => String(v).toLowerCase());
        const hasMah = vals.some((v) => v.includes('mah'));
        const hasWh = vals.some((v) => v.includes('wh'));
        if (hasMah && hasWh) {
          return {
            spec_name: key,
            values,
            best_product_id: '',
            best_product_ids: [],
            is_tie: false,
          };
        }
      }

      if (!hasValue || DESCRIPTIVE_FIELDS.has(key)) {
        return {
          spec_name: key,
          values,
          best_product_id: '',
          best_product_ids: [],
          is_tie: false,
        };
      }

      const numericVals = {};
      Object.entries(values).forEach(([pid, val]) => {
        const n = extractNum(val, key);
        if (n !== null) numericVals[pid] = n;
      });

      const pids = Object.keys(numericVals);
      if (pids.length === 0) {
        return {
          spec_name: key,
          values,
          best_product_id: '',
          best_product_ids: [],
          is_tie: false,
        };
      }

      const lowerIsBetter = key === 'weight' || key === 'price';
      const targetVal = lowerIsBetter
        ? Math.min(...Object.values(numericVals))
        : Math.max(...Object.values(numericVals));

      const winners = pids.filter((pid) => numericVals[pid] === targetVal);
      const isTie = winners.length > 1;

      return {
        spec_name: key,
        values,
        best_product_id: isTie ? '' : (winners[0] || ''),
        best_product_ids: winners,
        is_tie: isTie,
      };
    });

    // 8 Dimensions Evaluation
    const dimensionFields = [
      { attr: 'score_performance', label: 'Skor Performa', dimKey: 'performance' },
      { attr: 'score_camera', label: 'Skor Kamera', dimKey: 'camera' },
      { attr: 'score_battery', label: 'Skor Baterai', dimKey: 'battery' },
      { attr: 'score_display', label: 'Skor Layar', dimKey: 'display' },
      { attr: 'score_build_quality', label: 'Skor Build Quality', dimKey: 'build_quality' },
      { attr: 'score_value', label: 'Skor Value', dimKey: 'value' },
      { attr: 'score_audio', label: 'Skor Audio', dimKey: 'audio' },
      { attr: 'score_software', label: 'Skor Software', dimKey: 'software' },
    ];

    const winCounts = {};
    const winningSectors = {};
    const tiedSectors = {};
    const tiedSectorsSummary = [];
    products.forEach((p) => {
      winCounts[p.id] = 0;
      winningSectors[p.id] = [];
      tiedSectors[p.id] = [];
    });

    dimensionFields.forEach(({ attr, label, dimKey }) => {
      const values = {};
      const isApplicable = isSameCategory && applicableDimensions.includes(dimKey);

      if (isSameCategory && !isApplicable) {
        products.forEach((p) => {
          values[p.id] = '— (Tidak Berlaku)';
        });
        highlights.push({
          spec_name: label,
          values,
          best_product_id: '',
          best_product_ids: [],
          is_tie: false,
        });
        return;
      }

      products.forEach((p) => {
        values[p.id] = p[attr] !== undefined && p[attr] !== null ? String(p[attr]) : '—';
      });

      const hasMissing = Object.values(values).some((v) => v === '—');
      if (isSameCategory && !hasMissing) {
        const scores = {};
        Object.entries(values).forEach(([pid, v]) => {
          scores[pid] = parseInt(v, 10);
        });
        const maxScore = Math.max(...Object.values(scores));
        const winners = Object.keys(scores).filter((pid) => scores[pid] === maxScore);

        if (winners.length > 1) {
          winners.forEach((wId) => {
            winCounts[wId] += 1;
            tiedSectors[wId].push(`${label} (Seri)`);
          });
          const tiedNames = winners.map((wId) => products.find((p) => p.id === wId)?.name || wId);
          tiedSectorsSummary.push(`${label}: Seri antara ${tiedNames.join(', ')} (${maxScore})`);
          highlights.push({
            spec_name: label,
            values,
            best_product_id: '',
            best_product_ids: winners,
            is_tie: true,
          });
        } else if (winners.length === 1) {
          const wId = winners[0];
          winCounts[wId] += 1;
          winningSectors[wId].push(label);
          highlights.push({
            spec_name: label,
            values,
            best_product_id: wId,
            best_product_ids: [wId],
            is_tie: false,
          });
        }
      } else {
        highlights.push({
          spec_name: label,
          values,
          best_product_id: '',
          best_product_ids: [],
          is_tie: false,
        });
      }
    });

    // Price highlight
    const priceValues = {};
    products.forEach((p) => {
      priceValues[p.id] = String(p.price);
    });
    const minPrice = Math.min(...products.map((p) => p.price));
    const cheapestIds = products.filter((p) => p.price === minPrice).map((p) => p.id);
    const isPriceTie = cheapestIds.length > 1;

    highlights.push({
      spec_name: 'Harga (IDR)',
      values: priceValues,
      best_product_id: (!isSameCategory || isPriceTie) ? '' : (cheapestIds[0] || ''),
      best_product_ids: isSameCategory ? cheapestIds : [],
      is_tie: isSameCategory && isPriceTie,
    });

    // Warranty highlight
    const warrantyValues = {};
    products.forEach((p) => {
      warrantyValues[p.id] = `${p.warranty?.duration_months || 0} bulan (skor: ${p.warranty?.score || 0})`;
    });
    const maxWarrantyScore = Math.max(...products.map((p) => p.warranty?.score || 0));
    const topWarrantyIds = products.filter((p) => (p.warranty?.score || 0) === maxWarrantyScore).map((p) => p.id);
    const isWarrantyTie = topWarrantyIds.length > 1;

    highlights.push({
      spec_name: 'Garansi',
      values: warrantyValues,
      best_product_id: isWarrantyTie ? '' : (topWarrantyIds[0] || ''),
      best_product_ids: topWarrantyIds,
      is_tie: isWarrantyTie,
    });

    const winSummary = isSameCategory
      ? products.map((p) => ({
          product_id: p.id,
          product_name: p.name,
          win_count: winCounts[p.id],
          winning_sectors: winningSectors[p.id],
          tied_sectors: tiedSectors[p.id],
          solo_wins: winningSectors[p.id].length,
          shared_wins: tiedSectors[p.id].length,
        }))
      : [];

    return {
      products,
      highlights,
      is_same_category: isSameCategory,
      category: currentCategory,
      win_summary: winSummary,
      tied_sectors_summary: tiedSectorsSummary,
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
          source: 'fallback',
          captured_at: new Date().toISOString(),
        },
        {
          marketplace: 'Shopee',
          price: Math.round(basePrice * 0.96),
          url: product?.marketplace_links?.shopee || 'https://shopee.co.id',
          seller: `${product?.brand || 'Official'} Mall Indonesia`,
          available: true,
          source: 'fallback',
          captured_at: new Date().toISOString(),
        },
        {
          marketplace: 'Lazada',
          price: Math.round(basePrice * 0.98),
          url: product?.marketplace_links?.lazada || 'https://www.lazada.co.id',
          seller: `LazMall ${product?.brand || 'Brand'} Partner`,
          available: true,
          source: 'fallback',
          captured_at: new Date().toISOString(),
        },
      ].sort((a, b) => a.price - b.price),
    };
  }
}
