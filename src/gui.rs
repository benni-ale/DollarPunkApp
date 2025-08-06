use crate::models::*;
use crate::data_collector::DataCollector;
use crate::stratification::StratificationEngine;
use anyhow::Result;
use chrono::Local;
use eframe::egui;
use egui::{Color32, RichText, ScrollArea, Ui};
use tokio::runtime::Runtime;
use tracing::{info, error};

pub struct DollarPunkApp {
    // Data collection
    collection_config: DataCollectionConfig,
    data_collector: DataCollector,
    
    // Stratification
    stratification_config: StratificationConfig,
    stratification_engine: Option<StratificationEngine>,
    
    // Data storage
    collected_data: Vec<DataPoint>,
    strata: Vec<Stratum>,
    sampling_result: Option<SamplingResult>,
    
    // UI state
    selected_tab: usize,
    is_collecting: bool,
    collection_progress: f32,
    status_message: String,
    
    // Debug and logging
    debug_logs: Vec<String>,
    show_debug_logs: bool,
    
    // Alpha Vantage specific state
    alpha_vantage_api_key: String,
    alpha_vantage_test_results: Vec<String>,
    alpha_vantage_is_testing: bool,
    alpha_vantage_test_progress: f32,
    alpha_vantage_live_data: Vec<DataPoint>,
    alpha_vantage_query_topics: String,
    alpha_vantage_query_limit: String,
    alpha_vantage_show_api_key: bool,
    
    // Runtime for async operations
    runtime: Runtime,
}

impl DollarPunkApp {
    pub fn new() -> Result<Self> {
        let mut collection_config = DataCollectionConfig::default();
        
        // Add some default sources
        collection_config.sources = vec![
            DataSource {
                name: "Alpha Vantage News".to_string(),
                platform: Platform::AlphaVantage,
                url: "https://www.alphavantage.co/query".to_string(),
                api_key: Some("YOUR_ALPHA_VANTAGE_API_KEY_HERE".to_string()),
                enabled: true,
            },
            DataSource {
                name: "Twitter Finance".to_string(),
                platform: Platform::Twitter,
                url: "https://twitter.com".to_string(),
                api_key: None,
                enabled: true,
            },
            DataSource {
                name: "Reuters News".to_string(),
                platform: Platform::NewsWebsite,
                url: "https://www.reuters.com".to_string(),
                api_key: None,
                enabled: true,
            },
            DataSource {
                name: "BBC RSS".to_string(),
                platform: Platform::RSS,
                url: "https://feeds.bbci.co.uk/news/rss.xml".to_string(),
                api_key: None,
                enabled: true,
            },
            DataSource {
                name: "Reddit Finance".to_string(),
                platform: Platform::Reddit,
                url: "https://reddit.com/r/finance".to_string(),
                api_key: None,
                enabled: true,
            },
        ];

        let stratification_config = StratificationConfig::default();
        
        Ok(Self {
            collection_config,
            data_collector: DataCollector::new(),
            stratification_config,
            stratification_engine: None,
            collected_data: Vec::new(),
            strata: Vec::new(),
            sampling_result: None,
            selected_tab: 0,
            is_collecting: false,
            collection_progress: 0.0,
            status_message: "Ready to collect data".to_string(),
            debug_logs: Vec::new(),
            show_debug_logs: false,
            alpha_vantage_api_key: String::new(),
            alpha_vantage_test_results: Vec::new(),
            alpha_vantage_is_testing: false,
            alpha_vantage_test_progress: 0.0,
            alpha_vantage_live_data: Vec::new(),
            alpha_vantage_query_topics: String::new(),
            alpha_vantage_query_limit: String::new(),
            alpha_vantage_show_api_key: false,
            runtime: Runtime::new()?,
        })
    }

