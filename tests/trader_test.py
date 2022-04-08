import unittest
import akbot
import order
import os
from unittest import IsolatedAsyncioTestCase

import order


class Test(IsolatedAsyncioTestCase):

#    async def test_get_btc_price(self):
#        trader = akbot01.Trader()
#        btc_price = await trader.get_btc_price()
#        self.assertEqual(type(btc_price), float)
#
    async def test_on_calculate(self):
        pass


class TraderTestCase(unittest.TestCase):
    def test_get_whitelist(self):
        list_etalon = ["1INCH", "AAVE", "ADA"]

        trader = akbot01.Trader()
        trader.whitelist_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\whitelist.txt"
        list_result = trader.get_whitelist()
        self.assertEqual(list_etalon, list_result)

    def test_get_whitelist_file_not_found(self):
        trader = akbot01.Trader()
        trader.whitelist_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\w.txt"
        with self.assertRaises(FileNotFoundError) as cm:
            trader.get_whitelist()
        the_exception = cm.exception
        self.assertEqual(the_exception.strerror, 'No such file or directory')
        self.assertEqual(the_exception.errno, 2)

    def test_set_whitelist(self):

        list_etalon = ['AXS', 'BAT', 'BCD', 'BCH', 'BICO', 'BNB', 'BTCST', 'BTG', 'CAKE', 'CELO']
        trader = akbot01.Trader()
        trader.whitelist_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\whitelist2.txt"
        whitelist = "AXS BAT BCD BCH BICO BNB BTCST BTG CAKE CELO"
        trader.set_whitelist(whitelist=whitelist)
        list_result = trader.get_whitelist()
        self.assertEqual(list_etalon, list_result)

    def test_get_whitelist_file_not_found(self):
        trader = akbot01.Trader()
        trader.whitelist_filename = "E:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\w.txt"
        whitelist = "AXS BAT BCD BCH BICO BNB BTCST BTG CAKE CELO"
        with self.assertRaises(FileNotFoundError) as cm:
            trader.set_whitelist(whitelist=whitelist)
        the_exception = cm.exception
        self.assertEqual(the_exception.strerror, 'No such file or directory')
        self.assertEqual(the_exception.errno, 2)

    def test_get_assets(self):
        list_etalon = ['USDT']
        trader = akbot01.Trader()
        trader.assets_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\assets_test.txt"
        list_result = trader.get_assets()
        self.assertEqual(list_etalon, list_result)

    def test_set_assets(self):
        list_etalon = ['USDT', 'BTC']
        trader = akbot01.Trader()
        trader.assets_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\tests\\assets_test2.txt"
        assets = "USDT BTC"
        trader.set_assets(assets=assets)
        list_result = trader.get_assets()
        self.assertEqual(list_etalon, list_result)

    def test_make_pair(self):
        pairs_etalon = ['WAVESUSDT', 'WAVESBTC', 'AAVEUSDT', 'AAVEBTC', 'SHIBUSDT', 'SHIBBTC']
        trader = akbot01.Trader()
        trader.assets = ["USDT", "BTC"]
        trader.whitelist = ["WAVES", "AAVE", "SHIB"]
        self.assertEqual(pairs_etalon, trader.make_pairs())

    def test_get_pairs_if_empty(self):
        pairs_etalon = ['WAVESUSDT', 'WAVESBTC', 'AAVEUSDT', 'AAVEBTC', 'SHIBUSDT', 'SHIBBTC']
        trader = akbot01.Trader()
        trader.assets = ["USDT", "BTC"]
        trader.whitelist = ["WAVES", "AAVE", "SHIB"]
        trader.pairs = []
        self.assertEqual(pairs_etalon, trader.get_pairs())

    def test_get_pairs_if_not_empty(self):
        pairs_etalon = ['WAVESUSDT', 'WAVESBTC', 'AAVEUSDT', 'AAVEBTC', 'SHIBUSDT', 'SHIBBTC']
        trader = akbot01.Trader()
        trader.assets = ["USDT", "BTC"]
        trader.whitelist = ["WAVES", "AAVE", "SHIB"]
        trader.make_pairs()
        self.assertEqual(pairs_etalon, trader.get_pairs())

    def test_get_asset_4(self):
        pair = 'SHIBUSDT'
        order = order01.Order(pair, -5, 0.00002465)
        self.assertEqual('SHIB', order.get_asset(pair))

    def test_get_asset_3(self):
        pair = 'USDTBTC'
        order = order01.Order(pair, -5, 0.00002465)
        self.assertEqual('USDT', order.get_asset(pair))

    def test_trim_step_size6(self):
        quantity = 32.156654234
        step_size = 0.000001
        order = order01.Order('SHIBUSDT', -5, 0.00002465)
        self.assertEqual(32.156654, order.trim_step_size(quantity, step_size))

    def test_trim_step_size4(self):
        quantity = 32.156654234
        step_size = 0.0001
        order = order01.Order('SHIBUSDT', -5, 0.00002465)
        self.assertEqual(32.1566, order.trim_step_size(quantity, step_size))

    def test_trim_step_size1(self):
        quantity = 32.156654234
        step_size = 0.1
        order = order01.Order('SHIBUSDT', -5, 0.00002465)
        self.assertEqual(32.1, order.trim_step_size(quantity, step_size))

    def test_trim_step_size0(self):
        quantity = 32.156654234
        step_size = 1
        order = order01.Order('SHIBUSDT', -5, 0.00002465)
        self.assertEqual(32, order.trim_step_size(quantity, step_size))


if __name__ == '__main__':
    unittest.main()

