# -*- coding: utf-8 -*-
import requests
from decimal import Decimal
headers = {"Authorization": "Bearer YOUR API KEY"}
url='https://api.thegraph.com/subgraphs/name/developerfred/quick-swap'
def fetch_quickswap(url):
    """Fetches thegraph Data.
    Retrieves price,c_supply,m_supply,mcap,fd_cap from coingecko
    Args:
        token_name
    Returns:
       last 30days trading_volume | TVL
    Raises:
        Exception: An error occurred api request.
    """    
    #query data
    query_data = """
      {
      uniswapDayDatas(first: 30,orderBy:date,orderDirection:desc){
        id
        date
        dailyVolumeUSD
        totalLiquidityUSD
      }
      }
      """
    try:
      request = requests.post(url, json={'query': query_data}, headers=headers)
      if request.status_code == 200:
        result = request.json()
        trading_vl = Decimal(0).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
        last_day_tvl =Decimal(result['data']['uniswapDayDatas'][0]['totalLiquidityUSD']).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
      #calculating from last day data to previous 30 days
      for i in range(0,30):
          volume = Decimal(result['data']['uniswapDayDatas'][i]['dailyVolumeUSD']).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
          trading_vl+=volume
      print("quichswap : 30 days trading volume is {0} and today TVL is {1}".format(trading_vl,last_day_tvl))
      return trading_vl,last_day_tvl
    except Exception as e:
      raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query_data))

def main():
    fetch_quickswap(url)

if __name__ == "__main__":
    main()

