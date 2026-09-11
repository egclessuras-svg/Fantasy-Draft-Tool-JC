# 🚀 PickProphet Deployment Guide

## Quick Deploy

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Run the deployment script**:
   ```bash
   ./deploy.sh
   ```

## Manual Deployment

If you prefer to deploy manually:

1. **Test dependencies**:
   ```bash
   python3 test_dependencies.py
   ```

2. **Deploy to Railway**:
   ```bash
   railway up
   ```

## Environment Variables

Make sure these environment variables are set in Railway:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `FLASK_SECRET_KEY`: A secure random string for Flask sessions

## Health Check

The app includes a comprehensive health check at `/health` that checks:
- ✅ App status
- ✅ Database connection
- ✅ Player projections loading

## Troubleshooting

### Network Check Failures

If Railway network checks are failing:

1. **Check the health endpoint**: Visit `https://your-app.railway.app/health`
2. **Check logs**: Use `railway logs` to see application logs
3. **Verify dependencies**: Run `python3 test_dependencies.py` locally

### Common Issues

- **Missing pandas**: The app now includes pandas in requirements.txt
- **Database connection**: The health check will show database status
- **App startup**: The initialization function provides detailed logging

## Monitoring

- **Railway Dashboard**: https://railway.app/dashboard
- **Health Check**: `https://your-app.railway.app/health`
- **Application**: `https://your-app.railway.app`

## Support

If you encounter issues:
1. Check the logs: `railway logs`
2. Test locally: `python3 fantasy_draft_web_enhanced.py`
3. Run dependency test: `python3 test_dependencies.py` 