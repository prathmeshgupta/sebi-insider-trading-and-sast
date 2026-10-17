"""
Automated Weekly Dataset Updater for sebi-insider-trading-and-sast
Can be executed locally or via GitHub Actions.
Zero credentials required.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
from sebi_insider_trading.fetcher import InsiderTradingFetcher

OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = OUTPUT_DIR / "insider_trading.csv"
PARQUET_FILE = OUTPUT_DIR / "insider_trading.parquet"


def update():
    print("[1/3] Fetching recent SEBI PIT insider trading disclosures from official NSE API...")
    fetcher = InsiderTradingFetcher()
    new_df = fetcher.fetch_disclosures()
    print(f"      Retrieved {len(new_df)} disclosures.")

    print("[2/3] Merging with historical disclosures archive...")
    if CSV_FILE.exists():
        existing_df = pd.read_csv(CSV_FILE)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df.copy()

    if not combined.empty:
        # Deduplicate by symbol, insider_name, trade_date, shares_traded, transaction_type
        dedup_keys = ["symbol", "insider_name", "trade_date", "shares_traded", "transaction_type"]
        combined = combined.drop_duplicates(subset=dedup_keys, keep="last")
        combined = combined.sort_values(by=["trade_date", "broadcast_date", "symbol"], ascending=[False, False, True])

        combined.to_csv(CSV_FILE, index=False)
        combined.to_parquet(PARQUET_FILE, index=False)
        print(f"      Saved {len(combined)} disclosures to {CSV_FILE.name} and {PARQUET_FILE.name}.")

    print("[3/3] Running automated quality audit...")
    from evaluate_quality import audit_quality
    audit_quality()
    print("Update complete successfully.")


if __name__ == "__main__":
    update()
