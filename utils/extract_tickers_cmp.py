from bs4 import BeautifulSoup
import requests

# EITHER load from web:
# html = requests.get("https://companiesmarketcap.com/", headers={"User-Agent":"Mozilla/5.0"}).text
# OR from a saved file/snippet:
html = open("snippet.html", encoding="utf-8").read()

soup = BeautifulSoup(html, "lxml")
tickers = []

for tr in soup.select("table.marketcap-table tbody tr"):
    country_td = tr.find_all("td")[-1]
    is_usa = (country_td.find("img", src=lambda s: s and "/us.png" in s) is not None) \
             or ("USA" in country_td.get_text())
    if not is_usa:
        continue
    code = tr.select_one(".company-code")
    if not code:
        continue
    # get only the text nodes (skip the hidden <span>)
    ticker = "".join(code.find_all(string=True, recursive=False)).strip()
    if ticker:
        tickers.append(ticker)

print(tickers)           # ['NVDA', 'MSFT', ...]
# Optional: write to CSV
# import csv
# with open("usa_tickers.csv","w",newline="",encoding="utf-8") as f:
#     w=csv.writer(f); w.writerow(["ticker"]); w.writerows([[t] for t in tickers])
