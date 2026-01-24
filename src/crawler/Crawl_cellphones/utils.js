import fs from 'fs';
import path from 'path';

/**
 * Lưu array of objects vào file JSONL
 */
export function saveToJsonl(data, filepath) {
    // Ensure directory exists
    const dir = path.dirname(filepath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }

    const jsonlContent = data.map(item => JSON.stringify(item)).join('\n');
    fs.writeFileSync(filepath, jsonlContent + '\n', 'utf8');
    console.log(`✅ Đã lưu ${data.length} sản phẩm vào ${filepath}`);
}

/**
 * Append array of objects vào file JSONL (không overwrite)
 */
export function appendToJsonl(data, filepath) {
    const dir = path.dirname(filepath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }

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
        .map(line => {
            try {
                return JSON.parse(line);
            } catch (e) {
                return null;
            }
        })
        .filter(item => item !== null);
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
