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

# result of date 
res = pd.DataFrame(columns=('token_name', 'Price', 'Circulating supply','Max Supply','Market Cap','Fully Diluted Valuation','Volume (last30d)','Sales (30d - TT)','Annualized Sales','Token holders rewards','Earnings','TVL'))
graph_url = {
  'uni':"https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2",
  'pancake':"https://api.thegraph.com/subgraphs/name/pancakeswap/exchange",
  'sushi':"https://api.thegraph.com/subgraphs/name/croco-finance/sushiswap",
  'mDex':"https://graph.mdex.cc/subgraphs/name/mdex/swap",
  'balancer':"https://api.thegraph.com/subgraphs/name/balancer-labs/balancer",
  'bancor':"https://api.thegraph.com/subgraphs/name/blocklytics/bancor"
}

def query_coingecko(token_name):
    """Fetches Coingecko Data.
    Retrieves price,c_supply,m_supply,mcap,fd_cap from coingecko
    Args:
        token_name
    Returns:
       price,c_supply,m_supply,mcap,fd_cap from coingecko
    Raises:
        Exception: An error occurred api request.
    """    
    try:
      price = cg.get_coin_by_id(token_name)['market_data']['current_price']['usd']
    except Exception as e:
      print('Error:', e)
      price = None    

    #get circulting_supply
    try:
      c_supply= cg.get_coin_by_id(token_name)['market_data']['circulating_supply']
    except Exception as e:
      print('Error:', e)
      c_supply = None   
    #get max_suply
    try:
      m_supply =  cg.get_coin_by_id(token_name)['market_data']['max_supply']  
    except Exception as e:
      print('Error:', e)
      m_supply = None  
    #get market_cap
    try:
      mcap = cg.get_coin_by_id(token_name)['market_data']['market_cap']['usd']
    except Exception as e:
      print('Error:', e)
      mcap = None    
      #fully dilute
    try:
      fd_cap = cg.get_coin_by_id(token_name)['market_data']['fully_diluted_valuation']['usd']
    except Exception as e:
      print('Error:', e)
      fd_cap = None
      
    return (price,c_supply,m_supply,mcap,fd_cap)
# uniswap unified fee forumla

def bal_query(): #query uniswap_grt api
    global res
    #get price from coingecko
    tup1 = query_coingecko('balancer')
    p_bal = tup1[0]
    c_bal= tup1[1]
    max_bal = tup1[2]
    mcap_bal = tup1[3]
    fd_bal = tup1[4]
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

def fetch_thegrahp(token_name):
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
      uniswapDayDatas(first: 31,orderBy:date,orderDirection:desc){
        id
        date
        dailyVolumeUSD
        totalLiquidityUSD
      }
      }
      """
    url = graph_url[token_name]
    try:
      request = requests.post(url, json={'query': query_data}, headers=headers)
      if request.status_code == 200:
        result = request.json()
        trading_vl = 0
        last_day_tvl = result['data']['uniswapDayDatas'][1]['totalLiquidityUSD']
      #calculating from last day data to previous 30 days
      for i in range(1,31):
          volume = float(result['data']['uniswapDayDatas'][i]['dailyVolumeUSD'])
          trading_vl+=volume
      return trading_vl,last_day_tvl
    except Exception as e:
      raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

#get current block number
w3 = Web3(Web3.HTTPProvider(infura_api))
block_num = w3.eth.block_number
#indexed block_num
indexed_block_num = block_num -5
print("begin to query from current block number {0} to past 30days data".format(block_num))

#bal_query()



print('fetch pancake ..................')
tup1 = query_coingecko('pancakeswap-token')
print(tup1)
tup2 = fetch_thegrahp('pancake')
monthly_fee=tup2[0]*0.002
predicted_yearly_fee = monthly_fee*12
token_holder_rewards=0.15
earnings = predicted_yearly_fee*token_holder_rewards
res = res.append([{'token_name':'pancake','Price':tup1[0],'Circulating supply':tup1[1],'Max Supply':tup1[2],'Market Cap':tup1[3],'Fully Diluted Valuation':tup1[4],'Volume (last30d)':tup2[0],'Sales (30d - TT)':monthly_fee,'Annualized Sales':predicted_yearly_fee,'Token holders rewards':token_holder_rewards,'Earnings':earnings,'TVL':tup2[1]}], ignore_index=True)
print(res)
print('fetch uni ..................')
tup1 = query_coingecko('uniswap')
tup2 = fetch_thegrahp('uni')
monthly_fee=tup2[0]*0.003
predicted_yearly_fee = monthly_fee*12
token_holder_rewards=0.1666666
earnings = predicted_yearly_fee*token_holder_rewards
res = res.append([{'token_name':'uni','Price':tup1[0],'Circulating supply':tup1[1],'Max Supply':tup1[2],'Market Cap':tup1[3],'Fully Diluted Valuation':tup1[4],'Volume (last30d)':tup2[0],'Sales (30d - TT)':monthly_fee,'Annualized Sales':predicted_yearly_fee,'Token holders rewards':token_holder_rewards,'Earnings':earnings,'TVL':tup2[1]}], ignore_index=True)
print(res)

print('fetch sushi ..................')
tup1 = query_coingecko('sushi')
tup2 = fetch_thegrahp('sushi')
monthly_fee=tup2[0]*0.003
predicted_yearly_fee = monthly_fee*12
token_holder_rewards=0.1666666
earnings = predicted_yearly_fee*token_holder_rewards
res = res.append([{'token_name':'sushi','Price':tup1[0],'Circulating supply':tup1[1],'Max Supply':tup1[2],'Market Cap':tup1[3],'Fully Diluted Valuation':tup1[4],'Volume (last30d)':tup2[0],'Sales (30d - TT)':monthly_fee,'Annualized Sales':predicted_yearly_fee,'Token holders rewards':token_holder_rewards,'Earnings':earnings,'TVL':tup2[1]}], ignore_index=True)
print(res)

print('fetch mdex ..................')
tup1 = query_coingecko('mdex')
tup2 = fetch_thegrahp('mDex')
monthly_fee=tup2[0]*0.003
predicted_yearly_fee = monthly_fee*12
token_holder_rewards=0.14
earnings = predicted_yearly_fee*token_holder_rewards
res = res.append([{'token_name':'mdex','Price':tup1[0],'Circulating supply':tup1[1],'Max Supply':tup1[2],'Market Cap':tup1[3],'Fully Diluted Valuation':tup1[4],'Volume (last30d)':tup2[0],'Sales (30d - TT)':monthly_fee,'Annualized Sales':predicted_yearly_fee,'Token holders rewards':token_holder_rewards,'Earnings':earnings,'TVL':tup2[1]}], ignore_index=True)
print(res)

print('fetch bancor ..................')
#not a same skema

print('fetch balancer ..................')
bal_query()

gc = gspread.oauth()

wks = gc.open("test").sheet1

wks.update([res.columns.values.tolist()] + res.values.tolist())