import httpx

def fetch_shares_securities():
    url = "https://iss.moex.com/iss/engines/stock/markets/shares/securities.json"
    resp = httpx.get(url)
    resp.raise_for_status()
    data = resp.json()

    rows = data.get('securities', {}).get('data', [])
    columns = data.get('securities', {}).get('columns', [])
    name_candidates = ('NAME', 'SHORTNAME', 'NAME_FULL', 'SECNAME', 'TITLE')

    securities = []
    for row in rows:
        row_dict = dict(zip(columns, row))
        name = None
        for cand in name_candidates:
            if cand in row_dict and row_dict[cand] not in (None, ''):
                name = row_dict[cand]
                break
        if name is None:
            name = row_dict.get('SECID', '')

        securities.append({
            'ticker': row_dict.get('SECID'),
            'name': name
        })

    return securities