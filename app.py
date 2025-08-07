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
    """Get statistics from the news data file"""
    try:
        with open("output/news_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        stats = {
            "total_articles": len(data),
            "tickers": {},
            "sentiment_distribution": {},
            "latest_articles": []
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

@app.route('/api/start_ingestion', methods=['POST'])
def start_ingestion():
    if ingestion_status["is_running"]:
        return jsonify({"error": "Ingestion already running"}), 400
    
    try:
        # Start Docker container in background
        subprocess.Popen([
            "docker-compose", "up", "-d"
        ], cwd=os.getcwd())
        
        ingestion_status["is_running"] = True
        ingestion_status["start_time"] = datetime.now().isoformat()
        ingestion_status["progress"] = 0
        
        return jsonify({"message": "Ingestion started successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stop_ingestion', methods=['POST'])
def stop_ingestion():
    try:
        # Stop Docker container
        subprocess.run([
            "docker-compose", "down"
        ], cwd=os.getcwd())
        
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 