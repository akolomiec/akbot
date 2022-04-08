import os
import time
import asyncio
from rich.live import Live
from rich.table import Table
import pymongo
from binance import AsyncClient, BinanceSocketManager
from binance.helpers import round_step_size
from loguru import logger

# todo Сделать статистику на экране приятной для восприятия.
# todo Сделать логирование нормальное. с использованием loguru
# todo сделать трейлинг на покупку.
# todo Сделать ограничение на время сделки, продавать через 30 минут после боковика.


api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
min_order = 11
max_trade_pair = 5
daily_percent = -1
trailing_stop = True
sell_up = 1.5
stop_loss = -1
trailing_sell = 1
logger.add("file_{time}.log", compression="zip", rotation="500 MB")


@logger.catch
def tofixed(num, digits=0):
    """
    Обрезает количество знаков после запятой в числе
    :param num: Число которое надо обрезать до какого-то количества знаков после запятой
    :param digits: Количество знаков после запятой, которое надо оставить
    :return: число с заданным количеством знаков после запятой
    """
    return f"{num:.{digits}f}"


@logger.catch
def get_assets():
    """
    Получаем базовые активы к которым торгуются валюты из Whitelist
    :return: Список базовых валют разделенных пробелом.
    """
    lst = ""
    # logger.info("Start get_assets()")
    f = open('assets.txt', 'r')
    try:
        assets = f.read()
        lst = assets.split()
    except FileExistsError:
        logger.exception("Can not reding tha file assets.txt")
    finally:
        f.close()
    # logger.info("Stop get_assets(). result = {}", lst)
    return lst


@logger.catch
def save_assets(assets):
    """
    Сохранение базовых валют в файл
    :param assets: Список базовых валют для сохранения
    :return: None
    """
    f = open('assets.txt', 'w')
    try:
        f.write(assets.upper())
    finally:
        f.close()


@logger.catch
def get_whitelist():
    """
    Получить список валют из файла для торговли
    :return: список валют разделенные пробелами
    """
    f = open('whitelist.txt', 'r')
    try:
        whitelist = f.read()
        lst = whitelist.split()
    finally:
        f.close()
    return lst


@logger.catch
def save_whitelist(whitelist):
    """
    Сохраним белый список валют в файл
    :param whitelist: список валют разделенных пробелом
    :return: Ничто
    """
    f = open('whitelist.txt', 'w')
    try:
        f.write(whitelist.upper())
    finally:
        f.close()


def make_pair():
    """
    Возвращает список пар валюты к активам
    :return:list список пар
    """
    whitelist = get_whitelist()
    assets = get_assets()
    pairs = list()
    for currency in whitelist:
        for asset in assets:
            if currency != asset:
                pair = currency + asset
                pairs.append(pair)
    return pairs


@logger.catch
def get_orders(pair):
    """
    Возвращает найденные  в базе сделки по данной паре
    :param pair: Название пары
    :return: True, False
    """
    found_pair = db.orders.find_one({'pair': pair, 'status': 'BUY'})
    return found_pair


@logger.catch
def get_pair_data(data, pair):
    """
    Извлекает из общей кучи данные по заданной паре
    :param data:
    :param pair:
    :return:
    """
    for item in data:
        if pair == item["s"]:
            return item


@logger.catch
def get_price(data, pair):
    """
    Получаем цену заданной пары из набора данных
    :param data:
    :param pair:
    :return:
    """
    for item in data:
        if item['s'] == pair:
            #logger.info("result ={}", item)
            return float(item['c'])


@logger.catch
async def get_btc_price(client):
    """
    Получаем цену биткоина к доллару.
    :param client:
    :return:
    """
    btc = await client.get_ticker(symbol="BTCUSDT")
    logger.info("BTCUSDT ={}", btc)
    return float(btc["lastPrice"])


@logger.catch
async def get_binance_status(client):
    btc = await client.get_ticker(symbol="BTCUSDT")


@logger.catch
async def on_calculate(client, data, symbols):
    """
    Производим рассчеты перед процедурой торговли. Выводим статистику
    :param data:
    [
   {
      "E": 1648703288108,
      "s": "ETHBTC",
      "P": "1.127",
      "c": "0.07225500"
   },
   {
      "E": 1648703288126,
      "s": "LTCBTC",
      "P": "1.621",
      "c": "0.00275900"
   }]

    :param symbols:
    [
        '1INCHUSDT',
        'AAVEUSDT',
        'ADAUSDT'
    ]
    :return:
    """
    await get_binance_status(client)
    for pair in symbols:
        item = get_pair_data(data, pair)
        if item is not None:
            if get_orders(pair):
                order_data = get_orders(pair)
                price = get_price(data, pair)
                cur_percent = (float(item["c"]) - float(order_data["cur_price"])) / float(item["c"]) * 100
                # logger.info("order_data ={}", order_data)
                logger.info("{} Buy_price:{} Price:{} %:{}", order_data["pair"], order_data["buy_price"], price, tofixed(cur_percent, 2))


@logger.catch
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


@logger.catch
async def buy_pair(database, client, pair, data):
    """
    Покупает валютную пару.
    :param database:
    :param client:
    :param pair:
    :param data:
    :return:
    """
    logger.info("{}", pair)
    asset = get_asset(pair)
    price = get_price(data, pair)
    info = await client.get_symbol_info(pair)
    step_size = float(info['filters'][2]['stepSize'])
    # todo пересчитывать мин ордер для каждой пары USDT / BTC
    if asset == "BTC":
        price_btc = await get_btc_price(client)
        quantity = round_step_size(min_order / price_btc / price, step_size)
    else:
        quantity = round_step_size(min_order / price, step_size)
    logger.info("{} price:{} qty:{}", pair, price, quantity)


    await client.order_market_buy(symbol=pair, quantity=quantity)
    insert_order(database, pair, data, step_size)
    delete_pair_price(database, pair)


