import unittest
import akbot
import order
import os
from unittest import IsolatedAsyncioTestCase
from binance import AsyncClient

events = []


class Test(IsolatedAsyncioTestCase):

    def setUp(self):
        events.append("setUp")

    async def asyncSetUp(self):
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('API_SECRET')
        self.client = await AsyncClient.create(self.api_key, self.api_secret)
        self.trader = akbot.Trader()

        events.append("asyncSetUp")

    async def test_get_btc_price_dict(self):
        events.append("test_get_btc_price_dict")
        btcusdt = "BTCUSDT"
        btc = await self.client.get_ticker(symbol=btcusdt)
        self.assertEqual(dict, type(btc))

    async def test_get_btc_price_greater_null(self):
        events.append("test_get_btc_price_greater_null")
        btcusdt = "BTCUSDT"
        btc = await self.client.get_ticker(symbol=btcusdt)
        self.assertGreater(float(btc["lastPrice"]), 0)


    async def test_calculate_quantity_btc(self):
        events.append("test_calculate_quantity_btc")
        asset = "BTC"
        min_order = 11
        cur_price = 0.0006821
        step_size = 0.01
        quantity = await self.trader.calculate_quantity(self.client, asset, min_order, cur_price, step_size)
        self.assertEqual(0.37, quantity)

    async def test_calculate_quantity_usdt(self):
        events.append("test_calculate_quantity_btc")
        asset = "USDT"
        min_order = 11
        cur_price = 0.00002504
        step_size = 1
        quantity = await self.trader.calculate_quantity(self.client, asset, min_order, cur_price, step_size)
        self.assertEqual(439297.0, quantity)

    def tearDown(self):
        events.append("tearDown")

    async def asyncTearDown(self):
        await self.client.close_connection()
        events.append("asyncTearDown")


class TraderTestCase(unittest.TestCase):
    def test_get_whitelist(self):
        list_etalon = ["1INCH", "AAVE", "ADA"]

        trader = akbot.Trader()
        trader.whitelist_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\whitelist.txt"
        list_result = trader.get_whitelist()
        self.assertEqual(list_etalon, list_result)

    def test_set_whitelist(self):
        list_etalon = ['AXS', 'BAT', 'BCD', 'BCH', 'BICO', 'BNB', 'BTCST', 'BTG', 'CAKE', 'CELO']
        trader = akbot.Trader()
        trader.whitelist_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\whitelist2.txt"
        whitelist = "AXS BAT BCD BCH BICO BNB BTCST BTG CAKE CELO"
        trader.set_whitelist(whitelist=whitelist)
        list_result = trader.get_whitelist()
        self.assertEqual(list_etalon, list_result)

    def test_get_whitelist_file_not_found(self):
        trader = akbot.Trader()
        trader.whitelist_filename = "E:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\w.txt"
        whitelist = "AXS BAT BCD BCH BICO BNB BTCST BTG CAKE CELO"
        with self.assertRaises(FileNotFoundError) as cm:
            trader.set_whitelist(whitelist=whitelist)
        the_exception = cm.exception
        self.assertEqual(the_exception.strerror, 'No such file or directory')
        self.assertEqual(the_exception.errno, 2)

    def test_get_assets(self):
        list_etalon = ['USDT']
        trader = akbot.Trader()
        trader.assets_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\assets_test.txt"
        list_result = trader.get_assets()
        self.assertEqual(list_etalon, list_result)

    def test_set_assets(self):
        list_etalon = ['USDT', 'BTC']
        trader = akbot.Trader()
        trader.assets_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\assets_test2.txt"
        assets = "USDT BTC"
        trader.set_assets(assets=assets)
        list_result = trader.get_assets()
        self.assertEqual(list_etalon, list_result)

    def test_make_pair(self):
        pairs_etalon = ['WAVESUSDT', 'WAVESBTC', 'AAVEUSDT', 'AAVEBTC', 'SHIBUSDT', 'SHIBBTC']
        trader = akbot.Trader()
        trader.assets = ["USDT", "BTC"]
        trader.whitelist = ["WAVES", "AAVE", "SHIB"]
        self.assertEqual(pairs_etalon, trader.make_pairs())

    def test_get_pairs_if_empty(self):
        pairs_etalon = ['WAVESUSDT', 'WAVESBTC', 'AAVEUSDT', 'AAVEBTC', 'SHIBUSDT', 'SHIBBTC']
        trader = akbot.Trader()
        trader.assets = ["USDT", "BTC"]
        trader.whitelist = ["WAVES", "AAVE", "SHIB"]
        trader.pairs = []
        self.assertEqual(pairs_etalon, trader.get_pairs())

    def test_get_pairs_if_not_empty(self):
        pairs_etalon = ['WAVESUSDT', 'WAVESBTC', 'AAVEUSDT', 'AAVEBTC', 'SHIBUSDT', 'SHIBBTC']
        trader = akbot.Trader()
        trader.assets = ["USDT", "BTC"]
        trader.whitelist = ["WAVES", "AAVE", "SHIB"]
        trader.make_pairs()
        self.assertEqual(pairs_etalon, trader.get_pairs())

    def test_get_asset_4(self):
        pair = 'SHIBUSDT'
        o = order.Order(pair, -5, 0.00002465)
        self.assertEqual('SHIB', o.get_asset(pair))

    def test_get_asset_3(self):
        pair = 'USDTBTC'
        o = order.Order(pair, -5, 0.00002465)
        self.assertEqual('USDT', o.get_asset(pair))

    def test_trim_step_size6(self):
        quantity = 32.156654234
        step_size = 0.000001
        o = order.Order('SHIBUSDT', -5, 0.00002465)
        self.assertEqual(32.156654, o.trim_step_size(quantity, step_size))

    def test_trim_step_size4(self):
        quantity = 32.156654234
        step_size = 0.0001
        o = order.Order('SHIBUSDT', -5, 0.00002465)
        self.assertEqual(32.1566, o.trim_step_size(quantity, step_size))

    def test_trim_step_size1(self):
        quantity = 32.156654234
        step_size = 0.1
        o = order.Order('SHIBUSDT', -5, 0.00002465)
        self.assertEqual(32.1, o.trim_step_size(quantity, step_size))

    def test_trim_step_size0(self):
        quantity = 32.156654234
        step_size = 1
        o = order.Order('SHIBUSDT', -5, 0.00002465)
        self.assertEqual(32, o.trim_step_size(quantity, step_size))


if __name__ == '__main__':
    unittest.main()

