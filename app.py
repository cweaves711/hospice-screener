import streamlit as st
import pandas as pd
import numpy as np
import io
from pathlib import Path

st.set_page_config(
    page_title="Hospice Target Screener | Willowbridge Capital",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #0c0f18; color: #e2e8f0; }
  [data-testid="stSidebar"] { background: #0a0d14; border-right: 1px solid #1e293b; }
  [data-testid="stSidebar"] * { color: #94a3b8 !important; }
  .stDataFrame { background: #0f1520; }
  h1,h2,h3 { color: #f1f5f9 !important; }
  .metric-card { background: #0f1520; border: 1px solid #1e293b; border-radius: 8px; padding: 14px 18px; }
  .hot { color: #22c55e; font-weight: 700; }
  .warm { color: #f59e0b; font-weight: 700; }
  .cold { color: #475569; }
  .flag { color: #f59e0b; }
  .stButton button { background: #1d4ed8 !important; color: white !important; border: none !important; }
  div[data-testid="stExpander"] { background: #0f1520; border: 1px solid #1e293b; border-radius: 6px; }
  .stSelectbox > div, .stMultiSelect > div { background: #111827 !important; }
  label { color: #94a3b8 !important; }
  .upload-note { font-size: 11px; color: #374151; padding: 8px 0; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
TARGET_STATES = ["ID", "UT", "NV", "MT", "WY", "CO", "AZ", "TX", "OK"]

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
    df.columns = (df.columns.str.strip()
                  .str.lower()
                  .str.replace(r'\s+', '_', regex=True)
                  .str.replace(r'[()]', '', regex=True))
    return df

def get_ccn(row):
    for col in ["cms_certification_number_ccn", "ccn", "cms_certification_number",
                "prvdr_id", "provider_id", "prvdr_num", "facility_id", "certification_number"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            val = str(row[col]).strip()
            # Pad to 6 digits
            try:
                return str(int(val)).zfill(6)
            except:
                return val
    return ""

def detect_chain(name):
    if not name:
        return None
    lower = str(name).lower()
    for pattern in KNOWN_CHAIN_PATTERNS:
        if pattern in lower:
            return pattern
    return None

def load_csv(file_or_path):
    if isinstance(file_or_path, (str, Path)):
        with open(file_or_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    else:
        content = file_or_path.read().decode('utf-8-sig')
    delimiter = '\t' if '\t' in content.split('\n')[0] else ','
    df = pd.read_csv(io.StringIO(content), sep=delimiter, dtype=str, on_bad_lines='skip')
    return normalize_cols(df)

def score_target(gen_row, prov_row, puf_row, cahps_row):
    score = 25
    signals = []
    ownership_flag = None

    # ── Independence ──
    chain_src = prov_row if prov_row is not None else gen_row
    chain_val = ""
    for col in ["affiliated_with_a_hospice_chain", "affiliated_with_chain", "chain_owned", "chain"]:
        if col in chain_src.index and pd.notna(chain_src[col]):
            chain_val = str(chain_src[col]).lower().strip()
            break

    cms_independent = chain_val in ("", "no", "n", "nan")
    name = str(gen_row.get("facility_name", gen_row.get("provider_name", "")))
    name_match = detect_chain(name)

    if name_match and cms_independent:
        ownership_flag = f'Name matches known chain pattern "{name_match}" — verify ownership before outreach'
        score += 30
        signals.append({"label": f"CMS: Independent — ⚠️ name suggests possible chain ({name_match}), verify", "type": "warn", "weight": 30})
    elif cms_independent:
        score += 30
        signals.append({"label": "Independent operator — likely founder-owned", "type": "positive", "weight": 30})
    else:
        score -= 20
        signals.append({"label": "Chain-affiliated — harder negotiation", "type": "negative", "weight": -20})
        ownership_flag = "CMS reports chain-affiliated — confirm current ownership structure"

    # ── Cert Age ──
    cert_str = str(gen_row.get("certification_date", ""))
    if cert_str and cert_str != "nan":
        try:
            parts = cert_str.split("/")
            year = int(parts[2]) if len(parts) == 3 else int(parts[0])
            if year <= 2005:   score += 25; signals.append({"label": f"Established {year} — 20+ yr referral roots", "type": "positive", "weight": 25})
            elif year <= 2010: score += 20; signals.append({"label": f"Established {year} — deep market presence", "type": "positive", "weight": 20})
            elif year <= 2015: score += 14; signals.append({"label": f"Certified {year} — mature operation", "type": "positive", "weight": 14})
            elif year <= 2019: score += 8;  signals.append({"label": f"Certified {year}", "type": "neutral", "weight": 8})
            else:              score += 3;  signals.append({"label": f"Newer provider ({year}) — limited track record", "type": "neutral", "weight": 3})
        except:
            pass

    # ── Star Rating ──
    stars_src = prov_row if prov_row is not None else gen_row
    stars = 0
    for col in ["overall_rating", "overall_star_rating", "hospice_overall_rating"]:
        if col in stars_src.index and pd.notna(stars_src[col]):
            try: stars = float(stars_src[col]); break
            except: pass

    if 1 <= stars <= 2:   score += 25; signals.append({"label": f"Low stars ({stars}★) — distress, motivated seller", "type": "hot", "weight": 25})
    elif stars == 3:       score += 10; signals.append({"label": "Average rating (3★) — improvement upside", "type": "neutral", "weight": 10})
    elif stars >= 4:       score += 15; signals.append({"label": f"High quality ({stars}★) — premium asset", "type": "positive", "weight": 15})
    else:                  score += 12; signals.append({"label": "No star rating — likely small/below survey threshold", "type": "neutral", "weight": 12})

    # ── HCI ──
    hci = 0
    for col in ["hospice_care_index_score", "hci_score", "hospice_care_index"]:
        src = prov_row if prov_row is not None else gen_row
        if col in src.index and pd.notna(src[col]):
            try: hci = float(src[col]); break
            except: pass

    if 1 <= hci < 6:  score += 20; signals.append({"label": f"Low HCI ({hci}/10) — operational challenges", "type": "hot", "weight": 20})
    elif 6 <= hci < 8: score += 8; signals.append({"label": f"Average HCI ({hci}/10)", "type": "neutral", "weight": 8})
    elif hci >= 8:     score += 5;  signals.append({"label": f"Strong HCI ({hci}/10)", "type": "positive", "weight": 5})
    else:              score += 10; signals.append({"label": "No HCI score — likely small/new", "type": "neutral", "weight": 10})

    # ── ADC from PUF ──
    adc = 0
    revenue = 0
    benes = 0
    if puf_row is not None:
        try: benes = int(float(str(puf_row.get("bene_dstnct_cnt", 0) or 0)))
        except: benes = 0
        try:
            srvc_days = int(float(str(puf_row.get("tot_srvc_days", 0) or 0)))
            adc = round(srvc_days / 365, 1)
        except: adc = 0
        try:
            pay_str = str(puf_row.get("tot_mdcr_pymt_amt", "0") or "0").replace("$","").replace(",","")
            revenue = float(pay_str)
        except: revenue = 0

        adc_val = adc or benes
        if 10 <= adc_val <= 50:   score += 15; signals.append({"label": f"Est. ADC ~{adc_val} — in target range (10–50)", "type": "positive", "weight": 15})
        elif 50 < adc_val <= 80:  score += 8;  signals.append({"label": f"Est. ADC ~{adc_val} — slightly above target", "type": "neutral", "weight": 8})
        elif adc_val > 80:        score += 3;  signals.append({"label": f"Est. ADC ~{adc_val} — larger operator", "type": "neutral", "weight": 3})
        elif adc_val > 0:         score += 10; signals.append({"label": f"Est. ADC ~{adc_val} — very small", "type": "neutral", "weight": 10})

    # ── CAHPS ──
    cahps_rating = None
    if cahps_row is not None:
        for col in ["rating_of_this_hospice_summary_score", "overall_rating_of_hospice", "cahps_overall_rating"]:
            if col in cahps_row.index and pd.notna(cahps_row[col]):
                try: cahps_rating = float(cahps_row[col]); break
                except: pass
        if cahps_rating:
            if cahps_rating < 70:   score += 15; signals.append({"label": f"Low CAHPS ({cahps_rating}%) — family dissatisfaction", "type": "hot", "weight": 15})
            elif cahps_rating < 85: score += 6;  signals.append({"label": f"Average CAHPS ({cahps_rating}%)", "type": "neutral", "weight": 6})
            else:                   score += 10; signals.append({"label": f"Strong CAHPS ({cahps_rating}%)", "type": "positive", "weight": 10})

    return score, signals, adc, benes, revenue, cahps_rating, ownership_flag

def score_label(s):
    if s >= 70: return "🔥 HOT"
    if s >= 45: return "🌤 WARM"
    return "❄️ COLD"

def score_color(s):
    if s >= 70: return "hot"
    if s >= 45: return "warm"
    return "cold"

# ── Data Loading ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_defaults():
    base = Path(__file__).parent / "data"
    gen = load_csv(base / "general.csv") if (base / "general.csv").exists() else None
    puf = load_csv(base / "puf.csv") if (base / "puf.csv").exists() else None
    return gen, puf

def build_targets(df_gen, df_puf=None, df_prov=None, df_cahps=None, for_profit_only=True, selected_states=None):
    if selected_states is None:
        selected_states = TARGET_STATES

    # Index supplemental files by CCN
    puf_by_ccn = {}
    prov_by_ccn = {}
    cahps_by_ccn = {}

    if df_puf is not None:
        # Filter to PROVIDER rows only
        if "smry_ctgry" in df_puf.columns:
            df_puf = df_puf[df_puf["smry_ctgry"].str.upper().str.strip() == "PROVIDER"]
        for _, row in df_puf.iterrows():
            ccn = get_ccn(row)
            if ccn: puf_by_ccn[ccn] = row

    if df_prov is not None:
        for _, row in df_prov.iterrows():
            ccn = get_ccn(row)
            if ccn: prov_by_ccn[ccn] = row

    if df_cahps is not None:
        for _, row in df_cahps.iterrows():
            ccn = get_ccn(row)
            if ccn: cahps_by_ccn[ccn] = row

    # Get state col
    state_col = next((c for c in ["state", "state_code", "provider_state"] if c in df_gen.columns), None)
    own_col   = next((c for c in ["ownership_type", "type_of_ownership"] if c in df_gen.columns), None)

    results = []
    for _, row in df_gen.iterrows():
        state = str(row.get(state_col, "")).strip().upper() if state_col else ""
        if state not in selected_states:
            continue
        if for_profit_only and own_col:
            own = str(row.get(own_col, "")).lower()
            if not ("for-profit" in own or "for profit" in own or "proprietary" in own):
                continue

        ccn = get_ccn(row)
        puf_row   = puf_by_ccn.get(ccn)
        prov_row  = prov_by_ccn.get(ccn)
        cahps_row = cahps_by_ccn.get(ccn)

        score, signals, adc, benes, revenue, cahps_rating, ownership_flag = score_target(
            row, prov_row, puf_row, cahps_row
        )

        name_col = next((c for c in ["facility_name","provider_name","organization_name"] if c in row.index), None)
        city_col = next((c for c in ["city/town","city_town","city","provider_city"] if c in row.index), None)
        cert_col = next((c for c in ["certification_date","date_of_certification"] if c in row.index), None)
        phone_col = next((c for c in ["telephone_number","phone"] if c in row.index), None)
        stars_src = prov_row if prov_row is not None else row
        stars_col = next((c for c in ["overall_rating","overall_star_rating","hospice_overall_rating"] if c in stars_src.index), None)
        hci_src = prov_row if prov_row is not None else row
        hci_col = next((c for c in ["hospice_care_index_score","hci_score","hospice_care_index"] if c in hci_src.index), None)
        chain_src = prov_row if prov_row is not None else row
        chain_col = next((c for c in ["affiliated_with_a_hospice_chain","affiliated_with_chain","chain_owned","chain"] if c in chain_src.index), None)

        cert_str = str(row.get(cert_col, "")) if cert_col else ""
        cert_year = ""
        if cert_str and cert_str != "nan":
            try:
                parts = cert_str.split("/")
                cert_year = parts[2] if len(parts) == 3 else parts[0]
            except: pass

        results.append({
            "Name": str(row.get(name_col, "Unknown")) if name_col else "Unknown",
            "CCN": ccn,
            "State": state,
            "City": str(row.get(city_col, "")) if city_col else "",
            "Phone": str(row.get(phone_col, "")) if phone_col else "",
            "Ownership": str(row.get(own_col, "")) if own_col else "",
            "Chain": str(chain_src.get(chain_col, "")) if chain_col else "",
            "Cert Year": cert_year,
            "Stars": str(stars_src.get(stars_col, "—")) if stars_col else "—",
            "HCI": str(hci_src.get(hci_col, "—")) if hci_col else "—",
            "Est ADC": adc if adc else (benes if benes else None),
            "Est Revenue ($k)": round(revenue / 1000) if revenue else None,
            "CAHPS": cahps_rating,
            "Score": score,
            "Label": score_label(score),
            "Signals": signals,
            "Ownership Flag": ownership_flag,
            "Has PUF": puf_row is not None,
            "Has CAHPS": cahps_row is not None,
        })

    df = pd.DataFrame(results)
    df = df.sort_values("Score", ascending=False).reset_index(drop=True)
    return df

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 4px 0 16px 0;">
  <div style="font-size:10px;letter-spacing:3px;color:#475569;text-transform:uppercase;">Willowbridge Capital · Deal Sourcing</div>
  <div style="font-size:24px;font-weight:700;color:#f8fafc;margin-top:4px;">Hospice Target Screener</div>
  <div style="font-size:12px;color:#475569;margin-top:2px;">ID · UT · NV · MT · WY · CO · AZ · TX · OK · Scored 0–125</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Filters")

    selected_states = st.multiselect(
        "States", TARGET_STATES, default=TARGET_STATES, key="states"
    )

    for_profit_only = st.toggle("For-profit only", value=True)

    score_filter = st.selectbox("Min score tier", ["All", "🌤 WARM (45+)", "🔥 HOT (70+)"])

    search = st.text_input("Search name / city", "")

    st.markdown("---")
    st.markdown("### 📂 Update Data Files")
    st.markdown('<div class="upload-note">Default data is Feb 2026. Drop new CMS CSVs to refresh.</div>', unsafe_allow_html=True)

    up_general  = st.file_uploader("General Information CSV", type="csv", key="up_gen")
    up_prov     = st.file_uploader("Provider Information CSV (stars/HCI)", type="csv", key="up_prov")
    up_puf      = st.file_uploader("PAC PUF CSV (utilization)", type="csv", key="up_puf")
    up_cahps    = st.file_uploader("CAHPS Survey CSV", type="csv", key="up_cahps")

    st.markdown("---")
    st.markdown('<div class="upload-note">data.cms.gov/provider-data/topics/hospice-care</div>', unsafe_allow_html=True)

# ── Load Data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading data..."):
    df_gen_default, df_puf_default = load_defaults()

df_gen   = load_csv(up_general) if up_general else df_gen_default
df_puf   = load_csv(up_puf) if up_puf else df_puf_default
df_prov  = load_csv(up_prov) if up_prov else None
df_cahps = load_csv(up_cahps) if up_cahps else None

if df_gen is None:
    st.error("No General Information file found. Please upload one in the sidebar.")
    st.stop()

# ── Build Targets ──────────────────────────────────────────────────────────────
with st.spinner("Scoring targets..."):
    df = build_targets(df_gen, df_puf, df_prov, df_cahps,
                       for_profit_only=for_profit_only,
                       selected_states=selected_states if selected_states else TARGET_STATES)

# ── Apply UI Filters ───────────────────────────────────────────────────────────
if score_filter == "🔥 HOT (70+)":
    df = df[df["Score"] >= 70]
elif score_filter == "🌤 WARM (45+)":
    df = df[df["Score"] >= 45]

if search:
    mask = (df["Name"].str.contains(search, case=False, na=False) |
            df["City"].str.contains(search, case=False, na=False))
    df = df[mask]

# ── KPI Cards ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Total Shown", len(df))
with c2:
    st.metric("🔥 HOT (70+)", len(df[df["Score"] >= 70]))
with c3:
    st.metric("🌤 WARM (45+)", len(df[(df["Score"] >= 45) & (df["Score"] < 70)]))
with c4:
    st.metric("⚠️ Verify Ownership", len(df[df["Ownership Flag"].notna()]))
with c5:
    st.metric("Has Census Data", len(df[df["Has PUF"]]))

st.markdown("---")

# ── Export ─────────────────────────────────────────────────────────────────────
export_df = df.drop(columns=["Signals", "Has PUF", "Has CAHPS"], errors="ignore")
csv_bytes = export_df.to_csv(index=False).encode()
st.download_button("⬇ Export CSV", csv_bytes, "hospice_targets.csv", "text/csv", use_container_width=False)

st.markdown(f"**{len(df)} providers** · click any row to expand details")

# ── Main Table ─────────────────────────────────────────────────────────────────
def render_label(label):
    if "HOT" in label: return f'<span class="hot">{label}</span>'
    if "WARM" in label: return f'<span class="warm">{label}</span>'
    return f'<span class="cold">{label}</span>'

def render_flag(flag):
    if pd.notna(flag) and flag:
        return f'<span class="flag">⚠️</span>'
    return ""

def render_indep(chain, flag):
    chain_val = str(chain).lower().strip() if pd.notna(chain) else ""
    is_indep = chain_val in ("", "no", "n", "nan")
    if flag and pd.notna(flag) and is_indep:
        return '<span style="color:#f59e0b;font-weight:700">?</span>'
    elif is_indep:
        return '<span style="color:#22c55e;font-weight:700">✓</span>'
    return '<span style="color:#ef4444;font-weight:700">✗</span>'

# Build display table
display_cols = ["Name", "State", "City", "Ownership", "Cert Year", "Stars", "HCI", "Est ADC", "Score", "Label", "Ownership Flag", "Chain"]

st.dataframe(
    df[display_cols].rename(columns={
        "Ownership Flag": "⚠️",
        "Cert Year": "Yr",
        "Est ADC": "ADC",
        "Ownership": "Type",
    }),
    use_container_width=True,
    height=480,
    column_config={
        "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=125, format="%d"),
        "ADC": st.column_config.NumberColumn("Est ADC", format="%.1f"),
        "⚠️": st.column_config.TextColumn("⚠️", width="small"),
        "Label": st.column_config.TextColumn("Tier", width="small"),
    },
    hide_index=True,
)

# ── Detail Expander ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔍 Provider Detail")

selected_name = st.selectbox(
    "Select provider to view details",
    options=df["Name"].tolist(),
    index=0 if len(df) > 0 else None,
    key="detail_select"
)

if selected_name:
    row = df[df["Name"] == selected_name].iloc[0]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"#### {row['Name']}")
        st.markdown(f"**{row['City']}, {row['State']}** · CCN: `{row['CCN']}`")

        if pd.notna(row.get("Ownership Flag")) and row["Ownership Flag"]:
            st.warning(f"⚠️ **Verify Ownership Before Outreach**\n\n{row['Ownership Flag']}")

        # Info grid
        info = {
            "Phone": row.get("Phone", "—"),
            "Ownership": row.get("Ownership", "—"),
            "Chain": row.get("Chain") or "Independent",
            "Certified": row.get("Cert Year", "—"),
            "Stars": f"{row['Stars']}★" if row['Stars'] not in ("—","nan","") else "No rating",
            "HCI Score": row.get("HCI", "—"),
            "Est. ADC": f"{row['Est ADC']:.1f} pts/day" if pd.notna(row.get("Est ADC")) else "No PUF data",
            "Est. Revenue": f"${row['Est Revenue ($k)']:.0f}k Medicare/yr" if pd.notna(row.get("Est Revenue ($k)")) else "No PUF data",
            "CAHPS": f"{row['CAHPS']}%" if pd.notna(row.get("CAHPS")) else "Not available",
        }
        cols = st.columns(3)
        for i, (k, v) in enumerate(info.items()):
            with cols[i % 3]:
                st.markdown(f"**{k}**  \n{v}")

    with col2:
        # Score badge
        score = row["Score"]
        label = row["Label"]
        color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 45 else "#475569"
        st.markdown(f"""
        <div style="background:{color}22;border:2px solid {color};border-radius:12px;padding:20px;text-align:center;margin-bottom:12px;">
          <div style="font-size:36px;font-weight:700;color:{color};">{score}</div>
          <div style="font-size:14px;font-weight:700;color:{color};">{label}</div>
          <div style="font-size:11px;color:#475569;margin-top:4px;">out of 125</div>
        </div>
        """, unsafe_allow_html=True)

    # Signals
    st.markdown("**Acquisition Signals**")
    signals = row["Signals"]
    if signals:
        for sig in signals:
            t = sig["type"]
            icon = "🔥" if t == "hot" else "✓" if t == "positive" else "⚠️" if t == "warn" else "·" if t == "neutral" else "✗"
            weight_str = f"+{sig['weight']}" if sig['weight'] > 0 else str(sig['weight'])
            color_str = "#ef4444" if t in ("hot","negative") else "#22c55e" if t == "positive" else "#f59e0b" if t == "warn" else "#94a3b8"
            st.markdown(f'<span style="color:{color_str}">{icon} {sig["label"]}</span> <span style="color:#374151;font-size:11px">({weight_str})</span>', unsafe_allow_html=True)
