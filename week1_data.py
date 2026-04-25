# week1_data.py — Fetch stock data + technical indicators + fundamentals
import yfinance as yf
import ta
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_stock_data(ticker, period="1y"):
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    df.columns = df.columns.get_level_values(0)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    if df.empty:
        raise ValueError(f"Empty dataframe after dropna for {ticker}")
    return df

def get_fundamentals(ticker):
    """Fetch fundamental data from Yahoo Finance — completely free."""
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # Price metrics
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        target_price = info.get('targetMeanPrice')
        upside = None
        if current_price and target_price:
            upside = round(((target_price - current_price) / current_price) * 100, 1)

        # Valuation
        pe_ratio = info.get('trailingPE')
        forward_pe = info.get('forwardPE')
        pb_ratio = info.get('priceToBook')
        ps_ratio = info.get('priceToSalesTrailing12Months')

        # Growth
        revenue_growth = info.get('revenueGrowth')
        earnings_growth = info.get('earningsGrowth')
        earnings_quarterly_growth = info.get('earningsQuarterlyGrowth')

        # Profitability
        profit_margin = info.get('profitMargins')
        operating_margin = info.get('operatingMargins')
        roe = info.get('returnOnEquity')

        # Financial health
        debt_to_equity = info.get('debtToEquity')
        current_ratio = info.get('currentRatio')
        free_cashflow = info.get('freeCashflow')

        # Market data
        market_cap = info.get('marketCap')
        beta = info.get('beta')
        week_52_high = info.get('fiftyTwoWeekHigh')
        week_52_low = info.get('fiftyTwoWeekLow')
        week_52_pct = None
        if current_price and week_52_high and week_52_low:
            range_size = week_52_high - week_52_low
            if range_size > 0:
                week_52_pct = round(((current_price - week_52_low) / range_size) * 100, 1)

        # Analyst consensus
        analyst_rating = info.get('recommendationKey', 'N/A').upper().replace('_', ' ')
        num_analysts = info.get('numberOfAnalystOpinions', 0)

        # Dividend
        dividend_yield = info.get('dividendYield')

        # Sector/Industry
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')

        # Fundamental score (0-10)
        fund_score = 0

        # Upside potential
        if upside and upside > 20: fund_score += 2
        elif upside and upside > 10: fund_score += 1
        elif upside and upside < 0: fund_score -= 1

        # Analyst rating
        if analyst_rating in ['STRONG BUY', 'BUY']: fund_score += 2
        elif analyst_rating == 'HOLD': fund_score += 0
        elif analyst_rating in ['SELL', 'STRONG SELL']: fund_score -= 2

        # Growth
        if revenue_growth and revenue_growth > 0.15: fund_score += 1
        elif revenue_growth and revenue_growth > 0.05: fund_score += 0.5

        if earnings_growth and earnings_growth > 0.15: fund_score += 1
        elif earnings_growth and earnings_growth > 0.05: fund_score += 0.5

        # Profitability
        if profit_margin and profit_margin > 0.15: fund_score += 1
        elif profit_margin and profit_margin < 0: fund_score -= 1

        # Valuation — not too expensive
        if pe_ratio and 0 < pe_ratio < 25: fund_score += 1
        elif pe_ratio and pe_ratio > 50: fund_score -= 1

        # Debt safety
        if debt_to_equity and debt_to_equity < 50: fund_score += 1
        elif debt_to_equity and debt_to_equity > 200: fund_score -= 1

        # 52-week position — buying near lows is better for medium term
        if week_52_pct and week_52_pct < 30: fund_score += 1
        elif week_52_pct and week_52_pct > 90: fund_score -= 0.5

        return {
            "current_price": current_price,
            "target_price": target_price,
            "upside_pct": upside,
            "pe_ratio": round(pe_ratio, 1) if pe_ratio else None,
            "forward_pe": round(forward_pe, 1) if forward_pe else None,
            "pb_ratio": round(pb_ratio, 2) if pb_ratio else None,
            "revenue_growth": round(revenue_growth * 100, 1) if revenue_growth else None,
            "earnings_growth": round(earnings_growth * 100, 1) if earnings_growth else None,
            "profit_margin": round(profit_margin * 100, 1) if profit_margin else None,
            "operating_margin": round(operating_margin * 100, 1) if operating_margin else None,
            "roe": round(roe * 100, 1) if roe else None,
            "debt_to_equity": round(debt_to_equity, 1) if debt_to_equity else None,
            "current_ratio": round(current_ratio, 2) if current_ratio else None,
            "beta": round(beta, 2) if beta else None,
            "week_52_high": week_52_high,
            "week_52_low": week_52_low,
            "week_52_position_pct": week_52_pct,
            "analyst_rating": analyst_rating,
            "num_analysts": num_analysts,
            "dividend_yield": round(dividend_yield * 100, 2) if dividend_yield else None,
            "market_cap": market_cap,
            "sector": sector,
            "industry": industry,
            "fund_score": round(fund_score, 1)
        }
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return {"fund_score": 0, "analyst_rating": "N/A", "error": str(e)}

