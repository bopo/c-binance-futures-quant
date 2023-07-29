import _thread
import decimal
import json
import random
import time

import httpx
from httpx._config import Timeout
# from binance_spot.requestclient import RequestClient as SpotRequestClient
from binance.client import Client as SpotRequestClient

from .common import FunctionClient
from .kernel.model.constant import *
from .kernel.requestclient import RequestClient

# from bottle import post
# from bottle import request
# from bottle import response

FUNCTION_CLIENT = FunctionClient(larkMsgSymbol='webServer', connectMysqlPool=True)

tableName = 'trade_machine_status'

tableExit = False

sql = 'show tables;'
tableData = FUNCTION_CLIENT.mysql_select(sql, [])

for a in range(len(tableData)):
    if tableData[a][0] == tableName:
        tableExit = True

if not tableExit:
    sql = """CREATE TABLE `""" + tableName + """` (
    `id` int NOT NULL AUTO_INCREMENT,
    `private_ip` varchar(255) DEFAULT NULL,
    `insert_ts` bigint DEFAULT NULL,
    `update_ts` bigint DEFAULT NULL,
    `status` varchar(255) DEFAULT NULL,
    `run_time` bigint DEFAULT NULL,

    PRIMARY KEY (`id`) USING BTREE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3
    ;
    """

    FUNCTION_CLIENT.mysql_commit(sql, [])

tableName = 'machine_status'

tableExit = False

sql = 'show tables;'
tableData = FUNCTION_CLIENT.mysql_select(sql, [])

for a in range(len(tableData)):
    if tableData[a][0] == tableName:
        tableExit = True

if not tableExit:
    sql = """CREATE TABLE `""" + tableName + """` (
    `id` int NOT NULL AUTO_INCREMENT,
    `private_ip` varchar(255) DEFAULT NULL,
    `insert_ts` bigint DEFAULT NULL,
    `update_ts` bigint DEFAULT NULL,
    `status` varchar(255) DEFAULT NULL,
    `symbol` varchar(255) DEFAULT NULL,
    `run_time` bigint DEFAULT NULL,

    PRIMARY KEY (`id`) USING BTREE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3
    ;
    """

    FUNCTION_CLIENT.mysql_commit(sql, [])

ORDER_ID_SYMBOL = 'wTake'

PRIVATE_IP = FUNCTION_CLIENT.get_private_ip()

ORDER_ID_INDEX = random.randint(1, 100000)

PRICE_DECIMAL_OBJ = {}

AMOUNT_DECIMAL_OBJ = {}

PRICE_TICK_OBJ = {}

PRICE_DECIMAL_AMOUNT_OBJ = {}

AMOUNT_DECIMAL_AMOUNT_OBJ = {}

MARKET_MAX_SIZE_OBJ = {}

MARKET_MIN_SIZE_OBJ = {}


def updateSymbolInfo():
    global PRICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, PRICE_DECIMAL_AMOUNT_OBJ, AMOUNT_DECIMAL_AMOUNT_OBJ, PRICE_TICK_OBJ, MARKET_MAX_SIZE_OBJ, MARKET_MIN_SIZE_OBJ
    url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'

    response = httpx.get(url, timeout=Timeout(7)).json()
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
                MARKET_MAX_SIZE_OBJ[thisInstrumentID] = float(symbols[i]['filters'][c]['maxQty'])
                MARKET_MIN_SIZE_OBJ[thisInstrumentID] = float(symbols[i]['filters'][c]['minQty'])
        PRICE_DECIMAL_OBJ[thisInstrumentID] = priceDecimal
        AMOUNT_DECIMAL_OBJ[thisInstrumentID] = amountDecimal
        PRICE_TICK_OBJ[thisInstrumentID] = priceTick
        PRICE_DECIMAL_AMOUNT_OBJ[thisInstrumentID] = priceDecimalAmount
        if amountDecimalAmount != '':
            AMOUNT_DECIMAL_AMOUNT_OBJ[thisInstrumentID] = int(amountDecimalAmount)


updateSymbolInfo()

