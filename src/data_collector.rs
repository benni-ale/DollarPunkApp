use crate::models::*;
use anyhow::Result;
use chrono::Utc;
use reqwest::Client;
use scraper::{Html, Selector};
use std::collections::HashMap;
use tokio::time::{sleep, Duration};
use rand::Rng;
use rand::prelude::SliceRandom;

#[derive(Clone)]
pub struct DataCollector {
    cache: HashMap<String, DataPoint>,
}

impl DataCollector {
    pub fn new() -> Self {
        Self {
            cache: HashMap::new(),
        }
    }

    pub async fn collect_data(&mut self, config: &DataCollectionConfig) -> Result<Vec<DataPoint>> {
        let mut all_data = Vec::new();

        for source in &config.sources {
            if !source.enabled {
                continue;
            }

            match source.platform {
                Platform::Twitter => {
                    let twitter_data = self.collect_twitter_data(source, &config.filters).await?;
                    all_data.extend(twitter_data);
                }
                Platform::NewsWebsite => {
                    let news_data = self.collect_news_data(source, &config.filters).await?;
                    all_data.extend(news_data);
                }
                Platform::RSS => {
                    let rss_data = self.collect_rss_data(source, &config.filters).await?;
                    all_data.extend(rss_data);
                }
                Platform::Reddit => {
                    let reddit_data = self.collect_reddit_data(source, &config.filters).await?;
                    all_data.extend(reddit_data);
                }
                _ => {
                    // Simulated data for other platforms
                    let simulated_data = self.generate_simulated_data(source, &config.filters).await?;
                    all_data.extend(simulated_data);
                }
            }

            // Rate limiting
            sleep(Duration::from_millis(1000)).await;
        }

        Ok(all_data)
    }

    async fn collect_twitter_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        // Simulated Twitter data collection
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();

        for i in 0..50 {
            let content = self.generate_twitter_content(&filters.keywords);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);

            if self.matches_filters(&content, filters) {
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

        Ok(data)
    }

    async fn collect_news_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();

        // Try to fetch real news data
        let client = Client::new();
        if let Ok(response) = client.get(&source.url).send().await {
            if let Ok(html_content) = response.text().await {
                let document = Html::parse_document(&html_content);
                
                // Extract article titles and content
                if let Ok(title_selector) = Selector::parse("h1, h2, h3") {
                    for (i, element) in document.select(&title_selector).enumerate().take(20) {
                        let title = element.text().collect::<Vec<_>>().join(" ");
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
                }
            }
        }

        // If no real data, generate simulated data
        if data.is_empty() {
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

        Ok(data)
    }

    async fn collect_rss_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();

        // Try to fetch RSS feed
        let client = Client::new();
        if let Ok(response) = client.get(&source.url).send().await {
            if let Ok(rss_content) = response.text().await {
                // Simple RSS parsing
                let document = Html::parse_fragment(&rss_content);
                
                if let Ok(item_selector) = Selector::parse("item") {
                    for (i, element) in document.select(&item_selector).enumerate().take(25) {
                        let title = element.select(&Selector::parse("title").unwrap())
                            .next()
                            .map(|e| e.text().collect::<Vec<_>>().join(" "))
                            .unwrap_or_default();
                        
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
                }
            }
        }

        // Generate simulated RSS data if no real data
        if data.is_empty() {
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

        Ok(data)
    }

    async fn collect_reddit_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();

        for i in 0..40 {
            let content = self.generate_reddit_content(&filters.keywords);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);

            if self.matches_filters(&content, filters) {
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

        Ok(data)
    }

    async fn generate_simulated_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();

        for i in 0..30 {
            let content = self.generate_generic_content(&filters.keywords);
            let theme = self.classify_theme(&content);
            let language = self.detect_language(&content);

            if self.matches_filters(&content, filters) {
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

        Ok(data)
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
        
        format!("{} #{} #news", template.replace("{}", keyword), keyword)
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
} 