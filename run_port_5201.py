#!/usr/bin/env python3
"""
Run the Fantasy Draft Assistant on port 5201
"""

import os
import sys

# Set the port environment variable
os.environ['PORT'] = '5201'

# Import and run the main application
from fantasy_draft_web_enhanced import app

if __name__ == '__main__':
    print("Starting Fantasy Draft Assistant on port 5201...")
    print("Using rankings from: 09042025LEAGUE_Rankings 2.csv")
    print("Access the application at: http://localhost:5201")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5201)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)