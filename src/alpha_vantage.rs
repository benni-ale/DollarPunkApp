use crate::models::*;
use anyhow::Result;
use chrono::{DateTime, Utc};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tokio::time::{sleep, Duration};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageConfig {
    pub api_key: String,
    pub base_url: String,
    pub rate_limit_delay_ms: u64,
    pub max_requests_per_minute: u32,
}

impl Default for AlphaVantageConfig {
    fn default() -> Self {
        Self {
            api_key: String::new(),
            base_url: "https://www.alphavantage.co/query".to_string(),
            rate_limit_delay_ms: 12000, // Alpha Vantage free tier: 5 requests per minute
            max_requests_per_minute: 5,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageNewsResponse {
    pub items: Vec<AlphaVantageNewsItem>,
    pub feed: Option<AlphaVantageFeed>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageNewsItem {
    pub title: String,
    pub url: String,
    pub time_published: String,
    pub authors: Vec<String>,
    pub summary: String,
    pub banner_image: Option<String>,
    pub source: String,
    pub category_within_source: String,
    pub source_domain: String,
    pub topics: Vec<AlphaVantageTopic>,
    pub overall_sentiment_score: Option<f64>,
    pub overall_sentiment_label: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageFeed {
    pub title: String,
    pub url: String,
    pub time_published: String,
    pub authors: Vec<String>,
    pub summary: String,
    pub banner_image: Option<String>,
    pub source: String,
    pub category_within_source: String,
    pub source_domain: String,
    pub topics: Vec<AlphaVantageTopic>,
    pub overall_sentiment_score: Option<f64>,
    pub overall_sentiment_label: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageTopic {
    pub topic: String,
    pub relevance_score: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageSentimentResponse {
    pub items: Vec<AlphaVantageSentimentItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageSentimentItem {
    pub title: String,
    pub url: String,
    pub time_published: String,
    pub authors: Vec<String>,
    pub summary: String,
    pub banner_image: Option<String>,
    pub source: String,
    pub category_within_source: String,
    pub source_domain: String,
    pub topics: Vec<AlphaVantageTopic>,
    pub overall_sentiment_score: Option<f64>,
    pub overall_sentiment_label: Option<String>,
    pub ticker_sentiment: Vec<AlphaVantageTickerSentiment>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageTickerSentiment {
    pub ticker: String,
    pub relevance_score: String,
    pub ticker_sentiment_score: String,
    pub ticker_sentiment_label: String,
}

#[derive(Clone)]
pub struct AlphaVantageClient {
    config: AlphaVantageConfig,
    client: Client,
    request_count: u32,
    last_request_time: DateTime<Utc>,
}

impl AlphaVantageClient {
    pub fn new(config: AlphaVantageConfig) -> Self {
        Self {
            config,
            client: Client::new(),
            request_count: 0,
            last_request_time: Utc::now(),
        }
    }

    pub async fn collect_news_data(&mut self, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        let mut all_news = Vec::new();
        
        // Collect general news
        let general_news = self.fetch_news_sentiment("general", filters).await?;
        all_news.extend(general_news);
        
        // Collect news for specific keywords
        for keyword in &filters.keywords {
            let keyword_news = self.fetch_news_sentiment(keyword, filters).await?;
            all_news.extend(keyword_news);
            
            // Rate limiting
            sleep(Duration::from_millis(self.config.rate_limit_delay_ms)).await;
        }
        
        Ok(all_news)
    }

    async fn fetch_news_sentiment(&mut self, topics: &str, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        self.check_rate_limit().await;
        
        let mut params = HashMap::new();
        params.insert("function", "NEWS_SENTIMENT");
        params.insert("apikey", &self.config.api_key);
        params.insert("topics", topics);
        params.insert("limit", "50"); // Maximum for free tier
        
        let response = self.client
            .get(&self.config.base_url)
            .query(&params)
            .send()
            .await?;
        
        self.request_count += 1;
        self.last_request_time = Utc::now();
        
        if response.status().is_success() {
            let json_response: AlphaVantageSentimentResponse = response.json().await?;
            Ok(self.convert_to_data_points(json_response, filters))
        } else {
            eprintln!("Alpha Vantage API error: {}", response.status());
            Ok(Vec::new())
        }
    }

    async fn fetch_news(&mut self, topics: &str, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        self.check_rate_limit().await;
        
        let mut params = HashMap::new();
        params.insert("function", "NEWS_SENTIMENT");
        params.insert("apikey", &self.config.api_key);
        params.insert("topics", topics);
        params.insert("limit", "50");
        
        let response = self.client
            .get(&self.config.base_url)
            .query(&params)
            .send()
            .await?;
        
        self.request_count += 1;
        self.last_request_time = Utc::now();
        
        if response.status().is_success() {
            let json_response: AlphaVantageNewsResponse = response.json().await?;
            Ok(self.convert_news_to_data_points(json_response, filters))
        } else {
            eprintln!("Alpha Vantage API error: {}", response.status());
            Ok(Vec::new())
        }
    }

    fn convert_to_data_points(&self, response: AlphaVantageSentimentResponse, filters: &DataFilters) -> Vec<DataPoint> {
        let mut data_points = Vec::new();
        
        for (i, item) in response.items.into_iter().enumerate() {
            let content = format!("{} - {}", item.title, item.summary);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);
            
            if self.matches_filters(&content, filters) {
                let timestamp = self.parse_alpha_vantage_time(&item.time_published);
                
                data_points.push(DataPoint {
                    id: format!("alpha_vantage_{}", i),
                    content,
                    platform: Platform::NewsWebsite,
                    timestamp,
                    theme,
                    author: item.authors.join(", "),
                    url: Some(item.url),
                    engagement_metrics: EngagementMetrics {
                        likes: 0, // Alpha Vantage doesn't provide engagement metrics
                        shares: 0,
                        comments: 0,
                        views: 0,
                    },
                    language,
                    sentiment_score: item.overall_sentiment_score,
                });
            }
        }
        
        data_points
    }

    fn convert_news_to_data_points(&self, response: AlphaVantageNewsResponse, filters: &DataFilters) -> Vec<DataPoint> {
        let mut data_points = Vec::new();
        
        // Handle items
        for (i, item) in response.items.into_iter().enumerate() {
            let content = format!("{} - {}", item.title, item.summary);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);
            
            if self.matches_filters(&content, filters) {
                let timestamp = self.parse_alpha_vantage_time(&item.time_published);
                
                data_points.push(DataPoint {
                    id: format!("alpha_vantage_news_{}", i),
                    content,
                    platform: Platform::NewsWebsite,
                    timestamp,
                    theme,
                    author: item.authors.join(", "),
                    url: Some(item.url),
                    engagement_metrics: EngagementMetrics {
                        likes: 0,
                        shares: 0,
                        comments: 0,
                        views: 0,
                    },
                    language,
                    sentiment_score: item.overall_sentiment_score,
                });
            }
        }
        
        // Handle feed if present
        if let Some(feed) = response.feed {
            let content = format!("{} - {}", feed.title, feed.summary);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);
            
            if self.matches_filters(&content, filters) {
                let timestamp = self.parse_alpha_vantage_time(&feed.time_published);
                
                data_points.push(DataPoint {
                    id: "alpha_vantage_feed".to_string(),
                    content,
                    platform: Platform::NewsWebsite,
                    timestamp,
                    theme,
                    author: feed.authors.join(", "),
                    url: Some(feed.url),
                    engagement_metrics: EngagementMetrics {
                        likes: 0,
                        shares: 0,
                        comments: 0,
                        views: 0,
                    },
                    language,
                    sentiment_score: feed.overall_sentiment_score,
                });
            }
        }
        
        data_points
    }

    fn parse_alpha_vantage_time(&self, time_str: &str) -> DateTime<Utc> {
        // Alpha Vantage time format: "20231201T000000"
        if let Ok(datetime) = DateTime::parse_from_str(&format!("{} +00:00", time_str), "%Y%m%dT%H%M%S %z") {
            datetime.with_timezone(&Utc)
        } else {
            Utc::now()
        }
    }

    fn classify_theme(&self, content: &str) -> Theme {
        let content_lower = content.to_lowercase();
        
        if content_lower.contains("politic") || content_lower.contains("government") {
            Theme::Politics
        } else if content_lower.contains("econom") || content_lower.contains("finance") || 
                  content_lower.contains("market") || content_lower.contains("stock") ||
                  content_lower.contains("trading") || content_lower.contains("investment") {
            Theme::Economy
        } else if content_lower.contains("tech") || content_lower.contains("ai") || 
                  content_lower.contains("software") || content_lower.contains("digital") {
            Theme::Technology
        } else if content_lower.contains("sport") {
            Theme::Sports
        } else if content_lower.contains("entertain") || content_lower.contains("movie") {
            Theme::Entertainment
        } else if content_lower.contains("health") || content_lower.contains("medical") {
            Theme::Health
        } else if content_lower.contains("scien") || content_lower.contains("research") {
            Theme::Science
        } else if content_lower.contains("environ") || content_lower.contains("climate") {
            Theme::Environment
        } else if content_lower.contains("educat") || content_lower.contains("school") {
            Theme::Education
        } else {
            Theme::Other("General".to_string())
        }
    }

    fn detect_language(&self, content: &str) -> String {
        match whatlang::detect(content) {
            Some(info) => info.lang().code().to_string(),
            None => "en".to_string(),
        }
    }

    fn matches_filters(&self, content: &str, filters: &DataFilters) -> bool {
        let content_lower = content.to_lowercase();
        
        // Check keywords
        let has_keyword = filters.keywords.iter().any(|keyword| {
            content_lower.contains(&keyword.to_lowercase())
        });

        // Check language
        let language = self.detect_language(content);
        let has_language = filters.languages.contains(&language);

        has_keyword && has_language
    }

    async fn check_rate_limit(&mut self) {
        let now = Utc::now();
        let time_diff = now.signed_duration_since(self.last_request_time);
        
        // Reset counter if more than a minute has passed
        if time_diff.num_minutes() >= 1 {
            self.request_count = 0;
        }
        
        // If we've hit the rate limit, wait
        if self.request_count >= self.config.max_requests_per_minute {
            let wait_time = 60 - time_diff.num_seconds() as u64;
            if wait_time > 0 {
                sleep(Duration::from_secs(wait_time)).await;
                self.request_count = 0;
                self.last_request_time = Utc::now();
            }
        }
    }

    pub async fn get_market_data(&mut self, symbol: &str) -> Result<HashMap<String, f64>> {
        self.check_rate_limit().await;
        
        let mut params = HashMap::new();
        params.insert("function", "GLOBAL_QUOTE");
        params.insert("apikey", &self.config.api_key);
        params.insert("symbol", symbol);
        
        let response = self.client
            .get(&self.config.base_url)
            .query(&params)
            .send()
            .await?;
        
        self.request_count += 1;
        self.last_request_time = Utc::now();
        
        if response.status().is_success() {
            let json_response: serde_json::Value = response.json().await?;
            
            if let Some(quote) = json_response.get("Global Quote") {
                let mut market_data = HashMap::new();
                
                if let Some(price) = quote.get("05. price").and_then(|v| v.as_str()).and_then(|s| s.parse::<f64>().ok()) {
                    market_data.insert("price".to_string(), price);
                }
                
                if let Some(change) = quote.get("09. change").and_then(|v| v.as_str()).and_then(|s| s.parse::<f64>().ok()) {
                    market_data.insert("change".to_string(), change);
                }
                
                if let Some(change_percent) = quote.get("10. change percent").and_then(|v| v.as_str()).and_then(|s| s.trim_end_matches('%').parse::<f64>().ok()) {
                    market_data.insert("change_percent".to_string(), change_percent);
                }
                
                Ok(market_data)
            } else {
                Ok(HashMap::new())
            }
        } else {
            eprintln!("Alpha Vantage API error: {}", response.status());
            Ok(HashMap::new())
        }
    }
} 