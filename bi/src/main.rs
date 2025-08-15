use std::collections::HashMap;
use std::io::{self, Write};
use std::path::Path;

use chrono::{Datelike, NaiveDateTime, Weekday};
use clap::Parser;
use csv::Reader;
use serde::Deserialize;
use anyhow::Result;

#[derive(Debug, Deserialize, Clone, serde::Serialize)]
struct TickerData {
    ticker: String,
    time_published: String,
    ticker_sentiment_score: f64,
    ticker_sentiment_label: String,
    title: String,
    source: String,
    url: String,
}

#[derive(Parser)]
#[command(name = "dollarpunk-bi")]
#[command(about = "Fast BI dashboard for DollarPunk ticker sentiment data")]
struct Args {
    #[arg(short, long, default_value = "../output/processed/tickers.csv")]
    data_file: String,
    
    #[arg(short, long)]
    tickers: Option<Vec<String>>,
    
    #[arg(short, long)]
    start_date: Option<String>,
    
    #[arg(short, long)]
    end_date: Option<String>,
    
    #[arg(short, long, default_value = "summary")]
    mode: String,
}

struct SentimentAnalyzer {
    data: Vec<TickerData>,
    filtered_data: Vec<TickerData>,
}

impl SentimentAnalyzer {
    fn new(data_file: &str) -> Result<Self> {
        println!("📂 Loading data from: {}", data_file);
        let mut reader = Reader::from_path(data_file)?;
        let mut data = Vec::new();
        
        for result in reader.deserialize() {
            let record: TickerData = result?;
            data.push(record);
        }
        
        println!("✅ Loaded {} records", data.len());
        
        Ok(SentimentAnalyzer {
            filtered_data: data.clone(),
            data,
        })
    }
    
    fn filter_by_tickers(&mut self, tickers: &[String]) {
        println!("🔍 Filtering by tickers: {:?}", tickers);
        self.filtered_data = self.data
            .iter()
            .filter(|record| tickers.contains(&record.ticker))
            .cloned()
            .collect();
        println!("✅ Filtered to {} records", self.filtered_data.len());
    }
    
    fn filter_by_date_range(&mut self, start_date: Option<&str>, end_date: Option<&str>) {
        if let Some(start_str) = start_date {
            println!("📅 Filtering from date: {}", start_str);
            if let Ok(start_dt) = NaiveDateTime::parse_from_str(start_str, "%Y%m%dT%H%M%S") {
                self.filtered_data = self.filtered_data
                    .iter()
                    .filter(|record| {
                        if let Ok(dt) = NaiveDateTime::parse_from_str(&record.time_published, "%Y%m%dT%H%M%S") {
                            dt >= start_dt
                        } else {
                            false
                        }
                    })
                    .cloned()
                    .collect();
            }
        }
        
        if let Some(end_str) = end_date {
            println!("📅 Filtering to date: {}", end_str);
            if let Ok(end_dt) = NaiveDateTime::parse_from_str(end_str, "%Y%m%dT%H%M%S") {
                self.filtered_data = self.filtered_data
                    .iter()
                    .filter(|record| {
                        if let Ok(dt) = NaiveDateTime::parse_from_str(&record.time_published, "%Y%m%dT%H%M%S") {
                            dt <= end_dt
                        } else {
                            false
                        }
                    })
                    .cloned()
                    .collect();
            }
        }
        
        println!("✅ Date filtered to {} records", self.filtered_data.len());
    }
    
    fn get_summary_stats(&self) -> HashMap<String, f64> {
        let mut stats = HashMap::new();
        
        if self.filtered_data.is_empty() {
            return stats;
        }
        
        let avg_sentiment = self.filtered_data
            .iter()
            .map(|r| r.ticker_sentiment_score)
            .sum::<f64>() / self.filtered_data.len() as f64;
        
        stats.insert("avg_sentiment".to_string(), avg_sentiment);
        stats.insert("total_articles".to_string(), self.filtered_data.len() as f64);
        
        let unique_tickers = self.filtered_data
            .iter()
            .map(|r| &r.ticker)
            .collect::<std::collections::HashSet<_>>()
            .len();
        
        stats.insert("unique_tickers".to_string(), unique_tickers as f64);
        
        stats
    }
    
    fn get_sentiment_by_ticker(&self) -> HashMap<String, f64> {
        let mut ticker_sentiments = HashMap::new();
        
        for record in &self.filtered_data {
            let entry = ticker_sentiments.entry(record.ticker.clone()).or_insert(Vec::new());
            entry.push(record.ticker_sentiment_score);
        }
        
        ticker_sentiments
            .into_iter()
            .map(|(ticker, scores)| {
                let avg = scores.iter().sum::<f64>() / scores.len() as f64;
                (ticker, avg)
            })
            .collect()
    }
    
