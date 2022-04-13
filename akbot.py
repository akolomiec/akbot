import os

import asyncio
from loguru import logger
from binance import AsyncClient, BinanceSocketManager
from binance.helpers import round_step_size


import order




class Trader:
    """
    Основной класс программы. выполняет роль контроллера и бизнес-логики
    """

    def __init__(self):
        self.binance_response = None
        self.asset = None
        self.symbols = None
        self.client = None
        self.pair = None
        self.tickerarr = None
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('API_SECRET')
        self.min_order = 50
        self.max_trade_pair = 5
        self.daily_percent = -1
        self.trailing_stop = True
        self.sell_up = 1.2
        self.stop_loss = -1
        self.trailing_sell = 1
        self.whitelist_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\whitelist.txt"
        self.whitelist = self.get_whitelist(self.whitelist_filename)
        self.assets_filename = "C:\\Users\\Feliks\\PycharmProjects\\pythonProject\\assets.txt"
        self.assets = self.get_assets(self.assets_filename)
        self.pairs = self.make_pairs()
        self.orders = []
        self.trade_order = 0

    @classmethod
    def get_whitelist(cls, whitelist_filename: str):
        """
            Получить список валют из файла для торговли
            :param whitelist_filename: str Имя файла для белого списка валют
            :return: list список валют разделенные пробелами
            """
        whitelist_result = []
        f = open(whitelist_filename, 'r')
        try:
            whitelist = f.read()
            whitelist_result = whitelist.split()
            cls.whitelist = whitelist_result
        except FileNotFoundError as e:
            logger.exception("{} file {}", e.strerror, whitelist_filename)
        finally:
            f.close()
        return whitelist_result

    @classmethod
    def set_whitelist(cls, whitelist, whitelist_filename):
        """
        Сохраним белый список валют в файл
            :param whitelist: str список валют разделенных пробелом
            :param whitelist_filename: str
            :return: bool
        """

        f = open(whitelist_filename, 'w')
        try:
            f.write(whitelist.upper())
        except FileExistsError:
            logger.exception("Can not reding tha file assets.txt")
        finally:
            f.close()
        return True

    @classmethod
    def get_assets(cls, assets_filename):
        """
            Получаем базовые активы к которым торгуются валюты из Whitelist
            :return: Список базовых валют разделенных пробелом.
            """
        lst = ""
        f = open(assets_filename, 'r')
        try:
            assets = f.read()
            lst = assets.split()
            cls.assets = lst
        except FileExistsError:
            logger.exception("Can not reding tha file assets.txt")
        finally:
            f.close()
        return lst

    @classmethod
    def set_assets(cls, assets, assets_filename):
        """
        Сохранение базовых валют в файл
        :param assets: Список базовых валют для сохранения
        :return: None
        """
        f = open(assets_filename, 'w')
        try:
            f.write(assets.upper())
        finally:
            f.close()

    def make_pairs(self):
        """
        генерирует список пар для работы и сохраняет их в объекта трейдер
        :return:list список пар
        """
        whitelist = self.whitelist
        assets = self.assets
        self.pairs = list()
        for currency in whitelist:
            for asset in assets:
                if currency != asset:
                    pair = currency + asset
                    self.pairs.append(pair)
        return self.pairs

    def get_pairs(self):
        if self.pairs:
            return self.pairs
        else:
            self.make_pairs()
            return self.pairs

    async def get_btc_price(self, client):
        """
            Получаем цену биткоина к доллару.
            :param
            :return:
            """
        btc = await client.get_ticker(symbol="BTCUSDT")
        await client.close_connection()
        return float(btc["lastPrice"])

    def get_binance_status(self):
        pass

    def get_pair_data(self, pair):
        """
        Извлекает из общей кучи данные по заданной паре
        :param
        :param
        :return:
        """
        for item in self.tickerarr:
            if pair == item["s"]:
                return item

    @logger.catch
    async def on_calculate(self, pairs, orders):
        for pair in pairs:
            item = self.get_pair_data(pair)
            if item is not None:
                found_order = False
                for order_item in orders:
                    if order_item.pair == pair:
                        found_order = True
                        order_item.cur_price = float(item['c'])
                        order_item.daily_percent = float(item['P'])

                        if order_item.stage == "pre":
                            if order_item.min_price is None:
                                order_item.min_price = order_item.cur_price
                            if order_item.min_price > order_item.cur_price:
                                order_item.min_price = order_item.cur_price
                            else:
                                percent = (order_item.cur_price - order_item.min_price) / order_item.cur_price * 100
                                if percent > 2:
                                    order_item.flag = "buy"
                                    return order_item.flag

                        elif order_item.stage == "sell_up":
                            logger.debug("{} buy:{} cur:{} qty:{} max:{} min:{} %:{}", order_item.pair,
                                         order_item.buy_price,
                                         order_item.cur_price, order_item.quantity, order_item.max_price,
                                         order_item.min_price,
                                         (order_item.cur_price - order_item.buy_price) / order_item.cur_price * 100)
                            if order_item.max_price is None:
                                order_item.max_price = order_item.cur_price
                            if order_item.max_price < order_item.cur_price:
                                order_item.max_price = order_item.cur_price
                            if order_item.cur_price / order_item.buy_price * 100 - 100 < self.stop_loss:
                                order_item.flag = "sell"
                                return order_item.flag
                            if order_item.cur_price / order_item.buy_price * 100 - 100 > self.sell_up:
                                order_item.flag = "sell"
                                return order_item.flag

                if not found_order:
                    self.orders.append(order.Order(pair, float(item['P']), float(item['c'])))
                    return None

    @logger.catch
    async def on_trade(self):
        for self.pair in self.pairs:
            item = self.get_pair_data(self.pair)
            if item is not None:
                for order_item in self.orders:
                    if order_item.pair == self.pair:
                        if order_item.flag == "buy":
                            if self.max_trade_pair > self.trade_order:
                                asset = trader.get_asset(self.pair)
                                if order_item.step_size is None:
                                    info = await self.client.get_symbol_info(self.pair)
                                    logger.warning(info)
                                    order_item.step_size = float(info['filters'][2]['stepSize'])
                                order_item.quantity = await self.calculate_quantity(asset, self.client, self.min_order,
                                                                                    order_item.cur_price,
                                                                                    order_item.step_size)
                                logger.info("{} price:{} qty:{}", order_item.pair, order_item.cur_price,
                                            order_item.quantity)
                                await order_item.buy_pair(self.client)
                                self.trade_order += 1
                        elif order_item.flag == "sell":
                            await order_item.sell_pair(self.client)
                            self.trade_order -= 1

    async def calculate_quantity(self, client, asset, min_order, cur_price, step_size):
        if min_order > 10.5:
            if asset == "BTC":
                price_btc = await self.get_btc_price(client)
                quantity = round_step_size(min_order / price_btc / cur_price, step_size)
            else:
                quantity = round_step_size(min_order / cur_price, step_size)
        else:
            return None
        return quantity

    @staticmethod
    def get_asset(pair):
        """
        Возвращаем базовый актив, BTC или USDT
        :param pair:
        :return:
        """
        asset = pair[-3:]
        if asset == "BTC":
            return "BTC"
        else:
            return "USDT"

    def convert_usdt2btc(self):
        pass

    @logger.catch
    async def main(self):
        
        self.symbols = trader.get_whitelist(self.whitelist_filename)
        self.asset = trader.get_assets(self.assets_filename)
        # todo убрать подготовку соединений в соответствующие классы.
        self.client = await AsyncClient.create(self.api_key, self.api_secret)
        self.bm = BinanceSocketManager(self.client)

        # todo убрать получение данных в отдельный метод класса Binancer
        ts = self.bm.multiplex_socket(['!ticker@arr'])

        async with ts as tscm:
            while True:
                self.binance_response = await tscm.recv()
                await self.on_calculate(self.symbols, self. assets, self.orders, res)
                await self.on_trade()


if __name__ == "__main__":
    trader = Trader()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(trader.main())
    loop.run_forever()