def add_indicators(df):
    if df.empty or len(df) < 20:
        raise ValueError("Not enough data to compute indicators")

    close = df['Close'].squeeze()
    df = df.copy()

    df['RSI'] = ta.momentum.RSIIndicator(close, window=14).rsi()

    macd = ta.trend.MACD(close)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()

    bb = ta.volatility.BollingerBands(close, window=20)
    df['BB_upper'] = bb.bollinger_hband()
    df['BB_lower'] = bb.bollinger_lband()
    df['BB_mid'] = bb.bollinger_mavg()

    df['SMA_20'] = ta.trend.SMAIndicator(close, window=20).sma_indicator()
    df['SMA_50'] = ta.trend.SMAIndicator(close, window=50).sma_indicator()
    df['SMA_200'] = ta.trend.SMAIndicator(close, window=200).sma_indicator()

    return df

def get_signal(df):
    if df.empty or len(df) == 0:
        return "HOLD", 0

    latest = df.iloc[-1]
    score = 0

    try:
        rsi = float(latest['RSI'])
        if pd.isna(rsi): rsi = 50
        if rsi < 30: score += 2
        elif rsi > 70: score -= 2
    except: pass

    try:
        macd = float(latest['MACD'])
        macd_sig = float(latest['MACD_signal'])
        if not pd.isna(macd) and not pd.isna(macd_sig):
            if macd > macd_sig: score += 2
            else: score -= 2
    except: pass

    try:
        sma20 = float(latest['SMA_20'])
        sma50 = float(latest['SMA_50'])
        if not pd.isna(sma20) and not pd.isna(sma50):
            if sma20 > sma50: score += 1
            else: score -= 1
    except: pass

    try:
        close = float(latest['Close'])
        bb_upper = float(latest['BB_upper'])
        bb_lower = float(latest['BB_lower'])
        if not pd.isna(bb_upper) and not pd.isna(bb_lower):
            if close < bb_lower: score += 1
            elif close > bb_upper: score -= 1
    except: pass

    if score >= 3: return "BUY", score
    elif score <= -3: return "SELL", score
    else: return "HOLD", score

def get_combined_score(tech_score, fund_score, sentiment="NEUTRAL"):
    """Combine technical + fundamental + sentiment into final score."""
    # Weights: 40% technical, 40% fundamental, 20% sentiment
    tech_normalized = (tech_score + 6) / 12 * 10  # normalize -6 to +6 → 0 to 10
    fund_normalized = min(max(fund_score, 0), 10)   # already 0-10

    sentiment_score = 7 if sentiment == "BULLISH" else (3 if sentiment == "BEARISH" else 5)

    combined = (tech_normalized * 0.40) + (fund_normalized * 0.40) + (sentiment_score * 0.20)
    return round(combined, 1)

if __name__ == "__main__":
    print("Testing fundamentals for AAPL...")
    fund = get_fundamentals("AAPL")
    print(f"P/E: {fund.get('pe_ratio')}")
    print(f"Revenue Growth: {fund.get('revenue_growth')}%")
    print(f"Analyst Rating: {fund.get('analyst_rating')}")
    print(f"Upside: {fund.get('upside_pct')}%")
    print(f"Fundamental Score: {fund.get('fund_score')}/10")

    print("\nTesting fundamentals for RELIANCE.NS...")
    fund_in = get_fundamentals("RELIANCE.NS")
    print(f"P/E: {fund_in.get('pe_ratio')}")
    print(f"Analyst Rating: {fund_in.get('analyst_rating')}")
    print(f"Fundamental Score: {fund_in.get('fund_score')}/10")
