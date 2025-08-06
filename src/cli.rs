use crate::config::{AppConfig, utils};
use crate::data_collector::DataCollector;
use crate::models::*;
use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "dollar-punk")]
#[command(about = "DollarPunk - Financial Data Collection and Analysis")]
#[command(version)]
pub struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Testa l'integrazione con Alpha Vantage
    TestAlphaVantage {
        /// File di configurazione
        #[arg(short, long, default_value = "config.toml")]
        config: PathBuf,
        
        /// API key di Alpha Vantage (opzionale, può essere nel file config)
        #[arg(long)]
        api_key: Option<String>,
        
        /// Modalità demo (senza chiamate API reali)
        #[arg(long)]
        demo: bool,
    },
    
    /// Crea un file di configurazione di esempio
    CreateConfig {
        /// Percorso del file di configurazione da creare
        #[arg(default_value = "config.toml")]
        output: PathBuf,
    },
    
    /// Valida un file di configurazione
    ValidateConfig {
        /// File di configurazione da validare
        #[arg(default_value = "config.toml")]
        config: PathBuf,
    },
    
    /// Raccolta dati completa
    CollectData {
        /// File di configurazione
        #[arg(short, long, default_value = "config.toml")]
        config: PathBuf,
        
        /// Modalità demo
        #[arg(long)]
        demo: bool,
    },
}

impl Cli {
    pub async fn run() -> Result<()> {
        let cli = Cli::parse();
        
        match cli.command {
            Commands::TestAlphaVantage { config, api_key, demo } => {
                Self::test_alpha_vantage(config, api_key, demo).await
            }
            Commands::CreateConfig { output } => {
                Self::create_config(output)
            }
            Commands::ValidateConfig { config } => {
                Self::validate_config(config)
            }
            Commands::CollectData { config, demo } => {
                Self::collect_data(config, demo).await
            }
        }
    }
    
    async fn test_alpha_vantage(config_path: PathBuf, api_key: Option<String>, demo: bool) -> Result<()> {
        println!("🧪 Test Alpha Vantage Integration");
        println!("==================================");
        
        // Carica configurazione
        let mut app_config = AppConfig::load_or_default(&config_path);
        
        // Imposta API key se fornita
        if let Some(key) = api_key {
            utils::set_alpha_vantage_api_key(&mut app_config, key);
        }
        
        // Imposta modalità demo se richiesto
        if demo {
            app_config.data_collection.mode = DataCollectionMode::Demo;
        }
        
        // Valida configurazione
        match app_config.validate() {
            Ok(_) => println!("✅ Configurazione valida"),
            Err(e) => {
                println!("❌ Errore di configurazione: {}", e);
                if !demo {
                    println!("💡 Prova con --demo per testare senza API key");
                    return Ok(());
                }
            }
        }
        
        // Verifica se Alpha Vantage è configurato
        if !utils::is_alpha_vantage_ready(&app_config) {
            println!("⚠️  Alpha Vantage non configurato correttamente");
            println!("   Assicurati di avere una API key valida");
            return Ok(());
        }
        
        // Test raccolta dati
        println!("\n📊 Testando raccolta dati...");
        let mut collector = DataCollector::new();
        
        match collector.collect_data(&app_config.data_collection).await {
            Ok(data_points) => {
                println!("✅ Raccolta completata!");
                println!("📈 Dati raccolti: {} punti", data_points.len());
                
                if data_points.is_empty() {
                    println!("⚠️  Nessun dato raccolto");
                    return Ok(());
                }
                
                // Analisi rapida
                Self::quick_analysis(&data_points);
                
            }
            Err(e) => {
                println!("❌ Errore durante la raccolta: {}", e);
            }
        }
        
        Ok(())
    }
    
    fn create_config(output: PathBuf) -> Result<()> {
        println!("📝 Creazione file di configurazione...");
        
        match utils::create_example_config_file(&output) {
            Ok(_) => {
                println!("✅ File di configurazione creato: {}", output.display());
                println!("\n📋 Prossimi passi:");
                println!("1. Modifica il file {} per aggiungere la tua API key", output.display());
                println!("2. Personalizza i filtri e le fonti dati");
                println!("3. Esegui: cargo run -- test-alpha-vantage");
            }
            Err(e) => {
                println!("❌ Errore nella creazione del file: {}", e);
            }
        }
        
        Ok(())
    }
    
