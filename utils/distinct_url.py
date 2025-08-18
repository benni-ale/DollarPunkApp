import pandas as pd
from urllib.parse import urlparse

df = pd.read_csv("../output/processed/tickers.csv")
sources = sorted({f"{p.scheme}://{p.netloc}/" for p in map(urlparse, df["url"].dropna())})
print("\n".join(sources))
# opzionale: salva
pd.Series(sources).to_csv("unique_sources.txt", index=False, header=False)