@logger.catch
def insert_order(database, pair, data, step_size):
    """
    Сохраняет сделку в базе данных.
    :param database:
    :param pair:
    :param data:
    :return:

    """
    # logger.info("start")
    price = get_price(data, pair)
    quantity = round_step_size(min_order / price, step_size)

    for item in data:
        if item["s"] == pair:
            result = {'time': item["E"],
                      'pair': item["s"],
                      'buy_price': item['c'],
                      'daily_percent': item["P"],
                      'cur_price': item["c"],
                      'quantity': quantity,
                      'status': 'BUY',
                      'update': time.time(),
                      'max_price': item["c"],
                      'min_price': item["c"]
                      }
    logger.info("{}", result)
    database.orders.insert_one(result)
    # logger.info("stop")


@logger.catch
def close_order(database, data):
    current = {'_id': data["_id"]}
    new_data = {"$set": {"status": "SELL", "update": time.time()}}
    logger.info("{}", new_data)
    database.orders.update_one(current, new_data)


@logger.catch
async def sell_pair(database, client, data):
    logger.info("{}", data)
    quantity = data['quantity']
    symbol = data["pair"]
    await client.order_market_sell(symbol=symbol, quantity=quantity)
    close_order(database, data)


@logger.catch
def save_max_price(database, max_price, data):
    current = {'pair': data["pair"]}
    new_data = {"$set": {"max_price": max_price}}
    logger.warning("Update MAX Price {}", new_data)
    database.orders.update_one(current, new_data)


@logger.catch
def save_min_price(database, item):
    result = {
        'time': item['E'],
        'pair': item['s'],
        'daily_percent': item['P'],
        'cur_price': item['c'],
        'min_price': item['c'],
        'max_price': 0
    }
    # logger.info("insert {}", result)
    database.prices.insert_one(result)


@logger.catch
def get_min_price(database, item):
    found_pair = database.prices.find_one({'pair': item["s"]})
    if found_pair is None:
        save_min_price(database, item)
        return float(item['c'])
    else:
        return float(found_pair["min_price"])


@logger.catch
def update_min_price(database, item, cur_price):
    current = {'pair': item["s"]}
    new_data = {"$set": {"min_price": cur_price}}
    # logger.info("Update item {} for {}", item, new_data)
    res = database.prices.update_one(current, new_data)


def trim_data(res):
    dict_res = []
    data = res["data"]
    for item in data:
        result = {'E': item["E"], 's': item["s"], 'P': item["P"], 'c': item["c"]}
        dict_res.append(result)

    return dict_res


def delete_pair_price(database, pair):
    database.prices.delete_one({'pair': pair})


async def on_trade(client, database, data, symbols):
    """
    Торговая функция для бизнес-логики. Занимается покупкой и продажей валютных пар в зависимости от условий.
    :param client:
    :param database:
    :param data:
    :param symbols:
    :return:
    order_data =
    {'_id': ObjectId('624715a06be72a423f00c1d2'),
    'time': 1648825758537,
    'pair': 'AMPUSDT',
    'buy_price': '0.02763000',
    'daily_percent': '-1.603',
    'cur_price': '0.02763000',
    'quantity': 361.92544335866813,
    'status': 'BUY',
    'update': 1648825760.4829183,
    'max_price': 0,
    'min_price': 0
    }
    """
    for pair in symbols:
        item = get_pair_data(data, pair)
        if item is not None:
            order_data = get_orders(pair)
            if order_data:
                cur_price = float(item["c"])
                buy_price = float(order_data["buy_price"])
                cur_percent = (cur_price - buy_price) / cur_price * 100
                if cur_percent <= stop_loss:
                    logger.warning("Sell stop-loss {} Buy:{} Sell:{}", item["s"], buy_price, cur_price)
                    await sell_pair(database, client, order_data)
                elif cur_percent >= sell_up: #не ясно зачем и что тут делается
                    await sell_pair(database, client, order_data)

            else:

                cur_percent = float(item["P"])
                if cur_percent < daily_percent:
                    cur_price = float(item["c"])
                    min_price = get_min_price(db, item)
                    buy_percent = (cur_price - min_price) / cur_price * 100
                    order_count = database.orders.count_documents({'status': 'BUY'})
                    if cur_price < min_price:

                        update_min_price(db, item, cur_price)
                    elif buy_percent > 2:
                        logger.info("buy_percent {} > 2", buy_percent)
                        if order_count < max_trade_pair:
                            await buy_pair(database, client, pair, data)
                        else:
                            delete_pair_price(database, pair)


@logger.catch
async def main(database, symbols):
    """
    Основная функция запускающая асинхронное выполнение заданий.
    :param database:
    :param symbols:
    :return:
    """
    client = await AsyncClient.create(api_key, api_secret)
    bm = BinanceSocketManager(client)

    ts = bm.multiplex_socket(['!ticker@arr'])

    async with ts as tscm:
        while True:
            res = await tscm.recv()
            data = trim_data(res)

            await on_calculate(client, data, symbols)
            await on_trade(client, database, data, symbols)
    await client.close_connection()


if __name__ == "__main__":
    mongo = pymongo.MongoClient("localhost", 27017)  # Подключение и создание БД
    db = mongo.akbot
    pairs = make_pair()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(db, pairs))

