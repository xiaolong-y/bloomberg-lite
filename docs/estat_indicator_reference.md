# e-Stat Dashboard Indicator Code Reference

Quick reference for Japan economic indicators from the e-Stat Statistics Dashboard API.

## Active Indicators (Currently Implemented)

### GDP Indicators
| Metric | Indicator Code | Description | Frequency | Base Year |
|--------|---------------|-------------|-----------|-----------|
| japan.gdp_qoq | 0705020401000060000 | Real GDP, annualized QoQ% | Quarterly | 2015 |

### Labor Market
| Metric | Indicator Code | Description | Frequency |
|--------|---------------|-------------|-----------|
| japan.unemployment | 0301010000020020010 | Complete unemployment rate (both sexes) | Monthly |

### Industrial Production
| Metric | Indicator Code | Description | Frequency | Base Year |
|--------|---------------|-------------|-----------|-----------|
| japan.industrial_production | 0502070301000090010 | Mining & manufacturing production index | Monthly | 2020 |

## Available Indicators (Not Yet Implemented)

### GDP - Alternative Series
```
0705010401000010000  Nominal GDP (expenditure), 2015 base
0705010401000040000  Nominal GDP QoQ%, 2015 base
0705020401000010000  Real GDP (expenditure), 2015 base
0705020401000040000  Real GDP QoQ%, 2015 base
0705010001010010000  Nominal GDP (USD), all base years
0705020001010030000  Real GDP YoY% (USD)
```

### GDP Deflator
```
0705010404010010010  GDP deflator (nominal, chain method), 2015 base
0705010404010040010  GDP deflator QoQ%, 2015 base
```

### Industrial Production - Additional Indices
```
0502070302000090010  Industrial shipment index, 2020 base
0502070303000090010  Industrial inventory index, 2020 base
0502070304000090010  Industrial inventory ratio index, 2020 base
```

### Export/Import Price Indices
```
0703050201000090010  Export price index (yen base), 2010 base
0703050202000090010  Export price index (contract currency), 2010 base
0703050301000090010  Export price index (yen base), 2015 base
0703060201000090010  Import price index (yen base), 2010 base
0703060301000090010  Import price index (yen base), 2015 base
```

### Unemployment - Gender Breakdown
```
0301010001020020010  Unemployment rate (male)
0301010002020020010  Unemployment rate (female)
0301010000020010010  Total unemployed persons (both sexes)
```

## Indicator Code Structure

e-Stat indicator codes are 19 digits with the following structure:

```
[19-digit base code][cycle][region][adjustment]
```

### Cycle Codes (digits 20-21)
- `01` = Monthly
- `02` = Quarterly
- `03` = Calendar year (annual)
- `04` = Fiscal year (April-March for Japan)

### Regional Level (digits 22-23)
- `01` = Country (international comparison)
- `02` = Nationwide (Japan total)
- `03` = Prefecture level
- `04` = Municipal level

### Adjustment Type (digits 24-25)
- `01` = Original figures (not seasonally adjusted)
- `02` = Seasonally adjusted

## API Usage Examples

### Fetch GDP Data
```bash
curl "https://dashboard.e-stat.go.jp/api/1.0/Json/getData?IndicatorCode=0705020401000060000"
```

### Search for Indicators
```bash
curl "https://dashboard.e-stat.go.jp/api/1.0/Json/getIndicatorInfo?"
```

## Time Period Format

e-Stat uses special time period formats:

- Monthly: `YYYYMM00` (e.g., `202411M00` for November 2024)
- Quarterly: `YYYYNQ00` (e.g., `20243Q00` for Q3 2024)
- Annual (calendar): `YYYYCY00` (e.g., `2024CY00` for 2024)
- Annual (fiscal): `YYYYFY00` (e.g., `2024FY00` for FY2024, which is April 2024 - March 2025)

## Data Coverage Summary

Based on API exploration:

- **GDP series**: 34+ different measures (nominal, real, various base years)
- **Industrial production**: 12+ indices (production, shipment, inventory)
- **Price indices**: 20+ series (export, import, corporate goods)
- **Unemployment**: 25+ series (total, gender, age groups)
- **Total indicators**: ~6,000 across all categories

## Adding New Indicators

To add a new indicator to bloomberg-lite:

1. Find the indicator code using the API or documentation
2. Add to `config/metrics.yaml`:
```yaml
- id: japan.your_metric
  name: "Your Metric Name"
  source: estat_dashboard
  indicator_code: "your_19_digit_code_here"
  frequency: monthly  # or quarterly, annual
  unit: "%"  # or appropriate unit
  decimals: 1
```

3. Update the dashboard group in `metrics.yaml`:
```yaml
groups:
  - name: "Asia Pacific"
    metrics: [..., japan.your_metric]
```

4. Run the data pipeline: `python -m src.main`

## Resources

- **API Documentation**: https://dashboard.e-stat.go.jp/en/static/api
- **Main Portal**: https://www.e-stat.go.jp/en
- **Statistics Bureau**: https://www.stat.go.jp/english/
- **GitHub**: https://github.com/e-stat-api

## Notes

- No API key or authentication required
- API responses are in Japanese but data values are numeric
- Indicator names in responses use Japanese characters
- Historical data typically goes back several decades
- Updates are near real-time with official government releases
