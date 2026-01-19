import CellphonesCrawler from './src/crawlers/cellphones_api.js';
import { saveToJsonl, getTimestamp } from './src/utils/helpers.js';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Quick Test Script - Crawl nhanh với 1-2 pages để test
 */
async function main() {
    console.log('🧪 CellphoneS Quick Test Crawler\n');

    // Test config - crawl ít để test nhanh
    const config = {
        keywords: ['iphone', 'samsung'],  // 2 keywords để test
        maxPages: 2,                      // Chỉ 2 pages
        delayMs: 500,                     // Nhanh hơn (0.5s)
        province: 30
    };

    const crawler = new CellphonesCrawler({
        province: config.province,
        delayMs: config.delayMs
    });

    try {
        const results = await crawler.crawlMultipleKeywords(config.keywords, {
            maxPages: config.maxPages
        });

        // Gộp và lọc trùng
        let allProducts = [];
        for (const products of Object.values(results)) {
            allProducts.push(...products);
        }

        console.log(`\n📊 Tổng: ${allProducts.length} sản phẩm`);

        // Lọc trùng
        const uniqueProducts = [];
        const seenIds = new Set();

        for (const product of allProducts) {
            if (!seenIds.has(product.product_id)) {
                seenIds.add(product.product_id);
                uniqueProducts.push(product);
            }
        }

        console.log(`✨ Unique: ${uniqueProducts.length} sản phẩm`);
        console.log(`🗑️  Removed: ${allProducts.length - uniqueProducts.length} duplicates\n`);

        // Save
        const timestamp = getTimestamp();
        const filepath = path.join(__dirname, 'output', `test_${timestamp}.jsonl`);
        saveToJsonl(uniqueProducts, filepath);

        console.log('✅ Test completed!');

    } catch (error) {
        console.error('\n❌ Error:', error.message);
        process.exit(1);
    }
}

main();
