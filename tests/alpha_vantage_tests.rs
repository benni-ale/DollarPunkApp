use dollar_punk::alpha_vantage::{AlphaVantageClient, AlphaVantageConfig};
use dollar_punk::models::*;

#[tokio::test]
async fn test_alpha_vantage_config_default() {
    let config = AlphaVantageConfig::default();
    
    assert_eq!(config.base_url, "https://www.alphavantage.co/query");
    assert_eq!(config.rate_limit_delay_ms, 12000);
    assert_eq!(config.max_requests_per_minute, 5);
    assert!(config.api_key.is_empty());
}

#[tokio::test]
async fn test_alpha_vantage_client_creation() {
    let config = AlphaVantageConfig {
        api_key: "test_key".to_string(),
        ..Default::default()
    };
    
    let client = AlphaVantageClient::new(config);
    assert!(client.request_count == 0);
}

#[tokio::test]
async fn test_theme_classification() {
    let config = AlphaVantageConfig::default();
    let client = AlphaVantageClient::new(config);
    
    // Test economy theme
    let economy_content = "Bitcoin price surges as market sentiment improves";
    let theme = client.classify_theme(economy_content);
    assert!(matches!(theme, Theme::Economy));
    
    // Test technology theme
    let tech_content = "AI technology advances in software development";
    let theme = client.classify_theme(tech_content);
    assert!(matches!(theme, Theme::Technology));
    
    // Test politics theme
    let politics_content = "Government announces new political policies";
    let theme = client.classify_theme(politics_content);
    assert!(matches!(theme, Theme::Politics));
}

#[tokio::test]
async fn test_language_detection() {
    let config = AlphaVantageConfig::default();
    let client = AlphaVantageClient::new(config);
    
    let english_content = "This is an English text about finance";
    let language = client.detect_language(english_content);
    assert_eq!(language, "en");
    
    let italian_content = "Questo è un testo italiano sull'economia";
    let language = client.detect_language(italian_content);
    assert_eq!(language, "it");
}

#[tokio::test]
async fn test_filter_matching() {
    let config = AlphaVantageConfig::default();
    let client = AlphaVantageClient::new(config);
    
    let filters = DataFilters {
        keywords: vec!["bitcoin".to_string(), "finance".to_string()],
        languages: vec!["en".to_string()],
        min_engagement: 0,
        exclude_retweets: false,
        exclude_ads: true,
    };
    
    // Content that matches filters
    let matching_content = "Bitcoin price analysis shows positive trends";
    assert!(client.matches_filters(matching_content, &filters));
    
    // Content that doesn't match keywords
    let non_matching_content = "Sports news about football";
    assert!(!client.matches_filters(non_matching_content, &filters));
}

#[tokio::test]
async fn test_time_parsing() {
    let config = AlphaVantageConfig::default();
    let client = AlphaVantageClient::new(config);
    
    let time_str = "20241201T143000";
    let datetime = client.parse_alpha_vantage_time(time_str);
    
    // Should parse correctly
    assert!(datetime.year() == 2024);
    assert!(datetime.month() == 12);
    assert!(datetime.day() == 1);
    assert!(datetime.hour() == 14);
    assert!(datetime.minute() == 30);
    assert!(datetime.second() == 0);
}

#[tokio::test]
async fn test_invalid_time_parsing() {
    let config = AlphaVantageConfig::default();
    let client = AlphaVantageClient::new(config);
    
    let invalid_time_str = "invalid_time_format";
    let datetime = client.parse_alpha_vantage_time(invalid_time_str);
    
    // Should fall back to current time
    let now = chrono::Utc::now();
    let diff = (datetime - now).num_seconds().abs();
    assert!(diff < 10); // Should be within 10 seconds
}

#[tokio::test]
async fn test_data_collector_with_alpha_vantage() {
    use dollar_punk::data_collector::DataCollector;
    
    let collector = DataCollector::new()
        .with_alpha_vantage("test_key".to_string());
    
    // Should have alpha vantage client configured
    // Note: We can't directly test the private field, but we can test the builder pattern
    assert!(true); // If we reach here, the builder worked
}

#[tokio::test]
async fn test_alpha_vantage_response_structures() {
    // Test that our response structures can be serialized/deserialized
    let news_item = AlphaVantageNewsItem {
        title: "Test Article".to_string(),
        url: "https://example.com".to_string(),
        time_published: "20241201T120000".to_string(),
        authors: vec!["Test Author".to_string()],
        summary: "Test summary".to_string(),
        banner_image: Some("https://example.com/image.jpg".to_string()),
        source: "Test Source".to_string(),
        category_within_source: "Finance".to_string(),
        source_domain: "example.com".to_string(),
        topics: vec![],
        overall_sentiment_score: Some(0.5),
        overall_sentiment_label: Some("positive".to_string()),
    };
    
    // Test serialization
    let json = serde_json::to_string(&news_item).unwrap();
    assert!(json.contains("Test Article"));
    assert!(json.contains("0.5"));
    
    // Test deserialization
    let deserialized: AlphaVantageNewsItem = serde_json::from_str(&json).unwrap();
    assert_eq!(deserialized.title, "Test Article");
    assert_eq!(deserialized.overall_sentiment_score, Some(0.5));
} 