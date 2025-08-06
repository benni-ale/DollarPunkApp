use crate::models::*;
use anyhow::Result;
use chrono::{DateTime, Utc};
use config::{Config, ConfigError, Environment, File};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub data_collection: DataCollectionConfig,
    pub stratification: StratificationConfig,
}

impl AppConfig {
    /// Carica la configurazione da un file TOML
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, ConfigError> {
        let config = Config::builder()
            .add_source(File::from(path.as_ref()))
            .add_source(Environment::with_prefix("DOLLAR_PUNK"))
            .build()?;

        // Deserializza manualmente per gestire le enum
        let value = config.try_deserialize::<serde_json::Value>()?;
        
        // Converti la configurazione
        let data_collection = if let Some(dc) = value.get("data_collection") {
            let mode = match dc.get("mode").and_then(|v| v.as_str()) {
                Some("demo") => DataCollectionMode::Demo,
                Some("prod") => DataCollectionMode::Prod,
                _ => DataCollectionMode::Demo,
            };

            let sources = if let Some(sources_array) = dc.get("sources").and_then(|v| v.as_array()) {
                sources_array.iter().filter_map(|s| {
                    let name = s.get("name")?.as_str()?.to_string();
                    let platform_str = s.get("platform")?.as_str()?;
                    let platform = match platform_str {
                        "twitter" => Platform::Twitter,
                        "facebook" => Platform::Facebook,
                        "instagram" => Platform::Instagram,
                        "linkedin" => Platform::LinkedIn,
                        "reddit" => Platform::Reddit,
                        "newswebsite" => Platform::NewsWebsite,
                        "rss" => Platform::RSS,
                        "youtube" => Platform::YouTube,
                        "tiktok" => Platform::TikTok,
                        "alphavantage" => Platform::AlphaVantage,
                        other => Platform::Other(other.to_string()),
                    };
                    let url = s.get("url")?.as_str()?.to_string();
                    let api_key = s.get("api_key").and_then(|v| v.as_str()).map(|s| s.to_string());
                    let enabled = s.get("enabled").and_then(|v| v.as_bool()).unwrap_or(true);
                    
                    Some(DataSource {
                        name,
                        platform,
                        url,
                        api_key,
                        enabled,
                    })
                }).collect()
            } else {
                vec![]
            };

            let collection_period = if let Some(cp) = dc.get("collection_period") {
                let start_date = cp.get("start_date")
                    .and_then(|v| v.as_str())
                    .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
                    .map(|dt| dt.with_timezone(&Utc))
                    .unwrap_or_else(|| Utc::now() - chrono::Duration::days(7));
                
                let end_date = cp.get("end_date")
                    .and_then(|v| v.as_str())
                    .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
                    .map(|dt| dt.with_timezone(&Utc))
                    .unwrap_or_else(Utc::now);
                
                let interval_hours = cp.get("interval_hours")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(24) as u32;

                CollectionPeriod {
                    start_date,
                    end_date,
                    interval_hours,
                }
            } else {
                CollectionPeriod {
                    start_date: Utc::now() - chrono::Duration::days(7),
                    end_date: Utc::now(),
                    interval_hours: 24,
                }
            };

            let filters = if let Some(f) = dc.get("filters") {
                let keywords = f.get("keywords")
                    .and_then(|v| v.as_array())
                    .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
                    .unwrap_or_default();
                
                let languages = f.get("languages")
                    .and_then(|v| v.as_array())
                    .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
                    .unwrap_or_default();
                
                let min_engagement = f.get("min_engagement")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(10) as u32;
                
                let exclude_retweets = f.get("exclude_retweets")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(true);
                
                let exclude_ads = f.get("exclude_ads")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(true);

                DataFilters {
                    keywords,
                    languages,
                    min_engagement,
                    exclude_retweets,
                    exclude_ads,
                }
            } else {
                DataFilters::default()
            };

            DataCollectionConfig {
                sources,
                collection_period,
                filters,
                mode,
            }
        } else {
            DataCollectionConfig::default()
        };

        let stratification = if let Some(s) = value.get("stratification") {
            let mut platform_weights = std::collections::HashMap::new();
            if let Some(pw) = s.get("platform_weights") {
                if let Some(obj) = pw.as_object() {
                    for (k, v) in obj {
                        if let Some(weight) = v.as_f64() {
                            let platform = match k.as_str() {
                                "twitter" => Platform::Twitter,
                                "facebook" => Platform::Facebook,
                                "instagram" => Platform::Instagram,
                                "linkedin" => Platform::LinkedIn,
                                "reddit" => Platform::Reddit,
                                "newswebsite" => Platform::NewsWebsite,
                                "rss" => Platform::RSS,
                                "youtube" => Platform::YouTube,
                                "tiktok" => Platform::TikTok,
                                "alphavantage" => Platform::AlphaVantage,
                                other => Platform::Other(other.to_string()),
                            };
                            platform_weights.insert(platform, weight);
                        }
                    }
                }
            }

            let mut theme_weights = std::collections::HashMap::new();
            if let Some(tw) = s.get("theme_weights") {
                if let Some(obj) = tw.as_object() {
                    for (k, v) in obj {
                        if let Some(weight) = v.as_f64() {
                            let theme = match k.as_str() {
                                "politics" => Theme::Politics,
                                "economy" => Theme::Economy,
                                "technology" => Theme::Technology,
                                "sports" => Theme::Sports,
                                "entertainment" => Theme::Entertainment,
                                "health" => Theme::Health,
                                "science" => Theme::Science,
                                "environment" => Theme::Environment,
                                "education" => Theme::Education,
                                "other" => Theme::Other("General".to_string()),
                                other => Theme::Other(other.to_string()),
                            };
                            theme_weights.insert(theme, weight);
                        }
                    }
                }
            }

            let min_samples_per_stratum = s.get("min_samples_per_stratum")
                .and_then(|v| v.as_u64())
                .unwrap_or(10) as usize;
            
            let max_samples_per_stratum = s.get("max_samples_per_stratum")
                .and_then(|v| v.as_u64())
                .map(|v| v as usize);

            StratificationConfig {
                platform_weights,
                theme_weights,
                time_periods: vec![],
                min_samples_per_stratum,
                max_samples_per_stratum,
            }
        } else {
            StratificationConfig::default()
        };

        Ok(AppConfig {
            data_collection,
            stratification,
        })
    }

