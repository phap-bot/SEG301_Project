import fetch from 'node-fetch';
import { transformCellphonesData, delay } from '../utils/helpers.js';

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

                // Transform data
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

export default CellphonesCrawler;
