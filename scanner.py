# scanner.py — Monthly scan + cache results
import json
import os
from datetime import datetime
from week1_data import get_stock_data, add_indicators, get_signal
from week2_ai import get_news_sentiment, client
from watchlist import get_all_tickers
import pandas as pd

CACHE_FILE = "cache/recommendations.json"

def score_stock(ticker_info):
    ticker = ticker_info['ticker']
    try:
        df = get_stock_data(ticker, period="6mo")
        df = add_indicators(df)
        signal, score = get_signal(df)
        latest = df.iloc[-1]

        close = float(latest['Close'])
        rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50
        sma50 = float(latest['SMA_50']) if not pd.isna(latest['SMA_50']) else close
        sma200 = float(latest['SMA_200']) if not pd.isna(latest['SMA_200']) else close
        macd = float(latest['MACD']) if not pd.isna(latest['MACD']) else 0
        macd_sig = float(latest['MACD_signal']) if not pd.isna(latest['MACD_signal']) else 0

        tech_score = score
        if close > sma200: tech_score += 2
        if close > sma50: tech_score += 1
        if 40 <= rsi <= 60: tech_score += 1

        return {
            "ticker": ticker,
            "sector": ticker_info['sector'],
            "market": ticker_info['market'],
            "price": round(close, 2),
            "rsi": round(rsi, 1),
            "signal": signal,
            "tech_score": tech_score,
            "above_sma200": close > sma200,
            "macd_bullish": macd > macd_sig
        }
    except Exception as e:
        print(f"  Error: {ticker} — {e}")
        return None

def get_ai_recommendations(top_stocks):
    prompt = f"""You are a financial advisor for medium-term investments (1-6 months).

Analyze these technically strong stocks and give final buy recommendations.

STOCKS:
{json.dumps(top_stocks, indent=2)}

Return JSON with:
- recommendations: list of objects each with:
  - ticker: string
  - sector: string
  - rank: number
  - action: BUY or STRONG BUY
  - reasoning: 2 sentence explanation
  - target_horizon: e.g. 2-3 months
  - risk: LOW / MEDIUM / HIGH
- summary: 2 sentence overall market comment

Return ONLY valid JSON."""

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content)

def run_monthly_scan():
    print("="*50)
    print("MONTHLY STOCK SCAN")
    print("="*50)

    all_tickers = get_all_tickers()
    print(f"Scanning {len(all_tickers)} stocks...")

    scores = []
    for t in all_tickers:
        print(f"  {t['ticker']}...")
        result = score_stock(t)
        if result:
            scores.append(result)

    # Sort by tech score
    scores.sort(key=lambda x: x['tech_score'], reverse=True)

    # Get news for top 10 only — saves API cost
    print("\nGetting news for top 10 stocks...")
    top10 = scores[:10]
    for stock in top10:
        sentiment = get_news_sentiment(stock['ticker'])
        stock['sentiment'] = sentiment.get('sentiment', 'NEUTRAL')
        stock['news_summary'] = sentiment.get('summary', '')

    # Add neutral sentiment for rest
    for stock in scores[10:]:
        stock['sentiment'] = 'NEUTRAL'
        stock['news_summary'] = ''

    # AI recommendations for top 10
    print("\nGenerating AI recommendations...")
    ai_result = get_ai_recommendations(top10)

    # Build cache
    cache = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_scanned": len(scores),
        "all_scores": scores,
        "recommendations": ai_result.get("recommendations", []),
        "market_summary": ai_result.get("summary", "")
    }

    os.makedirs("cache", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\nDone! Results saved to {CACHE_FILE}")
    print(f"Top 5 picks:")
    for r in cache['recommendations'][:5]:
        print(f"  #{r['rank']} {r['ticker']} — {r['action']}")

    return cache

if __name__ == "__main__":
    run_monthly_scan()