    /// Carica la configurazione con fallback ai valori di default
    pub fn load_or_default<P: AsRef<Path>>(path: P) -> Self {
        match Self::from_file(path) {
            Ok(config) => {
                tracing::info!("Configurazione caricata da file");
                config
            }
            Err(e) => {
                tracing::warn!("Impossibile caricare configurazione da file: {}. Usando valori di default.", e);
                Self::default()
            }
        }
    }

    /// Salva la configurazione in un file TOML
    pub fn save_to_file<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        // Crea una struttura semplificata per la serializzazione TOML
        #[derive(Serialize)]
        struct TomlConfig {
            data_collection: TomlDataCollection,
            stratification: TomlStratification,
        }

        #[derive(Serialize)]
        struct TomlDataCollection {
            mode: String,
            sources: Vec<TomlDataSource>,
            collection_period: TomlCollectionPeriod,
            filters: TomlDataFilters,
        }

        #[derive(Serialize)]
        struct TomlDataSource {
            name: String,
            platform: String,
            url: String,
            api_key: Option<String>,
            enabled: bool,
        }

        #[derive(Serialize)]
        struct TomlCollectionPeriod {
            start_date: String,
            end_date: String,
            interval_hours: u32,
        }

        #[derive(Serialize)]
        struct TomlDataFilters {
            keywords: Vec<String>,
            languages: Vec<String>,
            min_engagement: u32,
            exclude_retweets: bool,
            exclude_ads: bool,
        }

        #[derive(Serialize)]
        struct TomlStratification {
            platform_weights: std::collections::HashMap<String, f64>,
            theme_weights: std::collections::HashMap<String, f64>,
            min_samples_per_stratum: usize,
            max_samples_per_stratum: Option<usize>,
        }