while not 'BTCUSDT' in PRICE_DECIMAL_OBJ:
    FUNCTION_CLIENT.send_lark_msg('mainConsole updateSymbolInfo')
    updateSymbolInfo()
    time.sleep(1)


def takeElemZero(elem):
    return float(elem[0])


def getFutureDepthBySymbol(symbol, limit):
    response = {}
    try:
        url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=50'
        response = httpx.get(url, timeout=(0.5, 0.5)).json()
    except Exception as e:
        try:
            url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=50'
            response = httpx.get(url, timeout=(1, 1)).json()
        except Exception as e:
            try:
                url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=50'
                response = httpx.get(url, timeout=(2, 2)).json()
            except Exception as e:
                print(e)
    return response


def getKline(symbol, interval, limit):
    nowPrice = 0
    klineDataArr = []
    try:
        url = 'https://fapi.binance.com/fapi/v1/klines?symbol=' + symbol + '&interval=' + interval + '&limit=' + str(limit)
        klineDataArr = httpx.get(url, timeout=(0.5, 0.5)).json()
        klineDataArr.sort(key=takeElemZero, reverse=False)
    except Exception as e:
        print(e)
        try:
            url = 'https://fapi.binance.com/fapi/v1/klines?symbol=' + symbol + '&interval=' + interval + '&limit=' + str(limit)
            klineDataArr = httpx.get(url, timeout=(1, 1)).json()
            klineDataArr.sort(key=takeElemZero, reverse=False)
        except Exception as e:
            print(e)
            try:
                url = 'https://fapi.binance.com/fapi/v1/klines?symbol=' + symbol + '&interval=' + interval + '&limit=' + str(limit)
                klineDataArr = httpx.get(url, timeout=(2, 2)).json()
                klineDataArr.sort(key=takeElemZero, reverse=False)
            except Exception as e:
                print(e)
    return klineDataArr


def getFutureNowPriceByDepth(symbol):
    nowPrice = 0
    try:
        url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=5'
        response = httpx.get(url, timeout=(0.5, 0.5)).json()
        nowPrice = (float(response['asks'][0][0]) + float(response['bids'][0][0])) / 2
    except Exception as e:
        try:
            url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=5'
            response = httpx.get(url, timeout=(1, 1)).json()
            nowPrice = (float(response['asks'][0][0]) + float(response['bids'][0][0])) / 2
        except Exception as e:
            try:
                url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=5'
                response = httpx.get(url, timeout=(2, 2)).json()
                nowPrice = (float(response['asks'][0][0]) + float(response['bids'][0][0])) / 2
            except Exception as e:
                print(e)
    return nowPrice


def getSpotNowPriceByDepth(symbol):
    nowPrice = 0
    try:
        url = 'https://api.binance.com/api/v1/depth?symbol=' + symbol + '&limit=5'
        response = httpx.get(url, timeout=(0.5, 0.5)).json()
        nowPrice = (float(response['asks'][0][0]) + float(response['bids'][0][0])) / 2
    except Exception as e:
        try:
            url = 'https://api.binance.com/api/v1/depth?symbol=' + symbol + '&limit=5'
            response = httpx.get(url, timeout=(1, 1)).json()
            nowPrice = (float(response['asks'][0][0]) + float(response['bids'][0][0])) / 2
        except Exception as e:
            try:
                url = 'https://api.binance.com/api/v1/depth?symbol=' + symbol + '&limit=5'
                response = httpx.get(url, timeout=(2, 2)).json()
                nowPrice = (float(response['asks'][0][0]) + float(response['bids'][0][0])) / 2
            except Exception as e:
                print(e)
    return nowPrice


BUY_BNB_TS = False


