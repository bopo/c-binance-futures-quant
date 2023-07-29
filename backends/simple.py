import _thread
import decimal
import json
import time
import traceback

import requests


from backends import config
from .config import FUNCTION_CLIENT, ONE_MIN_KLINE_OBJ_ARR, UPDATE_DATA_STR, RUN_TIME, PRICE_DECIMAL_OBJ
from .kernel.model.constant import *


def get_tick_data():
    """
    """
    global SECOND_NUMBER, OSS_BUCKET

    now = int(time.time() * 1000)
    nowMin = config.FUNCTION_CLIENT.turn_ts_to_min(now)
    dataStr = ''

    dataStr = config.FUNCTION_CLIENT.get_from_ws_a('B')

    if now - config.LAST_DATA_UPDATE_TS > 30000:
        _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('dataStr aways equal LAST_DATA_STR',))
    if dataStr != config.LAST_DATA_STR:
        config.UPDATE_DATA_STR = True
        config.LAST_DATA_UPDATE_TS = now
        config.LAST_DATA_STR = dataStr
        dataArr = dataStr.split('*')

        config.ACCOUNT_BALANCE_VALUE = float(dataArr[4])
        if config.ACCOUNT_BALANCE_VALUE == 0:
            _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('ACCOUNT_BALANCE_VALUE==0',))
        if dataArr[3] != '':
            config.BAN_SYMBOL_ARR = dataArr[3].split('@')
        else:
            config.BAN_SYMBOL_ARR = []

        if dataArr[2] != '':
            positionStrArr = dataArr[2].split('&')
            positionArr = []
            for a in range(len(positionStrArr)):
                positionArr.append(positionStrArr[a].split('@'))
                positionArr[a][1] = float(positionArr[a][1])
                positionArr[a][2] = float(positionArr[a][2])
            config.POSITION_ARR = positionArr
        else:
            config.POSITION_ARR = []

        if len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR) > 0:
            klineArr = dataArr[0].split('@')
            for a in range(len(klineArr)):
                klineArr[a] = klineArr[a].split('~')
                for b in range(len(klineArr[a])):
                    klineArr[a][b] = klineArr[a][b].split('&')
                    for c in range(len(klineArr[a][b])):
                        klineArr[a][b][c] = float(klineArr[a][b][c])

                    localMin = int(config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][len(config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr']) - 1][4])
                    klineMin = int(klineArr[a][b][0])

                    if localMin == klineMin:
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][len(config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr']) - 1] = [klineArr[a][b][1], klineArr[a][b][4],
                                                                                                                                               klineArr[a][b][2],
                                                                                                                                               klineArr[a][b][3], klineMin]
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['dataError'] = False
                    elif (klineMin == localMin + 1) or (klineMin == 0 and localMin == 59):
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'].append([klineArr[a][b][1], klineArr[a][b][4], klineArr[a][b][2], klineArr[a][b][3], klineMin])
                        del config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][0]
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['dataError'] = False
                    elif (klineMin < localMin - 2) and (localMin != 1 and localMin != 0):
                        _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, (
                            'localMin B:' + str(localMin) + ',klineMin:' + str(klineMin) + ',symbol:' + str(config.TRADE_SYMBOL_ARR[a]['symbol']) + ',' + str(
                                config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]),))
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['dataError'] = True

        priceStrArr = dataArr[1].split('~')
        priceArr = []
        for a in range(len(priceStrArr)):
            priceStrArr[a] = priceStrArr[a].split('^')
            # askPrice  = float(priceStrArr[a][0])
            # bidPrice  = float(priceStrArr[a][1])
            # serverMin  = int(priceStrArr[a][2])
            priceArr.append([float(priceStrArr[a][0]), float(priceStrArr[a][1]), int(priceStrArr[a][2])])

        config.DEPTH_PRICE_ARR = priceArr

        if len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR) != len(priceArr):
            config.LOCAL_ONE_MIN_KLINE_OBJ_ARR = []
            for a in range(len(priceArr)):
                serverMin = priceArr[a][2]
                # open close high low

                config.LOCAL_ONE_MIN_KLINE_OBJ_ARR.append([[priceArr[a][0], priceArr[a][0], priceArr[a][0], priceArr[a][1], serverMin]])
                config.LAST_OPEN_PRICE.append(0)
                config.LAST_OPEN_RATE_ARR.append(0)
                config.OPEN_TIME_ARR.append(0)
                config.TAKE_OPEN_TIME_ARR.append(0)
                config.OPEN_DIRECTION_ARR.append('')
                config.OPEN_POSITION_TS_ARR.append(0)
                config.SYMBOL_STOP_LOSS_TS_ARR.append(0)
                config.SYMBOL_OPEN_TYPE_ARR.append('C')
                config.SYMBOL_STANDARD_VALUE_ARR.append(0)
                config.ADD_POSITION_TS_ARR.append(0)
                config.LAST_ORDER_INFO_ARR.append({'highPrice': 0, 'lowPrice': 0})
                config.SPECIAL_CLOSE_POSITION_ARR.append(False)
        else:
            for a in range(len(priceArr)):

                openPrice = priceArr[a][0]
                closePrice = priceArr[a][1]

                if config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) - 1][1] > config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][len(
                    config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) - 1][0]:
                    openPrice = priceArr[a][1]
                    closePrice = priceArr[a][0]
                serverMin = priceArr[a][2]

                localMin = config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) - 1][4]

                if localMin == serverMin:
                    if (priceArr[a][0] > config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) - 1][2]):
                        config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) - 1][2] = priceArr[a][0]

                    if (priceArr[a][1] < config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) - 1][3]):
                        config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) - 1][3] = priceArr[a][1]

                    config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) - 1][1] = closePrice
                elif (localMin + 1 == serverMin) or (localMin == 59 and serverMin == 0):
                    config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a].append([openPrice, closePrice, priceArr[a][0], priceArr[a][1], serverMin])
                else:
                    if localMin - 1 != serverMin and (localMin != 1 and localMin != 0):
                        _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min,
                                                 ('localMin:' + str(localMin) + ',serverMin:' + str(serverMin) + ',symbol:' + str(config.TRADE_SYMBOL_ARR[a]['symbol']),))
                        config.LOCAL_ONE_MIN_KLINE_OBJ_ARR = []

                if len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]) > 3:
                    del config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][0]

            for a in range(len(config.ONE_MIN_KLINE_OBJ_ARR)):
                for b in range(len(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a])):
                    localMin = int(config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][4])
                    klineMin = int(config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][len(config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr']) - 1][4])

                    if klineMin == localMin:
                        if config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][2] > config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][len(
                            config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr']) - 1][2]:
                            config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][len(
                                config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr']) - 1][2] = config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][2]
                        if config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][3] < config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][len(
                            config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr']) - 1][3]:
                            config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][len(
                                config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr']) - 1][3] = config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][3]

                        config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][len(
                            config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr']) - 1][1] = config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][1]
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['dataError'] = False
                    elif (localMin == klineMin + 1) or (localMin == 0 and klineMin == 59):
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'].append(
                            [config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][0], config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][1],
                             config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][2], config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a][b][3],
                             localMin])
                        del config.ONE_MIN_KLINE_OBJ_ARR[a]['klineArr'][0]
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['dataError'] = False
                    elif localMin < klineMin - 2 and (klineMin != 1 and klineMin != 0):
                        _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, (
                            'localMin A:' + str(localMin) + ',klineMin:' + str(klineMin) + ',symbol:' + str(config.TRADE_SYMBOL_ARR[a]['symbol']) + ',' + str(
                                config.LOCAL_ONE_MIN_KLINE_OBJ_ARR[a]),))
                        config.ONE_MIN_KLINE_OBJ_ARR[a]['dataError'] = True


