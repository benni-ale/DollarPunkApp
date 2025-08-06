use crate::models::*;
use anyhow::Result;
use chrono::{DateTime, Utc};
use sqlx::{mysql::MySqlPoolOptions, MySql, MySqlPool, Row};
use tracing::info;
use uuid::Uuid;

pub struct DatabaseManager {
    pool: MySqlPool,
}

impl DatabaseManager {
    pub fn new_simulated() -> Self {
        info!("Creating simulated database manager for GUI");
        // Create a dummy pool that won't be used
        let pool = MySqlPoolOptions::new()
            .max_connections(1)
            .connect_lazy("mysql://dummy:dummy@localhost/dummy")
            .expect("Failed to create dummy pool");
        
        Self { pool }
    }

    pub async fn new(database_url: &str) -> Result<Self> {
        let pool = MySqlPoolOptions::new()
            .max_connections(5)
            .connect(database_url)
            .await?;

        info!("Database connection established");
        
        // Initialize database schema
        Self::init_schema(&pool).await?;
        
        Ok(Self { pool })
    }

    async fn init_schema(pool: &MySqlPool) -> Result<()> {
        // Create tables if they don't exist
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS data_points (
                id VARCHAR(255) PRIMARY KEY,
                content TEXT NOT NULL,
                platform VARCHAR(50) NOT NULL,
                timestamp DATETIME(3) NOT NULL,
                theme VARCHAR(50) NOT NULL,
                author VARCHAR(255) NOT NULL,
                url TEXT,
                engagement_likes INT DEFAULT 0,
                engagement_shares INT DEFAULT 0,
                engagement_comments INT DEFAULT 0,
                engagement_views INT DEFAULT 0,
                language VARCHAR(10) DEFAULT 'en',
                sentiment_score DECIMAL(5,4),
                created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
                updated_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
                INDEX idx_platform (platform),
                INDEX idx_theme (theme),
                INDEX idx_timestamp (timestamp),
                INDEX idx_sentiment (sentiment_score)
            )
            "#,
        )
        .execute(pool)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS collection_sessions (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status ENUM('running', 'completed', 'failed', 'cancelled') DEFAULT 'running',
                start_time DATETIME(3) NOT NULL,
                end_time DATETIME(3),
                total_points INT DEFAULT 0,
                created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
                updated_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
                INDEX idx_status (status),
                INDEX idx_start_time (start_time)
            )
            "#,
        )
        .execute(pool)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS alpha_vantage_queries (
                id VARCHAR(36) PRIMARY KEY,
                session_id VARCHAR(36),
                topics TEXT NOT NULL,
                limit_count INT DEFAULT 50,
                api_key_hash VARCHAR(64) NOT NULL,
                query_time DATETIME(3) NOT NULL,
                points_retrieved INT DEFAULT 0,
                status ENUM('success', 'failed', 'partial') DEFAULT 'success',
                error_message TEXT,
                created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
                FOREIGN KEY (session_id) REFERENCES collection_sessions(id) ON DELETE SET NULL,
                INDEX idx_session (session_id),
                INDEX idx_query_time (query_time)
            )
            "#,
        )
        .execute(pool)
        .await?;

        info!("Database schema initialized");
        Ok(())
    }

    /// Insert or update a data point (idempotent operation)
    pub async fn upsert_data_point(&self, data_point: &DataPoint) -> Result<bool> {
        let result = sqlx::query(
            r#"
            INSERT INTO data_points (
                id, content, platform, timestamp, theme, author, url,
                engagement_likes, engagement_shares, engagement_comments, engagement_views,
                language, sentiment_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                content = VALUES(content),
                platform = VALUES(platform),
                timestamp = VALUES(timestamp),
                theme = VALUES(theme),
                author = VALUES(author),
                url = VALUES(url),
                engagement_likes = VALUES(engagement_likes),
                engagement_shares = VALUES(engagement_shares),
                engagement_comments = VALUES(engagement_comments),
                engagement_views = VALUES(engagement_views),
                language = VALUES(language),
                sentiment_score = VALUES(sentiment_score),
                updated_at = CURRENT_TIMESTAMP(3)
            "#,
        )
        .bind(&data_point.id)
        .bind(&data_point.content)
        .bind(format!("{:?}", data_point.platform))
        .bind(data_point.timestamp)
        .bind(format!("{:?}", data_point.theme))
        .bind(&data_point.author)
        .bind(&data_point.url)
        .bind(data_point.engagement_metrics.likes)
        .bind(data_point.engagement_metrics.shares)
        .bind(data_point.engagement_metrics.comments)
        .bind(data_point.engagement_metrics.views)
        .bind(&data_point.language)
        .bind(data_point.sentiment_score)
        .execute(&self.pool)
        .await?;

        let was_inserted = result.rows_affected() == 1;
        if was_inserted {
            info!("New data point inserted: {}", data_point.id);
        } else {
            info!("Data point updated: {}", data_point.id);
        }

        Ok(was_inserted)
    }

    /// Insert multiple data points in a batch (idempotent)
    pub async fn upsert_data_points(&self, data_points: &[DataPoint]) -> Result<DatabaseInsertResult> {
        if data_points.is_empty() {
            return Ok(DatabaseInsertResult {
                inserted: 0,
                updated: 0,
                total: 0,
            });
        }

        let mut inserted = 0;
        let mut updated = 0;

        for data_point in data_points {
            let was_inserted = self.upsert_data_point(data_point).await?;
            if was_inserted {
                inserted += 1;
            } else {
                updated += 1;
            }
        }

        let result = DatabaseInsertResult {
            inserted,
            updated,
            total: data_points.len(),
        };

        info!("Batch insert completed: {} inserted, {} updated, {} total", 
              result.inserted, result.updated, result.total);

        Ok(result)
    }

    /// Create a new collection session
    pub async fn create_session(&self, name: &str, description: Option<&str>) -> Result<String> {
        let session_id = Uuid::new_v4().to_string();
        let start_time = Utc::now();

        sqlx::query(
            r#"
            INSERT INTO collection_sessions (id, name, description, start_time)
            VALUES (?, ?, ?, ?)
            "#,
        )
        .bind(&session_id)
        .bind(name)
        .bind(description)
        .bind(start_time)
        .execute(&self.pool)
        .await?;

        info!("Created collection session: {} ({})", name, session_id);
        Ok(session_id)
    }

    /// Update session status
    pub async fn update_session_status(&self, session_id: &str, status: &str, total_points: Option<i32>) -> Result<()> {
        let end_time = if status == "completed" || status == "failed" || status == "cancelled" {
            Some(Utc::now())
        } else {
            None
        };

        if let Some(end_time) = end_time {
            sqlx::query(
                r#"
                UPDATE collection_sessions 
                SET status = ?, end_time = ?, total_points = COALESCE(?, total_points)
                WHERE id = ?
                "#,
            )
            .bind(status)
            .bind(end_time)
            .bind(total_points)
            .bind(session_id)
            .execute(&self.pool)
            .await?;
        } else {
            sqlx::query(
                r#"
                UPDATE collection_sessions 
                SET status = ?, total_points = COALESCE(?, total_points)
                WHERE id = ?
                "#,
            )
            .bind(status)
            .bind(total_points)
            .bind(session_id)
            .execute(&self.pool)
            .await?;
        }

        info!("Updated session {} status to {}", session_id, status);
        Ok(())
    }

    /// Log Alpha Vantage query
    pub async fn log_alpha_vantage_query(
        &self,
        session_id: Option<&str>,
        topics: &str,
        limit_count: i32,
        api_key_hash: &str,
        points_retrieved: i32,
        status: &str,
        error_message: Option<&str>,
    ) -> Result<String> {
        let query_id = Uuid::new_v4().to_string();
        let query_time = Utc::now();

        sqlx::query(
            r#"
            INSERT INTO alpha_vantage_queries (
                id, session_id, topics, limit_count, api_key_hash, query_time,
                points_retrieved, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(&query_id)
        .bind(session_id)
        .bind(topics)
        .bind(limit_count)
        .bind(api_key_hash)
        .bind(query_time)
        .bind(points_retrieved)
        .bind(status)
        .bind(error_message)
        .execute(&self.pool)
        .await?;

        info!("Logged Alpha Vantage query: {} ({} points)", query_id, points_retrieved);
        Ok(query_id)
    }

    /// Get data points with optional filters
    pub async fn get_data_points(
        &self,
        limit: Option<i32>,
        platform: Option<&str>,
        theme: Option<&str>,
        since: Option<DateTime<Utc>>,
    ) -> Result<Vec<DataPoint>> {
        let mut query = String::from(
            "SELECT id, content, platform, timestamp, theme, author, url, 
                    engagement_likes, engagement_shares, engagement_comments, engagement_views,
                    language, sentiment_score 
             FROM data_points WHERE 1=1"
        );

        let mut conditions = Vec::new();
        let mut params: Vec<Box<dyn sqlx::Encode<'_, MySql> + Send + Sync>> = Vec::new();

        if let Some(platform) = platform {
            conditions.push("platform = ?");
            params.push(Box::new(platform.to_string()));
        }

        if let Some(theme) = theme {
            conditions.push("theme = ?");
            params.push(Box::new(theme.to_string()));
        }

        if let Some(since) = since {
            conditions.push("timestamp >= ?");
            params.push(Box::new(since));
        }

        if !conditions.is_empty() {
            query.push_str(" AND ");
            query.push_str(&conditions.join(" AND "));
        }

        query.push_str(" ORDER BY timestamp DESC");

        if let Some(limit) = limit {
            query.push_str(" LIMIT ?");
            params.push(Box::new(limit));
        }

        let rows = sqlx::query(&query)
            .fetch_all(&self.pool)
            .await?;

        let mut data_points = Vec::new();
        for row in rows {
            let data_point = DataPoint {
                id: row.try_get("id")?,
                content: row.try_get("content")?,
                platform: Self::parse_platform(row.try_get("platform")?),
                timestamp: row.try_get("timestamp")?,
                theme: Self::parse_theme(row.try_get("theme")?),
                author: row.try_get("author")?,
                url: row.try_get("url")?,
                engagement_metrics: EngagementMetrics {
                    likes: row.try_get("engagement_likes")?,
                    shares: row.try_get("engagement_shares")?,
                    comments: row.try_get("engagement_comments")?,
                    views: row.try_get("engagement_views")?,
                },
                language: row.try_get("language")?,
                sentiment_score: row.try_get("sentiment_score")?,
            };
            data_points.push(data_point);
        }

        Ok(data_points)
    }

    /// Get database statistics
    pub async fn get_statistics(&self) -> Result<DatabaseStatistics> {
        let total_points: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM data_points")
            .fetch_one(&self.pool)
            .await?;

        let today_points: i64 = sqlx::query_scalar(
            "SELECT COUNT(*) FROM data_points WHERE DATE(timestamp) = CURDATE()"
        )
        .fetch_one(&self.pool)
        .await?;

        let platform_stats = sqlx::query(
            "SELECT platform, COUNT(*) as count FROM data_points GROUP BY platform ORDER BY count DESC"
        )
        .fetch_all(&self.pool)
        .await?;

        let mut platform_counts = std::collections::HashMap::new();
        for row in platform_stats {
            let platform: String = row.try_get("platform")?;
            let count: i64 = row.try_get("count")?;
            platform_counts.insert(platform, count);
        }

        let avg_sentiment: Option<f64> = sqlx::query_scalar(
            "SELECT AVG(sentiment_score) FROM data_points WHERE sentiment_score IS NOT NULL"
        )
        .fetch_one(&self.pool)
        .await?;

        Ok(DatabaseStatistics {
            total_points,
            today_points,
            platform_counts,
            average_sentiment: avg_sentiment,
        })
    }

    fn parse_platform(platform_str: String) -> Platform {
        match platform_str.as_str() {
            "Twitter" => Platform::Twitter,
            "Facebook" => Platform::Facebook,
            "Instagram" => Platform::Instagram,
            "LinkedIn" => Platform::LinkedIn,
            "Reddit" => Platform::Reddit,
            "NewsWebsite" => Platform::NewsWebsite,
            "RSS" => Platform::RSS,
            "YouTube" => Platform::YouTube,
            "TikTok" => Platform::TikTok,
            "AlphaVantage" => Platform::AlphaVantage,
            other => Platform::Other(other.to_string()),
        }
    }

    fn parse_theme(theme_str: String) -> Theme {
        match theme_str.as_str() {
            "Politics" => Theme::Politics,
            "Economy" => Theme::Economy,
            "Technology" => Theme::Technology,
            "Sports" => Theme::Sports,
            "Entertainment" => Theme::Entertainment,
            "Health" => Theme::Health,
            "Science" => Theme::Science,
            "Environment" => Theme::Environment,
            "Education" => Theme::Education,
            other => Theme::Other(other.to_string()),
        }
    }
}

#[derive(Debug)]
pub struct DatabaseInsertResult {
    pub inserted: usize,
    pub updated: usize,
    pub total: usize,
}

#[derive(Debug)]
pub struct DatabaseStatistics {
    pub total_points: i64,
    pub today_points: i64,
    pub platform_counts: std::collections::HashMap<String, i64>,
    pub average_sentiment: Option<f64>,
} 