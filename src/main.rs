mod models;
mod data_collector;
mod stratification;
mod gui;
mod config;
mod cli;

use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    // Check if CLI arguments are provided
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() > 1 {
        // Run CLI mode
        cli::Cli::run().await
    } else {
        // Run GUI mode
        gui::DollarPunkApp::run()
    }
}
