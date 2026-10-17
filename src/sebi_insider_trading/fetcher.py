import datetime
import requests
import pandas as pd
from typing import Optional

NSE_PIT_URL = "https://www.nseindia.com/api/corporates-pit"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


class InsiderTradingFetcher:
    """
    Fetches official SEBI Prohibition of Insider Trading (PIT) Regulation 7(2) 
    and SAST disclosures from NSE India corporate filing API.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._primed = False

    def _prime_session(self):
        if not self._primed:
            try:
                self.session.get("https://www.nseindia.com", timeout=10)
            except Exception:
                pass
            self._primed = True

    def fetch_disclosures(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetches insider trading disclosures.
        If dates are provided ('DD-MM-YYYY'), queries that range.
        Otherwise queries the current and preceding calendar years.
        """
        self._prime_session()

        raw_records = []
        if from_date and to_date:
            ranges = [(from_date, to_date)]
        else:
            cur_year = datetime.datetime.now().year
            ranges = [
                (f"01-01-{cur_year-1}", f"31-12-{cur_year-1}"),
                (f"01-01-{cur_year}", f"31-12-{cur_year}")
            ]

        for f_dt, t_dt in ranges:
            params = {
                "index": "equities",
                "from_date": f_dt,
                "to_date": t_dt
            }
            try:
                resp = self.session.get(NSE_PIT_URL, params=params, timeout=25)
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    raw_records.extend(data)
            except Exception as e:
                print(f"Warning: Failed to fetch {f_dt} to {t_dt}: {e}")

        if not raw_records:
            return pd.DataFrame()

        df = pd.DataFrame(raw_records)

        def parse_iso(series):
            return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d")

        clean = pd.DataFrame()
        clean["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
        clean["company_name"] = df["company"].astype(str).str.strip()
        clean["insider_name"] = df["acqName"].astype(str).str.strip()
        clean["person_category"] = df["personCategory"].astype(str).str.strip()
        clean["transaction_type"] = df["tdpTransactionType"].astype(str).str.strip()
        clean["mode_of_acquisition"] = df["acqMode"].astype(str).str.strip()

        broadcast = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        t_date = parse_iso(df["acqtoDt"]).fillna(parse_iso(df["acqfromDt"])).fillna(broadcast)
        intim_date = parse_iso(df["intimDt"]).fillna(broadcast)

        clean["trade_date"] = t_date
        clean["intimation_date"] = intim_date
        clean["broadcast_date"] = broadcast

        clean["shares_traded"] = pd.to_numeric(df["secAcq"].astype(str).str.replace(",", ""), errors="coerce").fillna(0).astype("int64")
        clean["trade_value_inr"] = pd.to_numeric(df["secVal"].astype(str).str.replace(",", ""), errors="coerce").fillna(0.0)
        clean["pre_trade_pct"] = pd.to_numeric(df["befAcqSharesPer"].astype(str).str.replace(",", ""), errors="coerce").fillna(0.0)
        clean["post_trade_pct"] = pd.to_numeric(df["afterAcqSharesPer"].astype(str).str.replace(",", ""), errors="coerce").fillna(0.0)
        clean["regulation"] = df["anex"].astype(str).str.strip()
        clean["source"] = "NSE_PIT_DISCLOSURES"

        clean = clean.dropna(subset=["symbol", "trade_date"])
        clean = clean[clean["symbol"] != ""]
        return clean
