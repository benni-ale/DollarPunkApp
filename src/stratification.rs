use crate::models::*;
use anyhow::Result;
use chrono::{DateTime, Utc};
use rand::seq::SliceRandom;
use std::collections::HashMap;
use tracing::info;

pub struct StratificationEngine {
    config: StratificationConfig,
}

impl StratificationEngine {
    pub fn new(config: StratificationConfig) -> Self {
        Self { config }
    }

    pub fn create_strata(&self, data: &[DataPoint]) -> Vec<Stratum> {
        info!("Creating strata for {} data points", data.len());
        let mut strata = Vec::new();
        let mut stratum_map: HashMap<String, Vec<DataPoint>> = HashMap::new();

        // Group data points by platform, theme, and time period
        for data_point in data {
            let time_period = self.get_time_period(&data_point.timestamp);
            let stratum_key = format!(
                "{:?}_{:?}_{}",
                data_point.platform,
                data_point.theme,
                time_period
            );

            stratum_map
                .entry(stratum_key)
                .or_insert_with(Vec::new)
                .push(data_point.clone());
        }

        info!("Found {} unique strata", stratum_map.len());

        // Create stratum objects
        for (key, data_points) in stratum_map {
            let parts: Vec<&str> = key.split('_').collect();
            if parts.len() >= 3 {
                let platform = self.parse_platform(parts[0]);
                let theme = self.parse_theme(parts[1]);
                let time_period = parts[2..].join("_");

                let target_sample_size = self.calculate_target_sample_size(
                    data_points.len(),
                    &platform,
                    &theme,
                    &time_period,
                );

                info!("Stratum {}: {} points -> target {} samples", key, data_points.len(), target_sample_size);

                strata.push(Stratum {
                    platform,
                    theme,
                    time_period,
                    data_points,
                    target_sample_size,
                });
            }
        }

        info!("Created {} strata successfully", strata.len());
        strata
    }

    pub fn sample_strata(&self, strata: &[Stratum]) -> Result<SamplingResult> {
        let mut sampled_data = Vec::new();
        let mut stratum_counts = HashMap::new();

        for stratum in strata {
            let sample_size = std::cmp::min(stratum.target_sample_size, stratum.data_points.len());
            
            if sample_size > 0 {
                let mut rng = rand::thread_rng();
                let sampled: Vec<DataPoint> = stratum
                    .data_points
                    .choose_multiple(&mut rng, sample_size)
                    .cloned()
                    .collect();

                sampled_data.extend(sampled);

                let stratum_key = format!(
                    "{:?}_{:?}_{}",
                    stratum.platform, stratum.theme, stratum.time_period
                );
                stratum_counts.insert(stratum_key, sample_size);
            }
        }

        let total_original: usize = strata.iter().map(|s| s.data_points.len()).sum();
        let total_sampled = sampled_data.len();
        let balance_score = self.calculate_balance_score(&stratum_counts, total_sampled);

        let stats = StratificationStats {
            total_original,
            total_sampled,
            stratum_counts,
            balance_score,
        };

        let export_path = self.export_sampled_data(&sampled_data)?;

        Ok(SamplingResult {
            sampled_data,
            stratification_stats: stats,
            export_path,
        })
    }

    fn get_time_period(&self, timestamp: &DateTime<Utc>) -> String {
        let now = Utc::now();
        let hours_diff = (now - *timestamp).num_hours();

        if hours_diff < 24 {
            "last_24h".to_string()
        } else if hours_diff < 168 {
            "last_week".to_string()
        } else if hours_diff < 720 {
            "last_month".to_string()
        } else {
            "older".to_string()
        }
    }

    fn calculate_target_sample_size(
        &self,
        stratum_size: usize,
        platform: &Platform,
        theme: &Theme,
        time_period: &str,
    ) -> usize {
        let platform_weight = self.config.platform_weights.get(platform).unwrap_or(&1.0);
        let theme_weight = self.config.theme_weights.get(theme).unwrap_or(&1.0);
        let time_weight = self.get_time_period_weight(time_period);

        let base_size = (stratum_size as f64 * platform_weight * theme_weight * time_weight) as usize;
        
        let min_size = self.config.min_samples_per_stratum;
        let max_size = self.config.max_samples_per_stratum.unwrap_or(usize::MAX);

        // Ensure min_size doesn't exceed max_size or stratum_size
        let effective_min = min_size.min(max_size).min(stratum_size);
        let effective_max = max_size.min(stratum_size);

        info!("Target calculation: stratum_size={}, base_size={}, min_size={}, max_size={}, effective_min={}, effective_max={}", 
              stratum_size, base_size, min_size, max_size, effective_min, effective_max);

        // Ensure min <= max before using clamp
        if effective_min <= effective_max {
            let result = base_size.clamp(effective_min, effective_max);
            info!("  Result: {}", result);
            result
        } else {
            // Fallback: use stratum_size if min > max
            info!("  Fallback: using stratum_size {}", stratum_size);
            stratum_size
        }
    }

    fn get_time_period_weight(&self, time_period: &str) -> f64 {
        match time_period {
            "last_24h" => 1.5,  // Higher weight for recent content
            "last_week" => 1.2,
            "last_month" => 1.0,
            "older" => 0.5,     // Lower weight for older content
            _ => 1.0,
        }
    }

