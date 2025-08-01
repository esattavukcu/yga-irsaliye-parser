#!/bin/bash

echo "🚀 YGA İrsaliye Parser'ı GitHub'a yükleme scripti"
echo "================================================"

# Mevcut durum kontrolü
echo "📁 Mevcut dosyalar:"
ls -la

echo ""
echo "📊 Git durumu:"
git status

echo ""
echo "🔗 Remote repository ekle:"
git remote add origin https://github.com/esattavukcu/yga-irsaliye-parser.git 2>/dev/null || echo "Remote origin zaten mevcut"

echo ""
echo "🌿 Ana branch'i main olarak ayarla:"
git branch -M main

echo ""
echo "⬆️  GitHub'a yükle:"
echo "Şu komutu çalıştır:"
echo "git push -u origin main"

echo ""
echo "🎯 Upload tamamlandıktan sonra deploy seçenekleri:"
echo ""
echo "1️⃣  RAILWAY (ÖNERİLEN - EN KOLAY):"
echo "   → https://railway.app/ git"
echo "   → 'Deploy from GitHub repo' seç"
echo "   → 'esattavukcu/yga-irsaliye-parser' seç"
echo "   → Otomatik deploy başlar!"
echo ""
echo "2️⃣  RENDER (ÜCRETSİZ PLAN):"
echo "   → https://render.com/ git"
echo "   → 'New Web Service' seç" 
echo "   → GitHub repo bağla"
echo "   → Build Command: pip install -r requirements.txt"
echo "   → Start Command: gunicorn app:app"
echo ""
echo "3️⃣  HEROKU:"
echo "   → heroku create yga-irsaliye-parser"
echo "   → git push heroku main"
echo ""
echo "✨ Repository hazır: https://github.com/esattavukcu/yga-irsaliye-parser"