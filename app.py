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

st.markdown("""
<style>
  [data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#0c0f18!important;color:#e2e8f0!important}
  [data-testid="stHeader"]{background:transparent!important}
  section[data-testid="stSidebar"]{display:none}
  h1,h2,h3,h4{color:#f1f5f9!important}
  p,li{color:#94a3b8!important}
  [data-testid="stTextInput"] input{background:#111827!important;border:1px solid #1e293b!important;color:#e2e8f0!important;border-radius:6px!important}
  [data-baseweb="select"]>div{background:#111827!important;border:1px solid #1e293b!important;color:#e2e8f0!important}
  [data-baseweb="popover"]{background:#111827!important;border:1px solid #1e293b!important}
  [role="listbox"]{background:#111827!important}
  [role="option"]{color:#e2e8f0!important}
  [role="option"]:hover{background:#1e293b!important}
  [data-baseweb="tag"]{background:#1e3a5f!important;color:#93c5fd!important}
  [data-testid="metric-container"]{background:#0f1520!important;border:1px solid #1e293b!important;border-radius:8px!important;padding:12px 16px!important}
  [data-testid="stMetricLabel"] p{color:#475569!important;font-size:11px!important}
  [data-testid="stMetricValue"]{color:#f1f5f9!important}
  [data-testid="stDownloadButton"] button{background:#1e3a5f!important;border:1px solid #2563eb!important;color:#93c5fd!important;border-radius:6px!important;font-size:12px!important}
  [data-testid="stExpander"]{background:#0f1520!important;border:1px solid #1e293b!important;border-radius:8px!important}
  [data-testid="stExpander"] summary p{color:#94a3b8!important}
  [data-testid="stFileUploaderDropzone"]{background:#0f1520!important;border:1px dashed #1e3a5f!important}
  [data-testid="stToggle"] p{color:#94a3b8!important}
  div[data-baseweb="select"] span,div[data-baseweb="select"] div,[data-testid="stSelectbox"] span,[data-testid="stSelectbox"] label{color:#e2e8f0!important;background-color:transparent!important}
  div[data-baseweb="select"]>div{background-color:#111827!important;border-color:#1e293b!important}
  ul[role="listbox"] li{background-color:#111827!important;color:#e2e8f0!important}
  ul[role="listbox"] li:hover,ul[role="listbox"] li[aria-selected="true"]{background-color:#1e293b!important}
  hr{border-color:#1e293b!important;margin:12px 0!important}
  .sig-row{display:flex;align-items:flex-start;gap:10px;margin-bottom:5px;padding:7px 12px;background:#111827;border-radius:5px}
  .info-card{background:#111827;border:1px solid #1e293b;border-radius:6px;padding:10px 12px;margin-bottom:6px}
  .info-label{font-size:9px;letter-spacing:1px;color:#475569;text-transform:uppercase;margin-bottom:3px}
  .info-value{font-size:13px;color:#e2e8f0}
  .filter-row{background:#0a0d14;border:1px solid #1e293b;border-radius:8px;padding:16px 20px;margin-bottom:16px}
  .htbl{width:100%;border-collapse:collapse;font-size:13px}
  .htbl thead tr{background:#0a0d14;position:sticky;top:0;z-index:5}
  .htbl th{padding:8px 12px;text-align:left;color:#475569;font-size:10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #1e293b;white-space:nowrap}
  .htbl td{padding:8px 12px;border-bottom:1px solid #0c0f18;color:#94a3b8;font-size:12px}
  .htbl tr:hover td{background:#111827!important}
  .htbl .name-cell{color:#f1f5f9;font-weight:600;cursor:pointer;text-decoration:underline;text-decoration-color:#1e3a5f}
  .htbl .name-cell:hover{color:#93c5fd}
  .score-bar-wrap{display:flex;align-items:center;gap:6px}
  .score-bar-bg{flex:1;background:#1e293b;border-radius:3px;height:6px;min-width:60px}
  .score-bar-fill{height:6px;border-radius:3px}
  .tier-hot{background:#14532d33;border:1px solid #22c55e;color:#22c55e;border-radius:20px;padding:2px 8px;font-size:11px;font-weight:700;white-space:nowrap}
  .tier-warm{background:#78350f33;border:1px solid #f59e0b;color:#f59e0b;border-radius:20px;padding:2px 8px;font-size:11px;font-weight:700;white-space:nowrap}
  .tier-cold{background:#1e293b;border:1px solid #374151;color:#475569;border-radius:20px;padding:2px 8px;font-size:11px;white-space:nowrap}
  .state-badge{background:#1e3a5f;color:#93c5fd;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700}
  .indep-yes{color:#22c55e;font-weight:700}
  .indep-no{color:#ef4444;font-weight:700}
  .tbl-wrap{overflow-x:auto;overflow-y:auto;max-height:520px;border:1px solid #1e293b;border-radius:8px}
</style>
""", unsafe_allow_html=True)

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

