use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataPoint {
    pub id: String,
    pub content: String,
    pub platform: Platform,
    pub timestamp: DateTime<Utc>,
    pub theme: Theme,
    pub author: String,
    pub url: Option<String>,
    pub engagement_metrics: EngagementMetrics,
    pub language: String,
    pub sentiment_score: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum Platform {
    Twitter,
    Facebook,
    Instagram,
    LinkedIn,
    Reddit,
    NewsWebsite,
    RSS,
    YouTube,
    TikTok,
    Other(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum Theme {
    Politics,
    Economy,
    Technology,
    Sports,
    Entertainment,
    Health,
    Science,
    Environment,
    Education,
    Other(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngagementMetrics {
    pub likes: u32,
    pub shares: u32,
    pub comments: u32,
    pub views: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StratificationConfig {
    pub platform_weights: HashMap<Platform, f64>,
    pub theme_weights: HashMap<Theme, f64>,
    pub time_periods: Vec<TimePeriod>,
    pub min_samples_per_stratum: usize,
    pub max_samples_per_stratum: Option<usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimePeriod {
    pub name: String,
    pub start: DateTime<Utc>,
    pub end: DateTime<Utc>,
    pub weight: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Stratum {
    pub platform: Platform,
    pub theme: Theme,
    pub time_period: String,
    pub data_points: Vec<DataPoint>,
    pub target_sample_size: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SamplingResult {
    pub sampled_data: Vec<DataPoint>,
    pub stratification_stats: StratificationStats,
    pub export_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StratificationStats {
    pub total_original: usize,
    pub total_sampled: usize,
    pub stratum_counts: HashMap<String, usize>,
    pub balance_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataCollectionConfig {
    pub sources: Vec<DataSource>,
    pub collection_period: CollectionPeriod,
    pub filters: DataFilters,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataSource {
    pub name: String,
    pub platform: Platform,
    pub url: String,
    pub api_key: Option<String>,
    pub enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CollectionPeriod {
    pub start_date: DateTime<Utc>,
    pub end_date: DateTime<Utc>,
    pub interval_hours: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataFilters {
    pub keywords: Vec<String>,
    pub languages: Vec<String>,
    pub min_engagement: u32,
    pub exclude_retweets: bool,
    pub exclude_ads: bool,
}

impl Default for EngagementMetrics {
    fn default() -> Self {
        Self {
            likes: 0,
            shares: 0,
            comments: 0,
            views: 0,
        }
    }
}

impl Default for StratificationConfig {
    fn default() -> Self {
        let mut platform_weights = HashMap::new();
        platform_weights.insert(Platform::Twitter, 1.0);
        platform_weights.insert(Platform::Facebook, 1.0);
        platform_weights.insert(Platform::NewsWebsite, 1.0);
        platform_weights.insert(Platform::RSS, 1.0);

        let mut theme_weights = HashMap::new();
        theme_weights.insert(Theme::Politics, 1.0);
        theme_weights.insert(Theme::Economy, 1.0);
        theme_weights.insert(Theme::Technology, 1.0);
        theme_weights.insert(Theme::Other("General".to_string()), 1.0);

        Self {
            platform_weights,
            theme_weights,
            time_periods: vec![],
            min_samples_per_stratum: 10,
            max_samples_per_stratum: Some(100),
        }
    }
}

impl Default for DataCollectionConfig {
    fn default() -> Self {
        Self {
            sources: vec![],
            collection_period: CollectionPeriod {
                start_date: Utc::now() - chrono::Duration::days(7),
                end_date: Utc::now(),
                interval_hours: 24,
            },
            filters: DataFilters {
                keywords: vec!["economy".to_string(), "finance".to_string(), "crypto".to_string()],
                languages: vec!["it".to_string(), "en".to_string()],
                min_engagement: 10,
                exclude_retweets: true,
                exclude_ads: true,
            },
        }
    }
} 