        // Converti la configurazione
        let toml_config = TomlConfig {
            data_collection: TomlDataCollection {
                mode: match self.data_collection.mode {
                    DataCollectionMode::Demo => "demo".to_string(),
                    DataCollectionMode::Prod => "prod".to_string(),
                },
                sources: self.data_collection.sources.iter().map(|s| TomlDataSource {
                    name: s.name.clone(),
                    platform: match s.platform {
                        Platform::Twitter => "twitter".to_string(),
                        Platform::Facebook => "facebook".to_string(),
                        Platform::Instagram => "instagram".to_string(),
                        Platform::LinkedIn => "linkedin".to_string(),
                        Platform::Reddit => "reddit".to_string(),
                        Platform::NewsWebsite => "newswebsite".to_string(),
                        Platform::RSS => "rss".to_string(),
                        Platform::YouTube => "youtube".to_string(),
                        Platform::TikTok => "tiktok".to_string(),
                        Platform::AlphaVantage => "alphavantage".to_string(),
                        Platform::Other(ref s) => s.clone(),
                    },
                    url: s.url.clone(),
                    api_key: s.api_key.clone(),
                    enabled: s.enabled,
                }).collect(),
                collection_period: TomlCollectionPeriod {
                    start_date: self.data_collection.collection_period.start_date.to_rfc3339(),
                    end_date: self.data_collection.collection_period.end_date.to_rfc3339(),
                    interval_hours: self.data_collection.collection_period.interval_hours,
                },
                filters: TomlDataFilters {
                    keywords: self.data_collection.filters.keywords.clone(),
                    languages: self.data_collection.filters.languages.clone(),
                    min_engagement: self.data_collection.filters.min_engagement,
                    exclude_retweets: self.data_collection.filters.exclude_retweets,
                    exclude_ads: self.data_collection.filters.exclude_ads,
                },
            },
            stratification: TomlStratification {
                platform_weights: self.stratification.platform_weights.iter().map(|(k, v)| {
                    let key = match k {
                        Platform::Twitter => "twitter".to_string(),
                        Platform::Facebook => "facebook".to_string(),
                        Platform::Instagram => "instagram".to_string(),
                        Platform::LinkedIn => "linkedin".to_string(),
                        Platform::Reddit => "reddit".to_string(),
                        Platform::NewsWebsite => "newswebsite".to_string(),
                        Platform::RSS => "rss".to_string(),
                        Platform::YouTube => "youtube".to_string(),
                        Platform::TikTok => "tiktok".to_string(),
                        Platform::AlphaVantage => "alphavantage".to_string(),
                        Platform::Other(ref s) => s.clone(),
                    };
                    (key, *v)
                }).collect(),
                theme_weights: self.stratification.theme_weights.iter().map(|(k, v)| {
                    let key = match k {
                        Theme::Politics => "politics".to_string(),
                        Theme::Economy => "economy".to_string(),
                        Theme::Technology => "technology".to_string(),
                        Theme::Sports => "sports".to_string(),
                        Theme::Entertainment => "entertainment".to_string(),
                        Theme::Health => "health".to_string(),
                        Theme::Science => "science".to_string(),
                        Theme::Environment => "environment".to_string(),
                        Theme::Education => "education".to_string(),
                        Theme::Other(ref s) => s.clone(),
                    };
                    (key, *v)
                }).collect(),
                min_samples_per_stratum: self.stratification.min_samples_per_stratum,
                max_samples_per_stratum: self.stratification.max_samples_per_stratum,
            },
        };