    fn get_sentiment_by_weekday(&self) -> HashMap<Weekday, f64> {
        let mut weekday_sentiments = HashMap::new();
        
        for record in &self.filtered_data {
            if let Ok(dt) = NaiveDateTime::parse_from_str(&record.time_published, "%Y%m%dT%H%M%S") {
                let weekday = dt.weekday();
                let entry = weekday_sentiments.entry(weekday).or_insert(Vec::new());
                entry.push(record.ticker_sentiment_score);
            }
        }
        
        weekday_sentiments
            .into_iter()
            .map(|(weekday, scores)| {
                let avg = scores.iter().sum::<f64>() / scores.len() as f64;
                (weekday, avg)
            })
            .collect()
    }
    
    fn print_summary(&self) {
        println!("📊 DollarPunk BI Dashboard - Summary");
        println!("{}", "=".repeat(50));
        
        let stats = self.get_summary_stats();
        println!("📈 Key Metrics:");
        println!("   Average Sentiment: {:.3}", stats.get("avg_sentiment").unwrap_or(&0.0));
        println!("   Total Articles: {}", *stats.get("total_articles").unwrap_or(&0.0) as i32);
        println!("   Unique Tickers: {}", *stats.get("unique_tickers").unwrap_or(&0.0) as i32);
        println!();
        
        let ticker_sentiments = self.get_sentiment_by_ticker();
        println!("📊 Sentiment by Ticker (Top 10):");
        let mut sorted_tickers: Vec<_> = ticker_sentiments.iter().collect();
        sorted_tickers.sort_by(|a, b| b.1.partial_cmp(a.1).unwrap_or(std::cmp::Ordering::Equal));
        
        for (ticker, sentiment) in sorted_tickers.iter().take(10) {
            let emoji = match **sentiment {
                s if s > 0.3 => "🟢",
                s if s > 0.1 => "🟡",
                s if s > -0.1 => "⚪",
                s if s > -0.3 => "🟠",
                _ => "🔴",
            };
            println!("   {} {}: {:.3}", emoji, ticker, sentiment);
        }
        println!();
        
        let weekday_sentiments = self.get_sentiment_by_weekday();
        println!("📅 Sentiment by Weekday:");
        let weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
        for weekday in weekdays {
            let wd = match weekday {
                "Mon" => Weekday::Mon,
                "Tue" => Weekday::Tue,
                "Wed" => Weekday::Wed,
                "Thu" => Weekday::Thu,
                "Fri" => Weekday::Fri,
                "Sat" => Weekday::Sat,
                "Sun" => Weekday::Sun,
                _ => continue,
            };
            if let Some(sentiment) = weekday_sentiments.get(&wd) {
                let emoji = match *sentiment {
                    s if s > 0.3 => "🟢",
                    s if s > 0.1 => "🟡",
                    s if s > -0.1 => "⚪",
                    s if s > -0.3 => "🟠",
                    _ => "🔴",
                };
                println!("   {} {}: {:.3}", emoji, weekday, sentiment);
            }
        }
        println!();
        
        println!("📋 Sample Articles (Top 5 by sentiment):");
        let mut sorted_articles: Vec<_> = self.filtered_data.iter().collect();
        sorted_articles.sort_by(|a, b| b.ticker_sentiment_score.partial_cmp(&a.ticker_sentiment_score).unwrap_or(std::cmp::Ordering::Equal));
        
        for record in sorted_articles.iter().take(5) {
            let emoji = match record.ticker_sentiment_score {
                s if s > 0.3 => "🟢",
                s if s > 0.1 => "🟡",
                s if s > -0.1 => "⚪",
                s if s > -0.3 => "🟠",
                _ => "🔴",
            };
            println!("   {} {} - {:.3}: {}", 
                emoji,
                record.ticker, 
                record.ticker_sentiment_score, 
                record.title.chars().take(60).collect::<String>()
            );
        }
    }
    
