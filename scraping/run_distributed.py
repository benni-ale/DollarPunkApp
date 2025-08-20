#!/usr/bin/env python3
import subprocess
import json
import os
import sys
import time
from datetime import datetime

def run_coordinator(input_csv, output_folder, nodes=5):
    """Run the coordinator and get the node configurations"""
    print("🚀 Running coordinator...")
    
    cmd = [
        "python", "scrape_coordinator.py",
        input_csv,
        output_folder,
        "--nodes", str(nodes)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Coordinator failed: {result.stderr}")
        return None
    
    print(result.stdout)
    
    # Parse the output to get node configurations
    # We'll need to extract the configs from the coordinator output
    # For now, let's use a simpler approach with environment variables
    
    return True

def launch_node(node_id, run_id, urls_json, output_file):
    """Launch a single node"""
    cmd = [
        "python", "scrape.py",
        "--node-id", node_id,
        "--run-id", run_id,
        "--urls", urls_json,
        "--output", output_file
    ]
    
    print(f"🚀 Launching {node_id}...")
    process = subprocess.Popen(cmd)
    return process

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_distributed.py <input_csv> <output_folder> [nodes]")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_folder = sys.argv[2]
    nodes = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    print(f"🎯 Starting distributed scraping")
    print(f"📁 Input: {input_csv}")
    print(f"📁 Output: {output_folder}")
    print(f"🖥️  Nodes: {nodes}")
    
    # Run coordinator
    success = run_coordinator(input_csv, output_folder, nodes)
    if not success:
        print("❌ Coordinator failed, exiting")
        sys.exit(1)
    
    # For now, we'll use a simpler approach
    # In a real implementation, you'd parse the coordinator output
    # and extract the node configurations
    
    print("✅ Coordinator completed successfully!")
    print("📝 Note: This is a simplified version. For full distributed execution,")
    print("   you'll need to manually launch nodes with the parameters shown above.")

if __name__ == "__main__":
    main()
