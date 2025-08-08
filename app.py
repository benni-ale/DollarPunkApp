from flask import Flask, render_template, jsonify, request
import json
import os
import time
from datetime import datetime
import threading
import subprocess
import psutil

app = Flask(__name__)

# Global variables for monitoring
ingestion_status = {
    "is_running": False,
    "start_time": None,
    "last_update": None,
    "progress": 0,
    "current_ticker": None,
    "total_articles": 0,
    "articles_per_ticker": {}
}

def get_news_stats():
    """Get statistics from the most recent news data file"""
    try:
        # Find the most recent news data file with timestamp
        output_dir = "/app/output"
        if not os.path.exists(output_dir):
            print(f"Output directory not found at: {output_dir}")
            return {
                "total_articles": 0,
                "tickers": {},
                "sentiment_distribution": {},
                "latest_articles": []
            }
        
        # Look for files matching the pattern news_data_YYYYMMDD_HHMMSS.json
        import glob
        pattern = os.path.join(output_dir, "news_data_*.json")
        files = glob.glob(pattern)
        
        if not files:
            print(f"No news data files found in: {output_dir}")
            return {
                "total_articles": 0,
                "tickers": {},
                "sentiment_distribution": {},
                "latest_articles": []
            }
        
        # Get the most recent file (highest timestamp)
        latest_file = max(files, key=os.path.getctime)
        print(f"Using most recent file: {latest_file}")
        
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"Successfully loaded {len(data)} articles from: {latest_file}")
        
        stats = {
            "total_articles": len(data),
            "tickers": {},
            "sentiment_distribution": {},
            "latest_articles": [],
            "current_file": os.path.basename(latest_file)
        }
        
        # Count articles per ticker
        for article in data:
            ticker = article.get("source_ticker", "Unknown")
            if ticker not in stats["tickers"]:
                stats["tickers"][ticker] = 0
            stats["tickers"][ticker] += 1
            
            # Count sentiment distribution
            sentiment = article.get("overall_sentiment_label", "Unknown")
            if sentiment not in stats["sentiment_distribution"]:
                stats["sentiment_distribution"][sentiment] = 0
            stats["sentiment_distribution"][sentiment] += 1
        
        # Get latest 5 articles
        stats["latest_articles"] = data[-5:] if len(data) >= 5 else data
        
        return stats
    except FileNotFoundError:
        return {
            "total_articles": 0,
            "tickers": {},
            "sentiment_distribution": {},
            "latest_articles": []
        }
    except Exception as e:
        return {"error": str(e)}

def get_docker_status():
    """Check if Docker container is running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=dollarpunk", "--format", "{{.Status}}"],
            capture_output=True, text=True
        )
        return result.stdout.strip() != ""
    except:
        return False

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    stats = get_news_stats()
    docker_running = get_docker_status()
    
    return jsonify({
        "news_stats": stats,
        "docker_status": docker_running,
        "ingestion_status": ingestion_status
    })

def run_ingestion():
    """Run the ingestion process in a separate thread"""
    try:
        # Import and run the ingestion
        from ingest import run_ingestion as ingest_run
        ingest_run()
        print("Ingestion completed successfully")
        ingestion_status["is_running"] = False
        ingestion_status["progress"] = 100
    except Exception as e:
        print(f"Ingestion error: {e}")
        ingestion_status["is_running"] = False

@app.route('/api/start_ingestion', methods=['POST'])
def start_ingestion():
    if ingestion_status["is_running"]:
        return jsonify({"error": "Ingestion already running"}), 400
    
    try:
        # Start ingestion in a separate thread
        ingestion_thread = threading.Thread(target=run_ingestion)
        ingestion_thread.daemon = True
        ingestion_thread.start()
        
        ingestion_status["is_running"] = True
        ingestion_status["start_time"] = datetime.now().isoformat()
        ingestion_status["progress"] = 0
        
        return jsonify({"message": "Ingestion started successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stop_ingestion', methods=['POST'])
def stop_ingestion():
    try:
        # Stop ingestion by setting flag
        ingestion_status["is_running"] = False
        ingestion_status["progress"] = 0
        ingestion_status["current_ticker"] = None
        
        return jsonify({"message": "Ingestion stopped successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs')
def get_logs():
    try:
        result = subprocess.run([
            "docker-compose", "logs", "--tail=50"
        ], cwd=os.getcwd(), capture_output=True, text=True)
        return jsonify({"logs": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug')
def debug_info():
    """Debug endpoint to check file paths and data"""
    import os
    import glob
    debug_info = {
        "current_working_dir": os.getcwd(),
        "files_in_output": [],
        "file_exists": {},
        "data_sample": None,
        "news_files": []
    }
    
    # Check output directory
    output_paths = ["output", "/app/output", "./output"]
    for path in output_paths:
        try:
            if os.path.exists(path):
                files = os.listdir(path)
                debug_info["files_in_output"].extend(files)
                debug_info["file_exists"][path] = True
                
                # Find news data files with timestamps
                pattern = os.path.join(path, "news_data_*.json")
                news_files = glob.glob(pattern)
                debug_info["news_files"].extend([os.path.basename(f) for f in news_files])
            else:
                debug_info["file_exists"][path] = False
        except Exception as e:
            debug_info["file_exists"][path] = f"Error: {str(e)}"
    
    # Try to read a sample of the most recent data file
    try:
        # Find the most recent news data file
        output_dir = "output"
        if os.path.exists(output_dir):
            pattern = os.path.join(output_dir, "news_data_*.json")
            files = glob.glob(pattern)
            if files:
                latest_file = max(files, key=os.path.getctime)
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    debug_info["data_sample"] = {
                        "file": os.path.basename(latest_file),
                        "total_articles": len(data),
                        "first_article": data[0] if data else None
                    }
            else:
                debug_info["data_sample"] = "No news data files found"
        else:
            debug_info["data_sample"] = "Output directory not found"
    except Exception as e:
        debug_info["data_sample"] = f"Error reading file: {str(e)}"
    
    return jsonify(debug_info)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 