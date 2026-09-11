#!/usr/bin/env python3
"""
Launcher script for James Clessuras FF Fantasy Draft Assistant
Runs the Flask web application on port 8787
"""

import os
import sys

# Set the port environment variable
os.environ['PORT'] = '7676'

# Import and run the main application
from fantasy_draft_web_enhanced import app

if __name__ == '__main__':
    print("🚀 Starting James Clessuras FF Fantasy Draft Assistant...")
    print(f"🌐 Server will be available at:  http://localhost:7676")
    print("📱 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=7676)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
