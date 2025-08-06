use dollar_punk::models::*;
use dollar_punk::data_collector::DataCollector;
use anyhow::Result;
use chrono::Utc;

#[tokio::main]
async fn main() -> Result<()> {
    // Inizializza il logging
    tracing_subscriber::fmt::init();

    println!("🧪 Test Alpha Vantage Integration");
    println!("==================================");

    // Configurazione di test per Alpha Vantage
    let config = DataCollectionConfig {
        sources: vec![
            DataSource {
                name: "Alpha Vantage Test".to_string(),
                platform: Platform::AlphaVantage,
                url: "https://www.alphavantage.co/query".to_string(),
                api_key: std::env::var("ALPHA_VANTAGE_API_KEY").ok(), // Leggi da variabile d'ambiente
                enabled: true,
            }
        ],
        collection_period: CollectionPeriod {
            start_date: Utc::now() - chrono::Duration::days(7),
            end_date: Utc::now(),
            interval_hours: 24,
        },
        filters: DataFilters {
            keywords: vec![
                "bitcoin".to_string(),
                "ethereum".to_string(),
                "crypto".to_string(),
                "finance".to_string(),
                "earnings".to_string(),
            ],
            languages: vec!["en".to_string()],
            min_engagement: 10,
            exclude_retweets: true,
            exclude_ads: true,
        },
        mode: DataCollectionMode::Prod, // Usa dati reali
    };

    // Verifica se l'API key è disponibile
    if config.sources[0].api_key.is_none() {
        println!("⚠️  Nessuna API key trovata!");
        println!("   Imposta la variabile d'ambiente ALPHA_VANTAGE_API_KEY");
        println!("   Esempio: export ALPHA_VANTAGE_API_KEY=\"your_key_here\"");
        println!("\n🔄 Passando alla modalità Demo per test...");
        
        // Fallback alla modalità demo
        let mut demo_config = config.clone();
        demo_config.mode = DataCollectionMode::Demo;
        run_test(&demo_config).await?;
    } else {
        println!("✅ API key trovata, testando con dati reali...");
        run_test(&config).await?;
    }

    Ok(())
}

async fn run_test(config: &DataCollectionConfig) -> Result<()> {
    let mut collector = DataCollector::new();
    
    println!("\n📊 Raccolta dati in corso...");
    let start_time = std::time::Instant::now();
    
    match collector.collect_data(config).await {
        Ok(data_points) => {
            let duration = start_time.elapsed();
            println!("✅ Raccolta completata in {:?}", duration);
            println!("📈 Dati raccolti: {} punti", data_points.len());
            
            if data_points.is_empty() {
                println!("⚠️  Nessun dato raccolto. Verifica i filtri o la connessione.");
                return Ok(());
            }
            
            // Analisi dei dati raccolti
            analyze_data(&data_points);
            
            // Esempi di dati
            show_examples(&data_points);
            
        }
        Err(e) => {
            println!("❌ Errore durante la raccolta: {}", e);
        }
    }
    
    Ok(())
}

fn analyze_data(data_points: &[DataPoint]) {
    println!("\n📊 Analisi dei Dati");
    println!("==================");
    
    // Statistiche per piattaforma
    let mut platform_counts = std::collections::HashMap::new();
    let mut theme_counts = std::collections::HashMap::new();
    let mut sentiment_sum = 0.0;
    let mut sentiment_count = 0;
    
    for point in data_points {
        *platform_counts.entry(&point.platform).or_insert(0) += 1;
        *theme_counts.entry(&point.theme).or_insert(0) += 1;
        
        if let Some(sentiment) = point.sentiment_score {
            sentiment_sum += sentiment;
            sentiment_count += 1;
        }
    }
    
    println!("📱 Distribuzione per Piattaforma:");
    for (platform, count) in platform_counts {
        println!("   {:?}: {} ({:.1}%)", platform, count, 
                (count as f64 / data_points.len() as f64) * 100.0);
    }
    
    println!("\n🎯 Distribuzione per Tema:");
    for (theme, count) in theme_counts {
        println!("   {:?}: {} ({:.1}%)", theme, count, 
                (count as f64 / data_points.len() as f64) * 100.0);
    }
    
    if sentiment_count > 0 {
        let avg_sentiment = sentiment_sum / sentiment_count as f64;
        println!("\n😊 Sentiment Analysis:");
        println!("   Media sentiment: {:.3}", avg_sentiment);
        println!("   Punti con sentiment: {}/{}", sentiment_count, data_points.len());
        
        // Classifica sentiment
        let sentiment_label = if avg_sentiment > 0.3 {
            "🟢 Positivo"
        } else if avg_sentiment < -0.3 {
            "🔴 Negativo"
        } else {
            "🟡 Neutrale"
        };
        println!("   Classificazione: {}", sentiment_label);
    }
}

fn show_examples(data_points: &[DataPoint]) {
    println!("\n📝 Esempi di Dati");
    println!("================");
    
    // Mostra i primi 3 esempi
    for (i, point) in data_points.iter().take(3).enumerate() {
        println!("\n--- Esempio {} ---", i + 1);
        println!("ID: {}", point.id);
        println!("Piattaforma: {:?}", point.platform);
        println!("Tema: {:?}", point.theme);
        println!("Autore: {}", point.author);
        println!("Timestamp: {}", point.timestamp.format("%Y-%m-%d %H:%M:%S UTC"));
        
        if let Some(sentiment) = point.sentiment_score {
            let sentiment_emoji = if sentiment > 0.3 {
                "😊"
            } else if sentiment < -0.3 {
                "😞"
            } else {
                "😐"
            };
            println!("Sentiment: {:.3} {}", sentiment, sentiment_emoji);
        }
        
        println!("Contenuto: {}", 
                if point.content.len() > 100 {
                    format!("{}...", &point.content[..100])
                } else {
                    point.content.clone()
                });
        
        if let Some(url) = &point.url {
            println!("URL: {}", url);
        }
        
        println!("Engagement: {} likes, {} shares, {} comments, {} views",
                point.engagement_metrics.likes,
                point.engagement_metrics.shares,
                point.engagement_metrics.comments,
                point.engagement_metrics.views);
    }
    
    if data_points.len() > 3 {
        println!("\n... e altri {} punti dati", data_points.len() - 3);
    }
} 