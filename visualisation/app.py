import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import calendar
from datetime import date as Date
import plotly.express as px   # <-- aggiungi questo import


st.set_page_config(page_title="Calendar – Weighted Sentiment", page_icon="📅", layout="wide")

@st.cache_data
def load_csvs():
    t = pd.read_csv('/app/data/processed/tickers.csv')
    p = pd.read_csv('/app/data/processed/topics.csv')
    for df in (t, p):
        if 'time_published' in df.columns:
            df['time_published'] = pd.to_datetime(df['time_published'], format='%Y%m%dT%H%M%S', errors='coerce')
    return t, p

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

def render_calendar_for(df, label_col, label_value):
    sub = df[df[label_col].astype(str) == str(label_value)]
    if sub.empty:
        st.info("Nessun dato per la selezione.")
        return

    # mesi disponibili
    months = sub['time_published'].dt.to_period('M').dropna().sort_values().unique()
    sel = st.selectbox("Mese", options=list(months), index=len(months)-1,
                       format_func=lambda p: p.strftime("%B %Y"))
    y, m = int(sel.start_time.year), int(sel.start_time.month)

    # subset mese
    mstart = pd.Timestamp(y, m, 1)
    mend   = pd.Timestamp(y, m, calendar.monthrange(y, m)[1], 23, 59, 59)
    month_df = sub[(sub['time_published'] >= mstart) & (sub['time_published'] <= mend)]

    # sentiment giornaliero (pesato)
    daily = daily_weighted_sentiment(month_df)  # index=python date
    Z, TEXT = build_calendar_matrix(daily.to_dict(), y, m)

    # heatmap stile calendario
    fig = go.Figure(data=go.Heatmap(
        z=Z, text=TEXT, texttemplate="%{text}", textfont={"size":12},
        colorscale='RdYlGn', zmin=-1, zmax=1, hoverinfo="skip", showscale=True
    ))
    fig.update_layout(
        title=f"Sentiment ponderato giornaliero – {label_col.capitalize()} {label_value} – {sel.strftime('%B %Y')}",
        xaxis=dict(title="Giorno", tickmode='array', ticktext=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], tickvals=list(range(7))),
        yaxis=dict(title="Settimana", tickmode='array', ticktext=[f"W{i+1}" for i in range(len(Z))], tickvals=list(range(len(Z)))),
        margin=dict(t=60, l=10, r=10, b=10), height=420
    )
    st.plotly_chart(fig, use_container_width=True)
    # --- LINE CHART (mese selezionato) ---
    # serie giornaliera pesata per il mese corrente
    line = daily.reset_index()
    line.columns = ['date', 'sentiment_w']

    # numero articoli per giorno (per hover)
    counts = month_df.groupby(month_df['time_published'].dt.date).size()
    line['n_articles'] = line['date'].map(counts).fillna(0).astype(int)

    fig_line = px.line(
        line, x='date', y='sentiment_w', markers=True,
        title=f"Andamento giornaliero (pesato) – {label_col.capitalize()} {label_value} – {sel.strftime('%B %Y')}",
        hover_data={'n_articles': True, 'date': '|%Y-%m-%d'}
    )
    fig_line.update_yaxes(title="Sentiment (w)", range=[-1, 1])
    fig_line.update_xaxes(title="Data")
    fig_line.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig_line, use_container_width=True)

    # KPI rapidi
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

    tickers_df, topics_df = load_csvs()
    dataset = st.sidebar.radio("Dataset", ["Tickers", "Topics"])
    df = tickers_df.copy() if dataset == "Tickers" else topics_df.copy()
    label_col = "ticker" if dataset == "Tickers" else "topic"
    need = {'time_published','overall_sentiment_score'}
    if not need.issubset(df.columns):
        st.error(f"Mancano colonne richieste: {need - set(df.columns)}"); return

    # filtri
    st.sidebar.header("Filtri")
    min_d, max_d = df['time_published'].min().date(), df['time_published'].max().date()
    date_range = st.sidebar.date_input("Intervallo date", (min_d, max_d), min_value=min_d, max_value=max_d)
    opts = sorted(df[label_col].dropna().astype(str).unique())
    chosen_filter = st.sidebar.multiselect(f"Filtra {label_col}", opts)
    fdf = apply_filters(df, date_range, label_col, chosen_filter)

    if fdf.empty:
        st.info("Nessun dato dopo i filtri."); return

    # scegli l'elemento da visualizzare
    values = sorted(fdf[label_col].dropna().astype(str).unique())
    chosen = st.selectbox(f"Seleziona {label_col.capitalize()} per il calendario", values)
    render_calendar_for(fdf, label_col, chosen)

if __name__ == "__main__":
    main()