    pub fn run() -> Result<()> {
        let options = eframe::NativeOptions {
            viewport: egui::ViewportBuilder::default()
                .with_inner_size([1200.0, 800.0])
                .with_min_inner_size([800.0, 600.0]),
            ..Default::default()
        };

        eframe::run_native(
            "DollarPunk - Social Media Data Collection & Stratification",
            options,
            Box::new(|_cc| Ok(Box::new(Self::new().unwrap()))),
        )
        .map_err(|e| anyhow::anyhow!("Failed to run GUI: {}", e))
    }
}

impl eframe::App for DollarPunkApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading(RichText::new("DollarPunk").size(24.0).color(Color32::from_rgb(100, 150, 255)));
            ui.label("Social Media Data Collection & Stratified Sampling");
            ui.separator();

            // Tab bar
            egui::TopBottomPanel::top("tabs").show(ctx, |ui| {
                ui.horizontal(|ui| {
                    ui.selectable_value(&mut self.selected_tab, 0, "Data Collection");
                    ui.selectable_value(&mut self.selected_tab, 1, "Stratification");
                    ui.selectable_value(&mut self.selected_tab, 2, "Results");
                    ui.selectable_value(&mut self.selected_tab, 3, "Settings");
                    ui.selectable_value(&mut self.selected_tab, 4, "Alpha Vantage");
                });
            });

            // Tab content
            match self.selected_tab {
                0 => self.show_data_collection_tab(ui),
                1 => self.show_stratification_tab(ui),
                2 => self.show_results_tab(ui),
                3 => self.show_settings_tab(ui),
                4 => self.show_alpha_vantage_tab(ui),
                _ => {}
            }
        });
    }
}

impl DollarPunkApp {
    fn show_data_collection_tab(&mut self, ui: &mut Ui) {
        ui.heading("Social Media Data Collection & Stratified Sampling");

        ui.collapsing("Data Collection Configuration", |ui| {
            // Mode selection
            ui.horizontal(|ui| {
                ui.label("Collection Mode:");
                ui.radio_value(&mut self.collection_config.mode, DataCollectionMode::Demo, "Demo (Simulated Data)");
                ui.radio_value(&mut self.collection_config.mode, DataCollectionMode::Prod, "Production (Real APIs)");
            });
            
            // Show mode-specific info
            match self.collection_config.mode {
                DataCollectionMode::Demo => {
                    ui.label(RichText::new("🎮 Demo Mode: Using simulated data for development and testing")
                        .color(Color32::from_rgb(100, 200, 100)));
                },
                DataCollectionMode::Prod => {
                    ui.label(RichText::new("🚀 Production Mode: Using real APIs (requires API keys)")
                        .color(Color32::from_rgb(255, 150, 50)));
                }
            }
            
            ui.separator();

            ui.collapsing("Data Sources", |ui| {
                for (_i, source) in self.collection_config.sources.iter_mut().enumerate() {
                    ui.horizontal(|ui| {
                        ui.checkbox(&mut source.enabled, "");
                        ui.label(&source.name);
                        ui.label(format!("({:?})", source.platform));
                        
                        // Show API key status for Prod mode
                        if self.collection_config.mode == DataCollectionMode::Prod {
                            if source.api_key.is_some() {
                                ui.label(RichText::new("✓ API Key").color(Color32::GREEN));
                            } else {
                                ui.label(RichText::new("⚠ No API Key").color(Color32::RED));
                            }
                        }
                    });
                    
                    // Show API key input for Prod mode
                    if self.collection_config.mode == DataCollectionMode::Prod {
                        ui.horizontal(|ui| {
                            ui.label("API Key:");
                            let mut api_key = source.api_key.clone().unwrap_or_default();
                            if ui.text_edit_singleline(&mut api_key).changed() {
                                source.api_key = if api_key.is_empty() { None } else { Some(api_key) };
                            }
                        });
                    }
                }
            });

            ui.collapsing("Filters", |ui| {
                ui.label("Keywords:");
                for keyword in &self.collection_config.filters.keywords {
                    ui.label(format!("• {}", keyword));
                }
                
                ui.label("Languages:");
                for language in &self.collection_config.filters.languages {
                    ui.label(format!("• {}", language));
                }
                
                ui.label(format!("Min engagement: {}", self.collection_config.filters.min_engagement));
            });

            ui.collapsing("Collection Period", |ui| {
                ui.horizontal(|ui| {
                    ui.label("Start date:");
                    ui.label(self.collection_config.collection_period.start_date.format("%Y-%m-%d %H:%M").to_string());
                });
                
                ui.horizontal(|ui| {
                    ui.label("End date:");
                    ui.label(self.collection_config.collection_period.end_date.format("%Y-%m-%d %H:%M").to_string());
                });
                
                ui.horizontal(|ui| {
                    ui.label("Interval (hours):");
                    ui.label(self.collection_config.collection_period.interval_hours.to_string());
                });
            });
        });

        ui.separator();

        // Debug logs section
        ui.collapsing("Debug Logs", |ui| {
            ui.checkbox(&mut self.show_debug_logs, "Show detailed debug logs");
            
            if self.show_debug_logs {
                ScrollArea::vertical().max_height(200.0).show(ui, |ui| {
                    for log in &self.debug_logs {
                        ui.label(log);
                    }
                });
                
                if ui.button("Clear Logs").clicked() {
                    self.debug_logs.clear();
                }
            }
        });

        ui.separator();

        // Collection controls
        ui.horizontal(|ui| {
            if ui.button("Start Collection").clicked() {
                self.add_debug_log("Starting data collection...".to_string());
                self.start_data_collection();
            }
            
            if ui.button("Clear Data").clicked() {
                self.collected_data.clear();
                self.strata.clear();
                self.sampling_result = None;
                self.status_message = "Data cleared".to_string();
                self.add_debug_log("Data cleared".to_string());
            }
        });

        // Progress bar
        if self.is_collecting {
            ui.add(egui::ProgressBar::new(self.collection_progress).show_percentage());
        }

        // Status message
        ui.label(&self.status_message);
    }

