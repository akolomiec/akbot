import telebot
import pymysql
import time
from telebot import types
from binance.client import Client
from binance import ThreadedWebsocketManager
from datetime import datetime

api_key = '7tmGEBOvx4sxDPiH3lON1cNBFKrr6Dj41nRssuAbpQXrbfax9BWSjvCniWb9krsG'
api_secret = 'mTfx0ZF7z1DFk3bZSswrHjvsOKzkBghigRtVzTes0AdBVGjV7BPfB7EvEyaQez2P'
telegram_token = '5000273564:AAFST9lcsY7IxgJzhDtVnDY8EkNKXLdf5WE'
quantity = 1

def telegram_bot(token):
    bot = telebot.TeleBot(token, parse_mode=None)

    @bot.message_handler(commands=["start"])
    def start_message(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        statistic = types.KeyboardButton("Статистика")
        whitelst = types.KeyboardButton("Whitelist")
        assets = types.KeyboardButton("Базовые валюты")

        markup.add(statistic)
        markup.add(whitelst)
        markup.add(assets)
        bot.send_message(message.chat.id, "Здарова, братан!", reply_markup=markup)

    @bot.message_handler(content_types='text')
    def message_reply(message):
        if message.text == "Статистика":
            bot.send_message(message.chat.id, "Статистика, а что дальше?")
            #todo написать процесс получения статистики по аккаунту
            # Нужны данные, баланс аккаунта по биткам и USDT. Свободный депозит. Ордера в работе/максимум ордеров. Кол-во сделок. Суточная дельта. Время обновления данных.
        elif message.text == "Whitelist":

            list = get_whitelist()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            main_menu = types.KeyboardButton("Главная")
            edit_btn = types.KeyboardButton("Изменить Whitelist")
            markup.add(main_menu)
            markup.add(edit_btn)

            bot.send_message(message.chat.id, f"Whitelist\n{list}", reply_markup=markup)
        elif message.text == "Главная":
            start_message(message)
        elif message.text == "Изменить Whitelist":

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            main_menu = types.KeyboardButton("Главная")
            markup.add(main_menu)

            msg = bot.send_message(message.chat.id, f"Введите список разрешенных валют через пробел.\nНапример: BTC ATOM SHIB UNI", reply_markup=markup)
            bot.register_next_step_handler(msg, ac_whitelist)
        elif message.text == "Базовые валюты":
            list = get_assets()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            main_menu = types.KeyboardButton("Главная")
            edit_btn = types.KeyboardButton("Изменить Assets")
            markup.add(main_menu)
            markup.add(edit_btn)

            bot.send_message(message.chat.id, f"Базовые валюты\n{list}", reply_markup=markup)
        elif message.text == "Изменить Assets":

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            main_menu = types.KeyboardButton("Главная")
            markup.add(main_menu)

            msg = bot.send_message(message.chat.id, f"Введите список базовых валют через пробел.\nНапример: BTC USDT", reply_markup=markup)
            bot.register_next_step_handler(msg, ac_assets)

    def ac_whitelist(message):
        if message.text != "Главная":
            save_whitelist(message.text)
        start_message(message)
    def ac_assets(message):
        if message.text != "Главная":
            save_assets(message.text)
        start_message(message)
    # todo Надо сделать управление через телегу. Сейчас останавливается работа скрипта, до выключения телеграм-бота.
    #bot.polling()
def get_assets():
    f = open('assets.txt', 'r')
    try:
        assets = f.read()
    finally:
        f.close()
    return assets
def save_assets(assets):
    f = open('assets.txt', 'w')
    try:
        f.write(assets.upper())
    finally:
        f.close()
def get_whitelist():
    f = open('whitelist.txt', 'r')
    try:
        whitelist = f.read()
    finally:
        f.close()
    return whitelist
def save_whitelist(whitelist):
    f = open('whitelist.txt', 'w')
    try:
        f.write(whitelist.upper())
    finally:
        f.close()


def initial(key, secret):

    #client = Client(api_key, api_secret, testnet=False)
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    # start is required to initialise its internal loop
    twm.start()

    def handle_socket_message(msg):
        print(f"message type: {msg['e']}")
        print(msg)


    symbol = get_whitelist()+get_assets()
    print ("symbol", symbol)



    while True:
        #updates = telebot.get_updates()

        sts = twm.start_symbol_ticker_socket(callback=handle_socket_message, symbol=symbol)

        twm.join()

        #cost = float(get_cost(symbol, client))
        #cost_avg = float(get_avg_price(symbol, client))
        print(sts)
        #price_change_percent = float(twm.(symbol, client))

        # Если цена упала на 5% от дневного уровня, то надо брать

        #if price_change_percent <= -5:
            # Запрос пользователю на покупку валюты
        #    limit_order_buy = buy_pair(symbol=symbol, quantity=quantity, price=cost, client=client)  # купить валюту
        #    print(limit_order_buy)

        #profit = take_profit(cost)  # расчитать доход
        #print("Price: ", cost, "Profit price:", profit, " ", price_change_percent)
        #if price_change_percent > 1.3:
        #    sell_pair(symbol)

        time.sleep(1 - time.time() % 1)
    twm.stop()

def ak_get_orders(client):
    orders = client.get_all_orders(symbol='SHIBUSDT')
    i = 0
    for order in orders:
        i += 1
        amount = float(order['origQty']) * float(order['price'])
        print(f"{i}. {order['orderId']} {order['symbol']} {order['status']} {order['type']} {order['side']} {order['origQty']} {order['price']} {amount}$")
    return True

def get_avg_price(symbol, client):
    # Получить среднюю цену пары монет
    # Получаем пару на входе. На выходе средняя цена за сутки
    cost_avg = client.get_ticker(symbol=symbol)
    #print(cost_avg)
    return cost_avg['weightedAvgPrice']

def get_change_percent(symbol, client):

    result = client.get_ticker(symbol=symbol)
    return result['priceChangePercent']

def get_cost(symbol, client):
    # Получить текущую цену пары монет
    # Получаем пару на входе. На выходе текущая цена

    cost = client.get_ticker(symbol=symbol)
    return cost['lastPrice']

def buy_req(symbol):
    # Запрос на покупку монеты в паре.
    # На входе пара монет, отправляем пользователю в телеграм название, цену на пару и график цены за последние время.
    # Ждем ответа от пользователя бесконечно?
    return True

def sell_req(symbol):
    # Запрос на продажу монеты в паре.
    # На входе пара монет, отправляем пользователю в телеграм название, цену на пару и график цены за последние время.
    # Ждем ответа от пользователя бесконечно?
    return True

def buy_pair(symbol, quantity, price, client):
    # купить пару на заданное количество монет

    buy_order_limit = client.create_test_order(
        symbol=symbol,
        side='BUY',
        type='MARKET',
        timeInForce='GTC',
        quantity=quantity,
        price=price)
    return True

def sell_pair(symbol):
    # Продать Валюту
    # todo Продать валюту исходя из ранее созданных ордеров. если ордеров нет, то ничего не делать.
    print("sell pair")
    return True

def take_profit(price):
    #todo нормально рассчитать профит от сделки.
    profit = price + price*0.013
    return profit




if __name__ == '__main__':
    telegram_bot(telegram_token)
    initial(api_key, api_secret)









