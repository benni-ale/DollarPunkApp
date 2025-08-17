import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import calendar
from datetime import date as Date
import plotly.express as px
from plotly.subplots import make_subplots


st.set_page_config(page_title="Calendar – Weighted Sentiment", page_icon="📅", layout="wide")

@st.cache_data
def load_csvs():
    t = pd.read_csv('/app/data/processed/tickers.csv')
    p = pd.read_csv('/app/data/processed/topics.csv')
    # Load stock data
    try:
        stocks_df = pd.read_csv('/app/data/stocks/stocks_data.csv')
        stocks_df['date'] = pd.to_datetime(stocks_df['date'])
    except FileNotFoundError:
        stocks_df = pd.DataFrame()
    
    for df in (t, p):
        if 'time_published' in df.columns:
            df['time_published'] = pd.to_datetime(df['time_published'], format='%Y%m%dT%H%M%S', errors='coerce')
    return t, p, stocks_df

def apply_filters(df, date_range, label_col, selected_vals):
    df = df[df['time_published'].notna()]
    if date_range:
        start = pd.to_datetime(date_range[0])
        end   = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df['time_published'] >= start) & (df['time_published'] <= end)]
    if selected_vals:
        df = df[df[label_col].astype(str).isin([str(v) for v in selected_vals])]
    return df

def daily_weighted_sentiment(df):
    """Series: date -> weighted mean; fallback alla media semplice se pesi assenti/zero."""
    if df.empty: return pd.Series(dtype=float)
    g = df.groupby(df['time_published'].dt.date)
    def wavg(s):
        x = s['overall_sentiment_score'].astype(float)
        w = s['relevance_score'].fillna(0) if 'relevance_score' in s else None
        if (w is None) or (w.sum() == 0):
            return x.mean()
        return np.average(x, weights=w)
    return g.apply(wavg)

def build_calendar_matrix(values_by_date, year, month):
    """Ritorna (Z, TEXT) per Heatmap calendario (lun→dom)."""
    weeks = calendar.monthcalendar(year, month)  # 0 = fuori mese
    Z, TEXT = [], []
    for w_idx, week in enumerate(weeks):
        zrow, trow = [], []
        for d_idx, d in enumerate(week):
            if d == 0:
                zrow.append(np.nan); trow.append("")
            else:
                val = float(values_by_date.get(Date(year, month, d), np.nan))
                zrow.append(val)
                trow.append(f"{d}\n{'' if np.isnan(val) else f'{val:.2f}'}")
        Z.append(zrow); TEXT.append(trow)
    return np.array(Z, dtype=float), TEXT

def render_sentiment_calendar(df, label_col, label_value, date_range, sel):
    """Rende il calendario sentiment."""
    y, m = int(sel.start_time.year), int(sel.start_time.month)
    
    # subset mese per il calendario
    mstart = pd.Timestamp(y, m, 1)
    mend   = pd.Timestamp(y, m, calendar.monthrange(y, m)[1], 23, 59, 59)
    month_df = df[(df['time_published'] >= mstart) & (df['time_published'] <= mend)]

    # sentiment giornaliero (pesato)
    daily = daily_weighted_sentiment(month_df)  # index=python date
    Z, TEXT = build_calendar_matrix(daily.to_dict(), y, m)

    # heatmap stile calendario
    fig = go.Figure(data=go.Heatmap(
        z=Z, text=TEXT, texttemplate="%{text}", textfont={"size":12},
        colorscale='RdYlGn', zmin=-1, zmax=1, hoverinfo="skip", showscale=True
    ))
    fig.update_layout(
        title=f"📅 Sentiment ponderato giornaliero – {label_col.capitalize()} {label_value} – {sel.strftime('%B %Y')}",
        xaxis=dict(title="Giorno", tickmode='array', ticktext=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], tickvals=list(range(7))),
        yaxis=dict(title="Settimana", tickmode='array', ticktext=[f"W{i+1}" for i in range(len(Z))], tickvals=list(range(len(Z)))),
        margin=dict(t=60, l=10, r=10, b=10), height=420
    )
    st.plotly_chart(fig, use_container_width=True)
    
    return daily, Z

