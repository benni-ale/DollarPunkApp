# DollarPunk Visualization Dashboard

A modern, interactive web-based dashboard for visualizing financial news data from the DollarPunk project. Built with Streamlit and Plotly for rich, interactive visualizations.

## Features

### 📊 Dashboard Overview
- **Key Metrics**: Total articles, unique tickers, unique topics, average sentiment
- **Sentiment Distribution**: Interactive pie charts showing sentiment breakdown
- **Real-time Filtering**: Date range, ticker, and topic filters

### 📈 Tickers Analysis
- **Most Mentioned Tickers**: Horizontal bar chart of top 15 tickers
- **Sentiment by Ticker**: Average sentiment scores for each ticker
- **Sentiment Trends**: Time series analysis of sentiment for top 5 tickers
- **Relevance Analysis**: Distribution and average relevance scores

### 🏷️ Topics Analysis
- **Topic Distribution**: Pie chart and bar chart of topic frequency
- **Sentiment vs Frequency**: Scatter plot showing relationship between sentiment and article count
- **Topic Trends**: Time series analysis of topic popularity

### 📰 News Feed
- **Recent Articles**: Expandable list of latest articles
- **Article Details**: Title, summary, source, authors, sentiment scores
- **Direct Links**: Clickable URLs to full articles

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the visualization service:**
   ```bash
   cd visualisation
   docker-compose up --build
   ```

2. **Access the dashboard:**
   Open your browser and navigate to `http://localhost:8501`

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## Data Requirements

The application expects the following CSV files in the `../output/processed/` directory:
- `tickers.csv` - Ticker-specific news data
- `topics.csv` - Topic-categorized news data

### Expected CSV Structure

#### tickers.csv
- `url` - Article URL
- `title` - Article title
- `summary` - Article summary
- `authors` - Author information
- `time_published` - Publication timestamp
- `source` - News source
- `overall_sentiment_score` - Overall sentiment score
- `overall_sentiment_label` - Sentiment label
- `ticker` - Stock ticker symbol
- `relevance_score` - Relevance score
- `ticker_sentiment_score` - Ticker-specific sentiment
- `ticker_sentiment_label` - Ticker sentiment label

#### topics.csv
- `url` - Article URL
- `title` - Article title
- `summary` - Article summary
- `authors` - Author information
- `time_published` - Publication timestamp
- `source` - News source
- `overall_sentiment_score` - Overall sentiment score
- `overall_sentiment_label` - Sentiment label
- `topic` - Topic category
- `relevance_score` - Relevance score

## Interactive Features

### Filters
- **Date Range**: Filter articles by publication date
- **Ticker Selection**: Choose specific tickers to analyze
- **Topic Selection**: Filter by specific topics

### Visualizations
- **Interactive Charts**: Hover for details, zoom, pan
- **Responsive Design**: Adapts to different screen sizes
- **Real-time Updates**: Data refreshes automatically

### Navigation
- **Tabbed Interface**: Organized sections for different analyses
- **Expandable Articles**: Click to view detailed article information
- **Direct Links**: Access full articles with one click

## Technical Stack

- **Frontend**: Streamlit
- **Visualization**: Plotly
- **Data Processing**: Pandas, NumPy
- **Containerization**: Docker
- **Styling**: Custom CSS

## Customization

### Adding New Visualizations
1. Create new functions in `app.py`
2. Add new tabs or sections as needed
3. Update the main function to include new features

### Styling
- Modify the CSS in the `st.markdown()` section
- Update color schemes and layouts
- Add custom components as needed

### Data Sources
- Update the `load_data()` function to read from different sources
- Add support for additional file formats
- Implement real-time data streaming

## Troubleshooting

### Common Issues

1. **Data not loading:**
   - Ensure CSV files exist in the correct location
   - Check file permissions
   - Verify CSV structure matches expected format

2. **Docker issues:**
   - Ensure Docker is running
   - Check if port 8501 is available
   - Verify network connectivity

3. **Performance issues:**
   - Reduce data size for testing
   - Use data caching effectively
   - Optimize queries and filters

### Logs
- Check Docker logs: `docker-compose logs visualization`
- Streamlit logs appear in the terminal when running locally

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the DollarPunk ecosystem and follows the same licensing terms.