def buyBNB(apiKey, buyBNBAmount, bnbPrice, assetType):
    global BUY_BNB_TS, API_OBJ, AMOUNT_DECIMAL_OBJ
    now = int(time.time())
    symbol = 'BNB' + assetType
    print('buyBNB')
    if now - BUY_BNB_TS > 60:
        BUY_BNB_TS = now

        spot_request_client = SpotRequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        result = spot_request_client.transfer('UMFUTURE_MAIN', assetType, bnbPrice * buyBNBAmount * 1.05)
        result = json.loads(result)

        amount = buyBNBAmount
        amount = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (amount))
        betPrice = decimal.Decimal('%.1f' % (bnbPrice * 1.005))

        spot_request_client = SpotRequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        result = spot_request_client.post_order(symbol=symbol, quantity=amount, side=OrderSide.BUY, ordertype=OrderType.LIMIT, price=betPrice, positionSide='BOTH',
                                                timeInForce=TimeInForce.GTC)
        result = json.loads(result)

        time.sleep(1)

        spot_request_client = SpotRequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        result = spot_request_client.get_account_information()
        result = json.loads(result)

        result = result['balances']
        bnbBalance = 0
        usdtBalance = 0
        for i in range(len(result)):
            if result[i]['asset'] == assetType:
                usdtBalance = float(result[i]['free'])
            if result[i]['asset'] == 'BNB':
                bnbBalance = float(result[i]['free'])

        spot_request_client = spot_request_client = SpotRequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        result = spot_request_client.transfer('MAIN_UMFUTURE', 'BNB', bnbBalance)
        result = json.loads(result)
        spot_request_client = spot_request_client = SpotRequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        result = spot_request_client.transfer('MAIN_UMFUTURE', assetType, usdtBalance)
        result = json.loads(result)
        return True


INCOME_OBJ = {
    '15m': {'c': 0, 'p': 0, 's': 0},
    '30m': {'c': 0, 'p': 0, 's': 0},
    '1h': {'c': 0, 'p': 0, 's': 0},
    '4h': {'c': 0, 'p': 0, 's': 0},
    'oneDay': {'c': 0, 'p': 0, 's': 0},
    'today': {'c': 0, 'p': 0, 's': 0}
}

SYMBOL_INCOME_OBJ = {
}

LAST_UPDATE_INCOME_TS = 0
INCOME_LOCK = False

ACCOUNT_INFO_UPDATE_TS = 0
BNB_PRICE = 0
POSITION_ARR = []
ASSETS_ARR = []
for i in range(10):
    POSITION_ARR.append([])
    ASSETS_ARR.append([])


def getBinanceAccountInfo(apiIndex, apiKey, autoBuyBnb, beginMinBnbMoney, buyBNBMoney, accessToken):
    global ACCOUNT_INFO_UPDATE_TS, POSITION_ARR, ASSETS_ARR, BNB_PRICE
    now = int(time.time() * 1000)
    buyBNBResult = False
    if now - ACCOUNT_INFO_UPDATE_TS > 60000:
        positionsArr = []
        assetsArr = []
        result = {}
        bnbAmount = -1
        usdtAmount = -1
        busdAmount = -1
        try:
            request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
            result = request_client.get_account_information()
            result = json.loads(result)
            for i in range(len(result['positions'])):
                if float(result['positions'][i]['positionAmt']) != 0:
                    positionsArr.append(result['positions'][i])

            # positionsArr = result["positions"]
            assetsArr = result['assets']
            for i in range(len(assetsArr)):
                if assetsArr[i]['asset'] == 'BNB':
                    bnbAmount = float(assetsArr[i]['marginBalance'])
                if assetsArr[i]['asset'] == 'USDT':
                    usdtAmount = float(assetsArr[i]['marginBalance'])
                if assetsArr[i]['asset'] == 'BUSD':
                    busdAmount = float(assetsArr[i]['marginBalance'])
            BNB_PRICE = getSpotNowPriceByDepth('BNBUSDT')
            beginMinBnbAmount = beginMinBnbMoney / BNB_PRICE
            buyBNBAmount = buyBNBMoney / BNB_PRICE
            if autoBuyBnb and bnbAmount != -1 and bnbAmount < beginMinBnbAmount and usdtAmount >= buyBNBMoney * 1.1:
                buyAsset = 'USDT'
                buyBNBResult = buyBNB(apiKey, buyBNBAmount, BNB_PRICE, buyAsset)
            elif autoBuyBnb and bnbAmount != -1 and bnbAmount < beginMinBnbAmount and busdAmount >= buyBNBMoney * 1.1:
                buyAsset = 'BUSD'
                buyBNBResult = buyBNB(apiKey, buyBNBAmount, BNB_PRICE, buyAsset)
            POSITION_ARR[apiIndex] = positionsArr
            ASSETS_ARR[apiIndex] = assetsArr

        except Exception as e:
            print(e)
        ACCOUNT_INFO_UPDATE_TS = now
    return [POSITION_ARR, ASSETS_ARR, buyBNBResult, BNB_PRICE]


