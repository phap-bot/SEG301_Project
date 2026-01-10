#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           AUTO-RESTART CRAWLER - LINUX/MAC                 ║"
echo "║                                                            ║"
echo "║  Press Ctrl+C to stop the crawler                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

while true; do
  echo "════════════════════════════════════════════════════════════"
  echo "🚀 Starting crawler..."
  echo "════════════════════════════════════════════════════════════"
  echo ""
  
  node index.js
  EXIT_CODE=$?
  
  if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Crawler exited normally"
    echo "🔄 Auto-restarting in 3 seconds..."
    echo ""
    sleep 3
  else
    echo ""
    echo "❌ Crawler exited with error code: $EXIT_CODE"
    echo "🔄 Restarting in 5 seconds..."
    echo ""
    sleep 5
  fi
done
