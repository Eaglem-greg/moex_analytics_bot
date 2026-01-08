from flask import Flask, jsonify
from services.data_mapper import get_sectors, get_sector_ticker, get_asset_type

def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False

    @app.route('/sectors')
    def sectors():
        res = jsonify(get_sectors())
        res.headers["Content-Type"] = "application/json; charset=utf-8"
        return res
    
    @app.route('/sectors/<sector>/tickers')
    def tickers(sector: str):
        return jsonify(get_sector_ticker(sector))

    @app.route('/instruments/<ticker>/types')
    def types_asset(ticker: str):
        return jsonify(get_asset_type(ticker))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)