DEPTH_UPDATE_TS = 0
LAST_BINANCE_RESPONSE_OBJ = {}

API_OBJ = {}


def updateAPIObj(apiKey):
    global API_OBJ
    if apiKey in API_OBJ:
        return
    else:
        sql = 'select `binanceApiArr` from user'
        userData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
        for a in range(len(userData)):
            binanceApiArr = json.loads(userData[a][0])
            for b in range(len(binanceApiArr)):
                if apiKey == binanceApiArr[b]['apiKey']:
                    API_OBJ[binanceApiArr[b]['apiKey']] = binanceApiArr[b]['apiSecret']
                    break


def cancelBinanceOrder(symbol, apiKey):
    global API_OBJ
    result = {}
    try:
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        result = request_client.cancel_all_orders(symbol=symbol)
        result = json.loads(result)
    except Exception as e:
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        result = request_client.cancel_all_orders(symbol=symbol)
        result = json.loads(result)
        print(e)
    resp = json.dumps({'s': 'ok', 'result': result})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


def getPolePrice(symbol, mins):
    stopLossPrice = 0
    mins = int(mins)
    highPrice = 0
    lowPrice = 99999999
    if mins < 500:
        klineArr = getKline(symbol, '1m', mins)
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif mins < 7500:
        klineArr = getKline(symbol, '15m', int(mins / 15))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif mins < 30000:
        klineArr = getKline(symbol, '1h', int(mins / 60))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif mins < 120000:
        klineArr = getKline(symbol, '4h', int(mins / 240))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif mins < 720000:
        klineArr = getKline(symbol, '1d', int(mins / 1440))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])

    return [highPrice, lowPrice]


def getStopProfitPriceByTime(symbol, stopProfitPara, positionDirection):
    stopProfitPrice = 0
    stopProfitTime = int(stopProfitPara)
    highPrice = 0
    lowPrice = 99999999
    if stopProfitTime < 500:
        klineArr = getKline(symbol, '1m', stopProfitTime)
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif stopProfitTime < 7500:
        klineArr = getKline(symbol, '15m', int(stopProfitTime / 15))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif stopProfitTime < 30000:
        klineArr = getKline(symbol, '1h', int(stopProfitTime / 60))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif stopProfitTime < 120000:
        klineArr = getKline(symbol, '4h', int(stopProfitTime / 240))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif stopProfitTime < 720000:
        klineArr = getKline(symbol, '1d', int(stopProfitTime / 1440))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])

    if positionDirection == 'shorts':
        stopProfitPrice = lowPrice
    if positionDirection == 'longs':
        stopProfitPrice = highPrice

    return stopProfitPrice


def takeElemTime(elem):
    return float(elem['time'])


LAST_RECORD_TS = 0
RECORD_LOCK = False

CHAT_OBJ = {}

UPDATE_DAY_INCOME_TS = 0


