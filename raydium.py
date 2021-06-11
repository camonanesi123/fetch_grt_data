
import requests
from decimal import Decimal
#raydium only has 24h volume data. we premise that its monthly data is 30* volume_24h

url ="https://api.raydium.io/info"
def raydium(url):
  response1 = requests.get(url)
  Tvl = 0
  tr = 0 
  if response1.status_code == 200:
    result = response1.json()
    Tvl+=float(result['tvl'])
    #24 hours Volume
    tr+=float(result['volume24h'])
  volume_monthly= tr*30
  print(Tvl,tr)
  return Tvl,tr
def main():
    raydium(url)

if __name__ == "__main__":
    main()