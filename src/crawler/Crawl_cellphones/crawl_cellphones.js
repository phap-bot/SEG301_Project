import CellphonesCrawler from './src/crawlers/cellphones_api.js';
import { saveToJsonl, sanitizeFilename, getTimestamp } from './src/utils/helpers.js';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Main Script - Crawl CellphoneS Products
 */
async function main() {
    console.log('🚀 CellphoneS Crawler Starting...\n');

    // Configuration - THÊM/XÓA KEYWORDS Ở ĐÂY
    const config = {
        keywords: [
            // 'samsung',
            //'laptop',
            //  'tai nghe',
            // 'smartwatch',
            // 'tablet',
            // 'macbook',
            // 'ipad',
            // 'mic',
            //   'dong ho',
            // 'camera',
            // 'do gia dung',
            // 'phu kien',
            // 'pc',
            // 'man hinh',
            // 'may in',
            // 'ti vi',
            // 'dien may',
            // 'khuyen mai'
            'tan nhiet',
            'thung may',
            'nguon may',
            'ram',
            'oc cứng',
            'ssd',
            'card do hoa',
            'main',
            'tay cam',
            'loa',
            'gia treo man hinh',
            'loa karaoke',
            'op dien thoai'

        ],
        maxPages: Infinity,        // Số pages mỗi keyword (hoặc Infinity để crawl hết)
        delayMs: 1000,      // Delay 1 giây giữa các requests
        province: 30        // 30 = HCM, 1 = Hanoi
    };

    // Initialize crawler
    const crawler = new CellphonesCrawler({
        province: config.province,
        delayMs: config.delayMs
    });

    try {
        // Crawl all keywords
        const results = await crawler.crawlMultipleKeywords(config.keywords, {
            maxPages: config.maxPages
        });

        // ===== LỌC TRÙNG VÀ GỘP TẤT CẢ VÀO 1 FILE =====
        console.log('\n💾 Đang lưu dữ liệu...\n');

        const outputDir = path.join(__dirname, 'output');
        const filename = 'cellphones_products.jsonl';
        const filepath = path.join(outputDir, filename);

        // Gộp tất cả products từ các keywords
        let allProducts = [];
        for (const [keyword, products] of Object.entries(results)) {
            allProducts.push(...products);
        }

        console.log(`📊 Tổng sản phẩm crawl lần này: ${allProducts.length}`);

        // Đọc dữ liệu cũ nếu có
        const { loadFromJsonl } = await import('./src/utils/helpers.js');
        const existingProducts = loadFromJsonl(filepath);
        console.log(`📂 Sản phẩm đã có trong file: ${existingProducts.length}`);

        // Gộp dữ liệu cũ và mới
        const combinedProducts = [...existingProducts, ...allProducts];

        // Lọc trùng dựa trên product_id (giữ bản mới nhất)
        const uniqueProducts = [];
        const seenIds = new Map(); // Dùng Map để tracking index

        for (let i = combinedProducts.length - 1; i >= 0; i--) {
            const product = combinedProducts[i];
            if (!seenIds.has(product.product_id)) {
                seenIds.set(product.product_id, true);
                uniqueProducts.unshift(product); // Thêm vào đầu để giữ thứ tự
            }
        }

        console.log(`✨ Tổng sản phẩm sau khi lọc trùng: ${uniqueProducts.length}`);
        console.log(`🗑️  Đã loại bỏ: ${combinedProducts.length - uniqueProducts.length} sản phẩm trùng\n`);

        // Ghi đè file với dữ liệu đã lọc trùng
        saveToJsonl(uniqueProducts, filepath);

        // Summary
        console.log('\n📈 Tổng kết:');
        console.log('─'.repeat(50));
        for (const [keyword, products] of Object.entries(results)) {
            console.log(`  ${keyword}: ${products.length} sản phẩm`);
        }
        console.log('─'.repeat(50));
        console.log(`  TỔNG (trước lọc): ${allProducts.length} sản phẩm`);
        console.log(`  TỔNG (sau lọc): ${uniqueProducts.length} sản phẩm`);
        console.log('─'.repeat(50));
        console.log(`  📁 Output: ${filename}\n`);

        console.log('✅ Hoàn thành!');

    } catch (error) {
        console.error('\n❌ Lỗi:', error.message);
        process.exit(1);
    }
}

// Run
main();
