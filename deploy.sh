#!/bin/bash

echo "🚀 Deploying PickProphet to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

# Check if we're logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run:"
    echo "railway login"
    exit 1
fi

echo "✅ Railway CLI ready"

# Test dependencies first
echo "🧪 Testing dependencies..."
python3 test_dependencies.py
if [ $? -ne 0 ]; then
    echo "❌ Dependency test failed. Please fix the issues before deploying."
    exit 1
fi

# Test the application locally first
echo "🧪 Testing application locally..."
python3 fantasy_draft_web_enhanced.py &
APP_PID=$!

# Wait for app to start
sleep 5

# Test health check
HEALTH_RESPONSE=$(curl -s http://localhost:6007/health)
if [[ $HEALTH_RESPONSE == *"PickProphet is running"* ]]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    kill $APP_PID
    exit 1
fi

# Kill local app
kill $APP_PID

echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo "🌐 Your app should be available at: https://your-app-name.railway.app"
echo "📊 Monitor your app at: https://railway.app/dashboard" 