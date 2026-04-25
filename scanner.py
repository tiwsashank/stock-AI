# scanner.py — Monthly scan + cache results (with fundamentals)
import json
import os
from datetime import datetime
from week1_data import get_stock_data, add_indicators, get_signal, get_fundamentals, get_combined_score
from week2_ai import get_news_sentiment, client
from watchlist import get_all_tickers, get_sector
import pandas as pd

CACHE_FILE = "cache/recommendations.json"

def score_stock(ticker_info):
    ticker = ticker_info['ticker']
    try:
        df = get_stock_data(ticker, period="6mo")
        df = add_indicators(df)
        signal, tech_score = get_signal(df)
        latest = df.iloc[-1]

        close = float(latest['Close'])
        rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50
        sma50 = float(latest['SMA_50']) if not pd.isna(latest['SMA_50']) else close
        sma200 = float(latest['SMA_200']) if not pd.isna(latest['SMA_200']) else close
        macd = float(latest['MACD']) if not pd.isna(latest['MACD']) else 0
        macd_sig = float(latest['MACD_signal']) if not pd.isna(latest['MACD_signal']) else 0

        if close > sma200: tech_score += 2
        if close > sma50: tech_score += 1
        if 40 <= rsi <= 60: tech_score += 1

        print(f"    Fetching fundamentals...")
        fund = get_fundamentals(ticker)
        fund_score = fund.get('fund_score', 0)
        combined = get_combined_score(tech_score, fund_score, "NEUTRAL")

        return {
            "ticker": ticker,
            "sector": get_sector(ticker),
            "market": ticker_info['market'],
            "price": round(close, 2),
            "rsi": round(rsi, 1),
            "signal": signal,
            "tech_score": tech_score,
            "fund_score": fund_score,
            "combined_score": combined,
            "above_sma200": close > sma200,
            "macd_bullish": macd > macd_sig,
            "pe_ratio": fund.get('pe_ratio'),
            "revenue_growth": fund.get('revenue_growth'),
            "profit_margin": fund.get('profit_margin'),
            "analyst_rating": fund.get('analyst_rating', 'N/A'),
            "upside_pct": fund.get('upside_pct'),
            "debt_to_equity": fund.get('debt_to_equity'),
            "week_52_position_pct": fund.get('week_52_position_pct'),
            "dividend_yield": fund.get('dividend_yield'),
            "industry": fund.get('industry', 'N/A'),
        }
    except Exception as e:
        print(f"  Error: {ticker} - {e}")
        return None

def get_ai_recommendations(top_stocks):
    prompt = f"""You are a professional financial advisor specializing in medium-term investments (1-6 months).

Analyze these stocks combining technical momentum AND fundamental strength.

STOCKS:
{json.dumps(top_stocks, indent=2)}

Return JSON with:
- recommendations: list of up to 5 objects each with:
  - ticker: string
  - sector: string
  - rank: number
  - action: BUY or STRONG BUY
  - reasoning: 3 sentence explanation covering both technical AND fundamental factors
  - target_horizon: e.g. 2-4 months
  - risk: LOW / MEDIUM / HIGH
  - key_strength: one short phrase
  - key_risk: one short phrase
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
    print("=" * 50)
    print("MONTHLY SCAN — Technical + Fundamental")
    print("=" * 50)

    all_tickers = get_all_tickers()
    print(f"Scanning {len(all_tickers)} stocks...")

    scores = []
    for t in all_tickers:
        print(f"  {t['ticker']}...")
        result = score_stock(t)
        if result:
            scores.append(result)

    scores.sort(key=lambda x: x['combined_score'], reverse=True)

    print("\nGetting news for top 10...")
    top10 = scores[:10]
    for stock in top10:
        sentiment = get_news_sentiment(stock['ticker'])
        stock['sentiment'] = sentiment.get('sentiment', 'NEUTRAL')
        stock['news_summary'] = sentiment.get('summary', '')
        stock['combined_score'] = get_combined_score(
            stock['tech_score'], stock['fund_score'], stock['sentiment']
        )

    top10.sort(key=lambda x: x['combined_score'], reverse=True)

    for stock in scores[10:]:
        stock['sentiment'] = 'NEUTRAL'
        stock['news_summary'] = ''

    print("\nGenerating AI recommendations...")
    ai_result = get_ai_recommendations(top10)

    cache = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_scanned": len(scores),
        "all_scores": scores,
        "recommendations": ai_result.get("recommendations", []),
        "market_summary": ai_result.get("summary", ""),
        "scoring_method": "Technical 40% + Fundamental 40% + Sentiment 20%"
    }

    os.makedirs("cache", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\nDone! Results saved to {CACHE_FILE}")
    for r in cache['recommendations'][:5]:
        print(f"  #{r['rank']} {r['ticker']} — {r['action']} | {r.get('key_strength','')}")

    return cache

if __name__ == "__main__":
    run_monthly_scan()
