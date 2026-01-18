const fs = require('fs');
const path = require('path');

console.log('🔄 Đang reset progress...\n');

try {
    // Đọc config
    const configPath = path.join(__dirname, 'config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

    // Tạo progress mới
    const progress = {
        keywords: config.keywords.map(k => ({
            term: k,
            status: 'pending',
            completedAt: null
        }))
    };

    // Ghi file
    const progressPath = path.join(__dirname, 'progress.json');
    fs.writeFileSync(progressPath, JSON.stringify(progress, null, 2));

    console.log('✅ Progress đã được reset!');
    console.log(`📋 Tổng số keywords: ${progress.keywords.length}\n`);

    progress.keywords.forEach((k, i) => {
        console.log(`  ${i + 1}. "${k.term}" - ${k.status}`);
    });

    console.log('\n💡 Chạy "node index.js" hoặc "run_crawler.bat" để bắt đầu!\n');
} catch (error) {
    console.error('❌ Lỗi:', error.message);
    process.exit(1);
}
