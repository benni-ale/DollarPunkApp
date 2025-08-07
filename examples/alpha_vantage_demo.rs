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
pub struct AlphaVantageTopic {
    pub topic: String,
    pub relevance_score: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageSentimentResponse {
    pub items: Vec<AlphaVantageNewsItem>,
}

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

    pub async fn collect_news_data(&mut self, keywords: &[String]) -> Result<Vec<AlphaVantageNewsItem>> {
        let mut all_news = Vec::new();
        
        // Collect general news
        let general_news = self.fetch_news_sentiment("general").await?;
        all_news.extend(general_news);
        
        // Collect news for specific keywords
        for keyword in keywords {
            let keyword_news = self.fetch_news_sentiment(keyword).await?;
            all_news.extend(keyword_news);
            
            // Rate limiting
            sleep(Duration::from_millis(self.config.rate_limit_delay_ms)).await;
        }
        
        Ok(all_news)
    }

    async fn fetch_news_sentiment(&mut self, topics: &str) -> Result<Vec<AlphaVantageNewsItem>> {
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
            Ok(json_response.items)
        } else {
            eprintln!("Alpha Vantage API error: {}", response.status());
            Ok(Vec::new())
        }
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

#[tokio::main]
async fn main() -> Result<()> {
    // Inizializza il logging
    tracing_subscriber::fmt::init();

    println!("🚀 Esempio di utilizzo di Alpha Vantage per l'ingestione di dati news");

    // Configura Alpha Vantage
    // NOTA: Sostituisci con la tua API key di Alpha Vantage
    let api_key = std::env::var("ALPHA_VANTAGE_API_KEY")
        .unwrap_or_else(|_| "YOUR_API_KEY_HERE".to_string());
    
    if api_key == "YOUR_API_KEY_HERE" {
        println!("⚠️  Attenzione: Imposta la variabile d'ambiente ALPHA_VANTAGE_API_KEY");
        println!("   Puoi ottenere una API key gratuita da: https://www.alphavantage.co/support/#api-key");
        println!("\n📝 Per testare senza API key, l'esempio mostrerà la struttura dei dati");
        
        // Simula dati di esempio
        let example_news = vec![
            AlphaVantageNewsItem {
                title: "Bitcoin Surges Past $50,000 as Institutional Adoption Grows".to_string(),
                url: "https://example.com/article1".to_string(),
                time_published: "20241201T143000".to_string(),
                authors: vec!["John Smith".to_string(), "Financial Times".to_string()],
                summary: "Bitcoin reaches new highs as institutional investors show increasing interest in cryptocurrency markets.".to_string(),
                banner_image: Some("https://example.com/image1.jpg".to_string()),
                source: "Financial Times".to_string(),
                category_within_source: "Finance".to_string(),
                source_domain: "ft.com".to_string(),
                topics: vec![
                    AlphaVantageTopic {
                        topic: "bitcoin".to_string(),
                        relevance_score: "0.95".to_string(),
                    },
                    AlphaVantageTopic {
                        topic: "cryptocurrency".to_string(),
                        relevance_score: "0.87".to_string(),
                    },
                ],
                overall_sentiment_score: Some(0.234),
                overall_sentiment_label: Some("positive".to_string()),
            },
            AlphaVantageNewsItem {
                title: "Ethereum 2.0 Upgrade Shows Promising Results".to_string(),
                url: "https://example.com/article2".to_string(),
                time_published: "20241201T120000".to_string(),
                authors: vec!["Jane Doe".to_string(), "Crypto News".to_string()],
                summary: "The latest Ethereum upgrade demonstrates improved scalability and reduced energy consumption.".to_string(),
                banner_image: Some("https://example.com/image2.jpg".to_string()),
                source: "Crypto News".to_string(),
                category_within_source: "Technology".to_string(),
                source_domain: "cryptonews.com".to_string(),
                topics: vec![
                    AlphaVantageTopic {
                        topic: "ethereum".to_string(),
                        relevance_score: "0.92".to_string(),
                    },
                    AlphaVantageTopic {
                        topic: "blockchain".to_string(),
                        relevance_score: "0.78".to_string(),
                    },
                ],
                overall_sentiment_score: Some(0.156),
                overall_sentiment_label: Some("positive".to_string()),
            },
        ];

        println!("✅ Dati di esempio generati:");
        for (i, article) in example_news.iter().enumerate() {
            println!("\n--- Articolo {} ---", i + 1);
            println!("📝 Titolo: {}", article.title);
            println!("👤 Autori: {}", article.authors.join(", "));
            println!("📅 Data: {}", article.time_published);
            println!("🏷️  Fonte: {}", article.source);
            println!("🌍 Dominio: {}", article.source_domain);
            if let Some(sentiment) = article.overall_sentiment_score {
                println!("😊 Sentiment: {:.3} ({})", sentiment, 
                    article.overall_sentiment_label.as_deref().unwrap_or("unknown"));
            }
            println!("🔗 URL: {}", article.url);
            println!("📊 Topics:");
            for topic in &article.topics {
                println!("  - {} (relevance: {})", topic.topic, topic.relevance_score);
            }
        }

        return Ok(());
    }

    let config = AlphaVantageConfig {
        api_key,
        ..Default::default()
    };

    let mut client = AlphaVantageClient::new(config);

    // Configura le keywords per la ricerca
    let keywords = vec![
        "economy".to_string(),
        "finance".to_string(),
        "crypto".to_string(),
        "bitcoin".to_string(),
        "ethereum".to_string(),
    ];

    println!("📰 Raccolta dati news da Alpha Vantage...");
    println!("🔍 Keywords: {:?}", keywords);

    // Raccogli dati news
    match client.collect_news_data(&keywords).await {
        Ok(news_data) => {
            println!("✅ Raccolti {} articoli news", news_data.len());
            
            // Mostra i primi 5 articoli
            for (i, article) in news_data.iter().take(5).enumerate() {
                println!("\n--- Articolo {} ---", i + 1);
                println!("📝 Titolo: {}", article.title);
                println!("👤 Autori: {}", article.authors.join(", "));
                println!("📅 Data: {}", article.time_published);
                println!("🏷️  Fonte: {}", article.source);
                println!("🌍 Dominio: {}", article.source_domain);
                if let Some(sentiment) = article.overall_sentiment_score {
                    println!("😊 Sentiment: {:.3} ({})", sentiment, 
                        article.overall_sentiment_label.as_deref().unwrap_or("unknown"));
                }
                println!("🔗 URL: {}", article.url);
                println!("📊 Topics:");
                for topic in &article.topics {
                    println!("  - {} (relevance: {})", topic.topic, topic.relevance_score);
                }
            }

            // Analizza il sentiment medio
            let sentiment_scores: Vec<f64> = news_data
                .iter()
                .filter_map(|a| a.overall_sentiment_score)
                .collect();
            
            if !sentiment_scores.is_empty() {
                let avg_sentiment = sentiment_scores.iter().sum::<f64>() / sentiment_scores.len() as f64;
                println!("\n😊 Sentiment medio: {:.3}", avg_sentiment);
                
                let positive_count = sentiment_scores.iter().filter(|&&s| s > 0.1).count();
                let negative_count = sentiment_scores.iter().filter(|&&s| s < -0.1).count();
                let neutral_count = sentiment_scores.len() - positive_count - negative_count;
                
                println!("  Positivi: {} ({:.1}%)", positive_count, 
                    (positive_count as f64 / sentiment_scores.len() as f64) * 100.0);
                println!("  Negativi: {} ({:.1}%)", negative_count,
                    (negative_count as f64 / sentiment_scores.len() as f64) * 100.0);
                println!("  Neutri: {} ({:.1}%)", neutral_count,
                    (neutral_count as f64 / sentiment_scores.len() as f64) * 100.0);
            }

        }
        Err(e) => {
            eprintln!("❌ Errore durante la raccolta dei dati: {}", e);
        }
    }

    // Esempio di raccolta dati di mercato
    println!("\n📈 Raccolta dati di mercato per Bitcoin...");
    match client.get_market_data("BTCUSD").await {
        Ok(market_data) => {
            if !market_data.is_empty() {
                println!("✅ Dati di mercato Bitcoin:");
                for (key, value) in market_data {
                    println!("  {}: {}", key, value);
                }
            } else {
                println!("⚠️  Nessun dato di mercato disponibile");
            }
        }
        Err(e) => {
            eprintln!("❌ Errore durante la raccolta dei dati di mercato: {}", e);
        }
    }

    println!("\n🎉 Esempio completato!");
    Ok(())
} 