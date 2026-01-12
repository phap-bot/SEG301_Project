const express = require('express');
const http = require('http');
const socketIO = require('socket.io');
const path = require('path');
const cors = require('cors');
const { spawn } = require('child_process');
const fs = require('fs');

// Load .env from parent directory (since server runs from web/ folder)
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const app = express();
const server = http.createServer(app);
const io = socketIO(server);

const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Global state
let crawlerProcess = null;
let crawlerLogs = [];

// Socket.IO connection
io.on('connection', (socket) => {
    console.log('✅ Client connected');

    // Send existing logs to new client
    crawlerLogs.forEach(log => socket.emit('log', log));

    socket.on('disconnect', () => {
        console.log('❌ Client disconnected');
    });
});

// Helper: Emit log to all clients
function emitLog(level, message) {
    const logEntry = {
        timestamp: new Date().toLocaleTimeString('vi-VN'),
        level,
        message
    };
    crawlerLogs.push(logEntry);

    // Keep only last 100 logs
    if (crawlerLogs.length > 100) {
        crawlerLogs = crawlerLogs.slice(-100);
    }

    io.emit('log', logEntry);
}

// API Routes
const apiRouter = require('./routes/api')(emitLog);
const crawlerRouter = require('./routes/crawler')(emitLog, () => crawlerProcess, (proc) => { crawlerProcess = proc; });

app.use('/api', apiRouter);
app.use('/api/crawler', crawlerRouter);

// Start server
server.listen(PORT, () => {
    console.log(`🚀 Server running at http://localhost:${PORT}`);
    console.log(`📊 Dashboard: http://localhost:${PORT}`);
    emitLog('info', '🚀 Web server started');
});
