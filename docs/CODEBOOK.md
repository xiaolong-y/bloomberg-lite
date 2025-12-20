# Data Codebook

This document provides precise definitions and sources for all statistics displayed on the Bloomberg-Lite dashboard.

---

## Data Sources

| Source | API | Auth Required | Update Frequency |
|--------|-----|---------------|------------------|
| IMF DataMapper | `imf.org/external/datamapper/api` | No | Annual |
| ECB SDMX | `data-api.ecb.europa.eu` | No | Monthly/Daily |
| World Bank | `api.worldbank.org/v2` | No | Annual |
| Japan e-Stat | `dashboard.e-stat.go.jp/api` | No | Monthly/Quarterly |
| Yahoo Finance | `query1.finance.yahoo.com` | No | Daily |
| CoinGecko | `api.coingecko.com/api/v3` | No | Daily |
| Hacker News | `hacker-news.firebaseio.com` + `hn.algolia.com` | No | Real-time |

---

## US Economy

| Metric | Definition | Source | Indicator Code | Frequency |
|--------|------------|--------|----------------|-----------|
| **US GDP Growth** | Real GDP growth rate, annual percent change | IMF DataMapper | `NGDP_RPCH` / `USA` | Annual |
| **US Inflation** | Consumer price inflation, annual average percent change | IMF DataMapper | `PCPIPCH` / `USA` | Annual |
| **US Real Interest Rate** | Lending rate adjusted for inflation (nominal rate minus GDP deflator) | World Bank | `FR.INR.RINR` / `USA` | Annual |
| **US Unemployment** | Unemployment rate as percent of labor force | IMF DataMapper | `LUR` / `USA` | Annual |
| **US Gov Debt/GDP** | General government gross debt as percent of GDP | IMF DataMapper | `GGXWDG_NGDP` / `USA` | Annual |
| **US Current Account** | Current account balance as percent of GDP | IMF DataMapper | `BCA_NGDPD` / `USA` | Annual |

---

## Eurozone

| Metric | Definition | Source | Indicator Code | Frequency |
|--------|------------|--------|----------------|-----------|
| **EU GDP Growth** | Euro area real GDP growth rate | IMF DataMapper | `NGDP_RPCH` / `EUQ` | Annual |
| **EU HICP Inflation** | Harmonised Index of Consumer Prices, annual rate of change, all items | ECB SDMX | `ICP/M.U2.N.000000.4.ANR` | Monthly |
| **EU Policy Rate** | ECB Deposit Facility Rate (key policy rate) | ECB SDMX | `FM/B.U2.EUR.4F.KR.DFR.LEV` | Daily |
| **Germany Unemployment** | Unemployment rate, Germany (proxy for Eurozone) | IMF DataMapper | `LUR` / `DEU` | Annual |

---

## China

| Metric | Definition | Source | Indicator Code | Frequency |
|--------|------------|--------|----------------|-----------|
| **China GDP Growth** | Real GDP growth rate | IMF DataMapper | `NGDP_RPCH` / `CHN` | Annual |
| **China Inflation** | Consumer price inflation, annual average | IMF DataMapper | `PCPIPCH` / `CHN` | Annual |
| **China Real Rate** | Real interest rate (lending rate minus inflation) | World Bank | `FR.INR.RINR` / `CHN` | Annual |
| **China Unemployment** | Surveyed urban unemployment rate | IMF DataMapper | `LUR` / `CHN` | Annual |
| **China Current Account** | Current account balance as percent of GDP | IMF DataMapper | `BCA_NGDPD` / `CHN` | Annual |

---

## Japan

| Metric | Definition | Source | Indicator Code | Frequency |
|--------|------------|--------|----------------|-----------|
| **Japan GDP QoQ** | Quarterly GDP growth rate, seasonally adjusted | Japan e-Stat Dashboard | `0705020401000060000` | Quarterly |
| **Japan Inflation** | Consumer price inflation, annual average | IMF DataMapper | `PCPIPCH` / `JPN` | Annual |
| **Japan Real Rate** | Real interest rate | World Bank | `FR.INR.RINR` / `JPN` | Annual |
| **Japan Unemployment** | Seasonally adjusted unemployment rate | Japan e-Stat Dashboard | `0301010000020020010` | Monthly |
| **Japan Industrial Prod** | Industrial Production Index | Japan e-Stat Dashboard | `0502070301000090010` | Monthly |

---

## Global Markets

| Metric | Definition | Source | Ticker | Frequency |
|--------|------------|--------|--------|-----------|
| **S&P 500** | S&P 500 Index, major US equity benchmark | Yahoo Finance | `^GSPC` | Daily |
| **Brent Crude** | Brent crude oil futures price (USD per barrel) | Yahoo Finance | `BZ=F` | Daily |
| **Gold** | Gold futures price (USD per troy ounce) | Yahoo Finance | `GC=F` | Daily |
| **US Dollar Index** | Trade-weighted USD index (DXY) | Yahoo Finance | `DX-Y.NYB` | Daily |

---

## Crypto

| Metric | Definition | Source | Coin ID | Frequency |
|--------|------------|--------|---------|-----------|
| **Bitcoin** | Bitcoin price in USD | CoinGecko | `bitcoin` | Daily |
| **Ethereum** | Ethereum price in USD | CoinGecko | `ethereum` | Daily |

---

## News Feeds

| Feed | Definition | Source | Query/Endpoint | Time Window |
|------|------------|--------|----------------|-------------|
| **Tech** | Top 20 stories from HN homepage (algorithmic ranking) | HN Firebase | `topstories` | Real-time |
| **AI/ML** | Top AI-related stories by popularity | HN Algolia | `query="AI"`, `min_score=50` | 30 days |
| **Startups** | Top startup-related stories by popularity | HN Algolia | `query="startup"`, `min_score=30` | 30 days |

---

## Notes

1. **IMF DataMapper** provides forecasts for current and future years; historical data goes back to 1980.

2. **World Bank Real Interest Rate** is calculated as: lending rate minus inflation (GDP deflator). Data typically lags 2-3 years.

3. **ECB Policy Rate** shows the Deposit Facility Rate, which is the rate banks receive for overnight deposits with the ECB. This is the key rate used to implement monetary policy since 2022.

4. **Japan e-Stat** data is sourced from official Japanese government statistics (Statistics Bureau, Cabinet Office, METI).

5. **Sparklines** display the last 16 data points using Unicode braille patterns for 2x resolution.

6. **Change values** show period-over-period change where available (e.g., YoY for annual data, MoM for monthly).

---

## API Endpoints

```
IMF:        https://www.imf.org/external/datamapper/api/v1/{indicator}/{country}
ECB:        https://data-api.ecb.europa.eu/service/data/{dataflow}/{series_key}
World Bank: https://api.worldbank.org/v2/country/{country}/indicator/{indicator}
e-Stat:     https://dashboard.e-stat.go.jp/api/1.0/Json/getData?IndicatorCode={code}
Yahoo:      https://query1.finance.yahoo.com/v8/finance/chart/{ticker}
CoinGecko:  https://api.coingecko.com/api/v3/coins/{id}/market_chart
HN:         https://hacker-news.firebaseio.com/v0/topstories.json
Algolia:    https://hn.algolia.com/api/v1/search?query={query}
```
