mod models;
mod data_collector;
mod stratification;
mod gui;
mod alpha_vantage;

use anyhow::Result;

fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    // Run the GUI application
    gui::DollarPunkApp::run()
}
