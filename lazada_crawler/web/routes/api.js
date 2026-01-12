const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');
const db = require('../../src/utils/db');

module.exports = (emitLog) => {

    // GET /api/stats - Database statistics
    router.get('/stats', async (req, res) => {
        try {
            // Use Supabase client to get product count
            const { createClient } = require('@supabase/supabase-js');
            const supabase = createClient(
                process.env.SUPABASE_URL,
                process.env.SUPABASE_KEY
            );

            const { count, error } = await supabase
                .from('products')
                .select('*', { count: 'exact', head: true });

            if (error) {
                throw new Error(`Database error: ${error.message}`);
            }

            const configPath = path.join(__dirname, '../../config.json');
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

            res.json({
                totalProducts: count || 0,
                lastUpdated: new Date().toISOString(),
                platform: config.platform === '2' ? 'Lazada' : 'Tiki'
            });
        } catch (error) {
            console.error('API /stats error:', error);
            res.status(500).json({ error: error.message });
        }
    });

    // GET /api/config - Get current config
    router.get('/config', (req, res) => {
        try {
            const configPath = path.join(__dirname, '../../config.json');
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            res.json(config);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // POST /api/config - Update full config
    router.post('/config', (req, res) => {
        try {
            const { maxPages, platform, keywords } = req.body;

            const configPath = path.join(__dirname, '../../config.json');
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

            // Update fields if provided
            if (maxPages !== undefined) config.maxPages = parseInt(maxPages);
            if (platform !== undefined) config.platform = platform;
            if (keywords !== undefined) config.keywords = keywords;

            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

            emitLog('success', '💾 Settings saved');

            res.json({
                success: true,
                message: 'Config updated successfully'
            });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // POST /api/keywords - Update keywords
    router.post('/keywords', (req, res) => {
        try {
            const { keywords } = req.body;

            if (!Array.isArray(keywords)) {
                return res.status(400).json({ error: 'Keywords must be an array' });
            }

            const configPath = path.join(__dirname, '../../config.json');
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

            config.keywords = keywords;
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

            emitLog('success', `✅ Updated ${keywords.length} keywords`);

            res.json({
                success: true,
                message: `Updated ${keywords.length} keywords`
            });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /api/progress - Get crawl progress
    router.get('/progress', (req, res) => {
        try {
            const progressPath = path.join(__dirname, '../../progress.json');

            if (!fs.existsSync(progressPath)) {
                return res.json({ keywords: [] });
            }

            const progress = JSON.parse(fs.readFileSync(progressPath, 'utf8'));
            res.json(progress);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /api/plan - Generate crawl plan
    router.get('/plan', (req, res) => {
        try {
            const configPath = path.join(__dirname, '../../config.json');
            const progressPath = path.join(__dirname, '../../progress.json');

            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            let progress = { keywords: [] };

            if (fs.existsSync(progressPath)) {
                progress = JSON.parse(fs.readFileSync(progressPath, 'utf8'));
            }

            const keywordPlans = config.keywords.map(kw => {
                const progressItem = progress.keywords.find(p => p.term === kw);
                const estimatedProductsPerPage = 40;
                const estimatedProducts = config.maxPages * estimatedProductsPerPage;
                const estimatedTimeMinutes = Math.round(config.maxPages * 1.5); // ~1.5 min/page avg

                return {
                    term: kw,
                    status: progressItem ? progressItem.status : 'pending',
                    estimatedProducts,
                    estimatedTime: `${estimatedTimeMinutes} min`,
                    estimatedTimeMinutes, // Keep numeric value for calculation
                    maxPages: config.maxPages
                };
            });

            const totalProducts = keywordPlans.reduce((sum, kw) => sum + kw.estimatedProducts, 0);
            const totalMinutes = keywordPlans.reduce((sum, kw) => sum + kw.estimatedTimeMinutes, 0);
            const totalHours = (totalMinutes / 60).toFixed(1);

            res.json({
                keywords: keywordPlans,
                totalKeywords: keywordPlans.length,
                totalEstimatedProducts: totalProducts,
                totalEstimatedTime: `${totalHours} hours`
            });
        } catch (error) {
            console.error('API /plan error:', error);
            res.status(500).json({ error: error.message });
        }
    });

    // POST /api/cookies/clear - Delete cookies file
    router.post('/cookies/clear', (req, res) => {
        try {
            const cookiesPath = path.join(__dirname, '../../.cookies/lazada_cookies.json');

            if (fs.existsSync(cookiesPath)) {
                fs.unlinkSync(cookiesPath);
                emitLog('info', '🗑️ Cookies deleted - browser will run in visible mode on next crawl');
                res.json({
                    success: true,
                    message: 'Cookies cleared successfully. Next crawl will require CAPTCHA solving.'
                });
            } else {
                res.json({
                    success: true,
                    message: 'No cookies file found'
                });
            }
        } catch (error) {
            console.error('API /cookies/clear error:', error);
            res.status(500).json({ error: error.message });
        }
    });

    return router;
};
