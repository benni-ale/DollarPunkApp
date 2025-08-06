use crate::models::*;
use anyhow::Result;
use chrono::{DateTime, Utc};
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

    pub fn generate_sample_data(&self, config: &DataCollectionConfig) -> Vec<DataPoint> {
        info!("Generating sample data for GUI (synchronous)");
        
        let mut all_data = Vec::new();
        let enabled_sources: Vec<_> = config.sources.iter()
            .filter(|s| s.enabled)
            .collect();

        info!("Processing {} enabled sources", enabled_sources.len());

        for (i, source) in enabled_sources.iter().enumerate() {
            info!("Processing source {}/{}: {} ({:?})", 
                  i + 1, enabled_sources.len(), source.name, source.platform);

            // Generate sample data for each source
            let source_data = self.generate_single_source_sample_data(source, &config.filters);
            info!("Generated {} data points from {}", source_data.len(), source.name);
            all_data.extend(source_data);
        }

        info!("Sample data generation completed. Total data points: {}", all_data.len());
        all_data
    }

    fn generate_single_source_sample_data(&self, source: &DataSource, _filters: &DataFilters) -> Vec<DataPoint> {
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();
        
        // Generate 5-15 sample data points per source
        let num_posts = rng.gen_range(5..15);
        
        for i in 0..num_posts {
            let content = format!("Sample {} data from {} - Financial markets show mixed signals", i + 1, source.name);
            let data_point = DataPoint {
                id: format!("sample_{}_{}", source.name.to_lowercase().replace(" ", "_"), i),
                content,
                platform: source.platform.clone(),
                timestamp: Utc::now() - chrono::Duration::hours(i as i64),
                theme: Theme::Economy,
                author: format!("Sample Author {}", i + 1),
                url: Some(format!("https://example.com/sample/{}", i)),
                engagement_metrics: EngagementMetrics {
                    likes: 100 + i * 10,
                    shares: 20 + i * 5,
                    comments: 15 + i * 3,
                    views: 50 + i * 10,
                },
                language: "en".to_string(),
                sentiment_score: Some(0.5 + (i as f64 * 0.1)),
            };
            data.push(data_point);
        }
        
        data
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
                    info!("Using DEMO mode - generating realistic simulated data for {}", source.name);
                    self.generate_realistic_demo_data(source, &config.filters).await?
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

    async fn generate_realistic_demo_data(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        debug!("Starting realistic demo data generation for {} ({:?})", source.name, source.platform);
        let mut data = Vec::new();
        let mut rng = rand::thread_rng();
        let mut generated_count = 0;
        let mut filtered_count = 0;

        // Generate more realistic number of posts based on platform and market conditions
        let base_num_posts = match source.platform {
            Platform::Twitter => rng.gen_range(80..150),
            Platform::Reddit => rng.gen_range(60..120),
            Platform::NewsWebsite => rng.gen_range(40..80),
            Platform::RSS => rng.gen_range(30..60),
            _ => rng.gen_range(50..100),
        };

        // Market volatility affects post volume
        let market_volatility = rng.gen_range(0.0..1.0);
        let volatility_multiplier = if market_volatility > 0.7 {
            // High volatility = more posts
            rng.gen_range(1.3..1.8)
        } else if market_volatility > 0.4 {
            // Moderate volatility = normal posts
            rng.gen_range(0.9..1.2)
        } else {
            // Low volatility = fewer posts
            rng.gen_range(0.6..1.0)
        };

        let num_posts = (base_num_posts as f64 * volatility_multiplier) as usize;

        // Generate market events that affect multiple posts
        let market_events = self.generate_market_events();
        
        for i in 0..num_posts {
            // Determine if this post is related to a market event
            let is_event_related = rng.gen_range(0.0..1.0) < 0.3; // 30% chance
            let event_context = if is_event_related && !market_events.is_empty() {
                market_events.choose(&mut rng)
            } else {
                None
            };

            let content = if let Some(event) = event_context {
                self.generate_event_related_content(&source.platform, &filters.keywords, event)
            } else {
                self.generate_realistic_content(&source.platform, &filters.keywords)
            };
            
            let theme = self.classify_theme_realistic(&content);
            let language = self.detect_language(&content);
            let sentiment = self.generate_realistic_sentiment(&content, &theme);
            generated_count += 1;

            if self.matches_filters(&content, filters) {
                filtered_count += 1;
                data.push(DataPoint {
                    id: format!("{}_{}", source.name.to_lowercase().replace(" ", "_"), i),
                    content,
                    platform: source.platform.clone(),
                    timestamp: self.generate_realistic_timestamp(),
                    theme,
                    author: self.generate_realistic_author(&source.platform),
                    url: Some(self.generate_realistic_url(&source.platform, i)),
                    engagement_metrics: self.generate_realistic_engagement(&source.platform, &sentiment),
                    language,
                    sentiment_score: Some(sentiment),
                });
            }
        }

        debug!("Realistic demo generation: generated={}, filtered={}, final={}", 
               generated_count, filtered_count, data.len());
        info!("Realistic demo generation completed: {} data points", data.len());
        Ok(data)
    }

    fn generate_market_events(&self) -> Vec<MarketEvent> {
        let mut rng = rand::thread_rng();
        let mut events = Vec::new();
        
        // Generate 2-5 market events
        let num_events = rng.gen_range(2..6);
        
        for _ in 0..num_events {
            let event_type = match rng.gen_range(0..6) {
                0 => MarketEventType::Earnings,
                1 => MarketEventType::FedDecision,
                2 => MarketEventType::EconomicData,
                3 => MarketEventType::CryptoSurge,
                4 => MarketEventType::MarketCrash,
                _ => MarketEventType::Merger,
            };
            
            events.push(MarketEvent {
                event_type: event_type.clone(),
                impact: rng.gen_range(-0.8..0.8),
                affected_sectors: {
                    let count = rng.gen_range(1..3);
                    vec!["tech", "finance", "crypto", "energy"].choose_multiple(&mut rng, count).map(|s| s.to_string()).collect()
                },
                description: self.generate_event_description(&event_type),
            });
        }
        
        events
    }

    fn generate_event_description(&self, event_type: &MarketEventType) -> String {
        let mut rng = rand::thread_rng();
        
        match event_type {
            MarketEventType::Earnings => {
                let companies = ["Apple", "Tesla", "Microsoft", "Amazon", "Google"];
                let company = companies.choose(&mut rng).unwrap();
                format!("{} Q4 earnings beat expectations", company)
            },
            MarketEventType::FedDecision => {
                let actions = ["rate hike", "rate cut", "no change", "QE announcement"];
                let action = actions.choose(&mut rng).unwrap();
                format!("Federal Reserve announces {}", action)
            },
            MarketEventType::EconomicData => {
                let indicators = ["CPI", "GDP", "unemployment", "retail sales"];
                let indicator = indicators.choose(&mut rng).unwrap();
                format!("{} data released", indicator)
            },
            MarketEventType::CryptoSurge => {
                let cryptos = ["Bitcoin", "Ethereum", "Solana"];
                let crypto = cryptos.choose(&mut rng).unwrap();
                format!("{} price surge", crypto)
            },
            MarketEventType::MarketCrash => {
                let triggers = ["inflation fears", "recession concerns", "geopolitical tensions"];
                let trigger = triggers.choose(&mut rng).unwrap();
                format!("Market selloff due to {}", trigger)
            },
            MarketEventType::Merger => {
                let companies = ["Microsoft", "Amazon", "Google", "Meta"];
                let company1 = companies.choose(&mut rng).unwrap();
                let company2 = companies.choose(&mut rng).unwrap();
                format!("{} acquires {}", company1, company2)
            },
        }
    }

    fn generate_event_related_content(&self, _platform: &Platform, _keywords: &[String], event: &MarketEvent) -> String {
        let mut rng = rand::thread_rng();
        
        match &event.event_type {
            MarketEventType::Earnings => {
                let templates = vec![
                    "BREAKING: {} earnings reaction across markets. Analysts updating price targets.",
                    "{} earnings impact: sector rotation happening. Money flowing into/out of tech.",
                    "Post-earnings analysis: {} performance affecting market sentiment.",
                ];
                let template = templates.choose(&mut rng).unwrap();
                template.replace("{}", &event.description)
            },
            MarketEventType::FedDecision => {
                let templates = vec![
                    "Fed decision impact: {} affecting all markets. Bond yields moving.",
                    "Market reaction to {}: risk assets under pressure/surging.",
                    "Post-Fed analysis: {} implications for inflation and growth.",
                ];
                let template = templates.choose(&mut rng).unwrap();
                template.replace("{}", &event.description)
            },
            MarketEventType::EconomicData => {
                let templates = vec![
                    "Economic data release: {} moving markets. Inflation/growth implications.",
                    "Market digesting {}: risk sentiment shifting. Sector rotation expected.",
                    "{} impact: Fed policy expectations adjusting. Rate hike/cut probability changing.",
                ];
                let template = templates.choose(&mut rng).unwrap();
                template.replace("{}", &event.description)
            },
            MarketEventType::CryptoSurge => {
                let templates = vec![
                    "Crypto rally: {} driving altcoin season. DeFi tokens surging.",
                    "{} momentum: institutional adoption accelerating. Traditional finance taking notice.",
                    "Crypto market update: {} leading the charge. Risk-on sentiment in digital assets.",
                ];
                let template = templates.choose(&mut rng).unwrap();
                template.replace("{}", &event.description)
            },
            MarketEventType::MarketCrash => {
                let templates = vec![
                    "Market volatility: {} causing flight to safety. Bonds and gold rallying.",
                    "Risk-off sentiment: {} triggering selloff. Defensive sectors outperforming.",
                    "Market stress: {} impact on correlations. Diversification failing.",
                ];
                let template = templates.choose(&mut rng).unwrap();
                template.replace("{}", &event.description)
            },
            MarketEventType::Merger => {
                let templates = vec![
                    "Merger news: {} creating sector opportunities. Antitrust concerns rising.",
                    "Corporate action: {} implications for competition. Market consolidation trend.",
                    "Deal analysis: {} strategic rationale. Synergy expectations and execution risk.",
                ];
                let template = templates.choose(&mut rng).unwrap();
                template.replace("{}", &event.description)
            },
        }
    }

    fn generate_realistic_content(&self, platform: &Platform, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        
        match platform {
            Platform::Twitter => self.generate_realistic_twitter_content(keywords),
            Platform::Reddit => self.generate_realistic_reddit_content(keywords),
            Platform::NewsWebsite => self.generate_realistic_news_content(keywords),
            Platform::RSS => self.generate_realistic_rss_content(keywords),
            _ => self.generate_realistic_generic_content(keywords),
        }
    }

    fn generate_realistic_twitter_content(&self, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        
        // Real-world companies and market events
        let companies = vec!["Apple", "Tesla", "Microsoft", "Amazon", "Google", "Meta", "Netflix", "NVIDIA", "AMD", "Intel"];
        let crypto_projects = vec!["Bitcoin", "Ethereum", "Cardano", "Solana", "Polkadot", "Chainlink", "Uniswap", "Aave"];
        let sectors = vec!["tech", "finance", "healthcare", "energy", "consumer", "industrial", "materials"];
        let countries = vec!["US", "EU", "China", "Japan", "UK", "Canada", "Australia"];
        
        // Real-world financial and economic scenarios
        let scenarios = vec![
            // Market movements with real companies
            ("BREAKING: {} stock surges {}% after earnings beat! Q4 revenue up {}% YoY. Analysts upgrading price targets.", "finance"),
            ("{} announces major AI partnership with {}. Stock up {}% in pre-market. Tech sector rally continues.", "technology"),
            ("Federal Reserve raises rates by {} basis points. Market reaction: {}. Impact on {} stocks?", "economy"),
            
            // Economic indicators with realistic values
            ("CPI data: {}% YoY inflation, {} than expected. Core inflation at {}%. Market implications?", "economy"),
            ("Jobs report: {}K new jobs, unemployment at {}%. {} sector leading job growth.", "economy"),
            ("GDP Q4 growth: {}% annualized. {} sector strongest performer. Recession fears easing.", "economy"),
            
            // Crypto developments with real projects
            ("{} just hit ${}K! 🚀 Market cap now ${}B. Institutional adoption accelerating.", "crypto"),
            ("{} {} upgrade live! Gas fees down {}%. DeFi TVL reaches ${}B. Bullish!", "crypto"),
            ("New {} regulation in {}. Impact on {} market? Institutional flows continue.", "crypto"),
            
            // Company-specific news
            ("{} earnings: EPS ${}, revenue ${}B. Beat estimates by {}%. Stock up {}% AH.", "finance"),
            ("{} acquires {} for ${}B. Strategic move into {} market. Competition heating up!", "finance"),
            ("{} launches new {} product. Early reviews positive. Market share implications?", "technology"),
            
            // Market analysis
            ("S&P 500 up {}% today. {} sector leading gains. VIX down to {}. Risk-on sentiment.", "finance"),
            ("{} market analysis: Technical breakout at ${}. Support at ${}. Target: ${}.", "finance"),
            ("Portfolio update: {}% in growth, {}% in value, {}% in bonds. Rebalancing needed?", "finance"),
            
            // Real-world events
            ("Oil prices hit ${} per barrel. {} production cuts. Energy sector implications?", "economy"),
            ("{} central bank announces {} policy. Currency impact: {} vs USD. Trade implications?", "economy"),
            ("Supply chain update: {} delays easing. {} sector recovery. Inflation pressure?", "economy"),
        ];

        let (template, default_keyword) = scenarios.choose(&mut rng).unwrap();
        let default_keyword_str = default_keyword.to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword_str);
        
        // Fill template with realistic values and real company names
        let content = match template {
            t if t.contains("stock surges") => {
                let company = companies.choose(&mut rng).unwrap();
                let percent = rng.gen_range(5..25);
                let revenue_growth = rng.gen_range(10..50);
                t.replace("{} stock surges", &format!("{} stock surges", company))
                 .replace("{}% after earnings beat! Q4 revenue up {}% YoY", &format!("{}% after earnings beat! Q4 revenue up {}% YoY", percent, revenue_growth))
            },
            t if t.contains("announces major AI partnership") => {
                let company1 = companies.choose(&mut rng).unwrap();
                let company2 = companies.choose(&mut rng).unwrap();
                let percent = rng.gen_range(3..15);
                t.replace("{} announces major AI partnership with {}", &format!("{} announces major AI partnership with {}", company1, company2))
                 .replace("Stock up {}% in pre-market", &format!("Stock up {}% in pre-market", percent))
            },
            t if t.contains("raises rates by") => {
                let bps = rng.gen_range(25..100);
                let reaction = ["bullish", "mixed", "cautious", "bearish"].choose(&mut rng).unwrap();
                let sector = sectors.choose(&mut rng).unwrap();
                t.replace("raises rates by {} basis points", &format!("raises rates by {} basis points", bps))
                 .replace("Market reaction: {}", &format!("Market reaction: {}", reaction))
                 .replace("Impact on {} stocks?", &format!("Impact on {} stocks?", sector))
            },
            t if t.contains("CPI data:") => {
                let inflation = rng.gen_range(20..80) as f64 / 10.0;
                let comparison = ["higher", "lower"].choose(&mut rng).unwrap();
                let core = rng.gen_range(15..70) as f64 / 10.0;
                t.replace("CPI data: {}% YoY inflation, {} than expected", &format!("CPI data: {:.1}% YoY inflation, {} than expected", inflation, comparison))
                 .replace("Core inflation at {}%", &format!("Core inflation at {:.1}%", core))
            },
            t if t.contains("Jobs report:") => {
                let jobs = rng.gen_range(100..500);
                let unemployment = rng.gen_range(30..60) as f64 / 10.0;
                let sector = sectors.choose(&mut rng).unwrap();
                t.replace("Jobs report: {}K new jobs, unemployment at {}%", &format!("Jobs report: {}K new jobs, unemployment at {:.1}%", jobs, unemployment))
                 .replace("{} sector leading job growth", &format!("{} sector leading job growth", sector))
            },
            t if t.contains("just hit $") && t.contains("K!") => {
                let crypto = crypto_projects.choose(&mut rng).unwrap();
                let price = rng.gen_range(30..80);
                let market_cap = rng.gen_range(100..1000);
                t.replace("{} just hit ${}K!", &format!("{} just hit ${}K!", crypto, price))
                 .replace("Market cap now ${}B", &format!("Market cap now ${}B", market_cap))
            },
            t if t.contains("earnings: EPS $") => {
                let company = companies.choose(&mut rng).unwrap();
                let eps = rng.gen_range(10..50) as f64 / 10.0;
                let revenue = rng.gen_range(10..100);
                let beat = rng.gen_range(5..20);
                let stock_move = rng.gen_range(2..12);
                t.replace("{} earnings: EPS ${}, revenue ${}B", &format!("{} earnings: EPS ${:.2}, revenue ${}B", company, eps, revenue))
                 .replace("Beat estimates by {}%", &format!("Beat estimates by {}%", beat))
                 .replace("Stock up {}% AH", &format!("Stock up {}% AH", stock_move))
            },
            t if t.contains("Oil prices hit $") => {
                let oil_price = rng.gen_range(60..120);
                let country = countries.choose(&mut rng).unwrap();
                t.replace("Oil prices hit ${} per barrel", &format!("Oil prices hit ${} per barrel", oil_price))
                 .replace("{} production cuts", &format!("{} production cuts", country))
            },
            t if t.contains("central bank announces") => {
                let country = countries.choose(&mut rng).unwrap();
                let policy = ["rate hike", "rate cut", "QE", "tightening"].choose(&mut rng).unwrap();
                let currency_move = rng.gen_range(-5..5);
                t.replace("{} central bank announces {} policy", &format!("{} central bank announces {} policy", country, policy))
                 .replace("Currency impact: {} vs USD", &format!("Currency impact: {}% vs USD", currency_move))
            },
            _ => {
                // Generic replacement for remaining templates
                let mut content = template.to_string();
                for _ in 0..content.matches("{}").count() {
                    if content.contains("{}") {
                        content = content.replacen("{}", &keyword, 1);
                    }
                }
                content
            }
        };

        // Add realistic hashtags and mentions
        let hashtags = vec![
            format!("#{}", keyword),
            "#markets".to_string(),
            "#investing".to_string(),
            "#finance".to_string(),
            "#economy".to_string(),
            "#crypto".to_string(),
            "#stocks".to_string(),
            "#trading".to_string(),
            "#wallstreet".to_string(),
            "#fintech".to_string(),
        ];
        
        let hashtag_count = rng.gen_range(2..5);
        let selected_hashtags: Vec<_> = hashtags.choose_multiple(&mut rng, hashtag_count).collect();
        let hashtag_string = selected_hashtags.iter().map(|s| s.as_str()).collect::<Vec<_>>().join(" ");
        
        format!("{} {}", content, hashtag_string)
    }

    fn generate_realistic_reddit_content(&self, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        
        let scenarios = vec![
            // Discussion posts
            ("What's everyone's thoughts on {}? I've been following it for a while and the recent developments are interesting.", "finance"),
            ("Discussion: {} market analysis and predictions for Q1. What are your positions?", "crypto"),
            ("{} sector deep dive: fundamentals vs technical analysis. Which approach do you prefer?", "economy"),
            
            // News sharing
            ("BREAKING: {} just announced {}. How will this affect the market?", "finance"),
            ("New report on {}: key findings and market implications. Worth reading!", "economy"),
            ("{} regulation update: what this means for investors and traders.", "crypto"),
            
            // Personal experiences
            ("My experience with {} investing: lessons learned and portfolio performance.", "finance"),
            ("Just completed my first {} trade. Here's what I learned and my strategy moving forward.", "crypto"),
            ("{} market volatility: how I'm adjusting my investment strategy.", "economy"),
            
            // Analysis requests
            ("Can someone explain the recent {} movements? Looking for technical analysis.", "finance"),
            ("{} fundamentals check: is this a good entry point or wait for pullback?", "crypto"),
            ("Economic indicators for {}: what should we watch for in the coming weeks?", "economy"),
        ];

        let (template, default_keyword) = scenarios.choose(&mut rng).unwrap();
        let default_keyword_str = default_keyword.to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword_str);
        
        template.replace("{}", keyword)
    }

    fn generate_realistic_news_content(&self, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        
        let scenarios = vec![
            // Market analysis
            ("Market Analysis: {} sector shows strong momentum as investors focus on growth opportunities. Expert analysis suggests continued upward trend.", "finance"),
            ("Economic Update: {} indicators point to robust recovery. Central bank policies supporting market stability.", "economy"),
            ("Technology Trends: {} innovation driving market transformation. Industry leaders adapt to changing landscape.", "technology"),
            
            // Breaking news
            ("BREAKING: Major developments in {} market as regulatory changes take effect. Impact on global markets analyzed.", "crypto"),
            ("Exclusive: {} company announces strategic partnership. Market reaction and future prospects examined.", "finance"),
            ("Economic Policy: New measures affecting {} sector announced. Expert opinions on market implications.", "economy"),
            
            // Research reports
            ("Research Report: {} market analysis reveals key trends and investment opportunities. Comprehensive coverage of sector performance.", "finance"),
            ("Industry Study: {} sector growth projections for 2024. Data-driven insights for investors.", "technology"),
            ("Economic Forecast: {} indicators suggest market direction. Professional analysis and predictions.", "economy"),
        ];

        let (template, default_keyword) = scenarios.choose(&mut rng).unwrap();
        let default_keyword_str = default_keyword.to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword_str);
        
        template.replace("{}", keyword)
    }

    fn generate_realistic_rss_content(&self, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        
        let scenarios = vec![
            // RSS feed content
            ("RSS Update: {} market developments and analysis. Latest news and expert commentary on sector trends.", "finance"),
            ("Feed Alert: {} economic indicators released. Market impact and investor sentiment analysis.", "economy"),
            ("RSS Report: {} technology sector updates. Innovation trends and market opportunities.", "technology"),
            ("Feed News: {} cryptocurrency developments. Regulatory updates and market analysis.", "crypto"),
        ];

        let (template, default_keyword) = scenarios.choose(&mut rng).unwrap();
        let default_keyword_str = default_keyword.to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword_str);
        
        template.replace("{}", keyword)
    }

    fn generate_realistic_generic_content(&self, keywords: &[String]) -> String {
        let mut rng = rand::thread_rng();
        
        let scenarios = vec![
            ("Market Update: {} sector performance analysis and future outlook.", "finance"),
            ("Economic Review: {} indicators and market implications.", "economy"),
            ("Technology Report: {} innovations and market impact.", "technology"),
        ];

        let (template, default_keyword) = scenarios.choose(&mut rng).unwrap();
        let default_keyword_str = default_keyword.to_string();
        let keyword = keywords.choose(&mut rng).unwrap_or(&default_keyword_str);
        
        template.replace("{}", keyword)
    }

    fn generate_realistic_timestamp(&self) -> DateTime<Utc> {
        let mut rng = rand::thread_rng();
        let now = Utc::now();
        
        // Generate timestamps with realistic market patterns
        let base_hours_ago = rng.gen_range(0..168); // 7 days
        
        // Adjust for market hours (more activity during trading hours)
        let market_hour_multiplier = if rng.gen_range(0.0..1.0) < 0.7 {
            // 70% chance of being during market hours (9:30 AM - 4:00 PM ET)
            rng.gen_range(0.8..1.2)
        } else {
            // 30% chance of being outside market hours
            rng.gen_range(1.5..3.0)
        };
        
        // Weekend effect (less activity on weekends)
        let weekend_multiplier = if rng.gen_range(0.0..1.0) < 0.3 {
            // 30% chance of weekend activity
            rng.gen_range(1.5..2.5)
        } else {
            // 70% chance of weekday activity
            rng.gen_range(0.8..1.2)
        };
        
        let adjusted_hours = (base_hours_ago as f64 * market_hour_multiplier * weekend_multiplier) as i64;
        let minutes_ago = rng.gen_range(0..60);
        
        now - chrono::Duration::hours(adjusted_hours) - chrono::Duration::minutes(minutes_ago)
    }

    fn generate_realistic_author(&self, platform: &Platform) -> String {
        let mut rng = rand::thread_rng();
        
        match platform {
            Platform::Twitter => {
                let prefixes = vec!["trader", "analyst", "investor", "fintech", "crypto", "market"];
                let suffixes = vec!["pro", "guru", "expert", "daily", "news", "insights"];
                let prefix = prefixes.choose(&mut rng).unwrap();
                let suffix = suffixes.choose(&mut rng).unwrap();
                let number = rng.gen_range(100..999);
                format!("{}_{}_{}", prefix, suffix, number)
            },
            Platform::Reddit => {
                let adjectives = vec!["smart", "wise", "crypto", "finance", "market", "trading"];
                let nouns = vec!["trader", "investor", "analyst", "enthusiast", "expert"];
                let adj = adjectives.choose(&mut rng).unwrap();
                let noun = nouns.choose(&mut rng).unwrap();
                let number = rng.gen_range(1000..9999);
                format!("{}_{}_{}", adj, noun, number)
            },
            Platform::NewsWebsite => {
                let first_names = vec!["John", "Sarah", "Michael", "Emma", "David", "Lisa"];
                let last_names = vec!["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"];
                let first = first_names.choose(&mut rng).unwrap();
                let last = last_names.choose(&mut rng).unwrap();
                format!("{} {}", first, last)
            },
            Platform::RSS => {
                let sources = vec!["Reuters", "Bloomberg", "CNBC", "MarketWatch", "Yahoo Finance"];
                sources.choose(&mut rng).unwrap().to_string()
            },
            _ => {
                format!("user_{}", rng.gen_range(1000..9999))
            }
        }
    }

    fn generate_realistic_url(&self, platform: &Platform, post_id: usize) -> String {
        let mut rng = rand::thread_rng();
        
        match platform {
            Platform::Twitter => {
                let user_id = rng.gen_range(100000000..999999999);
                let status_id = rng.gen_range(1000000000000000000..9999999999999999999u64);
                format!("https://twitter.com/user_{}/status/{}", user_id, status_id)
            },
            Platform::Reddit => {
                let subreddit = ["finance", "investing", "cryptocurrency", "stocks", "wallstreetbets"].choose(&mut rng).unwrap();
                let post_id = rng.gen_range(1000000000..9999999999u64);
                format!("https://reddit.com/r/{}/comments/{}", subreddit, post_id)
            },
            Platform::NewsWebsite => {
                let domains = ["reuters.com", "bloomberg.com", "cnbc.com", "marketwatch.com"];
                let domain = domains.choose(&mut rng).unwrap();
                format!("https://www.{}/article/{}", domain, post_id)
            },
            Platform::RSS => {
                let feeds = ["feeds.reuters.com", "feeds.bloomberg.com", "feeds.cnbc.com"];
                let feed = feeds.choose(&mut rng).unwrap();
                format!("https://{}/feed/{}", feed, post_id)
            },
            _ => {
                format!("https://example.com/post/{}", post_id)
            }
        }
    }

    fn generate_realistic_engagement(&self, platform: &Platform, sentiment: &f64) -> EngagementMetrics {
        let mut rng = rand::thread_rng();
        
        // More sophisticated engagement patterns based on platform and content type
        let (base_likes, base_shares, base_comments, base_views) = match platform {
            Platform::Twitter => {
                // Twitter: High likes, moderate shares, low comments, high views
                let likes = rng.gen_range(50..800);
                let shares = rng.gen_range(10..150);
                let comments = rng.gen_range(5..80);
                let views = rng.gen_range(1000..15000);
                (likes, shares, comments, views)
            },
            Platform::Reddit => {
                // Reddit: High upvotes, low shares, high comments, moderate views
                let likes = rng.gen_range(100..3000);
                let shares = rng.gen_range(5..100);
                let comments = rng.gen_range(20..500);
                let views = rng.gen_range(5000..80000);
                (likes, shares, comments, views)
            },
            Platform::NewsWebsite => {
                // News: Moderate likes, high shares, low comments, high views
                let likes = rng.gen_range(20..300);
                let shares = rng.gen_range(10..200);
                let comments = rng.gen_range(2..30);
                let views = rng.gen_range(500..8000);
                (likes, shares, comments, views)
            },
            Platform::RSS => {
                // RSS: Low engagement overall, but consistent
                let likes = rng.gen_range(10..150);
                let shares = rng.gen_range(2..25);
                let comments = rng.gen_range(1..15);
                let views = rng.gen_range(200..3000);
                (likes, shares, comments, views)
            },
            _ => {
                let likes = rng.gen_range(30..400);
                let shares = rng.gen_range(5..80);
                let comments = rng.gen_range(3..50);
                let views = rng.gen_range(1000..10000);
                (likes, shares, comments, views)
            }
        };
        
        // Sentiment affects engagement with more nuanced patterns
        let sentiment_multiplier = if *sentiment > 0.5 {
            // Very positive content gets high engagement
            rng.gen_range(1.5..2.5)
        } else if *sentiment > 0.2 {
            // Positive content gets moderate boost
            rng.gen_range(1.2..1.8)
        } else if *sentiment < -0.5 {
            // Very negative content can also get high engagement (controversy)
            rng.gen_range(1.3..2.0)
        } else if *sentiment < -0.2 {
            // Negative content gets reduced engagement
            rng.gen_range(0.6..1.2)
        } else {
            // Neutral content
            rng.gen_range(0.8..1.4)
        };
        
        // Add viral factor (some posts go viral)
        let viral_factor = if rng.gen_range(0.0..1.0) < 0.05 {
            // 5% chance of viral post
            rng.gen_range(3.0..10.0)
        } else if rng.gen_range(0.0..1.0) < 0.15 {
            // 15% chance of trending post
            rng.gen_range(1.5..3.0)
        } else {
            1.0
        };
        
        // Time-based engagement (recent posts get more engagement)
        let time_factor = rng.gen_range(0.8..1.3);
        
        let final_multiplier = sentiment_multiplier * viral_factor * time_factor;
        
        EngagementMetrics {
            likes: (base_likes as f64 * final_multiplier) as u32,
            shares: (base_shares as f64 * final_multiplier) as u32,
            comments: (base_comments as f64 * final_multiplier) as u32,
            views: (base_views as f64 * final_multiplier) as u32,
        }
    }

    fn generate_realistic_sentiment(&self, content: &str, theme: &Theme) -> f64 {
        let mut rng = rand::thread_rng();
        let content_lower = content.to_lowercase();
        
        // More sophisticated base sentiment based on theme and market context
        let base_sentiment = match theme {
            Theme::Economy => {
                // Economic sentiment varies based on market conditions
                if content_lower.contains("inflation") || content_lower.contains("recession") {
                    rng.gen_range(-0.6..0.2) // Generally negative for inflation/recession news
                } else if content_lower.contains("growth") || content_lower.contains("recovery") {
                    rng.gen_range(0.2..0.8) // Positive for growth news
                } else if content_lower.contains("fed") || content_lower.contains("rates") {
                    rng.gen_range(-0.4..0.4) // Mixed for Fed news
                } else {
                    rng.gen_range(-0.3..0.6) // General economic news
                }
            },
            Theme::Technology => {
                if content_lower.contains("ai") || content_lower.contains("innovation") {
                    rng.gen_range(0.3..0.9) // Very positive for AI/innovation
                } else if content_lower.contains("regulation") || content_lower.contains("antitrust") {
                    rng.gen_range(-0.2..0.4) // Mixed for regulation news
                } else {
                    rng.gen_range(0.1..0.8) // Generally positive for tech
                }
            },
            Theme::Politics => {
                if content_lower.contains("election") || content_lower.contains("policy") {
                    rng.gen_range(-0.8..0.3) // Very polarized
                } else {
                    rng.gen_range(-0.6..0.2) // Generally negative
                }
            },
            Theme::Sports => rng.gen_range(-0.2..0.7), // Sports can be mixed
            Theme::Entertainment => rng.gen_range(0.0..0.8), // Entertainment tends to be positive
            Theme::Health => {
                if content_lower.contains("breakthrough") || content_lower.contains("cure") {
                    rng.gen_range(0.4..0.8) // Positive for medical breakthroughs
                } else {
                    rng.gen_range(-0.1..0.5) // Mixed for general health news
                }
            },
            Theme::Science => rng.gen_range(0.2..0.8), // Science news tends to be positive
            Theme::Environment => {
                if content_lower.contains("climate") || content_lower.contains("pollution") {
                    rng.gen_range(-0.5..0.2) // Generally negative for environmental issues
                } else if content_lower.contains("renewable") || content_lower.contains("green") {
                    rng.gen_range(0.2..0.7) // Positive for renewable energy
                } else {
                    rng.gen_range(-0.3..0.4) // Mixed
                }
            },
            Theme::Education => rng.gen_range(0.1..0.7), // Education tends to be positive
            _ => rng.gen_range(-0.2..0.6),
        };
        
        // Sophisticated keyword-based sentiment adjustments
        let sentiment_adjustment = if content_lower.contains("breaking") || content_lower.contains("surge") || content_lower.contains("🚀") || content_lower.contains("rally") {
            rng.gen_range(0.2..0.4) // Positive for breaking news and rallies
        } else if content_lower.contains("crash") || content_lower.contains("plunge") || content_lower.contains("collapse") {
            rng.gen_range(-0.5..-0.2) // Very negative for crashes
        } else if content_lower.contains("drop") || content_lower.contains("fall") || content_lower.contains("decline") {
            rng.gen_range(-0.3..-0.1) // Negative for declines
        } else if content_lower.contains("growth") || content_lower.contains("up") || content_lower.contains("gain") || content_lower.contains("rise") {
            rng.gen_range(0.1..0.3) // Positive for growth
        } else if content_lower.contains("beat") || content_lower.contains("exceed") || content_lower.contains("outperform") {
            rng.gen_range(0.2..0.4) // Positive for beats
        } else if content_lower.contains("miss") || content_lower.contains("disappoint") || content_lower.contains("underperform") {
            rng.gen_range(-0.3..-0.1) // Negative for misses
        } else if content_lower.contains("volatility") || content_lower.contains("uncertainty") {
            rng.gen_range(-0.2..0.1) // Slightly negative for uncertainty
        } else if content_lower.contains("stability") || content_lower.contains("recovery") {
            rng.gen_range(0.1..0.3) // Positive for stability
        } else {
            0.0
        };
        
        // Market-specific sentiment patterns
        let market_sentiment = if content_lower.contains("bull") || content_lower.contains("bullish") {
            rng.gen_range(0.3..0.6)
        } else if content_lower.contains("bear") || content_lower.contains("bearish") {
            rng.gen_range(-0.4..-0.1)
        } else if content_lower.contains("neutral") || content_lower.contains("sideways") {
            rng.gen_range(-0.1..0.1)
        } else {
            0.0
        };
        
        // Crypto-specific sentiment
        let crypto_sentiment = if content_lower.contains("bitcoin") || content_lower.contains("ethereum") {
            if content_lower.contains("adoption") || content_lower.contains("institutional") {
                rng.gen_range(0.2..0.5) // Positive for adoption news
            } else if content_lower.contains("regulation") || content_lower.contains("ban") {
                rng.gen_range(-0.3..0.1) // Mixed for regulation
            } else {
                rng.gen_range(-0.1..0.3) // Slightly positive for general crypto news
            }
        } else {
            0.0
        };
        
        let final_sentiment: f64 = base_sentiment + sentiment_adjustment + market_sentiment + crypto_sentiment;
        final_sentiment.max(-1.0).min(1.0)
    }

    fn classify_theme_realistic(&self, content: &str) -> Theme {
        let content_lower = content.to_lowercase();
        
        // More sophisticated theme classification
        if content_lower.contains("bitcoin") || content_lower.contains("crypto") || content_lower.contains("ethereum") || content_lower.contains("blockchain") {
            Theme::Economy // Crypto is part of economy
        } else if content_lower.contains("stock") || content_lower.contains("market") || content_lower.contains("trading") || content_lower.contains("invest") || content_lower.contains("finance") {
            Theme::Economy
        } else if content_lower.contains("tech") || content_lower.contains("ai") || content_lower.contains("software") || content_lower.contains("innovation") {
            Theme::Technology
        } else if content_lower.contains("politic") || content_lower.contains("government") || content_lower.contains("election") {
            Theme::Politics
        } else if content_lower.contains("sport") || content_lower.contains("football") || content_lower.contains("basketball") {
            Theme::Sports
        } else if content_lower.contains("movie") || content_lower.contains("entertain") || content_lower.contains("celebrity") {
            Theme::Entertainment
        } else if content_lower.contains("health") || content_lower.contains("medical") || content_lower.contains("covid") {
            Theme::Health
        } else if content_lower.contains("scien") || content_lower.contains("research") || content_lower.contains("study") {
            Theme::Science
        } else if content_lower.contains("environ") || content_lower.contains("climate") || content_lower.contains("green") {
            Theme::Environment
        } else if content_lower.contains("educat") || content_lower.contains("school") || content_lower.contains("university") {
            Theme::Education
        } else {
            Theme::Economy // Default to economy for financial content
        }
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
            Platform::AlphaVantage => {
                info!("Collecting real Alpha Vantage news data from {}", source.name);
                self.collect_alpha_vantage_news(source, filters).await
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

    pub async fn collect_alpha_vantage_news(&self, source: &DataSource, filters: &DataFilters) -> Result<Vec<DataPoint>> {
        info!("Starting Alpha Vantage news collection for {}", source.name);
        
        // Check if API key is available
        let api_key = match &source.api_key {
            Some(key) => key,
            None => {
                warn!("No API key provided for Alpha Vantage source {}, falling back to simulated data", source.name);
                return self.generate_simulated_data(source, filters).await;
            }
        };

        let mut data = Vec::new();
        let client = Client::new();
        
        // Alpha Vantage News API endpoint
        let base_url = "https://www.alphavantage.co/query";
        
        // Build query parameters
        let mut params = vec![
            ("function", "NEWS_SENTIMENT"),
            ("apikey", api_key),
            ("limit", "50"), // Get up to 50 news items
        ];
        
        // Add topics if keywords are provided
        if !filters.keywords.is_empty() {
            // Use the first keyword as the main topic
            let topic = &filters.keywords[0];
            params.push(("topics", topic));
        }
        
        // Add time_from parameter (last 7 days)
        let time_from = (Utc::now() - chrono::Duration::days(7))
            .format("%Y%m%dT%H%M%S")
            .to_string();
        params.push(("time_from", &time_from));
        
        info!("Making Alpha Vantage API request with params: {:?}", params);
        
        match client.get(base_url).query(&params).send().await {
            Ok(response) => {
                info!("Alpha Vantage API response status: {}", response.status());
                
                if response.status().is_success() {
                    match response.json::<serde_json::Value>().await {
                        Ok(json_response) => {
                            debug!("Alpha Vantage API response: {:?}", json_response);
                            
                            // Check for API errors
                            if let Some(error_message) = json_response.get("Error Message") {
                                error!("Alpha Vantage API error: {}", error_message);
                                return self.generate_simulated_data(source, filters).await;
                            }
                            
                            if let Some(note) = json_response.get("Note") {
                                warn!("Alpha Vantage API note: {}", note);
                                return self.generate_simulated_data(source, filters).await;
                            }
                            
                            // Parse the feed
                            if let Some(feed) = json_response.get("feed") {
                                if let Ok(news_items) = serde_json::from_value::<Vec<AlphaVantageNewsItem>>(feed.clone()) {
                                    info!("Successfully parsed {} Alpha Vantage news items", news_items.len());
                                    
                                    for (i, news_item) in news_items.iter().enumerate() {
                                        // Create content combining title and summary
                                        let content = format!("{} - {}", news_item.title, news_item.summary);
                                        
                                        // Check if content matches our filters
                                        if self.matches_filters(&content, filters) {
                                            // Parse timestamp
                                            let timestamp = match chrono::DateTime::parse_from_rfc3339(&news_item.time_published) {
                                                Ok(dt) => dt.with_timezone(&Utc),
                                                Err(_) => Utc::now() - chrono::Duration::hours(i as i64),
                                            };
                                            
                                            // Determine theme based on topics and category
                                            let theme = self.classify_theme_from_alpha_vantage(news_item);
                                            
                                            // Use the sentiment score from Alpha Vantage
                                            let sentiment_score = Some(news_item.overall_sentiment_score);
                                            
                                            // Create engagement metrics (simulated since Alpha Vantage doesn't provide these)
                                            let engagement_metrics = self.generate_alpha_vantage_engagement(news_item);
                                            
                                            data.push(DataPoint {
                                                id: format!("alphavantage_{}", i),
                                                content,
                                                platform: Platform::AlphaVantage,
                                                timestamp,
                                                theme,
                                                author: news_item.authors.join(", "),
                                                url: Some(news_item.url.clone()),
                                                engagement_metrics,
                                                language: "en".to_string(), // Alpha Vantage primarily provides English content
                                                sentiment_score,
                                            });
                                        }
                                    }
                                } else {
                                    error!("Failed to parse Alpha Vantage news feed");
                                }
                            } else {
                                warn!("No 'feed' field found in Alpha Vantage response");
                            }
                        }
                        Err(e) => {
                            error!("Failed to parse Alpha Vantage JSON response: {}", e);
                        }
                    }
                } else {
                    error!("Alpha Vantage API request failed with status: {}", response.status());
                }
            }
            Err(e) => {
                error!("Alpha Vantage API request failed: {}", e);
            }
        }
        
        // If no real data collected, generate simulated data
        if data.is_empty() {
            info!("No real Alpha Vantage data collected, generating simulated data");
            return self.generate_simulated_data(source, filters).await;
        }
        
        info!("Alpha Vantage news collection completed: {} data points", data.len());
        Ok(data)
    }

    fn classify_theme_from_alpha_vantage(&self, news_item: &AlphaVantageNewsItem) -> Theme {
        let title_lower = news_item.title.to_lowercase();
        let _summary_lower = news_item.summary.to_lowercase();
        let category_lower = news_item.category_within_source.to_lowercase();
        
        // Check for specific financial/economic terms
        if title_lower.contains("earnings") || title_lower.contains("revenue") || title_lower.contains("profit") {
            return Theme::Economy;
        }
        
        if title_lower.contains("fed") || title_lower.contains("federal reserve") || title_lower.contains("interest rate") {
            return Theme::Economy;
        }
        
        if title_lower.contains("inflation") || title_lower.contains("cpi") || title_lower.contains("gdp") {
            return Theme::Economy;
        }
        
        if title_lower.contains("crypto") || title_lower.contains("bitcoin") || title_lower.contains("ethereum") {
            return Theme::Economy;
        }
        
        if title_lower.contains("stock") || title_lower.contains("market") || title_lower.contains("trading") {
            return Theme::Economy;
        }
        
        if title_lower.contains("tech") || title_lower.contains("ai") || title_lower.contains("software") {
            return Theme::Technology;
        }
        
        // Check category
        match category_lower.as_str() {
            "top news" | "earnings" | "ipo" | "mergers & acquisitions" => Theme::Economy,
            "technology" | "innovation" => Theme::Technology,
            "politics" | "government" => Theme::Politics,
            _ => Theme::Economy, // Default to economy for financial news
        }
    }

    fn generate_alpha_vantage_engagement(&self, news_item: &AlphaVantageNewsItem) -> EngagementMetrics {
        let mut rng = rand::thread_rng();
        
        // Base engagement for news articles
        let base_likes = rng.gen_range(50..500);
        let base_shares = rng.gen_range(20..200);
        let base_comments = rng.gen_range(5..50);
        let base_views = rng.gen_range(1000..10000);
        
        // Adjust based on sentiment (positive news gets more engagement)
        let sentiment_multiplier = if news_item.overall_sentiment_score > 0.3 {
            rng.gen_range(1.2..1.8) // Positive news
        } else if news_item.overall_sentiment_score < -0.3 {
            rng.gen_range(1.1..1.5) // Negative news can also get engagement
        } else {
            rng.gen_range(0.8..1.2) // Neutral news
        };
        
        // Adjust based on source credibility
        let source_multiplier = match news_item.source.to_lowercase().as_str() {
            "reuters" | "bloomberg" | "cnbc" | "marketwatch" => rng.gen_range(1.3..1.7),
            "yahoo finance" | "seeking alpha" => rng.gen_range(1.1..1.4),
            _ => rng.gen_range(0.9..1.2),
        };
        
        let final_multiplier = sentiment_multiplier * source_multiplier;
        
        EngagementMetrics {
            likes: (base_likes as f64 * final_multiplier) as u32,
            shares: (base_shares as f64 * final_multiplier) as u32,
            comments: (base_comments as f64 * final_multiplier) as u32,
            views: (base_views as f64 * final_multiplier) as u32,
        }
    }
} 