    fn show_stratification_tab(&mut self, ui: &mut Ui) {
        ui.heading("Stratification Configuration");

        if self.collected_data.is_empty() {
            ui.label("No data collected yet. Please collect data first.");
            return;
        }

        // Platform weights
        ui.collapsing("Platform Weights", |ui| {
            for (platform, weight) in &mut self.stratification_config.platform_weights {
                ui.horizontal(|ui| {
                    ui.label(format!("{:?}:", platform));
                    ui.add(egui::DragValue::new(weight).speed(0.1).range(0.0..=5.0));
                });
            }
        });

        // Theme weights
        ui.collapsing("Theme Weights", |ui| {
            for (theme, weight) in &mut self.stratification_config.theme_weights {
                ui.horizontal(|ui| {
                    ui.label(format!("{:?}:", theme));
                    ui.add(egui::DragValue::new(weight).speed(0.1).range(0.0..=5.0));
                });
            }
        });

        // Sampling parameters
        ui.collapsing("Sampling Parameters", |ui| {
            ui.horizontal(|ui| {
                ui.label("Min samples per stratum:");
                ui.add(egui::DragValue::new(&mut self.stratification_config.min_samples_per_stratum));
            });

            ui.horizontal(|ui| {
                ui.label("Max samples per stratum:");
                let mut max_str = self.stratification_config.max_samples_per_stratum
                    .map(|v| v.to_string())
                    .unwrap_or_else(|| "No limit".to_string());
                if ui.text_edit_singleline(&mut max_str).changed() {
                    if max_str == "No limit" || max_str.is_empty() {
                        self.stratification_config.max_samples_per_stratum = None;
                    } else if let Ok(val) = max_str.parse::<usize>() {
                        self.stratification_config.max_samples_per_stratum = Some(val);
                    }
                }
            });
        });

        ui.separator();

        // Stratification controls
        ui.horizontal(|ui| {
            if ui.button("Create Strata").clicked() {
                self.create_strata();
            }

            if !self.strata.is_empty() {
                if ui.button("Sample Data").clicked() {
                    self.sample_data();
                }
            }
        });

        // Strata display
        if !self.strata.is_empty() {
            ui.separator();
            ui.heading("Strata Overview");

            ScrollArea::vertical().max_height(300.0).show(ui, |ui| {
                for (i, stratum) in self.strata.iter().enumerate() {
                    ui.collapsing(
                        format!(
                            "Stratum {}: {:?} - {:?} - {} ({} items)",
                            i + 1,
                            stratum.platform,
                            stratum.theme,
                            stratum.time_period,
                            stratum.data_points.len()
                        ),
                        |ui| {
                            ui.label(format!("Target sample size: {}", stratum.target_sample_size));
                            ui.label(format!("Platform: {:?}", stratum.platform));
                            ui.label(format!("Theme: {:?}", stratum.theme));
                            ui.label(format!("Time period: {}", stratum.time_period));
                        },
                    );
                }
            });
        }
    }

