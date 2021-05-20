# request thegraph fetch uni daily data
from os import terminal_size
import requests
from requests.api import request
from web3 import Web3
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()
infura_api = "https://mainnet.infura.io/v3/f4087772a79840a6b24442386b8d54d3"
headers = {"Authorization": "Bearer YOUR API KEY"}
import numpy as np
import pandas as pd
import gspread

import time,datetime
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
    
    #print(price,c_supply,m_supply,mcap,fd_cap)
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
def dodo_query():
    global res
    #get price from coingecko
    tup1 = query_coingecko('dodo')  
    p_dodo = tup1[0]
    c_dodo= tup1[1]
    max_dodo = tup1[2]
    mcap_dodo = tup1[3]
    fd_dodo = tup1[4]
    print(tup1)
    #get trading volue and TVL from dodo API
    variables = dict({
  "lastId": "",
  "first": 1000
        })
    dodo_tvl_query = """
    query FetchTVL($first: Int, $lastId: String) {
      pairDayDatas(
        first: $first
        where: {id_gt: $lastId, volumeUSD_gt: 1000, txns_gt: 10}
      ) {
        id
        pairAddress
        date
        baseToken {
          usdPrice
          symbol
          __typename
        }
        baseTokenReserve
        quoteToken {
          usdPrice
          symbol
          __typename
        }
        quoteTokenReserve
        pair {
          lastTradePrice
          __typename
        }
        __typename
      }
    }
    """
    #print(dodo_tvl_query)
    # 获取TVL
    response = requests.post('https://api.thegraph.com/subgraphs/name/dodoex/dodoex-v2', json={'query': dodo_tvl_query,"operationName": "FetchTVL", 'variables':variables}, headers=headers)
    Tvl = 0
    if response.status_code == 200:
        result = response.json()
        while(len(result['data']['pairDayDatas'])!=0):
          for pair in result['data']['pairDayDatas']:
            #获取当天 UTC 0 时间的统计数据
            now_time = int(time.time())
            day_time = now_time - (now_time)%86400
            #print(day_time)
            if pair['date'] == day_time:
              bst_price = float(pair['baseToken']['usdPrice'])
              bst_reserve = float(pair['baseTokenReserve'])
              quote_price = float(pair['quoteToken']['usdPrice'])
              quote_reserve =float(pair['quoteTokenReserve'])
              pair_value= bst_price*bst_reserve + quote_price*quote_reserve
              Tvl+=pair_value
          #记录最后一个id号 重新修改传入参数
          last_id = result['data']['pairDayDatas'][-1]['id']
          variables['lastId']=last_id
          response = requests.post('https://api.thegraph.com/subgraphs/name/dodoex/dodoex-v2', json={'query': dodo_tvl_query,"operationName": "FetchTVL", 'variables':variables}, headers=headers)
          result = response.json()
    print("Total Value Locked is:",Tvl)

    #当前块高度的所有交易量之和，减去24小时之前块高度的交易量之和。等于当日交易额
    month_before_block= indexed_block_num-180000
    variables = {
      "lastId": "",
      "first": 1000,
      "blockHeight": indexed_block_num
    }
    dodo_tv_query = """
    query FetchVolume($first: Int, $blockHeight: Int, $lastId: String) {
      tokens(
        first: $first
        where: {volumeUSD_gt: 1000, id_gt: $lastId}
        block: {number: $blockHeight}
      ) {
        id
        symbol
        volumeUSD
        usdPrice
        tradeVolume
        __typename
      }
    }
    """
    response = requests.post('https://api.thegraph.com/subgraphs/name/dodoex/dodoex-v2', json={'query': dodo_tv_query,"operationName": "FetchVolume", 'variables':variables}, headers=headers)
    trd_vol = 0
    if response.status_code == 200:
      result = response.json()
      while(len(result['data']['tokens'])!=0):
        for token in result['data']['tokens']:
          volumeUSD = float(token['volumeUSD'])
          trd_vol+=volumeUSD
        #记录最后一个id号 重新修改传入参数
        last_id = result['data']['tokens'][-1]['id']
        variables['lastId']=last_id
        response = requests.post('https://api.thegraph.com/subgraphs/name/dodoex/dodoex-v2', json={'query': dodo_tv_query,"operationName": "FetchTVL", 'variables':variables}, headers=headers)
        result = response.json()
    print("Currently Block total trading volume is: ",trd_vol)

    variables = {
      "lastId": "",
      "first": 1000,
      "blockHeight": month_before_block
    }
    response = requests.post('https://api.thegraph.com/subgraphs/name/dodoex/dodoex-v2', json={'query': dodo_tv_query,"operationName": "FetchVolume", 'variables':variables}, headers=headers)
    trd_vol1 = 0
    if response.status_code == 200:
      result = response.json()
      while(len(result['data']['tokens'])!=0):
        for token in result['data']['tokens']:
          volumeUSD = float(token['volumeUSD'])
          trd_vol1+=volumeUSD
        #记录最后一个id号 重新修改传入参数
        last_id = result['data']['tokens'][-1]['id']
        variables['lastId']=last_id
        response = requests.post('https://api.thegraph.com/subgraphs/name/dodoex/dodoex-v2', json={'query': dodo_tv_query,"operationName": "FetchTVL", 'variables':variables}, headers=headers)
        result = response.json()
    print("One month before total trading volume is: ",trd_vol1)
    #should divided two becauese of double counting
    trade_volume_USD = (trd_vol-trd_vol1)/2
    print('One month Dodo exchange trading volume is:',trade_volume_USD)
    dodo_fee_revenue = trade_volume_USD*0.003
    Annualized_Sales = dodo_fee_revenue*12
    Token_holders_rewards=0.15
    Earnings = Annualized_Sales*Token_holders_rewards

    res = res.append([{'token_name':'dodo','Price':tup1[0],'Circulating supply':tup1[1],'Max Supply':tup1[2],'Market Cap':tup1[3],'Fully Diluted Valuation':tup1[4],'Volume (last30d)':trade_volume_USD,'Sales (30d - TT)':dodo_fee_revenue,'Annualized Sales':Annualized_Sales,'Token holders rewards':Token_holders_rewards,'Earnings':Earnings,'TVL':Tvl}], ignore_index=True)
