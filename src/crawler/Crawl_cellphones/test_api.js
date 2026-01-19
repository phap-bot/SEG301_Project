import CellphonesCrawler from './src/crawlers/cellphones_api.js';

/**
 * Test Script - Verify API Connection
 */
async function test() {
    console.log('🧪 Testing CellphoneS GraphQL API...\n');

    const crawler = new CellphonesCrawler({
        province: 30,
        delayMs: 500
    });

    try {
        // Test 1: Search for a single keyword, single page
        console.log('Test 1: Tìm kiếm "iphone" - Trang 1');
        const result = await crawler.searchProducts('iphone', 1);

        console.log(`✅ API Response:`);
        console.log(`   - Tổng sản phẩm: ${result.meta.total}`);
        console.log(`   - Sản phẩm trên trang này: ${result.products.length}`);
        console.log(`   - Trang hiện tại: ${result.meta.page}`);

        if (result.products.length > 0) {
            console.log(`\n📱 Sản phẩm đầu tiên:`);
            const first = result.products[0];
            console.log(`   - Name: ${first.name}`);
            console.log(`   - Price: ${first.special_price || first.price}`);
            console.log(`   - Original: ${first.price}`);
            console.log(`   - Discount: ${first.discount_percent}%`);
            console.log(`   - URL: https://cellphones.com.vn/${first.url_path}.html`);
        }

        console.log('\n✅ Test passed! API hoạt động tốt.\n');

    } catch (error) {
        console.error('\n❌ Test failed:', error.message);
        process.exit(1);
    }
}

test();
