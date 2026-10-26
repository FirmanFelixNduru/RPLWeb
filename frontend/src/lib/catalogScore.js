// Preserve the existing card score, including its defaults and rounding.
export function getCatalogScore(product) {
  return Math.round(
    ((product.score_performance || 50) +
      (product.score_camera || 50) +
      (product.score_battery || 50) +
      (product.score_display || 50) +
      (product.score_value || 50)) / 5
  );
}
