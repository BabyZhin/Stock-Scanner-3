import time
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------
# Page config (iPad + desktop friendly)
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Flow Scanner | US Stocks",
    page_icon="📡",
    layout="wide",
)

# ---------------------------------------------------------------
# Theme
# ---------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root{
  --bg:#090B16; --panel:#11142A; --panel2:#171B38; --line:#232850;
  --ink:#E8EAF6; --mute:#8B90B5;
  --up:#2EE6A6; --down:#FF5C7A; --violet:#7C5CFF; --cyan:#38D4FF;
}

html, body, .stApp, [class*="css"]{ font-family:'Sora',sans-serif; color:var(--ink); }
.stApp{
  background:
    radial-gradient(1100px 520px at 12% -10%, rgba(124,92,255,.24), transparent 60%),
    radial-gradient(900px 420px at 100% 0%, rgba(56,212,255,.13), transparent 60%),
    var(--bg);
}
#MainMenu, footer{ visibility:hidden; }
header[data-testid="stHeader"]{ background:transparent; }
.block-container{ padding-top:2.2rem; max-width:1250px; }

/* Sidebar */
section[data-testid="stSidebar"]{ background:#0C0F1F; border-right:1px solid var(--line); }
section[data-testid="stSidebar"] h2{ font-size:1.05rem; font-weight:600; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p{ color:var(--ink); }
section[data-testid="stSidebar"] input{
  background:var(--panel) !important; border:1px solid var(--line) !important;
  border-radius:10px !important; font-family:'IBM Plex Mono',monospace !important;
}

/* Buttons */
.stButton > button, .stDownloadButton > button{
  width:100%; border:0; border-radius:12px; padding:.7rem 1rem;
  font-family:'Sora',sans-serif; font-weight:600; color:#fff;
  background:linear-gradient(120deg,var(--violet),var(--cyan));
  box-shadow:0 0 22px rgba(124,92,255,.45);
  transition:transform .15s ease, box-shadow .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover{
  transform:translateY(-1px); box-shadow:0 0 34px rgba(56,212,255,.55); color:#fff;
}
.stDownloadButton > button{
  background:var(--panel2); border:1px solid var(--line); box-shadow:none; width:auto;
}

/* Hero */
.hero{ margin-bottom:1.4rem; }
.hero-title{
  font-size:2.5rem; font-weight:700; letter-spacing:-.02em; line-height:1.1;
  background:linear-gradient(100deg,#fff 10%,#B7A8FF 55%,var(--cyan) 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.hero-sub{ color:var(--mute); margin-top:.5rem; font-size:1rem; max-width:60ch; }

/* Stat strip */
.stats{ display:grid; grid-template-columns:repeat(4,1fr); gap:.8rem; margin:0 0 1.6rem; }
.stat{
  background:linear-gradient(160deg,var(--panel2),var(--panel));
  border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem;
}
.stat-v{ font-family:'IBM Plex Mono',monospace; font-weight:600; font-size:1.55rem; }
.stat-l{ color:var(--mute); font-size:.82rem; margin-top:.25rem; }
@media (max-width:760px){ .stats{ grid-template-columns:repeat(2,1fr); } .hero-title{ font-size:1.9rem; } }

/* Signal panels */
.panel{
  background:linear-gradient(170deg,var(--panel2),var(--panel));
  border:1px solid var(--line); border-radius:16px; padding:1.1rem 1.2rem 1.25rem;
  margin-bottom:1.1rem; position:relative; overflow:hidden;
}
.panel::before{
  content:""; position:absolute; inset:0 0 auto 0; height:2px;
}
.panel.up::before{ background:linear-gradient(90deg,var(--up),transparent); }
.panel.down::before{ background:linear-gradient(90deg,var(--down),transparent); }
.panel-head{ display:flex; align-items:center; gap:.8rem; margin-bottom:.9rem; }
.panel-title{ font-weight:600; font-size:1.02rem; }
.panel-sub{ color:var(--mute); font-size:.8rem; margin-top:.15rem; }
.dot{ width:10px; height:10px; border-radius:50%; flex:none; }
.dot.up{ background:var(--up); box-shadow:0 0 12px var(--up); }
.dot.down{ background:var(--down); box-shadow:0 0 12px var(--down); }
.count{
  margin-left:auto; font-family:'IBM Plex Mono',monospace; font-weight:600;
  font-size:1.3rem; padding:.1rem .7rem; border-radius:10px; background:rgba(255,255,255,.05);
}

.chips{ display:flex; flex-wrap:wrap; gap:.5rem; }
.chip{
  font-family:'IBM Plex Mono',monospace; font-weight:600; font-size:.88rem;
  padding:.38rem .75rem; border-radius:999px; text-decoration:none !important;
  transition:box-shadow .15s ease, background .15s ease;
}
.chip.up{ color:var(--up); background:rgba(46,230,166,.09); border:1px solid rgba(46,230,166,.35); }
.chip.down{ color:var(--down); background:rgba(255,92,122,.09); border:1px solid rgba(255,92,122,.35); }
.chip.up:hover{ background:rgba(46,230,166,.18); box-shadow:0 0 16px rgba(46,230,166,.45); }
.chip.down:hover{ background:rgba(255,92,122,.18); box-shadow:0 0 16px rgba(255,92,122,.45); }
.empty{ color:var(--mute); font-size:.88rem; }

/* Notices */
.notice{
  border:1px solid var(--line); border-radius:14px; padding:.9rem 1.1rem;
  background:var(--panel); color:var(--mute); margin-bottom:1.2rem;
}
.notice b{ color:var(--ink); font-weight:600; }
.notice.ok{ border-color:rgba(46,230,166,.35); }

/* Progress bar */
.stProgress > div > div > div > div{ background:linear-gradient(90deg,var(--violet),var(--cyan)); }
.stProgress p{ font-family:'IBM Plex Mono',monospace; color:var(--mute); font-size:.85rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------
def stat(label, value):
    return f'<div class="stat"><div class="stat-v">{value}</div><div class="stat-l">{label}</div></div>'


def panel(title, subtitle, items, kind):
    if items:
        chips = "".join(
            f'<a class="chip {kind}" href="https://finance.yahoo.com/quote/{t}" target="_blank">{t}</a>'
            for t in sorted(items)
        )
    else:
        chips = '<span class="empty">No matches in this scan</span>'
    return (
        f'<div class="panel {kind}"><div class="panel-head"><span class="dot {kind}"></span>'
        f'<div><div class="panel-title">{title}</div><div class="panel-sub">{subtitle}</div></div>'
        f'<div class="count">{len(items)}</div></div><div class="chips">{chips}</div></div>'
    )


st.markdown(
    '<div class="hero"><div class="hero-title">US Stock Flow Scanner</div>'
    '<div class="hero-sub">Institutional flow and trend signals across large, liquid US stocks. '
    'Tap any ticker to open it on Yahoo Finance.</div></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------
st.sidebar.header("⚙️ Scan Settings")
scan_mode = st.sidebar.radio(
    "Select Stock Universe",
    [
        "Auto scan US market (Market Cap > $1.6B, Float > 400M + Hot Liquids)",
        "Custom stock tickers",
    ],
)

if scan_mode == "Custom stock tickers":
    custom_tickers = st.sidebar.text_input(
        "Enter tickers (comma separated, e.g., AAPL, TSLA, NVDA)",
        "AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, AMD, NFLX, INTC",
    )
    tickers = [s.strip().upper() for s in custom_tickers.split(",") if s.strip()]
else:
    # Dynamically fetch S&P 500, Nasdaq 100, and comprehensive high-liquidity hot stocks pool
    @st.cache_data(ttl=86400)
    def get_filtered_us_universe():
        try:
            # 1. Fetch S&P 500
            table_sp = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
            sp_tickers = table_sp[0]['Symbol'].str.replace('.', '-', regex=False).tolist()

            # 2. Fetch Nasdaq 100
            table_ndx = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')
            df_ndx = next((t_df for t_df in table_ndx if 'Ticker' in t_df.columns or 'Symbol' in t_df.columns), table_ndx[4])
            col_name = 'Ticker' if 'Ticker' in df_ndx.columns else 'Symbol'
            ndx_tickers = df_ndx[col_name].str.replace('.', '-', regex=False).tolist()

            # 3. Comprehensive high-liquidity hot US growth/value/meme/tech stocks pool
            extra_hot_tickers = [
                "PLTR", "COIN", "MARA", "RIOT", "SQ", "SHOP", "ROKU", "U", "ARM", "SMCI",
                "MSTR", "HOOD", "SNOW", "DDOG", "NET", "CRWD", "ZS", "PANW", "TEAM", "MELI",
                "SE", "BABA", "JD", "PDD", "NIO", "XPEV", "LI", "TSM", "ASML", "MU", "QCOM",
                "PYPL", "ABNB", "UBER", "LYFT", "DASH", "PINS", "SNAP", "RBLX", "DKNG", "PATH",
                "CELH", "ELF", "RDDT", "ASTS", "LUNR", "RKLB", "IONQ", "RGTI", "HOOD", "CVNA"
            ]

            raw_tickers = list(set(sp_tickers + ndx_tickers + extra_hot_tickers))

            # 4. Filter criteria check function via yfinance info (Market Cap > $1.6B and Float > 400M)
            def check_criteria(ticker):
                try:
                    info = yf.Ticker(ticker).info
                    mcap = info.get('marketCap', 0) or 0
                    float_shares = info.get('floatShares', 0) or 0
                    if mcap > 1.6e9 and float_shares > 4e8:
                        return ticker
                except:
                    pass
                return None

            filtered_tickers = []
            with ThreadPoolExecutor(max_workers=15) as executor:
                results = executor.map(check_criteria, raw_tickers)
                filtered_tickers = [t for t in results if t is not None]

            return filtered_tickers if filtered_tickers else raw_tickers[:150]
        except Exception:
            # Fallback robust broad list
            return [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "AMD", "INTC",
                "AVGO", "COST", "PEP", "TMUS", "CSCO", "CRM", "QCOM", "TXN", "AMAT", "IBM",
                "GE", "CAT", "AXP", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "UNH", "JNJ",
                "LLY", "XOM", "CVX", "COP", "SLB", "PFE", "ABBV", "MRK", "T", "VZ", "WMT", "HD",
                "PLTR", "COIN", "MARA", "SQ", "SHOP", "ROKU", "ARM", "SMCI", "MSTR", "HOOD"
            ]

    with st.spinner("Filtering stocks (Market Cap > $1.6B & Float > 400M + Hot Liquids)... Please wait..."):
        tickers = get_filtered_us_universe()

timeframe = st.sidebar.selectbox("Scan Timeframe", ["Daily", "Weekly"])
interval_val = "1d" if timeframe == "Daily" else "1wk"


# ---------------------------------------------------------------
# Indicator logic (unchanged)
# ---------------------------------------------------------------
def process_single_ticker(ticker, interval_val):
    try:
        df = yf.download(ticker, period="1y", interval=interval_val, progress=False)
        if df.empty or len(df) < 60:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']
        high = df['High']
        low = df['Low']
        vol = df['Volume']

        # --- KEIAS Indicator Logic ---
        ll52 = low.rolling(252).min() if len(df) >= 252 else low.min()
        hh52 = high.rolling(252).max() if len(df) >= 252 else high.max()
        pos_score = np.where(hh52 == ll52, 0, (close - ll52) / (hh52 - ll52) * 200 - 100)

        ma50 = close.rolling(50).mean()
        trend_score = np.where(close > ma50, 100, -100)

        coef = np.where(high == low, 0.001, (2 * close - high - low) / (high - low))
        raw_ev = vol * coef
        sd_ev = raw_ev.rolling(30).std()
        vol_score = np.where(sd_ev == 0, 0, (raw_ev - raw_ev.rolling(30).mean()) / sd_ev * 100)
        vol_score_lim = np.clip(vol_score, -100, 100)

        raw_ias = pos_score * 0.3 + trend_score * 0.4 + vol_score_lim * 0.3
        ias = pd.Series(raw_ias, index=df.index).rolling(3).mean()

        keias_buy, keias_sell = False, False
        if len(ias) > 2:
            if ias.iloc[-1] > 60 and ias.iloc[-2] <= 60:
                keias_buy = True
            elif ias.iloc[-1] < -60 and ias.iloc[-2] >= -60:
                keias_sell = True

        # --- KXKX Indicator Logic ---
        vma20 = vol.rolling(20).mean()
        vma60 = vol.rolling(60).mean()
        amp = np.where((high - low) == 0, 0.001, high - low)
        pos_kx = ((close - low) - (high - close)) / amp
        net_inst = pos_kx * vol

        ema50 = close.ewm(span=50, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()
        safe_zone = (close > ema50) | (ema50 > ema200)

        zqxsl = (vol.rolling(30).min() < vma60 * 0.5)
        zcxdw = (close <= close.rolling(60).min() * 1.15)
        szjbf = (vol > vma20 * 2.0) & (net_inst > 0)

        inst_buy_signal = safe_zone & zqxsl & zcxdw & szjbf
        kxkx_buy = bool(len(inst_buy_signal) > 0 and inst_buy_signal.iloc[-1])

        zcxgw = (close >= high.rolling(60).max() * 0.95)
        inst_sell_signal = zcxgw & (vol > vma20 * 1.8) & (net_inst < 0)
        kxkx_sell = bool(len(inst_sell_signal) > 0 and inst_sell_signal.iloc[-1])

        return {
            "ticker": ticker,
            "keias_buy": keias_buy,
            "keias_sell": keias_sell,
            "kxkx_buy": kxkx_buy,
            "kxkx_sell": kxkx_sell,
        }
    except Exception:
        return None


# ---------------------------------------------------------------
# Stat strip (updates after the scan)
# ---------------------------------------------------------------
stats_slot = st.empty()


def render_stats(found="-", elapsed="-"):
    stats_slot.markdown(
        '<div class="stats">'
        + stat("Stocks in universe", len(tickers))
        + stat("Timeframe", timeframe)
        + stat("Signals found", found)
        + stat("Scan time", elapsed)
        + "</div>",
        unsafe_allow_html=True,
    )


render_stats()

# ---------------------------------------------------------------
# Run
# ---------------------------------------------------------------
if st.sidebar.button("Run Scanner"):
    t0 = time.time()
    st.markdown(
        f'<div class="notice">Scanning <b>{len(tickers)}</b> stocks on the <b>{timeframe.lower()}</b> '
        f'timeframe. This can take a minute.</div>',
        unsafe_allow_html=True,
    )

    keias_buy_list, keias_sell_list = [], []
    kxkx_buy_list, kxkx_sell_list = [], []

    progress_bar = st.progress(0, text="Starting scan")
    completed_count = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_single_ticker, ticker, interval_val): ticker for ticker in tickers}

        for future in as_completed(futures):
            completed_count += 1
            progress_bar.progress(
                completed_count / len(tickers),
                text=f"Scanning {futures[future]} ({completed_count} of {len(tickers)})",
            )

            res = future.result()
            if res:
                if res["keias_buy"]:
                    keias_buy_list.append(res["ticker"])
                if res["keias_sell"]:
                    keias_sell_list.append(res["ticker"])
                if res["kxkx_buy"]:
                    kxkx_buy_list.append(res["ticker"])
                if res["kxkx_sell"]:
                    kxkx_sell_list.append(res["ticker"])

    progress_bar.empty()
    elapsed = time.time() - t0
    total_signals = len(keias_buy_list) + len(keias_sell_list) + len(kxkx_buy_list) + len(kxkx_sell_list)
    render_stats(total_signals, f"{elapsed:.0f}s")

    st.markdown(
        f'<div class="notice ok">Scan complete. Checked <b>{len(tickers)}</b> stocks.</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            panel("KEIAS Buy Signals", "Score crossed above 60", keias_buy_list, "up")
            + panel("KXKX Institutional Accumulation", "Heavy buying near the lows", kxkx_buy_list, "up"),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            panel("KEIAS Sell Signals", "Score crossed below -60", keias_sell_list, "down")
            + panel("KXKX Institutional Distribution", "Heavy selling near the highs", kxkx_sell_list, "down"),
            unsafe_allow_html=True,
        )

    rows = (
        [(t, "KEIAS Buy") for t in keias_buy_list]
        + [(t, "KEIAS Sell") for t in keias_sell_list]
        + [(t, "KXKX Accumulation") for t in kxkx_buy_list]
        + [(t, "KXKX Distribution") for t in kxkx_sell_list]
    )
    st.download_button(
        "Download signals (CSV)",
        pd.DataFrame(rows, columns=["Ticker", "Signal"]).to_csv(index=False),
        file_name=f"signals_{timeframe.lower()}.csv",
        mime="text/csv",
    )
else:
    st.markdown(
        '<div class="notice">Choose a universe and timeframe in the sidebar, then press <b>Run Scanner</b>. '
        'Results show up here as tappable ticker chips.</div>',
        unsafe_allow_html=True,
    )