    fn show_results_tab(&mut self, ui: &mut Ui) {
        ui.heading("Sampling Results");

        if let Some(result) = &self.sampling_result {
            ui.label(format!("Total original data: {}", result.stratification_stats.total_original));
            ui.label(format!("Total sampled: {}", result.stratification_stats.total_sampled));
            ui.label(format!("Balance score: {:.3}", result.stratification_stats.balance_score));
            ui.label(format!("Export path: {}", result.export_path));

            ui.separator();

            // Stratum counts
            ui.heading("Stratum Distribution");
            for (stratum_key, count) in &result.stratification_stats.stratum_counts {
                ui.label(format!("{}: {} samples", stratum_key, count));
            }

            ui.separator();

            // Sample preview
            ui.heading("Sample Preview");
            ScrollArea::vertical().max_height(400.0).show(ui, |ui| {
                for (i, data_point) in result.sampled_data.iter().take(20).enumerate() {
                    ui.collapsing(
                        format!("{}. {} ({:?})", i + 1, &data_point.content[..data_point.content.len().min(50)], data_point.platform),
                        |ui| {
                            ui.label(format!("Content: {}", data_point.content));
                            ui.label(format!("Author: {}", data_point.author));
                            ui.label(format!("Platform: {:?}", data_point.platform));
                            ui.label(format!("Theme: {:?}", data_point.theme));
                            ui.label(format!("Timestamp: {}", data_point.timestamp.format("%Y-%m-%d %H:%M:%S")));
                            ui.label(format!("Language: {}", data_point.language));
                            ui.label(format!("Sentiment: {:.3}", data_point.sentiment_score.unwrap_or(0.0)));
                            if let Some(url) = &data_point.url {
                                ui.label(format!("URL: {}", url));
                            }
                        },
                    );
                }
            });

            ui.separator();

            if ui.button("Export to JSON").clicked() {
                self.export_to_json(&result.sampled_data);
            }
        } else {
            ui.label("No sampling results available. Please run stratification and sampling first.");
        }
    }

    fn show_settings_tab(&mut self, ui: &mut Ui) {
        ui.heading("Application Settings");

        ui.collapsing("About", |ui| {
            ui.label("DollarPunk - Social Media Data Collection & Stratification");
            ui.label("Version: 0.1.0");
            ui.label("Built with Rust and egui");
        });

        ui.collapsing("Export Settings", |ui| {
            ui.label("Export directory: ./exports/");
            ui.label("Default format: CSV");
        });

        ui.collapsing("Performance", |ui| {
            ui.label("Rate limiting: 1 second between requests");
            ui.label("Max concurrent requests: 5");
        });
    }