def render_sentiment_timeline(df, label_col, label_value, date_range):
    """Rende il grafico timeline sentiment per l'intero intervallo date."""
    # Applica filtro date range
    if date_range:
        start = pd.to_datetime(date_range[0])
        end = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_filtered = df[(df['time_published'] >= start) & (df['time_published'] <= end)]
    else:
        df_filtered = df
    
    # sentiment giornaliero (pesato) per tutto l'intervallo
    daily = daily_weighted_sentiment(df_filtered)
    
    if daily.empty:
        st.info("Nessun dato sentiment nell'intervallo selezionato.")
        return daily
    
    line = daily.reset_index()
    line.columns = ['date', 'sentiment_w']
    
    # Formatta il titolo con l'intervallo date
    if date_range:
        start_str = date_range[0].strftime('%d/%m/%Y')
        end_str = date_range[1].strftime('%d/%m/%Y')
        title = f"📈 Andamento sentiment giornaliero – {label_col.capitalize()} {label_value} – {start_str} → {end_str}"
    else:
        title = f"📈 Andamento sentiment giornaliero – {label_col.capitalize()} {label_value}"
    
    fig_line = px.line(
        line, x='date', y='sentiment_w',
        title=title,
        hover_data={'date': '|%Y-%m-%d'}
    )
    fig_line.update_yaxes(title="Sentiment (w)", range=[-1, 1])
    fig_line.update_xaxes(title="Data")
    fig_line.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_line, use_container_width=True)
    
    return daily

def render_stock_price_chart(stocks_df, label_value, date_range):
    """Rende il grafico prezzi azioni per l'intero intervallo date."""
    # Applica filtro date range
    if date_range:
        start = pd.to_datetime(date_range[0])
        end = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        stock_subset = stocks_df[
            (stocks_df['ticker'] == label_value) & 
            (stocks_df['date'] >= start) & 
            (stocks_df['date'] <= end)
        ].copy()
    else:
        stock_subset = stocks_df[stocks_df['ticker'] == label_value].copy()
    
    if stock_subset.empty:
        st.info(f"📊 Nessun dato stock disponibile per {label_value} nell'intervallo selezionato.")
        return None
    
    # Formatta il titolo con l'intervallo date
    if date_range:
        start_str = date_range[0].strftime('%d/%m/%Y')
        end_str = date_range[1].strftime('%d/%m/%Y')
        title = f"💰 Prezzi di chiusura – {label_value} – {start_str} → {end_str}"
    else:
        title = f"💰 Prezzi di chiusura – {label_value}"
    
    # Grafico prezzi
    fig_stock = px.line(
        stock_subset, x='date', y='close',
        title=title,
        hover_data={'date': '|%Y-%m-%d', 'close': ':.2f'}
    )
    fig_stock.update_yaxes(title="Prezzo di chiusura ($)")
    fig_stock.update_xaxes(title="Data")
    st.plotly_chart(fig_stock, use_container_width=True)
    
    # Stock price KPI
    st.subheader("📈 Metriche Stock Price")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Prezzo iniziale", f"${stock_subset['close'].iloc[0]:.2f}")
    with col2:
        st.metric("Prezzo finale", f"${stock_subset['close'].iloc[-1]:.2f}")
    with col3:
        change = stock_subset['close'].iloc[-1] - stock_subset['close'].iloc[0]
        change_pct = (change / stock_subset['close'].iloc[0]) * 100
        st.metric("Variazione", f"${change:.2f}", f"{change_pct:+.2f}%")
    with col4:
        st.metric("Prezzo massimo", f"${stock_subset['close'].max():.2f}")
    
    return stock_subset

