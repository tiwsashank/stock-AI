# bucket.py — Weekly SIP bucket tracker
import json
import os
from datetime import datetime
from week1_data import get_stock_data

BUCKET_FILE = "cache/buckets.json"

def load_buckets():
    if os.path.exists(BUCKET_FILE):
        with open(BUCKET_FILE) as f:
            return json.load(f)
    return {
        "US": {"weekly_amount": 100, "currency": "USD", "investments": []},
        "IN": {"weekly_amount": 100, "currency": "INR", "investments": []}
    }

def save_buckets(buckets):
    os.makedirs("cache", exist_ok=True)
    with open(BUCKET_FILE, "w") as f:
        json.dump(buckets, f, indent=2)

def add_weekly_investment(market, amount, tickers, prices, date=None):
    """
    Add a weekly investment entry.
    Splits amount equally across tickers.
    """
    buckets = load_buckets()
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    per_stock = amount / len(tickers)
    holdings = []
    for ticker, price in zip(tickers, prices):
        shares = per_stock / price
        holdings.append({
            "ticker": ticker,
            "price_at_buy": round(price, 2),
            "shares": round(shares, 6),
            "amount_invested": round(per_stock, 2)
        })

    entry = {
        "date": date,
        "total_invested": amount,
        "holdings": holdings
    }

    buckets[market]["investments"].append(entry)
    save_buckets(buckets)
    return entry

def get_bucket_performance(market):
    """Calculate current value vs invested for a bucket."""
    buckets = load_buckets()
    bucket = buckets.get(market, {})
    investments = bucket.get("investments", [])

    if not investments:
        return {
            "total_invested": 0,
            "current_value": 0,
            "pnl": 0,
            "pnl_pct": 0,
            "holdings_summary": []
        }

    # Aggregate shares per ticker
    ticker_shares = {}
    ticker_invested = {}
    for inv in investments:
        for h in inv["holdings"]:
            t = h["ticker"]
            ticker_shares[t] = ticker_shares.get(t, 0) + h["shares"]
            ticker_invested[t] = ticker_invested.get(t, 0) + h["amount_invested"]

    # Get current prices
    total_invested = sum(ticker_invested.values())
    current_value = 0
    holdings_summary = []

    for ticker, shares in ticker_shares.items():
        try:
            df = get_stock_data(ticker, period="5d")
            current_price = float(df['Close'].iloc[-1])
            value = shares * current_price
            invested = ticker_invested[ticker]
            pnl = value - invested
            pnl_pct = (pnl / invested) * 100

            holdings_summary.append({
                "ticker": ticker,
                "shares": round(shares, 4),
                "avg_buy_price": round(invested / shares, 2),
                "current_price": round(current_price, 2),
                "invested": round(invested, 2),
                "current_value": round(value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2)
            })
            current_value += value
        except Exception as e:
            print(f"Error getting price for {ticker}: {e}")

    total_pnl = current_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    return {
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "pnl": round(total_pnl, 2),
        "pnl_pct": round(total_pnl_pct, 2),
        "holdings_summary": sorted(holdings_summary, key=lambda x: x['pnl_pct'], reverse=True),
        "num_investments": len(investments),
        "currency": bucket.get("currency", "USD")
    }

def get_top_tickers_from_cache(market, n=5):
    """Get top N recommended tickers for a market from cache."""
    CACHE_FILE = "cache/recommendations.json"
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE) as f:
        cache = json.load(f)
    scores = cache.get("all_scores", [])
    filtered = [s for s in scores if s.get("market") == market]
    return [s["ticker"] for s in filtered[:n]]

if __name__ == "__main__":
    # Test
    tickers_us = get_top_tickers_from_cache("US", 5)
    print(f"Top US tickers: {tickers_us}")
    tickers_in = get_top_tickers_from_cache("IN", 5)
    print(f"Top IN tickers: {tickers_in}")
