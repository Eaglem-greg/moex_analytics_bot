def get_sectors():
    return ['Энергетика', 'Финансы', 'Металлы']

def get_sector_ticker(sector: str)->list:
    map = {
        "Энергетика": ["GAZP", "LKOH"],
        "Финансы": ["SBER", "VTBR"]
    }
    return map.get(sector, [])

def get_asset_type(ticker: str):
    map = {'GAZP': 'stocks'}
    return map.get(ticker, [])