def get_one_min_data():
    dataStr = config.FUNCTION_CLIENT.get_from_ws_a('A')
    newKlineDataObjArr = []
    klineArr = dataStr.split('@')

    for a in range(len(klineArr)):
        coin = config.TRADE_SYMBOL_ARR[a]['coin']
        quote = config.TRADE_SYMBOL_ARR[a]['quote']
        symbol = config.TRADE_SYMBOL_ARR[a]['symbol']
        newKlineDataObjArr.append({'coin': coin, 'quote': quote, 'symbol': symbol, 'klineArr': [], 'dataError': False})

        klineArr[a] = klineArr[a].split('~')
        for b in range(len(klineArr[a])):
            klineArr[a][b] = klineArr[a][b].split('&')
            for c in range(len(klineArr[a][b])):
                klineArr[a][b][c] = float(klineArr[a][b][c])
            klineMin = int(klineArr[a][b][0])
            newKlineDataObjArr[a]['klineArr'].append([klineArr[a][b][1], klineArr[a][b][4], klineArr[a][b][2], klineArr[a][b][3], klineMin])  # open close high low

    if len(newKlineDataObjArr) > 0:
        config.ONE_MIN_KLINE_OBJ_ARR = newKlineDataObjArr


def update_symbol_info():
    url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'

    response = requests.request('GET', url, timeout=(3, 7)).json()
    symbols = response['symbols']

    for i in range(len(symbols)):
        thisInstrumentID = symbols[i]['symbol']

        priceTick = 0
        priceDecimal = ''
        amountDecimal = ''
        priceDecimalAmount = ''
        amountDecimalAmount = ''

        for c in range(len(symbols[i]['filters'])):
            if symbols[i]['filters'][c]['filterType'] == 'PRICE_FILTER':
                priceTick = float(symbols[i]['filters'][c]['tickSize'])
                thisDecimal = 0
                initPara = 10

                for d in range(20):
                    thisDecimal = thisDecimal + 1
                    initPara = round(initPara / 10, 10)

                    if initPara == float(symbols[i]['filters'][c]['tickSize']):
                        break

                priceDecimal = '%.' + str(thisDecimal - 1) + 'f'
                priceDecimalAmount = str(thisDecimal - 1)

            if symbols[i]['filters'][c]['filterType'] == 'LOT_SIZE':
                thisDecimal = 0
                initPara = 10

                for d in range(20):
                    thisDecimal = thisDecimal + 1
                    initPara = round(initPara / 10, 10)

                    if initPara == float(symbols[i]['filters'][c]['stepSize']):
                        break

                amountDecimal = '%.' + str(thisDecimal - 1) + 'f'
                amountDecimalAmount = str(thisDecimal - 1)

            if symbols[i]['filters'][c]['filterType'] == 'MARKET_LOT_SIZE':
                config.MARKET_MAX_SIZE_OBJ[thisInstrumentID] = float(symbols[i]['filters'][c]['maxQty'])
                config.MARKET_MIN_SIZE_OBJ[thisInstrumentID] = float(symbols[i]['filters'][c]['minQty'])

        config.PRICE_DECIMAL_OBJ[thisInstrumentID] = priceDecimal
        config.AMOUNT_DECIMAL_OBJ[thisInstrumentID] = amountDecimal
        config.PRICE_TICK_OBJ[thisInstrumentID] = priceTick
        config.PRICE_DECIMAL_AMOUNT_OBJ[thisInstrumentID] = priceDecimalAmount

        if amountDecimalAmount != '':
            config.AMOUNT_DECIMAL_AMOUNT_OBJ[thisInstrumentID] = int(amountDecimalAmount)


