# James Clessuras FF - Fantasy Football Draft Assistant

A comprehensive fantasy football draft assistant with custom projections, simulations, and real-time recommendations.

## Features

- **Custom Projections**: Save and load custom player projections
- **Draft Simulations**: Run 40 simulations for accurate recommendations
- **Real-time Recommendations**: Get live draft advice based on your roster
- **User Authentication**: Secure login with Supabase
- **Multiple Scoring Formats**: PPR, Half-PPR, and Non-PPR support
- **Bench Value Optimization**: Smart bench value calculations

## Recent Updates

- **Bench Values**: TE (5%), RB/WR first (27%), RB/WR second (18%)
- **Simulation Count**: Increased to 40 simulations for better accuracy
- **Supabase Integration**: All data saved to and loaded from Supabase

## Railway Deployment

### Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Supabase Project**: Ensure your Supabase project is set up with the required tables
3. **Environment Variables**: Configure the following in Railway:

### Environment Variables

Set these in your Railway project settings:

```
SUPABASE_URL=https://arlovpdltkdlrkkmtigv.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFybG92cGRsdGtkbHJra210aWd2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1MjgyMDEsImV4cCI6MjA3MDEwNDIwMX0.PbTsyL_TmzNgYPxOPfAQPYI6MykbTNnW0sT5epwxTtg
FLASK_SECRET_KEY=your-secret-key-here
```

### Deployment Steps

1. **Connect Repository**: 
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub repository

2. **Configure Environment Variables**:
   - In your Railway project, go to "Variables"
   - Add the environment variables listed above

3. **Deploy**:
   - Railway will automatically detect the Python app
   - The `Procfile` and `requirements.txt` will handle the deployment
   - Your app will be available at the provided URL

### Database Setup

Ensure your Supabase project has the following tables:

- `users` - User authentication
- `user_custom_projections` - Custom player projections
- `user_draft_sessions` - Draft session data
- `user_rosters` - User roster data
- `completed_drafts` - Completed draft data

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL=https://arlovpdltkdlrkkmtigv.supabase.co
export SUPABASE_KEY=your-supabase-key
export FLASK_SECRET_KEY=your-secret-key

# Run the application
python3 fantasy_draft_web_enhanced.py
```

## Usage

1. **Login**: Use your credentials to access the application
2. **Pre-draft**: Set custom projections for players
3. **Initialize Draft**: Start a new draft session
4. **Get Recommendations**: Receive real-time draft advice
5. **Draft Players**: Make selections and track your roster

## Bench Value System

- **QB**: 10% (1st bench), 1% (2nd+ bench)
- **RB**: 27% (1st bench), 18% (2nd bench), 15% (3rd bench), 1% (4th+ bench)
- **WR**: 27% (1st bench), 18% (2nd bench), 10% (3rd bench), 1% (4th+ bench)
- **TE**: 5% (1st bench), 1% (2nd+ bench)
- **K/DST**: 1% (all bench positions)

## Support

For issues or questions, please check the application logs in Railway dashboard. 