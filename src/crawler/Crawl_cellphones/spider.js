import fetch from 'node-fetch';
import { transformCellphonesData } from './parser.js';
import { saveToJsonl, loadFromJsonl, delay } from './utils.js';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * CellphoneS GraphQL API Crawler
 * Crawl sản phẩm từ CellphoneS.com.vn bằng GraphQL API
 */
class CellphonesCrawler {
    constructor(options = {}) {
        this.apiUrl = 'https://api.cellphones.com.vn/graphql-search/v2/graphql/query';
        this.province = options.province || 30; // Default: HCM (30), Hanoi (1)
        this.delayMs = options.delayMs || 1000; // Delay giữa các requests (ms)
        this.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';
    }

    /**
     * Call GraphQL API
     */
    async callGraphQL(query) {
        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': this.userAgent,
                    'Accept': '*/*',
                    'Origin': 'https://cellphones.com.vn',
                    'Referer': 'https://cellphones.com.vn/'
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (!response.ok) {
                console.error('API Response:', JSON.stringify(data, null, 2));
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            if (data.errors) {
                throw new Error(`GraphQL Error: ${JSON.stringify(data.errors)}`);
            }

            return data;
        } catch (error) {
            console.error('❌ Lỗi khi call API:', error.message);
            throw error;
        }
    }

    /**
     * Tìm kiếm sản phẩm theo keyword
     */
    async searchProducts(keyword, page = 1) {
        console.log(`🔍 Tìm kiếm: "${keyword}" - Trang ${page}`);

        // GraphQL query - chỉ lấy fields cơ bản có sẵn trong API schema
        const query = `query advanced_search { advanced_search(user_query: { terms: "${keyword}", province: ${this.province} }, page: ${page}) { products { product_id name sku price special_price thumbnail url_path } meta { total page } } }`;

        const result = await this.callGraphQL(query);

        if (!result.data || !result.data.advanced_search) {
            throw new Error('Invalid API response structure');
        }

        return result.data.advanced_search;
    }

    /**
     * Crawl tất cả sản phẩm theo keyword với pagination
     */
    async crawlAllProducts(keyword, options = {}) {
        const maxPages = options.maxPages || Infinity;
        const allProducts = [];
        let page = 1;
        let hasMore = true;

        console.log(`\n📦 Bắt đầu crawl: "${keyword}"`);
        console.log(`⚙️  Max pages: ${maxPages === Infinity ? 'Unlimited' : maxPages}`);
        console.log(`⏱️  Delay: ${this.delayMs}ms\n`);

        while (hasMore && page <= maxPages) {
            try {
                const result = await this.searchProducts(keyword, page);
                const products = result.products || [];
                const meta = result.meta || {};

                if (products.length === 0) {
                    console.log(`⚠️  Trang ${page}: Không có sản phẩm`);
                    break;
                }

                // Transform data using parser logic
                const transformedProducts = products.map(p =>
                    transformCellphonesData(p, keyword)
                );

                allProducts.push(...transformedProducts);

                console.log(`✅ Trang ${page}: ${products.length} sản phẩm (Tổng: ${meta.total || 'N/A'})`);

                // Check if có thêm trang
                const itemsPerPage = 20; // Default của API
                const totalItems = meta.total || 0;
                hasMore = page * itemsPerPage < totalItems;

                // Delay trước khi request tiếp
                if (hasMore && page < maxPages) {
                    await delay(this.delayMs);
                }

                page++;
            } catch (error) {
                console.error(`❌ Lỗi trang ${page}:`, error.message);
                // Continue hoặc break tùy theo error
                break;
            }
        }

        console.log(`\n📊 Tổng kết: ${allProducts.length} sản phẩm đã crawl`);
        return allProducts;
    }

    /**
     * Crawl nhiều keywords
     */
    async crawlMultipleKeywords(keywords, options = {}) {
        const results = {};

        for (const keyword of keywords) {
            try {
                const products = await this.crawlAllProducts(keyword, options);
                results[keyword] = products;

                // Delay giữa các keywords
                if (keywords.indexOf(keyword) < keywords.length - 1) {
                    console.log(`\n⏳ Chờ ${this.delayMs}ms trước khi crawl keyword tiếp theo...\n`);
                    await delay(this.delayMs);
                }
            } catch (error) {
                console.error(`❌ Lỗi khi crawl keyword "${keyword}":`, error.message);
                results[keyword] = [];
            }
        }

        return results;
    }
}

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