update_symbol_info()
while not 'BTCUSDT' in PRICE_DECIMAL_OBJ:
    FUNCTION_CLIENT.send_lark_msg_limit_one_min('mainConsole updateSymbolInfo')
    update_symbol_info()
    time.sleep(1)


def get_future_depth_by_symbol(symbol, limit):
    response = {}
    try:
        url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=' + str(limit)
        response = requests.request('GET', url, timeout=(0.5, 0.5)).json()
    except Exception as e:
        try:
            url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=' + str(limit)
            response = requests.request('GET', url, timeout=(1, 1)).json()
        except Exception as e:
            try:
                url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=' + str(limit)
                response = requests.request('GET', url, timeout=(1.5, 1.5)).json()
            except Exception as e:
                try:
                    url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=' + str(limit)
                    response = requests.request('GET', url, timeout=(2, 2)).json()
                except Exception as e:
                    print(e)
    return response


def get_position_info_arr_by_symbol(symbol):
    for positionIndex in range(len(config.POSITION_ARR)):
        if config.POSITION_ARR[positionIndex][0] == symbol:
            return [config.POSITION_ARR[positionIndex][2], config.POSITION_ARR[positionIndex][1]]
    return [0, 0]


def maker_shorts_order(shorts_price, shorts_once_trade_coin_quantity, symbol):
    global PRICE_MOVE_SYMBOL, SEND_PUBLIC_SERVER_TS, NEED_CANCEL_SHORTS_ORDER_ID_ARR, TRADE_INFO, EIGHT_HOURS_PROFIT, TRADE_INFO, FOUR_HOURS_PROFIT, EIGHT_HOURS_PROFIT, TWELVE_HOURS_PROFIT, TWENTY_FOUR_HOURS_PROFIT
    shorts_price = float(decimal.Decimal(config.PRICE_DECIMAL_OBJ[symbol] % (shorts_price)))

    coinQuantity = shorts_once_trade_coin_quantity

    config.ORDER_ID_INDEX = config.ORDER_ID_INDEX + 1
    newClientOrderId = config.ORDER_ID_SYMBOL + '_' + str(config.ORDER_ID_INDEX)
    result = {}

    try:
        result = config.REQUEST_CLIENT.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.SELL,
                                                           ordertype=OrderType.LIMIT, price=shorts_price, positionSide='BOTH', timeInForce=TimeInForce.GTX)
        result = json.loads(result)

        if 'code' in result and result['code'] != -5022 and result['code'] != -1001 and result['code'] != -2022:
            _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('shorts order error:' + str(result) + ',' + str(coinQuantity),))

        print('--------------')
        print(result)
    except Exception as e:
        _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('shortsM:' + str(e),))

    return result