def load_csv(file_or_path):
    if isinstance(file_or_path,(str,Path)):
        with open(file_or_path,'r',encoding='utf-8-sig') as f: content = f.read()
    else:
        content = file_or_path.read().decode('utf-8-sig')
    delim = '\t' if '\t' in content.split('\n')[0] else ','
    df = pd.read_csv(io.StringIO(content), sep=delim, dtype=str, on_bad_lines='skip')
    return normalize_cols(df)

def score_target(gen_row, prov_row, puf_row, cahps_row):
    score = 25; signals = []

    chain_src = prov_row if prov_row is not None else gen_row
    chain_val = ""
    for col in ["affiliated_with_a_hospice_chain","affiliated_with_chain","chain_owned","chain"]:
        if col in chain_src.index and pd.notna(chain_src[col]):
            chain_val = str(chain_src[col]).lower().strip(); break
    if chain_val in ("","no","n","nan"):
        score+=30; signals.append({"label":"Independent operator — likely founder-owned","type":"positive","weight":30})
    else:
        score-=20; signals.append({"label":"Chain-affiliated — harder negotiation","type":"negative","weight":-20})

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

    stars_src = prov_row if prov_row is not None else gen_row
    stars = 0
    for col in ["overall_rating","overall_star_rating","hospice_overall_rating"]:
        if col in stars_src.index and pd.notna(stars_src[col]):
            try: stars = float(stars_src[col]); break
            except: pass
    if 1<=stars<=2:  score+=25; signals.append({"label":f"Low stars ({stars}★) — distress signal","type":"hot","weight":25})
    elif stars==3:   score+=10; signals.append({"label":"Average rating (3★) — improvement upside","type":"neutral","weight":10})
    elif stars>=4:   score+=15; signals.append({"label":f"High quality ({stars}★) — premium asset","type":"positive","weight":15})
    else:            signals.append({"label":"No star rating — unscored (too small or data pending)","type":"neutral","weight":0})

    hci = 0
    src = prov_row if prov_row is not None else gen_row
    for col in ["hospice_care_index_score","hci_score","hospice_care_index"]:
        if col in src.index and pd.notna(src[col]):
            try: hci = float(src[col]); break
            except: pass
    if 1<=hci<6:   score+=20; signals.append({"label":f"Low HCI ({hci}/10) — operational challenges","type":"hot","weight":20})
    elif 6<=hci<8: score+=8;  signals.append({"label":f"Average HCI ({hci}/10)","type":"neutral","weight":8})
    elif hci>=8:   score+=5;  signals.append({"label":f"Strong HCI ({hci}/10)","type":"positive","weight":5})
    else:          signals.append({"label":"No HCI score — unscored (too small or data pending)","type":"neutral","weight":0})

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
        if 10<=av<=50:    score+=15; signals.append({"label":f"Est. ADC ~{av} — in target range","type":"positive","weight":15})
        elif 50<av<=80:   score+=8;  signals.append({"label":f"Est. ADC ~{av} — slightly above target","type":"neutral","weight":8})
        elif av>80:       score+=3;  signals.append({"label":f"Est. ADC ~{av} — larger operator","type":"neutral","weight":3})
        elif av>0:        score+=10; signals.append({"label":f"Est. ADC ~{av} — very small","type":"neutral","weight":10})

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

    return score, signals, adc, benes, revenue, cahps_rating

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
        score,signals,adc,benes,revenue,cahps_rating = score_target(row,prov_r,puf_r,cahps_r)

        name_col =next((c for c in ["facility_name","provider_name","organization_name"] if c in row.index),None)
        city_col =next((c for c in ["city/town","city_town","city","provider_city"]      if c in row.index),None)
        cert_col =next((c for c in ["certification_date","date_of_certification"]        if c in row.index),None)
        phone_col=next((c for c in ["telephone_number","phone"]                          if c in row.index),None)
        ss=prov_r if prov_r is not None else row
        hs=prov_r if prov_r is not None else row
        cs=prov_r if prov_r is not None else row
        stars_col=next((c for c in ["overall_rating","overall_star_rating","hospice_overall_rating"] if c in ss.index),None)
        hci_col  =next((c for c in ["hospice_care_index_score","hci_score","hospice_care_index"]     if c in hs.index),None)
        chain_col=next((c for c in ["affiliated_with_a_hospice_chain","affiliated_with_chain","chain_owned","chain"] if c in cs.index),None)

        cert_str=str(row.get(cert_col,"")) if cert_col else ""
        cert_year=""
        if cert_str and cert_str!="nan":
            try:
                pts=cert_str.split("/"); cert_year=pts[2] if len(pts)==3 else pts[0]
            except: pass

        chain_val=str(cs.get(chain_col,"")) if chain_col else ""
        is_indep=chain_val.lower().strip() in ("","no","n","nan")

        results.append({
            "Name":             str(row.get(name_col,"Unknown")) if name_col else "Unknown",
            "CCN":              ccn,
            "State":            state,
            "City":             str(row.get(city_col,"")) if city_col else "",
            "Phone":            str(row.get(phone_col,"")) if phone_col else "",
            "Ownership Type":   str(row.get(own_col,"")) if own_col else "",
            "Independent":      "✓ Yes" if is_indep else "✗ Chain",
            "Cert Year":        cert_year,
            "Stars":            str(ss.get(stars_col,"—")) if stars_col else "—",
            "HCI":              str(hs.get(hci_col,"—")) if hci_col else "—",
            "Est ADC":          adc if adc else (benes if benes else None),
            "Est Revenue ($k)": round(revenue/1000) if revenue else None,
            "CAHPS %":          cahps_rating,
            "Score":            score,
            "Tier":             score_label(score),
            "Signals":          signals,
            "Has PUF":          puf_r is not None,
        })

    return pd.DataFrame(results).sort_values("Score",ascending=False).reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "selected_ccn" not in st.session_state:
    st.session_state.selected_ccn = None

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="border-bottom:1px solid #1e293b;padding-bottom:16px;margin-bottom:20px">
  <div style="font-size:10px;letter-spacing:3px;color:#475569;text-transform:uppercase">Willowbridge Capital · Deal Sourcing</div>
  <div style="font-size:26px;font-weight:700;color:#f8fafc;margin-top:4px">Hospice Target Screener</div>
  <div style="font-size:12px;color:#475569;margin-top:3px">CMS data · scored 0–125 · ID · UT · NV · MT · WY · CO · AZ · TX · OK</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTERS
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner("Loading CMS data..."):
    df_gen_default, df_puf_default = load_defaults()

