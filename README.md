# SEBI Insider Trading & SAST Disclosures Dataset (NSE)

[![Weekly Update](https://github.com/prathmeshgupta/sebi-insider-trading-and-sast/actions/workflows/update.yml/badge.svg)](https://github.com/prathmeshgupta/sebi-insider-trading-and-sast/actions/workflows/update.yml)
[![Format: Parquet](https://img.shields.io/badge/Format-Apache%20Parquet-blue.svg)](output/insider_trading.parquet)
[![Format: CSV](https://img.shields.io/badge/Format-CSV-green.svg)](output/insider_trading.csv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An institutional, automated, point-in-time quantitative dataset capturing official **SEBI Prohibition of Insider Trading (PIT) Regulation 7(2)** and **SAST (Substantial Acquisition of Shares and Takeovers) Regulation 29** filings across all National Stock Exchange of India (NSE) listed equities.

In Indian small-and-mid-cap quantitative strategies, open-market promoter/director acquisitions represent one of the highest information-coefficient (IC) signals of operational health and skin-in-the-game conviction.

---

## Dataset Schema (`output/insider_trading.parquet` / `.csv`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `symbol` | `string` | NSE listed equity ticker (e.g. `POONAWALLA`, `MAHICKRA`) |
| `company_name` | `string` | Official corporate entity name |
| `insider_name` | `string` | Full name of the transacting promoter, director, or KMP |
| `person_category` | `string` | Filer category (`Promoters`, `Director`, `Key Managerial Personnel`, etc.) |
| `transaction_type` | `string` | Direction of trade (`Buy`, `Sell`, `Pledge`, `Revoke`, `Pledge Release`) |
| `mode_of_acquisition` | `string` | Mode (`Market Purchase`, `Market Sale`, `ESOP`, `Off Market`, `Inter-se Transfer`) |
| `trade_date` | `string` | ISO-8601 execution date (`YYYY-MM-DD`) |
| `intimation_date` | `string` | ISO-8601 date when insider notified the exchange (`YYYY-MM-DD`) |
| `broadcast_date` | `string` | ISO-8601 exchange public broadcast date (`YYYY-MM-DD`) |
| `shares_traded` | `int64` | Total volume of securities transacted |
| `trade_value_inr` | `float64` | Gross monetary transaction value in INR |
| `pre_trade_pct` | `float64` | Filer's percentage equity holding prior to transaction |
| `post_trade_pct` | `float64` | Filer's percentage equity holding following transaction |
| `regulation` | `string` | SEBI Regulatory clause (`7(2)` PIT vs `29` SAST) |
| `source` | `string` | Source provenance identifier (`NSE_PIT_DISCLOSURES`) |

---

## Quick Start (Python / Polars / DuckDB)

```python
import polars as pl

# 1. Read directly from GitHub Raw Parquet
url = "https://github.com/prathmeshgupta/sebi-insider-trading-and-sast/raw/main/output/insider_trading.parquet"
df = pl.read_parquet(url)

# 2. Filter for significant open-market promoter purchases (> 50 Lakhs INR)
promoter_buys = df.filter(
    (pl.col("person_category") == "Promoters") &
    (pl.col("transaction_type") == "Buy") &
    (pl.col("mode_of_acquisition") == "Market Purchase") &
    (pl.col("trade_value_inr") >= 5_000_000)
)
print(promoter_buys.select(["trade_date", "symbol", "insider_name", "shares_traded", "trade_value_inr"]))
```

---

## Automated Weekly Ingestion & Quality Circuit Breaker

Updates run automatically via GitHub Actions every weekend with zero credentials:
1. Ingests all fresh disclosures from official NSE regulatory endpoints.
2. Formats all timestamps to strict ISO-8601 (`YYYY-MM-DD`).
3. Runs `evaluate_quality.py` to enforce row-parity, non-negativity, and percentage bounds.
4. Auto-commits and pushes updated `.parquet` and `.csv` files.