def maker_close_longs_order(shorts_price, shorts_once_trade_coin_quantity, symbol):
    global PRICE_MOVE_SYMBOL, SEND_PUBLIC_SERVER_TS, NEED_CANCEL_CLOSE_SHORTS_ORDER_ID_ARR, TRADE_INFO, EIGHT_HOURS_PROFIT, TRADE_INFO, FOUR_HOURS_PROFIT, EIGHT_HOURS_PROFIT, TWELVE_HOURS_PROFIT, TWENTY_FOUR_HOURS_PROFIT
    shorts_price = float(decimal.Decimal(config.PRICE_DECIMAL_OBJ[symbol] % (shorts_price)))

    coinQuantity = shorts_once_trade_coin_quantity

    config.ORDER_ID_INDEX = config.ORDER_ID_INDEX + 1
    newClientOrderId = 'MC_' + str(config.ORDER_ID_INDEX)
    result = {}

    try:
        result = config.REQUEST_CLIENT.post_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=coinQuantity, side=OrderSide.SELL,
                                                           ordertype=OrderType.LIMIT,
                                                           price=shorts_price, positionSide='BOTH', timeInForce=TimeInForce.GTX)
        result = json.loads(result)

        if 'code' in result and result['code'] != -5022 and result['code'] != -1001 and result['code'] != -2022:
            _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min,
                                     ('close longs order error:' + str(result) + ',' + str(coinQuantity) + ',' + str(symbol),))

        print('--------------')
        print(result)
    except Exception as e:
        _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('shortsM:' + str(e),))

    return result


