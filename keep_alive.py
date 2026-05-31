from flask import Flask
from threading import Thread
import logging

# Import our custom logging system
from logger import logger

# Suppress default Flask console spam to keep our custom logs clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/')
def home():
    """This is the invisible web page Render and UptimeRobot will visit."""
    return "SLERO Bot is actively tracking prices 24/7!"

def run_server():
    """Starts the Flask server on a network port."""
    logger.info("Keep-Alive System: Binding web server to port 8080...")
    # Bind to 0.0.0.0 so Render's external network can reach it
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Spins up a background daemon thread for the web server."""
    logger.info("Keep-Alive System: Initializing background thread...")
    
    # Create the thread pointing to the run_server function
    server_thread = Thread(target=run_server)
    
    # A daemon thread automatically shuts down when the main bot stops
    server_thread.daemon = True 
    server_thread.start()
    
    logger.info("Keep-Alive System: Background web server successfully booted.")

if __name__ == "__main__":
    # Local standalone test
    print("Running standalone Keep-Alive test...")
    keep_alive()
    
    # Keep the main thread alive briefly to test if Flask spins up
    import time
    while True:
        time.sleep(1)