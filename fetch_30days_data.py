# request thegraph fetch uni daily data
import requests
from web3 import Web3
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()
infura_api = "https://mainnet.infura.io/v3/f4087772a79840a6b24442386b8d54d3"
headers = {"Authorization": "Bearer YOUR API KEY"}
import numpy as np
import pandas as pd
import gspread

res = pd.DataFrame(columns=('token_name', 'Price', 'Circulating supply','Max Supply','Market Cap','Fully Diluted Valuation','Volume (last30d)','Sales (30d - TT)','Annualized Sales','Token holders rewards','Earnings','TVL'))



# uniswap unified fee forumla
def uni_query(): #query uniswap_grt api
    #get price from coingecko
    p_uni = cg.get_coin_by_id('uniswap')['market_data']['current_price']['usd']
    #get circulting_supply
    c_uni= cg.get_coin_by_id('uniswap')['market_data']['circulating_supply']
    #get max_suply
    max_uni =  cg.get_coin_by_id('uniswap')['market_data']['max_supply']  
    #get market_cap
    mcap_uni = cg.get_coin_by_id('uniswap')['market_data']['market_cap']['usd']
    #fully dilute
    fd_uni = cg.get_coin_by_id('uniswap')['market_data']['fully_diluted_valuation']['usd']
    global res
    #query past 30 days uniswapDaily Date by block_number
    query2 = """
    {
    uniswapDayDatas(first: 30,block:{number:"""+str(indexed_block_num)+"""},orderBy:date,orderDirection:desc){
      id
      date
      dailyVolumeUSD
      totalLiquidityUSD
    }
    }
    """
    #begin fetching
    print(query2)
    request = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2', json={'query': query2}, headers=headers)
    if request.status_code == 200:
        result = request.json()
            #statistic daliy volume , daily tvl , daily fee.
        monthly_fee = 0
        sum_tvl =0
        trading_vl = 0
        for i in result['data']['uniswapDayDatas']:
            #print(i)
            volume = float(i['dailyVolumeUSD'])
            trading_vl+=volume
            monthly_fee+=volume*0.003
            sum_tvl += float(i['totalLiquidityUSD'])

        monthly_average_tvl = sum_tvl/30
        print('p_uni is {0}'.format(p_uni))
        print('c_uni is {0}'.format(c_uni))
        print('max_uni is {0}'.format(max_uni))
        print('mcap_uni is {0}'.format(mcap_uni))
        print('fd_uni is {0}'.format(fd_uni))
        print('30 days trading volume is {0}'.format(trading_vl))
        print("30 days daily average liquidity:{0}".format(monthly_average_tvl))
        print("last 30 days return:{0}".format(monthly_fee))
        predicted_yearly_fee = monthly_fee*12
        print("estimated annually return:{0}".format(predicted_yearly_fee))
        token_holder_rewards=0.1666666
        earnings = predicted_yearly_fee*token_holder_rewards
        print("earnings:{0}".format(earnings))
        res = res.append([{'token_name':'uni','Price':p_uni,'Circulating supply':c_uni,'Max Supply':max_uni,'Market Cap':mcap_uni,'Fully Diluted Valuation':fd_uni,'Volume (last30d)':trading_vl,'Sales (30d - TT)':monthly_fee,'Annualized Sales':predicted_yearly_fee,'Token holders rewards':token_holder_rewards,'Earnings':earnings,'TVL':monthly_average_tvl}], ignore_index=True)
        #print(res.head())
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

