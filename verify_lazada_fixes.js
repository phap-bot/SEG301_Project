require('dotenv').config();
const path = require('path');

// Mock DB module
const dbPath = path.resolve('./src/utils/db.js');
require.cache[dbPath] = {
    id: dbPath,
    filename: dbPath,
    loaded: true,
    exports: {
        productExists: async () => false,
        upsertProduct: async (data) => {
            // Log results to check fixes
            if (!data.price) console.warn('⚠️ No price');
            if (data.image_url.startsWith('data:')) console.warn('⚠️ Base64 image');
            if (data.category === data.product_name) console.warn('⚠️ Category equals Name');

            console.log(`  [MOCK DB] Upsert: ${data.product_name.substring(0, 20)}... | Price: ${data.price} | Cat: ${data.category} | Img: ${data.image_url.substring(0, 15)}...`);
            return 1;
        },
        testConnection: async () => true
    }
};

const LazadaCrawler = require('./src/crawlers/lazada');

(async () => {
    console.log('--- TESTING LAZADA FIXES ---');
    const crawler = new LazadaCrawler();
    await crawler.init();
    // Test a specific category that usually has breadcrumbs
    const url = 'https://www.lazada.vn/shop-mobiles-tablets';
    try {
        await crawler.crawlListingPage(url, 'Test Cat', 1);
    } catch (e) {
        console.error(e);
    }
    await crawler.close();
})();