st.markdown('<div class="filter-row">', unsafe_allow_html=True)
fc1,fc2,fc3,fc4 = st.columns([2.5,2,1.8,1])
with fc1: search = st.text_input("🔍 Search provider or city","",placeholder="e.g. Boise, Heart n Home...")
with fc2: selected_states = st.multiselect("States",options=TARGET_STATES,default=TARGET_STATES,placeholder="Select states...")
with fc3: score_filter = st.selectbox("Minimum tier",["All tiers","🌤 WARM and above (45+)","🔥 HOT only (70+)"])
with fc4:
    st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
    for_profit_only = st.toggle("For-profit only",value=True)
st.markdown('</div>',unsafe_allow_html=True)

with st.expander("📂  Update CMS Data Files  ·  *default: Feb 2026 — upload newer files here*",expanded=False):
    uc1,uc2,uc3,uc4 = st.columns(4)
    with uc1: up_general = st.file_uploader("General Information *(required)*",type="csv",key="up_gen"); st.caption("data.cms.gov → Hospice - General Information")
    with uc2: up_prov = st.file_uploader("Provider Information",type="csv",key="up_prov"); st.caption("Stars, HCI score, chain affiliation")
    with uc3: up_puf = st.file_uploader("PAC PUF *(utilization)*",type="csv",key="up_puf"); st.caption("catalog.data.gov → Medicare PAC PUF Hospice")
    with uc4: up_cahps = st.file_uploader("CAHPS Survey",type="csv",key="up_cahps"); st.caption("Family satisfaction — larger providers only")

