import streamlit as st
import pandas as pd
import numpy as np
import io
from pathlib import Path

st.set_page_config(
    page_title="Hospice Target Screener | Willowbridge Capital",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Dark Mode Styling ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #0c0f18 !important; color: #e2e8f0 !important;
  }
  [data-testid="stSidebar"] { background: #0a0d14 !important; border-right: 1px solid #1e293b !important; }
  [data-testid="stHeader"] { background: transparent !important; }
  section[data-testid="stSidebar"] { display: none; }

  h1,h2,h3,h4 { color: #f1f5f9 !important; }
  p, li { color: #94a3b8 !important; }

  /* Inputs */
  [data-testid="stTextInput"] input {
    background: #111827 !important; border: 1px solid #1e293b !important;
    color: #e2e8f0 !important; border-radius: 6px !important;
  }
  [data-baseweb="select"] > div {
    background: #111827 !important; border: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
  }
  [data-baseweb="popover"] { background: #111827 !important; border: 1px solid #1e293b !important; }
  [role="listbox"] { background: #111827 !important; }
  [role="option"] { color: #e2e8f0 !important; }
  [role="option"]:hover { background: #1e293b !important; }
  [data-baseweb="tag"] { background: #1e3a5f !important; color: #93c5fd !important; }

  /* Metrics */
  [data-testid="metric-container"] {
    background: #0f1520 !important; border: 1px solid #1e293b !important;
    border-radius: 8px !important; padding: 12px 16px !important;
  }
  [data-testid="stMetricLabel"] p { color: #475569 !important; font-size: 11px !important; }
  [data-testid="stMetricValue"] { color: #f1f5f9 !important; }

  /* Download button */
  [data-testid="stDownloadButton"] button {
    background: #1e3a5f !important; border: 1px solid #2563eb !important;
    color: #93c5fd !important; border-radius: 6px !important; font-size: 12px !important;
  }

  /* Expander */
  [data-testid="stExpander"] {
    background: #0f1520 !important; border: 1px solid #1e293b !important;
    border-radius: 8px !important;
  }
  [data-testid="stExpander"] summary p { color: #94a3b8 !important; }
  details summary:hover { background: #111827 !important; }

  /* Dataframe */
  [data-testid="stDataFrame"] { border: 1px solid #1e293b !important; border-radius: 8px !important; }
  .dvn-scroller { background: #0f1520 !important; }

  /* File uploader */
  [data-testid="stFileUploaderDropzone"] {
    background: #0f1520 !important; border: 1px dashed #1e3a5f !important;
  }

  /* Toggle */
  [data-testid="stToggle"] p { color: #94a3b8 !important; }

  /* Selectbox dark override — fixes grey text on white */
  div[data-baseweb="select"] span,
  div[data-baseweb="select"] div,
  [data-testid="stSelectbox"] span,
  [data-testid="stSelectbox"] label {
    color: #e2e8f0 !important;
    background-color: transparent !important;
  }
  div[data-baseweb="select"] > div {
    background-color: #111827 !important;
    border-color: #1e293b !important;
  }
  ul[role="listbox"] li {
    background-color: #111827 !important;
    color: #e2e8f0 !important;
  }
  ul[role="listbox"] li:hover,
  ul[role="listbox"] li[aria-selected="true"] {
    background-color: #1e293b !important;
  }

  /* Caption */
  [data-testid="stCaptionContainer"] p { color: #374151 !important; font-size: 10px !important; }

  hr { border-color: #1e293b !important; margin: 12px 0 !important; }

  /* Custom */
  .sig-row { display:flex;align-items:flex-start;gap:10px;margin-bottom:5px;padding:7px 12px;background:#111827;border-radius:5px; }
  .info-card { background:#111827;border:1px solid #1e293b;border-radius:6px;padding:10px 12px;margin-bottom:6px; }
  .info-label { font-size:9px;letter-spacing:1px;color:#475569;text-transform:uppercase;margin-bottom:3px; }
  .info-value { font-size:13px;color:#e2e8f0; }
  .warn-banner { background:#2d1a00;border:1px solid #f59e0b;border-radius:8px;padding:12px 16px;margin-bottom:12px; }
  .filter-row { background:#0a0d14;border:1px solid #1e293b;border-radius:8px;padding:16px 20px;margin-bottom:16px; }
  .score-table th { text-align:left;padding:8px 12px;color:#475569;font-size:10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #1e293b; }
  .score-table td { padding:8px 12px;border-bottom:1px solid #0f172a;font-size:12px; }
  .score-table tr:nth-child(even) td { background:#111827; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
TARGET_STATES = ["ID","UT","NV","MT","WY","CO","AZ","TX","OK"]

KNOWN_CHAIN_PATTERNS = [
    "lhc group","lhc","enhabit","amedisys","vitas","compassus","interim healthcare",
    "gentiva","accentcare","bright spring","brightspring","elara caring","elara",
    "agia","agape","aveanna","bayada","kindred","kindred at home","curo",
    "crossroads hospice","crossroads","journey hospice","journey care",
    "seasons hospice","seasons","faith hospice","promise","promise healthcare",
    "national hospice","american hospice","guardian hospice","guardian angel",
    "suncrest","suncoast","sunridge","sun hospice",
    "care advantage","care partners","caremore","carepartners",
    "intrepid","landmark","optum","united hospice","united health",
    "harbor hospice","harbor light","harbor grace",
    "mountain valley","mountain west hospice","mountain hospice",
    "continuum","continuum hospice","continuum care",
    "sage hospice","sage health","sage care",
    "hallmark hospice","hallmark care","hallmark health",
    "solaris","solara","solace","solace hospice","solace health",
    "riverview hospice","river valley hospice","riverstone",
    "steward","steward hospice","steward health",
    "community hospice","community care partners",
    "clearwater hospice","clearwater care",
    "pathways hospice","pathways health","pathways care",
    "transitions hospice","transitions care","transitions health",
    "premier hospice","premier care","premiere hospice",
    "aspire hospice","aspire health","aspiration",
    "alliance hospice","alliance health","allied hospice",
    "legacy hospice","legacy health","legacy care",
    "evercare","ever care","evergreen hospice","evergreen health",
    "agrace","agrace hospice","profound","profound hospice","profound health",
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def normalize_cols(df):
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(r'\s+','_',regex=True)
                  .str.replace(r'[()]','',regex=True))
    return df

def get_ccn(row):
    for col in ["cms_certification_number_ccn","ccn","cms_certification_number",
                "prvdr_id","provider_id","prvdr_num","facility_id","certification_number"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            val = str(row[col]).strip()
            try: return str(int(val)).zfill(6)
            except: return val
    return ""

def detect_chain(name):
    if not name: return None
    lower = str(name).lower()
    for p in KNOWN_CHAIN_PATTERNS:
        if p in lower: return p
    return None

def load_csv(file_or_path):
    if isinstance(file_or_path,(str,Path)):
        with open(file_or_path,'r',encoding='utf-8-sig') as f: content = f.read()
    else:
        content = file_or_path.read().decode('utf-8-sig')
    delim = '\t' if '\t' in content.split('\n')[0] else ','
    df = pd.read_csv(io.StringIO(content), sep=delim, dtype=str, on_bad_lines='skip')
    return normalize_cols(df)

def score_target(gen_row, prov_row, puf_row, cahps_row):
    score = 25; signals = []; ownership_flag = None

    # Independence
    chain_src = prov_row if prov_row is not None else gen_row
    chain_val = ""
    for col in ["affiliated_with_a_hospice_chain","affiliated_with_chain","chain_owned","chain"]:
        if col in chain_src.index and pd.notna(chain_src[col]):
            chain_val = str(chain_src[col]).lower().strip(); break
    cms_independent = chain_val in ("","no","n","nan")
    if cms_independent:
        score += 30; signals.append({"label":"Independent operator — likely founder-owned","type":"positive","weight":30})
    else:
        score -= 20; signals.append({"label":"Chain-affiliated — harder negotiation","type":"negative","weight":-20})

    # Cert Age
    cert_str = str(gen_row.get("certification_date",""))
    if cert_str and cert_str != "nan":
        try:
            parts = cert_str.split("/")
            year = int(parts[2]) if len(parts)==3 else int(parts[0])
            if year<=2005:   score+=25; signals.append({"label":f"Established {year} — 20+ yr referral roots","type":"positive","weight":25})
            elif year<=2010: score+=20; signals.append({"label":f"Established {year} — deep market presence","type":"positive","weight":20})
            elif year<=2015: score+=14; signals.append({"label":f"Certified {year} — mature operation","type":"positive","weight":14})
            elif year<=2019: score+=8;  signals.append({"label":f"Certified {year}","type":"neutral","weight":8})
            else:            score+=3;  signals.append({"label":f"Newer provider ({year}) — limited track record","type":"neutral","weight":3})
        except: pass

    # Stars
    stars_src = prov_row if prov_row is not None else gen_row
    stars = 0
    for col in ["overall_rating","overall_star_rating","hospice_overall_rating"]:
        if col in stars_src.index and pd.notna(stars_src[col]):
            try: stars = float(stars_src[col]); break
            except: pass
    if 1<=stars<=2:  score+=25; signals.append({"label":f"Low stars ({stars}★) — distress, motivated seller","type":"hot","weight":25})
    elif stars==3:   score+=10; signals.append({"label":"Average rating (3★) — improvement upside","type":"neutral","weight":10})
    elif stars>=4:   score+=15; signals.append({"label":f"High quality ({stars}★) — premium asset","type":"positive","weight":15})
    else:            score+=12; signals.append({"label":"No star rating — likely small/below survey threshold","type":"neutral","weight":12})

    # HCI
    hci = 0
    src = prov_row if prov_row is not None else gen_row
    for col in ["hospice_care_index_score","hci_score","hospice_care_index"]:
        if col in src.index and pd.notna(src[col]):
            try: hci = float(src[col]); break
            except: pass
    if 1<=hci<6:   score+=20; signals.append({"label":f"Low HCI ({hci}/10) — operational challenges","type":"hot","weight":20})
    elif 6<=hci<8: score+=8;  signals.append({"label":f"Average HCI ({hci}/10)","type":"neutral","weight":8})
    elif hci>=8:   score+=5;  signals.append({"label":f"Strong HCI ({hci}/10)","type":"positive","weight":5})
    else:          score+=10; signals.append({"label":"No HCI score — likely small/new","type":"neutral","weight":10})

    # ADC
    adc=0; revenue=0; benes=0
    if puf_row is not None:
        try: benes=int(float(str(puf_row.get("bene_dstnct_cnt",0) or 0)))
        except: pass
        try:
            sd=int(float(str(puf_row.get("tot_srvc_days",0) or 0)))
            adc=round(sd/365,1)
        except: pass
        try:
            ps=str(puf_row.get("tot_mdcr_pymt_amt","0") or "0").replace("$","").replace(",","")
            revenue=float(ps)
        except: pass
        av=adc or benes
        if 10<=av<=50:    score+=15; signals.append({"label":f"Est. ADC ~{av} — in target range (10–50)","type":"positive","weight":15})
        elif 50<av<=80:   score+=8;  signals.append({"label":f"Est. ADC ~{av} — slightly above target","type":"neutral","weight":8})
        elif av>80:       score+=3;  signals.append({"label":f"Est. ADC ~{av} — larger operator","type":"neutral","weight":3})
        elif av>0:        score+=10; signals.append({"label":f"Est. ADC ~{av} — very small","type":"neutral","weight":10})

    # CAHPS
    cahps_rating=None
    if cahps_row is not None:
        for col in ["rating_of_this_hospice_summary_score","overall_rating_of_hospice","cahps_overall_rating"]:
            if col in cahps_row.index and pd.notna(cahps_row[col]):
                try: cahps_rating=float(cahps_row[col]); break
                except: pass
        if cahps_rating:
            if cahps_rating<70:   score+=15; signals.append({"label":f"Low CAHPS ({cahps_rating}%) — family dissatisfaction","type":"hot","weight":15})
            elif cahps_rating<85: score+=6;  signals.append({"label":f"Average CAHPS ({cahps_rating}%)","type":"neutral","weight":6})
            else:                 score+=10; signals.append({"label":f"Strong CAHPS ({cahps_rating}%)","type":"positive","weight":10})

    return score, signals, adc, benes, revenue, cahps_rating, ownership_flag

def score_label(s):
    if s>=70: return "🔥 HOT"
    if s>=45: return "🌤 WARM"
    return "❄️ COLD"

def score_color(s):
    if s>=70: return "#22c55e"
    if s>=45: return "#f59e0b"
    return "#475569"

@st.cache_data(show_spinner=False)
def load_defaults():
    base = Path(__file__).parent/"data"
    gen = load_csv(base/"general.csv") if (base/"general.csv").exists() else None
    puf = load_csv(base/"puf.csv")     if (base/"puf.csv").exists()     else None
    return gen, puf

def build_targets(df_gen, df_puf=None, df_prov=None, df_cahps=None, for_profit_only=True, selected_states=None):
    if selected_states is None: selected_states=TARGET_STATES
    puf_idx={}; prov_idx={}; cahps_idx={}
    if df_puf is not None:
        df_p = df_puf[df_puf["smry_ctgry"].str.upper().str.strip()=="PROVIDER"] if "smry_ctgry" in df_puf.columns else df_puf
        for _,r in df_p.iterrows():
            c=get_ccn(r)
            if c: puf_idx[c]=r
    if df_prov is not None:
        for _,r in df_prov.iterrows():
            c=get_ccn(r)
            if c: prov_idx[c]=r
    if df_cahps is not None:
        for _,r in df_cahps.iterrows():
            c=get_ccn(r)
            if c: cahps_idx[c]=r

    state_col=next((c for c in ["state","state_code","provider_state"] if c in df_gen.columns),None)
    own_col  =next((c for c in ["ownership_type","type_of_ownership"]  if c in df_gen.columns),None)
    results=[]
    for _,row in df_gen.iterrows():
        state=str(row.get(state_col,"")).strip().upper() if state_col else ""
        if state not in selected_states: continue
        if for_profit_only and own_col:
            own=str(row.get(own_col,"")).lower()
            if not("for-profit" in own or "for profit" in own or "proprietary" in own): continue
        ccn=get_ccn(row)
        puf_r=puf_idx.get(ccn); prov_r=prov_idx.get(ccn); cahps_r=cahps_idx.get(ccn)
        score,signals,adc,benes,revenue,cahps_rating,ownership_flag = score_target(row,prov_r,puf_r,cahps_r)

        name_col  =next((c for c in ["facility_name","provider_name","organization_name"] if c in row.index),None)
        city_col  =next((c for c in ["city/town","city_town","city","provider_city"]      if c in row.index),None)
        cert_col  =next((c for c in ["certification_date","date_of_certification"]        if c in row.index),None)
        phone_col =next((c for c in ["telephone_number","phone"]                          if c in row.index),None)
        ss=prov_r if prov_r is not None else row
        hs=prov_r if prov_r is not None else row
        cs=prov_r if prov_r is not None else row
        stars_col =next((c for c in ["overall_rating","overall_star_rating","hospice_overall_rating"]     if c in ss.index),None)
        hci_col   =next((c for c in ["hospice_care_index_score","hci_score","hospice_care_index"]         if c in hs.index),None)
        chain_col =next((c for c in ["affiliated_with_a_hospice_chain","affiliated_with_chain","chain_owned","chain"] if c in cs.index),None)

        cert_str=str(row.get(cert_col,"")) if cert_col else ""
        cert_year=""
        if cert_str and cert_str!="nan":
            try:
                pts=cert_str.split("/"); cert_year=pts[2] if len(pts)==3 else pts[0]
            except: pass

        chain_val=str(cs.get(chain_col,"")) if chain_col else ""
        is_indep=chain_val.lower().strip() in ("","no","n","nan")
        indep_display="✓ Yes" if is_indep else "✗ Chain"

        results.append({
            "Name":              str(row.get(name_col,"Unknown")) if name_col else "Unknown",
            "CCN":               ccn,
            "State":             state,
            "City":              str(row.get(city_col,"")) if city_col else "",
            "Phone":             str(row.get(phone_col,"")) if phone_col else "",
            "Ownership Type":    str(row.get(own_col,"")) if own_col else "",
            "Independent":       indep_display,
            "Cert Year":         cert_year,
            "Stars":             str(ss.get(stars_col,"—")) if stars_col else "—",
            "HCI":               str(hs.get(hci_col,"—")) if hci_col else "—",
            "Est ADC":           adc if adc else (benes if benes else None),
            "Est Revenue ($k)":  round(revenue/1000) if revenue else None,
            "CAHPS %":           cahps_rating,
            "Score":             score,
            "Tier":              score_label(score),
            "Signals":           signals,
            "Has PUF":           puf_r is not None,
            "Has CAHPS":         cahps_r is not None,
        })

    return pd.DataFrame(results).sort_values("Score",ascending=False).reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div style="border-bottom:1px solid #1e293b;padding-bottom:16px;margin-bottom:20px">
  <div style="font-size:10px;letter-spacing:3px;color:#475569;text-transform:uppercase">Willowbridge Capital · Deal Sourcing</div>
  <div style="font-size:26px;font-weight:700;color:#f8fafc;margin-top:4px">Hospice Target Screener</div>
  <div style="font-size:12px;color:#475569;margin-top:3px">CMS data · scored 0–125 · ID · UT · NV · MT · WY · CO · AZ · TX · OK</div>
</div>
""", unsafe_allow_html=True)

# Load defaults
with st.spinner("Loading CMS data..."):
    df_gen_default, df_puf_default = load_defaults()

# ── Filter Bar ─────────────────────────────────────────────────────────────────
st.markdown('<div class="filter-row">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([2.5, 2, 1.8, 1])

with fc1:
    search = st.text_input("🔍 Search provider or city", "", placeholder="e.g. Boise, Heart n Home...")
with fc2:
    selected_states = st.multiselect(
        "States", options=TARGET_STATES, default=TARGET_STATES, placeholder="Select states..."
    )
with fc3:
    score_filter = st.selectbox("Minimum tier", ["All tiers","🌤 WARM and above (45+)","🔥 HOT only (70+)"])
with fc4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    for_profit_only = st.toggle("For-profit only", value=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Data file uploads ──────────────────────────────────────────────────────────
with st.expander("📂  Update CMS Data Files  ·  *default: Feb 2026 — upload newer files here*", expanded=False):
    uc1,uc2,uc3,uc4 = st.columns(4)
    with uc1:
        up_general = st.file_uploader("General Information *(required)*", type="csv", key="up_gen")
        st.caption("data.cms.gov → Hospice - General Information")
    with uc2:
        up_prov = st.file_uploader("Provider Information", type="csv", key="up_prov")
        st.caption("Stars, HCI score, chain affiliation")
    with uc3:
        up_puf = st.file_uploader("PAC PUF *(utilization)*", type="csv", key="up_puf")
        st.caption("catalog.data.gov → Medicare PAC PUF Hospice")
    with uc4:
        up_cahps = st.file_uploader("CAHPS Survey", type="csv", key="up_cahps")
        st.caption("Family satisfaction — larger providers only")

# Resolve sources
df_gen   = load_csv(up_general) if up_general else df_gen_default
df_puf   = load_csv(up_puf)     if up_puf     else df_puf_default
df_prov  = load_csv(up_prov)    if up_prov    else None
df_cahps = load_csv(up_cahps)   if up_cahps   else None

if df_gen is None:
    st.error("No General Information file found. Upload one above.")
    st.stop()
if not selected_states:
    st.warning("Select at least one state to continue.")
    st.stop()

# Build
with st.spinner("Scoring providers..."):
    df_all = build_targets(df_gen, df_puf, df_prov, df_cahps,
                           for_profit_only=for_profit_only,
                           selected_states=selected_states)

# Apply UI filters
df = df_all.copy()
if score_filter == "🔥 HOT only (70+)":        df = df[df["Score"] >= 70]
elif score_filter == "🌤 WARM and above (45+)": df = df[df["Score"] >= 45]
if search:
    df = df[df["Name"].str.contains(search,case=False,na=False) |
            df["City"].str.contains(search,case=False,na=False)]

# ── KPI Cards ──────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5 = st.columns(5)
with k1: st.metric("Total Providers", len(df))
with k2: st.metric("🔥 HOT (70+)", len(df[df["Score"]>=70]))
with k3: st.metric("🌤 WARM (45–69)", len(df[(df["Score"]>=45)&(df["Score"]<70)]))
with k4: st.metric("Chain-Affiliated", int((df["Independent"]=="✗ Chain").sum()))
with k5: st.metric("Has Census Data", int(df["Has PUF"].sum()))

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# Export
ec1,ec2 = st.columns([9,1])
with ec2:
    export_df = df.drop(columns=["Signals","Has PUF","Has CAHPS"],errors="ignore")
    st.download_button("⬇ Export CSV", export_df.to_csv(index=False).encode(),
                       "hospice_targets.csv","text/csv",use_container_width=True)
with ec1:
    st.markdown(f"<div style='color:#475569;font-size:12px;padding-top:8px'>{len(df)} providers · sorted by score descending</div>",unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = None

# ── Main Table ─────────────────────────────────────────────────────────────────
def render_table(df_display):
    def score_bar(s):
        pct = min(s / 125 * 100, 100)
        c = "#22c55e" if s >= 70 else "#f59e0b" if s >= 45 else "#475569"
        return (f'<div style="display:flex;align-items:center;gap:6px">'
                f'<div style="flex:1;background:#1e293b;border-radius:3px;height:6px">'
                f'<div style="width:{pct}%;background:{c};height:6px;border-radius:3px"></div></div>'
                f'<span style="color:{c};font-weight:700;font-size:12px;min-width:24px">{s}</span></div>')

    def indep_badge(v):
        if "Yes" in str(v):
            return '<span style="color:#22c55e;font-weight:700">✓ Yes</span>'
        return '<span style="color:#ef4444;font-weight:700">✗ Chain</span>'

    def tier_badge(v):
        if "HOT" in str(v):  return f'<span style="background:#14532d33;border:1px solid #22c55e;color:#22c55e;border-radius:20px;padding:2px 8px;font-size:11px;font-weight:700">{v}</span>'
        if "WARM" in str(v): return f'<span style="background:#78350f33;border:1px solid #f59e0b;color:#f59e0b;border-radius:20px;padding:2px 8px;font-size:11px;font-weight:700">{v}</span>'
        return f'<span style="background:#1e293b;border:1px solid #374151;color:#475569;border-radius:20px;padding:2px 8px;font-size:11px">{v}</span>'

    th = "padding:8px 12px;text-align:left;color:#475569;font-size:10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #1e293b;white-space:nowrap;background:#0a0d14"
    headers = ["Provider","State","City","Ownership","Indep?","Est.","Stars","HCI","ADC","Score","Tier"]
    header_html = "".join(f"<th style='{th}'>{h}</th>" for h in headers)

    rows_html = ""
    for i, (_, r) in enumerate(df_display.iterrows()):
        bg = "#0f1520" if i % 2 == 0 else "#0c0f18"
        adc = f"{r['Est ADC']:.1f}" if pd.notna(r.get("Est ADC")) else "—"
        stars_raw = str(r['Stars']) if pd.notna(r.get('Stars')) else "—"
        try:
            sn = float(stars_raw)
            stars_display = f"{stars_raw}★"
            stars_color = "#ef4444" if sn <= 2 else "#22c55e" if sn >= 4 else "#94a3b8"
        except:
            stars_display = "—"; stars_color = "#374151"
        hci_raw = str(r['HCI']) if pd.notna(r.get('HCI')) else "—"
        hci_display = hci_raw if hci_raw not in ("—","nan","") else "—"
        adc_color = "#22c55e" if pd.notna(r.get("Est ADC")) and 10 <= r["Est ADC"] <= 50 else "#94a3b8"
        name     = r["Name"]
        state    = r["State"]
        city     = r["City"]
        own      = r["Ownership Type"] or "—"
        indep    = indep_badge(r["Independent"])
        cert     = r["Cert Year"] or "—"
        bar      = score_bar(r["Score"])
        tier     = tier_badge(r["Tier"])

        rows_html += (
            f'<tr style="background:{bg};border-bottom:1px solid #0f172a">'
            f'<td style="padding:8px 12px;color:#f1f5f9;font-weight:600;font-size:13px">{name}</td>'
            f'<td style="padding:8px 12px"><span style="background:#1e3a5f;color:#93c5fd;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700">{state}</span></td>'
            f'<td style="padding:8px 12px;color:#64748b;font-size:12px">{city}</td>'
            f'<td style="padding:8px 12px;color:#64748b;font-size:11px">{own}</td>'
            f'<td style="padding:8px 12px">{indep}</td>'
            f'<td style="padding:8px 12px;color:#64748b;font-size:12px">{cert}</td>'
            f'<td style="padding:8px 12px;color:{stars_color};font-size:12px">{stars_display}</td>'
            f'<td style="padding:8px 12px;color:#64748b;font-size:12px">{hci_display}</td>'
            f'<td style="padding:8px 12px;color:{adc_color};font-size:12px">{adc}</td>'
            f'<td style="padding:8px 12px;min-width:130px">{bar}</td>'
            f'<td style="padding:8px 12px">{tier}</td>'
            f'</tr>'
        )

    html = f"""
    <div style="overflow-x:auto;border:1px solid #1e293b;border-radius:8px;max-height:520px;overflow-y:auto" id="main-table">
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead style="position:sticky;top:0;z-index:10">
          <tr>{header_html}</tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <div style="font-size:10px;color:#374151;margin-top:6px;padding-left:2px">
      Est. = cert year &nbsp;·&nbsp; HCI = Hospice Care Index (0–10) &nbsp;·&nbsp; ADC = avg daily census
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)



render_table(df)

# ── Scoring Reference ──────────────────────────────────────────────────────────
with st.expander("📊  How Scoring Works", expanded=False):
    st.markdown("""
<div style="color:#94a3b8;font-size:13px;padding:4px 0 12px 0">
All for-profit hospices start with a <strong style="color:#e2e8f0">base score of 25</strong>.
Points are added or subtracted based on six acquisition signals below.
Maximum possible score is <strong style="color:#e2e8f0">125</strong>.
<br><br>
<strong style="color:#22c55e">🔥 HOT ≥ 70</strong> &nbsp;·&nbsp;
<strong style="color:#f59e0b">🌤 WARM ≥ 45</strong> &nbsp;·&nbsp;
<strong style="color:#475569">❄️ COLD &lt; 45</strong>
</div>

<table class="score-table" style="width:100%;border-collapse:collapse">
<thead>
  <tr>
    <th>Signal</th><th>Condition</th>
    <th style="text-align:right">Points</th>
    <th>Why it matters</th>
  </tr>
</thead>
<tbody>
  <tr><td style="color:#e2e8f0;font-weight:600">Independence</td><td style="color:#94a3b8">No chain affiliation (CMS)</td><td style="text-align:right;color:#22c55e;font-weight:700">+30</td><td style="color:#64748b">Founder-owned = motivated seller, simpler structure</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Independence</td><td style="color:#94a3b8">Chain-affiliated</td><td style="text-align:right;color:#ef4444;font-weight:700">−20</td><td style="color:#64748b">Corporate seller = lawyers, longer timeline, harder terms</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Cert Age</td><td style="color:#94a3b8">Certified ≤ 2005</td><td style="text-align:right;color:#22c55e;font-weight:700">+25</td><td style="color:#64748b">20+ years of referral relationships — hardest moat to replicate</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Cert Age</td><td style="color:#94a3b8">Certified ≤ 2010</td><td style="text-align:right;color:#22c55e;font-weight:700">+20</td><td style="color:#64748b">Deep market presence</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Cert Age</td><td style="color:#94a3b8">Certified ≤ 2015</td><td style="text-align:right;color:#22c55e;font-weight:700">+14</td><td style="color:#64748b">Mature operation</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Cert Age</td><td style="color:#94a3b8">Certified ≤ 2019</td><td style="text-align:right;color:#f59e0b;font-weight:700">+8</td><td style="color:#64748b">Growing operation</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Cert Age</td><td style="color:#94a3b8">Certified ≥ 2020</td><td style="text-align:right;color:#475569;font-weight:700">+3</td><td style="color:#64748b">Limited track record</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Star Rating</td><td style="color:#94a3b8">1–2 stars</td><td style="text-align:right;color:#ef4444;font-weight:700">+25 🔥</td><td style="color:#64748b">Distressed operator — more likely to accept favorable terms</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Star Rating</td><td style="color:#94a3b8">3 stars</td><td style="text-align:right;color:#f59e0b;font-weight:700">+10</td><td style="color:#64748b">Average quality, improvement upside</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Star Rating</td><td style="color:#94a3b8">4–5 stars</td><td style="text-align:right;color:#22c55e;font-weight:700">+15</td><td style="color:#64748b">Premium asset, strong clinical outcomes</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Star Rating</td><td style="color:#94a3b8">No rating</td><td style="text-align:right;color:#f59e0b;font-weight:700">+12</td><td style="color:#64748b">Below 50-patient survey threshold — small target signal</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">HCI Score</td><td style="color:#94a3b8">Below 6 / 10</td><td style="text-align:right;color:#ef4444;font-weight:700">+20 🔥</td><td style="color:#64748b">Operational challenges — seller leverage is low</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">HCI Score</td><td style="color:#94a3b8">6–8 / 10</td><td style="text-align:right;color:#f59e0b;font-weight:700">+8</td><td style="color:#64748b">Average quality</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">HCI Score</td><td style="color:#94a3b8">8+ / 10</td><td style="text-align:right;color:#22c55e;font-weight:700">+5</td><td style="color:#64748b">Strong operator — commands premium valuation</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">HCI Score</td><td style="color:#94a3b8">Not scored</td><td style="text-align:right;color:#f59e0b;font-weight:700">+10</td><td style="color:#64748b">Too small for CMS scoring — small target signal</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Est. ADC</td><td style="color:#94a3b8">10–50 patients/day</td><td style="text-align:right;color:#22c55e;font-weight:700">+15</td><td style="color:#64748b">Sweet spot — real cash flow, manageable for seller note structure</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Est. ADC</td><td style="color:#94a3b8">50–80 patients/day</td><td style="text-align:right;color:#f59e0b;font-weight:700">+8</td><td style="color:#64748b">Slightly above target, may need larger deal structure</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">Est. ADC</td><td style="color:#94a3b8">&gt; 80 patients/day</td><td style="text-align:right;color:#475569;font-weight:700">+3</td><td style="color:#64748b">Larger operator</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">CAHPS</td><td style="color:#94a3b8">Below 70%</td><td style="text-align:right;color:#ef4444;font-weight:700">+15 🔥</td><td style="color:#64748b">Family dissatisfaction — operational or staffing issues</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">CAHPS</td><td style="color:#94a3b8">70–84%</td><td style="text-align:right;color:#f59e0b;font-weight:700">+6</td><td style="color:#64748b">Average family satisfaction</td></tr>
  <tr><td style="color:#e2e8f0;font-weight:600">CAHPS</td><td style="color:#94a3b8">85%+</td><td style="text-align:right;color:#22c55e;font-weight:700">+10</td><td style="color:#64748b">Strong reputation — families rate care highly</td></tr>
</tbody>
</table>

<div style="margin-top:14px;background:#0f1520;border:1px solid #1e293b;border-radius:6px;padding:12px 16px;font-size:11px;color:#64748b">
  <strong style="color:#94a3b8">Data sources:</strong>
  CMS General Information (ownership, cert date) ·
  PAC PUF 2023 (ADC estimated as service days ÷ 365, revenue) ·
  Provider Information (stars, HCI, chain) ·
  CAHPS Survey (family satisfaction) ·
  <strong style="color:#94a3b8">Note:</strong>
  Stars and HCI are only populated for providers with 50+ patients.
  ADC does not include non-Medicare patients.
  CMS data lags reality by 6–18 months — always verify ownership independently before outreach.
</div>
""", unsafe_allow_html=True)

# ── Provider Detail ────────────────────────────────────────────────────────────
st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# Search box to select a provider for detail view
st.markdown("<div style='color:#f1f5f9;font-size:16px;font-weight:700;margin-bottom:8px'>🔍 Provider Detail</div>", unsafe_allow_html=True)

provider_names = df["Name"].tolist() if len(df) > 0 else []
search_options = ["— select a provider —"] + provider_names
picked = st.selectbox("Search or select a provider", options=search_options, index=0, key="detail_select", label_visibility="collapsed")

if picked != "— select a provider —":
    st.session_state.selected_provider = picked

sel_name = st.session_state.selected_provider
if len(df) > 0 and sel_name and sel_name in provider_names:
    if True:
        row = df[df["Name"]==sel_name].iloc[0]
        sc = row["Score"]; col = score_color(sc)

        d1,d2 = st.columns([3,1])
        with d1:
            st.markdown(f"""
            <div style="background:#0f1520;border:1px solid #1e293b;border-radius:10px;padding:16px 20px;margin-bottom:10px">
              <div style="font-size:18px;font-weight:700;color:#f1f5f9">{row['Name']}</div>
              <div style="font-size:12px;color:#475569;margin-top:3px">
                {row['City']}, {row['State']} &nbsp;·&nbsp;
                CCN: <code style="background:#1e293b;color:#94a3b8;padding:1px 6px;border-radius:3px">{row['CCN']}</code>
                &nbsp;·&nbsp; {row['Phone']}
              </div>
            </div>
            """, unsafe_allow_html=True)

            adc_d  = f"{row['Est ADC']:.1f} pts/day"    if pd.notna(row.get("Est ADC"))         else "No PUF data"
            rev_d  = f"${row['Est Revenue ($k)']:.0f}k Medicare/yr" if pd.notna(row.get("Est Revenue ($k)")) else "No PUF data"
            cahps_d= f"{row['CAHPS %']}%"               if pd.notna(row.get("CAHPS %"))          else "Not available"

            items=[
                ("Ownership Type", row.get("Ownership Type","—")),
                ("Independent?",   row.get("Independent","—")),
                ("Certified",      row.get("Cert Year","—")),
                ("CMS Stars",      f"{row['Stars']}★" if str(row['Stars']) not in ("—","nan","") else "No rating"),
                ("HCI Score",      f"{row['HCI']} / 10" if str(row['HCI']) not in ("—","nan","") else "Not scored"),
                ("Est. ADC",       adc_d),
                ("Est. Medicare Revenue", rev_d),
                ("CAHPS Family Rating",   cahps_d),
            ]
            cols = st.columns(4)
            for i,(k,v) in enumerate(items):
                with cols[i%4]:
                    st.markdown(f'<div class="info-card"><div class="info-label">{k}</div><div class="info-value">{v}</div></div>',unsafe_allow_html=True)

        with d2:
            st.markdown(f"""
            <div style="background:{col}18;border:2px solid {col};border-radius:12px;padding:24px 16px;text-align:center">
              <div style="font-size:44px;font-weight:700;color:{col};line-height:1">{sc}</div>
              <div style="font-size:10px;color:#475569;margin:4px 0 8px 0">out of 125</div>
              <div style="font-size:16px;font-weight:700;color:{col}">{row['Tier']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:11px;font-weight:700;color:#475569;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px'>Acquisition Signals</div>", unsafe_allow_html=True)

        for sig in row["Signals"]:
            t=sig["type"]
            icon  = "🔥" if t=="hot" else "✓" if t=="positive" else "⚠️" if t=="warn" else "✗" if t=="negative" else "·"
            cstr  = "#ef4444" if t in ("hot","negative") else "#22c55e" if t=="positive" else "#f59e0b" if t=="warn" else "#64748b"
            wstr  = f"+{sig['weight']}" if sig['weight']>0 else str(sig['weight'])
            st.markdown(f"""
            <div class="sig-row">
              <span style="color:{cstr};font-size:14px;flex-shrink:0;width:16px">{icon}</span>
              <span style="color:#cbd5e1;font-size:13px;flex:1">{sig['label']}</span>
              <span style="color:#374151;font-size:11px;flex-shrink:0">{wstr} pts</span>
            </div>
            """, unsafe_allow_html=True)
