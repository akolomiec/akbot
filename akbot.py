import os
import time
import asyncio
import pymongo
from binance import AsyncClient, BinanceSocketManager
from loguru import logger

# todo Сделать статистику на экране приятной для восприятия.
# todo Сделать логирование нормальное. с использованием loguru
# todo сделать трейлинг на покупку.
# todo Сделать ограничение на время сделки, продавать через 30 минут после боковика.


api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
min_order = 10
max_trade_pair = 5
debug = True
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
    logger.info("Start get_assets()")
    f = open('assets.txt', 'r')
    try:
        assets = f.read()
        lst = assets.split()
    except FileExistsError:
        logger.exception("Can not reding tha file assets.txt")
    finally:
        f.close()
    logger.info("Stop get_assets(). result = {}", lst)
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
    found_pair = db.orders.find_one({'s': pair, 'S': 'BUY'})
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


async def get_btc_price(client):
    """
    Получаем цену биткоина к доллару.
    :param client:
    :return:
    """
    btc = await client.get_ticker(symbol="BTCUSDT")
    logger.info("BTCUSDT ={}", btc)
    return float(btc["lastPrice"])


def on_calculate(data, symbols):
    """
    Производим рассчеты перед процедурой торговли. Выводим статистику
    :param data:
    :param symbols:
    :return:
    """
    logger.info("on calculate start")
    for pair in symbols:
        item = get_pair_data(data, pair)
        if item is not None:
            if get_orders(pair):
                order_data = get_orders(pair)
                price = get_price(data, pair)
                cur_percent = (float(item["c"]) - float(order_data["c"])) / float(item["c"]) * 100
                # logger.info("order_data ={}", order_data)
                logger.info("{} Buy_price:{} Price:{} %:{}", order_data["s"], order_data["c"], price, tofixed(cur_percent, 2))


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
    info = client.get_symbol_info(pair)
    print()
    # todo пересчитывать мин ордер для каждой пары USDT / BTC
    if asset == "BTC":
        price_btc = await get_btc_price(client)
        quantity = min_order / price_btc / price
    else:
        quantity = min_order / price
    logger.info("{} price:{} qty:{}", pair, price, quantity)
    if not debug:
        await client.order_market_buy(symbol=pair, quantity=quantity)
    save_order(database, pair, data)


@logger.catch
def save_order(database, pair, data):
    """
    Сохраняет сделку в базе данных.
    :param database:
    :param pair:
    :param data:
    :return:
    """
    # logger.info("start")
    price = get_price(data, pair)
    quantity = min_order / price
    for item in data:
        if item["s"] == pair:
            result = {'E': item["E"],
                      's': item["s"],
                      'P': item["P"],
                      'c': item["c"],
                      'q': quantity,
                      'S': 'BUY',
                      'u': time.time(),
                      'max': 0
                      }
    database.orders.insert_one(result)
    # logger.info("stop")


@logger.catch
def close_order(database, data):
    current = {'_id': data["_id"]}
    new_data = {"$set": {"S": "SELL", "u": time.time()}}
    logger.info("{}", new_data)
    database.orders.update_one(current, new_data)


@logger.catch
async def sell_pair(database, client, data):
    logger.info("{}", data)
    quantity = float(round(data["q"], 6))
    symbol = data["s"]
    if not debug:
        await client.order_market_sell(symbol=symbol, quantity=quantity)
    close_order(database, data)


@logger.catch
def save_max_price(database, max_price, data):
    current = {'_id': data["_id"]}
    new_data = {"$set": {"max": max_price}}
    logger.warning("Update MAX Price {}", new_data)
    database.orders.update_one(current, new_data)


@logger.catch
def save_min_price(database, item):
    logger.info("insert {}", item)
    result = {
        "E": item["E"],
        "s": item["s"],
        "P": item["P"],
        "c": item["c"],
        "min": item["c"]
    }
    database.prices.insert_one(result)




@logger.catch
def get_min_price(database, item):
    found_pair = database.prices.find_one({'s': item["s"]})
    if found_pair is None:
        return None
    else:
        return float(found_pair["min"])


@logger.catch
def update_min_price(database, item, cur_price):
    current = {'s': item["s"]}
    new_data = {"$set": {"min": cur_price}}
    logger.info("Update item {} for {}", item, new_data)
    res = database.prices.update_one(current, new_data)


def trim_data(res):
    dict_res = []
    data = res["data"]
    for item in data:
        result = {'E': item["E"], 's': item["s"], 'P': item["P"], 'c': item["c"]}
        dict_res.append(result)

    return dict_res


def delete_pair_price(database, pair):
    database.prices.delete_one({'s': pair})


async def on_trade(client, database, data, symbols):
    """
    Торговая функция для бизнес-логики. Занимается покупкой и продажей валютных пар в зависимости от условий.
    :param client:
    :param database:
    :param data:
    :param symbols:
    :return:
    """
    logger.info("on trade start")
    for pair in symbols:
        item = get_pair_data(data, pair)
        if item is not None:
            order_data = get_orders(pair)
            if order_data:
                cur_price = float(item["c"])
                buy_price = float(order_data["c"])
                cur_percent = (cur_price - buy_price) / cur_price * 100
                if cur_percent <= stop_loss:
                    logger.warning("Sell stop-loss {} Buy:{} Sell:{}", item["s"], buy_price, cur_price)
                    await sell_pair(database, client, order_data)
                elif cur_percent >= sell_up or order_data["max"] > 0:
                    max_price = float(order_data["max"])
                    if max_price == 0:
                        max_price = buy_price
                        save_max_price(database, max_price, order_data)
                    elif max_price < buy_price:
                        max_price = buy_price
                        save_max_price(database, max_price, order_data)
                    elif (max_price - buy_price)/max_price*100 > trailing_sell or cur_percent <= sell_up:
                        logger.warning("Sell {} Buy:{} Sell:{} %:{}",
                                       item["s"],
                                       buy_price,
                                       cur_price,
                                       (cur_price - buy_price)/cur_price*100)
                        await sell_pair(database, client, order_data)

            else:
                if float(item["P"]) < daily_percent:
                    cur_price = float(item["c"])
                    min_price = get_min_price(db, item)
                    if min_price is None:
                        save_min_price(db, item)
                        min_price = cur_price
                    buy_percent = (cur_price - min_price) / cur_price * 100
                    order_count = database.orders.count_documents({'S': 'BUY'})
                    if cur_price < min_price:
                        update_min_price(db, item, cur_price)
                    elif buy_percent > 2:
                        if order_count < max_trade_pair:
                            await buy_pair(database, client, pair, data)
                        else:
                            delete_pair_price(database, pair)
    await asyncio.sleep(0)


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
    # start any sockets here, i.e a trade socket
    ts = bm.multiplex_socket(['!ticker@arr'])
    # then start receiving messages
    async with ts as tscm:
        while True:
            res = await tscm.recv()
            data = trim_data(res)
            # logger.info(data)
            on_calculate(data, symbols)
            await on_trade(client, database, data, symbols)
    await client.close_connection()


if __name__ == "__main__":
    mongo = pymongo.MongoClient("localhost", 27017)  # Подключение и создание БД
    db = mongo.akbot
    pairs = make_pair()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(db, pairs))

