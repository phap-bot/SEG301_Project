import { loadFromJsonl, saveToJsonl } from './src/utils/helpers.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Script để merge các file cũ vào cellphones_products.jsonl
 */
async function mergeOldFiles() {
    console.log('🔄 Bắt đầu merge các file cũ...\n');

    const outputDir = path.join(__dirname, 'output');
    const targetFile = path.join(outputDir, 'cellphones_products.jsonl');

    // Tìm tất cả file cellphones_all_products_*.jsonl
    const oldFiles = fs.readdirSync(outputDir)
        .filter(file => file.startsWith('cellphones_all_products_') && file.endsWith('.jsonl'))
        .map(file => path.join(outputDir, file));

    if (oldFiles.length === 0) {
        console.log('❌ Không tìm thấy file cũ nào!');
        return;
    }

    console.log(`📁 Tìm thấy ${oldFiles.length} file cũ:`);
    oldFiles.forEach(file => console.log(`   - ${path.basename(file)}`));
    console.log();

    // Đọc tất cả dữ liệu
    let allProducts = [];

    for (const file of oldFiles) {
        const products = loadFromJsonl(file);
        console.log(`📂 ${path.basename(file)}: ${products.length} sản phẩm`);
        allProducts.push(...products);
    }

    console.log(`\n📊 Tổng sản phẩm từ các file cũ: ${allProducts.length}`);

    // Lọc trùng dựa trên product_id
    const uniqueProducts = [];
    const seenIds = new Set();

    for (const product of allProducts) {
        if (!seenIds.has(product.product_id)) {
            seenIds.add(product.product_id);
            uniqueProducts.push(product);
        }
    }

    console.log(`✨ Sản phẩm sau khi lọc trùng: ${uniqueProducts.length}`);
    console.log(`🗑️  Đã loại bỏ: ${allProducts.length - uniqueProducts.length} sản phẩm trùng\n`);

    // Lưu vào file mới
    saveToJsonl(uniqueProducts, targetFile);

    // Xóa các file cũ
    console.log('\n🗑️  Đang xóa các file cũ...');
    for (const file of oldFiles) {
        fs.unlinkSync(file);
        console.log(`   ✅ Đã xóa: ${path.basename(file)}`);
    }

    console.log('\n✅ Hoàn thành! Tất cả dữ liệu đã được merge vào cellphones_products.jsonl');
}

mergeOldFiles().catch(console.error);
