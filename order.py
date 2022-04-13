import time
from loguru import logger
from binance.helpers import round_step_size
import decimal


class Order:
    """Класс торгового ордера."""

    def __init__(self, symbol, asset, daily_percent, cur_price):
        self.flag = None
        self.create_time = time.time()
        self.symbol = symbol
        self.asset = asset
        self.daily_percent = daily_percent
        self.cur_price = cur_price
        self.buy_price = None
        self.quantity = None
        self.status = None
        self.max_price = None
        self.min_price = None
        self.sell_price = None
        self.last_update = None
        self.stage = "pre"
        self.step_size = None
        self.min_notional = None

    def calculate(self):
        pass

    async def buy_pair(self, client):

        await client.order_market_buy(symbol=self.pair, quantity=self.quantity)
        self.buy_price = self.cur_price
        self.status = "buy"
        self.stage = "sell_up"
        self.flag = None
        self.quantity = await self.get_quantity(client)
        self.quantity = self.trim_step_size(self.quantity, self.step_size)

    def trim_step_size(self, quantity, step_size):

        if step_size == 0.0000001:
            float_val = float(decimal.Decimal(str(quantity)).quantize(decimal.Decimal('.0000001'),
                                                                      rounding=decimal.ROUND_DOWN))
        elif step_size == 0.000001:
            float_val = float(decimal.Decimal(str(quantity)).quantize(decimal.Decimal('.000001'),
                                                                      rounding=decimal.ROUND_DOWN))
        elif step_size == 0.00001:
            float_val = float(decimal.Decimal(str(quantity)).quantize(decimal.Decimal('.00001'),
                                                                      rounding=decimal.ROUND_DOWN))
        elif step_size == 0.0001:
            float_val = float(decimal.Decimal(str(quantity)).quantize(decimal.Decimal('.0001'),
                                                                      rounding=decimal.ROUND_DOWN))
        elif step_size == 0.001:
            float_val = float(decimal.Decimal(str(quantity)).quantize(decimal.Decimal('.001'),
                                                                      rounding=decimal.ROUND_DOWN))
        elif step_size == 0.01:
            float_val = float(decimal.Decimal(str(quantity)).quantize(decimal.Decimal('.01'),
                                                                      rounding=decimal.ROUND_DOWN))
        elif step_size == 0.1:
            float_val = float(decimal.Decimal(str(quantity)).quantize(decimal.Decimal('.1'),
                                                                      rounding=decimal.ROUND_DOWN))
        elif step_size == 1:
            float_val = float(int(quantity))
        return float_val

    async def sell_pair(self, client):
        logger.warning("{} stage:{} Qty:{} Price Buy:{}, Sell:{}", self.pair, self.stage, self.quantity, self.buy_price,
                       self.sell_price)
        await client.order_market_sell(symbol=self.pair, quantity=self.quantity)
        self.sell_price = self.cur_price
        self.status = "None"
        self.flag = None
        self.stage = "pre"
        self.buy_price = None
        self.quantity = None
        self.min_price = None
        self.max_price = None

    def get_asset(self, pair):
        asset = pair[-3:]
        if asset == "BTC":
            length = len(pair) - 3
            val = pair[:length]
            return val
        else:
            length = len(pair) - 4
            val = pair[:length]
            return val

    async def get_quantity(self, client):
        val = self.get_asset(self.pair)
        balance = await client.get_asset_balance(asset=val)
        return float(balance['free'])

    def get_percent(self):
        pass

    def save_statistic(self):
        pass

    def set_stage(self):
        pass

    def get_stage(self):
        pass

    def set_status(self):
        pass

    def get_status(self):
        pass

    def set_min_price(self):
        pass

    def get_min_price(self):
        pass

    def set_max_price(self):
        pass

    def get_max_price(self):
        pass