def maker_longs_order(longs_price, longs_once_trade_coin_quantity, symbol):
    global PRICE_MOVE_SYMBOL, SEND_PUBLIC_SERVER_TS, THIRTY_MINS_POLE_SCORE, RICE_DECIMAL_OBJ, NEED_CANCEL_LONGS_ORDER_ID_ARR, TRADE_INFO, EIGHT_HOURS_PROFIT, TRADE_INFO, FOUR_HOURS_PROFIT, EIGHT_HOURS_PROFIT, TWELVE_HOURS_PROFIT, TWENTY_FOUR_HOURS_PROFIT

    longs_price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (longs_price)))

    coin_quantity = longs_once_trade_coin_quantity

    config.ORDER_ID_INDEX = config.ORDER_ID_INDEX + 1
    new_client_order_id = config.ORDER_ID_SYMBOL + '_' + str(config.ORDER_ID_INDEX)
    result = {}

    try:
        result = config.REQUEST_CLIENT.post_order(newClientOrderId=new_client_order_id, reduceOnly=False, symbol=symbol, quantity=coin_quantity, side=OrderSide.BUY,
                                                           ordertype=OrderType.LIMIT,
                                                           price=longs_price, positionSide='BOTH', timeInForce=TimeInForce.GTX)
        result = json.loads(result)

        if 'code' in result and result['code'] != -5022 and result['code'] != -1001:
            _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('longs order error:' + str(result) + ',' + str(coin_quantity),))

        print('--------------')
        print(result)
    except Exception as e:
        _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('longsM:' + str(e),))

    return result


def maker_close_shorts_order(longs_price, longsOnceTradeCoinQuantity, symbol):
    global PRICE_MOVE_SYMBOL, SEND_PUBLIC_SERVER_TS, THIRTY_MINS_POLE_SCORE, RICE_DECIMAL_OBJ, NEED_CANCEL_CLOSE_LONGS_ORDER_ID_ARR, TRADE_INFO, EIGHT_HOURS_PROFIT, TRADE_INFO, FOUR_HOURS_PROFIT, EIGHT_HOURS_PROFIT, TWELVE_HOURS_PROFIT, TWENTY_FOUR_HOURS_PROFIT

    longs_price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % longs_price))

    coin_quantity = longsOnceTradeCoinQuantity

    config.ORDER_ID_INDEX = config.ORDER_ID_INDEX + 1
    new_client_order_id = 'MC_' + str(config.ORDER_ID_INDEX)
    result = {}

    try:
        result = config.REQUEST_CLIENT.post_order(newClientOrderId=new_client_order_id, reduceOnly=True, symbol=symbol, quantity=coin_quantity, side=OrderSide.BUY,
                                                           ordertype=OrderType.LIMIT,
                                                           price=longs_price, positionSide='BOTH', timeInForce=TimeInForce.GTX)
        result = json.loads(result)

        if 'code' in result and result['code'] != -5022 and result['code'] != -1001 and result['code'] != -2022:
            _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min,
                                     ('close shorts order error:' + str(result) + ',' + str(coin_quantity) + ',' + str(symbol),))

        print('--------------')
        print(result)
    except Exception as e:
        _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('longsM:' + str(e),))

    return result


def force_close_shorts(symbol):
    market_max_size = config.MARKET_MAX_SIZE_OBJ[symbol]
    config.ORDER_ID_INDEX = config.ORDER_ID_INDEX + 1
    new_client_order_id = 'forceCloseShorts_c_' + str(config.ORDER_ID_INDEX)

    try:
        result = config.REQUEST_CLIENT.post_market_order(newClientOrderId=new_client_order_id, reduceOnly=True, symbol=symbol, quantity=market_max_size, side=OrderSide.BUY,
                                                                  ordertype=OrderType.MARKET, price='0', positionSide='BOTH', timeInForce=TimeInForce.GTC)
        result = json.loads(result)

        if 'code' in result:
            config.FUNCTION_CLIENT.send_lark_msg_limit_one_min('force code:' + str(result))

        print(result)
    except Exception as e:
        print(e)

    config.ORDER_ID_INDEX = config.ORDER_ID_INDEX + 1
    new_client_order_id = 'forceCloseShorts_c_' + str(config.ORDER_ID_INDEX)

    try:
        result = config.REQUEST_CLIENT.post_market_order(newClientOrderId=new_client_order_id, reduceOnly=True, symbol=symbol, quantity=market_max_size, side=OrderSide.BUY,
                                                                  ordertype=OrderType.MARKET, price='0', positionSide='BOTH', timeInForce=TimeInForce.GTC)
        result = json.loads(result)
        print(result)
    except Exception as e:
        print(e)


