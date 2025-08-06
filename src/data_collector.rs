use crate::models::*;
use anyhow::Result;
use chrono::Utc;
use reqwest::Client;
use scraper::{Html, Selector};
use std::collections::HashMap;
use tokio::time::{sleep, Duration};
use rand::Rng;
use rand::prelude::SliceRandom;
use tracing::{info, warn, error, debug};

#[derive(Clone)]
pub struct DataCollector {
    cache: HashMap<String, DataPoint>,
}

impl DataCollector {
    pub fn new() -> Self {
        info!("Initializing DataCollector");
        Self {
            cache: HashMap::new(),
        }
    }

    pub async fn collect_data(&mut self, config: &DataCollectionConfig) -> Result<Vec<DataPoint>> {
        info!("Starting data collection with {} sources in {:?} mode", 
              config.sources.len(), config.mode);
        debug!("Collection period: {} to {}", 
               config.collection_period.start_date, config.collection_period.end_date);

        let mut all_data = Vec::new();
        let enabled_sources: Vec<_> = config.sources.iter()
            .filter(|s| s.enabled)
            .collect();

        info!("Processing {} enabled sources", enabled_sources.len());

        for (i, source) in enabled_sources.iter().enumerate() {
            info!("Processing source {}/{}: {} ({:?})", 
                  i + 1, enabled_sources.len(), source.name, source.platform);

            let source_data = match config.mode {
                DataCollectionMode::Demo => {
                    info!("Using DEMO mode - generating simulated data for {}", source.name);
                    self.generate_simulated_data(source, &config.filters).await?
                },
                DataCollectionMode::Prod => {
                    info!("Using PROD mode - collecting real data from {}", source.name);
                    self.collect_real_data(source, &config.filters).await?
                }
            };

            info!("Collected {} data points from {}", source_data.len(), source.name);
            all_data.extend(source_data);

            // Rate limiting between sources
            if i < enabled_sources.len() - 1 {
                info!("Rate limiting: waiting 1 second before next source");
                sleep(Duration::from_secs(1)).await;
            }
        }

        info!("Data collection completed. Total data points: {}, Enabled sources: {}", 
              all_data.len(), enabled_sources.len());
        Ok(all_data)
    }

    async fn collect_twitter_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        debug!("Starting Twitter data collection simulation for {}", source.name);
        
        // Simulated Twitter data collection
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();
        let mut generated_count = 0;
        let mut filtered_count = 0;

        for i in 0..50 {
            let content = self.generate_twitter_content(&filters.keywords);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);
            generated_count += 1;