df_gen   = load_csv(up_general) if up_general else df_gen_default
df_puf   = load_csv(up_puf)     if up_puf     else df_puf_default
df_prov  = load_csv(up_prov)    if up_prov    else None
df_cahps = load_csv(up_cahps)   if up_cahps   else None

if df_gen is None:
    st.error("No General Information file found."); st.stop()
if not selected_states:
    st.warning("Select at least one state."); st.stop()

with st.spinner("Scoring providers..."):
    df_all = build_targets(df_gen,df_puf,df_prov,df_cahps,for_profit_only=for_profit_only,selected_states=selected_states)

df = df_all.copy()
if score_filter=="🔥 HOT only (70+)":        df=df[df["Score"]>=70]
elif score_filter=="🌤 WARM and above (45+)": df=df[df["Score"]>=45]
if search:
    df=df[df["Name"].str.contains(search,case=False,na=False)|df["City"].str.contains(search,case=False,na=False)]
df=df.reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ══════════════════════════════════════════════════════════════════════════════
k1,k2,k3,k4,k5=st.columns(5)
with k1: st.metric("Total Providers",len(df))
with k2: st.metric("🔥 HOT (70+)",len(df[df["Score"]>=70]))
with k3: st.metric("🌤 WARM (45–69)",len(df[(df["Score"]>=45)&(df["Score"]<70)]))
with k4: st.metric("Chain-Affiliated",int((df["Independent"]=="✗ Chain").sum()))
with k5: st.metric("Has Census Data",int(df["Has PUF"].sum()))

st.markdown("<div style='height:6px'></div>",unsafe_allow_html=True)

ec1,ec2=st.columns([9,1])
with ec2:
    export_df=df.drop(columns=["Signals","Has PUF"],errors="ignore")
    st.download_button("⬇ Export CSV",export_df.to_csv(index=False).encode(),"hospice_targets.csv","text/csv")
with ec1:
    st.markdown(f"<div style='color:#475569;font-size:12px;padding-top:8px'>{len(df)} providers · click a name to view detail</div>",unsafe_allow_html=True)

if df.empty:
    st.warning("No providers match the current filters."); st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# HTML TABLE — pure HTML, no st.dataframe