#balancer different pool different fee formula. here for simplification. revene = fee*0.003
def bal_query(): #query uniswap_grt api
    global res
    #get price from coingecko
    p_bal = cg.get_coin_by_id('balancer')['market_data']['current_price']['usd']
    #get circulting_supply
    c_bal= cg.get_coin_by_id('balancer')['market_data']['circulating_supply']
    #get max_suply
    max_bal =  cg.get_coin_by_id('balancer')['market_data']['max_supply']  
    #get market_cap
    mcap_bal = cg.get_coin_by_id('balancer')['market_data']['market_cap']['usd']
    #fully dilute
    fd_bal = cg.get_coin_by_id('balancer')['market_data']['fully_diluted_valuation']['usd']
    #30 days before blocknum = currently block_num - 6500*30
    month_before_block= indexed_block_num-195000
    bal_query = """
    {
      today_data:balancer(id:1,block:{number:"""+str(indexed_block_num)+"""}) {
        poolCount
        totalLiquidity
        totalSwapVolume
      }
      month_before_data:balancer(id:1,block:{number:"""+str(month_before_block)+"""}) {
        poolCount
        totalLiquidity
        totalSwapVolume
      }
    }
    """
    print(bal_query)
    request = requests.post('https://api.thegraph.com/subgraphs/name/balancer-labs/balancer', json={'query': bal_query}, headers=headers)
    if request.status_code == 200:
      result=request.json()
      #then calculate tvl and monthly trading volume
      tvl = result['data']['today_data']['totalLiquidity']
      trading_volume = result['data']['today_data']['totalSwapVolume']
      monthly_tv = float(result['data']['today_data']['totalSwapVolume'])-float(result['data']['month_before_data']['totalSwapVolume'])
      bal_monthly_fee = monthly_tv*0.003
      bal_monthly_revenue = bal_monthly_fee * 0.15
      print("balancer tvl is {0}".format(tvl))
      print("balancer monthly trading_volume is {0}".format(monthly_tv))
      print("balancer monthly fee is {0}".format(bal_monthly_fee))
      print("balancer monthly revenue is {0}".format(bal_monthly_revenue))
      print("balancer yearly approximately revenue is{0}".format(bal_monthly_revenue*12))

      res = res.append({'token_name':'bal','Price':p_bal,'Circulating supply':c_bal,'Max Supply':max_bal,'Market Cap':mcap_bal,'Fully Diluted Valuation':fd_bal,
        'Volume (last30d)':monthly_tv,'Sales (30d - TT)':bal_monthly_fee,'Annualized Sales':bal_monthly_fee*12,'Token holders rewards':0.15,'Earnings':bal_monthly_revenue*12,'TVL':tvl}, ignore_index=True)
      #print(res.head())
    else:
      raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, bal_query))

def dodo_query():
     #30 1619740800 统计 前30天 每天8:00 unix时间交易额
    month_before_block= indexed_block_num-195000
    #查询每天8点统计的昨天数据 86400
    dodo_query = """
    {
      pairDayDatas(where :{date:1619740800} ,orderBy:date,orderDirection:desc)
      {
        date
        id
        volumeUSD
        feeBase
        lpFeeRate
      }
    }
    """
    print(bal_query)
    request = requests.post('https://api.thegraph.com/subgraphs/name/dodoex/dodoex-v2', json={'query': dodo_query}, headers=headers)
    if request.status_code == 200:
      result=request.json()
      #then calculate tvl and monthly trading volume
      tvl = result['data']['today_data']['totalLiquidity']
      trading_volume = result['data']['today_data']['totalSwapVolume']
      monthly_tv = float(result['data']['today_data']['totalSwapVolume'])-float(result['data']['month_before_data']['totalSwapVolume'])
      bal_monthly_fee = monthly_tv*0.003
      bal_monthly_revenue = bal_monthly_fee * 0.15
      print("balancer tvl is {0}".format(tvl))
      print("balancer monthly trading_volume is {0}".format(monthly_tv))
      print("balancer monthly fee is {0}".format(bal_monthly_fee))
      print("balancer monthly revenue is {0}".format(bal_monthly_revenue))
      print("balancer yearly approximately revenue is{0}".format(bal_monthly_revenue*12))
    else:
      raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, bal_query)) 

#get current block number
w3 = Web3(Web3.HTTPProvider(infura_api))
block_num = w3.eth.block_number
#indexed block_num
indexed_block_num = block_num -5
print("begin to query from current block number {0} to past 30days data".format(block_num))

#get uni_data
uni_query()
#fetch bal_data
bal_query()

print(res)
#writting the res object to google sheet

gc = gspread.oauth()

wks = gc.open("test").sheet1

wks.update([res.columns.values.tolist()] + res.values.tolist())