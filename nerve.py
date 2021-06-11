#nerve data from dapper
import requests
from decimal import Decimal
headers = { "Accept":"text/html,application/xhtml+xml,application/xml;",
      "Accept-Encoding":"gzip",
      "Accept-Language":"zh-CN,zh;q=0.8",
      "Referer":"http://www.example.com/",
      "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
      }
url = "https://dappradar.com/v2/api/dapp/binance-smart-chain/exchanges/nerve/statistic/24h"
def nerve():
  response1 = requests.get(url,headers=headers)
  Tvl =""
  tr = ""
  print(response1)
  if response1.status_code == 200:
    result = response1.json()
    #print(result)
    Tvl=result['totalBalanceInUsdLabel']
    Tvl=Tvl.replace("$","")
    Tvl=Tvl.replace(",","")
    Tvl=Decimal(Tvl).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
    #24 hours Volume
    tr=result['totalVolumeInUSDLabel']
    tr=tr.replace("$","")
    tr=tr.replace(",","")
    tr=Decimal(tr).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
  print(Tvl,tr)
  return Tvl,tr
def main():
    nerve()

if __name__ == "__main__":
    main()