# ══════════════════════════════════════════════════════════════════════════════
rows_html = ""
for i, r in df.iterrows():
    bg = "#0f1520" if i%2==0 else "#0c0f18"
    sc = r["Score"]
    pct = min(sc/125*100,100)
    bar_color = "#22c55e" if sc>=70 else "#f59e0b" if sc>=45 else "#475569"
    tier = r["Tier"]
    tier_cls = "tier-hot" if "HOT" in tier else "tier-warm" if "WARM" in tier else "tier-cold"
    indep_cls = "indep-yes" if "Yes" in str(r["Independent"]) else "indep-no"
    adc_str = f"{r['Est ADC']:.1f}" if pd.notna(r.get("Est ADC")) else "—"
    stars_str = str(r["Stars"]) if str(r["Stars"]) not in ("—","nan","") else "—"
    hci_str   = str(r["HCI"])   if str(r["HCI"])   not in ("—","nan","") else "—"
    name_esc = r["Name"].replace('"','&quot;').replace("'","&#39;")
    ccn = r["CCN"]

    rows_html += f"""<tr style='background:{bg}'>
<td class='name-cell' onclick='selectProvider("{ccn}")'>{r["Name"]}</td>
<td><span class='state-badge'>{r["State"]}</span></td>
<td>{r["City"]}</td>
<td class='{indep_cls}'>{r["Independent"]}</td>
<td>{r["Cert Year"]}</td>
<td>{stars_str}</td>
<td>{hci_str}</td>
<td>{adc_str}</td>
<td><div class='score-bar-wrap'><div class='score-bar-bg'><div class='score-bar-fill' style='width:{pct}%;background:{bar_color}'></div></div><span style='color:{bar_color};font-weight:700;font-size:12px;min-width:24px'>{sc}</span></div></td>
<td><span class='{tier_cls}'>{tier}</span></td>
</tr>"""

table_html = f"""
<div class='tbl-wrap'>
<table class='htbl'>
<thead><tr>
<th>Provider</th><th>St</th><th>City</th><th>Indep?</th><th>Est.</th><th>Stars</th><th>HCI</th><th>ADC</th><th>Score</th><th>Tier</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>
<script>
function selectProvider(ccn, name) {{
    // Set query param and reload — Streamlit will read it on rerun
    const url = new URL(window.parent.location.href);
    url.searchParams.set('sel', ccn);
    window.parent.location.href = url.toString();
}}
</script>
"""

