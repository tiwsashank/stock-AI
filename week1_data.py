# week1_data.py — Fetch stock data + technical indicators
import yfinance as yf
import ta
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_stock_data(ticker, period="1y"):
    df = yf.download(ticker, period=period, auto_adjust=True)
    df.columns = df.columns.get_level_values(0)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    return df

def add_indicators(df):
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    volume = df['Volume'].squeeze()

    # RSI
    df['RSI'] = ta.momentum.RSIIndicator(close, window=14).rsi()

    # MACD
    macd = ta.trend.MACD(close)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close, window=20)
    df['BB_upper'] = bb.bollinger_hband()
    df['BB_lower'] = bb.bollinger_lband()
    df['BB_mid'] = bb.bollinger_mavg()

    # Moving Averages
    df['SMA_20'] = ta.trend.SMAIndicator(close, window=20).sma_indicator()
    df['SMA_50'] = ta.trend.SMAIndicator(close, window=50).sma_indicator()
    df['SMA_200'] = ta.trend.SMAIndicator(close, window=200).sma_indicator()

    return df

def get_signal(df):
    latest = df.iloc[-1]
    score = 0

    rsi = latest['RSI']
    if rsi < 30: score += 2
    elif rsi > 70: score -= 2

    if latest['MACD'] > latest['MACD_signal']: score += 2
    else: score -= 2

    if latest['SMA_20'] > latest['SMA_50']: score += 1
    else: score -= 1

    if latest['Close'] < latest['BB_lower']: score += 1
    elif latest['Close'] > latest['BB_upper']: score -= 1

    if score >= 3: return "BUY", score
    elif score <= -3: return "SELL", score
    else: return "HOLD", score

def get_portfolio_summary(holdings):
    results = []
    for h in holdings:
        ticker = h['ticker']
        print(f"Fetching {ticker}...")
        try:
            df = get_stock_data(ticker)
            df = add_indicators(df)
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            cost = h['avg_cost']
            shares = h['shares']
            pnl = (current_price - cost) * shares
            pnl_pct = ((current_price - cost) / cost) * 100
            signal, score = get_signal(df)
            results.append({
                'ticker': ticker,
                'market': h['market'],
                'shares': shares,
                'avg_cost': cost,
                'current_price': round(current_price, 2),
                'pnl': round(pnl, 2),
                'pnl_pct': round(pnl_pct, 2),
                'rsi': round(float(latest['RSI']), 1) if not pd.isna(latest['RSI']) else None,
                'signal': signal,
                'signal_score': score
            })
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
    return results

if __name__ == "__main__":
    holdings = [
        {"ticker": "AAPL", "shares": 10, "avg_cost": 150.00, "market": "US"},
        {"ticker": "RELIANCE.NS", "shares": 5, "avg_cost": 2400.00, "market": "IN"},
        {"ticker": "SPY", "shares": 3, "avg_cost": 420.00, "market": "US"}
    ]
    results = get_portfolio_summary(holdings)
    for r in results:
        print(f"\n{r['ticker']}: ${r['current_price']} | P&L: {r['pnl_pct']}% | Signal: {r['signal']} | RSI: {r['rsi']}")