def updateDayIncome():
    global UPDATE_DAY_INCOME_TS
    print('update_day_income')
    now = int(time.time())
    if now - UPDATE_DAY_INCOME_TS > 30:
        UPDATE_DAY_INCOME_TS = now
        accessToken = str(request.forms.get('accessToken'))
        incomeDayTableName = accessToken + '_income_day'
        incomeTableName = accessToken + '_income'
        sql = 'select `dayBeginTime` from ' + incomeDayTableName + ' order by id desc limit 1'
        lastBinanceTsData = ()

        con = pool.get_connection()
        c = con.cursor()
        try:
            c.execute(sql, [])
            lastBinanceTsData = c.fetchall()
            normal = True
        except Exception as e:
            print(e)
            print(e)
            tableExit = False
            sql = 'show tables;'
            tableData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
            for a in range(len(tableData)):
                if tableData[a][0] == incomeDayTableName:
                    tableExit = True

            if not tableExit:
                sql = """CREATE TABLE `""" + incomeDayTableName + """`  (
                  `id` int(11) NOT NULL AUTO_INCREMENT,
                  `dayBeginTime` varchar(255) NULL,
                  `dayEndTime` varchar(255) NULL,
                  `binanceCommission` double(30,10) NULL,
                  `zjyCommission` double(30,10) NULL,
                  `pnl` double(30,10) NULL,
                  PRIMARY KEY (`id`) USING BTREE
                );"""
                FUNCTION_CLIENT.mysql_pool_commit(sql, [])
        try:
            con.close()
        except Exception as e:
            print(q)
            print(e)

        initIncomeDayTime = '2022-11-20 00:00:00'
        initIncomeDayTs = FUNCTION_CLIENT.turn_ts_to_time(initIncomeDayTime)
        lastIncomeDayTs = 0
        if len(lastBinanceTsData) > 0:
            lastIncomeDayTs = FUNCTION_CLIENT.turn_ts_to_time(lastBinanceTsData[0][0])
        if lastIncomeDayTs == 0:
            lastIncomeDayTs = initIncomeDayTs
        nowTs = int(time.time())
        todayTs = nowTs - nowTs % 86400 - 8 * 3600

        needInsertDay = int((todayTs - lastIncomeDayTs) / 86400)
        print('todayTs:' + str(todayTs))
        print('lastIncomeDayTs:' + str(lastIncomeDayTs))
        for i in range(needInsertDay):
            endDayTs = lastIncomeDayTs + 86400 * (i + 1)
            beginDayTs = lastIncomeDayTs + 86400 * i
            sql = 'select `incomeType`,`income`,`asset`,`bnbPrice`,`commission` from ' + incomeTableName + ' where binance_ts>%s and binance_ts<=%s'
            incomeData = FUNCTION_CLIENT.mysql_pool_select(sql, [beginDayTs * 1000, endDayTs * 1000])
            dayBinanceCommission = 0
            dayZjyCommission = 0
            dayPnl = 0
            for incomeDataIndex in range(len(incomeData)):
                if incomeData[incomeDataIndex][0] == 'COMMISSION':
                    if incomeData[incomeDataIndex][2] == 'BNB':
                        dayBinanceCommission = dayBinanceCommission + incomeData[incomeDataIndex][1] * incomeData[incomeDataIndex][3]
                    elif incomeData[incomeDataIndex][2] == 'USDT' or incomeData[incomeDataIndex][2] == 'BUSD':
                        dayBinanceCommission = dayBinanceCommission + incomeData[incomeDataIndex][1]
                elif incomeData[incomeDataIndex][0] == 'REALIZED_PNL':
                    if incomeData[incomeDataIndex][2] == 'BNB':
                        dayPnl = dayPnl + incomeData[incomeDataIndex][1] * incomeData[incomeDataIndex][3]
                    elif incomeData[incomeDataIndex][2] == 'USDT' or incomeData[incomeDataIndex][2] == 'BUSD':
                        dayPnl = dayPnl + incomeData[incomeDataIndex][1]
                dayZjyCommission = dayZjyCommission + incomeData[incomeDataIndex][4]

            print(FUNCTION_CLIENT.turn_ts_to_time(beginDayTs))
            sql = 'select `id` from ' + incomeDayTableName + ' where dayBeginTime=%s'
            incomeData = FUNCTION_CLIENT.mysql_pool_select(sql, [FUNCTION_CLIENT.turn_ts_to_time(beginDayTs)])
            if len(incomeData) == 0:
                sql = 'INSERT INTO ' + incomeDayTableName + ' (`dayBeginTime`, `dayEndTime`,`binanceCommission`,`pnl`,`zjyCommission`)  VALUES (%s,%s,%s,%s,%s);'
                FUNCTION_CLIENT.mysql_pool_commit(sql, [FUNCTION_CLIENT.turn_ts_to_time(beginDayTs), FUNCTION_CLIENT.turn_ts_to_time(endDayTs), dayBinanceCommission, dayPnl,
                                                        dayZjyCommission])
            else:
                sql = 'update ' + incomeDayTableName + ' set `zjyCommission`=%s,`pnl`=%s,`zjyCommission`=%s where `dayEndTime`=%s '
                FUNCTION_CLIENT.mysql_pool_commit(sql, [dayBinanceCommission, dayPnl, dayZjyCommission, FUNCTION_CLIENT.turn_ts_to_time(endDayTs)])


