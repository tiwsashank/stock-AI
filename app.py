import streamlit as st
import plotly.graph_objects as go
import json
import os
from datetime import datetime
from week1_data import get_stock_data, add_indicators, get_signal, get_fundamentals
from week2_ai import get_news_sentiment
from watchlist import SECTOR_MAP, get_sp500_tickers, get_nifty50_tickers
from bucket import load_buckets, add_weekly_investment, get_bucket_performance, get_top_tickers_from_cache
from dotenv import load_dotenv

load_dotenv()

CACHE_FILE = "cache/recommendations.json"

st.set_page_config(page_title="StockAI", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if st.session_state.dark_mode:
    BG="𝔣0a0e1a";SURFACE="#0f172a";BORDER="#1e293b";TEXT="#f1f5f9";SUBTEXT="#64748b";MUTED="#334155"
    ACCENT="#38bdf8";GREEN="#22c55e";RED="#ef4444";NAV_BG="#0f172a";CARD_SH="0 1px 4px rgba(0,0,0,0.3)"
    PLOT_BG="#0f172a";PLOT_PAP="#0a0e1a";GRID_COL="#1e293b"
    INFO_BG="rgba(56,189,248,0.08)";INFO_BOR="rgba(56,189,248,0.2)";INFO_COL="#93c5fd"
    WARN_BG="rgba(251,191,36,0.08)";WARN_BOR="rgba(251,191,36,0.2)";WARN_COL="#fbbf24"
    OK_BG="rgba(34,197,94,0.08)";OK_BOR="rgba(34,197,94,0.2)";OK_COL="#86efac"
    TAB_ACT="#1e40af";BTN_BG="linear-gradient(135deg,#1d4ed8,#4f46e5)"
    THEME_ICON="☀️";THEME_LABEL="Light Mode";BG="#0a0e1a"
else:
    BG="#f7f8fa";SURFACE="#ffffff";BORDER="#e8eaed";TEXT="#1a1a2e";SUBTEXT="#6b7280";MUTED="#c4c9d4"
    ACCENT="#00c805";GREEN="#00a047";RED="#e11d48";NAV_BG="#ffffff";CARD_SH="0 1px 4px rgba(0,0,0,0.05)"
    PLOT_BG="#fafafa";PLOT_PAP="#ffffff";GRID_COL="#f0f1f5"
    INFO_BG="#eff6ff";INFO_BOR="#bfdbfe";INFO_COL="#1d4ed8"
    WARN_BG="#fffbeb";WARN_BOR="#fde68a";WARN_COL="#92400e"
    OK_BG="#f0fdf4";OK_BOR="#bbf7d0";OK_COL="#166534"
    TAB_ACT="#1a1a2e";BTN_BG="#1a1a2e"
    THEME_ICON="🌙";THEME_LABEL="Dark Mode"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;}}