def render_calendar_for(df, label_col, label_value, stocks_df=None, date_range=None):
    sub = df[df[label_col].astype(str) == str(label_value)]
    if sub.empty:
        st.info("Nessun dato per la selezione.")
        return

    # mesi disponibili per il calendario
    months = sub['time_published'].dt.to_period('M').dropna().sort_values().unique()
    sel = st.selectbox("Mese per calendario", options=list(months), index=len(months)-1,
                       format_func=lambda p: p.strftime("%B %Y"))

    # 1. CALENDARIO SENTIMENT (usa il mese selezionato)
    st.header("📅 Calendario Sentiment")
    daily_cal, Z = render_sentiment_calendar(sub, label_col, label_value, date_range, sel)
    
    # 2. TIMELINE SENTIMENT (usa l'intero intervallo date)
    st.header("📈 Timeline Sentiment")
    daily_timeline = render_sentiment_timeline(sub, label_col, label_value, date_range)
    
    # 3. GRAFICO PREZZI AZIONI (usa l'intero intervallo date)
    if label_col == "ticker" and not stocks_df.empty:
        st.header("💰 Prezzi Azioni")
        stock_data = render_stock_price_chart(stocks_df, label_value, date_range)
    
    # KPI rapidi sentiment (dal calendario)
    st.header("📊 Metriche Sentiment")
    flat = Z[~np.isnan(Z)]
    c1, c2, c3 = st.columns(3)
    c1.metric("Media mese (pesata)", f"{np.nanmean(flat):.3f}" if flat.size else "NA")
    c2.metric("Giorni positivi", int(np.nansum(flat > 0)))
    c3.metric("Giorni negativi", int(np.nansum(flat < 0)))

    # Formula (LaTeX)
    st.markdown("**Formula utilizzata (giorno d, ticker/topic t):**")
    st.latex(r"""
    S_{t,d} =
    \begin{cases}
      \dfrac{\sum_{i \in \mathcal{A}_{t,d}} s_i \, r_i}{\sum_{i \in \mathcal{A}_{t,d}} r_i}, & \text{se } \sum r_i > 0 \\
      \dfrac{1}{|\mathcal{A}_{t,d}|} \sum_{i \in \mathcal{A}_{t,d}} s_i, & \text{altrimenti (fallback media semplice)}
    \end{cases}
    """)
    st.caption("dove \(s_i=\) overall_sentiment_score e \(r_i=\) relevance_score.")

def main():
    st.title("📅 Calendar – Weighted Sentiment")

    tickers_df, topics_df, stocks_df = load_csvs()
    dataset = st.sidebar.radio("Dataset", ["Tickers", "Topics"])
    df = tickers_df.copy() if dataset == "Tickers" else topics_df.copy()
    label_col = "ticker" if dataset == "Tickers" else "topic"
    need = {'time_published','overall_sentiment_score'}
    if not need.issubset(df.columns):
        st.error(f"Mancano colonne richieste: {need - set(df.columns)}"); return

    # filtri nella sidebar
    st.sidebar.header("Filtri")
    min_d, max_d = df['time_published'].min().date(), df['time_published'].max().date()
    date_range = st.sidebar.date_input("Intervallo date", (min_d, max_d), min_value=min_d, max_value=max_d)
    
    # Selezione ticker/topic nella sidebar con barra di ricerca
    opts = sorted(df[label_col].dropna().astype(str).unique())
    
    # Barra di ricerca per filtrare le opzioni
    search_term = st.sidebar.text_input(f"🔍 Cerca {label_col.capitalize()}", placeholder=f"Digita per cercare {label_col}...")
    
    # Filtra le opzioni basandosi sulla ricerca
    if search_term:
        filtered_opts = [opt for opt in opts if search_term.upper() in opt.upper()]
        if not filtered_opts:
            st.sidebar.warning(f"Nessun {label_col} trovato per '{search_term}'")
            filtered_opts = opts
    else:
        filtered_opts = opts
    
    # Selectbox con le opzioni filtrate
    chosen = st.sidebar.selectbox(
        f"Seleziona {label_col.capitalize()}", 
        filtered_opts,
        help=f"Usa la barra di ricerca sopra per filtrare i {label_col}"
    )
    
    # Applica filtri
    fdf = apply_filters(df, date_range, label_col, [chosen])

    if fdf.empty:
        st.info("Nessun dato dopo i filtri."); return

    # Mostra il ticker/topic selezionato
    st.sidebar.success(f"📊 Analizzando: **{chosen}**")
    
    # Renderizza i grafici
    render_calendar_for(fdf, label_col, chosen, stocks_df, date_range)

if __name__ == "__main__":
    main()
