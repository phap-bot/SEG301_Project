function randomDelay(min = 2000, max = 6000) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function extractTikiProductId(url) {
  const match = url.match(/p(\d+)\.html/);
  return match ? match[1] : null;
}

function extractLazadaProductId(url) {
  // Ví dụ: https://www.lazada.vn/iphone-15-pro-max-256gb-i123456789.html
  const match = url.match(/-i(\d+)\.html/);
  return match ? match[1] : null;
}

function parsePrice(priceText) {
  if (!priceText) return 0;
  const cleaned = priceText.replace(/[^\d]/g, '');
  return cleaned ? parseInt(cleaned) : 0;
}

function calculateDiscount(original, current) {
  if (!original || !current || original <= current) return 0;
  return Math.round(((original - current) / original) * 100);
}

function parseRating(ratingText) {
  if (!ratingText) return 0;
  const match = ratingText.match(/[\d.]+/);
  return match ? parseFloat(match[0]) : 0;
}

function parseReviewCount(reviewText) {
  if (!reviewText) return 0;
  const cleaned = reviewText.replace(/[^\d]/g, '');
  return cleaned ? parseInt(cleaned) : 0;
}

module.exports = {
  randomDelay,
  extractTikiProductId,
  extractLazadaProductId,
  parsePrice,
  calculateDiscount,
  parseRating,
  parseReviewCount
};