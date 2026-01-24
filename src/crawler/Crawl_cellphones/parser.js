/**
 * Transform dữ liệu từ CellphoneS GraphQL API sang format JSONL
 */
export function transformCellphonesData(product, category) {
    const price = parseFloat(product.special_price || product.price || 0);
    const originalPrice = parseFloat(product.price || 0);

    // Tính discount_percent nếu có giá gốc
    let discountPercent = 0;
    if (originalPrice > price && originalPrice > 0) {
        discountPercent = Math.round(((originalPrice - price) / originalPrice) * 100);
    }

    return {
        platform: 'cellphones',
        product_id: String(product.product_id || ''),
        product_name: product.name || '',
        price: price,
        original_price: originalPrice,
        discount_percent: discountPercent,
        product_url: product.url_path
            ? `https://cellphones.com.vn/${product.url_path}.html`
            : '',
        image_url: product.thumbnail || '',
        rating: 0, // API không cung cấp field này
        review_count: 0, // API không cung cấp field này
        category: category || ''
    };
}
