# Hospice Target Screener — Willowbridge Capital

Scores and ranks for-profit hospice acquisition targets across ID, UT, NV, MT, WY, CO, AZ, TX, OK.

## Data
Default data is baked in (`data/` folder):
- `general.csv` — CMS Hospice General Information (Feb 2026)
- `puf.csv` — Medicare PAC PUF Hospice 2023

Upload fresher CSVs via the sidebar to refresh without redeploying.

## Scoring (0–125)
| Signal | Points |
|---|---|
| Independent operator | +30 |
| Chain-affiliated | -20 |
| Cert age ≤2005 | +25 |
| Cert age ≤2010 | +20 |
| Cert age ≤2015 | +14 |
| Low stars (1-2★) | +25 |
| High stars (4-5★) | +15 |
| No star rating | +12 |
| Low HCI (<6) | +20 |
| Est. ADC 10–50 | +15 |
| Low CAHPS (<70%) | +15 |

**HOT ≥ 70 · WARM ≥ 45**

## Deploy
Push to GitHub → connect to [Streamlit Community Cloud](https://streamlit.io/cloud) → deploy.
