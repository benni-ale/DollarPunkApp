use crate::models::*;
use crate::data_collector::DataCollector;
use crate::stratification::StratificationEngine;
use anyhow::Result;
use chrono::{Local, Utc};
use eframe::egui;
use egui::{Color32, RichText, ScrollArea, Ui};
use tokio::runtime::Runtime;

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
    
    // Runtime for async operations
    runtime: Runtime,
}

impl DollarPunkApp {
    pub fn new() -> Result<Self> {
        let mut collection_config = DataCollectionConfig::default();
        
        // Add some default sources
        collection_config.sources = vec![
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
                });
            });

            // Tab content
            match self.selected_tab {
                0 => self.show_data_collection_tab(ui),
                1 => self.show_stratification_tab(ui),
                2 => self.show_results_tab(ui),
                3 => self.show_settings_tab(ui),
                _ => {}
            }
        });
    }
}

impl DollarPunkApp {
    fn show_data_collection_tab(&mut self, ui: &mut Ui) {
        ui.heading("Data Collection Configuration");

        // Sources configuration
        ui.collapsing("Data Sources", |ui| {
            let mut to_remove = None;
            for (i, source) in self.collection_config.sources.iter_mut().enumerate() {
                ui.horizontal(|ui| {
                    ui.checkbox(&mut source.enabled, "");
                    ui.label(&source.name);
                    ui.label(format!("({:?})", source.platform));
                    if ui.button("Remove").clicked() {
                        to_remove = Some(i);
                    }
                });
            }
            if let Some(index) = to_remove {
                self.collection_config.sources.remove(index);
            }

            if ui.button("Add Source").clicked() {
                self.collection_config.sources.push(DataSource {
                    name: "New Source".to_string(),
                    platform: Platform::Other("Custom".to_string()),
                    url: "https://example.com".to_string(),
                    api_key: None,
                    enabled: true,
                });
            }
        });

        // Filters configuration
        ui.collapsing("Filters", |ui| {
            ui.label("Keywords (comma-separated):");
            let mut keywords = self.collection_config.filters.keywords.join(", ");
            if ui.text_edit_singleline(&mut keywords).changed() {
                self.collection_config.filters.keywords = keywords
                    .split(',')
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
                    .collect();
            }

            ui.label("Languages (comma-separated):");
            let mut languages = self.collection_config.filters.languages.join(", ");
            if ui.text_edit_singleline(&mut languages).changed() {
                self.collection_config.filters.languages = languages
                    .split(',')
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
                    .collect();
            }

            ui.horizontal(|ui| {
                ui.label("Min engagement:");
                ui.add(egui::DragValue::new(&mut self.collection_config.filters.min_engagement));
            });

            ui.checkbox(&mut self.collection_config.filters.exclude_retweets, "Exclude retweets");
            ui.checkbox(&mut self.collection_config.filters.exclude_ads, "Exclude ads");
        });

        // Collection period
        ui.collapsing("Collection Period", |ui| {
            ui.horizontal(|ui| {
                ui.label("Start date:");
                let start_str = self.collection_config.collection_period.start_date.format("%Y-%m-%d %H:%M").to_string();
                if ui.button(start_str).clicked() {
                    // In a real app, you'd show a date picker here
                    self.collection_config.collection_period.start_date = Utc::now() - chrono::Duration::days(7);
                }
            });

            ui.horizontal(|ui| {
                ui.label("End date:");
                let end_str = self.collection_config.collection_period.end_date.format("%Y-%m-%d %H:%M").to_string();
                if ui.button(end_str).clicked() {
                    self.collection_config.collection_period.end_date = Utc::now();
                }
            });

            ui.horizontal(|ui| {
                ui.label("Interval (hours):");
                ui.add(egui::DragValue::new(&mut self.collection_config.collection_period.interval_hours));
            });
        });

        ui.separator();

        // Collection controls
        ui.horizontal(|ui| {
            if !self.is_collecting {
                if ui.button("Start Collection").clicked() {
                    self.start_data_collection();
                }
            } else {
                if ui.button("Stop Collection").clicked() {
                    self.stop_data_collection();
                }
            }

            if ui.button("Clear Data").clicked() {
                self.collected_data.clear();
                self.strata.clear();
                self.sampling_result = None;
                self.status_message = "Data cleared".to_string();
            }
        });

        // Progress bar
        if self.is_collecting {
            ui.add(egui::ProgressBar::new(self.collection_progress).show_percentage());
        }

        // Status
        ui.label(&self.status_message);

        // Data summary
        if !self.collected_data.is_empty() {
            ui.separator();
            ui.heading("Collected Data Summary");
            
            let platform_counts: std::collections::HashMap<_, _> = self.collected_data
                .iter()
                .fold(std::collections::HashMap::new(), |mut acc, dp| {
                    *acc.entry(&dp.platform).or_insert(0) += 1;
                    acc
                });

            for (platform, count) in platform_counts {
                ui.label(format!("{:?}: {} items", platform, count));
            }

            ui.label(format!("Total: {} data points", self.collected_data.len()));
        }
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

    fn start_data_collection(&mut self) {
        self.is_collecting = true;
        self.collection_progress = 0.0;
        self.status_message = "Starting data collection...".to_string();

        // Simulate data collection
        let config = self.collection_config.clone();
        let mut collector = self.data_collector.clone();
        
        // For now, we'll simulate the collection with some sample data
        self.runtime.block_on(async {
            match collector.collect_data(&config).await {
                Ok(data) => {
                    self.collected_data = data;
                    self.status_message = format!("Collected {} data points", self.collected_data.len());
                }
                Err(e) => {
                    self.status_message = format!("Collection failed: {}", e);
                }
            }
        });
        
        self.is_collecting = false;
        self.collection_progress = 1.0;
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
} 