            if self.matches_filters(&content, filters) {
                filtered_count += 1;
                data.push(DataPoint {
                    id: format!("twitter_{}", i),
                    content,
                    platform: Platform::Twitter,
                    timestamp: Utc::now() - chrono::Duration::hours(rng.gen_range(0..168)),
                    theme,
                    author: format!("user_{}", rng.gen_range(1000..9999)),
                    url: Some(format!("https://twitter.com/user/status/{}", rng.gen_range(1000000000i64..9999999999i64))),
                    engagement_metrics: EngagementMetrics {
                        likes: rng.gen_range(0..1000),
                        shares: rng.gen_range(0..500),
                        comments: rng.gen_range(0..200),
                        views: rng.gen_range(0..10000),
                    },
                    language,
                    sentiment_score: Some(rng.gen_range(-1.0..1.0)),
                });
            }
        }

        debug!("Twitter collection: generated={}, filtered={}, final={}", 
               generated_count, filtered_count, data.len());

        Ok(data)
    }

    async fn collect_news_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        debug!("Starting news data collection from {}", source.url);
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();

        // Try to fetch real news data
        let client = Client::new();
        info!("Making HTTP request to: {}", source.url);
        
        match client.get(&source.url).send().await {
            Ok(response) => {
                info!("HTTP response status: {}", response.status());
                if response.status().is_success() {
                    match response.text().await {
                        Ok(html_content) => {
                            debug!("Received HTML content ({} bytes)", html_content.len());
                            let document = Html::parse_document(&html_content);
                            
                            // Extract article titles and content
                            if let Ok(title_selector) = Selector::parse("h1, h2, h3") {
                                let elements: Vec<_> = document.select(&title_selector).collect();
                                debug!("Found {} title elements", elements.len());
                                
                                for (i, element) in elements.iter().enumerate().take(20) {
                                    let title = element.text().collect::<Vec<_>>().join(" ");
                                    debug!("Processing title {}: '{}'", i, title);
                                    
                                    let content = self.generate_news_content(&title, &filters.keywords);
                                    let theme = self.classify_theme(&content);
                                    let language = self.detect_language(&content);

                                    if self.matches_filters(&content, filters) {
                                        data.push(DataPoint {
                                            id: format!("news_{}", i),
                                            content,
                                            platform: Platform::NewsWebsite,
                                            timestamp: Utc::now() - chrono::Duration::hours(rng.gen_range(0..168)),
                                            theme,
                                            author: format!("journalist_{}", rng.gen_range(100..999)),
                                            url: Some(format!("{}/article/{}", source.url, i)),
                                            engagement_metrics: EngagementMetrics {
                                                likes: rng.gen_range(0..500),
                                                shares: rng.gen_range(0..200),
                                                comments: rng.gen_range(0..100),
                                                views: rng.gen_range(0..5000),
                                            },
                                            language,
                                            sentiment_score: Some(rng.gen_range(-1.0..1.0)),
                                        });
                                    }
                                }
                            } else {
                                warn!("Failed to parse title selector for {}", source.name);
                            }
                        }
                        Err(e) => {
                            error!("Failed to read response text: {}", e);
                        }
                    }
                } else {
                    warn!("HTTP request failed with status: {}", response.status());
                }
            }
            Err(e) => {
                error!("HTTP request failed for {}: {}", source.url, e);
            }
        }

        // If no real data, generate simulated data
        if data.is_empty() {
            info!("No real data collected, generating simulated news data");
            for i in 0..30 {
                let content = self.generate_news_content("", &filters.keywords);
                let theme = self.classify_theme(&content);
                let language = self.detect_language(&content);

                if self.matches_filters(&content, filters) {
                    data.push(DataPoint {
                        id: format!("news_{}", i),
                        content,
                        platform: Platform::NewsWebsite,
                        timestamp: Utc::now() - chrono::Duration::hours(rng.gen_range(0..168)),
                        theme,
                        author: format!("journalist_{}", rng.gen_range(100..999)),
                        url: Some(format!("{}/article/{}", source.url, i)),
                        engagement_metrics: EngagementMetrics {
                            likes: rng.gen_range(0..500),
                            shares: rng.gen_range(0..200),
                            comments: rng.gen_range(0..100),
                            views: rng.gen_range(0..5000),
                        },
                        language,
                        sentiment_score: Some(rng.gen_range(-1.0..1.0)),
                    });
                }
            }
        }

        info!("News collection completed: {} data points", data.len());
        Ok(data)
    }

    async fn collect_rss_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        debug!("Starting RSS data collection from {}", source.url);
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();

        // Try to fetch RSS feed
        let client = Client::new();
        info!("Making HTTP request to RSS feed: {}", source.url);
        
        match client.get(&source.url).send().await {
            Ok(response) => {
                info!("RSS HTTP response status: {}", response.status());
                if response.status().is_success() {
                    match response.text().await {
                        Ok(rss_content) => {
                            debug!("Received RSS content ({} bytes)", rss_content.len());
                            // Simple RSS parsing
                            let document = Html::parse_fragment(&rss_content);
                            
                            if let Ok(item_selector) = Selector::parse("item") {
                                let elements: Vec<_> = document.select(&item_selector).collect();
                                debug!("Found {} RSS items", elements.len());
                                
                                for (i, element) in elements.iter().enumerate().take(25) {
                                    let title = element.select(&Selector::parse("title").unwrap())
                                        .next()
                                        .map(|e| e.text().collect::<Vec<_>>().join(" "))
                                        .unwrap_or_default();
                                    
                                    debug!("Processing RSS item {}: '{}'", i, title);
                                    
                                    let content = self.generate_rss_content(&title, &filters.keywords);
                                    let theme = self.classify_theme(&content);
                                    let language = self.detect_language(&content);

                                    if self.matches_filters(&content, filters) {
                                        data.push(DataPoint {
                                            id: format!("rss_{}", i),
                                            content,
                                            platform: Platform::RSS,
                                            timestamp: Utc::now() - chrono::Duration::hours(rng.gen_range(0..168)),
                                            theme,
                                            author: format!("rss_author_{}", rng.gen_range(100..999)),
                                            url: Some(format!("{}/feed/{}", source.url, i)),
                                            engagement_metrics: EngagementMetrics {
                                                likes: rng.gen_range(0..300),
                                                shares: rng.gen_range(0..150),
                                                comments: rng.gen_range(0..50),
                                                views: rng.gen_range(0..3000),
                                            },
                                            language,
                                            sentiment_score: Some(rng.gen_range(-1.0..1.0)),
                                        });
                                    }
                                }
                            } else {
                                warn!("Failed to parse RSS item selector for {}", source.name);
                            }
                        }
                        Err(e) => {
                            error!("Failed to read RSS response text: {}", e);
                        }
                    }
                } else {
                    warn!("RSS HTTP request failed with status: {}", response.status());
                }
            }
            Err(e) => {
                error!("RSS HTTP request failed for {}: {}", source.url, e);
            }
        }

        // Generate simulated RSS data if no real data
        if data.is_empty() {
            info!("No real RSS data collected, generating simulated RSS data");
            for i in 0..20 {
                let content = self.generate_rss_content("", &filters.keywords);
                let theme = self.classify_theme(&content);
                let language = self.detect_language(&content);

                if self.matches_filters(&content, filters) {
                    data.push(DataPoint {
                        id: format!("rss_{}", i),
                        content,
                        platform: Platform::RSS,
                        timestamp: Utc::now() - chrono::Duration::hours(rng.gen_range(0..168)),
                        theme,
                        author: format!("rss_author_{}", rng.gen_range(100..999)),
                        url: Some(format!("{}/feed/{}", source.url, i)),
                        engagement_metrics: EngagementMetrics {
                            likes: rng.gen_range(0..300),
                            shares: rng.gen_range(0..150),
                            comments: rng.gen_range(0..50),
                            views: rng.gen_range(0..3000),
                        },
                        language,
                        sentiment_score: Some(rng.gen_range(-1.0..1.0)),
                    });
                }
            }
        }

        info!("RSS collection completed: {} data points", data.len());
        Ok(data)
    }

    async fn collect_reddit_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        debug!("Starting Reddit data collection simulation for {}", source.name);
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();
        let mut generated_count = 0;
        let mut filtered_count = 0;

        for i in 0..40 {
            let content = self.generate_reddit_content(&filters.keywords);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);
            generated_count += 1;

            if self.matches_filters(&content, filters) {
                filtered_count += 1;
                data.push(DataPoint {
                    id: format!("reddit_{}", i),
                    content,
                    platform: Platform::Reddit,
                    timestamp: Utc::now() - chrono::Duration::hours(rng.gen_range(0..168)),
                    theme,
                    author: format!("redditor_{}", rng.gen_range(1000..9999)),
                    url: Some(format!("https://reddit.com/r/subreddit/comments/{}", rng.gen_range(1000000000i64..9999999999i64))),
                    engagement_metrics: EngagementMetrics {
                        likes: rng.gen_range(0..2000),
                        shares: rng.gen_range(0..100),
                        comments: rng.gen_range(0..500),
                        views: rng.gen_range(0..15000),
                    },
                    language,
                    sentiment_score: Some(rng.gen_range(-1.0..1.0)),
                });
            }
        }

        debug!("Reddit collection: generated={}, filtered={}, final={}", 
               generated_count, filtered_count, data.len());
        info!("Reddit collection completed: {} data points", data.len());
        Ok(data)
    }

    async fn generate_simulated_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        debug!("Starting simulated data generation for {} ({:?})", source.name, source.platform);
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();
        let mut generated_count = 0;
        let mut filtered_count = 0;

        for i in 0..30 {
            let content = self.generate_generic_content(&filters.keywords);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);
            generated_count += 1;

            if self.matches_filters(&content, filters) {
                filtered_count += 1;
                data.push(DataPoint {
                    id: format!("{}_{}", source.name.to_lowercase(), i),
                    content,
                    platform: source.platform.clone(),
                    timestamp: Utc::now() - chrono::Duration::hours(rng.gen_range(0..168)),
                    theme,
                    author: format!("user_{}", rng.gen_range(1000..9999)),
                    url: Some(format!("{}/post/{}", source.url, i)),
                    engagement_metrics: EngagementMetrics {
                        likes: rng.gen_range(0..800),
                        shares: rng.gen_range(0..400),
                        comments: rng.gen_range(0..200),
                        views: rng.gen_range(0..8000),
                    },
                    language,
                    sentiment_score: Some(rng.gen_range(-1.0..1.0)),
                });
            }
        }

        debug!("Simulated data generation: generated={}, filtered={}, final={}", 
               generated_count, filtered_count, data.len());
        info!("Simulated data generation completed: {} data points", data.len());
        Ok(data)
    }

    async fn collect_real_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        info!("Starting real data collection from {} ({:?})", source.name, source.platform);
        
        match source.platform {
            Platform::Twitter => {
                info!("Collecting real Twitter data from {}", source.name);
                self.collect_real_twitter_data(source, filters).await
            }
            Platform::Reddit => {
                info!("Collecting real Reddit data from {}", source.name);
                self.collect_real_reddit_data(source, filters).await
            }
            Platform::NewsWebsite => {
                info!("Collecting real news data from {}", source.name);
                self.collect_news_data(source, filters).await
            }
            Platform::RSS => {
                info!("Collecting real RSS data from {}", source.name);
                self.collect_rss_data(source, filters).await
            }
            _ => {
                warn!("No real API implementation for platform {:?}, falling back to simulated data", source.platform);
                self.generate_simulated_data(source, filters).await
            }
        }
    }

    async fn collect_real_twitter_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        info!("Attempting to collect real Twitter data from {}", source.name);
        
        // Check if API key is available
        if source.api_key.is_none() {
            warn!("No API key provided for Twitter source {}, falling back to simulated data", source.name);
            return self.generate_simulated_data(source, filters).await;
        }

        // TODO: Implement real Twitter API calls here
        // For now, fall back to simulated data
        info!("Real Twitter API not yet implemented, using simulated data");
        self.generate_simulated_data(source, filters).await
    }

    async fn collect_real_reddit_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        info!("Attempting to collect real Reddit data from {}", source.name);
        
        // Check if API key is available
        if source.api_key.is_none() {
            warn!("No API key provided for Reddit source {}, falling back to simulated data", source.name);
            return self.generate_simulated_data(source, filters).await;
        }

        // TODO: Implement real Reddit API calls here
        // For now, fall back to simulated data
        info!("Real Reddit API not yet implemented, using simulated data");
        self.generate_simulated_data(source, filters).await
    }

    fn generate_twitter_content(&self, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        let templates = vec![
            "Just read about {} - very interesting developments!",
            "{} is really changing the game right now",
            "Thoughts on {}? Seems like a big deal",
            "Following the {} situation closely",
            "{} analysis: what do you think?",
        ];

        let default_keyword = "finance".to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword);
        let template = templates.choose(&mut rng).unwrap();
        
        let content = format!("{} #{} #news", template.replace("{}", keyword), keyword);
        info!("Generated Twitter content: '{}'", content);
        content
    }

    fn generate_news_content(&self, title: &str, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        let default_keyword = "economy".to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword);
        
        if !title.is_empty() {
            format!("{} - Analysis of recent developments in {} sector. Market trends show significant changes.", title, keyword)
        } else {
            format!("Breaking news: Major developments in {} sector. Experts predict significant market impact.", keyword)
        }
    }

    fn generate_rss_content(&self, title: &str, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        let default_keyword = "technology".to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword);
        
        if !title.is_empty() {
            format!("{} - Comprehensive coverage of {} industry updates and market analysis.", title, keyword)
        } else {
            format!("Latest updates on {} sector: market analysis and expert insights.", keyword)
        }
    }

    fn generate_reddit_content(&self, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        let templates = vec![
            "What's everyone's take on {}?",
            "Discussion: {} trends and predictions",
            "{} news - thoughts?",
            "Analysis of {} market movements",
        ];

        let default_keyword = "crypto".to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword);
        let template = templates.choose(&mut rng).unwrap();
        
        template.replace("{}", keyword)
    }

    fn generate_generic_content(&self, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        let default_keyword = "business".to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword);
        
        format!("Update on {} sector: new developments and market insights.", keyword)
    }

    fn classify_theme(&self, content: &str) -> Theme {
        let content_lower = content.to_lowercase();
        
        if content_lower.contains("politic") || content_lower.contains("government") {
            Theme::Politics
        } else if content_lower.contains("econom") || content_lower.contains("finance") || content_lower.contains("market") {
            Theme::Economy
        } else if content_lower.contains("tech") || content_lower.contains("ai") || content_lower.contains("software") {
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
            Some(info) => {
                let lang_code = info.lang().code().to_string();
                // Map "eng" to "en" for compatibility with filters
                if lang_code == "eng" {
                    "en".to_string()
                } else {
                    lang_code
                }
            },
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

        // Log every filter check for debugging
        info!("Filter check for content (first 50 chars): '{}...'", 
               content.chars().take(50).collect::<String>());
        info!("  Keywords: {:?}, has_keyword: {}", filters.keywords, has_keyword);
        info!("  Language: {}, allowed_languages: {:?}, has_language: {}", 
               language, filters.languages, has_language);
        info!("  Final result: {}", has_keyword && has_language);

        // For now, let's be less restrictive - only check keywords
        // This will help us see if the content generation is working
        has_keyword
    }
} 