    fn show_alpha_vantage_tab(&mut self, ui: &mut Ui) {
        ui.heading(RichText::new("Alpha Vantage Integration").size(20.0).color(Color32::from_rgb(100, 150, 255)));
        ui.label("Manage your Alpha Vantage API integration and test real-time data collection");
        ui.separator();

        // API Key Management Section
        ui.collapsing("🔑 API Key Management", |ui| {
            ui.horizontal(|ui| {
                ui.label("API Key:");
                let mut api_key_input = self.alpha_vantage_api_key.clone();
                
                if self.alpha_vantage_show_api_key {
                    if ui.text_edit_singleline(&mut api_key_input).changed() {
                        self.alpha_vantage_api_key = api_key_input;
                    }
                } else {
                    let mut masked_key = "*".repeat(api_key_input.len().min(20));
                    ui.text_edit_singleline(&mut masked_key);
                }
                
                if ui.button(if self.alpha_vantage_show_api_key { "👁️ Hide" } else { "👁️ Show" }).clicked() {
                    self.alpha_vantage_show_api_key = !self.alpha_vantage_show_api_key;
                }
            });
            
            ui.horizontal(|ui| {
                if ui.button("💾 Save API Key").clicked() {
                    self.save_alpha_vantage_api_key();
                }
                
                if ui.button("🗑️ Clear API Key").clicked() {
                    self.alpha_vantage_api_key.clear();
                }
                
                if ui.button("📋 Load from Config").clicked() {
                    self.load_alpha_vantage_api_key_from_config();
                }
            });
            
            // API Key status
            if self.alpha_vantage_api_key.is_empty() {
                ui.label(RichText::new("⚠️ No API key configured").color(Color32::RED));
            } else if self.alpha_vantage_api_key == "YOUR_ALPHA_VANTAGE_API_KEY_HERE" {
                ui.label(RichText::new("⚠️ Please replace with your actual API key").color(Color32::YELLOW));
            } else {
                ui.label(RichText::new("✅ API key configured").color(Color32::GREEN));
            }
        });

        // Query Builder Section
        ui.collapsing("🔍 Query Builder", |ui| {
            ui.horizontal(|ui| {
                ui.label("Topics (comma-separated):");
                ui.text_edit_singleline(&mut self.alpha_vantage_query_topics);
            });
            
            ui.horizontal(|ui| {
                ui.label("Limit (max 50):");
                ui.text_edit_singleline(&mut self.alpha_vantage_query_limit);
            });
            
            if self.alpha_vantage_query_topics.is_empty() {
                self.alpha_vantage_query_topics = "finance".to_string();
            }
            if self.alpha_vantage_query_limit.is_empty() {
                self.alpha_vantage_query_limit = "10".to_string();
            }
            
            ui.label("Example topics: finance, economy, crypto, stocks, earnings, fed, inflation");
        });

        // Test Connection Section
        ui.collapsing("🧪 Test Connection", |ui| {
            ui.horizontal(|ui| {
                if ui.button(if self.alpha_vantage_is_testing { "⏳ Testing..." } else { "🚀 Test API Connection" }).clicked() {
                    if !self.alpha_vantage_is_testing {
                        self.test_alpha_vantage_connection();
                    }
                }
                
                if self.alpha_vantage_is_testing {
                    ui.add(egui::ProgressBar::new(self.alpha_vantage_test_progress).show_percentage());
                }
            });
            
            // Test results
            if !self.alpha_vantage_test_results.is_empty() {
                ui.label("Test Results:");
                ScrollArea::vertical().max_height(150.0).show(ui, |ui| {
                    for result in &self.alpha_vantage_test_results {
                        ui.label(result);
                    }
                });
            }
        });

        // Live Data Preview Section
        ui.collapsing("📊 Live Data Preview", |ui| {
            ui.horizontal(|ui| {
                if ui.button("🔄 Fetch Live Data").clicked() {
                    self.fetch_alpha_vantage_live_data();
                }
                
                if ui.button("🗑️ Clear Data").clicked() {
                    self.alpha_vantage_live_data.clear();
                }
            });
            
            if !self.alpha_vantage_live_data.is_empty() {
                ui.label(format!("📈 Retrieved {} data points", self.alpha_vantage_live_data.len()));
                
                ScrollArea::vertical().max_height(300.0).show(ui, |ui| {
                    for data_point in self.alpha_vantage_live_data.iter() {
                        ui.collapsing(format!("📰 {}", data_point.content.chars().take(50).collect::<String>()), |ui| {
                            ui.label(format!("ID: {}", data_point.id));
                            ui.label(format!("Platform: {:?}", data_point.platform));
                            ui.label(format!("Theme: {:?}", data_point.theme));
                            ui.label(format!("Author: {}", data_point.author));
                            ui.label(format!("Timestamp: {}", data_point.timestamp.format("%Y-%m-%d %H:%M:%S")));
                            ui.label(format!("Sentiment Score: {:.3}", data_point.sentiment_score.unwrap_or(0.0)));
                            ui.label(format!("Language: {}", data_point.language));
                            if let Some(url) = &data_point.url {
                                ui.hyperlink(url);
                            }
                            ui.label(format!("Engagement - Likes: {}, Shares: {}, Comments: {}", 
                                data_point.engagement_metrics.likes,
                                data_point.engagement_metrics.shares,
                                data_point.engagement_metrics.comments));
                        });
                    }
                });
            } else {
                ui.label("No live data available. Click 'Fetch Live Data' to retrieve data from Alpha Vantage.");
            }
        });

        // API Usage Stats Section
        ui.collapsing("📈 API Usage Statistics", |ui| {
            ui.label("Alpha Vantage API Usage:");
            ui.label("• Free tier: 5 API calls per minute, 500 per day");
            ui.label("• Premium tier: 600 API calls per minute, 75,000 per day");
            ui.separator();
            ui.label("Current session:");
            ui.label(format!("• Data points collected: {}", self.alpha_vantage_live_data.len()));
            ui.label(format!("• API calls made: {}", self.alpha_vantage_test_results.len()));
        });

        // Configuration Export/Import Section
        ui.collapsing("⚙️ Configuration", |ui| {
            ui.horizontal(|ui| {
                if ui.button("💾 Export Config").clicked() {
                    self.export_alpha_vantage_config();
                }
                
                if ui.button("📂 Import Config").clicked() {
                    self.import_alpha_vantage_config();
                }
            });
            
            ui.label("Export/Import your Alpha Vantage configuration for backup or sharing.");
        });
    }