def bancor_query():
    global res
    tup1 = query_coingecko('bancor')
    p_bnt = tup1[0]
    c_bnt= tup1[1]
    max_bnt = tup1[2]
    mcap_bnt = tup1[3]
    fd_bnt = tup1[4]
    url = 'https://api-v2.bancor.network/welcome'
    response = requests.get(url)
    Tvl = 0
    tr=0
    if response.status_code == 200:
        result = response.json()
        Tvl = float(result['total_liquidity']['usd'])
        tr = float(result['total_volume_24h']['usd'])
    print(tup1)
    print(Tvl)
    trade_volume_USD=tr*30
    fee_revenue=trade_volume_USD*0.003
    Annualized_Sales=fee_revenue*12
    Token_holders_rewards =0.15
    Earnings=Token_holders_rewards*Annualized_Sales
    res = res.append([{'token_name':'bancor','Price':tup1[0],'Circulating supply':tup1[1],'Max Supply':tup1[2],'Market Cap':tup1[3],'Fully Diluted Valuation':tup1[4],'Volume (last30d)':trade_volume_USD,'Sales (30d - TT)':fee_revenue,'Annualized Sales':Annualized_Sales,'Token holders rewards':Token_holders_rewards,'Earnings':Earnings,'TVL':Tvl}], ignore_index=True)
def curve_query():
  global res
  tvl_url = 'https://api.curve.fi/api/getTVL'
  daily_volume = 'https://api.curve.fi/api/getFactoryAPYs'
  #get coingecko data
  global res
  tup1 = query_coingecko('bancor')
  p_crv = tup1[0]
  c_crv= tup1[1]
  max_crv = tup1[2]
  mcap_crv = tup1[3]
  fd_crv = tup1[4]
  Tvl = 0
  tr = 0
  response1 = requests.get(tvl_url)
  if response1.status_code == 200:
    result = response1.json()
    #print(result)
    Tvl = result['data']['tvl']
  response2 = requests.get(daily_volume)
  if response2.status_code == 200:
    result = response2.json()
    #print(result)
    tr = result['data']['totalVolume']
  
  print(Tvl)
  print(tr)
  trade_volume_USD=tr*30
  fee_revenue=trade_volume_USD*0.0004
  Annualized_Sales=fee_revenue*12
  Token_holders_rewards =0.5
  Earnings=Token_holders_rewards*Annualized_Sales
  res = res.append([{'token_name':'curve','Price':tup1[0],'Circulating supply':tup1[1],'Max Supply':tup1[2],'Market Cap':tup1[3],'Fully Diluted Valuation':tup1[4],'Volume (last30d)':trade_volume_USD,'Sales (30d - TT)':fee_revenue,'Annualized Sales':Annualized_Sales,'Token holders rewards':Token_holders_rewards,'Earnings':Earnings,'TVL':Tvl}], ignore_index=True)
def oneinch_query():
  global res
  tup1 = query_coingecko('1inch')
  pair1_url = 'https://governance.1inch.exchange/v1.0/protocol/pairs'
  pair2_url = 'https://governance.1inch.exchange/v1.1/protocol/pairs'
  response1 = requests.get(pair1_url)
  Tvl = 0
  tr = 0 
  if response1.status_code == 200:
    result = response1.json()
    #print(result)
    print(len(result))
    for pair in result:
      Tvl+=float(pair['reserveUSD'])
      tr+=float(pair['volumeUSD24h'])
  response1 = requests.get(pair2_url)
  Tvl = 0
  tr = 0 
  if response1.status_code == 200:
    result = response1.json()
    #print(result)
    print(len(result))
    for pair in result:
      Tvl+=float(pair['reserveUSD'])
      tr+=float(pair['volumeUSD24h'])
     
  print(Tvl)
  print(tr)
  trade_volume_USD=tr*30
  fee_revenue=trade_volume_USD*0.0044
  Annualized_Sales=fee_revenue*12
  Token_holders_rewards =0.0976
  Earnings=Token_holders_rewards*Annualized_Sales
  res = res.append([{'token_name':'1inch','Price':tup1[0],'Circulating supply':tup1[1],'Max Supply':tup1[2],'Market Cap':tup1[3],'Fully Diluted Valuation':tup1[4],'Volume (last30d)':trade_volume_USD,'Sales (30d - TT)':fee_revenue,'Annualized Sales':Annualized_Sales,'Token holders rewards':Token_holders_rewards,'Earnings':Earnings,'TVL':Tvl}], ignore_index=True)
def zeroX_quer():
  #0x
  pass
#get current block number
w3 = Web3(Web3.HTTPProvider(infura_api))
block_num = w3.eth.block_number
#indexed block_num
indexed_block_num = block_num -5
print("begin to query from current block number {0} to past 30days data".format(block_num))
curve_query()
oneinch_query()
bancor_query()
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

print('fetch dodo ..................')
dodo_query()
print(res)

print('fetch balancer ..................')
bal_query()

gc = gspread.oauth()

wks = gc.open("test").sheet1

wks.update([res.columns.values.tolist()] + res.values.tolist())