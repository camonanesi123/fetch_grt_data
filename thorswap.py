import requests
from decimal import Decimal
tvl_url ="https://midgard.thorchain.info/v2/history/tvl?interval=day&count=100"
trading_volume_url = "https://midgard.thorchain.info/v2/history/swaps?interval=day&count=100"

# they calculate tvl using rune current price.
# the data denominal is rune
def thorswap():
  response1 = requests.get(tvl_url)
  Tvl = 0
  if response1.status_code == 200:
    result = response1.json()
    tvl_rune = Decimal(result['intervals'][-1]["totalValuePooled"]).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")/(10**8)
    price_rune = Decimal(result['intervals'][-1]["runePriceUSD"]).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
    Tvl = tvl_rune*price_rune
    print(Tvl)
  return Tvl

def torswap_volume():
  response1 = requests.get(trading_volume_url)
  past_30_days_volume = Decimal(0).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
  if response1.status_code == 200:
    result = response1.json()
    price_rune = Decimal(result['intervals'][-1]["runePriceUSD"]).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")
    list = result['intervals']
    list.reverse()
    #print(list)
    for i in range(1,31):
        past_30_days_volume +=Decimal(list[i]["totalVolume"]).quantize(Decimal("0.01"), rounding = "ROUND_HALF_UP")/(10**8)
    volume_usd = past_30_days_volume*price_rune
  print(volume_usd)
  return volume_usd
def main():
    thorswap()
    torswap_volume()
if __name__ == "__main__":
    main()