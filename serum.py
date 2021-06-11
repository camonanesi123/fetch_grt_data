#serum_dex
#serumswap
import requests
from decimal import Decimal
#serum tvl from https://defillama.com/protocol/serum
url ="https://api.llama.fi/protocol/serum"
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()
def serum_dex():
    res1 = cg.get_exchanges_by_id('serum_dex')
    volume_24_BTC_dex = res1['trade_volume_24h_btc']
    res2 = cg.get_exchanges_by_id('serumswap')
    volume_24_BTC_swap = res2['trade_volume_24h_btc']
    #get bitcoin price
    try:
      price = cg.get_coin_by_id('bitcoin')['market_data']['current_price']['usd']
    except Exception as e:
      print('Error:', e)
      price = 0   
    volume_24_USD = price*(volume_24_BTC_dex+volume_24_BTC_swap) 
    print(volume_24_USD)
    volume_24_USD=Decimal(volume_24_USD).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
    #get daily TVL 
    tvl = Decimal(0.00).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
    response1 = requests.get(url)
    if response1.status_code == 200:
        result = response1.json()
        #24 hours Volume
        tvl =  Decimal(result['tvl'][-1]['totalLiquidityUSD']).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
    print(tvl)
    return(tvl,volume_24_USD)
def main():
    serum_dex()
if __name__ == "__main__":
    main()