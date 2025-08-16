import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import re
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="DollarPunk Financial Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the CSV data"""
    try:
        tickers_df = pd.read_csv('/app/data/processed/tickers.csv')
        topics_df = pd.read_csv('/app/data/processed/topics.csv')
        return tickers_df, topics_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

def clean_timestamp(df):
    """Clean and convert timestamp columns"""
    if 'time_published' in df.columns:
        df['time_published'] = pd.to_datetime(df['time_published'], format='%Y%m%dT%H%M%S', errors='coerce')
    if 'ingestion_timestamp' in df.columns:
        df['ingestion_timestamp'] = pd.to_datetime(df['ingestion_timestamp'], errors='coerce')
    return df

def main():
    # Header
    st.markdown('<h1 class="main-header">📈 DollarPunk Financial Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    tickers_df, topics_df = load_data()
    
    if tickers_df is None or topics_df is None:
        st.error("Failed to load data. Please ensure the CSV files exist in the correct location.")
        return
    
    # Clean timestamps
    tickers_df = clean_timestamp(tickers_df)
    topics_df = clean_timestamp(topics_df)
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    if 'time_published' in tickers_df.columns:
        min_date = tickers_df['time_published'].min()
        max_date = tickers_df['time_published'].max()
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            tickers_df = tickers_df[
                (tickers_df['time_published'].dt.date >= start_date) &
                (tickers_df['time_published'].dt.date <= end_date)
            ]
            topics_df = topics_df[
                (topics_df['time_published'].dt.date >= start_date) &
                (topics_df['time_published'].dt.date <= end_date)
            ]
    
    # Ticker filter
    if 'ticker' in tickers_df.columns:
        # Filter out NaN values and convert to strings for sorting
        available_tickers = tickers_df['ticker'].dropna().astype(str).unique()
        available_tickers = sorted([ticker for ticker in available_tickers if ticker != 'nan' and ticker.strip()])
        selected_tickers = st.sidebar.multiselect(
            "Select Tickers",
            options=available_tickers,
            default=available_tickers[:10] if len(available_tickers) > 10 else available_tickers
        )
        if selected_tickers:
            tickers_df = tickers_df[tickers_df['ticker'].isin(selected_tickers)]
    
    # Topic filter
    if 'topic' in topics_df.columns:
        # Filter out NaN values and convert to strings for sorting
        available_topics = topics_df['topic'].dropna().astype(str).unique()
        available_topics = sorted([topic for topic in available_topics if topic != 'nan' and topic.strip()])
        selected_topics = st.sidebar.multiselect(
            "Select Topics",
            options=available_topics,
            default=available_topics[:5] if len(available_topics) > 5 else available_topics
        )
        if selected_topics:
            topics_df = topics_df[topics_df['topic'].isin(selected_topics)]
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Tickers Analysis", "🏷️ Topics Analysis", "📰 News Feed"])
    
    with tab1:
        st.header("📊 Dashboard Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Articles", len(tickers_df))
        
        with col2:
            unique_tickers = tickers_df['ticker'].dropna().nunique() if 'ticker' in tickers_df.columns else 0
            st.metric("Unique Tickers", unique_tickers)
        
        with col3:
            unique_topics = topics_df['topic'].dropna().nunique() if 'topic' in topics_df.columns else 0
            st.metric("Unique Topics", unique_topics)
        
        with col4:
            avg_sentiment = tickers_df['overall_sentiment_score'].mean() if 'overall_sentiment_score' in tickers_df.columns else 0
            st.metric("Avg Sentiment", f"{avg_sentiment:.3f}")
        
        # Sentiment distribution
        col1, col2 = st.columns(2)
        
        with col1:
            if 'overall_sentiment_label' in tickers_df.columns:
                sentiment_counts = tickers_df['overall_sentiment_label'].value_counts()
                fig = px.pie(
                    values=sentiment_counts.values,
                    names=sentiment_counts.index,
                    title="Overall Sentiment Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'ticker_sentiment_label' in tickers_df.columns:
                ticker_sentiment_counts = tickers_df['ticker_sentiment_label'].value_counts()
                fig = px.bar(
                    x=ticker_sentiment_counts.index,
                    y=ticker_sentiment_counts.values,
                    title="Ticker-Specific Sentiment Distribution",
                    color=ticker_sentiment_counts.values,
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("📈 Tickers Analysis")
        
        if 'ticker' in tickers_df.columns:
            # Top tickers by mention count
            col1, col2 = st.columns(2)
            
            with col1:
                # Filter out NaN values for ticker analysis
                ticker_counts = tickers_df['ticker'].dropna().value_counts().head(15)
                fig = px.bar(
                    x=ticker_counts.values,
                    y=ticker_counts.index,
                    orientation='h',
                    title="Top 15 Most Mentioned Tickers",
                    color=ticker_counts.values,
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Average sentiment by ticker
                ticker_sentiment = tickers_df.dropna(subset=['ticker']).groupby('ticker')['overall_sentiment_score'].mean().sort_values(ascending=False)
                fig = px.bar(
                    x=ticker_sentiment.index,
                    y=ticker_sentiment.values,
                    title="Average Sentiment by Ticker",
                    color=ticker_sentiment.values,
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Sentiment over time for top tickers
            if 'time_published' in tickers_df.columns:
                top_tickers = tickers_df['ticker'].dropna().value_counts().head(5).index
                top_tickers_data = tickers_df[tickers_df['ticker'].isin(top_tickers)]
                
                fig = px.line(
                    top_tickers_data,
                    x='time_published',
                    y='overall_sentiment_score',
                    color='ticker',
                    title="Sentiment Trends for Top 5 Tickers",
                    markers=True
                )
                fig.update_xaxes(title_text="Date")
                fig.update_yaxes(title_text="Sentiment Score")
                st.plotly_chart(fig, use_container_width=True)
            
            # Relevance score analysis
            if 'relevance_score' in tickers_df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.histogram(
                        tickers_df,
                        x='relevance_score',
                        nbins=30,
                        title="Distribution of Relevance Scores",
                        color_discrete_sequence=['#1f77b4']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    relevance_by_ticker = tickers_df.dropna(subset=['ticker']).groupby('ticker')['relevance_score'].mean().sort_values(ascending=False).head(10)
                    fig = px.bar(
                        x=relevance_by_ticker.index,
                        y=relevance_by_ticker.values,
                        title="Average Relevance Score by Ticker (Top 10)",
                        color=relevance_by_ticker.values,
                        color_continuous_scale='plasma'
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("🏷️ Topics Analysis")
        
        if 'topic' in topics_df.columns:
            # Topic distribution
            col1, col2 = st.columns(2)
            
            with col1:
                topic_counts = topics_df['topic'].dropna().value_counts()
                fig = px.pie(
                    values=topic_counts.values,
                    names=topic_counts.index,
                    title="Topic Distribution",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    x=topic_counts.index,
                    y=topic_counts.values,
                    title="Topic Frequency",
                    color=topic_counts.values,
                    color_continuous_scale='viridis'
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Sentiment by topic
            if 'overall_sentiment_score' in topics_df.columns:
                topic_sentiment = topics_df.dropna(subset=['topic']).groupby('topic')['overall_sentiment_score'].agg(['mean', 'count']).reset_index()
                topic_sentiment = topic_sentiment[topic_sentiment['count'] >= 3]  # Filter topics with at least 3 articles
                
                fig = px.scatter(
                    topic_sentiment,
                    x='mean',
                    y='count',
                    size='count',
                    color='mean',
                    hover_name='topic',
                    title="Topic Sentiment vs Frequency",
                    color_continuous_scale='RdYlGn',
                    size_max=50
                )
                fig.update_xaxes(title_text="Average Sentiment Score")
                fig.update_yaxes(title_text="Number of Articles")
                st.plotly_chart(fig, use_container_width=True)
            
            # Topics over time
            if 'time_published' in topics_df.columns:
                topics_df['date'] = topics_df['time_published'].dt.date
                topic_timeline = topics_df.dropna(subset=['topic']).groupby(['date', 'topic']).size().reset_index(name='count')
                
                fig = px.line(
                    topic_timeline,
                    x='date',
                    y='count',
                    color='topic',
                    title="Topic Trends Over Time",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.header("📰 News Feed")
        
        # Display recent articles
        if 'title' in tickers_df.columns:
            st.subheader("Recent Articles")
            
            # Sort by time published
            if 'time_published' in tickers_df.columns:
                recent_articles = tickers_df.sort_values('time_published', ascending=False).head(20)
            else:
                recent_articles = tickers_df.head(20)
            
            for idx, row in recent_articles.iterrows():
                with st.expander(f"📰 {row['title']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Summary:** {row.get('summary', 'N/A')}")
                        st.write(f"**Source:** {row.get('source', 'N/A')}")
                        if 'time_published' in row and pd.notna(row['time_published']):
                            st.write(f"**Published:** {row['time_published'].strftime('%Y-%m-%d %H:%M')}")
                        if 'authors' in row:
                            st.write(f"**Authors:** {row['authors']}")
                    
                    with col2:
                        if 'overall_sentiment_score' in row:
                            sentiment_color = "🟢" if row['overall_sentiment_score'] > 0 else "🔴" if row['overall_sentiment_score'] < 0 else "🟡"
                            st.write(f"{sentiment_color} **Sentiment:** {row['overall_sentiment_score']:.3f}")
                        
                        if 'ticker' in row:
                            st.write(f"**Ticker:** {row['ticker']}")
                        
                        if 'relevance_score' in row:
                            st.write(f"**Relevance:** {row['relevance_score']:.3f}")
                    
                    if 'url' in row and pd.notna(row['url']):
                        st.write(f"[Read Full Article]({row['url']})")

if __name__ == "__main__":
    main()
