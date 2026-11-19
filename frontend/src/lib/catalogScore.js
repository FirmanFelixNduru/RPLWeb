// Only missing values use the neutral default; zero is a valid score.
export function getCatalogScore(product) {
  return Math.round(
    ((product.score_performance ?? 50) +
      (product.score_camera ?? 50) +
      (product.score_battery ?? 50) +
      (product.score_display ?? 50) +
      (product.score_value ?? 50)) / 5
  );
}