st.markdown(table_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROVIDER DETAIL — driven by query param (set when row is clicked)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# Read CCN from query params (set by table row click)
qp = st.query_params
clicked_ccn = qp.get("sel", None)

# Also allow manual text search
st.markdown("<div style='color:#475569;font-size:11px;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px'>📋 Provider Detail — click a row above, or type a name below</div>", unsafe_allow_html=True)
name_input = st.text_input("Provider name", "", placeholder="Start typing a name...", label_visibility="collapsed", key="detail_search")

# Resolve which provider to show: text search takes priority, then click
row = None
if name_input.strip():
    matched = df[df["Name"].str.contains(name_input.strip(), case=False, na=False)]
    if not matched.empty:
        if len(matched) > 1:
            chosen = st.selectbox("Multiple matches:", matched["Name"].tolist(), key="detail_pick")
            row = matched[matched["Name"] == chosen].iloc[0]
        else:
            row = matched.iloc[0]
    else:
        st.markdown("<div style='color:#475569;font-size:12px'>No match found.</div>", unsafe_allow_html=True)
elif clicked_ccn:
    matched = df[df["CCN"] == clicked_ccn]
    if not matched.empty:
        row = matched.iloc[0]

# Render detail card if we have a row
if row is not None:
    sc = row["Score"]; col = score_color(sc)
    d1,d2 = st.columns([3,1])
    with d1:
        st.markdown(f"""<div style='background:#0f1520;border:1px solid #1e293b;border-radius:10px;padding:16px 20px;margin-bottom:12px'>
<div style='font-size:18px;font-weight:700;color:#f1f5f9'>{row["Name"]}</div>
<div style='font-size:12px;color:#475569;margin-top:3px'>{row["City"]}, {row["State"]} &nbsp;·&nbsp; CCN: <code style='background:#1e293b;color:#94a3b8;padding:1px 6px;border-radius:3px'>{row["CCN"]}</code> &nbsp;·&nbsp; {row["Phone"]}</div>
</div>""", unsafe_allow_html=True)

        adc_d   = f"{row['Est ADC']:.1f} pts/day"               if pd.notna(row.get("Est ADC"))          else "No PUF data"
        rev_d   = f"${row['Est Revenue ($k)']:.0f}k Medicare/yr" if pd.notna(row.get("Est Revenue ($k)")) else "No PUF data"
        cahps_d = f"{row['CAHPS %']}%"                           if pd.notna(row.get("CAHPS %"))           else "Not available"
        stars_v = f"{row['Stars']}★" if str(row['Stars']) not in ("—","nan","") else "No rating"
        hci_v   = f"{row['HCI']} / 10" if str(row['HCI']) not in ("—","nan","") else "Not scored"

        items=[("Ownership",row.get("Ownership Type","—")),("Independent?",row.get("Independent","—")),
               ("Certified",row.get("Cert Year","—")),("Stars",stars_v),("HCI",hci_v),
               ("Est. ADC",adc_d),("Medicare Rev.",rev_d),("CAHPS",cahps_d)]
        ic=st.columns(4)
        for idx,(k,v) in enumerate(items):
            with ic[idx%4]:
                st.markdown(f'<div class="info-card"><div class="info-label">{k}</div><div class="info-value">{v}</div></div>', unsafe_allow_html=True)

    with d2:
        st.markdown(f"""<div style='background:{col}18;border:2px solid {col};border-radius:12px;padding:24px 16px;text-align:center'>
<div style='font-size:44px;font-weight:700;color:{col};line-height:1'>{sc}</div>
<div style='font-size:10px;color:#475569;margin:4px 0 8px 0'>out of 125</div>
<div style='font-size:16px;font-weight:700;color:{col}'>{row["Tier"]}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;font-weight:700;color:#475569;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px'>Acquisition Signals</div>", unsafe_allow_html=True)
    for sig in row["Signals"]:
        t=sig["type"]
        icon="🔥" if t=="hot" else "✓" if t=="positive" else "⚠️" if t=="warn" else "✗" if t=="negative" else "·"
        cstr="#ef4444" if t in ("hot","negative") else "#22c55e" if t=="positive" else "#f59e0b" if t=="warn" else "#64748b"
        wstr=f"+{sig['weight']}" if sig['weight']>0 else str(sig['weight'])
        st.markdown(f'<div class="sig-row"><span style="color:{cstr};font-size:14px;flex-shrink:0;width:16px">{icon}</span><span style="color:#cbd5e1;font-size:13px;flex:1">{sig["label"]}</span><span style="color:#374151;font-size:11px;flex-shrink:0">{wstr} pts</span></div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="background:#0f1520;border:1px dashed #1e293b;border-radius:8px;padding:20px;text-align:center;color:#374151;font-size:13px">Click a provider name in the table above, or type a name to view detail</div>', unsafe_allow_html=True)

with st.expander("📊  How Scoring Works",expanded=False):
    st.markdown("""<div style='color:#94a3b8;font-size:13px;padding:4px 0 12px 0'>
Base score <strong style='color:#e2e8f0'>25</strong>. Max <strong style='color:#e2e8f0'>125</strong>.
<strong style='color:#22c55e'>🔥 HOT ≥70</strong> · <strong style='color:#f59e0b'>🌤 WARM ≥45</strong> · <strong style='color:#475569'>❄️ COLD &lt;45</strong>
</div>
<table style='width:100%;border-collapse:collapse;font-size:12px'>
<thead><tr style='background:#0a0d14'>
<th style='padding:8px 12px;text-align:left;color:#475569;font-size:10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #1e293b'>Signal</th>
<th style='padding:8px 12px;text-align:left;color:#475569;font-size:10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #1e293b'>Condition</th>
<th style='padding:8px 12px;text-align:right;color:#475569;font-size:10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #1e293b'>Pts</th>
</tr></thead>
<tbody>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Independence</td><td style='padding:7px 12px;color:#94a3b8'>No chain affiliation</td><td style='padding:7px 12px;text-align:right;color:#22c55e;font-weight:700'>+30</td></tr>
<tr style='background:#111827'><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Independence</td><td style='padding:7px 12px;color:#94a3b8'>Chain-affiliated</td><td style='padding:7px 12px;text-align:right;color:#ef4444;font-weight:700'>−20</td></tr>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Cert Age</td><td style='padding:7px 12px;color:#94a3b8'>≤ 2005</td><td style='padding:7px 12px;text-align:right;color:#22c55e;font-weight:700'>+25</td></tr>
<tr style='background:#111827'><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Cert Age</td><td style='padding:7px 12px;color:#94a3b8'>≤ 2010</td><td style='padding:7px 12px;text-align:right;color:#22c55e;font-weight:700'>+20</td></tr>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Cert Age</td><td style='padding:7px 12px;color:#94a3b8'>≤ 2015</td><td style='padding:7px 12px;text-align:right;color:#22c55e;font-weight:700'>+14</td></tr>
<tr style='background:#111827'><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Cert Age</td><td style='padding:7px 12px;color:#94a3b8'>≤ 2019</td><td style='padding:7px 12px;text-align:right;color:#f59e0b;font-weight:700'>+8</td></tr>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Stars</td><td style='padding:7px 12px;color:#94a3b8'>1–2 stars</td><td style='padding:7px 12px;text-align:right;color:#ef4444;font-weight:700'>+25 🔥</td></tr>
<tr style='background:#111827'><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Stars</td><td style='padding:7px 12px;color:#94a3b8'>3 stars</td><td style='padding:7px 12px;text-align:right;color:#f59e0b;font-weight:700'>+10</td></tr>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>Stars</td><td style='padding:7px 12px;color:#94a3b8'>4–5 stars</td><td style='padding:7px 12px;text-align:right;color:#22c55e;font-weight:700'>+15</td></tr>
<tr style='background:#111827'><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>HCI</td><td style='padding:7px 12px;color:#94a3b8'>Below 6</td><td style='padding:7px 12px;text-align:right;color:#ef4444;font-weight:700'>+20 🔥</td></tr>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>HCI</td><td style='padding:7px 12px;color:#94a3b8'>6–8</td><td style='padding:7px 12px;text-align:right;color:#f59e0b;font-weight:700'>+8</td></tr>
<tr style='background:#111827'><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>HCI</td><td style='padding:7px 12px;color:#94a3b8'>8+</td><td style='padding:7px 12px;text-align:right;color:#22c55e;font-weight:700'>+5</td></tr>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>ADC</td><td style='padding:7px 12px;color:#94a3b8'>10–50 pts/day</td><td style='padding:7px 12px;text-align:right;color:#22c55e;font-weight:700'>+15</td></tr>
<tr style='background:#111827'><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>ADC</td><td style='padding:7px 12px;color:#94a3b8'>50–80 pts/day</td><td style='padding:7px 12px;text-align:right;color:#f59e0b;font-weight:700'>+8</td></tr>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>CAHPS</td><td style='padding:7px 12px;color:#94a3b8'>Below 70%</td><td style='padding:7px 12px;text-align:right;color:#ef4444;font-weight:700'>+15 🔥</td></tr>
<tr style='background:#111827'><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>CAHPS</td><td style='padding:7px 12px;color:#94a3b8'>70–84%</td><td style='padding:7px 12px;text-align:right;color:#f59e0b;font-weight:700'>+6</td></tr>
<tr><td style='padding:7px 12px;color:#e2e8f0;font-weight:600'>CAHPS</td><td style='padding:7px 12px;color:#94a3b8'>85%+</td><td style='padding:7px 12px;text-align:right;color:#22c55e;font-weight:700'>+10</td></tr>
</tbody></table>""",unsafe_allow_html=True)