GET_DAY_INCOME_TS = 0
GET_DAY_INCOME_TODAY_TS = 0
DAY_INCOME_DATA = []

ONE_MIN_UPDATE_TS = 0
ONE_MIN_KLINE = []

POSITION_RECORD_TABLE_NAME_OBJ = {
    'ALL': 'position_record_all',
    'ETHUSDT': 'position_record_a',
    'BTCUSDT': 'position_record_b',

    # "ETHBUSD":"position_record_c",

    'ETHUSDT_2': 'position_record_d',
    'BTCUSDT_2': 'position_record_e',
}

CUSTOMIZE_DANGEROUS_DATA_ARR = []
CUSTOMIZE_DANGEROUS_DATA_ARR_UPDATE_TS = 0
TRADE_SERVER_STATUS_DATA = []
UPDATE_TRADE_SERVER_STATUS_DATA_TS = 0


def updateTradeServerStatusData():
    global TRADE_SERVER_STATUS_DATA, UPDATE_TRADE_SERVER_STATUS_DATA_TS
    now = int(time.time())
    if now - UPDATE_TRADE_SERVER_STATUS_DATA_TS > 5:
        UPDATE_TRADE_SERVER_STATUS_DATA_TS = now
        sql = 'select `extraPara`,`runInfo`,`symbol`,`privateIP`,`name`,`mySymbol`,`updateTs`,`updateTime` from trade_server_status'
        data = FUNCTION_CLIENT.mysql_pool_select(sql, [])
        TRADE_SERVER_STATUS_DATA = []
        for i in range(len(data)):
            extraPara = json.loads(data[i][0])
            TRADE_SERVER_STATUS_DATA.append({
                'extraPara': extraPara,
                'runInfo': json.loads(data[i][1]),
                'symbol': data[i][2],
                'privateIP': data[i][3],
                'name': data[i][4],
                'mySymbol': data[i][5],
                'updateTs': data[i][6],
                'updateTime': data[i][7],
                'customizeDangerousData': extraPara
            })


GET_LOSS_LIMIT_TIME_DATA_TS = 0
LOSS_LIMIT_TIME_DATA_ARR = []


def getLossLimitTimeData(forceUpdate):
    global GET_LOSS_LIMIT_TIME_DATA_TS, LOSS_LIMIT_TIME_DATA_ARR
    now = int(time.time())
    if (now - GET_LOSS_LIMIT_TIME_DATA_TS > 60) or forceUpdate:
        GET_LOSS_LIMIT_TIME_DATA_TS = now
        sql = 'select `symbol`,`limitTime` from loss_limit_time'
        lossLimitTimeData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
        LOSS_LIMIT_TIME_DATA_ARR = []
        for i in range(len(lossLimitTimeData)):
            LOSS_LIMIT_TIME_DATA_ARR.append({
                'symbol': lossLimitTimeData[i][0],
                'limitTime': lossLimitTimeData[i][1]
            })


ETH_1M_KLINE_ARR = []

BTC_1M_KLINE_ARR = []

ETH_TODAY_BEGIN_PRICE = {'price': 0, 'updateTs': 0}

BTC_TODAY_BEGIN_PRICE = {'price': 0, 'updateTs': 0}

TICK_ARR = []

UPDATE_BINANCE_DATA_TS = 0