        let toml_string = toml::to_string_pretty(&toml_config)?;
        std::fs::write(path, toml_string)?;
        Ok(())
    }

    /// Valida la configurazione
    pub fn validate(&self) -> Result<()> {
        // Verifica che ci siano fonti abilitate
        let enabled_sources: Vec<_> = self.data_collection.sources.iter()
            .filter(|s| s.enabled)
            .collect();

        if enabled_sources.is_empty() {
            return Err(anyhow::anyhow!("Nessuna fonte dati abilitata"));
        }

        // Verifica che le fonti Alpha Vantage abbiano una API key in modalità Prod
        if self.data_collection.mode == DataCollectionMode::Prod {
            for source in &enabled_sources {
                if matches!(source.platform, Platform::AlphaVantage) && source.api_key.is_none() {
                    return Err(anyhow::anyhow!(
                        "Fonte Alpha Vantage '{}' richiede una API key in modalità Prod",
                        source.name
                    ));
                }
            }
        }

        // Verifica che ci siano keywords configurate
        if self.data_collection.filters.keywords.is_empty() {
            return Err(anyhow::anyhow!("Nessuna keyword configurata per i filtri"));
        }

        // Verifica che ci siano lingue configurate
        if self.data_collection.filters.languages.is_empty() {
            return Err(anyhow::anyhow!("Nessuna lingua configurata per i filtri"));
        }

        Ok(())
    }

    /// Crea una configurazione di esempio per Alpha Vantage
    pub fn create_alpha_vantage_example() -> Self {
        let sources = vec![
            DataSource {
                name: "Alpha Vantage News".to_string(),
                platform: Platform::AlphaVantage,
                url: "https://www.alphavantage.co/query".to_string(),
                api_key: Some("YOUR_ALPHA_VANTAGE_API_KEY_HERE".to_string()),
                enabled: true,
            },
            DataSource {
                name: "Reuters Finance".to_string(),
                platform: Platform::NewsWebsite,
                url: "https://www.reuters.com/business/finance/".to_string(),
                api_key: None,
                enabled: true,
            },
            DataSource {
                name: "Bloomberg RSS".to_string(),
                platform: Platform::RSS,
                url: "https://feeds.bloomberg.com/markets/news.rss".to_string(),
                api_key: None,
                enabled: true,
            },
        ];

        let mut platform_weights = std::collections::HashMap::new();
        platform_weights.insert(Platform::Twitter, 1.0);
        platform_weights.insert(Platform::AlphaVantage, 1.5); // Peso maggiore per Alpha Vantage
        platform_weights.insert(Platform::NewsWebsite, 1.0);
        platform_weights.insert(Platform::RSS, 1.0);

        let mut theme_weights = std::collections::HashMap::new();
        theme_weights.insert(Theme::Economy, 1.5);
        theme_weights.insert(Theme::Technology, 1.0);
        theme_weights.insert(Theme::Politics, 0.8);
        theme_weights.insert(Theme::Other("General".to_string()), 0.5);

        Self {
            data_collection: DataCollectionConfig {
                sources,
                collection_period: CollectionPeriod {
                    start_date: Utc::now() - chrono::Duration::days(7),
                    end_date: Utc::now(),
                    interval_hours: 24,
                },
                filters: DataFilters {
                    keywords: vec![
                        "finance".to_string(),
                        "economy".to_string(),
                        "crypto".to_string(),
                        "stocks".to_string(),
                        "earnings".to_string(),
                        "fed".to_string(),
                        "inflation".to_string(),
                    ],
                    languages: vec!["en".to_string()],
                    min_engagement: 10,
                    exclude_retweets: true,
                    exclude_ads: true,
                },
                mode: DataCollectionMode::Demo, // Inizia in modalità demo
            },
            stratification: StratificationConfig {
                platform_weights,
                theme_weights,
                time_periods: vec![],
                min_samples_per_stratum: 10,
                max_samples_per_stratum: Some(100),
            },
        }
    }
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            data_collection: DataCollectionConfig::default(),
            stratification: StratificationConfig::default(),
        }
    }
}

/// Funzioni di utilità per la configurazione
pub mod utils {
    use super::*;

    /// Crea un file di configurazione di esempio
    pub fn create_example_config_file<P: AsRef<Path>>(path: P) -> Result<()> {
        let config = AppConfig::create_alpha_vantage_example();
        config.save_to_file(path)?;
        Ok(())
    }

    /// Verifica se una configurazione è valida per Alpha Vantage
    pub fn is_alpha_vantage_ready(config: &AppConfig) -> bool {
        config.data_collection.sources.iter()
            .any(|source| {
                source.enabled && 
                matches!(source.platform, Platform::AlphaVantage) && 
                source.api_key.is_some()
            })
    }

    /// Ottiene le fonti Alpha Vantage configurate
    pub fn get_alpha_vantage_sources(config: &AppConfig) -> Vec<&DataSource> {
        config.data_collection.sources.iter()
            .filter(|source| {
                source.enabled && 
                matches!(source.platform, Platform::AlphaVantage)
            })
            .collect()
    }

    /// Imposta l'API key per Alpha Vantage
    pub fn set_alpha_vantage_api_key(config: &mut AppConfig, api_key: String) {
        for source in &mut config.data_collection.sources {
            if matches!(source.platform, Platform::AlphaVantage) {
                source.api_key = Some(api_key.clone());
            }
        }
    }

    /// Rimuove l'API key per Alpha Vantage (per sicurezza)
    pub fn clear_alpha_vantage_api_keys(config: &mut AppConfig) {
        for source in &mut config.data_collection.sources {
            if matches!(source.platform, Platform::AlphaVantage) {
                source.api_key = None;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_validation() {
        let config = AppConfig::create_alpha_vantage_example();
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_config_without_sources() {
        let mut config = AppConfig::default();
        config.data_collection.sources.clear();
        assert!(config.validate().is_err());
    }

    #[test]
    fn test_alpha_vantage_without_api_key() {
        let mut config = AppConfig::create_alpha_vantage_example();
        config.data_collection.mode = DataCollectionMode::Prod;
        utils::clear_alpha_vantage_api_keys(&mut config);
        assert!(config.validate().is_err());
    }
} 