    fn parse_platform(&self, platform_str: &str) -> Platform {
        match platform_str {
            "Twitter" => Platform::Twitter,
            "Facebook" => Platform::Facebook,
            "Instagram" => Platform::Instagram,
            "LinkedIn" => Platform::LinkedIn,
            "Reddit" => Platform::Reddit,
            "NewsWebsite" => Platform::NewsWebsite,
            "RSS" => Platform::RSS,
            "YouTube" => Platform::YouTube,
            "TikTok" => Platform::TikTok,
            _ => Platform::Other(platform_str.to_string()),
        }
    }

    fn parse_theme(&self, theme_str: &str) -> Theme {
        match theme_str {
            "Politics" => Theme::Politics,
            "Economy" => Theme::Economy,
            "Technology" => Theme::Technology,
            "Sports" => Theme::Sports,
            "Entertainment" => Theme::Entertainment,
            "Health" => Theme::Health,
            "Science" => Theme::Science,
            "Environment" => Theme::Environment,
            "Education" => Theme::Education,
            _ => Theme::Other(theme_str.to_string()),
        }
    }

    fn calculate_balance_score(&self, stratum_counts: &HashMap<String, usize>, total: usize) -> f64 {
        if total == 0 || stratum_counts.is_empty() {
            return 0.0;
        }

        let expected_per_stratum = total as f64 / stratum_counts.len() as f64;
        let mut variance = 0.0;

        for count in stratum_counts.values() {
            let diff = *count as f64 - expected_per_stratum;
            variance += diff * diff;
        }

        let standard_deviation = (variance / stratum_counts.len() as f64).sqrt();
        let coefficient_of_variation = standard_deviation / expected_per_stratum;

        // Convert to a balance score (0 = perfectly balanced, 1 = completely unbalanced)
        (1.0 - coefficient_of_variation).max(0.0)
    }

    fn export_sampled_data(&self, data: &[DataPoint]) -> Result<String> {
        use std::fs::File;
        use std::io::Write;
        use chrono::Local;

        let timestamp = Local::now().format("%Y%m%d_%H%M%S");
        let filename = format!("sampled_data_{}.csv", timestamp);
        let filepath = format!("./exports/{}", filename);

        // Create exports directory if it doesn't exist
        std::fs::create_dir_all("./exports")?;

        let mut file = File::create(&filepath)?;
        
        // Write CSV header
        writeln!(
            file,
            "id,content,platform,theme,author,timestamp,language,likes,shares,comments,views,sentiment_score,url"
        )?;

        // Write data rows
        for data_point in data {
            writeln!(
                file,
                "\"{}\",\"{}\",\"{:?}\",\"{:?}\",\"{}\",\"{}\",\"{}\",{},{},{},{},{:.3},\"{}\"",
                data_point.id,
                data_point.content.replace("\"", "\"\""),
                data_point.platform,
                data_point.theme,
                data_point.author,
                data_point.timestamp.format("%Y-%m-%d %H:%M:%S"),
                data_point.language,
                data_point.engagement_metrics.likes,
                data_point.engagement_metrics.shares,
                data_point.engagement_metrics.comments,
                data_point.engagement_metrics.views,
                data_point.sentiment_score.unwrap_or(0.0),
                data_point.url.as_deref().unwrap_or("")
            )?;
        }

        Ok(filepath)
    }

    pub fn get_stratification_summary(&self, strata: &[Stratum]) -> String {
        let mut summary = String::new();
        summary.push_str("=== STRATIFICATION SUMMARY ===\n\n");

        let total_data_points: usize = strata.iter().map(|s| s.data_points.len()).sum();
        summary.push_str(&format!("Total data points: {}\n", total_data_points));
        summary.push_str(&format!("Number of strata: {}\n\n", strata.len()));

        // Group by platform
        let mut platform_stats: HashMap<Platform, (usize, usize)> = HashMap::new();
        for stratum in strata {
            let (count, target) = platform_stats
                .entry(stratum.platform.clone())
                .or_insert((0, 0));
            *count += stratum.data_points.len();
            *target += stratum.target_sample_size;
        }

        summary.push_str("By Platform:\n");
        for (platform, (count, target)) in platform_stats {
            summary.push_str(&format!("  {:?}: {} points -> {} target samples\n", platform, count, target));
        }

        // Group by theme
        let mut theme_stats: HashMap<Theme, (usize, usize)> = HashMap::new();
        for stratum in strata {
            let (count, target) = theme_stats
                .entry(stratum.theme.clone())
                .or_insert((0, 0));
            *count += stratum.data_points.len();
            *target += stratum.target_sample_size;
        }

        summary.push_str("\nBy Theme:\n");
        for (theme, (count, target)) in theme_stats {
            summary.push_str(&format!("  {:?}: {} points -> {} target samples\n", theme, count, target));
        }

        // Time periods
        let mut time_stats: HashMap<String, (usize, usize)> = HashMap::new();
        for stratum in strata {
            let (count, target) = time_stats
                .entry(stratum.time_period.clone())
                .or_insert((0, 0));
            *count += stratum.data_points.len();
            *target += stratum.target_sample_size;
        }

        summary.push_str("\nBy Time Period:\n");
        for (time_period, (count, target)) in time_stats {
            summary.push_str(&format!("  {}: {} points -> {} target samples\n", time_period, count, target));
        }

        summary
    }
} 