.stApp{{background:{BG};color:{TEXT};}}
#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding-top:0!important;padding-bottom:2rem;max-width:1300px;}}
.navbar{{background:{NAV_BG};border-bottom:1px solid {BORDER};padding:0 28px;height:58px;display:flex;align-items:center;justify-content:space-between;margin:-1rem -1rem 20px -1rem;box-shadow:{CARD_SH};position:sticky;top:0;z-index:100;}}
.nav-logo{{font-size:20px;font-weight:800;color:{ACCENT};letter-spacing:-0.5px;}}
.nav-logo span{{color:{TEXT};}}
.nav-date{{font-size:12px;color:{SUBTEXT};font-family:'JetBrains Mono',monospace;}}
.stTabs [data-baseweb="tab-list"]{{background:{SURFACE};border-radius:12px;padding:5px;border:1px solid {BORDER};gap:2px;box-shadow:{CARD_SH};}}
.stTabs [data-baseweb="tab"]{{background:transparent;border-radius:8px;color:{SUBTEXT};font-weight:500;font-size:14px;padding:8px 20px;border:none;}}
.stTabs [aria-selected="true"]{{background:{TAB_ACT}!important;color:#ffffff!important;font-weight:600!important;}}
.kpi-card{{background:{SURFACE};border:1px solid {BORDER};border-radius:14px;padding:16px 20px;box-shadow:{CARD_SH};}}
.kpi-label{{color:{SUBTEXT};font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;}}
.kpi-value{{color:{TEXT};font-size:22px;font-weight:700;font-family:'JetBrains Mono',monospace;letter-spacing:-0.5px;}}
.kpi-sub{{font-size:12px;margin-top:3px;}}
.sec-header{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;color:{SUBTEXT};padding:5px 0;border-bottom:2px solid {BORDER};margin:18px 0 12px 0;}}
.rec-card{{background:{SURFACE};border:1px solid {BORDER};border-radius:16px;padding:18px 22px;margin-bottom:10px;position:relative;overflow:hidden;box-shadow:{CARD_SH};transition:box-shadow 0.2s,transform 0.2s;}}
.rec-card:hover{{box-shadow:0 6px 20px rgba(0,0,0,0.1);transform:translateY(-1px);}}
.rec-card::before{{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:{ACCENT};border-radius:4px 0 0 4px;}}
.rec-rank{{font-size:40px;font-weight:800;color:{BORDER};font-family:'JetBrains Mono',monospace;line-height:1;}}
.rec-ticker{{font-size:24px;font-weight:800;color:{TEXT};letter-spacing:-0.5px;}}
.rec-sector{{font-size:12px;color:{SUBTEXT};margin-top:2px;}}
.rec-reasoning{{font-size:14px;color:{SUBTEXT};line-height:1.7;margin-top:10px;}}
.fund-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px;}}
.fund-item{{background:{BG};border:1px solid {BORDER};border-radius:8px;padding:8px 12px;}}
.fund-label{{font-size:10px;color:{SUBTEXT};text-transform:uppercase;letter-spacing:0.8px;}}
.fund-value{{font-size:14px;font-weight:700;color:{TEXT};font-family:'JetBrains Mono',monospace;margin-top:2px;}}
.badge{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;}}
.b-strong-buy{{background:rgba(0,160,71,0.12);color:{GREEN};border:1px solid rgba(0,160,71,0.25);}}
.b-buy{{background:rgba(37,99,235,0.1);color:#2563eb;border:1px solid rgba(37,99,235,0.2);}}
.b-risk-low{{background:rgba(0,160,71,0.08);color:{GREEN};border:1px solid rgba(0,160,71,0.2);}}
.b-risk-med{{background:rgba(217,119,6,0.1);color:#d97706;border:1px solid rgba(217,119,6,0.2);}}
.b-risk-high{{background:rgba(225,29,72,0.1);color:{RED};border:1px solid rgba(225,29,72,0.2);}}
.b-neutral{{background:{BG};color:{SUBTEXT};border:1px solid {BORDER};}}
.strength-badge{{background:rgba(0,160,71,0.08);color:{GREEN};border:1px solid rgba(0,160,71,0.2);border-radius:8px;padding:4px 10px;font-size:12px;font-weight:600;}}
.risk-badge{{background:rgba(225,29,72,0.08);color:{RED};border:1px solid rgba(225,29,72,0.2);border-radius:8px;padding:4px 10px;font-size:12px;font-weight:600;}}
.score-bar-bg{{background:{BORDER};border-radius:4px;height:6px;margin-top:4px;}}
.stock-row{{background:{SURFACE};border:1px solid {BORDER};border-radius:10px;padding:10px 16px;margin-bottom:5px;display:flex;align-items:center;justify-content:space-between;}}
.mkt-card{{background:{SURFACE};border:1px solid {BORDER};border-radius:16px;padding:22px;text-align:center;box-shadow:{CARD_SH};}}
.mkt-name{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:{SUBTEXT};margin-bottom:8px;}}
.mkt-value{{font-size:26px;font-weight:800;color:{TEXT};font-family:'JetBrains Mono',monospace;letter-spacing:-1px;}}
.holding-row{{background:{SURFACE};border:1px solid {BORDER};border-radius:12px;padding:13px 16px;margin-bottom:7px;box-shadow:{CARD_SH};}}
.h-ticker{{font-size:15px;font-weight:700;color:{TEXT};}}
.h-detail{{font-size:12px;color:{SUBTEXT};font-family:'JetBrains Mono',monospace;margin-top:2px;}}
.h-price{{font-size:15px;font-weight:700;color:{TEXT};font-family:'JetBrains Mono',monospace;}}
.info-pill{{background:{INFO_BG};border:1px solid {INFO_BOR};border-radius:10px;padding:11px 16px;color:{INFO_COL};font-size:13px;margin:7px 0;}}
.warn-pill{{background:{WARN_BG};border:1px solid {WARN_BOR};border-radius:10px;padding:11px 16px;color:{WARN_COL};font-size:13px;margin:7px 0;}}
.ok-pill{{background:{OK_BG};border:1px solid {OK_BOR};border-radius:10px;padding:11px 16px;color:{OK_COL};font-size:13px;margin:7px 0;}}
.stButton>button{{background:{BTN_BG};color:#ffffff;border:none;border-radius:10px;font-weight:600;font-size:14px;padding:10px 22px;box-shadow:0 2px 8px rgba(0,0,0,0.15);transition:all 0.2s;}}
.stButton>button:hover{{opacity:0.88;transform:translateY(-1px);}}
.stSelectbox>div>div{{background:{SURFACE}!important;border:1px solid {BORDER}!important;border-radius:10px!important;color:{TEXT}!important;}}
.stNumberInput>div>div>input,.stDateInput>div>div>input{{background:{SURFACE}!important;border:1px solid {BORDER}!important;border-radius:10px!important;color:{TEXT}!important;}}
.streamlit-expanderHeader{{background:{SURFACE}!important;border:1px solid {BORDER}!important;border-radius:10px!important;color:{SUBTEXT}!important;}}
</style>
""", unsafe_allow_html=True)

# NAVBAR
col_nav1, col_nav2 = st.columns([6,1])
with col_nav1:
    st.markdown(f'<div class="navbar"><div class="nav-logo">Stock<span>AI</span> 📈</div><div class="nav-date">{datetime.now().strftime("%a, %b %d %Y")}</div></div>', unsafe_allow_html=True)
with col_nav2:
    st.markdown("<div style='padding-top:8px'></div>", unsafe_allow_html=True)
    if st.button(f"{THEME_ICON} {THEME_LABEL}"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return None

def chart_layout(title="", height=400):
    return dict(title=dict(text=title,font=dict(color=SUBTEXT,size=13,family="Inter")),height=height,
        paper_bgcolor=PLOT_PAP,plot_bgcolor=PLOT_BG,font=dict(color=SUBTEXT,family="Inter"),
        xaxis=dict(gridcolor=GRID_COL,showgrid=True,zeroline=False,linecolor=BORDER),
        yaxis=dict(gridcolor=GRID_COL,showgrid=True,zeroline=False,linecolor=BORDER),
        margin=dict(l=10,r=10,t=40,b=10),legend=dict(bgcolor=SURFACE,bordercolor=BORDER,borderwidth=1))

def fmt_pct(val):
    if val is None: return "N/A"
    return f"{val:+.1f}%" if val else "N/A"

def fmt_val(val, suffix=""):
    if val is None: return "N/A"
    return f"{val}{suffix}"

tab1, tab2, tab3, tab4 = st.tabs(["🏆  Top Picks", "📊  Analysis", "🌍  Market", "🪣  Buckets"])

# ══════════════════════════════
# TAB 1: TOP PICKS
# ══════════════════════════════
with tab1:
    cache = load_cache()
    if not cache:
        st.markdown('<div class="warn-pill">⚠️ No data yet. Run scanner.py first.</div>', unsafe_allow_html=True)
    else:
        c1,c2,c3,c4 = st.columns(4)
        for col,label,val in [
            (c1,"Last Scanned",cache['last_updated']),
            (c2,"Stocks Analyzed",str(cache['total_scanned'])),
            (c3,"Top Picks",str(len(cache.get('recommendations',[])))),
            (c4,"Method",cache.get('scoring_method','Technical only'))
        ]:
            with col:
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:14px;letter-spacing:0">{val}</div></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="info-pill">📊 {cache.get("market_summary","")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">Filter by Sector</div>', unsafe_allow_html=True)
        sectors = ["All"] + list(SECTOR_MAP.keys())
        selected_sector = st.selectbox("", sectors, label_visibility="collapsed")

        recs = cache.get("recommendations",[])
        if selected_sector != "All":
            recs = [r for r in recs if r.get("sector") == selected_sector]

        st.markdown('<div class="sec-header">AI Recommendations — Technical + Fundamental</div>', unsafe_allow_html=True)
        for rec in recs:
            action = rec.get('action','BUY')
            risk = rec.get('risk','MEDIUM')
            ba = "b-strong-buy" if action == "STRONG BUY" else "b-buy"
            br = "b-risk-low" if risk == "LOW" else ("b-risk-high" if risk == "HIGH" else "b-risk-med")
            key_strength = rec.get('key_strength','')
            key_risk = rec.get('key_risk','')

            # Get fundamental data from all_scores
            all_scores = cache.get("all_scores",[])
            stock_data = next((s for s in all_scores if s['ticker'] == rec['ticker']), {})
            pe = stock_data.get('pe_ratio')
            rev_growth = stock_data.get('revenue_growth')
            profit_m = stock_data.get('profit_margin')
            upside = stock_data.get('upside_pct')
            analyst = stock_data.get('analyst_rating','N/A')
            fund_score = stock_data.get('fund_score', 0)
            tech_score = stock_data.get('tech_score', 0)
            combined = stock_data.get('combined_score', 0)

            st.markdown(f"""
            <div class="rec-card">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">
                    <div style="display:flex;align-items:center;gap:16px;">
                        <div class="rec-rank">#{rec['rank']}</div>
                        <div>
                            <div class="rec-ticker">{rec['ticker']}</div>
                            <div class="rec-sector">🏭 {rec.get('sector','')} · {stock_data.get('industry','')}</div>
                        </div>
                    </div>
                    <div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;align-items:center;">
                        <span class="badge {ba}">⭐ {action}</span>
                        <span class="badge {br}">Risk: {risk}</span>
                        <span class="badge b-neutral">⏱ {rec.get('target_horizon','')}</span>
                        <span class="badge b-neutral">📊 Score: {combined}/10</span>
                    </div>
                </div>
                <div class="rec-reasoning">{rec.get('reasoning','')}</div>
                <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
                    {'<span class="strength-badge">💪 ' + key_strength + '</span>' if key_strength else ''}
                    {'<span class="risk-badge">⚠️ ' + key_risk + '</span>' if key_risk else ''}
                </div>
                <div class="fund-grid">
                    <div class="fund-item"><div class="fund-label">P/E Ratio</div><div class="fund-value">{fmt_val(pe,'x')}</div></div>
                    <div class="fund-item"><div class="fund-label">Revenue Growth</div><div class="fund-value">{fmt_pct(rev_growth)}</div></div>
                    <div class="fund-item"><div class="fund-label">Profit Margin</div><div class="fund-value">{fmt_pct(profit_m)}</div></div>
                    <div class="fund-item"><div class="fund-label">Analyst Upside</div><div class="fund-value" style="color:{'#00a047' if upside and upside>0 else '#e11d48'}">{fmt_pct(upside)}</div></div>
                    <div class="fund-item"><div class="fund-label">Analyst Rating</div><div class="fund-value" style="font-size:11px">{analyst}</div></div>
                    <div class="fund-item"><div class="fund-label">Tech Score</div><div class="fund-value">{tech_score}</div></div>
                    <div class="fund-item"><div class="fund-label">Fund Score</div><div class="fund-value">{fund_score}</div></div>
                    <div class="fund-item"><div class="fund-label">Combined</div><div class="fund-value" style="color:{ACCENT}">{combined}/10</div></div>
                </div>
            </div>""", unsafe_allow_html=True)

        with st.expander("📋 View All Scanned Stocks"):
            all_scores = cache.get("all_scores",[])
            if selected_sector != "All":
                all_scores = [s for s in all_scores if s.get("sector") == selected_sector]
            for i,s in enumerate(all_scores):
                sig = s['signal']
                sc = GREEN if sig == "BUY" else (RED if sig == "SELL" else SUBTEXT)
                mkt = "🇺🇸" if s.get('market') == "US" else "🇮🇳"
                combined = s.get('combined_score', s.get('tech_score',0))
                analyst = s.get('analyst_rating','N/A')
                upside = s.get('upside_pct')
                st.markdown(f"""<div class="stock-row">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="color:{MUTED};font-size:11px;font-family:'JetBrains Mono',monospace;width:26px;">#{i+1}</span>
                        <span>{mkt}</span>
                        <span style="font-weight:700;color:{TEXT};">{s['ticker']}</span>
                        <span style="color:{SUBTEXT};font-size:12px;">{s.get('sector','')}</span>
                    </div>
                    <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;">
                        <span style="color:{SUBTEXT};font-family:'JetBrains Mono',monospace;font-size:13px;">${s['price']}</span>
                        <span style="color:{SUBTEXT};font-size:12px;">RSI {s['rsi']}</span>
                        <span style="color:{SUBTEXT};font-size:12px;">PE {s.get('pe_ratio','N/A')}</span>
                        <span style="color:{'#00a047' if upside and upside>0 else SUBTEXT};font-size:12px;">↑{upside}%</span>
                        <span style="color:{SUBTEXT};font-size:12px;">{analyst}</span>
                        <span style="color:{ACCENT};font-weight:700;font-size:13px;">{combined}/10</span>
                        <span style="color:{sc};font-weight:700;font-size:13px;">{sig}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-header">Refresh Scan</div>', unsafe_allow_html=True)
        st.markdown('<div class="warn-pill">⏱ Run monthly · ~$0.30 · 10-15 mins for 100 stocks with fundamentals</div>', unsafe_allow_html=True)
        if st.button("🔄 Run New Scan"):
            with st.spinner("Scanning 100 stocks with fundamentals..."):
                from scanner import run_monthly_scan
                run_monthly_scan()
            st.markdown('<div class="ok-pill">✅ Done! Reload page to see results.</div>', unsafe_allow_html=True)

# ══════════════════════════════
# TAB 2: STOCK ANALYSIS
# ══════════════════════════════
with tab2:
    all_tickers = get_sp500_tickers()[:50] + get_nifty50_tickers()[:50]
    c1,c2 = st.columns([3,1])
    with c1: selected = st.selectbox("Select Stock", all_tickers)
    with c2: period = st.selectbox("Period", ["1mo","3mo","6mo","1y"], index=3)

    if st.button("Analyze Stock"):
        with st.spinner(f"Loading {selected}..."):
            df = get_stock_data(selected, period)
            df = add_indicators(df)
            signal, score = get_signal(df)
            latest = df.iloc[-1]

        with st.spinner("Fetching fundamentals..."):
            fund = get_fundamentals(selected)

        curr = float(latest['Close'])
        rsi_v = float(latest['RSI']) if str(latest['RSI']) != 'nan' else None
        sma20 = float(latest['SMA_20']) if str(latest['SMA_20']) != 'nan' else None
        sma200 = float(latest['SMA_200']) if str(latest['SMA_200']) != 'nan' else None
        sig_color = GREEN if signal == "BUY" else (RED if signal == "SELL" else SUBTEXT)

        # Technical metrics
        st.markdown('<div class="sec-header">Technical Indicators</div>', unsafe_allow_html=True)
        c1,c2,c3,c4,c5 = st.columns(5)
        for col,label,val,extra in [
            (c1,"Price",f"${curr:.2f}",""),
            (c2,"RSI",f"{rsi_v:.1f}" if rsi_v else "N/A",
             f"color:{RED};" if rsi_v and rsi_v>70 else (f"color:{GREEN};" if rsi_v and rsi_v<30 else "")),
            (c3,"SMA 20",f"${sma20:.2f}" if sma20 else "N/A",""),
            (c4,"SMA 200",f"${sma200:.2f}" if sma200 else "N/A",""),
            (c5,"Signal",signal,f"color:{sig_color};")
        ]:
            with col:
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:19px;{extra}">{val}</div></div>', unsafe_allow_html=True)

        # Fundamental metrics
        st.markdown('<div class="sec-header">Fundamental Analysis</div>', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        upside = fund.get('upside_pct')
        upside_color = f"color:{GREEN};" if upside and upside > 0 else f"color:{RED};"
        analyst = fund.get('analyst_rating','N/A')
        analyst_color = f"color:{GREEN};" if analyst in ['BUY','STRONG BUY'] else (f"color:{RED};" if analyst in ['SELL','STRONG SELL'] else "")

        for col,label,val,extra in [
            (c1,"P/E Ratio",f"{fund.get('pe_ratio','N/A')}x",""),
            (c2,"Revenue Growth",fmt_pct(fund.get('revenue_growth')),f"color:{GREEN};" if fund.get('revenue_growth') and fund.get('revenue_growth')>0 else ""),
            (c3,"Profit Margin",fmt_pct(fund.get('profit_margin')),""),
            (c4,"Analyst Upside",fmt_pct(upside),upside_color),
        ]:
            with col:
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:19px;{extra}">{val}</div></div>', unsafe_allow_html=True)

        c1,c2,c3,c4 = st.columns(4)
        for col,label,val,extra in [
            (c1,"Analyst Rating",analyst,analyst_color),
            (c2,"Debt/Equity",f"{fund.get('debt_to_equity','N/A')}",""),
            (c3,"52W Position",f"{fund.get('week_52_position_pct','N/A')}%" if fund.get('week_52_position_pct') else "N/A",""),
            (c4,"Dividend Yield",f"{fund.get('dividend_yield','N/A')}%" if fund.get('dividend_yield') else "N/A",""),
        ]:
            with col:
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:17px;{extra}">{val}</div></div>', unsafe_allow_html=True)

        # Fund score
        fund_score = fund.get('fund_score', 0)
        st.markdown(f'<div class="info-pill">📊 Fundamental Score: <strong>{fund_score}/10</strong> · Sector: {fund.get("sector","N/A")} · Industry: {fund.get("industry","N/A")}</div>', unsafe_allow_html=True)

        st.markdown("")
        up_color = "#00c805" if not st.session_state.dark_mode else "#22c55e"
        dn_color = "#ff5000" if not st.session_state.dark_mode else "#ef4444"

        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name=selected,
            increasing_line_color=up_color, decreasing_line_color=dn_color))
        if sma20: fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='#f59e0b',width=1.5)))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='#8b5cf6',width=1.5)))
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color=SUBTEXT,dash='dash',width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color=SUBTEXT,dash='dash',width=1)))
        fig.update_layout(**chart_layout(f"{selected} · Price Chart",420), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        cr,cm = st.columns(2)
        with cr:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#8b5cf6',width=2), fill='tozeroy', fillcolor='rgba(139,92,246,0.06)'))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color=RED, line_width=1)
            fig_rsi.add_hline(y=30, line_dash="dash", line_color=GREEN, line_width=1)
            fig_rsi.update_layout(**chart_layout("RSI (14)",220))
            st.plotly_chart(fig_rsi, use_container_width=True)
        with cm:
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='#0ea5e9',width=2)))
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'], name='Signal', line=dict(color='#f97316',width=2)))
            fig_macd.update_layout(**chart_layout("MACD",220))
            st.plotly_chart(fig_macd, use_container_width=True)

        st.markdown('<div class="sec-header">News Sentiment</div>', unsafe_allow_html=True)
        with st.spinner("Fetching news..."):
            sentiment = get_news_sentiment(selected)
        s = sentiment.get("sentiment","NEUTRAL")
        sc = GREEN if s == "BULLISH" else (RED if s == "BEARISH" else SUBTEXT)
        si = "📈" if s == "BULLISH" else ("📉" if s == "BEARISH" else "➡️")
        themes = ''.join([f'<span class="badge b-neutral">{t}</span>' for t in sentiment.get('key_themes',[])])
        st.markdown(f"""<div class="rec-card" style="margin-top:0;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                <span style="font-size:22px;">{si}</span>
                <span style="color:{sc};font-size:18px;font-weight:800;">{s}</span>
                <span class="badge b-neutral">Confidence: {sentiment.get('confidence','')}</span>
            </div>
            <div style="color:{SUBTEXT};font-size:14px;line-height:1.7;">{sentiment.get('summary','')}</div>
            <div style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;">{themes}</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════
# TAB 3: MARKET
# ══════════════════════════════
with tab3:
    if st.button("Load Live Market Data"):
        st.markdown('<div class="sec-header">🇺🇸 US Indices</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        for col,(name,ticker) in zip([c1,c2,c3],[("S&P 500","^GSPC"),("NASDAQ","^IXIC"),("Dow Jones","^DJI")]):
            with col:
                df = get_stock_data(ticker,"5d")
                v=float(df['Close'].iloc[-1]); p=float(df['Close'].iloc[-2])
                chg=((v-p)/p)*100; cc=GREEN if chg>0 else RED
                st.markdown(f'<div class="mkt-card"><div class="mkt-name">{name}</div><div class="mkt-value">{v:,.2f}</div><div style="color:{cc};font-size:14px;font-weight:600;margin-top:6px;">{"▲" if chg>0 else "▼"} {abs(chg):.2f}%</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-header">🇮🇳 Indian Indices</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        for col,(name,ticker) in zip([c1,c2],[("Nifty 50","^NSEI"),("Sensex","^BSESN")]):
            with col:
                df = get_stock_data(ticker,"5d")
                v=float(df['Close'].iloc[-1]); p=float(df['Close'].iloc[-2])
                chg=((v-p)/p)*100; cc=GREEN if chg>0 else RED
                st.markdown(f'<div class="mkt-card"><div class="mkt-name">{name}</div><div class="mkt-value">{v:,.2f}</div><div style="color:{cc};font-size:14px;font-weight:600;margin-top:6px;">{"▲" if chg>0 else "▼"} {abs(chg):.2f}%</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-pill">Click the button to load live index data.</div>', unsafe_allow_html=True)

# ══════════════════════════════
# TAB 4: BUCKETS
# ══════════════════════════════
with tab4:
    st.markdown('<div class="info-pill">💡 <strong>Weekly SIP Strategy</strong> — Fixed weekly investment split across top 5 AI picks.</div>', unsafe_allow_html=True)
    col1,col2 = st.columns(2)

    for col,market,symbol,currency in [(col1,"US","$","USD"),(col2,"IN","₹","INR")]:
        with col:
            flag = "🇺🇸" if market == "US" else "🇮🇳"
            st.markdown(f'<div class="sec-header">{flag} {market} Bucket · {symbol}100/week</div>', unsafe_allow_html=True)
            perf = get_bucket_performance(market)

            if perf["total_invested"] > 0:
                pnl_color = GREEN if perf['pnl'] >= 0 else RED
                m1,m2,m3 = st.columns(3)
                for mc,ml,mv,mc_extra,sub in [
                    (m1,"Invested",f"{symbol}{perf['total_invested']:,.0f}","",""),
                    (m2,"Value",f"{symbol}{perf['current_value']:,.0f}","",""),
                    (m3,"P&L",f"{symbol}{abs(perf['pnl']):,.2f}",f"color:{pnl_color};",f'<div class="kpi-sub" style="color:{pnl_color}">{perf["pnl_pct"]:+.1f}%</div>')
                ]:
                    with mc:
                        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{ml}</div><div class="kpi-value" style="font-size:17px;{mc_extra}">{mv}</div>{sub}</div>', unsafe_allow_html=True)

                st.markdown('<div class="sec-header">Holdings</div>', unsafe_allow_html=True)
                for h in perf['holdings_summary']:
                    hc = GREEN if h['pnl_pct'] > 0 else RED
                    icon = "▲" if h['pnl_pct'] > 0 else "▼"
                    st.markdown(f"""<div class="holding-row">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div><div class="h-ticker">{h['ticker']}</div>
                            <div class="h-detail">{h['shares']} sh · avg {symbol}{h['avg_buy_price']}</div></div>
                            <div style="text-align:right;">
                                <div class="h-price">{symbol}{h['current_price']}</div>
                                <div style="color:{hc};font-size:13px;font-weight:600;">{icon} {abs(h['pnl_pct']):.1f}%</div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="info-pill">No investments yet.</div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-header">Add Weekly Investment</div>', unsafe_allow_html=True)
            amount = st.number_input(f"Amount ({currency})", value=100.0, min_value=1.0, key=f"amt_{market}")
            inv_date = st.date_input("Date", value=datetime.now(), key=f"date_{market}")
            top_picks = get_top_tickers_from_cache(market, 5)
            if top_picks:
                st.markdown(f'<div class="info-pill">Splits across: <strong>{", ".join(top_picks)}</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warn-pill">Run scanner.py first.</div>', unsafe_allow_html=True)

            if st.button(f"💰 Invest {symbol}{int(amount)}", key=f"btn_{market}", type="primary"):
                if top_picks:
                    with st.spinner("Fetching prices..."):
                        prices,valid = [],[]
                        for t in top_picks:
                            try:
                                df = get_stock_data(t,"5d")
                                prices.append(float(df['Close'].iloc[-1]))
                                valid.append(t)
                            except: pass
                    if valid:
                        add_weekly_investment(market, amount, valid, prices, str(inv_date))
                        st.markdown(f'<div class="ok-pill">✅ {symbol}{amount:.0f} invested across {", ".join(valid)}</div>', unsafe_allow_html=True)
                        st.rerun()

    buckets = load_buckets()
    us_inv = buckets.get("US",{}).get("investments",[])
    in_inv = buckets.get("IN",{}).get("investments",[])
    if us_inv or in_inv:
        st.markdown('<div class="sec-header">Cumulative Investment Over Time</div>', unsafe_allow_html=True)
        fig = go.Figure()
        if us_inv:
            dates=[i["date"] for i in us_inv]
            cum=[sum(x["total_invested"] for x in us_inv[:j+1]) for j in range(len(us_inv))]
            fig.add_trace(go.Scatter(x=dates,y=cum,name="US ($)",line=dict(color=ACCENT,width=2.5),fill='tozeroy',fillcolor='rgba(0,200,5,0.06)'))
        if in_inv:
            dates=[i["date"] for i in in_inv]
            cum=[sum(x["total_invested"] for x in in_inv[:j+1]) for j in range(len(in_inv))]
            fig.add_trace(go.Scatter(x=dates,y=cum,name="India (₹)",line=dict(color="#f97316",width=2.5),fill='tozeroy',fillcolor='rgba(249,115,22,0.06)'))
        fig.update_layout(**chart_layout("",260))
        st.plotly_chart(fig, use_container_width=True)

st.markdown(f'<div style="text-align:center;color:{MUTED};font-size:12px;padding:20px 0;border-top:1px solid {BORDER};margin-top:28px;">⚠️ For personal research only · Not financial advice · Always do your own due diligence</div>', unsafe_allow_html=True)
