from data.sectors_mapping import SECTORS_MAPPING
from services.moex_client import fetch_shares_securities

_catched_securities = None

def _get_all__shares():
    global _cached_securities
    if _catched_securities is None:
        _cached_securities = fetch_shares_securities()
    return _cached_securities

def get_sectors()->list:
    return list(SECTORS_MAPPING.keys())

def get_sector_ticker(sector: str)->list:
    target = SECTORS_MAPPING.get(sector)
    all_shares = _get_all__shares()
    moex_tickers = {i['ticker'] for i in all_shares}
    need_tickers = [i for i in target if i in moex_tickers]
    return need_tickers

def get_asset_type(ticker: str):
    all_shares = _get_all__shares()
    moex_tickers = {s['ticker'] for s in all_shares}
    if ticker in moex_tickers:
        return ["stock"]
    return []