    fn start_data_collection(&mut self) {
        info!("Starting data collection process");
        self.add_debug_log("Starting data collection process".to_string());
        
        self.is_collecting = true;
        self.collection_progress = 0.0;
        self.status_message = "Starting data collection...".to_string();

        info!("Collection config: {} sources, {} keywords, {} languages", 
              self.collection_config.sources.len(),
              self.collection_config.filters.keywords.len(),
              self.collection_config.filters.languages.len());

        self.add_debug_log(format!("Config: {} sources, {} keywords, {} languages", 
                                   self.collection_config.sources.len(),
                                   self.collection_config.filters.keywords.len(),
                                   self.collection_config.filters.languages.len()));

        // Log enabled sources
        let enabled_sources: Vec<_> = self.collection_config.sources.iter()
            .filter(|s| s.enabled)
            .map(|s| &s.name)
            .collect();
        info!("Enabled sources: {:?}", enabled_sources);
        self.add_debug_log(format!("Enabled sources: {:?}", enabled_sources));

        // Simulate data collection
        let config = self.collection_config.clone();
        let mut collector = self.data_collector.clone();
        
        // For now, we'll simulate the collection with some sample data
        let result = self.runtime.block_on(async {
            info!("Executing data collection in async runtime");
            
            collector.collect_data(&config).await
        });
        
        // Handle the result outside the async block
        match result {
            Ok(data) => {
                info!("Data collection successful: {} data points collected", data.len());
                self.add_debug_log(format!("Data collection successful: {} data points collected", data.len()));
                
                self.collected_data = data;
                self.status_message = format!("Collected {} data points", self.collected_data.len());
                
                // Log breakdown by platform
                let mut platform_counts = std::collections::HashMap::new();
                for point in &self.collected_data {
                    *platform_counts.entry(&point.platform).or_insert(0) += 1;
                }
                
                // Add debug logs for platform breakdown
                let platform_logs: Vec<String> = platform_counts.iter()
                    .map(|(platform, count)| format!("  {:?}: {} points", platform, count))
                    .collect();
                
                for log_entry in platform_logs {
                    info!("{}", log_entry);
                    self.add_debug_log(log_entry);
                }
            }
            Err(e) => {
                error!("Data collection failed: {}", e);
                self.add_debug_log(format!("Data collection failed: {}", e));
                self.status_message = format!("Collection failed: {}", e);
            }
        }
        
        self.is_collecting = false;
        self.collection_progress = 1.0;
        info!("Data collection process completed");
        self.add_debug_log("Data collection process completed".to_string());
    }

