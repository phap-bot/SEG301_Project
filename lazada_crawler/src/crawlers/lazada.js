const { chromium } = require('playwright-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

// Apply stealth plugin to chromium
chromium.use(StealthPlugin());

const { upsertProduct, productExists } = require('../utils/db');
const {
  randomDelay,
  parsePrice,
  calculateDiscount,
  parseRating,
  parseReviewCount,
  extractLazadaProductId
} = require('../utils/helpers');

class LazadaCrawler {
  constructor() {
    this.platform = 'lazada';
    this.browser = null;
    this.cookiesPath = path.join(__dirname, '../../.cookies/lazada_cookies.json');
  }

  async saveCookies(context) {
    try {
      const cookies = await context.cookies();
      const dir = path.dirname(this.cookiesPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(this.cookiesPath, JSON.stringify(cookies, null, 2));
      console.log('💾 Đã lưu cookies vào file');
    } catch (error) {
      console.error('⚠️  Lỗi khi lưu cookies:', error.message);
    }
  }

  async loadCookies(context) {
    try {
      if (fs.existsSync(this.cookiesPath)) {
        const cookies = JSON.parse(fs.readFileSync(this.cookiesPath, 'utf8'));
        await context.addCookies(cookies);
        console.log('✅ Đã load cookies từ file');
        return true;
      }
    } catch (error) {
      console.error('⚠️  Lỗi khi load cookies:', error.message);
    }
    return false;
  }

  getRandomUserAgent() {
    const userAgents = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ];
    return userAgents[Math.floor(Math.random() * userAgents.length)];
  }

  async init() {
    // Auto-detect: Nếu có cookies → headless, nếu chưa → visible để giải CAPTCHA
    const hasCookies = fs.existsSync(this.cookiesPath);
    const headlessMode = hasCookies;

    if (hasCookies) {
      console.log('🌐 Đang mở trình duyệt (Lazada - Headless Mode với cookies)...');
    } else {
      console.log('🌐 Đang mở trình duyệt (Lazada - Visible Mode - Cần giải CAPTCHA)...');
    }

    this.browser = await chromium.launch({
      headless: headlessMode,
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-features=IsolateOrigins,site-per-process',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--start-maximized'
      ]
    });
  }

  async crawlListingPage(categoryUrl, categoryName, page = 1) {
    const pageUrl = `${categoryUrl}?page=${page}`;
    console.log(`\n📄 [Lazada] Đang crawl trang ${page}: ${pageUrl}`);

    // Random viewport for more realistic behavior
    const viewportWidth = 1366 + Math.floor(Math.random() * 200);
    const viewportHeight = 768 + Math.floor(Math.random() * 200);

    const context = await this.browser.newContext({
      userAgent: this.getRandomUserAgent(),
      viewport: { width: viewportWidth, height: viewportHeight },
      deviceScaleFactor: 1,
      maskColor: null,
      locale: 'vi-VN',
      timezoneId: 'Asia/Ho_Chi_Minh',
      hasTouch: false,
      isMobile: false,
      permissions: ['geolocation']
    });

    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
      });
    });

    // Load cookies if exist
    await this.loadCookies(context);

    const browserPage = await context.newPage();

    try {
      await browserPage.route('**/*analytics*', route => route.abort());
      await browserPage.goto(pageUrl, { timeout: 60000 });
      await browserPage.waitForTimeout(2000);

      // ⭐ CHECK: Detect CAPTCHA
      const currentUrl = browserPage.url();
      if (currentUrl.includes('punish') || currentUrl.includes('captcha')) {
        console.log('\n⚠️  ====================================');
        console.log('⚠️  PHÁT HIỆN CAPTCHA!');
        console.log('🔔 VUI LÒNG GIẢI CAPTCHA TRONG BROWSER');
        console.log('⏳ Đợi 90 giây để bạn giải CAPTCHA...');
        console.log('⚠️  ====================================\n');

        // Wait for user to solve CAPTCHA
        await browserPage.waitForTimeout(90000);

        // Check if CAPTCHA solved
        const newUrl = browserPage.url();
        if (!newUrl.includes('punish') && !newUrl.includes('captcha')) {
          console.log('✅ CAPTCHA ĐÃ ĐƯỢC GIẢI! Lưu cookies...');
          await this.saveCookies(context);

          // ⭐ RESTART BROWSER IN HEADLESS MODE
          console.log('🔄 Đóng browser visible...');
          await browserPage.close();
          await context.close();
          await this.browser.close();

          console.log('🌐 Mở lại browser ở chế độ HEADLESS (ẩn)...');
          this.browser = await chromium.launch({
            headless: true,
            args: [
              '--disable-blink-features=AutomationControlled',
              '--disable-features=IsolateOrigins,site-per-process',
              '--no-sandbox',
              '--disable-setuid-sandbox',
              '--disable-dev-shm-usage'
            ]
          });

          console.log('✅ Browser đã chuyển sang chế độ ẨN (headless)');
          console.log('✅ Từ giờ bạn sẽ không thấy browser nữa!\n');

          // Return special flag to indicate restart needed
          return { total: 0, new: 0, needsRestart: true };
        } else {
          console.log('❌ CAPTCHA CHƯA ĐƯỢC GIẢI hoặc hết thời gian.');
          console.log('⚠️  Skip keyword này. Vui lòng chạy lại.\n');
          return { total: 0, new: 0 };
        }
      }

      // Enhanced scroll with more randomization
      for (let i = 0; i < 5; i++) {
        await browserPage.evaluate(() => {
          const scrollAmount = Math.floor(window.innerHeight * (3 + Math.random() * 2));
          window.scrollBy(0, scrollAmount);
        });
        await browserPage.waitForTimeout(300 + Math.floor(Math.random() * 500));
      }

      const products = await browserPage.evaluate(() => {
        const items = document.querySelectorAll('div.Ms6aG.MefHh, div[data-qa-locator="product-item"], div[data-tracking="product-card"]');

        return Array.from(items).map(item => {
          const linkEl = item.querySelector('a[href*="-i"][href*=".html"], a[href*="pdp-i"]');

          const nameEl =
            item.querySelector('.RfADt a') ||
            item.querySelector('a[title]') ||
            item.querySelector('img[alt]');

          // ===== FIX: Tìm giá hiện tại =====
          const priceEl = item.querySelector('.ooOxS') ||
            item.querySelector('[class*="price"]:not([class*="origin"])');

          // ===== FIX: Tìm giá gốc - ƯU TIÊN thẻ <del> và style line-through =====
          let originalPriceText = '';

          // 1. Tìm thẻ <del>
          const delEl = item.querySelector('del');
          if (delEl) {
            const text = delEl.textContent.trim();
            if (text.includes('₫') && !text.includes('%') && !text.toLowerCase().includes('off')) {
              originalPriceText = text;
            }
          }

          // 2. Nếu chưa có, tìm element có style line-through
          if (!originalPriceText) {
            const allSpans = item.querySelectorAll('span, div');
            for (const span of allSpans) {
              const style = window.getComputedStyle(span);
              const text = span.textContent.trim();

              if (style.textDecorationLine === 'line-through' &&
                text.includes('₫') &&
                !text.includes('%') &&
                !text.toLowerCase().includes('off')) {
                originalPriceText = text;
                break;
              }
            }
          }

          // 3. Fallback: tìm class có chứa "origin" (KHÔNG dùng .IcOsH vì nó chứa % Off)
          if (!originalPriceText) {
            const originEl = item.querySelector('[class*="origin"]:not(.IcOsH)');
            if (originEl) {
              const text = originEl.textContent.trim();
              if (text.includes('₫') && !text.includes('%') && !text.toLowerCase().includes('off')) {
                originalPriceText = text;
              }
            }
          }

          // ===== FIX: Tìm % giảm giá từ .IcOsH hoặc .WNoq3 =====
          let discountText = '';

          // Tìm trong .IcOsH trước (vd: "28% Off")
          const icOsHEl = item.querySelector('.IcOsH');
          if (icOsHEl) {
            const text = icOsHEl.textContent.trim();
            if (text.includes('%')) {
              discountText = text;
            }
          }

          // Nếu chưa có, tìm trong .WNoq3 hoặc badge
          if (!discountText) {
            const discountEl = item.querySelector('.WNoq3') ||
              item.querySelector('.ic-dynamic-badge-text') ||
              item.querySelector('[class*="discount"]');
            if (discountEl) {
              const text = discountEl.textContent.trim();
              if (text.includes('%')) {
                discountText = text;
              }
            }
          }

          // ===== FIX: Rating - đếm số sao filled =====
          let rating = '';

          // Cách 1: Đếm icon sao filled (._9-ogB.Dy1nx)
          const starIcons = item.querySelectorAll('._9-ogB.Dy1nx');
          if (starIcons.length > 0) {
            rating = starIcons.length.toString();
          }

          // Cách 2: Fallback - tìm style width
          if (!rating) {
            const ratingEl = item.querySelector('[class*="rating"], [class*="star"]');
            if (ratingEl) {
              const style = ratingEl.getAttribute('style');
              if (style && style.includes('width')) {
                const widthMatch = style.match(/width:\s*(\d+)%/);
                if (widthMatch) {
                  rating = (parseInt(widthMatch[1], 10) / 20).toString();
                }
              }
              if (!rating) rating = ratingEl.innerText;
            }
          }

          // ===== FIX: Review count - lấy từ .qzqFw =====
          let reviewCount = '';
          const reviewEl = item.querySelector('.qzqFw');
          if (reviewEl) {
            reviewCount = reviewEl.textContent.trim();
          } else {
            // Fallback
            const reviewFallback = item.querySelector('[class*="rating__review"], [class*="review"]');
            if (reviewFallback) reviewCount = reviewFallback.textContent.trim();
          }

          // ===== FIX: Sold count - lấy từ ._1cEkb =====
          let soldCount = '';
          const soldEl = item.querySelector('._1cEkb span');
          if (soldEl) {
            const text = soldEl.textContent.trim();
            // Lấy số từ text "316 sold"
            const match = text.match(/(\d+)\s*sold/i);
            if (match) {
              soldCount = match[1];
            }
          }

          // Ảnh
          const imgEl = item.querySelector('img');
          const image = (() => {
            if (!imgEl) return '';
            const src = imgEl.getAttribute('src') || '';
            const dataSrc = imgEl.getAttribute('data-src') || imgEl.getAttribute('data-ks-lazyload') || '';
            let url = src && !src.startsWith('data:') ? src : dataSrc;
            if (!url) return '';
            if (url.startsWith('//')) url = 'https:' + url;
            return url;
          })();

          // Tên
          let name = nameEl?.innerText?.trim() || nameEl?.getAttribute?.('title') || nameEl?.alt;
          const href = linkEl?.href || linkEl?.getAttribute?.('href') || '';
          let fullUrl = href;
          if (href && !href.startsWith('http')) {
            fullUrl = 'https:' + href;
          }

          if (!name && fullUrl) {
            const slugMatch = fullUrl.match(/\/([^\/]+)-i\d+\.html/);
            if (slugMatch && slugMatch[1]) {
              name = decodeURIComponent(slugMatch[1].replace(/-/g, ' '));
            } else {
              name = fullUrl;
            }
          }

          return {
            name,
            price: priceEl?.innerText?.trim() || priceEl?.textContent?.trim(),
            original_price: originalPriceText,
            discount_text: discountText,
            rating: rating || '',
            review_count: reviewCount || '',
            sold_count: soldCount || '',
            url: fullUrl,
            image: (image && !image.startsWith('data:')) ? image : ''
          };
        }).filter(p => p.url && (p.url.includes('lazada.vn') || p.url.includes('pdp-i')) && p.image && p.image.startsWith('http'));
      });

      console.log(`✅ [Lazada] Tìm thấy ${products.length} sản phẩm`);

      let newCount = 0;
      const detailPage = await context.newPage();
      await detailPage.route('**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,ico}', route => route.abort());

      for (const product of products) {
        const productId = extractLazadaProductId(product.url);
        if (!productId) continue;

        // ===== SMART SKIP PDP LOGIC =====
        const hasPrice = product.price && parsePrice(product.price) > 0;
        const hasImage = product.image && product.image.startsWith('http');
        const hasRating = product.rating && parseFloat(product.rating) > 0;

        let shouldSkipPDP = false;
        let skipReason = '';

        // Case 1: Có đủ price + original_price + image + rating → SKIP
        if (hasPrice && product.original_price && hasImage && hasRating) {
          shouldSkipPDP = true;
          skipReason = 'đủ giá gốc & sale';
        }
        // Case 2: Có price + image + rating nhưng không có original_price → Không giảm giá
        else if (hasPrice && hasImage && hasRating && !product.original_price) {
          product.original_price = product.price;  // Set original = price
          shouldSkipPDP = true;
          skipReason = 'không giảm giá';
        }
        // Case 3: Có price + image (dù không có rating) → Có thể skip
        else if (hasPrice && product.original_price && hasImage) {
          shouldSkipPDP = true;
          skipReason = 'đủ data cơ bản';
        }

        // ===== FIX: Lấy giá từ PDP với selector mới hơn =====
        let priceText = product.price;
        let originalPriceText = product.original_price;
        let discountText = product.discount_text;

        if (shouldSkipPDP) {
          console.log(`  ⚡ Skip PDP (${skipReason}): ${product.name ? product.name.substring(0, 40) + '...' : productId}`);
        } else {
          console.log(`  🔍 Visit PDP (thiếu data): ${product.name ? product.name.substring(0, 40) + '...' : productId}`);

          try {
            await detailPage.goto(product.url, {
              timeout: 30000,
              waitUntil: 'domcontentloaded'
            });

            try {
              await detailPage.waitForSelector(
                '.pdp-price, [class*="price"]',
                { timeout: 3000 }
              );
            } catch {
              // Timeout OK, continue
            }

            await detailPage.waitForTimeout(200);

            const pdpPrices = await detailPage.evaluate(() => {
              // ===== FIX: Tìm giá bán (sale price) - MỚI NHẤT =====
              const findSalePrice = () => {
                // 1. Selector chính xác từ HTML thực tế
                const amountEl = document.querySelector('.pdp-v2-product-price-content-salePrice-amount');
                if (amountEl) {
                  return amountEl.textContent.trim();
                }

                // 2. Fallback: tìm parent div rồi lấy text
                const salePriceDiv = document.querySelector('.pdp-v2-product-price-content-salePrice');
                if (salePriceDiv) {
                  return salePriceDiv.textContent.trim();
                }

                // 3. Selector cũ (cho case Lazada đổi layout)
                const selectors = [
                  '.pdp-price_type_normal',
                  '.pdp-price_size_xl',
                  '.pdp-product-price__current-price'
                ];

                for (const sel of selectors) {
                  const el = document.querySelector(sel);
                  if (el && el.textContent.includes('₫')) {
                    return el.textContent.trim();
                  }
                }

                return '';
              };

              // ===== FIX: Tìm giá gốc (original price) - MỚI NHẤT =====
              const findOriginalPrice = () => {
                // 1. Selector chính xác từ HTML thực tế
                const amountEl = document.querySelector('.pdp-v2-product-price-content-originalPrice-amount');
                if (amountEl) {
                  return amountEl.textContent.trim();
                }

                // 2. Fallback: tìm parent div
                const originalPriceDiv = document.querySelector('.pdp-v2-product-price-content-originalPrice');
                if (originalPriceDiv) {
                  // Lấy chỉ phần amount, bỏ qua discount
                  const amount = originalPriceDiv.querySelector('span:first-child');
                  if (amount) return amount.textContent.trim();
                }

                // 3. Tìm thẻ <del>
                const delEls = document.querySelectorAll('del');
                for (const del of delEls) {
                  const text = del.textContent.trim();
                  if (text.includes('₫')) return text;
                }

                // 4. Tìm element có line-through
                const allEls = document.querySelectorAll('[class*="price"], span, div');
                for (const el of allEls) {
                  const style = window.getComputedStyle(el);
                  const text = el.textContent.trim();

                  if (style.textDecorationLine === 'line-through' && text.includes('₫')) {
                    return text;
                  }
                }

                // 5. Selector class cũ
                const selectors = [
                  '.pdp-price_type_deleted',
                  '.pdp-product-price__old-price'
                ];

                for (const sel of selectors) {
                  const el = document.querySelector(sel);
                  if (el && el.textContent.includes('₫')) {
                    return el.textContent.trim();
                  }
                }

                return '';
              };

              // ===== FIX: Tìm % giảm giá - MỚI NHẤT =====
              const findDiscount = () => {
                // 1. Selector chính xác từ HTML thực tế
                const discountEl = document.querySelector('.pdp-v2-product-price-content-originalPrice-discount');
                if (discountEl) {
                  return discountEl.textContent.trim();
                }

                // 2. Selector cũ
                const selectors = [
                  '.pdp-product-price__discount',
                  '[class*="discount"]'
                ];

                for (const sel of selectors) {
                  const el = document.querySelector(sel);
                  if (el) {
                    const text = el.textContent.trim();
                    if (text.includes('%')) return text;
                  }
                }

                return '';
              };

              const salePrice = findSalePrice();
              const originalPrice = findOriginalPrice();
              const discount = findDiscount();

              // Rating & review
              const ratingScore = document.querySelector('.container-star-v2-score') ||
                document.querySelector('.score-average');
              const ratingCount = document.querySelector('.container-star-v2-count') ||
                document.querySelector('.count');

              // Ảnh
              const mainImg = document.querySelector('.gallery-preview-panel-v2__image') ||
                document.querySelector('.item-gallery-v2-mini img') ||
                document.querySelector('.item-gallery-v2 img') ||
                document.querySelector('.pdp-mod-common-image') ||
                document.querySelector('img.pdp-mod-common-image');

              let imageUrl = mainImg?.getAttribute('src') || '';
              if (imageUrl.startsWith('data:')) imageUrl = '';
              if (imageUrl && imageUrl.startsWith('//')) {
                imageUrl = 'https:' + imageUrl;
              }

              // Category
              let categoryFromPdp = '';
              const breadcrumbs = document.querySelectorAll('.breadcrumb_item');
              if (breadcrumbs.length >= 2) {
                categoryFromPdp = breadcrumbs[breadcrumbs.length - 2].textContent.trim();
              }

              return {
                price: salePrice,
                original: originalPrice,
                discount: discount,
                rating: ratingScore?.textContent || '',
                review_count: ratingCount?.textContent || '',
                category: categoryFromPdp,
                image: imageUrl
              };
            });

            if (pdpPrices.price) priceText = pdpPrices.price;
            if (pdpPrices.original) originalPriceText = pdpPrices.original;
            if (pdpPrices.discount) discountText = pdpPrices.discount;

            if (pdpPrices.rating) product.rating = pdpPrices.rating;
            if (pdpPrices.review_count) product.review_count = pdpPrices.review_count;
            if (pdpPrices.category) product.categoryFromPdp = pdpPrices.category;
            if ((!product.image || product.image.startsWith('data:')) && pdpPrices.image) {
              product.image = pdpPrices.image;
            }
          } catch (err) {
            console.error(`⚠️ [Lazada] Lỗi lấy giá PDP cho ${product.url}:`, err.message);
          }
        } // ← End of PDP visit block

        // ===== FIX: Chuẩn hóa giá - TÍNH NGƯỢC giá gốc từ % nếu cần =====
        let price = parsePrice(priceText);
        let originalPrice = parsePrice(originalPriceText);

        // Tính % giảm giá từ discount text trước
        let discountPercent = 0;
        if (discountText) {
          const parsed = parseInt(discountText.replace(/[^\d]/g, ''), 10);
          if (!isNaN(parsed) && parsed > 0 && parsed <= 100) {
            discountPercent = parsed;
          }
        }

        // ===== LOGIC MỚI: Nếu không có giá gốc nhưng có % giảm, tính ngược =====
        if ((!originalPrice || originalPrice < price) && discountPercent > 0) {
          // Công thức: giá_hiện_tại = giá_gốc * (1 - %/100)
          // => giá_gốc = giá_hiện_tại / (1 - %/100)
          originalPrice = Math.round(price / (1 - discountPercent / 100));
          console.log(`  💡 [Lazada] Tính ngược giá gốc: ${price.toLocaleString()}₫ + ${discountPercent}% = ${originalPrice.toLocaleString()}₫`);
        }

        // Nếu vẫn không có giá gốc, set bằng giá hiện tại
        if (!originalPrice || originalPrice < price) {
          originalPrice = price;
        }

        // Tính lại % giảm từ 2 giá (ưu tiên hơn % từ text)
        const calculatedDiscount = calculateDiscount(originalPrice, price);
        if (calculatedDiscount > 0) {
          discountPercent = calculatedDiscount;
        }

        const exists = await productExists(this.platform, productId);

        if (!exists) {
          await upsertProduct({
            platform: this.platform,
            site_product_id: productId,
            product_name: product.name,
            price,
            original_price: originalPrice,
            discount_percent: discountPercent,
            product_url: product.url,
            image_url: product.image || '',
            rating: parseRating(product.rating),
            review_count: parseReviewCount(product.review_count),
            sold_count: parseReviewCount(product.sold_count), // Dùng parseReviewCount vì cùng format số
            location: 'Việt Nam',
            category: product.categoryFromPdp || categoryName
          });

          newCount++;
          if (product.name) {
            console.log(`  ✅ [Lazada] Lưu: ${product.name.substring(0, 50)}... | Giá: ${price.toLocaleString()}₫ | Gốc: ${originalPrice.toLocaleString()}₫ | Giảm: ${discountPercent}%`);
          } else {
            console.log(`  ✅ [Lazada] Lưu sản phẩm ID ${productId}`);
          }
        }

        await browserPage.waitForTimeout(randomDelay(300, 800));
      }

      console.log(`📊 [Lazada] Trang ${page}: ${newCount} sản phẩm mới`);

      // Save cookies after successful crawl
      await this.saveCookies(context);

      return { total: products.length, new: newCount };
    } catch (error) {
      console.error(`❌ [Lazada] Lỗi trang ${page}:`, error.message);
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

module.exports = LazadaCrawler;