def force_close_longs(symbol):
    marketMaxSize = config.MARKET_MAX_SIZE_OBJ[symbol]
    config.ORDER_ID_INDEX = config.ORDER_ID_INDEX + 1
    newClientOrderId = 'forceCloseLongs_c_' + str(config.ORDER_ID_INDEX)

    try:
        result = config.REQUEST_CLIENT.post_market_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=marketMaxSize, side=OrderSide.SELL,
                                                                  ordertype=OrderType.MARKET, price='0', positionSide='BOTH', timeInForce=TimeInForce.GTC)
        result = json.loads(result)

        if 'code' in result:
            config.FUNCTION_CLIENT.send_lark_msg_limit_one_min(' force code:' + str(result))

        print(result)
    except Exception as e:
        print(e)

    config.ORDER_ID_INDEX = config.ORDER_ID_INDEX + 1
    newClientOrderId = 'forceCloseLongs_c_' + str(config.ORDER_ID_INDEX)

    try:
        result = config.REQUEST_CLIENT.post_market_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=marketMaxSize, side=OrderSide.SELL,
                                                                  ordertype=OrderType.MARKET, price='0', positionSide='BOTH', timeInForce=TimeInForce.GTC)
        result = json.loads(result)
        print(result)
    except Exception as e:
        print(e)