def updateBinanceData():
    global TICK_ARR, ETH_1M_KLINE_ARR, BTC_1M_KLINE_ARR, UPDATE_BINANCE_DATA_TS, ETH_TODAY_BEGIN_PRICE, BTC_TODAY_BEGIN_PRICE
    now = int(time.time())
    if now - UPDATE_BINANCE_DATA_TS >= 1:
        UPDATE_BINANCE_DATA_TS = now
        try:
            klineAmount = 99
            url = 'https://fapi.binance.com/fapi/v1/klines?symbol=ETHUSDT&interval=1m&limit=' + str(klineAmount)
            ethKlineData = httpx.get(url, timeout=(1, 1), headers={}).json()
            if len(ethKlineData) == klineAmount:
                ETH_1M_KLINE_ARR = ethKlineData
        except Exception as e:
            print(e)

        try:
            klineAmount = 99
            url = 'https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&limit=' + str(klineAmount)
            btcKlineData = httpx.get(url, timeout=(1, 1), headers={}).json()
            if len(btcKlineData) == klineAmount:
                BTC_1M_KLINE_ARR = btcKlineData
        except Exception as e:
            print(e)

        try:
            url = 'https://fapi.binance.com/fapi/v1/ticker/price'
            tickArr = httpx.get(url, timeout=(1, 1)).json()
            if len(tickArr) > 100:
                TICK_ARR = tickArr
        except Exception as e:
            print(e)


ETH_TURN_PRICE = 0

BTC_TURN_PRICE = 0

TURN_PRICE_UPDATE_TS = 0

ETH_TURN_TS = 0

BTC_TURN_TS = 0


def updateTurnPrice():
    global ETH_TURN_PRICE, BTC_TURN_PRICE, TURN_PRICE_UPDATE_TS, ETH_TURN_TS, BTC_TURN_TS
    now = int(time.time())
    for key in NEW_API_OBJ:
        if now - TURN_PRICE_UPDATE_TS > 60:
            TURN_PRICE_UPDATE_TS = now
            sql = 'select `positionAmt` from position_record_a order by id desc limit 1'
            positionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
            positionAmt = positionRecordData[0][0]
            if positionAmt > 0:
                sql = 'select `price`,`ts` from position_record_a where positionAmt<0 order by id desc limit 1'
                lastTurnPositionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
                ETH_TURN_PRICE = lastTurnPositionRecordData[0][0]
                ETH_TURN_TS = lastTurnPositionRecordData[0][1]
            if positionAmt <= 0:
                sql = 'select `price`,`ts` from position_record_a where positionAmt>0 order by id desc limit 1'
                lastTurnPositionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
                ETH_TURN_PRICE = lastTurnPositionRecordData[0][0]
                ETH_TURN_TS = lastTurnPositionRecordData[0][1]

            sql = 'select `positionAmt` from position_record_b order by id desc limit 1'
            positionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
            positionAmt = positionRecordData[0][0]
            if positionAmt > 0:
                sql = 'select `price`,`ts` from position_record_b where positionAmt<0 order by id desc limit 1'
                lastTurnPositionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
                BTC_TURN_PRICE = lastTurnPositionRecordData[0][0]
                BTC_TURN_TS = lastTurnPositionRecordData[0][1]
            if positionAmt <= 0:
                sql = 'select `price`,`ts` from position_record_b where positionAmt>0 order by id desc limit 1'
                lastTurnPositionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
                BTC_TURN_PRICE = lastTurnPositionRecordData[0][0]
                BTC_TURN_TS = lastTurnPositionRecordData[0][1]


WATCH_INFO_UPDATE_TS = 0
WATCH_INFO_OBJ = {}

TRADE_MACHINE_STATUS_DATA = {}
UPDATE_TRADE_MACHINE_STATUS_DATA_TS = 0
AVERAGE_RUN_TIME = 0

SYMBOL_DATA_OBJ = {}

UPDATE_ONE_DAY_RATE_TS = 0


def takeQuotVolume(elem):
    return float(elem['quoteVolume'])


BIG_LOSS_TRADES_ARR = []
UPDATE_BIG_LOSS_TRADES_DARA_TS = 0

SYMBOL_LAST_INSEART_TS_OBJ = {}


