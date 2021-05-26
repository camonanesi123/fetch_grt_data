# -*- coding: utf-8 -*-
import requests
from decimal import Decimal
headers = {"Authorization": "Bearer YOUR API KEY"}
def fetch_sushi(thegraph_url):
    """Fetches thegraph Data.
    Retrieves price,c_supply,m_supply,mcap,fd_cap from coingecko
    Args:
        thegraph_url
    Returns:
       last 30days trading_volume | TVL
    Raises:
        Exception: An error occurred api request.
    """    
    query_data ="""
    {
        dayDatas(last: 30,orderBy:id,orderDirection:desc) {
  	        id
            date
            volumeUSD
            liquidityUSD
        }
    }
    """
    try:
        request = requests.post(thegraph_url, json={'query': query_data}, headers=headers)
        if request.status_code == 200:
            result = request.json()
            #print(result)
            trading_vl = Decimal(0).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
            last_day_tvl = result['data']['dayDatas'][0]['liquidityUSD']
            last_day_vl = result['data']['dayDatas'][0]['volumeUSD']
        #calculating from last day data to previous 30 days
        for i in range(0,30):
            volume = Decimal(result['data']['dayDatas'][i]['volumeUSD']).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
            trading_vl+=volume
        print(last_day_vl,last_day_tvl)
        return trading_vl,Decimal(last_day_vl).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
    except Exception as e:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query_data))

        
url = { 
    "FTM":"https://api.thegraph.com/subgraphs/name/sushiswap/fantom-exchange",
    "XDAI":"https://api.thegraph.com/subgraphs/name/sushiswap/xdai-exchange",
    "BSC":"https://api.thegraph.com/subgraphs/name/sushiswap/bsc-exchange",
    "MATIC":"https://api.thegraph.com/subgraphs/name/sushiswap/matic-exchange",
    "ETH":"https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
}

def sushi_total():
    #etherium
    a = fetch_sushi(url["ETH"])
    b = fetch_sushi(url["FTM"])
    #no liquidity or trading volume
    c = fetch_sushi(url["XDAI"])
    #no liquidity or trading volume
    d = fetch_sushi(url["BSC"])
    e = fetch_sushi(url["MATIC"])
    trading_volume = a[0]+b[0]+c[0]+d[0]+e[0]
    last_day_tvl= a[1]+b[1]+c[1]+d[1]+e[1]
    
    print("\n")
    print(trading_volume,last_day_tvl)
def main():
    sushi_total()


	
	
if __name__ == "__main__":
    main()