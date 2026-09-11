#!/usr/bin/env python3
"""
James Clessuras FF - Fantasy Draft Assistant Launcher
Custom launcher script for James Clessuras FF
"""

import os
import sys

# Set the port environment variable
os.environ['PORT'] = '8787'

# Import and run the main application
from fantasy_draft_web_enhanced import app

if __name__ == '__main__':
    print("🏈 Starting James Clessuras FF Fantasy Draft Assistant...")
    print("🎯 Your personal fantasy football draft assistant")
    print(f"🌐 Server will be available at:  http://localhost:8787")
    print("📱 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=8787)
    except KeyboardInterrupt:
        print("\n👋 James Clessuras FF stopped by user")
    except Exception as e:
        print(f"❌ Error starting James Clessuras FF: {e}")
        sys.exit(1)

