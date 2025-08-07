use anyhow::Result;
use chrono::Utc;
use dotenv::dotenv;
use dollar_punk::models::*;
use dollar_punk::data_collector::DataCollector;

#[tokio::main]
async fn main() -> Result<()> {
    // Carica le variabili dal file .env
    dotenv().ok();
    
    println!("🚀 Esempio: Data Collection con Alpha Vantage");
    println!("=" * 50);
    
    // Crea il data collector con Alpha Vantage dal file .env
    let mut collector = DataCollector::new()
        .with_alpha_vantage_from_env();
    
    // Configura le fonti di dati
    let sources = vec![
        DataSource {
            name: "Alpha Vantage News".to_string(),
            platform: Platform::AlphaVantage,
            url: "https://www.alphavantage.co/query".to_string(),
            api_key: None, // Usata dal file .env
            enabled: true,
        },
        DataSource {
            name: "Twitter Simulato".to_string(),
            platform: Platform::Twitter,
            url: "https://twitter.com".to_string(),
            api_key: None,
            enabled: true,
        },
        DataSource {
            name: "Reddit Simulato".to_string(),
            platform: Platform::Reddit,
            url: "https://reddit.com".to_string(),
            api_key: None,
            enabled: true,
        },
    ];
    
    // Configura i filtri per le news
    let filters = DataFilters {
        keywords: vec![
            "bitcoin".to_string(),
            "crypto".to_string(),
            "ethereum".to_string(),
            "finance".to_string(),
            "stock".to_string(),
            "market".to_string(),
        ],
        languages: vec!["en".to_string(), "it".to_string()],
        min_engagement: 0,
        exclude_retweets: false,
        exclude_ads: true,
    };
    
    // Configura il periodo di raccolta
    let collection_period = CollectionPeriod {
        start_date: Utc::now() - chrono::Duration::days(7),
        end_date: Utc::now(),
        interval_hours: 24,
    };
    
    // Configura la raccolta dati
    let config = DataCollectionConfig {
        sources,
        collection_period,
        filters,
    };
    
    println!("📊 Configurazione:");
    println!("  Fonti: {:?}", config.sources.iter().map(|s| &s.name).collect::<Vec<_>>());
    println!("  Keywords: {:?}", config.filters.keywords);
    println!("  Lingue: {:?}", config.filters.languages);
    println!("  Periodo: {} - {}", 
        config.collection_period.start_date.format("%Y-%m-%d"),
        config.collection_period.end_date.format("%Y-%m-%d")
    );
    
    println!("\n🔄 Inizio raccolta dati...");
    
    // Raccogli i dati
    match collector.collect_data(&config).await {
        Ok(all_data) => {
            println!("\n✅ Raccolta completata!");
            println!("📈 Totale dati raccolti: {}", all_data.len());
            
            // Analizza i dati per piattaforma
            let mut platform_stats = std::collections::HashMap::new();
            let mut alpha_vantage_news = Vec::new();
            
            for data_point in &all_data {
                *platform_stats.entry(&data_point.platform).or_insert(0) += 1;
                
                if let Platform::AlphaVantage = data_point.platform {
                    alpha_vantage_news.push(data_point);
                }
            }
            
            println!("\n📊 Statistiche per piattaforma:");
            for (platform, count) in platform_stats {
                println!("  {:?}: {} dati", platform, count);
            }
            
            // Mostra le news di Alpha Vantage
            if !alpha_vantage_news.is_empty() {
                println!("\n📰 NEWS ALPHA VANTAGE (prime 5):");
                println!("=" * 60);
                
                for (i, news) in alpha_vantage_news.iter().take(5).enumerate() {
                    println!("\n--- NEWS {} ---", i + 1);
                    println!("📝 Titolo: {}", news.content.split(" - ").next().unwrap_or("N/A"));
                    println!("👤 Autore: {}", news.author);
                    println!("🏷️  Tema: {:?}", news.theme);
                    println!("🌍 Lingua: {}", news.language);
                    
                    if let Some(sentiment) = news.sentiment_score {
                        let sentiment_label = if sentiment > 0.1 { "😊 Positivo" }
                            else if sentiment < -0.1 { "😞 Negativo" }
                            else { "😐 Neutro" };
                        println!("😊 Sentiment: {:.3} ({})", sentiment, sentiment_label);
                    }
                    
                    if let Some(url) = &news.url {
                        println!("🔗 URL: {}", url);
                    }
                    
                    println!("📅 Data: {}", news.timestamp.format("%Y-%m-%d %H:%M"));
                }
                
                // Statistiche sentiment Alpha Vantage
                let sentiment_scores: Vec<f64> = alpha_vantage_news
                    .iter()
                    .filter_map(|n| n.sentiment_score)
                    .collect();
                
                if !sentiment_scores.is_empty() {
                    let avg_sentiment = sentiment_scores.iter().sum::<f64>() / sentiment_scores.len() as f64;
                    println!("\n📊 STATISTICHE SENTIMENT ALPHA VANTAGE:");
                    println!("😊 Sentiment medio: {:.3}", avg_sentiment);
                    
                    let positive_count = sentiment_scores.iter().filter(|&&s| s > 0.1).count();
                    let negative_count = sentiment_scores.iter().filter(|&&s| s < -0.1).count();
                    let neutral_count = sentiment_scores.len() - positive_count - negative_count;
                    
                    println!("  ✅ Positivi: {} ({:.1}%)", positive_count,
                        (positive_count as f64 / sentiment_scores.len() as f64) * 100.0);
                    println!("  ❌ Negativi: {} ({:.1}%)", negative_count,
                        (negative_count as f64 / sentiment_scores.len() as f64) * 100.0);
                    println!("  ⚖️  Neutri: {} ({:.1}%)", neutral_count,
                        (neutral_count as f64 / sentiment_scores.len() as f64) * 100.0);
                }
            } else {
                println!("\n⚠️  Nessuna news da Alpha Vantage trovata");
                println!("💡 Controlla che l'API key sia corretta nel file .env");
            }
            
            // Esporta i dati in CSV
            let export_path = "alpha_vantage_data.csv";
            if let Ok(mut writer) = csv::Writer::from_path(export_path) {
                for data_point in &all_data {
                    if let Err(e) = writer.serialize(data_point) {
                        eprintln!("Errore scrittura CSV: {}", e);
                    }
                }
                if let Err(e) = writer.flush() {
                    eprintln!("Errore flush CSV: {}", e);
                } else {
                    println!("\n💾 Dati esportati in: {}", export_path);
                }
            }
            
        }
        Err(e) => {
            eprintln!("❌ Errore durante la raccolta dati: {}", e);
        }
    }
    
    println!("\n🎉 Esempio completato!");
    Ok(())
} 