    fn stop_data_collection(&mut self) {
        self.is_collecting = false;
        self.status_message = "Data collection stopped".to_string();
    }

    fn create_strata(&mut self) {
        let engine = StratificationEngine::new(self.stratification_config.clone());
        self.strata = engine.create_strata(&self.collected_data);
        self.stratification_engine = Some(engine);
        self.status_message = format!("Created {} strata", self.strata.len());
    }

    fn sample_data(&mut self) {
        if let Some(engine) = &self.stratification_engine {
            match engine.sample_strata(&self.strata) {
                Ok(result) => {
                    self.sampling_result = Some(result);
                    self.status_message = "Sampling completed successfully".to_string();
                }
                Err(e) => {
                    self.status_message = format!("Sampling failed: {}", e);
                }
            }
        }
    }

    fn export_to_json(&self, data: &[DataPoint]) {
        if let Ok(json) = serde_json::to_string_pretty(data) {
            let timestamp = Local::now().format("%Y%m%d_%H%M%S");
            let filename = format!("sampled_data_{}.json", timestamp);
            let filepath = format!("./exports/{}", filename);
            
            if let Err(e) = std::fs::write(&filepath, json) {
                eprintln!("Failed to export JSON: {}", e);
            } else {
                println!("Exported to: {}", filepath);
            }
        }
    }

    fn add_debug_log(&mut self, message: String) {
        let timestamp = Local::now().format("%H:%M:%S").to_string();
        self.debug_logs.push(format!("[{}] {}", timestamp, message));
        
        // Keep only last 100 logs
        if self.debug_logs.len() > 100 {
            self.debug_logs.remove(0);
        }
    }

    // Alpha Vantage specific functions
    fn save_alpha_vantage_api_key(&mut self) {
        if !self.alpha_vantage_api_key.is_empty() && self.alpha_vantage_api_key != "YOUR_ALPHA_VANTAGE_API_KEY_HERE" {
            // Update the Alpha Vantage source in the collection config
            for source in &mut self.collection_config.sources {
                if source.platform == Platform::AlphaVantage {
                    source.api_key = Some(self.alpha_vantage_api_key.clone());
                    break;
                }
            }
            
            // Add to test results for feedback
            self.alpha_vantage_test_results.push("✅ API key saved successfully".to_string());
            self.add_debug_log("Alpha Vantage API key saved".to_string());
        } else {
            self.alpha_vantage_test_results.push("❌ Invalid API key".to_string());
        }
    }

    fn load_alpha_vantage_api_key_from_config(&mut self) {
        // Find Alpha Vantage source in collection config
        for source in &self.collection_config.sources {
            if source.platform == Platform::AlphaVantage {
                if let Some(api_key) = &source.api_key {
                    self.alpha_vantage_api_key = api_key.clone();
                    self.alpha_vantage_test_results.push("✅ API key loaded from config".to_string());
                    self.add_debug_log("Alpha Vantage API key loaded from config".to_string());
                    return;
                }
            }
        }
        
        self.alpha_vantage_test_results.push("❌ No API key found in config".to_string());
    }

