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

html, body, .stApp, [class*="css"]{
  font-family:'Sora','PingFang SC','Noto Sans SC','Microsoft YaHei',sans-serif; color:var(--ink);
}
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
# Language (English / 中文)
# ---------------------------------------------------------------
T = {
    "en": {
        "hero_title": "US Stock Flow Scanner",
        "hero_sub": "Institutional flow and trend signals across large, liquid US stocks. "
                    "Tap any ticker to open it on Yahoo Finance.",
        "settings": "⚙️ Scan Settings",
        "universe": "Select Stock Universe",
        "modes": [
            "Auto scan US market (Market Cap > $1.6B, Float > 400M + Hot Liquids)",
            "Custom stock tickers",
        ],
        "custom": "Enter tickers (comma separated, e.g., AAPL, TSLA, NVDA)",
        "spinner": "Filtering stocks (Market Cap > $1.6B & Float > 400M + Hot Liquids)... Please wait...",
        "tf_label": "Scan Timeframe",
        "tf": {"Daily": "Daily", "Weekly": "Weekly"},
        "run": "Run Scanner",
        "s_universe": "Stocks in universe",
        "s_tf": "Timeframe",
        "s_found": "Signals found",
        "s_time": "Scan time",
        "scanning": "Scanning <b>{n}</b> stocks on the <b>{tf}</b> timeframe. This can take a minute.",
        "start": "Starting scan",
        "progress": "Scanning {t} ({i} of {n})",
        "done": "Scan complete. Checked <b>{n}</b> stocks.",
        "keias_buy": "KEIAS Buy Signals", "keias_buy_sub": "Score crossed above 60",
        "kxkx_buy": "KXKX Institutional Accumulation", "kxkx_buy_sub": "Heavy buying near the lows",
        "keias_sell": "KEIAS Sell Signals", "keias_sell_sub": "Score crossed below -60",
        "kxkx_sell": "KXKX Institutional Distribution", "kxkx_sell_sub": "Heavy selling near the highs",
        "empty": "No matches in this scan",
        "download": "Download signals (CSV)",
        "idle": "Choose a universe and timeframe in the sidebar, then press <b>Run Scanner</b>. "
                "Results show up here as tappable ticker chips.",
    },
    "zh": {
        "hero_title": "美股资金流向扫描器",
        "hero_sub": "在大市值、高流动性的美股中扫描机构资金流向与趋势信号。点击任意代码即可在 Yahoo Finance 打开。",
        "settings": "⚙️ 扫描设置",
        "universe": "选择股票范围",
        "modes": [
            "自动扫描美股（市值 > 16 亿美元，流通股 > 4 亿 + 热门高流动性股票）",
            "自定义股票代码",
        ],
        "custom": "输入股票代码（逗号分隔，例如 AAPL, TSLA, NVDA）",
        "spinner": "正在筛选股票（市值 > 16 亿美元，流通股 > 4 亿 + 热门高流动性股票）…请稍候…",
        "tf_label": "扫描周期",
        "tf": {"Daily": "日线", "Weekly": "周线"},
        "run": "开始扫描",
        "s_universe": "股票池数量",
        "s_tf": "周期",
        "s_found": "信号数量",
        "s_time": "扫描用时",
        "scanning": "正在扫描 <b>{n}</b> 只股票，周期：<b>{tf}</b>。可能需要一分钟。",
        "start": "开始扫描",
        "progress": "正在扫描 {t}（{i}/{n}）",
        "done": "扫描完成，共检查 <b>{n}</b> 只股票。",
        "keias_buy": "KEIAS 买入信号", "keias_buy_sub": "评分上穿 60",
        "kxkx_buy": "KXKX 机构吸筹", "kxkx_buy_sub": "低位放量买入",
        "keias_sell": "KEIAS 卖出信号", "keias_sell_sub": "评分下穿 -60",
        "kxkx_sell": "KXKX 机构派发", "kxkx_sell_sub": "高位放量卖出",
        "empty": "本次扫描没有符合条件的股票",
        "download": "下载信号 (CSV)",
        "idle": "在侧边栏选择股票范围和周期，然后点击 <b>开始扫描</b>。结果会以可点击的代码标签显示在这里。",
    },
}

