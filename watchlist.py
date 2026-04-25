# watchlist.py — Dynamic stock watchlist from Nifty 50 + S&P 500
import pandas as pd

def get_nifty50_tickers():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/NIFTY_50")
        for table in tables:
            for col in table.columns:
                if 'symbol' in col.lower():
                    tickers = table[col].tolist()
                    clean = []
                    for t in tickers:
                        t = str(t).strip().replace(' ', '')
                        if t and t != 'nan':
                            clean.append(t + ".NS")
                    if len(clean) >= 40:
                        return clean[:50]
    except Exception as e:
        print(f"Error fetching Nifty 50: {e}")
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS",
        "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
        "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS", "BAJFINANCE.NS", "NESTLEIND.NS",
        "HCLTECH.NS", "TECHM.NS", "POWERGRID.NS", "NTPC.NS", "ONGC.NS",
        "JSWSTEEL.NS", "TATAMOTORS.NS", "ADANIENT.NS", "COALINDIA.NS", "DIVISLAB.NS",
        "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS",
        "HINDALCO.NS", "INDUSINDBK.NS", "CIPLA.NS", "BAJAJ-AUTO.NS", "BPCL.NS",
        "BRITANNIA.NS", "APOLLOHOSP.NS", "SBILIFE.NS", "TATACONSUM.NS", "TATASTEEL.NS",
        "ADANIPORTS.NS", "BAJAJFINSV.NS", "LTIM.NS", "M&M.NS", "COALINDIA.NS"
    ]

def get_sp500_tickers():
    try:
        table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        tickers = table[0]['Symbol'].tolist()
        clean = [str(t).replace('.', '-') for t in tickers if t and str(t) != 'nan']
        return clean[:50]
    except Exception as e:
        print(f"Error fetching S&P 500: {e}")
    return [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "JPM", "V",
        "JNJ", "UNH", "PG", "MA", "HD", "XOM", "CVX", "MRK", "ABBV", "PEP",
        "KO", "COST", "WMT", "LLY", "AVGO", "TMO", "ACN", "DHR", "NEE", "TXN",
        "AMD", "QCOM", "HON", "UPS", "SBUX", "GE", "CAT", "BA", "MMM", "GS",
        "BAC", "WFC", "C", "AXP", "BLK", "SPGI", "CME", "ICE", "PFE", "MCD"
    ]

def get_all_tickers():
    print("Fetching Nifty 50 tickers...")
    nifty = get_nifty50_tickers()
    print(f"  Got {len(nifty)} Indian stocks")
    print("Fetching S&P 500 tickers (top 50)...")
    sp500 = get_sp500_tickers()
    print(f"  Got {len(sp500)} US stocks")
    tickers = []
    for t in sp500:
        tickers.append({"ticker": t, "market": "US"})
    for t in nifty:
        tickers.append({"ticker": t, "market": "IN"})
    return tickers

SECTOR_MAP = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMD", "QCOM", "AVGO", "TXN", "ACN",
                   "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTIM.NS"],
    "Finance": ["JPM", "BAC", "WFC", "GS", "V", "MA", "AXP", "BLK", "C",
                "HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "AXISBANK.NS", "BAJFINANCE.NS"],
    "FMCG": ["PG", "KO", "PEP", "COST", "WMT", "MCD", "SBUX",
             "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
    "Energy": ["XOM", "CVX", "NEE",
               "RELIANCE.NS", "ONGC.NS", "BPCL.NS", "NTPC.NS", "POWERGRID.NS"],
    "Healthcare": ["JNJ", "UNH", "MRK", "ABBV", "TMO", "PFE", "LLY",
                   "SUNPHARMA.NS", "DRREDDY.NS", "DIVISLAB.NS", "CIPLA.NS", "APOLLOHOSP.NS"]
}

def get_sector(ticker):
    for sector, tickers in SECTOR_MAP.items():
        if ticker in tickers:
            return sector
    return "Other"
