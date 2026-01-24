const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');

module.exports = (emitLog, getCrawlerProcess, setCrawlerProcess) => {

    // POST /api/crawler/start - Start crawler
    router.post('/start', (req, res) => {
        const crawlerProcess = getCrawlerProcess();

        if (crawlerProcess && !crawlerProcess.killed) {
            return res.status(400).json({
                success: false,
                message: 'Crawler is already running'
            });
        }

        try {
            const crawlerPath = path.join(__dirname, '../../index.js');
            const proc = spawn('node', [crawlerPath], {
                cwd: path.join(__dirname, '../..'),
                detached: false
            });

            setCrawlerProcess(proc);

            proc.stdout.on('data', (data) => {
                const output = data.toString();
                output.split('\n').forEach(line => {
                    if (line.trim()) {
                        // Detect log level from output
                        let level = 'info';
                        if (line.includes('✅') || line.includes('Hoàn thành')) level = 'success';
                        if (line.includes('❌') || line.includes('Lỗi')) level = 'error';
                        if (line.includes('⚠️')) level = 'warning';

                        emitLog(level, line.trim());
                    }
                });
            });

            proc.stderr.on('data', (data) => {
                emitLog('error', data.toString().trim());
            });

            proc.on('exit', (code) => {
                emitLog('info', `🛑 Crawler stopped (Exit code: ${code})`);
                setCrawlerProcess(null);
            });

            emitLog('success', '▶️ Crawler started');

            res.json({
                success: true,
                pid: proc.pid,
                message: 'Crawler started successfully'
            });
        } catch (error) {
            emitLog('error', `❌ Failed to start crawler: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });

    // POST /api/crawler/stop - Stop crawler
    router.post('/stop', (req, res) => {
        const crawlerProcess = getCrawlerProcess();

        if (!crawlerProcess || crawlerProcess.killed) {
            return res.status(400).json({
                success: false,
                message: 'Crawler is not running'
            });
        }

        try {
            crawlerProcess.kill('SIGTERM');
            emitLog('warning', '⏹️ Stopping crawler...');

            setTimeout(() => {
                if (!crawlerProcess.killed) {
                    crawlerProcess.kill('SIGKILL');
                    emitLog('warning', '⏹️ Force killed crawler');
                }
            }, 5000);

            res.json({
                success: true,
                message: 'Crawler stopped'
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });

    // GET /api/crawler/status - Get crawler status
    router.get('/status', (req, res) => {
        const crawlerProcess = getCrawlerProcess();
        const isRunning = crawlerProcess && !crawlerProcess.killed;

        res.json({
            running: isRunning,
            pid: isRunning ? crawlerProcess.pid : null
        });
    });

    return router;
};