lang = st.sidebar.radio("Language / 语言", ["English", "中文"], horizontal=True)
L = T["zh" if lang == "中文" else "en"]


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
        chips = f'<span class="empty">{L["empty"]}</span>'
    return (
        f'<div class="panel {kind}"><div class="panel-head"><span class="dot {kind}"></span>'
        f'<div><div class="panel-title">{title}</div><div class="panel-sub">{subtitle}</div></div>'
        f'<div class="count">{len(items)}</div></div><div class="chips">{chips}</div></div>'
    )


st.markdown(
    f'<div class="hero"><div class="hero-title">{L["hero_title"]}</div>'
    f'<div class="hero-sub">{L["hero_sub"]}</div></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------
st.sidebar.header(L["settings"])
scan_mode = st.sidebar.radio(L["universe"], L["modes"])

if scan_mode == L["modes"][1]:
    custom_tickers = st.sidebar.text_input(
        L["custom"],
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

    with st.spinner(L["spinner"]):
        tickers = get_filtered_us_universe()

timeframe = st.sidebar.selectbox(L["tf_label"], ["Daily", "Weekly"], format_func=lambda x: L["tf"][x])
interval_val = "1d" if timeframe == "Daily" else "1wk"


# ---------------------------------------------------------------
# Indicator logic (unchanged)
# ---------------------------------------------------------------
def process_single_ticker(ticker, interval_val):
    try:
        # Weekly needs more history (1y of weekly bars is only ~52, below the 60-bar minimum)
        period = "1y" if interval_val == "1d" else "5y"
        df = yf.download(ticker, period=period, interval=interval_val, progress=False)
        if df.empty or len(df) < 60:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']
        high = df['High']
        low = df['Low']
        vol = df['Volume']

        # --- KEIAS Indicator Logic ---
        win = 252 if interval_val == "1d" else 52  # 52 weeks either way
        ll52 = low.rolling(win).min() if len(df) >= win else low.min()
        hh52 = high.rolling(win).max() if len(df) >= win else high.max()
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
        + stat(L["s_universe"], len(tickers))
        + stat(L["s_tf"], L["tf"][timeframe])
        + stat(L["s_found"], found)
        + stat(L["s_time"], elapsed)
        + "</div>",
        unsafe_allow_html=True,
    )


render_stats()

# ---------------------------------------------------------------
# Run
# ---------------------------------------------------------------
if st.sidebar.button(L["run"]):
    t0 = time.time()
    st.markdown(
        f'<div class="notice">{L["scanning"].format(n=len(tickers), tf=L["tf"][timeframe].lower())}</div>',
        unsafe_allow_html=True,
    )

    keias_buy_list, keias_sell_list = [], []
    kxkx_buy_list, kxkx_sell_list = [], []

    progress_bar = st.progress(0, text=L["start"])
    completed_count = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_single_ticker, ticker, interval_val): ticker for ticker in tickers}

        for future in as_completed(futures):
            completed_count += 1
            progress_bar.progress(
                completed_count / len(tickers),
                text=L["progress"].format(t=futures[future], i=completed_count, n=len(tickers)),
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
        f'<div class="notice ok">{L["done"].format(n=len(tickers))}</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            panel(L["keias_buy"], L["keias_buy_sub"], keias_buy_list, "up")
            + panel(L["kxkx_buy"], L["kxkx_buy_sub"], kxkx_buy_list, "up"),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            panel(L["keias_sell"], L["keias_sell_sub"], keias_sell_list, "down")
            + panel(L["kxkx_sell"], L["kxkx_sell_sub"], kxkx_sell_list, "down"),
            unsafe_allow_html=True,
        )

    rows = (
        [(t, L["keias_buy"]) for t in keias_buy_list]
        + [(t, L["keias_sell"]) for t in keias_sell_list]
        + [(t, L["kxkx_buy"]) for t in kxkx_buy_list]
        + [(t, L["kxkx_sell"]) for t in kxkx_sell_list]
    )
    st.download_button(
        L["download"],
        pd.DataFrame(rows, columns=["Ticker", "Signal"]).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"signals_{timeframe.lower()}.csv",
        mime="text/csv",
    )
else:
    st.markdown(f'<div class="notice">{L["idle"]}</div>', unsafe_allow_html=True)