    fn print_calendar_heatmap(&self) {
        println!("📅 Sentiment Calendar Heatmap");
        println!("{}", "=".repeat(50));
        
        let mut daily_sentiments: HashMap<String, Vec<f64>> = HashMap::new();
        
        for record in &self.filtered_data {
            if let Ok(dt) = NaiveDateTime::parse_from_str(&record.time_published, "%Y%m%dT%H%M%S") {
                let date_key = dt.format("%Y-%m-%d").to_string();
                daily_sentiments.entry(date_key).or_insert(Vec::new()).push(record.ticker_sentiment_score);
            }
        }
        
        // Sort dates and print heatmap
        let mut sorted_dates: Vec<_> = daily_sentiments.keys().collect();
        sorted_dates.sort();
        
        println!("📊 Daily Average Sentiment (Last 30 days):");
        for date in sorted_dates.iter().take(30) {
            let sentiments = &daily_sentiments[*date];
            let avg_sentiment = sentiments.iter().sum::<f64>() / sentiments.len() as f64;
            
            // Create a simple text-based heatmap
            let intensity = match avg_sentiment {
                s if s > 0.5 => "🟢", // Very positive
                s if s > 0.2 => "🟡", // Positive
                s if s > -0.2 => "⚪", // Neutral
                s if s > -0.5 => "🟠", // Negative
                _ => "🔴", // Very negative
            };
            
            println!("{} {}: {:.3} ({} articles)", intensity, date, avg_sentiment, sentiments.len());
        }
    }
    
    fn export_to_csv(&self, filename: &str) -> Result<()> {
        let mut writer = csv::Writer::from_path(filename)?;
        
        for record in &self.filtered_data {
            writer.serialize(record)?;
        }
        
        writer.flush()?;
        println!("✅ Data exported to {}", filename);
        Ok(())
    }
    
    fn list_available_tickers(&self) {
        let mut tickers: Vec<_> = self.data.iter().map(|r| &r.ticker).collect::<std::collections::HashSet<_>>().into_iter().collect();
        tickers.sort();
        
        println!("📋 Available Tickers ({}):", tickers.len());
        for (i, ticker) in tickers.iter().enumerate() {
            print!("{} ", ticker);
            if (i + 1) % 10 == 0 {
                println!();
            }
        }
        println!();
    }
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    if !Path::new(&args.data_file).exists() {
        eprintln!("❌ Data file not found: {}", args.data_file);
        std::process::exit(1);
    }
    
    let mut analyzer = SentimentAnalyzer::new(&args.data_file)?;
    
    // Apply filters
    if let Some(tickers) = args.tickers {
        analyzer.filter_by_tickers(&tickers);
    }
    
    analyzer.filter_by_date_range(args.start_date.as_deref(), args.end_date.as_deref());
    
    match args.mode.as_str() {
        "summary" => {
            analyzer.print_summary();
        }
        "calendar" => {
            analyzer.print_calendar_heatmap();
        }
        "export" => {
            analyzer.export_to_csv("filtered_tickers.csv")?;
        }
        "tickers" => {
            analyzer.list_available_tickers();
        }
        "interactive" => {
            interactive_mode(&mut analyzer)?;
        }
        _ => {
            println!("Available modes: summary, calendar, export, tickers, interactive");
        }
    }
    
    Ok(())
}

fn interactive_mode(analyzer: &mut SentimentAnalyzer) -> Result<()> {
    println!("🎮 Interactive Mode - DollarPunk BI");
    println!("Commands:");
    println!("  summary                    - Show summary statistics");
    println!("  calendar                   - Show calendar heatmap");
    println!("  tickers                    - List available tickers");
    println!("  filter AAPL TSLA MSFT      - Filter by specific tickers");
    println!("  date 20250101 20250131     - Filter by date range");
    println!("  export                     - Export filtered data");
    println!("  quit                       - Exit");
    println!("{}", "=".repeat(50));
    
    loop {
        print!("dollarpunk> ");
        io::stdout().flush()?;
        
        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        let input = input.trim();
        
        match input {
            "summary" => {
                analyzer.print_summary();
            }
            "calendar" => {
                analyzer.print_calendar_heatmap();
            }
            "tickers" => {
                analyzer.list_available_tickers();
            }
            "export" => {
                analyzer.export_to_csv("interactive_export.csv")?;
            }
            "quit" | "exit" => {
                println!("👋 Goodbye!");
                break;
            }
            input if input.starts_with("filter ") => {
                let tickers: Vec<String> = input[7..]
                    .split_whitespace()
                    .map(|s| s.to_string())
                    .collect();
                analyzer.filter_by_tickers(&tickers);
            }
            input if input.starts_with("date ") => {
                let parts: Vec<&str> = input[5..].split_whitespace().collect();
                if parts.len() >= 2 {
                    let start_date = format!("{}T000000", parts[0]);
                    let end_date = format!("{}T235959", parts[1]);
                    analyzer.filter_by_date_range(Some(&start_date), Some(&end_date));
                } else {
                    println!("❌ Usage: date YYYYMMDD YYYYMMDD");
                }
            }
            _ => {
                println!("❓ Unknown command. Type 'help' for available commands.");
            }
        }
    }
    
    Ok(())
}
