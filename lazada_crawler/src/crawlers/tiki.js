const { chromium } = require('playwright');
const { upsertProduct, productExists } = require('../utils/db');
const {
  randomDelay,
  extractTikiProductId,
  parsePrice,
  calculateDiscount,
  parseRating,
  parseReviewCount
} = require('../utils/helpers');

class TikiCrawler {
  constructor() {
    this.platform = 'tiki';
    this.browser = null;
  }

  async init() {
    console.log('🌐 Đang mở trình duyệt (Chromium ảo, headless)...');
    // Browser ảo, không dùng Chrome thật của bạn
    this.browser = await chromium.launch({
      headless: true
    });
  }

  async crawlListingPage(categoryUrl, categoryName, page = 1) {
    const pageUrl = `${categoryUrl}?page=${page}`;
    console.log(`\n📄 Đang crawl trang ${page}: ${categoryUrl}`);

    // Mỗi lượt crawl dùng một context mới => cookie/session sạch
    const context = await this.browser.newContext({
      locale: 'vi-VN',
      timezoneId: 'Asia/Ho_Chi_Minh'
    });
    const browserPage = await context.newPage();

    try {
      await browserPage.goto(pageUrl, { timeout: 60000 });
      await browserPage.waitForTimeout(5000);

      // Scroll nhiều lần để load thêm sản phẩm (lazy load)
      for (let i = 0; i < 5; i++) {
        await browserPage.evaluate(() => {
          window.scrollTo(0, document.body.scrollHeight);
        });
        await browserPage.waitForTimeout(1500);
      }

      const products = await browserPage.evaluate(() => {
        // Selector rộng hơn cho item sản phẩm trên Tiki - Bỏ href$=".html" để bắt được cả link có query params
        const items = document.querySelectorAll(
          'a[href*="-p"][href*=".html"]'
        );

        return Array.from(items).map(item => {
          // Tên sản phẩm
          const nameEl = item.querySelector('[class*="name"], [class*="title"], h3, div[class*="product"]');

          // --- Xử lý GIÁ (tìm element chứa '₫') ---
          let price = null;
          let original_price = null;
          let discount_percent = null;

          // Lấy tất cả các thẻ con có chứa text
          const allTextEls = Array.from(item.querySelectorAll('*')).filter(el =>
            el.children.length === 0 && el.textContent.trim().length > 0
          );

          for (const el of allTextEls) {
            const text = el.textContent.trim();
            // Tìm số tiền (có thể có hoặc không có '₫', nhưng thường là format số)
            if (text.includes('₫') || text.match(/[\d\.]+\s*₫?$/)) {
              // Nếu text chứa '-' và '%', đó là discount
              if (text.includes('-') && text.includes('%')) {
                discount_percent = parseInt(text.replace(/[^\d]/g, ''), 10);
              }
              // Nếu element cha hoặc chính nó có class gạch chân/strike -> giá gốc
              else if (
                getComputedStyle(el).textDecorationLine === 'line-through' ||
                el.className.includes('original') ||
                el.parentNode.className.includes('original')
              ) {
                original_price = text;
              }
              // Ngược lại, nếu chưa có giá và nhìn giống tiền thì lấy làm giá bán
              else if (!price && (text.includes('₫') || text.length > 3)) {
                price = text;
              }
            }
          }

          // Fallback nếu không tìm thấy theo logic trên
          if (!price) {
            const priceEl = item.querySelector('[class*="price"]:not([class*="original"])');
            price = priceEl?.innerText || '';
          }

          // --- Xử lý ẢNH (srcset, data-src) ---
          const imgEl = item.querySelector('img');
          let image = '';
          if (imgEl) {
            // Tiki thường dùng srcset cho ảnh retina, lấy ảnh to nhất (cuối cùng trong chuỗi)
            if (imgEl.srcset) {
              const sources = imgEl.srcset.split(',').map(s => s.trim().split(' ')[0]);
              image = sources[sources.length - 1];
            }
            else if (imgEl.dataset.src) {
              image = imgEl.dataset.src;
            }
            else {
              image = imgEl.src;
            }
          }

          // --- Xử lý RATING ---
          let rating = '';
          const ratingEl = item.querySelector('[class*="rating"], [class*="star"]');
          if (ratingEl) {
            // Thử lấy style width (vd: width: 80% -> 4 sao)
            const style = ratingEl.getAttribute('style');
            if (style && style.includes('width')) {
              const widthMatch = style.match(/width:\s*(\d+)%/);
              if (widthMatch) {
                rating = (parseInt(widthMatch[1], 10) / 20).toString();
              }
            }
            if (!rating) rating = ratingEl.innerText;
          }
          // Fallback text (vd: "4.5") nó thường nằm cạnh sao
          if (!rating) {
            const ratingTextEl = item.querySelector('[class*="average"]');
            if (ratingTextEl) rating = ratingTextEl.textContent;
          }

          // Review count
          const reviewEl = item.querySelector('[class*="review"], [class*="quantity"]');

          // --- Xử lý TÊN ---
          let name = nameEl?.innerText?.trim() || nameEl?.textContent?.trim();
          if (!name && item.href) {
            const slugMatch = item.href.match(/\/([^\/]+)-p\d+\.html/);
            if (slugMatch && slugMatch[1]) {
              name = decodeURIComponent(slugMatch[1].replace(/-/g, ' '));
            } else {
              name = item.title || item.href;
            }
          }

          return {
            name,
            price: price || '',
            original_price: original_price || '',
            discount_percent,
            rating: rating || '',
            review_count: reviewEl?.innerText?.trim() || '',
            url: item.href,
            image: image || ''
          };
        }).filter(p => p.url && p.url.includes('tiki.vn') && p.image && p.image.startsWith('http'));
      });

      console.log(`✅ Tìm thấy ${products.length} sản phẩm`);

      let newCount = 0;

      for (const product of products) {
        const productId = extractTikiProductId(product.url);
        if (!productId) continue;

        const exists = await productExists(this.platform, productId);

        if (!exists) {
          await upsertProduct({
            platform: this.platform,
            site_product_id: productId,
            product_name: product.name,
            price: parsePrice(product.price),
            original_price: parsePrice(product.original_price),
            discount_percent: calculateDiscount(
              parsePrice(product.original_price),
              parsePrice(product.price)
            ),
            product_url: product.url,
            image_url: product.image,
            rating: parseRating(product.rating),
            review_count: parseReviewCount(product.review_count),
            location: 'Việt Nam',
            category: categoryName
          });

          newCount++;
          console.log(`  ✅ Lưu: ${product.name.substring(0, 50)}...`);
        }

        await browserPage.waitForTimeout(randomDelay(300, 800));
      }

      console.log(`📊 Trang ${page}: ${newCount} sản phẩm mới`);

      return { total: products.length, new: newCount };

    } catch (error) {
      console.error(`❌ Lỗi trang ${page}:`, error.message);
      return { total: 0, new: 0 };
    } finally {
      await browserPage.close();
      await context.close();
    }
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

module.exports = TikiCrawler;