    fn validate_config(config_path: PathBuf) -> Result<()> {
        println!("🔍 Validazione configurazione...");
        
        let app_config = AppConfig::load_or_default(&config_path);
        
        match app_config.validate() {
            Ok(_) => {
                println!("✅ Configurazione valida!");
                
                // Mostra informazioni sulla configurazione
                println!("\n📋 Informazioni configurazione:");
                println!("   Fonti abilitate: {}", 
                    app_config.data_collection.sources.iter()
                        .filter(|s| s.enabled)
                        .count());
                println!("   Modalità: {:?}", app_config.data_collection.mode);
                println!("   Keywords: {}", app_config.data_collection.filters.keywords.len());
                println!("   Lingue: {}", app_config.data_collection.filters.languages.len());
                
                // Verifica Alpha Vantage
                if utils::is_alpha_vantage_ready(&app_config) {
                    println!("   ✅ Alpha Vantage configurato correttamente");
                } else {
                    println!("   ⚠️  Alpha Vantage non configurato");
                }
            }
            Err(e) => {
                println!("❌ Configurazione non valida: {}", e);
            }
        }
        
        Ok(())
    }
    
    async fn collect_data(config_path: PathBuf, demo: bool) -> Result<()> {
        println!("📊 Raccolta dati completa...");
        
        let mut app_config = AppConfig::load_or_default(&config_path);
        
        if demo {
            app_config.data_collection.mode = DataCollectionMode::Demo;
            println!("🔄 Modalità demo attivata");
        }
        
        // Valida configurazione
        match app_config.validate() {
            Ok(_) => println!("✅ Configurazione valida"),
            Err(e) => {
                println!("❌ Errore di configurazione: {}", e);
                return Ok(());
            }
        }
        
        // Raccolta dati
        let mut collector = DataCollector::new();
        let start_time = std::time::Instant::now();
        
        match collector.collect_data(&app_config.data_collection).await {
            Ok(data_points) => {
                let duration = start_time.elapsed();
                println!("✅ Raccolta completata in {:?}", duration);
                println!("📈 Dati raccolti: {} punti", data_points.len());
                
                if !data_points.is_empty() {
                    Self::detailed_analysis(&data_points);
                }
            }
            Err(e) => {
                println!("❌ Errore durante la raccolta: {}", e);
            }
        }
        
        Ok(())
    }
    
    fn quick_analysis(data_points: &[DataPoint]) {
        println!("\n📊 Analisi Rapida");
        println!("================");
        
        // Statistiche per piattaforma
        let mut platform_counts = std::collections::HashMap::new();
        let mut sentiment_sum = 0.0;
        let mut sentiment_count = 0;
        
        for point in data_points {
            *platform_counts.entry(&point.platform).or_insert(0) += 1;
            if let Some(sentiment) = point.sentiment_score {
                sentiment_sum += sentiment;
                sentiment_count += 1;
            }
        }
        
        println!("📱 Piattaforme:");
        for (platform, count) in platform_counts {
            println!("   {:?}: {} ({:.1}%)", platform, count, 
                    (count as f64 / data_points.len() as f64) * 100.0);
        }
        
        if sentiment_count > 0 {
            let avg_sentiment = sentiment_sum / sentiment_count as f64;
            println!("\n😊 Sentiment medio: {:.3}", avg_sentiment);
            
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
    
    fn detailed_analysis(data_points: &[DataPoint]) {
        println!("\n📊 Analisi Dettagliata");
        println!("=====================");
        
        let mut platform_counts = std::collections::HashMap::new();
        let mut theme_counts = std::collections::HashMap::new();
        let mut sentiment_sum = 0.0;
        let mut sentiment_count = 0;
        let mut engagement_sum = 0;
        
        for point in data_points {
            *platform_counts.entry(&point.platform).or_insert(0) += 1;
            *theme_counts.entry(&point.theme).or_insert(0) += 1;
            
            if let Some(sentiment) = point.sentiment_score {
                sentiment_sum += sentiment;
                sentiment_count += 1;
            }
            
            engagement_sum += point.engagement_metrics.likes + 
                            point.engagement_metrics.shares + 
                            point.engagement_metrics.comments;
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
            println!("   Media: {:.3}", avg_sentiment);
            println!("   Punti con sentiment: {}/{}", sentiment_count, data_points.len());
            
            let sentiment_label = if avg_sentiment > 0.3 {
                "🟢 Positivo"
            } else if avg_sentiment < -0.3 {
                "🔴 Negativo"
            } else {
                "🟡 Neutrale"
            };
            println!("   Classificazione: {}", sentiment_label);
        }
        
        let avg_engagement = engagement_sum as f64 / data_points.len() as f64;
        println!("\n📈 Engagement medio: {:.1} interazioni per punto", avg_engagement);
        
        // Mostra alcuni esempi
        println!("\n📝 Esempi di dati:");
        for (i, point) in data_points.iter().take(3).enumerate() {
            println!("\n--- Esempio {} ---", i + 1);
            println!("Piattaforma: {:?}", point.platform);
            println!("Tema: {:?}", point.theme);
            if let Some(sentiment) = point.sentiment_score {
                println!("Sentiment: {:.3}", sentiment);
            }
            println!("Contenuto: {}", 
                    if point.content.len() > 80 {
                        format!("{}...", &point.content[..80])
                    } else {
                        point.content.clone()
                    });
        }
    }
} 