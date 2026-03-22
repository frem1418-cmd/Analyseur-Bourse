import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. CONFIGURATION & SÉCURITÉ ---
st.set_page_config(page_title="Analyseur Bourse Privé", layout="wide")

# Définis ton mot de passe ici
PASSWORD_CIBLE = "Plha649" 

def check_password():
    """Retourne True si l'utilisateur a saisi le bon mot de passe."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Affichage du formulaire de login
    st.title("🔒 Accès Restreint")
    pwd = st.text_input("Veuillez saisir le code d'accès :", type="password")
    if st.button("Se connecter"):
        if pwd == PASSWORD_CIBLE:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Mot de passe incorrect.")
    return False

# Si le mot de passe n'est pas bon, on arrête l'exécution ici
if not check_password():
    st.stop()

# --- 2. STYLE CSS ---
st.markdown("""
    <style>
    .section-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 25px; }
    .badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 8px; vertical-align: middle; display: inline-block; }
    .badge-yf { background-color: #e2f0d9; color: #385723; }
    .badge-calc { background-color: #deebf7; color: #2f5597; }
    .badge-manual { background-color: #fff2cc; color: #bf9000; }
    .price-large { font-size: 52px; font-weight: 800; line-height: 1; margin: 10px 0; color: #1E1E1E; }
    .stat-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
    .stat-label { color: #888; text-transform: uppercase; font-size: 11px; font-weight: 600; }
    .ticker-tag { background-color: #f4cccc; color: #a61c00; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; display: inline-block; margin-bottom: 10px; }
    .decote-card { text-align: center; padding: 20px; border-radius: 10px; background: #fff; border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .legend-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff; margin-bottom: 20px; font-size: 13px; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÉGENDE & LOGIQUE ---
with st.expander("📍 Guide des Tickers (Extensions Marchés)"):
    st.markdown("""
    <div class="legend-box">
    <b>Ajoutez l'extension selon la place boursière :</b><br>
    • <b>.PA</b> : Paris | • <b>.AS</b> : Amsterdam | • <b>.DE</b> : Allemagne | • <b>.MC</b> : Madrid | • <b>.MI</b> : Milan<br>
    • <b>Sans extension</b> : USA (ex: AAPL, NVDA)
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_data(ticker_str):
    try:
        stock = yf.Ticker(ticker_str)
        info = stock.info
        cf = stock.cashflow
        price = info.get("currentPrice", 0.0)
        sh_out = info.get("sharesOutstanding", 1)
        
        g_bna_auto = (info.get("earningsGrowth", 0.05) or 0.05) * 100
        
        fcf_series = cf.loc["Free Cash Flow"] if "Free Cash Flow" in cf.index else pd.Series()
        v_fcf_curr = fcf_series.iloc[0] / sh_out if not fcf_series.empty else price / 20
        g_fcf_auto = 5.0
        if len(fcf_series) >= 3 and fcf_series.iloc[2] != 0:
            g_fcf_auto = ((fcf_series.iloc[0] / fcf_series.iloc[2])**(1/2) - 1) * 100

        return {
            "name": info.get("longName", ticker_str),
            "price": price,
            "currency": info.get("currency", "EUR"),
            "eps": info.get("trailingEps", 1.0) if (info.get("trailingEps") and info.get("trailingEps") > 0) else 1.0,
            "per": info.get("trailingPE", 15.0),
            "fcf_ps": v_fcf_curr,
            "g_bna": g_bna_auto,
            "g_fcf": g_fcf_auto,
            "pfcf_target": price / v_fcf_curr if v_fcf_curr > 0 else 20.0,
            "div": info.get("dividendRate", 0.0),
            "mcap": info.get("marketCap", 0),
            "low52": info.get("fiftyTwoWeekLow", 0),
            "high52": info.get("fiftyTwoWeekHigh", 0)
        }
    except: return None

# --- 4. INTERFACE ---
ticker = st.text_input("Saisir le Ticker", "AI.PA").upper()
d = get_data(ticker)

if d:
    col_main, col_side = st.columns([2.8, 1.2], gap="large")
    ans = [2026, 2027, 2028, 2029, 2030]

    with col_main:
        st.title(f"🏢 {d['name']}")

        # MODÈLE BNA
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("📈 Modèle BNA")
        b1, b2, b3 = st.columns(3)
        v_bna = b1.number_input("BNA TTM", value=float(d['eps']))
        b1.markdown("<span class='badge badge-yf'>yfinance</span>", unsafe_allow_html=True)
        g_bna = b2.number_input("Croissance BNA %", value=float(d['g_bna']))
        b2.markdown("<span class='badge badge-yf'>analystes</span>", unsafe_allow_html=True)
        p_c = b3.number_input("PER cible", value=float(d['per']))
        b3.markdown("<span class='badge badge-yf'>actuel</span>", unsafe_allow_html=True)
        projs_bna = [v_bna * (1 + g_bna/100)**i * p_c for i in range(1, 6)]
        st.table(pd.DataFrame({"Année": ans, "PRIX (BNA)": projs_bna}).set_index("Année").T)
        st.markdown('</div>', unsafe_allow_html=True)

        # MODÈLE FCF
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("💸 Modèle FCF")
        f1, f2, f3 = st.columns(3)
        v_fcf = f1.number_input("FCF / action", value=float(d['fcf_ps']))
        f1.markdown("<span class='badge badge-calc'>T.T.M.</span>", unsafe_allow_html=True)
        g_fcf = f2.number_input("Croissance FCF %", value=float(d['g_fcf']))
        f2.markdown("<span class='badge badge-calc'>CAGR 3 ans</span>", unsafe_allow_html=True)
        pf_c = f3.number_input("P/FCF cible", value=float(d['pfcf_target']))
        f3.markdown("<span class='badge badge-calc'>actuel</span>", unsafe_allow_html=True)
        projs_fcf = [v_fcf * (1 + g_fcf/100)**i * pf_c for i in range(1, 6)]
        st.table(pd.DataFrame({"Année": ans, "PRIX (FCF)": projs_fcf}).set_index("Année").T)
        st.markdown('</div>', unsafe_allow_html=True)

        # MODÈLE DIVIDENDES
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("💰 Modèle Dividendes")
        d1, d2 = st.columns(2)
        v_div = d1.number_input("Dividende annuel", value=float(d['div']))
        d1.markdown("<span class='badge badge-yf'>yfinance</span>", unsafe_allow_html=True)
        g_div = d2.number_input("Croissance Div. %", value=7.0)
        d2.markdown("<span class='badge badge-manual'>manuel</span>", unsafe_allow_html=True)
        projs_div = [v_div * (1 + g_div/100)**i for i in range(1, 6)]
        yoc = [(v / d['price']) * 100 if d['price'] > 0 else 0 for v in projs_div]
        st.table(pd.DataFrame({"Année": ans, "DIV. ESTIMÉ": projs_div, "YIELD ON COST (%)": yoc}).set_index("Année").T)
        st.markdown('</div>', unsafe_allow_html=True)

        # SYNTHÈSE
        st.write("---")
        st.subheader("🎯 Juste Prix d'achat (Actualisé 10%)")
        va = ((projs_bna[0] + projs_fcf[0]) / 2) / 1.10
        c_res = st.columns(3)
        for i, m in enumerate([0.10, 0.12, 0.15]):
            pf = va * (1 - m)
            color = "#28a745" if d['price'] < pf else "#dc3545"
            with c_res[i]:
                st.markdown(f'<div class="decote-card" style="border-top: 5px solid {color}"><div class="stat-label">Décote {int(m*100)}%</div><div style="font-size:22px; font-weight:bold; color:{color};">{pf:.2f} {d['currency']}</div></div>', unsafe_allow_html=True)

    with col_side:
        st.markdown(f"<span class='ticker-tag'>{ticker}</span>", unsafe_allow_html=True)
        st.markdown(f"<div class='price-large'>{d['price']:.2f}</div>", unsafe_allow_html=True)
        st.write("---")
        def s_row(l, v): st.markdown(f"<div class='stat-row'><span class='stat-label'>{l}</span><b>{v}</b></div>", unsafe_allow_html=True)
        s_row("CAPITALISATION", f"{d['mcap']/1e9:.2f} Md")
        s_row("RENDEMENT", f"{(d['div']/d['price'])*100:.2f} %" if d['price'] > 0 else "0 %")
        st.write("---")
        st.slider("Range 52W", float(d['low52']), float(d['high52']), float(d['price']), disabled=True)
