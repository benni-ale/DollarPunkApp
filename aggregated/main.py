#!/usr/bin/env python3
"""
Main script to aggregate ticker sentiment data using the avgW_no_decay function.
Reads from output/processed/tickers.csv and outputs to output/aggregated/tickers.csv
"""

import os
import sys
import pandas as pd
import time
import threading
from datetime import datetime, timedelta
from aggregate import avgW_no_decay

# Global variables for progress tracking
processing_start_time = None
progress_stop_flag = False

def progress_logger():
    """Log progress every minute during processing"""
    global processing_start_time, progress_stop_flag
    
    while not progress_stop_flag:
        time.sleep(60)  # Wait 1 minute
        if not progress_stop_flag and processing_start_time:
            elapsed = time.time() - processing_start_time
            elapsed_str = str(timedelta(seconds=int(elapsed)))
            print(f"[PROGRESS] Processing still running... Elapsed time: {elapsed_str}")

def log_with_timestamp(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    global processing_start_time, progress_stop_flag
    
    # Define input and output paths
    input_file = "/app/data/input/tickers.csv"
    output_dir = "/app/data/output/aggregated"
    output_file = os.path.join(output_dir, "tickers.csv")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    log_with_timestamp("=" * 60)
    log_with_timestamp("DOLLARPUNK AGGREGATION PROCESS STARTING")
    log_with_timestamp("=" * 60)
    log_with_timestamp(f"Input file: {input_file}")
    log_with_timestamp(f"Output file: {output_file}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        log_with_timestamp(f"ERROR: Input file {input_file} not found!")
        sys.exit(1)
    
    # Get file size for progress tracking
    file_size = os.path.getsize(input_file)
    log_with_timestamp(f"Input file size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    try:
        # Start progress logging thread
        progress_thread = threading.Thread(target=progress_logger, daemon=True)
        progress_thread.start()
        
        # Start timing
        processing_start_time = time.time()
        log_with_timestamp("Starting data processing...")
        
        # Process the data using the avgW_no_decay function
        log_with_timestamp("Reading CSV file...")
        read_start = time.time()
        
        result_df = avgW_no_decay(input_file)
        
        read_end = time.time()
        read_duration = read_end - read_start
        log_with_timestamp(f"CSV processing completed in {read_duration:.2f} seconds")
        
        # Stop progress logging
        progress_stop_flag = True
        
        # Calculate total processing time
        total_time = time.time() - processing_start_time
        log_with_timestamp(f"Total processing time: {total_time:.2f} seconds")
        
        # Save the aggregated results
        log_with_timestamp("Saving aggregated results...")
        save_start = time.time()
        
        result_df.to_csv(output_file, index=False)
        
        save_end = time.time()
        save_duration = save_end - save_start
        log_with_timestamp(f"Results saved in {save_duration:.2f} seconds")
        
        # Display results summary
        log_with_timestamp("=" * 60)
        log_with_timestamp("PROCESSING COMPLETED SUCCESSFULLY")
        log_with_timestamp("=" * 60)
        log_with_timestamp(f"Total aggregated records: {len(result_df):,}")
        log_with_timestamp(f"Results saved to: {output_file}")
        
        # Display sample of results
        log_with_timestamp("\nSample of aggregated results (first 10 rows):")
        print(result_df.head(10).to_string(index=False))
        
        # Display summary statistics
        log_with_timestamp(f"\nSummary Statistics:")
        log_with_timestamp(f"Total unique tickers: {result_df['ticker'].nunique():,}")
        log_with_timestamp(f"Date range: {result_df['date'].min()} to {result_df['date'].max()}")
        log_with_timestamp(f"Total days covered: {(result_df['date'].max() - result_df['date'].min()).days + 1}")
        
        # Top sentiment tickers
        ticker_avg = result_df.groupby('ticker')['AvgW_d'].mean().sort_values(ascending=False)
        log_with_timestamp(f"\nTop 10 most positive sentiment tickers:")
        for i, (ticker, score) in enumerate(ticker_avg.head(10).items(), 1):
            log_with_timestamp(f"{i:2d}. {ticker}: {score:.4f}")
        
        # Bottom sentiment tickers
        log_with_timestamp(f"\nTop 10 most negative sentiment tickers:")
        for i, (ticker, score) in enumerate(ticker_avg.tail(10).items(), 1):
            log_with_timestamp(f"{i:2d}. {ticker}: {score:.4f}")
        
        # Performance metrics
        records_per_second = len(result_df) / total_time if total_time > 0 else 0
        log_with_timestamp(f"\nPerformance Metrics:")
        log_with_timestamp(f"Processing speed: {records_per_second:.0f} records/second")
        log_with_timestamp(f"Memory usage: {sys.getsizeof(result_df):,} bytes")
        
        log_with_timestamp("=" * 60)
        log_with_timestamp("AGGREGATION PROCESS COMPLETED")
        log_with_timestamp("=" * 60)
        
    except Exception as e:
        progress_stop_flag = True
        log_with_timestamp(f"ERROR during processing: {str(e)}")
        log_with_timestamp(f"Error type: {type(e).__name__}")
        import traceback
        log_with_timestamp(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