def new_open_orders():
    global SECOND_NUMBER, SEND_POSITION_TS, CONDITION_AND_RATE_ARR_A, CONDITION_AND_RATE_ARR_B, MULTIPLE_OBJ_B, MULTIPLE_OBJ_A, UPDATE_VOL_CONDITION_A, UPDATE_VOL_CONDITION_B, FOUR_HOURS_VOL_OBJ_A, THREE_DAYS_VOL_OBJ_A, SECOND_NUMBER, FILL_WARN_TS, NEW_OPEN_CLASS, ONE_HOUR_POLE_SCORE, THIRTY_MINS_POLE_SCORE, NEED_CANCEL_SHORTS_ORDER_ID_ARR, NEED_CANCEL_LONGS_ORDER_ID_ARR, LAST_LONGS_ORDER_TS, SEND_PUBLIC_SERVER_TS, DATA_DELAY_WARN_TS, NEED_CANCEL_SHORTS_ORDER_ID_ARR, ONE_HOUR_CLOSE_OBJ_ARR, ONE_HOUR_POLE_OBJ, UPDATE_ONE_HOUR_POLE_OBJ_TS, MAKER_COMMISSION_RATE, UPDATE_THIRTY_MINS_POLE_OBJ_TS, THIRTY_MINS_POLE_OBJ, THIRTY_MINS_CLOSE_OBJ_ARR, STOP_SERVER_WARN_TS, DAY_INFO_OBJ, CLOSE_OBJ_ARR, TRADE_INFO, START_TRADE_TS, NOW_POSITION_AMOUNT, END_TRADE_TS, LAST_OPEN_MID_PRICE, NEED_CANCEL_LONGS_ORDER_ID_ARR, SHORTS_DEPTH_CHANGE_RATE, LONGS_DEPTH_CHANGE_RATE, FOUR_HOURS_PROFIT, EIGHT_HOURS_PROFIT, TWELVE_HOURS_PROFIT, TWENTY_FOUR_HOURS_PROFIT

    now = int(time.time() * 1000)

    allProfit = 0
    for oneMinKlineObjArrIndex in range(len(ONE_MIN_KLINE_OBJ_ARR)):

        symbol = ONE_MIN_KLINE_OBJ_ARR[oneMinKlineObjArrIndex]['symbol']

        symbolPositionInfoArr = get_position_info_arr_by_symbol(symbol)
        positionCost = symbolPositionInfoArr[1]
        symbolPositionAmt = symbolPositionInfoArr[0]
        positionValue = abs(positionCost * symbolPositionAmt)
        oneMinArr = ONE_MIN_KLINE_OBJ_ARR[oneMinKlineObjArrIndex]['klineArr']
        dataError = ONE_MIN_KLINE_OBJ_ARR[oneMinKlineObjArrIndex]['dataError']

        nowOpenPrice = float(oneMinArr[len(oneMinArr) - 1][0])
        nowClosePrice = float(oneMinArr[len(oneMinArr) - 1][1])
        nowHighPrice = float(oneMinArr[len(oneMinArr) - 1][2])
        nowLowPrice = float(oneMinArr[len(oneMinArr) - 1][3])

        allProfit = allProfit + symbolPositionAmt * (float(oneMinArr[len(oneMinArr) - 1][1]) - positionCost)

        openQuantity = float(decimal.Decimal(config.AMOUNT_DECIMAL_OBJ[symbol] % (100 / nowClosePrice)))
        closeQuantity = float(decimal.Decimal(config.AMOUNT_DECIMAL_OBJ[symbol] % (100 / nowClosePrice)))
        oneMinRate = config.FUNCTION_CLIENT.get_percent_num(float(oneMinArr[len(oneMinArr) - 1][1]) - float(oneMinArr[len(oneMinArr) - 1 - 1][1]),
                                                                     float(oneMinArr[len(oneMinArr) - 1 - 1][1]))

        # 一分钟下跌超过1%，并且该币种没有仓位则开多
        if oneMinRate < -1 and positionValue == 0:
            result = maker_longs_order(nowClosePrice, openQuantity, symbol)
            errorTime = 1

            while 'code' in result and (result['code'] == -5022 or result['code'] == -1001):
                result = maker_longs_order(nowClosePrice, openQuantity, symbol)
                errorTime = errorTime + 1

                get_tick_data()

                if errorTime > 3:
                    _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg, (' errorTime>3 A:' + symbol,))
                    time.sleep(errorTime * 0.1)

        # 一分钟上涨超过0.5%，并且该币种没有仓位则平多
        if oneMinRate > 0.5 and positionValue != 0:
            result = maker_close_longs_order(nowClosePrice, closeQuantity, symbol)
            errorTime = 1

            while ('code' in result and (result['code'] == -5022 or result['code'] == -1001)):
                result = maker_close_longs_order(shortsPriceObj['price'], closeQuantity, symbol)
                errorTime = errorTime + 1
                get_tick_data()

                if errorTime > 3:
                    _thread.start_new_thread(config.FUNCTION_CLIENT.send_lark_msg, (' errorTime>3 A:' + symbol,))
                    time.sleep(errorTime * 0.1)

    # 当前持仓总利润低于-100则强制平仓

    if allProfit <= -100:
        for i in range(len(config.POSITION_ARR)):

            if config.POSITION_ARR[i][2] < 0:
                _thread.start_new_thread(force_close_shorts, (config.POSITION_ARR[i][0],))

            if config.POSITION_ARR[i][2] > 0:
                _thread.start_new_thread(force_close_longs, (config.POSITION_ARR[i][0],))

        config.FUNCTION_CLIENT.send_lark_msg_limit_one_min('allProfit<=-100:' + str(allProfit))


if __name__ == '__main__':
    get_one_min_data()
    get_tick_data()

    GET_ONE_MIN_DATA_TS = 0

    print('begin')

    while 1:
        now = int(time.time() * 1000)

        try:
            if now - GET_ONE_MIN_DATA_TS > 60 * 1000:
                GET_ONE_MIN_DATA_TS = now
                get_one_min_data()

            get_tick_data()

            if UPDATE_DATA_STR:
                UPDATE_DATA_STR = False
                new_open_orders()

            RUN_TIME = RUN_TIME + 1
        except Exception as e:
            ex = traceback.format_exc()
            FUNCTION_CLIENT.send_lark_msg_limit_one_min(str(ex))
            print(e)
            print(ex)
            time.sleep(1)
