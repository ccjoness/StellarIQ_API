# import json
#
# import yfinance as yf
# symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN']
# company_info = yf.Tickers(symbols)
# # print(dir(company_info))
# symbol_dict = {}
# for symbol in symbols:
#     print(company_info.tickers[symbol].info.get('longName'))
#     # symbol_dict[symbol.info.get('symbol')] = symbol.info.get('longName')
#
# # print(json.dumps(symbol_dict, indent=4))
# # print(company_info.tickers['AAPL'].info.get('longName'))
# # for co in company_info:
# #     print(co)
# # print(company_info)
import json

# company_name = msft.info['longName']
#
# print(company_name)


from yahooquery import Ticker
ticker_list = ['AGMH', 'CJET', 'ARQQW', 'SAIHW', 'PLTS', 'ATMCW', 'CAPTW', 'OKLL', 'DFSCW', 'QUBX', 'DSYWW', 'FATN', 'PSQH+', 'OUSTW', 'CLNNW', 'SMUP', 'SMU', 'ATMV', 'EOSEW', 'QMCO', 'SHOTW', 'LSBPW', 'MYSEW', 'RVPH', 'BREA', 'SYTAW', 'LIMNW', 'ALTO', 'CREVW', 'MYPSW', 'RVPHW', 'QSIAW', 'NXLIW', 'AERTW', 'ADSEW', 'SABSW', 'ATCH', 'BTBDW', 'LSB', 'BNZIW', 'CJET', 'YAAS', 'ADAP', 'NVDA', 'OPEN', 'INTC', 'AGMH', 'HOOD', 'SNAP', 'WBD', 'AAPL', 'PLUG', 'BBAI', 'RAYA', 'HL', 'RGTI', 'SOXS', 'DNN', 'CPNG', 'PLTR']
all_symbols = " ".join(ticker_list)
ticker_info = Ticker(all_symbols)
ticker_info_dict = ticker_info.price
ticker_symbol_to_name_dict = {}

for ticker in ticker_list:
    try:
        longName = ticker_info_dict[ticker]['longName']
    except KeyError:
        longName = ticker
    ticker_symbol_to_name_dict[ticker] = longName

print(json.dumps(ticker_symbol_to_name_dict, indent=4))