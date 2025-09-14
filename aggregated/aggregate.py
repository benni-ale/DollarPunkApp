import numpy as np, pandas as pd

def avgW_no_decay(csv_path_or_buf):
    df = pd.read_csv(csv_path_or_buf)
    df["date"] = pd.to_datetime(df["time_published"], format="%Y%m%dT%H%M%S", errors="coerce").dt.date
    df = df.dropna(subset=["date","ticker","ticker_sentiment_score","relevance_score"])
    df = df.drop_duplicates(subset=["ticker","url","time_published"])  # optional de-dupe

    df["S0"] = df["ticker_sentiment_score"].astype(float)
    df["R0"] = df["relevance_score"].astype(float).clip(lower=0)

    out = (df.groupby(["ticker","date"], as_index=False)
             .apply(lambda g: pd.Series({
                 "AvgW_d": (g["S0"].mul(g["R0"]).sum() / g["R0"].sum()) if g["R0"].sum() > 0 else np.nan
             })))
    return out.sort_values(["ticker","date"])

# Example:
# res = avgW_no_decay("alpha_vantage_news.csv")
# res.query("ticker == 'ACN'")
