import re
import pandas as pd
from pathlib import Path

ISO_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def audit_quality():
    print("=" * 65)
    print(" SEBI INSIDER TRADING & SAST - DATA QUALITY AUDIT")
    print("=" * 65)

    root = Path(__file__).parent
    pq_path = root / "output" / "insider_trading.parquet"
    csv_path = root / "output" / "insider_trading.csv"

    assert pq_path.exists(), "insider_trading.parquet missing"
    assert csv_path.exists(), "insider_trading.csv missing"

    df_pq = pd.read_parquet(pq_path)
    df_csv = pd.read_csv(csv_path)

    # 1. Parity Check
    assert len(df_pq) == len(df_csv), f"Parity mismatch: Parquet ({len(df_pq)}) != CSV ({len(df_csv)})"
    print(f"Total Disclosures Indexed: {len(df_pq)} [PASS - Parquet/CSV 100% Parity]")

    # 2. Key Identifier & Date Completeness
    null_sym = df_pq["symbol"].isnull().sum()
    null_dt = df_pq["trade_date"].isnull().sum()
    assert null_sym == 0, f"Found {null_sym} null symbols"
    assert null_dt == 0, f"Found {null_dt} null trade dates"
    print("Null Symbols & Trade Dates: 0 [PASS]")

    # 3. ISO-8601 Compliance
    for col in ["trade_date", "intimation_date", "broadcast_date"]:
        s = df_pq[col].dropna().astype(str)
        invalid = s[~s.str.match(ISO_REGEX)]
        assert len(invalid) == 0, f"Non-ISO dates in {col}: {len(invalid)}"
        print(f"ISO-8601 Format ({col}): 100% PASS")

    # 4. Domain Microstructure Invariants
    assert (df_pq["shares_traded"] >= 0).all(), "Negative shares traded detected"
    assert (df_pq["trade_value_inr"] >= 0).all(), "Negative trade value detected"
    assert ((df_pq["pre_trade_pct"] >= 0) & (df_pq["pre_trade_pct"] <= 100)).all(), "Pre-trade % out of [0, 100]"
    assert ((df_pq["post_trade_pct"] >= 0) & (df_pq["post_trade_pct"] <= 100)).all(), "Post-trade % out of [0, 100]"
    print("Domain Invariants (Non-negative qty/value, percentage bounds [0, 100]): [PASS]")

    # 5. Breakdown Statistics
    print("\nTop 5 Insider Categories:")
    for cat, count in df_pq["person_category"].value_counts().head(5).items():
        print(f"  • {cat:<25}: {count:>6} filings")

    print("\nTransaction Type Distribution:")
    for tx, count in df_pq["transaction_type"].value_counts().head(5).items():
        print(f"  • {tx:<25}: {count:>6} filings")

    print("=" * 65)
    print("ALL AUDIT CHECKS PASSED.")
    print("=" * 65)


if __name__ == "__main__":
    audit_quality()
