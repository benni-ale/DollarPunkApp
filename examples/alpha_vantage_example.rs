use crate::models::*;
use crate::alpha_vantage::{AlphaVantageClient, AlphaVantageConfig};
use anyhow::Result;

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
        return Ok(());
    }

    let config = AlphaVantageConfig {
        api_key,
        ..Default::default()
    };

    let mut client = AlphaVantageClient::new(config);

    // Configura i filtri per i dati
    let filters = DataFilters {
        keywords: vec![
            "economy".to_string(),
            "finance".to_string(),
            "crypto".to_string(),
            "bitcoin".to_string(),
            "ethereum".to_string(),
        ],
        languages: vec!["en".to_string(), "it".to_string()],
        min_engagement: 0,
        exclude_retweets: false,
        exclude_ads: true,
    };

    println!("📰 Raccolta dati news da Alpha Vantage...");
    println!("🔍 Keywords: {:?}", filters.keywords);
    println!("🌍 Lingue: {:?}", filters.languages);

    // Raccogli dati news
    match client.collect_news_data(&filters).await {
        Ok(news_data) => {
            println!("✅ Raccolti {} articoli news", news_data.len());
            
            // Mostra i primi 5 articoli
            for (i, article) in news_data.iter().take(5).enumerate() {
                println!("\n--- Articolo {} ---", i + 1);
                println!("📝 Titolo: {}", article.content.split(" - ").next().unwrap_or("N/A"));
                println!("👤 Autore: {}", article.author);
                println!("📅 Data: {}", article.timestamp.format("%Y-%m-%d %H:%M:%S UTC"));
                println!("🏷️  Tema: {:?}", article.theme);
                println!("🌍 Lingua: {}", article.language);
                if let Some(sentiment) = article.sentiment_score {
                    println!("😊 Sentiment: {:.3}", sentiment);
                }
                if let Some(url) = &article.url {
                    println!("🔗 URL: {}", url);
                }
            }

            // Analizza la distribuzione per tema
            let mut theme_counts = std::collections::HashMap::new();
            for article in &news_data {
                *theme_counts.entry(&article.theme).or_insert(0) += 1;
            }

            println!("\n📊 Distribuzione per tema:");
            for (theme, count) in theme_counts {
                println!("  {:?}: {} articoli", theme, count);
            }

            // Analizza il sentiment medio
            let sentiment_scores: Vec<f64> = news_data
                .iter()
                .filter_map(|a| a.sentiment_score)
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