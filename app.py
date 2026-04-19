import streamlit as st
import yfinance as yf
import pandas as pd

# --- 2. LOGIQUE MÉTIER ---
def get_sector_per(sector):
    per_map = {
        "Technology": 25.0, "Healthcare": 18.0, "Consumer Defensive": 18.0,
        "Consumer Cyclical": 22.0, "Financial Services": 12.0, "Energy": 10.0,
        "Industrials": 16.0, "Utilities": 15.0, "Basic Materials": 14.0,
        "Communication Services": 20.0
    }
    return per_map.get(sector, 15.0)

# --- 3. STYLE CSS ---
st.markdown("""
    <style>
    .section-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 25px; }
    .badge-source { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; display: inline-block; margin-bottom: 5px; }
    .badge-yf { background-color: #7b1fa2; color: white; } 
    .badge-calc { background-color: #0288d1; color: white; } 
    .price-large { font-size: 52px; font-weight: 800; line-height: 1; margin: 10px 0; color: #1E1E1E; }
    .stat-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
    .stat-label { color: #888; text-transform: uppercase; font-size: 11px; font-weight: 600; }
    .stat-value { font-weight: bold; color: #333; text-align: right; }
    .decote-card { text-align: center; padding: 20px; border-radius: 10px; background: #fff; border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    
    .range-container { margin-top: 20px; }
    .range-labels { display: flex; justify-content: space-between; font-size: 11px; color: #888; margin-bottom: 4px; }
    .range-bar { height: 6px; background: linear-gradient(to right, #d98c8c, #f2c9c9); border-radius: 3px; position: relative; }
    .range-dot { position: absolute; height: 12px; width: 12px; background-color: #d9534f; border: 2px solid white; border-radius: 50%; top: -3px; transform: translateX(-50%); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_data(ticker_str):
    try:
        stock = yf.Ticker(ticker_str)
        info = stock.info
        cf = stock.cashflow
        price = info.get("currentPrice", 0.0)
        sh_out = info.get("sharesOutstanding", 1)
        
        # BNA
        t_eps = info.get("trailingEps", 1.0)
        f_eps = info.get("forwardEps", t_eps)
        g_bna_auto = ((f_eps / t_eps) - 1) * 100 if t_eps and t_eps > 0 else 5.0
        
        # FCF
        fcf_series = cf.loc["Free Cash Flow"] if "Free Cash Flow" in cf.index else pd.Series()
        v_fcf_curr = fcf_series.iloc[0] / sh_out if not fcf_series.empty else 0.0
        g_fcf_auto = (info.get("revenueGrowth", 0.05) * 100) if info.get("revenueGrowth") else 5.0
        p_fcf_target = (price / v_fcf_curr) if v_fcf_curr > 0 else 15.0
        
        # DIVIDENDE - CALCUL MANUEL SÉCURISÉ
        current_div = info.get("dividendRate", 0.0) or 0.0
        calc_yield = (current_div / price * 100) if price > 0 else 0.0
        g_div_auto = min(g_bna_auto, 10.0) if g_bna_auto > 0 else 5.0

        return {
            "name": info.get("longName", ticker_str),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "beta": info.get("beta", "N/A"),
            "price": price,
            "currency": info.get("currency", "EUR"),
            "eps_ttm": t_eps,
            "per_ttm": info.get("trailingPE", 0.0),
            "per_fwd": info.get("forwardPE", 0.0),
            "peg": info.get("pegRatio", "-"),
            "div_yield": calc_yield,
            "fcf_ps": v_fcf_curr,
            "g_fcf": g_fcf_auto,
            "p_fcf": p_fcf_target,
            "g_bna": g_bna_auto,
            "g_div": g_div_auto,
            "per_sector": get_sector_per(info.get("sector")),
            "div": current_div,
            "mcap": info.get("marketCap", 0),
            "low52": info.get("fiftyTwoWeekLow", 0.0),
            "high52": info.get("fiftyTwoWeekHigh", 0.0)
        }
    except: return None

# --- 4. INTERFACE ---
# Menu réduit pour les suffixes
with st.expander("ℹ️ Suffixe des tickers (Exemples : ETR:AOF, AMS:ASML...)"):
    st.markdown("""
        * **Paris :** `.PA` (ex: `AI.PA`, `TTE.PA`)
        * **Xetra (All) :** `.DE` (ex: `SAP.DE`, `2FE.DE`)
        * **Amsterdam :** `.AS` (ex: `ASML.AS`)
        * **USA :** Aucun suffixe (ex: `AAPL`, `MSFT`)
        * **Londres :** `.L` | **Milan :** `.MI` | **Madrid :** `.MC`
    """)

ticker = st.text_input("RECHERCHER UNE ACTION", "AI.PA").upper()
d = get_data(ticker)

if d:
    col_main, col_side = st.columns([2.8, 1.2], gap="large")
    ans = [2026, 2027, 2028, 2029, 2030]

    with col_main:
        st.title(f"🏢 {d['name']}")

        # --- MODÈLE BNA ---
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("📈 Modèle BNA (Bénéfices)")
        b1, b2, b3 = st.columns(3)
        v_bna = b1.number_input("BNA TTM", value=float(d['eps_ttm']))
        b1.markdown('<span class="badge-source badge-yf">Source: Yahoo Finance</span>', unsafe_allow_html=True)
        g_bna = b2.number_input("Croissance BNA %", value=float(d['g_bna']))
        b2.markdown('<span class="badge-source badge-yf">Source: Yahoo Forward</span>', unsafe_allow_html=True)
        p_c = b3.number_input(f"PER cible (Secteur: {d['per_sector']}x)", value=float(d['per_fwd'] if d['per_fwd'] > 0 else d['per_sector']))
        b3.markdown('<span class="badge-source badge-yf">Source: Yahoo Forward PE</span>', unsafe_allow_html=True)
        
        projs_bna = [v_bna * (1 + g_bna/100)**i * p_c for i in range(1, 6)]
        st.table(pd.DataFrame({"Année": ans, "PRIX (BNA)": projs_bna}).set_index("Année").T)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- MODÈLE FCF ---
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("💸 Modèle FCF (Cash-Flow)")
        f1, f2, f3 = st.columns(3)
        v_fcf = f1.number_input("FCF / action", value=float(d['fcf_ps']))
        f1.markdown('<span class="badge-source badge-calc">Source: Yahoo CashFlow</span>', unsafe_allow_html=True)
        g_fcf = f2.number_input("Croissance FCF %", value=float(d['g_fcf']))
        f2.markdown('<span class="badge-source badge-yf">Source: Yahoo Growth</span>', unsafe_allow_html=True)
        pf_c = f3.number_input("P/FCF cible", value=float(d['p_fcf']))
        f3.markdown('<span class="badge-source badge-yf">Source: Yahoo P/FCF</span>', unsafe_allow_html=True)
        
        projs_fcf = [v_fcf * (1 + g_fcf/100)**i * pf_c for i in range(1, 6)]
        st.table(pd.DataFrame({"Année": ans, "PRIX (FCF)": projs_fcf}).set_index("Année").T)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- MODÈLE DIVIDENDES ---
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("💰 Modèle Dividendes")
        d1, d2 = st.columns(2)
        v_div = d1.number_input("Dividende annuel", value=float(d['div']))
        d1.markdown('<span class="badge-source badge-yf">Source: Yahoo Finance</span>', unsafe_allow_html=True)
        g_div = d2.number_input("Croissance Div. %", value=float(d['g_div']))
        d2.markdown('<span class="badge-source badge-calc">Source: Est. Croissance</span>', unsafe_allow_html=True)
        
        projs_div = [v_div * (1 + g_div/100)**i for i in range(1, 6)]
        yoc = [(v / d['price']) * 100 if d['price'] > 0 else 0 for v in projs_div]
        st.table(pd.DataFrame({"Année": ans, "DIV. ESTIMÉ": projs_div, "YIELD ON COST (%)": yoc}).set_index("Année").T)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- SYNTHÈSE ---
        st.divider()
        st.subheader("🎯 Juste Prix d'achat (Actualisé 10%)")
        va = ((projs_bna[0] + projs_fcf[0]) / 2) / 1.10
        c_res = st.columns(3)
        for i, m in enumerate([0.10, 0.20, 0.30]):
            pf = va * (1 - m)
            color = "#28a745" if d['price'] < pf else "#dc3545"
            with c_res[i]:
                st.markdown(f'<div class="decote-card" style="border-top: 5px solid {color}"><div class="stat-label">Décote {int(m*100)}%</div><div style="font-size:22px; font-weight:bold; color:{color};">{pf:.2f} {d["currency"]}</div></div>', unsafe_allow_html=True)

    with col_side:
        st.markdown(f"<b>{d['name']}</b>", unsafe_allow_html=True)
        st.markdown(f"<div class='price-large'>{d['price']:.2f}</div>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#888; font-size:12px;'>{d['currency']} · {ticker}</span>", unsafe_allow_html=True)
        st.write("---")
        def s_row(l, v): st.markdown(f"<div class='stat-row'><span class='stat-label'>{l}</span><span class='stat-value'>{v}</span></div>", unsafe_allow_html=True)
        
        s_row("CAPITALISATION", f"{d['mcap']/1e9:.2f} Md")
        s_row("SECTEUR", d['sector'])
        s_row("INDUSTRIE", d['industry'])
        
        st.write("") 
        s_row("PER (TTM)", f"{d['per_ttm']:.2f}x")
        s_row("PER (FWD)", f"{d['per_fwd']:.2f}x")
        s_row("RDT DIVIDENDE", f"{d['div_yield']:.2f} %")
        s_row("PEG", f"{d['peg']}")
        
        pos = ((d['price'] - d['low52']) / (d['high52'] - d['low52'])) * 100 if d['high52'] > d['low52'] else 50
        st.markdown(f"""
            <div class="range-container">
                <div class="range-labels"><span>{d['low52']:.2f}</span><b>PLAGE 52 SEMAINES</b><span>{d['high52']:.2f}</span></div>
                <div class="range-bar"><div class="range-dot" style="left:{max(0, min(100, pos))}%;"></div></div>
            </div>
        """, unsafe_allow_html=True)

else:
    st.error("Données Yahoo introuvables. Vérifiez le symbole saisi.")
