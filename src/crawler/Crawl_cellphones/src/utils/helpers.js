import fs from 'fs';
import path from 'path';

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

/**
 * Lưu array of objects vào file JSONL
 */
export function saveToJsonl(data, filepath) {
    const jsonlContent = data.map(item => JSON.stringify(item)).join('\n');
    fs.writeFileSync(filepath, jsonlContent + '\n', 'utf8');
    console.log(`✅ Đã lưu ${data.length} sản phẩm vào ${filepath}`);
}

/**
 * Append array of objects vào file JSONL (không overwrite)
 */
export function appendToJsonl(data, filepath) {
    const jsonlContent = data.map(item => JSON.stringify(item)).join('\n');
    fs.appendFileSync(filepath, jsonlContent + '\n', 'utf8');
    console.log(`✅ Đã thêm ${data.length} sản phẩm vào ${filepath}`);
}

/**
 * Đọc file JSONL thành array of objects
 */
export function loadFromJsonl(filepath) {
    if (!fs.existsSync(filepath)) {
        return [];
    }
    const content = fs.readFileSync(filepath, 'utf8');
    return content
        .split('\n')
        .filter(line => line.trim())
        .map(line => JSON.parse(line));
}

/**
 * Tính tổng số trang dựa trên total items và items per page
 */
export function calculateTotalPages(total, perPage = 20) {
    return Math.ceil(total / perPage);
}

/**
 * Delay (sleep) trong async function
 */
export function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Lấy timestamp hiện tại cho filename
 */
export function getTimestamp() {
    const now = new Date();
    return now.toISOString().replace(/[:.]/g, '-').slice(0, -5);
}

/**
 * Sanitize filename (remove invalid characters)
 */
export function sanitizeFilename(filename) {
    return filename.replace(/[<>:"/\\|?*]/g, '_').replace(/\s+/g, '_').toLowerCase();
}
