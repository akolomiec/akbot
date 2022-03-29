from binance.client import Client

api_key = '7tmGEBOvx4sxDPiH3lON1cNBFKrr6Dj41nRssuAbpQXrbfax9BWSjvCniWb9krsG'
api_secret = 'mTfx0ZF7z1DFk3bZSswrHjvsOKzkBghigRtVzTes0AdBVGjV7BPfB7EvEyaQez2P'


def main():
    client = Client(api_key, api_secret)
    klines = client.get_historical_klines("LRCUSDT", Client.KLINE_INTERVAL_30MINUTE, "22 Mar, 2022", "23 Mar, 2022")
    for l in klines:
        print(l)

if __name__ == "__main__":
    main()