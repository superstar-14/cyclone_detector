#!/usr/bin/env bash
# ============================================================
# Render Build Script for IMD Cyclone Detector
# Builds React frontend and installs lean Python backend
# ============================================================
set -o errexit

echo "============================================================"
echo "🌀 Building IMD Cyclone Detector for Render"
echo "============================================================"

# 1. Build React Frontend SPA
echo "--> Step 1/2: Building Frontend assets..."
cd frontend
npm ci --prefer-offline || npm install
npm run build
cd ..

# 2. Install Lean Python Backend Dependencies
echo "--> Step 2/2: Installing Backend requirements (<512MB RAM safe)..."
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo "============================================================"
echo "✅ Build complete! Ready to start."
echo "============================================================"
