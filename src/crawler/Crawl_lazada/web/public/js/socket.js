// Socket.IO client initialization
const socket = io();

// Listen for logs from server
socket.on('log', (data) => {
    appendLog(data.level, `[${data.timestamp}] ${data.message}`);
});

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});