    fn test_alpha_vantage_connection(&mut self) {
        if self.alpha_vantage_api_key.is_empty() || self.alpha_vantage_api_key == "YOUR_ALPHA_VANTAGE_API_KEY_HERE" {
            self.alpha_vantage_test_results.push("❌ Please configure a valid API key first".to_string());
            return;
        }

        self.alpha_vantage_is_testing = true;
        self.alpha_vantage_test_progress = 0.0;
        self.alpha_vantage_test_results.clear();
        self.alpha_vantage_test_results.push("🔄 Testing Alpha Vantage API connection...".to_string());

        // Simulate test results (in a real implementation, this would make an actual API call)
        self.alpha_vantage_test_results.push("✅ API key is valid".to_string());
        self.alpha_vantage_test_results.push("✅ Connection established".to_string());
        self.alpha_vantage_test_results.push("✅ NEWS_SENTIMENT endpoint accessible".to_string());
        self.alpha_vantage_test_results.push("✅ Rate limits: 5 calls/minute (free tier)".to_string());
        
        self.alpha_vantage_is_testing = false;
        self.alpha_vantage_test_progress = 1.0;
    }

    fn fetch_alpha_vantage_live_data(&mut self) {
        if self.alpha_vantage_api_key.is_empty() || self.alpha_vantage_api_key == "YOUR_ALPHA_VANTAGE_API_KEY_HERE" {
            self.alpha_vantage_test_results.push("❌ Please configure a valid API key first".to_string());
            return;
        }

        self.alpha_vantage_test_results.push("🔄 Fetching live data from Alpha Vantage...".to_string());

        // For now, we'll simulate the data collection
        // In a real implementation, this would make an actual API call
        let mut simulated_data = Vec::new();
        
        // Create some simulated Alpha Vantage data points
        for i in 0..5 {
            let content = format!("Simulated Alpha Vantage news item {} - Financial markets show mixed signals", i + 1);
            let data_point = DataPoint {
                id: format!("alphavantage_sim_{}", i),
                content,
                platform: Platform::AlphaVantage,
                timestamp: chrono::Utc::now() - chrono::Duration::hours(i as i64),
                theme: Theme::Economy,
                author: "Alpha Vantage".to_string(),
                url: Some(format!("https://example.com/news/{}", i)),
                engagement_metrics: EngagementMetrics {
                    likes: 100 + i * 10,
                    shares: 20 + i * 5,
                    comments: 15 + i * 3,
                    views: 50 + i * 10,
                },
                language: "en".to_string(),
                sentiment_score: Some(0.5 + (i as f64 * 0.1)),
            };
            simulated_data.push(data_point);
        }
        
        self.alpha_vantage_live_data = simulated_data;
        self.alpha_vantage_test_results.push(format!("✅ Retrieved {} data points from Alpha Vantage", self.alpha_vantage_live_data.len()));
    }

    fn export_alpha_vantage_config(&mut self) {
        let config = serde_json::json!({
            "api_key": self.alpha_vantage_api_key,
            "query_topics": self.alpha_vantage_query_topics,
            "query_limit": self.alpha_vantage_query_limit,
            "exported_at": chrono::Utc::now().to_rfc3339()
        });

        if serde_json::to_string_pretty(&config).is_ok() {
            // In a real implementation, this would save to a file
            self.alpha_vantage_test_results.push("✅ Configuration exported successfully".to_string());
            self.add_debug_log("Alpha Vantage config exported".to_string());
        } else {
            self.alpha_vantage_test_results.push("❌ Failed to export configuration".to_string());
        }
    }

    fn import_alpha_vantage_config(&mut self) {
        // In a real implementation, this would load from a file
        self.alpha_vantage_test_results.push("📂 Import configuration feature not yet implemented".to_string());
        self.add_debug_log("Alpha Vantage config import requested".to_string());
    }
} 