def takeShortsOrder(shortsPrice, shortsOnceTradeCoinQuantity, tradeType, symbol, key, secret):
    global FUNCTION_CLIENT, ORDER_ID_SYMBOL, PRICE_MOVE_SYMBOL, PRIVATE_IP, PUBLIC_SERVER_IP, SEND_PUBLIC_SERVER_TS, PRICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, ORDER_ID_INDEX, REQUEST_CLIENT, NEED_CANCEL_SHORTS_ORDER_ID_ARR, TRADE_INFO, EIGHT_HOURS_PROFIT, TRADE_INFO, FOUR_HOURS_PROFIT, EIGHT_HOURS_PROFIT, TWELVE_HOURS_PROFIT, TWENTY_FOUR_HOURS_PROFIT
    shortsPrice = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (shortsPrice)))

    coinQuantity = shortsOnceTradeCoinQuantity

    ORDER_ID_INDEX = ORDER_ID_INDEX + 1
    newClientOrderId = ORDER_ID_SYMBOL + '_' + tradeType + '_' + str(ORDER_ID_INDEX)
    result = {}

    try:
        request_client = RequestClient(api_key=key, secret_key=secret)
        result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.SELL,
                                           ordertype=OrderType.LIMIT, price=shortsPrice, positionSide='BOTH', timeInForce=TimeInForce.GTC)
        result = json.loads(result)

        if 'code' in result and result['code'] == -1001:
            request_client = RequestClient(api_key=key, secret_key=secret)
            result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.SELL,
                                               ordertype=OrderType.LIMIT, price=shortsPrice, positionSide='BOTH', timeInForce=TimeInForce.GTC)
            result = json.loads(result)

        if 'code' in result and result['code'] != -5022 and result['code'] != -1001 and result['code'] != -2022:
            _thread.start_new_thread(FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('shorts order error:' + str(result) + ',' + str(coinQuantity),))

        print('--------------')
        print(result)
    except Exception as e:
        _thread.start_new_thread(FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('shortsM:' + str(e),))

    return result


def takeLongsOrder(longsPrice, longsOnceTradeCoinQuantity, tradeType, symbol, key, secret):
    global FUNCTION_CLIENT, ORDER_ID_SYMBOL, PRICE_MOVE_SYMBOL, PRIVATE_IP, PUBLIC_SERVER_IP, SEND_PUBLIC_SERVER_TS, PRIVATE_IP, THIRTY_MINS_POLE_SCORE, RICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, ORDER_ID_INDEX, REQUEST_CLIENT, NEED_CANCEL_LONGS_ORDER_ID_ARR, TRADE_INFO, EIGHT_HOURS_PROFIT, TRADE_INFO, FOUR_HOURS_PROFIT, EIGHT_HOURS_PROFIT, TWELVE_HOURS_PROFIT, TWENTY_FOUR_HOURS_PROFIT

    longsPrice = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (longsPrice)))

    coinQuantity = longsOnceTradeCoinQuantity

    ORDER_ID_INDEX = ORDER_ID_INDEX + 1
    newClientOrderId = ORDER_ID_SYMBOL + '_' + tradeType + '_' + str(ORDER_ID_INDEX)
    result = {}

    try:
        request_client = RequestClient(api_key=key, secret_key=secret)
        result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.BUY, ordertype=OrderType.LIMIT,
                                           price=longsPrice, positionSide='BOTH', timeInForce=TimeInForce.GTC)
        result = json.loads(result)

        if 'code' in result and result['code'] == -1001:
            request_client = RequestClient(api_key=key, secret_key=secret)
            result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.BUY,
                                               ordertype=OrderType.LIMIT, price=longsPrice, positionSide='BOTH', timeInForce=TimeInForce.GTC)
            result = json.loads(result)

        if 'code' in result and result['code'] != -5022 and result['code'] != -1001:
            _thread.start_new_thread(FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('longs order error:' + str(result) + ',' + str(coinQuantity),))

        print('--------------')
        print(result)

    except Exception as e:
        _thread.start_new_thread(FUNCTION_CLIENT.send_lark_msg_limit_one_min, ('longsM:' + str(e),))

    return result


TAKE_OPEN_OBJ = {

}
