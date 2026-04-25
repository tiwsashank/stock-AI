# week2_ai.py — AI insights + news sentiment
import os
import json
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def get_news_sentiment(ticker):
    try:
        results = tavily.search(f"{ticker} stock news today", max_results=5)
        headlines = [r['content'][:200] for r in results['results']]

        prompt = f"""You are a financial analyst. Analyze these news headlines for {ticker} and return JSON:
- sentiment: BULLISH / NEUTRAL / BEARISH
- confidence: HIGH / MEDIUM / LOW
- key_themes: list of 2-3 main themes
- summary: one sentence summary

Headlines:
{json.dumps(headlines, indent=2)}

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
    except Exception as e:
        return {"sentiment": "NEUTRAL", "confidence": "LOW", "key_themes": [], "summary": str(e)}

def get_ai_briefing(portfolio_summary):
    prompt = f"""You are a personal financial advisor. Analyze this portfolio and give a morning briefing.

PORTFOLIO:
{json.dumps(portfolio_summary, indent=2)}

Return JSON with:
- overall_health: STRONG / NEUTRAL / WEAK
- summary: 2-3 sentence portfolio overview
- top_opportunity: ticker + reason
- top_risk: ticker + reason
- action: one specific thing to watch today

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

if __name__ == "__main__":
    from week1_data import get_portfolio_summary

    holdings = [
        {"ticker": "AAPL", "shares": 10, "avg_cost": 150.00, "market": "US"},
        {"ticker": "RELIANCE.NS", "shares": 5, "avg_cost": 2400.00, "market": "IN"},
        {"ticker": "SPY", "shares": 3, "avg_cost": 420.00, "market": "US"}
    ]

    print("Fetching portfolio...")
    portfolio = get_portfolio_summary(holdings)

    print("\nGetting AI briefing...")
    briefing = get_ai_briefing(portfolio)
    print(json.dumps(briefing, indent=2))

    print("\nGetting news sentiment for AAPL...")
    sentiment = get_news_sentiment("AAPL")
    print(json.dumps(sentiment, indent=2))