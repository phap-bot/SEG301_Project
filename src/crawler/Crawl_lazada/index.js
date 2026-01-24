const TikiCrawler = require('./src/crawlers/tiki');
const LazadaCrawler = require('./src/crawlers/lazada');
const { testConnection } = require('./src/utils/db');
require('dotenv').config();

async function main() {
  const fs = require('fs');
  const path = require('path');

  console.log('🔌 Kiểm tra kết nối database...\n');
  const dbOk = await testConnection();

  if (!dbOk) {
    console.error('❌ Không kết nối được database!');
    process.exit(1);
  }

  // ===== ĐỌC CONFIG =====
  let config;
  try {
    const configPath = path.join(__dirname, 'config.json');
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    console.log('✅ Đọc config thành công!\n');
  } catch (error) {
    console.error('❌ Không đọc được file config.json:', error.message);
    process.exit(1);
  }

  // ===== ĐỌC/TẠO PROGRESS VÀ SYNC VỚI CONFIG =====
  const progressPath = path.join(__dirname, 'progress.json');
  let progress;

  try {
    progress = JSON.parse(fs.readFileSync(progressPath, 'utf8'));
    console.log('✅ Đọc progress thành công!\n');

    // ===== AUTO-SYNC: Merge config keywords vào progress =====
    const configKeywords = config.keywords;
    const progressKeywords = progress.keywords || [];

    // Tìm keywords mới trong config (chưa có trong progress)
    const newKeywords = configKeywords.filter(
      configKw => !progressKeywords.some(progKw => progKw.term === configKw)
    );

    // Lọc keywords còn trong config (xóa những keyword không còn trong config)
    const validKeywords = progressKeywords.filter(
      progKw => configKeywords.includes(progKw.term)
    );

    // Thêm keywords mới vào cuối danh sách
    newKeywords.forEach(kw => {
      validKeywords.push({
        term: kw,
        status: 'pending',
        completedAt: null
      });
    });

    // Cập nhật progress nếu có thay đổi
    if (newKeywords.length > 0 || validKeywords.length !== progressKeywords.length) {
      progress.keywords = validKeywords;
      fs.writeFileSync(progressPath, JSON.stringify(progress, null, 2));

      if (newKeywords.length > 0) {
        console.log(`➕ Đã thêm ${newKeywords.length} keyword mới: ${newKeywords.join(', ')}`);
      }
      if (validKeywords.length < progressKeywords.length) {
        console.log(`➖ Đã xóa ${progressKeywords.length - validKeywords.length} keyword không còn trong config`);
      }
      console.log('💾 Đã đồng bộ progress với config\n');
    }

  } catch (error) {
    // Tạo progress mới từ config
    console.log('📝 Tạo progress mới từ config...\n');
    progress = {
      keywords: config.keywords.map(k => ({
        term: k,
        status: 'pending',
        completedAt: null
      }))
    };
    fs.writeFileSync(progressPath, JSON.stringify(progress, null, 2));
  }

  // ===== TÌM KEYWORD TIẾP THEO =====
  const nextTask = progress.keywords.find(k => k.status === 'pending');

  if (!nextTask) {
    console.log('✅ ĐÃ HOÀN THÀNH TẤT CẢ KEYWORDS!');
    console.log('💡 Để chạy lại, dùng: node reset_progress.js\n');
    process.exit(0);
  }

  const currentIndex = progress.keywords.indexOf(nextTask);
  const keyword = nextTask.term;

  console.log(`${'='.repeat(60)}`);
  console.log(`🔍 [${currentIndex + 1}/${progress.keywords.length}] Từ khóa: "${keyword}"`);
  console.log(`${'='.repeat(60)}\n`);

  // ===== KHỞI TẠO CRAWLER =====
  let crawler;
  if (config.platform === '2') {
    crawler = new LazadaCrawler();
    console.log('🛒 Sàn: Lazada');
  } else {
    crawler = new TikiCrawler();
    console.log('🛒 Sàn: Tiki');
  }

  await crawler.init();
  console.log(`📄 Max pages: ${config.maxPages}\n`);

  // ===== TẠO URL =====
  const encoded = encodeURIComponent(keyword);
  let categoryUrl;
  if (config.platform === '2') {
    categoryUrl = `https://www.lazada.vn/catalog/?q=${encoded}`;
  } else {
    categoryUrl = `https://tiki.vn/search?q=${encoded}`;
  }

  // ===== CRAWL KEYWORD NÀY =====
  let keywordTotalNew = 0;

  for (let page = 1; page <= config.maxPages; page++) {
    const result = await crawler.crawlListingPage(categoryUrl, keyword, page);

    // ⭐ Handle browser restart after CAPTCHA
    if (result.needsRestart) {
      console.log('🔄 Browser đã restart. Thử lại trang này...\n');
      // Retry current page with new headless browser
      const retryResult = await crawler.crawlListingPage(categoryUrl, keyword, page);
      keywordTotalNew += retryResult.new;

      // Check if retry succeeded
      if (retryResult.total === 0) {
        console.log(`\n⚠️ Trang ${page} không còn sản phẩm. Dừng crawl keyword này!`);
        break;
      }
    } else {
      keywordTotalNew += result.new;

      // Auto-stop nếu không còn sản phẩm
      if (result.total === 0) {
        console.log(`\n⚠️ Trang ${page} không còn sản phẩm. Dừng crawl keyword này!`);
        break;
      }
    }

    // Delay giữa các trang
    if (page < config.maxPages) {
      console.log('⏳ Đợi 5 giây...\n');
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }

  await crawler.close();

  console.log(`\n✅ Hoàn thành "${keyword}": ${keywordTotalNew} sản phẩm mới\n`);

  // ===== CẬP NHẬT PROGRESS =====
  nextTask.status = 'completed';
  nextTask.completedAt = new Date().toISOString();
  fs.writeFileSync(progressPath, JSON.stringify(progress, null, 2));
  console.log('💾 Đã lưu progress\n');

  // ===== KIỂM TRA CÒN KEYWORD NÀO KHÔNG =====
  const remaining = progress.keywords.filter(k => k.status === 'pending').length;

  if (remaining > 0) {
    // Random delay 1-3 phút
    const delayMinutes = Math.floor(Math.random() * 3) + 1;
    const delayMs = delayMinutes * 60 * 1000;

    console.log(`📊 Còn ${remaining} keyword chưa crawl`);
    console.log(`⏳ Đợi ${delayMinutes} phút trước khi restart...\n`);

    await new Promise(resolve => setTimeout(resolve, delayMs));

    console.log('🔄 Tắt process để restart...\n');
    process.exit(0);
  } else {
    console.log('🎉 ĐÃ HOÀN THÀNH TẤT CẢ KEYWORDS!\n');
    process.exit(0);
  }
}

main();