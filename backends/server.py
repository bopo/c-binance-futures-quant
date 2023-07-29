import datetime
import decimal
import json
import math
import random
import string
import time
import traceback

import fastapi
import requests
from bottle import request
from bottle import response
from fastapi import Form

from backends.kernel.impl.tradeServer import pool
from .kernel.base.printobject import *
from .kernel.model.constant import *
from .kernel.requestclient import RequestClient
from .webServer import takeShortsOrder, takeLongsOrder, updateTradeServerStatusData, updateBinanceData, updateTurnPrice, getLossLimitTimeData, takeQuotVolume, updateDayIncome, \
    getKline, cancelBinanceOrder, updateAPIObj, getFutureNowPriceByDepth, takeElemTime, getFutureDepthBySymbol, getPolePrice, getBinanceAccountInfo, getStopProfitPriceByTime

app = fastapi.FastAPI(title="paste")


@app.post('/check_maker_server_in_data')
def check_maker_server_in_data():
    name = str(request.forms.get('name'))
    privateIP = str(request.forms.get('privateIP'))
    symbol = str(request.forms.get('symbol'))
    mySymbol = str(request.forms.get('mySymbol'))

    sql = 'select `status` from trade_server_status where privateIP =%s '
    data = FUNCTION_CLIENT.mysql_pool_select(sql, [privateIP])

    if len(data) == 0:
        extraPara = {'customizeDangerous': 0}
        sql = 'INSERT INTO trade_server_status ( privateIP,`name`,`extraPara`,symbol,mySymbol)  VALUES ( %s, %s, %s, %s, %s);'
        FUNCTION_CLIENT.mysql_pool_commit(sql, [privateIP, name, json.dumps(extraPara), symbol, mySymbol])

    return {'s': 'ok'}


@app.post('/update_maker_server_run_info')
def update_maker_server_run_info():
    global TRADE_SERVER_STATUS_DATA
    privateIP = str(request.forms.get('privateIP'))
    dangerousClass = str(request.forms.get('dangerousClass'))
    dangerousName = str(request.forms.get('dangerousName'))
    direction = str(request.forms.get('direction'))
    longsOnceTradeValue = float(request.forms.get('longsOnceTradeValue'))
    shortsOnceTradeValue = float(request.forms.get('shortsOnceTradeValue'))
    longsBollTimeAmount = float(request.forms.get('longsBollTimeAmount'))
    shortsBollTimeAmount = float(request.forms.get('shortsBollTimeAmount'))
    positionValue = float(request.forms.get('positionValue'))

    runInfo = {
        'dangerousClass': dangerousClass,
        'dangerousName': dangerousName,
        'longsOnceTradeValue': longsOnceTradeValue,
        'shortsOnceTradeValue': shortsOnceTradeValue,
        'longsBollTimeAmount': longsBollTimeAmount,
        'shortsBollTimeAmount': shortsBollTimeAmount,
        'positionValue': positionValue,
        'direction': direction
    }
    now = int(time.time())
    symbol = str(request.forms.get('symbol'))
    sql = 'update trade_server_status set runInfo=%s,updateTs=%s,updateTime=%s where privateIP=%s'
    FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(runInfo), now, FUNCTION_CLIENT.turn_ts_to_time(now), privateIP])
    updateTradeServerStatusData()
    customizeDangerousData = {'customizeDangerous': 0}
    print(privateIP)
    for a in range(len(TRADE_SERVER_STATUS_DATA)):
        if TRADE_SERVER_STATUS_DATA[a]['privateIP'] == privateIP:
            customizeDangerousData = TRADE_SERVER_STATUS_DATA[a]['customizeDangerousData']
            break

    resp = json.dumps({'s': 'ok', 'customizeDangerous': customizeDangerousData['customizeDangerous']})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_customize_dangerous')
def get_customize_dangerous():
    global CUSTOMIZE_DANGEROUS_DATA_ARR, CUSTOMIZE_DANGEROUS_DATA_ARR_UPDATE_TS, TRADE_SERVER_STATUS_DATA
    SYMBOL_ARR = ['ETHUSDT', 'BTCUSDT']
    now = int(time.time())
    updateTradeServerStatusData()
    if now - CUSTOMIZE_DANGEROUS_DATA_ARR_UPDATE_TS > 5:
        CUSTOMIZE_DANGEROUS_DATA_ARR_UPDATE_TS = now
        customizeDangerousDataArr = []
        for a in range(len(SYMBOL_ARR)):
            for b in range(len(TRADE_SERVER_STATUS_DATA)):
                if TRADE_SERVER_STATUS_DATA[b]['symbol'] == SYMBOL_ARR[a]:
                    customizeDangerousData = TRADE_SERVER_STATUS_DATA[b]['customizeDangerousData']
                    runInfo = TRADE_SERVER_STATUS_DATA[b]['runInfo']
                    customizeDangerousDataArr.append({
                        'customizeDangerous': customizeDangerousData['customizeDangerous'], 'dangerousName': runInfo['dangerousName'], 'dangerousClass': runInfo['dangerousClass'],
                        'symbol': TRADE_SERVER_STATUS_DATA[b]['symbol']
                    })
        CUSTOMIZE_DANGEROUS_DATA_ARR = customizeDangerousDataArr
    resp = json.dumps({'s': 'ok', 'customizeDangerousDataArr': CUSTOMIZE_DANGEROUS_DATA_ARR})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/update_customize_dangerous')
def update_customize_dangerous():
    customizeDangerous = int(request.forms.get('customizeDangerous'))
    symbol = str(request.forms.get('symbol'))

    if symbol == 'all':
        extraInfo = {
            'customizeDangerous': customizeDangerous
        }
        sql = 'update trade_server_status set extraPara=%s'
        FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(extraInfo)])
    else:
        extraInfo = {
            'customizeDangerous': customizeDangerous
        }
        sql = 'update trade_server_status set extraPara=%s where symbol=%s'
        FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(extraInfo), symbol])
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


ALL_OPEN_ORDERS_ARR = []


@app.post('/get_all_open_orders_b')
def get_all_open_orders_b():
    global NEW_API_OBJ
    symbol = str(request.forms.get('symbol'))
    now = int(time.time() * 1000)
    result = {}
    request_client = RequestClient(api_key=NEW_API_OBJ[symbol]['apiKey'], secret_key=NEW_API_OBJ[symbol]['apiSecret'])
    result = request_client.get_all_open_orders()
    result = json.loads(result)
    resp = json.dumps({'s': 'ok', 'r': result, 't': int(time.time())})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_position')
def get_position():
    global NEW_API_OBJ
    symbol = str(request.forms.get('symbol'))
    positionsArr = []
    now = int(time.time() * 1000)
    result = {}
    request_client = RequestClient(api_key=NEW_API_OBJ[symbol]['apiKey'], secret_key=NEW_API_OBJ[symbol]['apiSecret'])
    result = request_client.get_account_information()
    result = json.loads(result)
    for i in range(len(result['positions'])):
        if float(result['positions'][i]['positionAmt']) != 0:
            positionsArr.append(result['positions'][i])

    resp = json.dumps({'s': 'ok', 'r': positionsArr, 't': int(time.time())})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_watch_info')
def get_watch_info():
    global WATCH_INFO_OBJ, WATCH_INFO_UPDATE_TS, BTC_TURN_TS, ETH_TURN_TS, ETH_TURN_PRICE_UPDATE_TS, BTC_TURN_PRICE_UPDATE_TS, NEW_API_OBJ, TRADE_SERVER_STATUS_DATA, LOSS_LIMIT_TIME_DATA_ARR, TICK_ARR, ETH_1M_KLINE_ARR, BTC_1M_KLINE_ARR, ETH_TODAY_BEGIN_PRICE, BTC_TODAY_BEGIN_PRICE, BTC_TURN_PRICE, ETH_TURN_PRICE
    now = int(time.time())
    if now - WATCH_INFO_UPDATE_TS >= 60:
        WATCH_INFO_UPDATE_TS = now
        updateBinanceData()
        allPositionArr = []
        updateTradeServerStatusData()
        updateTurnPrice()
        for key in NEW_API_OBJ:
            dayBeginBalaneUpdateTime = FUNCTION_CLIENT.turn_ts_to_day_time(now)
            positionTableName = NEW_API_OBJ[key]['positionTableName']
            if dayBeginBalaneUpdateTime != NEW_API_OBJ[key]['dayBeginBalaneUpdateTime']:
                sql = 'select `balance` from ' + positionTableName + ' where ts>=%s order by id asc limit 1'
                zeroPoint = FUNCTION_CLIENT.turn_ts_to_time(dayBeginBalaneUpdateTime)
                positionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [zeroPoint])
                if len(positionRecordData) > 0:
                    NEW_API_OBJ[key]['dayBeginBalane'] = positionRecordData[0][0]
                    NEW_API_OBJ[key]['dayBeginBalaneUpdateTime'] = dayBeginBalaneUpdateTime

            thisIP = NEW_API_OBJ[key]['positionIP']
            thisKey = NEW_API_OBJ[key]['apiKey']
            mySymbol = NEW_API_OBJ[key]['mySymbol']
            dayBeginBalane = NEW_API_OBJ[key]['dayBeginBalane']
            symbol = NEW_API_OBJ[key]['symbol']

            getLossLimitTimeData(False)
            thisLossLimitTime = ''
            for i in range(len(LOSS_LIMIT_TIME_DATA_ARR)):
                if LOSS_LIMIT_TIME_DATA_ARR[i]['symbol'] == symbol:
                    thisLossLimitTime = LOSS_LIMIT_TIME_DATA_ARR[i]['limitTime']
                    break
            if thisLossLimitTime == '':
                sql = 'INSERT INTO loss_limit_time ( symbol,`limitTime`)  VALUES ( %s, %s);'
                FUNCTION_CLIENT.mysql_pool_commit(sql, [symbol, '2023-03-28 01:00:00'])
                getLossLimitTimeData(True)

            url = 'http://' + thisIP + '/' + thisKey[0:10] + '.json'
            print(thisIP)
            result = requests.request('GET', url, timeout=(0.25, 0.25)).json()
            accountBalanceValue = result['balance']

            for a in range(len(result['positionArr'])):
                thisPrice = 0
                for b in range(len(TICK_ARR)):
                    if TICK_ARR[b]['symbol'] == result['positionArr'][a]['symbol']:
                        thisPrice = float(TICK_ARR[b]['price'])
                result['positionArr'][a]['balance'] = accountBalanceValue
                result['positionArr'][a]['mySymbol'] = mySymbol
                if mySymbol == 'OTHER':
                    result['positionArr'][a]['mySymbol'] = result['positionArr'][a]['symbol'] + '_BINANCE'
                result['positionArr'][a]['price'] = thisPrice
                result['positionArr'][a]['dayBeginBalane'] = dayBeginBalane
                result['positionArr'][a]['updateTime'] = int(time.time() * 1000)
                result['positionArr'][a]['tradeType'] = str(result['positionArr'][a]['entryPrice'])[-1]
                result['positionArr'][a]['entryPrice'] = 0
                result['positionArr'][a]['unrealizedProfit'] = 0
                result['positionArr'][a]['profitPercent'] = 0
                allPositionArr.append(result['positionArr'][a])

        WATCH_INFO_OBJ = {'s': 'ok', 'balance': accountBalanceValue, 'ethP': ETH_TURN_PRICE, 'btcP': BTC_TURN_PRICE, 'ethT': ETH_TURN_TS, 'btcT': BTC_TURN_TS,
                          'eth': ETH_1M_KLINE_ARR, 'btc': BTC_1M_KLINE_ARR, 'e': LOSS_LIMIT_TIME_DATA_ARR, 'd': TRADE_SERVER_STATUS_DATA, 'a': allPositionArr,
                          't': int(time.time())}

    resp = json.dumps(WATCH_INFO_OBJ)
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


# @post('/get_loss_limit_time')
# def get_loss_limit_time():


@app.post('/update_loss_limit_time')
def update_loss_limit_time():
    symbol = str(request.forms.get('symbol'))
    nowTime = FUNCTION_CLIENT.turn_ts_to_time(int(time.time()))
    sql = 'update loss_limit_time set `limitTime`=%s where symbol=%s'
    FUNCTION_CLIENT.mysql_pool_commit(sql, [nowTime, symbol])
    getLossLimitTimeData(True)
    resp = json.dumps({'s': 'ok', 't': int(time.time())})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_second_open_position')
def get_second_open_position():
    BINANCE_API_KEY = 'bJpPkJe9kW8USXKDQuP2WKeSVaEIOM5wKT7Uta1ir2wmlAxNHN9hwrZDhjJCYcEd'
    thisIP = '172.24.207.4'
    url = 'http://' + thisIP + '/' + BINANCE_API_KEY[0:10] + '.json'
    result = requests.request('GET', url, timeout=(0.5, 0.5)).json()
    resp = json.dumps({'s': 'ok', 't': int(time.time()), 'r': result})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_invest_percent')
def get_invest_percent():
    investPercentObjArr = [

        {'name': '吴钊庆', 'time': '2023-05-19 14:59:00', 'percent': 12.206461839330702, 'initValue': 2800, 'assetsWhileJoin': 20138.67, 'investType': 'longs'},
        {'name': '一零二四', 'time': '2023-05-19 13:36:00', 'percent': 21.81179905448812, 'initValue': 5000, 'assetsWhileJoin': 15125.24, 'investType': 'longs'},
        {'name': '李', 'time': '2023-05-16 21:52:00', 'percent': 8.808005636839024, 'initValue': 2000, 'assetsWhileJoin': 12982.22, 'investType': 'longs'},
        {'name': 'michael', 'time': '2023-05-12 20:28:00', 'percent': 52.16531441742779, 'initValue': 10000, 'assetsWhileJoin': 959, 'investType': 'longs'},
        {'name': 'ming', 'time': '2023-05-09 00:00:00', 'percent': 5.008419051914373, 'initValue': 750, 'assetsWhileJoin': 0, 'investType': 'longs'}]

    for i in range(len(investPercentObjArr)):
        investPercentObjArr[i]['percent'] = int(investPercentObjArr[i]['percent'] * 10000) / 10000

    resp = json.dumps({'s': 'ok', 't': int(time.time()), 'r': investPercentObjArr})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/update_machine_status')
def update_machine_status():
    privateIP = str(request.forms.get('privateIP'))
    symbol = str(request.forms.get('symbol'))
    updateTs = int(time.time())

    sql = 'select `id` from machine_status where private_ip=%s'
    machineData = FUNCTION_CLIENT.mysql_pool_select(sql, [privateIP])

    if len(machineData) == 0:
        sql = 'INSERT INTO machine_status ( `private_ip`,`insert_ts`,`update_ts`,`symbol`)  VALUES ( %s, %s, %s, %s);'
        FUNCTION_CLIENT.mysql_pool_commit(sql, [privateIP, updateTs, updateTs, symbol])
    else:
        sql = 'update machine_status set update_ts=%s where private_ip=%s'
        print(privateIP)
        FUNCTION_CLIENT.mysql_pool_commit(sql, [updateTs, privateIP])

    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_one_day_rate')
def get_one_day_rate():
    global UPDATE_ONE_DAY_RATE_TS, SYMBOL_DATA_OBJ
    now = int(time.time() * 1000)
    if now - UPDATE_ONE_DAY_RATE_TS >= 30 * 1000:
        binanceResponse = []
        try:
            url = 'https://fapi.binance.com/fapi/v1/ticker/24hr'
            binanceResponse = requests.request('GET', url, timeout=(3, 3)).json()
            binanceResponse.sort(key=takeQuotVolume, reverse=True)
        except Exception as e:
            print(e)
        if len(binanceResponse) >= 100:
            SYMBOL_DATA_OBJ = {}
            for i in range(len(binanceResponse)):
                volIndex = 1
                if i <= 15:
                    volIndex = 1.5
                elif i <= 30:
                    volIndex = 1.4
                elif i <= 45:
                    volIndex = 1.3
                elif i <= 60:
                    volIndex = 1.2
                elif i <= 75:
                    volIndex = 1.1
                SYMBOL_DATA_OBJ[binanceResponse[i]['symbol']] = {
                    'oneDayWave': int(
                        FUNCTION_CLIENT.get_percent_num(float(binanceResponse[i]['highPrice']) - float(binanceResponse[i]['lowPrice']), float(binanceResponse[i]['lowPrice']))),
                    'volRank': i,
                    'volIndex': volIndex,
                    'vol': float(binanceResponse[i]['quoteVolume']),
                    'highPrice': float(binanceResponse[i]['highPrice']),
                    'lowPrice': float(binanceResponse[i]['lowPrice'])
                }
        UPDATE_ONE_DAY_RATE_TS = now

    resp = json.dumps({'s': 'ok', 'd': SYMBOL_DATA_OBJ})
    response.set_header('Access-Control-Allow-Origin', '*')

    return resp


SYMBOL_CANCEL_ORDERS_TS_OBJ = {}


@app.post('/cancel_binance_orders')
def cancel_binance_orders():
    global SYMBOL_CANCEL_ORDERS_TS_OBJ
    key = str(request.forms.get('key'))
    secret = str(request.forms.get('secret'))
    symbol = str(request.forms.get('symbol'))

    now = int(time.time() * 1000)
    needCancel = True

    if symbol in SYMBOL_CANCEL_ORDERS_TS_OBJ:
        if now - SYMBOL_CANCEL_ORDERS_TS_OBJ[symbol] <= 3000:
            needCancel = False

    if needCancel:
        try:
            request_client = RequestClient(api_key=key, secret_key=secret)
            result = request_client.cancel_all_orders(symbol=symbol)
        except Exception as e:
            print(e)

        try:
            request_client = RequestClient(api_key=key, secret_key=secret)
            result = request_client.cancel_all_orders(symbol=symbol)
        except Exception as e:
            print(e)

        try:
            request_client = RequestClient(api_key=key, secret_key=secret)
            result = request_client.cancel_all_orders(symbol=symbol)
        except Exception as e:
            print(e)

        SYMBOL_CANCEL_ORDERS_TS_OBJ[symbol] = now

    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/begin_trade_record')
def begin_trade_record():
    global FUNCTION_CLIENT, SYMBOL_LAST_INSEART_TS_OBJ
    try:
        ts = int(time.time() * 1000)
        tradeTime = FUNCTION_CLIENT.turn_ts_to_time(ts)
        volMultiple = float(request.forms.get('volMultiple'))
        standardRate = float(request.forms.get('standardRate'))
        symbol = str(request.forms.get('symbol'))
        klineArr = json.dumps(json.loads(request.forms.get('klineArr')))
        nowOpenRate = float(request.forms.get('nowOpenRate'))
        machineNumber = str(request.forms.get('machineNumber'))
        direction = str(request.forms.get('direction'))
        myTradeType = str(request.forms.get('myTradeType'))
        longsConditionA = int(request.forms.get('longsConditionA'))
        shortsConditionA = int(request.forms.get('shortsConditionA'))
        shortsConditionB = int(request.forms.get('shortsConditionB'))
        btcNowOpenRate = float(request.forms.get('btcNowOpenRate'))
        ethNowOpenRate = float(request.forms.get('ethNowOpenRate'))
        clientBeginPrice = float(request.forms.get('clientBeginPrice'))
        clientEndPrice = float(request.forms.get('clientEndPrice'))
        privateIP = str(request.forms.get('privateIP'))

        sql = "select `id` from trades_take where symbol=%s and status='tradeBegin'"
        tradesData = FUNCTION_CLIENT.mysql_pool_select(sql, [symbol])
        if myTradeType.find('open') >= 0 and len(tradesData) == 0:
            if not symbol in SYMBOL_LAST_INSEART_TS_OBJ or ts - SYMBOL_LAST_INSEART_TS_OBJ[symbol] > 30000:
                SYMBOL_LAST_INSEART_TS_OBJ[symbol] = ts
                sql = 'INSERT INTO trades_take (  `status`, `version`,`volMultiple`,`standardRate`,`symbol`,`klineArr`,  `nowOpenRate`,`beginMachineNumber`,`direction`,`longsConditionA`,  `shortsConditionA`,`shortsConditionB`,`btcNowOpenRate`,`ethNowOpenRate`,`beginTs`,  `endTs`,`tradeType`,`updateTs`,`clientBeginPrice`,`clientEndPrice`)  VALUES ( %s,%s, %s, %s,%s,  %s,%s, %s, %s,%s,  %s,%s, %s, %s,%s,  %s,%s, %s, %s, %s);'
                FUNCTION_CLIENT.mysql_pool_commit(sql, ['tradeBegin', 3, volMultiple, standardRate, symbol, klineArr, nowOpenRate, machineNumber, direction, longsConditionA,
                                                        shortsConditionA, shortsConditionB, btcNowOpenRate, ethNowOpenRate, ts, ts, myTradeType, ts, clientBeginPrice,
                                                        clientEndPrice])
        else:
            FUNCTION_CLIENT.send_lark_msg_limit_one_min(myTradeType)
        #     if len(tradesData)==0:
        #         time.sleep(3)
        #         sql = "select `id` from trades where symbol=%s and status='tradeBegin'"
        #         tradesData = FUNCTION_CLIENT.mysql_pool_select(sql,[symbol])
        #     if myTradeType.find("close")<0 and len(tradesData)==0:
        #         FUNCTION_CLIENT.send_lark_msg_limit_one_min(symbol+","+myTradeType)
        #     elif len(tradesData)>0:
        #         tradesID = tradesData[0][0]
        #         updateSql = ""
        #         if myTradeType.find("add")>=0:
        #             if myTradeType.find("gtx")>=0:
        #                 updateSql = "update trades set `addGtxTime` = `addGtxTime`+1 where id=%s"
        #             else:
        #                 updateSql = "update trades set `addTime` = `addTime`+1 where id=%s"
        #         if myTradeType.find("open")>=0:
        #             if myTradeType.find("gtx")>=0:
        #                 updateSql = "update trades set `openGtxTime` = `openGtxTime`+1 where id=%s"
        #             else:
        #                 updateSql = "update trades set `openTime` = `openTime`+1 where id=%s"
        #         if myTradeType.find("close")>=0:
        #             if myTradeType.find("gtx")>=0:
        #                 updateSql = "update trades set `closeGtxTime` = `closeGtxTime`+1 where id=%s"
        #             else:
        #                 updateSql = "update trades set `closeTime` = `closeTime`+1 where id=%s"
        #         FUNCTION_CLIENT.mysql_pool_commit(updateSql,[tradesID])

        resp = json.dumps({'s': 'ok'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        ex = traceback.format_exc()
        FUNCTION_CLIENT.send_lark_msg_limit_one_min(str(ex))


@app.post('/get_order_result_arr')
def get_order_result_arr():
    now = int(time.time())
    symbol = str(request.forms.get('symbol'))
    beginTs = int(request.forms.get('beginTs'))

    endTs = int(request.forms.get('endTs'))
    sql = 'select `symbol`,`time`,`asksDepthArr`,`bidsDepthArr`,`ordersResult`,direction,nowOpenRate,machineNumber,`ts`,myTradeType,nowPrice from begin_trade_record where symbol=%s and ts>%s and ts<%s order by id desc limit 5000'

    beginTradeRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [symbol, beginTs - 60000, endTs + 60000])
    beginTradeArr = []

    for i in range(len(beginTradeRecordData)):
        beginTradeArr.append({
            'symbol': beginTradeRecordData[i][0],
            'time': beginTradeRecordData[i][1],
            'asksDepthArr': json.loads(beginTradeRecordData[i][2]),
            'bidsDepthArr': json.loads(beginTradeRecordData[i][3]),
            'ordersResult': json.loads(beginTradeRecordData[i][4]),
            'direction': beginTradeRecordData[i][5],
            'nowOpenRate': beginTradeRecordData[i][6],
            'machineNumber': beginTradeRecordData[i][7],
            'ts': beginTradeRecordData[i][8],
            'myTradeType': beginTradeRecordData[i][9],
            'nowPrice': beginTradeRecordData[i][10]
        })

    resp = json.dumps({'s': 'ok', 'd': beginTradeArr})
    response.set_header('Access-Control-Allow-Origin', '*')

    return resp


@app.post('/get_trades_result_arr')
def get_trades_result_arr():
    try:
        now = int(time.time())
        tradeTimeIntervalIndex = int(request.forms.get('tradeTimeIntervalIndex'))
        nowTs = int(time.time() * 1000)
        limitTs = 0

        if tradeTimeIntervalIndex == 0:
            limitTs = nowTs - 4 * 60 * 60 * 1000

        if tradeTimeIntervalIndex == 1:
            limitTs = nowTs - 8 * 60 * 60 * 1000

        if tradeTimeIntervalIndex == 2:
            limitTs = nowTs - 12 * 60 * 60 * 1000

        if tradeTimeIntervalIndex == 3:
            limitTs = nowTs - 24 * 60 * 60 * 1000

        if tradeTimeIntervalIndex == 4:
            limitTs = nowTs - 72 * 60 * 60 * 1000

        if limitTs < 1686960000000:
            limitTs = 1686960000000

        print(limitTs)
        sql = "select `symbol`,`beginTs`,`endTs`,`direction`,`profit`,`value`,cost,volInfo,openType,openTime,addTime,closeTime,openGtxTime,addGtxTime,closeGtxTime,nowOpenRate,standardRate,takeTime,beginBollUp,beginBollDown,takeValue from trades where status='updateProfit' and beginTs>%s and version=2 order by id desc"

        tradesRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [limitTs])
        tradesRecordArr = []

        for i in range(len(tradesRecordData)):
            tradesRecordArr.append([
                tradesRecordData[i][0],
                tradesRecordData[i][1],
                tradesRecordData[i][2],
                tradesRecordData[i][3],
                tradesRecordData[i][4],
                tradesRecordData[i][5],
                tradesRecordData[i][6],
                json.loads(tradesRecordData[i][7]),
                tradesRecordData[i][8],
                tradesRecordData[i][9],
                tradesRecordData[i][10],
                tradesRecordData[i][11],
                tradesRecordData[i][12],
                tradesRecordData[i][13],
                tradesRecordData[i][14],
                tradesRecordData[i][15],
                tradesRecordData[i][16],
                tradesRecordData[i][17],
                FUNCTION_CLIENT.get_percent_num(tradesRecordData[i][18] - tradesRecordData[i][19], tradesRecordData[i][19]),
                tradesRecordData[i][20]]

            )

        sql = "select `openType` from trades where status='updateProfitFail' and beginTs>%s and version=2"
        tradesRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [limitTs])
        failValue = 0

        resp = json.dumps({'s': 'ok', 'd': tradesRecordArr, 'fT': len(tradesRecordData), 'fV': failValue})
        response.set_header('Access-Control-Allow-Origin', '*')

        return resp
    except Exception as e:
        ex = traceback.format_exc()
        FUNCTION_CLIENT.send_lark_msg_limit_one_min(str(ex))


@app.post('/get_position_record')
def get_position_record():
    global POSITION_RECORD_TABLE_NAME_OBJ
    symbol = str(request.forms.get('symbol'))
    beginTs = int(request.forms.get('beginTs'))
    endTs = int(request.forms.get('endTs'))

    sql = 'select `positionAmt`,`price`,`positionValue`,`balance`,`time`,`profit`,`commission`,`makerCommission`,`entryPrice`,`unrealizedProfit`,`maintMargin` from ' + \
          POSITION_RECORD_TABLE_NAME_OBJ[symbol] + ' where ts>%s and ts<%s'
    positionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [beginTs, endTs])
    positionRecordObjArr = []
    for i in range(len(positionRecordData)):
        positionRecordObjArr.append({
            'positionAmt': positionRecordData[i][0],
            'price': positionRecordData[i][1],
            'positionValue': positionRecordData[i][2],
            'balance': positionRecordData[i][3],
            'time': positionRecordData[i][4],
            'profit': positionRecordData[i][5],
            'commission': positionRecordData[i][6],
            'makerCommission': positionRecordData[i][7],
            'entryPrice': positionRecordData[i][8],
            'unrealizedProfit': positionRecordData[i][9],
            'maintMargin': positionRecordData[i][10]
        })

    resp = json.dumps({'s': 'ok', 'd': positionRecordObjArr, 'symbol': symbol})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_day_income')
def get_day_income():
    global GET_DAY_INCOME_TS, DAY_INCOME_DATA, GET_DAY_INCOME_TODAY_TS, INCOME_OBJ
    accessToken = str(request.forms.get('accessToken'))
    incomeDayTableName = accessToken + '_income_day'
    now = int(time.time())
    todayTime = str(datetime.date.today()) + ' 00:00:00'
    todayTs = FUNCTION_CLIENT.turn_ts_to_time(todayTime)
    isUpdate = 0
    print('------------a--------------')
    if now - GET_DAY_INCOME_TS > 300 or GET_DAY_INCOME_TODAY_TS != todayTs:
        updateDayIncome()
        print('------------b--------------')

        isUpdate = 1
        GET_DAY_INCOME_TODAY_TS = todayTs
        GET_DAY_INCOME_TS = now
        sql = 'select `dayBeginTime`, `dayEndTime`,`binanceCommission`,`pnl`,`zjyCommission` from ' + incomeDayTableName + ' order by id asc'
        dayIncomeData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
        DAY_INCOME_DATA = []
        allNetProfit = 0
        for i in range(len(dayIncomeData)):
            if FUNCTION_CLIENT.turn_ts_to_time(dayIncomeData[i][0]) != todayTs:
                DAY_INCOME_DATA.append({'allNetProfit': 0, 'dayBeginTime': dayIncomeData[i][0], 'dayEndTime': dayIncomeData[i][1], 'binanceCommission': dayIncomeData[i][2],
                                        'netProfit': dayIncomeData[i][3] + dayIncomeData[i][2], 'profit': dayIncomeData[i][3], 'zjyCommission': dayIncomeData[i][4]})
        # if FUNCTION_CLIENT.turn_ts_to_time(dayIncomeData[len(dayIncomeData)-1][0]) !=todayTs:

        #     DAY_INCOME_DATA.append({'allNetProfit':0,'dayBeginTime':FUNCTION_CLIENT.turn_ts_to_time(todayTs),'dayEndTime':FUNCTION_CLIENT.turn_ts_to_time(todayTs+86400),'binanceCommission':INCOME_OBJ["today"]["c"],'netProfit':INCOME_OBJ["today"]["c"]+INCOME_OBJ["today"]["p"],'profit':INCOME_OBJ["today"]["p"],'zjyCommission':INCOME_OBJ["today"]["s"]})

    if FUNCTION_CLIENT.turn_ts_to_time(DAY_INCOME_DATA[len(DAY_INCOME_DATA) - 1]['dayBeginTime']) != todayTs:
        DAY_INCOME_DATA.append({'allNetProfit': 0, 'dayBeginTime': FUNCTION_CLIENT.turn_ts_to_time(todayTs), 'dayEndTime': FUNCTION_CLIENT.turn_ts_to_time(todayTs + 86400),
                                'binanceCommission': INCOME_OBJ['today']['c'], 'netProfit': INCOME_OBJ['today']['c'] + INCOME_OBJ['today']['p'], 'profit': INCOME_OBJ['today']['p'],
                                'zjyCommission': INCOME_OBJ['today']['s']})
    else:
        print(INCOME_OBJ)
        DAY_INCOME_DATA[len(DAY_INCOME_DATA) - 1] = {'allNetProfit': 0, 'dayBeginTime': FUNCTION_CLIENT.turn_ts_to_time(todayTs),
                                                     'dayEndTime': FUNCTION_CLIENT.turn_ts_to_time(todayTs + 86400), 'binanceCommission': INCOME_OBJ['today']['c'],
                                                     'netProfit': INCOME_OBJ['today']['c'] + INCOME_OBJ['today']['p'], 'profit': INCOME_OBJ['today']['p'],
                                                     'zjyCommission': INCOME_OBJ['today']['s']}

    resp = json.dumps({'s': 'ok', 'd': DAY_INCOME_DATA, 'u': isUpdate})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_history_position_record')
def get_history_position_record():
    global POSITION_RECORD_TABLE_NAME_OBJ
    tableName = str(request.forms.get('tableName'))
    beginTs = int(request.forms.get('beginTs'))
    endTs = int(request.forms.get('endTs'))

    sql = 'select `positionAmt`,`price`,`positionValue`,`balance`,`time`,`profit`,`commission`,`makerCommission` from history_position_record_' + tableName + ' where ts>%s and ts<%s'
    positionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [beginTs, endTs])
    positionRecordObjArr = []
    for i in range(len(positionRecordData)):
        positionRecordObjArr.append({
            'positionAmt': positionRecordData[i][0],
            'price': positionRecordData[i][1],
            'positionValue': positionRecordData[i][2],
            'balance': positionRecordData[i][3],
            'time': positionRecordData[i][4],
            'profit': positionRecordData[i][5],
            'commission': positionRecordData[i][6],
            'makerCommission': positionRecordData[i][7]
        })

    resp = json.dumps({'s': 'ok', 'd': positionRecordObjArr})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_one_min_select_kline')
def get_one_min_select_kline():
    global ONE_MIN_UPDATE_TS, ONE_MIN_KLINE
    now = int(time.time() * 1000)
    if now - ONE_MIN_UPDATE_TS >= 100:
        ONE_MIN_UPDATE_TS = now
        symbol = str(request.forms.get('symbol'))
        klineArr = getKline(symbol, '1m', 3)
        ONE_MIN_KLINE = klineArr
    resp = json.dumps({'s': 'ok', 'k': ONE_MIN_KLINE})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_commission_rate')
def get_commission_rate():
    key = str(request.forms.get('key'))
    now = int(time.time() * 1000)

    secret = str(request.forms.get('secret'))
    symbol = str(request.forms.get('symbol'))

    request_client = RequestClient(api_key=key, secret_key=secret)

    result = request_client.get_commission_rate(symbol=symbol)
    result = json.loads(result)

    resp = json.dumps({'s': 'ok', 'd': result})
    response.set_header('Access-Control-Allow-Origin', '*')

    return resp


@app.post('/get_big_loss_trades')
def get_big_loss_trades():
    global BIG_LOSS_TRADES_ARR, UPDATE_BIG_LOSS_TRADES_DARA_TS, AVERAGE_RUN_TIME
    now = int(time.time())
    if now - UPDATE_BIG_LOSS_TRADES_DARA_TS > 60:
        UPDATE_BIG_LOSS_TRADES_DARA_TS = now
        sql = 'select `symbol`,`endTs`,`profit`,`profitPercentByBalance` from trades_record where profitPercentByBalance<=-0.15 order by id desc'
        bigLossData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
        BIG_LOSS_TRADES_ARR = []
        for i in range(len(bigLossData)):
            BIG_LOSS_TRADES_ARR.append({
                'symbol': bigLossData[i][0],
                'time': FUNCTION_CLIENT.turn_ts_to_time(bigLossData[i][1]),
                'profit': bigLossData[i][2],
                'profitPercentByBalance': str(abs(int(bigLossData[i][3] * 100) / 100)) + '%'
            })
    resp = json.dumps({'s': 'ok', 'd': BIG_LOSS_TRADES_ARR})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/cancel_binance_order')
def cancel_binance_order():
    key = str(request.forms.get('key'))
    secret = str(request.forms.get('secret'))
    symbol = str(request.forms.get('symbol'))
    clientOrderId = str(request.forms.get('clientOrderId'))
    now = int(time.time() * 1000)
    try:
        request_client = RequestClient(api_key=key, secret_key=secret)
        result = request_client.cancel_order(symbol=symbol, orderId=clientOrderId)
    except Exception as e:
        print(e)
        try:
            request_client = RequestClient(api_key=key, secret_key=secret)
            result = request_client.cancel_order(symbol=symbol, orderId=clientOrderId)
        except Exception as e:
            print(e)
            try:
                request_client = RequestClient(api_key=key, secret_key=secret)
                result = request_client.cancel_order(symbol=symbol, orderId=clientOrderId)
            except Exception as e:
                FUNCTION_CLIENT.send_lark_msg_limit_one_min('【cancel order error】，' + key + ',' + symbol + ',' + clientOrderId + ',' + str(e))

    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_trade_status')
def get_trade_status():
    global TRADE_MACHINE_STATUS_DATA, UPDATE_TRADE_MACHINE_STATUS_DATA_TS, AVERAGE_RUN_TIME
    now = int(time.time())
    if now - UPDATE_TRADE_MACHINE_STATUS_DATA_TS > 60:
        UPDATE_TRADE_MACHINE_STATUS_DATA_TS = now
        sql = 'select `status`,`update_ts`,`run_time` from trade_machine_status order by update_ts asc'
        TRADE_MACHINE_STATUS_DATA = FUNCTION_CLIENT.mysql_pool_select(sql, [])
        allRunTime = 0
        for i in range(len(TRADE_MACHINE_STATUS_DATA)):
            allRunTime = allRunTime + TRADE_MACHINE_STATUS_DATA[i][2]
        AVERAGE_RUN_TIME = int(allRunTime / len(TRADE_MACHINE_STATUS_DATA))
    resp = json.dumps({'s': 'ok', 'updateTs': TRADE_MACHINE_STATUS_DATA[0][1], 'status': TRADE_MACHINE_STATUS_DATA[0][0], 'runTime': AVERAGE_RUN_TIME})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/update_trade_status')
def update_trade_status():
    privateIP = str(request.forms.get('privateIP'))
    status = str(request.forms.get('status'))
    runTime = str(request.forms.get('runTime'))
    updateTs = int(time.time())

    sql = 'select `id` from trade_machine_status where private_ip=%s'
    machineData = FUNCTION_CLIENT.mysql_pool_select(sql, [privateIP])

    if len(machineData) == 0:
        sql = 'INSERT INTO trade_machine_status ( `private_ip`,`insert_ts`,`update_ts`,`status`)  VALUES ( %s, %s, %s, %s);'
        FUNCTION_CLIENT.mysql_pool_commit(sql, [privateIP, updateTs, updateTs, status])
    else:
        sql = 'update trade_machine_status set status=%s,update_ts=%s,run_time=%s where private_ip=%s'
        print(privateIP)
        FUNCTION_CLIENT.mysql_pool_commit(sql, [status, updateTs, runTime, privateIP])

    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_trade_record')
def get_trade_record():
    global NEW_API_OBJ
    symbol = str(request.forms.get('symbol'))
    now = int(time.time() * 1000)
    result = {}
    request_client = RequestClient(api_key=NEW_API_OBJ[symbol]['apiKey'], secret_key=NEW_API_OBJ[symbol]['apiSecret'])
    result = request_client.get_account_trades(symbol)
    result = json.loads(result)
    resp = json.dumps({'s': 'ok', 'r': result, 't': int(time.time())})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_all_acount_info')
def get_all_acount_info():
    global POSITION_RECORD_TABLE_NAME_OBJ
    allBalance = 0
    allPosition = 0
    for key in POSITION_RECORD_TABLE_NAME_OBJ:
        sql = 'select `positionValue`,`balance` from ' + POSITION_RECORD_TABLE_NAME_OBJ[key] + ' order by id desc limit 1'
        positionRecordData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
        allPosition = allPosition + positionRecordData[0][0]
        allBalance = allBalance + positionRecordData[0][1]
    resp = json.dumps({'s': 'ok', 'b': allBalance, 'p': allPosition, 't': int(time.time())})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_income_obj')
def getIncomeObj():
    global INCOME_OBJ, LAST_UPDATE_INCOME_TS, INCOME_LOCK, SYMBOL_INCOME_OBJ
    accessToken = str(request.forms.get('accessToken'))
    now = int(time.time())
    if now - LAST_UPDATE_INCOME_TS >= 9:
        if now - LAST_UPDATE_INCOME_TS >= 60 or (not INCOME_LOCK):
            LAST_UPDATE_INCOME_TS = now
            INCOME_LOCK = True

            todayTime = str(datetime.date.today()) + ' 00:00:00'
            todayeTs = FUNCTION_CLIENT.turn_ts_to_time(todayTime)

            todayeLimitTs = todayeTs * 1000
            fifteenMinsLimitTs = int(time.time() * 1000) - 900000
            thirtyMinsLimitTs = int(time.time() * 1000) - 1800000
            oneHourLimitTs = int(time.time() * 1000) - 3600000
            fourHoursLimitTs = int(time.time() * 1000) - 14400000
            oneDayLimitTs = int(time.time() * 1000) - 86400000
            tableName = accessToken + '_income'
            limitTs = int(time.time() * 1000) - 86400000
            sql = 'select `binance_ts`,`incomeType`,`income`,`asset`,`bnbPrice`,`commission`,`symbol` from ' + tableName + ' where binance_ts>%s order by id desc'
            data = FUNCTION_CLIENT.mysql_pool_select(sql, [limitTs])
            print('len(data):' + str(len(data)))
            if len(data) > 0:
                INCOME_OBJ = {
                    '15m': {'c': 0, 'p': 0, 's': 0},
                    '30m': {'c': 0, 'p': 0, 's': 0},
                    '1h': {'c': 0, 'p': 0, 's': 0},
                    '4h': {'c': 0, 'p': 0, 's': 0},
                    'oneDay': {'c': 0, 'p': 0, 's': 0},
                    'today': {'c': 0, 'p': 0, 's': 0}
                }

            symbolIncomeObj = {}
            for i in range(len(data)):
                symbol = data[i][6]
                binanceTs = data[i][0]
                value = data[i][2]
                commission = data[i][5]
                if not (symbol in symbolIncomeObj):
                    symbolIncomeObj[symbol] = {
                        '15m': {'p': 0, 'c': 0},
                        '30m': {'p': 0, 'c': 0},
                        '1h': {'p': 0, 'c': 0},
                        '4h': {'p': 0, 'c': 0},
                        'oneDay': {'p': 0, 'c': 0},
                        'today': {'p': 0, 'c': 0}
                    }

                if data[i][3] == 'BNB':
                    value = data[i][2] * data[i][4]

                if data[i][1] == 'COMMISSION':
                    if binanceTs >= fifteenMinsLimitTs:
                        INCOME_OBJ['15m']['c'] = INCOME_OBJ['15m']['c'] + value
                        INCOME_OBJ['15m']['s'] = INCOME_OBJ['15m']['s'] + commission
                        symbolIncomeObj[symbol]['15m']['c'] = symbolIncomeObj[symbol]['15m']['c'] + value
                    if binanceTs >= thirtyMinsLimitTs:
                        INCOME_OBJ['30m']['c'] = INCOME_OBJ['30m']['c'] + value
                        INCOME_OBJ['30m']['s'] = INCOME_OBJ['30m']['s'] + commission
                        symbolIncomeObj[symbol]['30m']['c'] = symbolIncomeObj[symbol]['30m']['c'] + value
                    if binanceTs >= oneHourLimitTs:
                        INCOME_OBJ['1h']['c'] = INCOME_OBJ['1h']['c'] + value
                        INCOME_OBJ['1h']['s'] = INCOME_OBJ['1h']['s'] + commission
                        symbolIncomeObj[symbol]['1h']['c'] = symbolIncomeObj[symbol]['1h']['c'] + value
                    if binanceTs >= fourHoursLimitTs:
                        INCOME_OBJ['4h']['c'] = INCOME_OBJ['4h']['c'] + value
                        INCOME_OBJ['4h']['s'] = INCOME_OBJ['4h']['s'] + commission
                        symbolIncomeObj[symbol]['4h']['c'] = symbolIncomeObj[symbol]['4h']['c'] + value
                    if binanceTs >= oneDayLimitTs:
                        INCOME_OBJ['oneDay']['c'] = INCOME_OBJ['oneDay']['c'] + value
                        INCOME_OBJ['oneDay']['s'] = INCOME_OBJ['oneDay']['s'] + commission
                        symbolIncomeObj[symbol]['oneDay']['c'] = symbolIncomeObj[symbol]['oneDay']['c'] + value
                    if binanceTs >= todayeLimitTs:
                        INCOME_OBJ['today']['c'] = INCOME_OBJ['today']['c'] + value
                        INCOME_OBJ['today']['s'] = INCOME_OBJ['today']['s'] + commission
                        symbolIncomeObj[symbol]['today']['c'] = symbolIncomeObj[symbol]['today']['c'] + value
                if data[i][1] == 'REALIZED_PNL':
                    if binanceTs >= fifteenMinsLimitTs:
                        INCOME_OBJ['15m']['p'] = INCOME_OBJ['15m']['p'] + value
                        symbolIncomeObj[symbol]['15m']['p'] = symbolIncomeObj[symbol]['15m']['p'] + value
                    if binanceTs >= thirtyMinsLimitTs:
                        INCOME_OBJ['30m']['p'] = INCOME_OBJ['30m']['p'] + value
                        symbolIncomeObj[symbol]['30m']['p'] = symbolIncomeObj[symbol]['30m']['p'] + value
                    if binanceTs >= oneHourLimitTs:
                        INCOME_OBJ['1h']['p'] = INCOME_OBJ['1h']['p'] + value
                        symbolIncomeObj[symbol]['1h']['p'] = symbolIncomeObj[symbol]['1h']['p'] + value
                    if binanceTs >= fourHoursLimitTs:
                        INCOME_OBJ['4h']['p'] = INCOME_OBJ['4h']['p'] + value
                        symbolIncomeObj[symbol]['4h']['p'] = symbolIncomeObj[symbol]['4h']['p'] + value
                    if binanceTs >= oneDayLimitTs:
                        INCOME_OBJ['oneDay']['p'] = INCOME_OBJ['oneDay']['p'] + value
                        symbolIncomeObj[symbol]['oneDay']['p'] = symbolIncomeObj[symbol]['oneDay']['p'] + value
                    if binanceTs >= todayeLimitTs:
                        INCOME_OBJ['today']['p'] = INCOME_OBJ['today']['p'] + value
                        symbolIncomeObj[symbol]['today']['p'] = symbolIncomeObj[symbol]['today']['p'] + value
            SYMBOL_INCOME_OBJ = symbolIncomeObj

            INCOME_LOCK = False
    resp = json.dumps({'s': 'ok', 'i': INCOME_OBJ, 'n': int(time.time()), 'd': SYMBOL_INCOME_OBJ})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/cancel_orders')
def cancel_orders():
    global API_OBJ
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    cancelBinanceOrder(symbol, apiKey)
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/cancel_order')
def cancel_order():
    global API_OBJ
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    clientOrderId = str(request.forms.get('clientOrderId'))
    request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
    result = request_client.cancel_order(symbol=symbol, orderId=clientOrderId)
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


ALL_OPEN_ORDERS_ARR_UPDATE_TS = 0
ALL_OPEN_ORDERS_ARR = []


@app.post('/get_all_open_orders')
def get_all_open_orders():
    global API_OBJ, ALL_OPEN_ORDERS_ARR, ALL_OPEN_ORDERS_ARR_UPDATE_TS
    key = str(request.forms.get('key'))
    secret = str(request.forms.get('secret'))
    request_client = RequestClient(api_key=key, secret_key=secret)
    result = request_client.get_all_open_orders()
    result = json.loads(result)
    resp = json.dumps({'s': 'ok', 'r': result, 't': int(time.time())})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


def getStopLossPriceByTime(symbol, stopLossPara, positionDirection):
    stopLossPrice = 0
    stopLossTime = int(stopLossPara)
    highPrice = 0
    lowPrice = 99999999
    if stopLossTime < 500:
        klineArr = getKline(symbol, '1m', stopLossTime)
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif stopLossTime < 7500:
        klineArr = getKline(symbol, '15m', int(stopLossTime / 15))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif stopLossTime < 30000:
        klineArr = getKline(symbol, '1h', int(stopLossTime / 60))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif stopLossTime < 120000:
        klineArr = getKline(symbol, '4h', int(stopLossTime / 240))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])
    elif stopLossTime < 720000:
        klineArr = getKline(symbol, '1d', int(stopLossTime / 1440))
        for i in range(len(klineArr)):
            if float(klineArr[i][2]) > highPrice:
                highPrice = float(klineArr[i][2])
            if float(klineArr[i][3]) < lowPrice:
                lowPrice = float(klineArr[i][3])

    if positionDirection == 'longs':
        stopLossPrice = lowPrice
    if positionDirection == 'shorts':
        stopLossPrice = highPrice

    return stopLossPrice


@app.post('/new_chat')
def new_chat():
    global CHAT_OBJ
    nowTs = int(time.time())
    nowTime = FUNCTION_CLIENT.turn_ts_to_time(nowTs)
    accessToken = str(request.forms.get('accessToken'))
    if accessToken in CHAT_OBJ:
        lastSendTs = CHAT_OBJ[accessToken]
        if nowTs - lastSendTs < 3:
            resp = json.dumps({'s': 'tooMuch'})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp

    CHAT_OBJ[accessToken] = nowTs
    name = str(request.forms.get('name'))
    content = str(request.forms.get('content'))

    insertSQLStr = "('" + str(accessToken) + "','" + str(name) + "','" + str(nowTime) + "','" + str(nowTs) + "','" + content + "')"
    sql = 'INSERT INTO chat (`accessToken`, `name`,`time`,`ts`,`content`)  VALUES ' + insertSQLStr + ';'
    FUNCTION_CLIENT.mysql_pool_commit(sql, [])
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/new_chat')
def new_chat():
    global CHAT_OBJ, CHAT_ARR
    nowTs = int(time.time())
    nowTime = FUNCTION_CLIENT.turn_ts_to_time(nowTs)
    accessToken = str(request.forms.get('accessToken'))
    chatType = str(request.forms.get('chatType'))
    if accessToken != 'lcsLknBbP29W8itfmXVzvFTNQ64Zjh':
        if accessToken in CHAT_OBJ:
            lastSendTs = CHAT_OBJ[accessToken]
            if nowTs - lastSendTs < 3:
                resp = json.dumps({'s': 'tooMuch'})
                response.set_header('Access-Control-Allow-Origin', '*')
                return resp

    CHAT_OBJ[accessToken] = nowTs
    name = str(request.forms.get('name'))
    content = str(request.forms.get('content'))
    CHAT_ARR.append({
        'n': name,
        't': nowTime,
        'c': content,
        'a': chatType,
        'i': CHAT_ARR[len(CHAT_ARR) - 1]['i'] + 1
    })
    if len(CHAT_ARR) > 100:
        CHAT_ARR = CHAT_ARR[-100:]
    insertSQLStr = "('" + str(accessToken) + "','" + str(name) + "','" + str(nowTime) + "','" + str(nowTs) + "','" + content + "','" + chatType + "')"
    sql = 'INSERT INTO chat (`accessToken`, `name`,`time`,`ts`,`content`,`chatType`)  VALUES ' + insertSQLStr + ';'
    FUNCTION_CLIENT.mysql_pool_commit(sql, [])
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_chat')
def get_chat():
    global CHAT_ARR
    chatArrIndex = str(request.forms.get('chatArrIndex'))
    sendArr = []
    if str(chatArrIndex) != str(CHAT_ARR[len(CHAT_ARR) - 1]['i']):
        sendArr = CHAT_ARR
    resp = json.dumps({'s': 'ok', 'c': sendArr})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/new_system')
def new_system(
    accessToken: str = Form('...'),
    chatType: str = Form('...')
):
    global SYSTEM_ARR
    nowTs = int(time.time())
    nowTime = FUNCTION_CLIENT.turn_ts_to_time(nowTs)

    if accessToken != 'lcsLknBbP29W8itfmXVzvFTNQ64Zjh':
        return {'s': 'tooMuch'}

    name = str(request.forms.get('name'))
    content = str(request.forms.get('content'))
    SYSTEM_ARR.append({
        'n': name,
        't': nowTime,
        'c': content,
        'a': chatType,
        'i': SYSTEM_ARR[len(SYSTEM_ARR) - 1]['i'] + 1
    })

    if len(SYSTEM_ARR) > 100:
        SYSTEM_ARR = SYSTEM_ARR[-100:]

    insertSQLStr = "('" + str(accessToken) + "','" + str(name) + "','" + str(nowTime) + "','" + str(nowTs) + "','" + content + "','" + chatType + "')"
    sql = 'INSERT INTO chat (`accessToken`, `name`,`time`,`ts`,`content`,`chatType`)  VALUES ' + insertSQLStr + ';'
    FUNCTION_CLIENT.mysql_pool_commit(sql, [])

    return {'s': 'ok'}


@app.post('/get_chat_and_system')
def get_chat_and_system(
    chat_arr_index: str = Form('...'),
    system_arr_index: str = Form('...'),
):
    global CHAT_ARR, SYSTEM_ARR

    chat_arr = []

    if str(chat_arr_index) != str(CHAT_ARR[len(CHAT_ARR) - 1]['i']):
        chat_arr = CHAT_ARR

    system_arr = []

    if str(system_arr_index) != str(SYSTEM_ARR[len(SYSTEM_ARR) - 1]['i']):
        system_arr = SYSTEM_ARR

    return {'s': 'ok', 'c': chat_arr, 'a': system_arr}


@app.post('/r')
def r():
    global API_OBJ, LAST_RECORD_TS, RECORD_LOCK
    now = int(time.time())
    if now - LAST_RECORD_TS >= 9:
        if now - LAST_RECORD_TS >= 300 or (not RECORD_LOCK):
            RECORD_LOCK = True
            LAST_RECORD_TS = now
            apiKey = str(request.forms.get('apiKey'))
            accessToken = str(request.forms.get('accessToken'))
            updateAPIObj(apiKey)
            tableName = accessToken + '_income'
            sql = 'select `binance_ts`,`incomeType`,`income`,`asset`,`trade_id` from ' + tableName + ' where apiKey=%s order by id desc limit 100'
            lastBinanceTsData = ()

            con = pool.get_connection()
            c = con.cursor()
            try:
                c.execute(sql, [apiKey])
                lastBinanceTsData = c.fetchall()
                normal = True
            except Exception as e:
                print(e)
                print(e)
                tableExit = False
                sql = 'show tables;'
                tableData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
                for a in range(len(tableData)):
                    if tableData[a][0] == tableName:
                        tableExit = True

                if not tableExit:
                    sql = """CREATE TABLE `""" + tableName + """`  (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `incomeType` varchar(255) NULL,
                      `income` double(30,10) NULL,
                      `bnbPrice` double(30,10) NULL,
                      `asset` varchar(255) NULL,
                      `trade_id` varchar(255) NULL,
                      `binance_ts` bigint(18) NULL,
                      `symbol` varchar(255) NULL,
                      `apiKey` varchar(255) NULL,
                      `commission` double(30,10) NULL,
                      PRIMARY KEY (`id`) USING BTREE
                    );"""
                    FUNCTION_CLIENT.mysql_pool_commit(sql, [])
            try:
                con.close()
            except Exception as e:
                print(q)
                print(e)

            lastBinanceTs = 0
            if len(lastBinanceTsData) > 0:
                lastBinanceTs = lastBinanceTsData[0][0]

            result = []
            try:
                request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
                result = request_client.get_income_history_with_no_symbol()
                result = json.loads(result)
            except Exception as e:
                request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
                result = request_client.get_income_history_with_no_symbol()
                result = json.loads(result)

            result.sort(key=takeElemTime, reverse=False)
            bnbPrice = getFutureNowPriceByDepth('BNBUSDT')

            for i in range(len(result)):
                trade_id = str(result[i]['tradeId'])
                binance_ts = str(result[i]['time'])
                incomeType = str(result[i]['incomeType'])
                income = str(result[i]['income'])
                asset = str(result[i]['asset'])
                info = str(result[i]['info'])

                symbol = str(result[i]['symbol'])
                if incomeType == 'COMMISSION' or incomeType == 'REALIZED_PNL':
                    isExit = False
                    for b in range(len(lastBinanceTsData)):
                        if int(result[i]['time']) < lastBinanceTs or (
                            (str(int(lastBinanceTsData[b][0])) == str(int(binance_ts))) and (str(lastBinanceTsData[b][1]) == str(incomeType)) and (
                            format(float(lastBinanceTsData[b][2]), '.8f') == format(float(income), '.8f')) and (str(lastBinanceTsData[b][3]) == str(asset)) and (
                                str(lastBinanceTsData[b][4]) == str(trade_id))):
                            isExit = True
                    if not isExit:
                        commission = 0
                        if incomeType == 'COMMISSION':
                            if asset == 'BNB':
                                if float(income) < 0:
                                    commission = abs(float(income) * bnbPrice * 0.1)
                                else:
                                    commission = abs(float(income) * bnbPrice * 0.05)
                            else:
                                if float(income) < 0:
                                    commission = abs(float(income) * 0.1)
                                else:
                                    commission = abs(float(income) * 0.05)

                        insertSQLStr = "('" + str(apiKey) + "','" + str(incomeType) + "','" + str(income) + "','" + str(
                            asset) + "','" + trade_id + "','" + binance_ts + "','" + symbol + "','" + str(bnbPrice) + "','" + str(commission) + "')"
                        sql = 'INSERT INTO ' + tableName + ' (`apiKey`, `incomeType`,`income`,`asset`,`trade_id`,`binance_ts`,`symbol`,`bnbPrice`,`commission`)  VALUES ' + insertSQLStr + ';'
                        FUNCTION_CLIENT.mysql_pool_commit(sql, [])
            RECORD_LOCK = False
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_depth')
def get_depth():
    global PRICE_DECIMAL_AMOUNT_OBJ, AMOUNT_DECIMAL_AMOUNT_OBJ, DEPTH_UPDATE_TS, LAST_BINANCE_RESPONSE_OBJ
    symbol = str(request.forms.get('symbol'))
    accessToken = str(request.forms.get('accessToken'))
    now = int(time.time() * 1000)
    if now - DEPTH_UPDATE_TS > 100:
        DEPTH_UPDATE_TS = now
        url = 'https://fapi.binance.com/fapi/v1/depth?symbol=' + symbol + '&limit=50'
        binanceResponse = requests.request('GET', url, timeout=(0.5, 0.5)).json()
        LAST_BINANCE_RESPONSE_OBJ = binanceResponse

    resp = json.dumps({'s': 'ok', 'r': LAST_BINANCE_RESPONSE_OBJ, 'i': symbol, 'p': PRICE_DECIMAL_AMOUNT_OBJ[symbol], 'a': AMOUNT_DECIMAL_AMOUNT_OBJ[symbol]})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/open_position')
def open_position():
    global API_OBJ, PRICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, RECENT_ORDERS_OBJ, ORDER_ID_INDEX, MARKET_MAX_SIZE_OBJ, PRICE_TICK_OBJ
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    money = float(request.forms.get('money'))
    tradeType = str(request.forms.get('tradeType'))
    nowPrice = float(request.forms.get('nowPrice'))
    paraArr = json.loads(request.forms.get('paraArr'))

    marketMaxSize = MARKET_MAX_SIZE_OBJ[symbol]
    now = int(time.time())
    resultArr = []
    result = {}
    direction = ''
    tradeCoinQuantity = 0
    if tradeType == 'openLongsByMarket':
        direction = 'longs'
        coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / nowPrice))
        if coinQuantity > marketMaxSize:
            coinQuantity = marketMaxSize
            tradeCoinQuantity = marketMaxSize
        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = 'marketOpenLongs_s' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        try:
            result = request_client.post_market_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.BUY,
                                                      ordertype=OrderType.MARKET, positionSide='BOTH', price='0')
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        result = json.loads(result)
        resultArr.append(result)
    elif tradeType == 'openShortsByMarket':
        direction = 'shorts'
        coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / nowPrice))
        if coinQuantity > marketMaxSize:
            coinQuantity = marketMaxSize
            tradeCoinQuantity = marketMaxSize

        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = 'marketOpenShorts_s' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        try:
            result = request_client.post_market_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.SELL,
                                                      ordertype=OrderType.MARKET, positionSide='BOTH', price='0')
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        result = json.loads(result)
        resultArr.append(result)


    elif tradeType == 'openLongsByDepth' or tradeType == 'openShortsByDepth':
        depthObj = getFutureDepthBySymbol(symbol, 50)
        if not ('bids' in depthObj):
            resp = json.dumps({'s': 'dataError', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        depthType = paraArr[0]
        price = 0
        if depthType == 'mid':
            price = (float(depthObj['bids'][0][0]) + float(depthObj['bids'][0][0])) / 2
        elif depthType == 'buy':
            depthNumber = int(paraArr[1]) - 1
            price = float(depthObj['bids'][depthNumber][0])
        elif depthType == 'sell':
            depthNumber = int(paraArr[1]) - 1
            price = float(depthObj['asks'][depthNumber][0])

        priceIndex = float(paraArr[2])
        price = price * priceIndex
        price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (price)))
        coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / nowPrice))
        if coinQuantity > marketMaxSize:
            coinQuantity = marketMaxSize
            tradeCoinQuantity = marketMaxSize

        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = ''
        if tradeType == 'openLongsByDepth':
            newClientOrderId = 'depthOpenLongs_s' + str(ORDER_ID_INDEX)
        if tradeType == 'openShortsByDepth':
            newClientOrderId = 'depthOpenShorts_s' + str(ORDER_ID_INDEX)

        timeInForce = ''
        if paraArr[4] == 'GTX':
            timeInForce = TimeInForce.GTX
        if paraArr[4] == 'GTC':
            timeInForce = TimeInForce.GTC

        orderSide = ''
        if tradeType == 'openLongsByDepth':
            orderSide = OrderSide.BUY
        if tradeType == 'openShortsByDepth':
            orderSide = OrderSide.SELL
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        try:
            result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=orderSide, ordertype=OrderType.LIMIT,
                                               price=price, positionSide='BOTH', timeInForce=timeInForce)
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        result = json.loads(result)
        resultArr.append(result)

    elif tradeType == 'openLongsByLeft' or tradeType == 'openShortsByLeft':

        mins = int(paraArr[0])
        priceIndex = float(paraArr[1])
        priceArr = getPolePrice(symbol, mins)
        highPrice = priceArr[0]
        if highPrice == 0:
            resp = json.dumps({'s': 'dataError', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        lowPirce = priceArr[1]
        price = 0
        if tradeType == 'openLongsByLeft':
            price = lowPirce * priceIndex
        if tradeType == 'openShortsByLeft':
            price = highPrice * priceIndex

        coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / price))
        if coinQuantity > marketMaxSize:
            coinQuantity = marketMaxSize
            tradeCoinQuantity = marketMaxSize

        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (price)))

        newClientOrderId = ''
        if tradeType == 'openLongsByLeft':
            newClientOrderId = 'leftOpenLongs_s' + str(ORDER_ID_INDEX)
        if tradeType == 'openShortsByLeft':
            newClientOrderId = 'leftOpenShortss_s' + str(ORDER_ID_INDEX)

        orderSide = ''
        if tradeType == 'openLongsByLeft':
            orderSide = OrderSide.BUY
        if tradeType == 'openShortsByLeft':
            orderSide = OrderSide.SELL
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        try:
            result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=orderSide, ordertype=OrderType.LIMIT,
                                               price=price, positionSide='BOTH', timeInForce=TimeInForce.GTC)
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        result = json.loads(result)
        resultArr.append(result)
    elif tradeType == 'openLongsByRight' or tradeType == 'openShortsByRight':

        mins = int(paraArr[0])
        priceIndex = float(paraArr[1])
        priceArr = getPolePrice(symbol, mins)
        highPrice = priceArr[0]
        if highPrice == 0:
            resp = json.dumps({'s': 'dataError', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        lowPirce = priceArr[1]
        price = 0
        stopPrice = 0
        if tradeType == 'openLongsByRight':
            price = highPrice * priceIndex
            stopPrice = highPrice
        if tradeType == 'openShortsByRight':
            price = lowPirce * priceIndex
            stopPrice = lowPirce

        coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / stopPrice))
        if coinQuantity > marketMaxSize:
            coinQuantity = marketMaxSize
            tradeCoinQuantity = marketMaxSize

        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (price)))

        newClientOrderId = ''
        if tradeType == 'openLongsByRight':
            newClientOrderId = 'rightOpenLongs_s' + str(ORDER_ID_INDEX)
        if tradeType == 'openShortsByRight':
            newClientOrderId = 'rightOpenShorts_s' + str(ORDER_ID_INDEX)

        orderSide = ''
        if tradeType == 'openLongsByRight':
            orderSide = OrderSide.BUY
        if tradeType == 'openShortsByRight':
            orderSide = OrderSide.SELL
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        try:
            result = request_client.post_auto_order_with_price(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=orderSide,
                                                               ordertype=OrderType.STOP, stopPrice=stopPrice, price=price, positionSide='BOTH', timeInForce=TimeInForce.GTC)
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        result = json.loads(result)
        resultArr.append(result)
    elif tradeType == 'openLongsByBatch' or tradeType == 'openShortsByBatch':
        depthObj = getFutureDepthBySymbol(symbol, 50)
        if not ('bids' in depthObj):
            resp = json.dumps({'s': 'dataError', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        depthType = paraArr[0]
        basicPrice = 0
        if depthType == 'mid':
            basicPrice = (float(depthObj['bids'][0][0]) + float(depthObj['bids'][0][0])) / 2
        elif depthType == 'buy':
            depthNumber = int(paraArr[1]) - 1
            basicPrice = float(depthObj['bids'][depthNumber][0])
        elif depthType == 'sell':
            depthNumber = int(paraArr[1]) - 1
            basicPrice = float(depthObj['asks'][depthNumber][0])

        priceIndex = float(paraArr[2])
        basicPrice = basicPrice * priceIndex

        addPricePercent = float(paraArr[4])
        orderCount = int(paraArr[5])
        priceArr = []
        if addPricePercent == 0:
            basicPrice = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (basicPrice)))
            for i in range(orderCount):
                if tradeType == 'openLongsByBatch':
                    priceArr.append(basicPrice - PRICE_TICK_OBJ[symbol] * i)
                if tradeType == 'openShortsByBatch':
                    priceArr.append(basicPrice + PRICE_TICK_OBJ[symbol] * i)
        else:
            for i in range(orderCount):
                if tradeType == 'openLongsByBatch':
                    priceArr.append(basicPrice * (1 - addPricePercent * i / 100))
                if tradeType == 'openShortsByBatch':
                    priceArr.append(basicPrice * (1 + addPricePercent * i / 100))

        for i in range(len(priceArr)):
            price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (priceArr[i])))

            coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / nowPrice / orderCount))
            if coinQuantity > marketMaxSize:
                coinQuantity = marketMaxSize
                tradeCoinQuantity = marketMaxSize

            timeInForce = ''
            if paraArr[6] == 'GTX':
                timeInForce = TimeInForce.GTX
            if paraArr[6] == 'GTC':
                timeInForce = TimeInForce.GTC

            ORDER_ID_INDEX = ORDER_ID_INDEX + 1
            newClientOrderId = ''
            if tradeType == 'openLongsByBatch':
                newClientOrderId = 'depthOpenLongs_s' + str(ORDER_ID_INDEX)
            if tradeType == 'openShortsByBatch':
                newClientOrderId = 'depthOpenShorts_s' + str(ORDER_ID_INDEX)

            orderSide = ''
            if tradeType == 'openLongsByBatch':
                orderSide = OrderSide.BUY
            if tradeType == 'openShortsByBatch':
                orderSide = OrderSide.SELL
            request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
            try:
                result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=orderSide,
                                                   ordertype=OrderType.LIMIT, price=price, positionSide='BOTH', timeInForce=timeInForce)
            except Exception as e:
                resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
                response.set_header('Access-Control-Allow-Origin', '*')
                return resp
            result = json.loads(result)
            resultArr.append(result)
    elif tradeType == 'openLongsByPrice':
        price = float(paraArr[0])
        clientIDPrefix = ''
        if price > nowPrice:
            clientIDPrefix = 'rightOpenLongs'
        if price <= nowPrice:
            clientIDPrefix = 'leftOpenLongs'

        coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / price))
        price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (price)))
        if coinQuantity > marketMaxSize:
            coinQuantity = marketMaxSize
            tradeCoinQuantity = marketMaxSize
        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = clientIDPrefix + '_s' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])

        try:
            if clientIDPrefix == 'leftOpenLongs':
                result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.BUY,
                                                   ordertype=OrderType.LIMIT, positionSide='BOTH', price=price, timeInForce=TimeInForce.GTC)
            if clientIDPrefix == 'rightOpenLongs':
                result = request_client.post_auto_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.BUY,
                                                        ordertype=OrderType.STOP_MARKET, stopPrice=price, price='0', positionSide='BOTH', timeInForce=TimeInForce.GTC)
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp

        result = json.loads(result)
        resultArr.append(result)
    elif tradeType == 'openShortsByPrice':
        price = float(paraArr[0])
        clientIDPrefix = ''
        if price < nowPrice:
            clientIDPrefix = 'rightOpenShorts'
        if price >= nowPrice:
            clientIDPrefix = 'leftOpenShorts'

        coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / price))
        price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (price)))
        if coinQuantity > marketMaxSize:
            coinQuantity = marketMaxSize
            tradeCoinQuantity = marketMaxSize
        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = clientIDPrefix + '_s' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])

        try:
            if clientIDPrefix == 'leftOpenShorts':
                result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.SELL,
                                                   ordertype=OrderType.LIMIT, positionSide='BOTH', price=price, timeInForce=TimeInForce.GTC)
            if clientIDPrefix == 'rightOpenShorts':
                result = request_client.post_auto_order(newClientOrderId=newClientOrderId, reduceOnly=False, symbol=symbol, quantity=coinQuantity, side=OrderSide.SELL,
                                                        ordertype=OrderType.STOP_MARKET, stopPrice=price, price='0', positionSide='BOTH', timeInForce=TimeInForce.GTC)
        except Exception as e:
            print(e)
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp

        result = json.loads(result)
        resultArr.append(result)

    resp = json.dumps({'s': 'ok', 'resultArr': resultArr, 'tradeCoinQuantity': tradeCoinQuantity, 'money': money, 'symbol': symbol, 'tradeType': tradeType})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/close_position')
def close_position():
    global API_OBJ, PRICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, RECENT_ORDERS_OBJ, ORDER_ID_INDEX
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    money = float(request.forms.get('money'))
    tradeType = str(request.forms.get('tradeType'))
    nowPrice = float(request.forms.get('nowPrice'))
    direction = str(request.forms.get('direction'))
    paraArr = json.loads(request.forms.get('paraArr'))
    now = int(time.time())
    marketMaxSize = MARKET_MAX_SIZE_OBJ[symbol]
    tradeCoinQuantity = 0
    resultArr = []
    if tradeType == 'selectCoinCloseByMarket':

        newClientOrderId = 'marketCloseLongs_s' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        orderSide = ''
        if direction == 'longs':
            orderSide = OrderSide.SELL
        if direction == 'shorts':
            orderSide = OrderSide.BUY

        try:
            result = request_client.post_market_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=marketMaxSize, side=orderSide,
                                                      ordertype=OrderType.MARKET, price='0', positionSide='BOTH', timeInForce=TimeInForce.GTC)
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp

        resultArr.append(json.loads(result))
        coinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / nowPrice))


    elif tradeType == 'selectCoinCloseByDepth':
        depthObj = getFutureDepthBySymbol(symbol, 50)
        if not ('bids' in depthObj):
            resp = json.dumps({'s': 'dataError', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp

        moneyIndex = float(paraArr[0])
        money = money * moneyIndex

        depthType = paraArr[1]
        price = 0
        depthNumber = int(paraArr[2]) - 1
        if depthType == 'mid':
            price = (float(depthObj['bids'][0][0]) + float(depthObj['bids'][0][0])) / 2
        elif depthType == 'reverse':
            if direction == 'longs':
                price = float(depthObj['bids'][depthNumber][0])
            if direction == 'shorts':
                price = float(depthObj['asks'][depthNumber][0])
        elif depthType == 'positive':
            if direction == 'longs':
                price = float(depthObj['asks'][depthNumber][0])
            if direction == 'shorts':
                price = float(depthObj['bids'][depthNumber][0])

        priceIndex = 0
        if direction == 'longs':
            priceIndex = float(paraArr[3])
        if direction == 'shorts':
            priceIndex = float(paraArr[4])

        price = price * priceIndex
        price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (price)))
        coinQuantity = float(decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / nowPrice)))
        if coinQuantity > marketMaxSize:
            coinQuantity = marketMaxSize
            tradeCoinQuantity = marketMaxSize

        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = ''
        if direction == 'longs':
            newClientOrderId = 'depthLongsClose_s' + str(ORDER_ID_INDEX)
        if direction == 'shorts':
            newClientOrderId = 'depthShortsClose_s' + str(ORDER_ID_INDEX)
        print(newClientOrderId)
        timeInForce = ''
        if paraArr[5] == 'GTX':
            timeInForce = TimeInForce.GTX
        if paraArr[5] == 'GTC':
            timeInForce = TimeInForce.GTC

        orderSide = ''
        if direction == 'longs':
            orderSide = OrderSide.SELL
        if direction == 'shorts':
            orderSide = OrderSide.BUY
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        try:
            result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=coinQuantity, side=orderSide, ordertype=OrderType.LIMIT,
                                               price=price, positionSide='BOTH', timeInForce=timeInForce)
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        resultArr.append(json.loads(result))

    elif tradeType == 'selectCoinCloseByBatch':
        depthObj = getFutureDepthBySymbol(symbol, 50)
        if not ('bids' in depthObj):
            resp = json.dumps({'s': 'dataError', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp

        moneyIndex = float(paraArr[0])
        money = money * moneyIndex

        depthType = paraArr[1]
        basicPrice = 0
        depthNumber = int(paraArr[2]) - 1
        if depthType == 'mid':
            basicPrice = (float(depthObj['asks'][0][0]) + float(depthObj['bids'][0][0])) / 2
        elif depthType == 'reverse':
            if direction == 'longs':
                basicPrice = float(depthObj['bids'][depthNumber][0])
            if direction == 'shorts':
                basicPrice = float(depthObj['asks'][depthNumber][0])
        elif depthType == 'positive':
            if direction == 'longs':
                basicPrice = float(depthObj['asks'][depthNumber][0])
            if direction == 'shorts':
                basicPrice = float(depthObj['bids'][depthNumber][0])

        priceIndex = 0
        if direction == 'longs':
            priceIndex = float(paraArr[3])
        if direction == 'shorts':
            priceIndex = float(paraArr[4])

        basicPrice = basicPrice * priceIndex

        priceArr = []

        addPricePercent = float(paraArr[5])
        orderCount = int(paraArr[6])
        if addPricePercent == 0:
            basicPrice = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (basicPrice)))
            for i in range(orderCount):
                if direction == 'longs':
                    priceArr.append(basicPrice + PRICE_TICK_OBJ[symbol] * i)
                if direction == 'shorts':
                    priceArr.append(basicPrice - PRICE_TICK_OBJ[symbol] * i)
        else:
            for i in range(orderCount):
                if direction == 'longs':
                    priceArr.append(basicPrice * (1 + addPricePercent * i / 100))
                if direction == 'shorts':
                    priceArr.append(basicPrice * (1 - addPricePercent * i / 100))

        for i in range(len(priceArr)):
            price = float(decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (priceArr[i])))
            coinQuantity = float(decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (money / nowPrice / orderCount)))
            if coinQuantity > marketMaxSize:
                coinQuantity = marketMaxSize
                tradeCoinQuantity = marketMaxSize

            ORDER_ID_INDEX = ORDER_ID_INDEX + 1
            newClientOrderId = ''
            if direction == 'longs':
                newClientOrderId = 'batchLongsClose_s' + str(ORDER_ID_INDEX)
            if direction == 'shorts':
                newClientOrderId = 'batchShortsClose_s' + str(ORDER_ID_INDEX)

            timeInForce = ''
            if paraArr[7] == 'GTX':
                timeInForce = TimeInForce.GTX
            if paraArr[7] == 'GTC':
                timeInForce = TimeInForce.GTC

            orderSide = ''
            if direction == 'longs':
                orderSide = OrderSide.SELL
            if direction == 'shorts':
                orderSide = OrderSide.BUY
            request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
            try:
                result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=coinQuantity, side=orderSide,
                                                   ordertype=OrderType.LIMIT, price=price, positionSide='BOTH', timeInForce=timeInForce)
            except Exception as e:
                resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
                response.set_header('Access-Control-Allow-Origin', '*')
                return resp
            resultArr.append(json.loads(result))
    resp = json.dumps({'s': 'ok', 'resultArr': resultArr, 'tradeCoinQuantity': tradeCoinQuantity, 'marketMaxSize': marketMaxSize, 'symbol': symbol, 'tradeType': tradeType})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/stop_loss_batch')
def stop_loss_batch():
    global API_OBJ, PRICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, RECENT_ORDERS_OBJ, ORDER_ID_INDEX, MARKET_MAX_SIZE_OBJ
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    coinAmount = float(request.forms.get('coinAmount'))
    positionDirection = str(request.forms.get('positionDirection'))
    stopLossPriceArr = json.loads(request.forms.get('stopLossPriceArr'))

    now = int(time.time())
    marketMaxSize = MARKET_MAX_SIZE_OBJ[symbol]

    # request_client = RequestClient(api_key=apiKey,secret_key=API_OBJ[apiKey])
    # result = request_client.get_open_orders(symbol=symbol)
    # result = json.loads(result)
    # stopLossOrderIDArr = []

    # for i in range(len(result)):
    #     clientOrderId = result[i]['clientOrderId']
    #     orderTypeSymbol = clientOrderId.split("_")[0]
    #     if orderTypeSymbol=="shortsStopLoss" or orderTypeSymbol=="longsStopLoss":
    #         stopLossOrderIDArr.append(clientOrderId)

    # for i in range(len(stopLossOrderIDArr)):
    #     try:
    #         request_client = RequestClient(api_key=apiKey,secret_key=API_OBJ[apiKey])
    #         result = request_client.cancel_order(symbol=symbol,orderId=stopLossOrderIDArr[i])
    #     except Exception as e:
    #         try:
    #             request_client = RequestClient(api_key=apiKey,secret_key=API_OBJ[apiKey])
    #             result = request_client.cancel_order(symbol=symbol,orderId=stopLossOrderIDArr[i])
    #         except Exception as e:
    #             print(e)

    stopLossCoinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (coinAmount / len(stopLossPriceArr)))

    orderResultArr = []
    positionSide = OrderSide.BUY
    if positionDirection == 'longs':
        positionSide = OrderSide.SELL

    someOrderTimeOut = False
    for i in range(len(stopLossPriceArr)):
        stopLossPrice = decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (stopLossPriceArr[i]))
        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = positionDirection + 'StopLoss_s_' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        if i == len(stopLossPriceArr) - 1:
            stopLossCoinQuantity = coinAmount - float(decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (coinAmount / len(stopLossPriceArr)))) * (len(stopLossPriceArr) - 1)
            stopLossCoinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (stopLossCoinQuantity))
        try:
            result = request_client.post_auto_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=stopLossCoinQuantity, side=positionSide,
                                                    ordertype=OrderType.STOP_MARKET, stopPrice=stopLossPrice, positionSide='BOTH', timeInForce=TimeInForce.GTC)
        except Exception as e:
            someOrderTimeOut = True
        result = json.loads(result)
        orderResultArr.append(result)

    resp = json.dumps({'s': 'ok', 'resultArr': orderResultArr, 'symbol': symbol, 'someOrderTimeOut': someOrderTimeOut})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/stop_loss_once')
def stop_loss_once():
    global API_OBJ, PRICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, RECENT_ORDERS_OBJ, ORDER_ID_INDEX, MARKET_MAX_SIZE_OBJ
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    coinAmount = float(request.forms.get('coinAmount'))
    stopLossType = str(request.forms.get('stopLossType'))
    stopLossParaArr = json.loads(request.forms.get('stopLossParaArr'))
    positionDirection = str(request.forms.get('positionDirection'))

    now = int(time.time())
    marketMaxSize = MARKET_MAX_SIZE_OBJ[symbol]

    # request_client = RequestClient(api_key=apiKey,secret_key=API_OBJ[apiKey])
    # result = request_client.get_open_orders(symbol=symbol)
    # result = json.loads(result)
    # stopLossOrderIDArr = []

    # for i in range(len(result)):
    #     clientOrderId = result[i]['clientOrderId']
    #     orderTypeSymbol = clientOrderId.split("_")[0]
    #     if orderTypeSymbol=="shortsStopLoss" or orderTypeSymbol=="longsStopLoss":
    #         stopLossOrderIDArr.append(clientOrderId)

    # for i in range(len(stopLossOrderIDArr)):
    #     try:
    #         request_client = RequestClient(api_key=apiKey,secret_key=API_OBJ[apiKey])
    #         result = request_client.cancel_order(symbol=symbol,orderId=stopLossOrderIDArr[i])
    #     except Exception as e:
    #         try:
    #             request_client = RequestClient(api_key=apiKey,secret_key=API_OBJ[apiKey])
    #             result = request_client.cancel_order(symbol=symbol,orderId=stopLossOrderIDArr[i])
    #         except Exception as e:
    #             print(e)

    stopLossPrice = 0
    if stopLossType == 'time':
        timeIndex = stopLossParaArr[1]
        stopLossPrice = getStopLossPriceByTime(symbol, stopLossParaArr[0], positionDirection) * timeIndex
    elif stopLossType == 'price':
        stopLossPrice = float(stopLossParaArr[0])

    stopLossPrice = decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (stopLossPrice))
    orderResultArr = []
    positionSide = OrderSide.BUY
    if positionDirection == 'longs':
        positionSide = OrderSide.SELL
    orderCount = math.ceil(coinAmount / marketMaxSize)
    if orderCount > 10:
        resp = json.dumps({'s': 'tooMuchPosition', 'marketMaxSize': marketMaxSize, 'symbol': symbol})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp
    if orderCount == 1:
        coinAmount = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (coinAmount))
        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = positionDirection + 'StopLoss_s_' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        try:
            result = request_client.post_auto_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=coinAmount, side=positionSide,
                                                    ordertype=OrderType.STOP_MARKET, stopPrice=stopLossPrice, positionSide='BOTH', timeInForce=TimeInForce.GTC)
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        result = json.loads(result)
        orderResultArr.append(result)
    else:
        for i in range(orderCount):
            ORDER_ID_INDEX = ORDER_ID_INDEX + 1
            newClientOrderId = positionDirection + 'StopLoss_s_' + str(ORDER_ID_INDEX)
            request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
            try:
                result = request_client.post_auto_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=marketMaxSize, side=positionSide,
                                                        ordertype=OrderType.STOP_MARKET, stopPrice=stopLossPrice, positionSide='BOTH', timeInForce=TimeInForce.GTC)
            except Exception as e:
                resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
                response.set_header('Access-Control-Allow-Origin', '*')
                return resp
            result = json.loads(result)
            orderResultArr.append(result)
    resp = json.dumps({'s': 'ok', 'resultArr': orderResultArr, 'symbol': symbol, 'stopLossType': stopLossType})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/stop_profit_batch')
def stop_profit_batch():
    global API_OBJ, PRICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, RECENT_ORDERS_OBJ, ORDER_ID_INDEX, MARKET_MAX_SIZE_OBJ
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    coinAmount = float(request.forms.get('coinAmount'))
    positionDirection = str(request.forms.get('positionDirection'))
    stopProfitPriceArr = json.loads(request.forms.get('stopProfitPriceArr'))

    now = int(time.time())
    marketMaxSize = MARKET_MAX_SIZE_OBJ[symbol]

    request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
    result = request_client.get_open_orders(symbol=symbol)
    result = json.loads(result)
    stopProfitOrderIDArr = []

    for i in range(len(result)):
        clientOrderId = result[i]['clientOrderId']
        orderTypeSymbol = clientOrderId.split('_')[0]
        if orderTypeSymbol == 'shortsStopProfit' or orderTypeSymbol == 'longsStopProfit':
            stopProfitOrderIDArr.append(clientOrderId)

    for i in range(len(stopProfitOrderIDArr)):
        try:
            request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
            result = request_client.cancel_order(symbol=symbol, orderId=stopProfitOrderIDArr[i])
        except Exception as e:
            try:
                request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
                result = request_client.cancel_order(symbol=symbol, orderId=stopProfitOrderIDArr[i])
            except Exception as e:
                print(e)

    stopProfitCoinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (coinAmount / len(stopProfitPriceArr)))

    if stopProfitCoinQuantity > marketMaxSize:
        resp = json.dumps({'s': 'tooMuchPosition', 'marketMaxSize': marketMaxSize, 'symbol': symbol})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp

    orderResultArr = []
    positionSide = OrderSide.BUY
    if positionDirection == 'longs':
        positionSide = OrderSide.SELL

    someOrderTimeOut = False
    for i in range(len(stopProfitPriceArr)):
        stopProfitPrice = decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (stopProfitPriceArr[i]))
        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = positionDirection + 'StopProfit_s_' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        if i == len(stopProfitPriceArr) - 1:
            stopProfitCoinQuantity = coinAmount - float(decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (coinAmount / len(stopProfitPriceArr)))) * (len(stopProfitPriceArr) - 1)
            stopProfitCoinQuantity = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (stopProfitCoinQuantity))
        try:
            result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=stopProfitCoinQuantity, side=positionSide,
                                               ordertype=OrderType.LIMIT, price=stopProfitPrice, positionSide='BOTH', timeInForce=TimeInForce.GTX)
        except Exception as e:
            someOrderTimeOut = True
        result = json.loads(result)
        orderResultArr.append(result)

    resp = json.dumps({'s': 'ok', 'resultArr': orderResultArr, 'symbol': symbol, 'someOrderTimeOut': someOrderTimeOut})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/stop_profit_once')
def stop_profit_once():
    global API_OBJ, PRICE_DECIMAL_OBJ, AMOUNT_DECIMAL_OBJ, RECENT_ORDERS_OBJ, ORDER_ID_INDEX, MARKET_MAX_SIZE_OBJ
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    coinAmount = float(request.forms.get('coinAmount'))
    stopProfitType = str(request.forms.get('stopProfitType'))
    stopProfitParaArr = json.loads(request.forms.get('stopProfitParaArr'))
    positionDirection = str(request.forms.get('positionDirection'))

    now = int(time.time())
    marketMaxSize = MARKET_MAX_SIZE_OBJ[symbol]

    request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
    result = request_client.get_open_orders(symbol=symbol)
    result = json.loads(result)
    stopProfitOrderIDArr = []

    for i in range(len(result)):
        clientOrderId = result[i]['clientOrderId']
        orderTypeSymbol = clientOrderId.split('_')[0]
        if orderTypeSymbol == 'shortsStopProfit' or orderTypeSymbol == 'longsStopProfit':
            stopProfitOrderIDArr.append(clientOrderId)

    for i in range(len(stopProfitOrderIDArr)):
        try:
            request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
            result = request_client.cancel_order(symbol=symbol, orderId=stopProfitOrderIDArr[i])
        except Exception as e:
            try:
                request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
                result = request_client.cancel_order(symbol=symbol, orderId=stopProfitOrderIDArr[i])
            except Exception as e:
                print(e)

    stopProfitPrice = 0
    if stopProfitType == 'time':
        timeIndex = stopProfitParaArr[1]
        stopProfitPrice = getStopProfitPriceByTime(symbol, stopProfitParaArr[0], positionDirection) * timeIndex
    elif stopProfitType == 'price':
        stopProfitPrice = float(stopProfitParaArr[0])

    stopProfitPrice = decimal.Decimal(PRICE_DECIMAL_OBJ[symbol] % (stopProfitPrice))
    orderResultArr = []
    positionSide = OrderSide.BUY
    if positionDirection == 'longs':
        positionSide = OrderSide.SELL
    orderCount = math.ceil(coinAmount / marketMaxSize)
    if orderCount > 10:
        resp = json.dumps({'s': 'tooMuchPosition', 'marketMaxSize': marketMaxSize, 'symbol': symbol})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp
    if orderCount == 1:
        coinAmount = decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (coinAmount))
        ORDER_ID_INDEX = ORDER_ID_INDEX + 1
        newClientOrderId = positionDirection + 'StopProfit_s_' + str(ORDER_ID_INDEX)
        request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
        try:
            result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=coinAmount, side=positionSide, ordertype=OrderType.LIMIT,
                                               price=stopProfitPrice, positionSide='BOTH', timeInForce=TimeInForce.GTX)
        except Exception as e:
            resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
            response.set_header('Access-Control-Allow-Origin', '*')
            return resp
        result = json.loads(result)
        orderResultArr.append(result)
    else:
        for i in range(orderCount):
            ORDER_ID_INDEX = ORDER_ID_INDEX + 1
            newClientOrderId = positionDirection + 'StopProfit_s_' + str(ORDER_ID_INDEX)
            request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
            try:
                result = request_client.post_order(newClientOrderId=newClientOrderId, reduceOnly=True, symbol=symbol, quantity=marketMaxSize, side=positionSide,
                                                   ordertype=OrderType.LIMIT, price=stopProfitPrice, positionSide='BOTH', timeInForce=TimeInForce.GTX)
            except Exception as e:
                resp = json.dumps({'s': 'timeout', 't': tradeType, 'i': symbol})
                response.set_header('Access-Control-Allow-Origin', '*')
                return resp
            result = json.loads(result)
            orderResultArr.append(result)
    resp = json.dumps({'s': 'ok', 'resultArr': orderResultArr, 'symbol': symbol, 'stopProfitType': stopProfitType})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/ping')
def ping():
    global PRIVATE_IP_OBJ, API_OBJ, UPDATE_POSITION_TS
    accessToken = str(request.forms.get('accessToken'))
    apiKey = str(request.forms.get('apiKey'))
    apiIndex = int(request.forms.get('apiIndex'))
    timestamp = int(request.forms.get('timestamp'))
    autoBuyBnbConfigArr = json.loads(request.forms.get('autoBuyBnbConfigArr'))

    autoBuyBnb = autoBuyBnbConfigArr[2]
    beginMinBnbMoney = autoBuyBnbConfigArr[0]
    buyBNBMoney = autoBuyBnbConfigArr[1]

    print(autoBuyBnb)
    updateAPIObj(apiKey)
    symbol = str(request.forms.get('symbol'))
    now = int(time.time() * 1000)
    binanceInfoArr = getBinanceAccountInfo(apiIndex, apiKey, autoBuyBnb, beginMinBnbMoney, buyBNBMoney, accessToken)
    resp = json.dumps({'s': 'ok', 'p': binanceInfoArr[0], 't': binanceInfoArr[1], 'r': binanceInfoArr[2], 'n': now, 'b': binanceInfoArr[3], 'l': timestamp})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_symbol_index')
def getSymbolIndex():
    sql = "select `symbol`,`id`,`coin`,`index`,`quote`,`linkSymbolArr`,`defaultShow` from trade_symbol where `status`='yes' order by id asc"
    tradeSymbolData = FUNCTION_CLIENT.mysql_pool_select(sql, [])

    tradeSymbolArr = []
    for i in range(len(tradeSymbolData)):
        symbolIndex = i
        tradeSymbolArr.append({
            'symbol': tradeSymbolData[i][0],
            'coin': tradeSymbolData[i][2],
            'symbolIndex': tradeSymbolData[i][3],
            'quote': tradeSymbolData[i][4],
            'linkSymbolArr': json.loads(tradeSymbolData[i][5]),
            'defaultShow': tradeSymbolData[i][6],
            'weight': 0
        })

    resp = json.dumps({'s': 'ok', 'd': tradeSymbolArr})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/record_visiter')
def record_visiter():
    page = str(request.forms.get('page'))
    ip = request.environ.get('REMOTE_ADDR')
    sql = 'INSERT INTO visiter ( ip,`time`,`page`)  VALUES ( %s, %s,%s );'
    FUNCTION_CLIENT.mysql_pool_commit(sql, [ip, FUNCTION_CLIENT.turn_ts_to_time(int(time.time())), page])
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/update_show_symbol_obj')
def updateShowSymbolObj():
    accessToken = str(request.forms.get('accessToken'))
    showSymbolObj = {}
    sql = 'select `symbol`,`defaultShow` from trade_symbol'
    tradeSymbolData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
    for i in range(len(tradeSymbolData)):
        showSymbolObj[tradeSymbolData[i][0]] = tradeSymbolData[i][1]
    sql = 'update user set showSymbolObj=%s where accessToken=%s'
    FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(showSymbolObj), accessToken])
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/register')
def register():
    account = str(request.forms.get('account'))
    password = str(request.forms.get('password'))
    newHotKeyConfigObj = str(request.forms.get('newHotKeyConfigObj'))
    ip = request.environ.get('REMOTE_ADDR')
    name = str(request.forms.get('name'))
    if len(account) < 4 or len(account) > 20:
        resp = json.dumps({'s': 'accountLengthError'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp
    if len(password) < 4 or len(password) > 20:
        resp = json.dumps({'s': 'passwordLengthError'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp
    if len(name) < 1 or len(name) > 20:
        resp = json.dumps({'s': 'nameLengthError'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp

    sql = 'select `id` from user where `account`=%s'
    userData = FUNCTION_CLIENT.mysql_pool_select(sql, [account])

    if len(userData) > 0:
        resp = json.dumps({'s': 'repeatRegister'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp

    showSymbolObj = {}
    sql = 'select `symbol`,`defaultShow` from trade_symbol'
    tradeSymbolData = FUNCTION_CLIENT.mysql_pool_select(sql, [])
    for i in range(len(tradeSymbolData)):
        showSymbolObj[tradeSymbolData[i][0]] = tradeSymbolData[i][1]

    if len(userData) > 0:
        resp = json.dumps({'s': 'repeatRegister'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp

    accessToken = ''.join(random.sample(string.ascii_letters + string.digits, 30))
    sql = 'INSERT INTO user ( `registerIP`,account,`password`,`name`,`registerTime`,`binanceApiArr`,`hotKeyConfigObj`,`stateConfigObj`,`serverInfoObj`,`accessToken`,`showSymbolObj`)  VALUES ( %s,%s,%s,%s, %s,%s ,%s,%s,%s,%s,%s  );'
    FUNCTION_CLIENT.mysql_pool_commit(sql,
                                      [ip, account, password, name, FUNCTION_CLIENT.turn_ts_to_time(int(time.time())), json.dumps([]), json.dumps(json.loads(newHotKeyConfigObj)),
                                       json.dumps({}), json.dumps({}), accessToken, json.dumps(showSymbolObj)])
    resp = json.dumps({'s': 'ok'})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/login')
def login():
    account = str(request.forms.get('account'))
    password = str(request.forms.get('password'))

    sql = 'select `password`,`usdtAssets`,`binanceApiArr`,`hotKeyConfigObj`,`stateConfigObj`,`serverInfoObj`,`name`,`accessToken`,`showSymbolObj` from user where `account`=%s '
    userData = FUNCTION_CLIENT.mysql_pool_select(sql, [account])
    if len(userData) == 0:
        resp = json.dumps({'s': 'noRegister'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp
    elif userData[0][0] != password:
        resp = json.dumps({'s': 'passwordError'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp
    else:
        binanceApiArr = json.loads(userData[0][2])
        for i in range(len(binanceApiArr)):
            binanceApiArr[i]['apiSecret'] = ''
        resp = json.dumps(
            {'s': 'ok', 'showSymbolObj': json.loads(userData[0][8]), 'account': account, 'password': userData[0][0], 'usdtAssets': userData[0][1], 'binanceApiArr': binanceApiArr,
             'hotKeyConfigObj': json.loads(userData[0][3]), 'stateConfigObj': json.loads(userData[0][4]), 'serverInfoObj': json.loads(userData[0][5]), 'name': userData[0][6],
             'accessToken': userData[0][7]})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp


@app.post('/add_api')
def add_api():
    accessToken = str(request.forms.get('accessToken'))
    apiKey = str(request.forms.get('apiKey'))
    apiSecret = str(request.forms.get('apiSecret'))
    apiDescribe = str(request.forms.get('apiDescribe'))

    request_client = RequestClient(api_key=apiKey, secret_key=apiSecret)
    result = request_client.get_position()
    result = json.loads(result)
    print(type(result))
    # {'code': -2014, 'msg': 'API-key format invalid.'}
    if 'code' in result and result['code'] == -2014:
        resp = json.dumps({'s': 'error'})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp
    else:

        sql = 'select `binanceApiArr` from user where `accessToken`=%s '
        userData = FUNCTION_CLIENT.mysql_pool_select(sql, [accessToken])
        binanceApiArr = json.loads(userData[0][0])
        binanceApiArr.append({'apiKey': apiKey, 'apiSecret': apiSecret, 'apiDescribe': apiDescribe})
        sql = 'update user set `binanceApiArr`=%s where `accessToken`=%s '
        FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(binanceApiArr), accessToken])
        resp = json.dumps({'s': 'ok', 'binanceApiArr': binanceApiArr})
        response.set_header('Access-Control-Allow-Origin', '*')
        return resp


@app.post('/change_leverage')
def change_leverage():
    global API_OBJ
    symbol = str(request.forms.get('symbol'))
    leverage = int(request.forms.get('leverage'))
    apiKey = str(request.forms.get('apiKey'))
    updateAPIObj(apiKey)
    request_client = RequestClient(api_key=apiKey, secret_key=API_OBJ[apiKey])
    result = request_client.change_initial_leverage(symbol, leverage)
    result = json.loads(result)
    resp = json.dumps({'s': 'ok', 'result': result})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/change_quote')
def change_quote():
    global API_OBJ
    accessToken = str(request.forms.get('accessToken'))
    newShowSymbolObj = json.loads(request.forms.get('newShowSymbolObj'))
    sql = 'update user set `showSymbolObj`=%s where `accessToken`=%s '
    FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(newShowSymbolObj), accessToken])
    resp = json.dumps({'s': 'ok', 'newShowSymbolObj': newShowSymbolObj})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/delete_api')
def delete_api():
    accessToken = str(request.forms.get('accessToken'))
    apiKey = str(request.forms.get('apiKey'))

    sql = 'select `binanceApiArr` from user where `accessToken`=%s '
    userData = FUNCTION_CLIENT.mysql_pool_select(sql, [accessToken])
    binanceApiArr = json.loads(userData[0][0])

    deleteIndex = -1
    for i in range(len(binanceApiArr)):
        if binanceApiArr[i]['apiKey'] == apiKey:
            deleteIndex = i
    if deleteIndex != -1:
        del binanceApiArr[deleteIndex]
    sql = 'update user set `binanceApiArr`=%s where `accessToken`=%s '
    FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(binanceApiArr), accessToken])
    resp = json.dumps({'s': 'ok', 'binanceApiArr': binanceApiArr})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/modify_hot_key')
def modify_hot_key():
    accessToken = str(request.forms.get('accessToken'))
    newHotKeyConfigObj = str(request.forms.get('newHotKeyConfigObj'))
    sql = 'update user set `hotKeyConfigObj`=%s where `accessToken`=%s '
    FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(json.loads(newHotKeyConfigObj)), accessToken])
    resp = json.dumps({'s': 'ok', 'newHotKeyConfigObj': newHotKeyConfigObj})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/get_state_config')
def get_state_config():
    accessToken = str(request.forms.get('accessToken'))
    apiKey = str(request.forms.get('apiKey'))

    sql = 'select `stateConfigObj` from user where `accessToken`=%s '
    userData = FUNCTION_CLIENT.mysql_pool_select(sql, [accessToken])
    stateConfigObj = json.loads(userData[0][0])
    resp = json.dumps({'s': 'ok', 'stateConfigObj': stateConfigObj})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/modify_state_config')
def modify_state_config():
    accessToken = str(request.forms.get('accessToken'))
    stateConfigObj = json.loads(request.forms.get('stateConfigObj'))
    sql = 'update user set `stateConfigObj`=%s where `accessToken`=%s '
    FUNCTION_CLIENT.mysql_pool_commit(sql, [json.dumps(stateConfigObj), accessToken])

    resp = json.dumps({'s': 'ok', 'stateConfigObj': stateConfigObj})
    response.set_header('Access-Control-Allow-Origin', '*')
    return resp


@app.post('/take_open')
def take_open(
    key: str = Form(...),
    secret: str = Form(...),
    symbol: str = Form(...),
    price: str = Form(...),
    direction: str = Form(...),
    open_time: str = Form(...),
    position_value: str = Form(...),
):
    global AMOUNT_DECIMAL_OBJ, PRIVATE_IP, TAKE_OPEN_OBJ

    try:

        now = int(time.time() * 1000)

        if (position_value == 0 and symbol in TAKE_OPEN_OBJ and now - TAKE_OPEN_OBJ[symbol]['ts'] > 60000 * 15) or (
            symbol in TAKE_OPEN_OBJ and TAKE_OPEN_OBJ[symbol]['status'] == 'end') or (symbol in TAKE_OPEN_OBJ and open_time > TAKE_OPEN_OBJ[symbol]['openTime']) or (
            not symbol in TAKE_OPEN_OBJ):
            TAKE_OPEN_OBJ[symbol] = {'ts': now, 'openTime': open_time, 'status': 'trading'}

            if direction == 'longs':
                value = 100
                quantity = float(decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (value / price)))
                takeLongsOrder(price, quantity, 'T', symbol, key, secret)
                FUNCTION_CLIENT.send_lark_msg_limit_one_min(symbol + ' take longs')

            if direction == 'shorts':
                value = 100
                quantity = float(decimal.Decimal(AMOUNT_DECIMAL_OBJ[symbol] % (value / price)))
                takeShortsOrder(price, quantity, 'T', symbol, key, secret)
                FUNCTION_CLIENT.send_lark_msg_limit_one_min(symbol + ' take shorts')

    except Exception as e:
        ex = traceback.format_exc()
        FUNCTION_CLIENT.send_lark_msg_limit_one_min(str(ex))

    return {'s': 'ok'}


@app.post('/end_open')
def end_open(symbol: str = Form(...)):
    global AMOUNT_DECIMAL_OBJ, PRIVATE_IP, TAKE_OPEN_OBJ

    try:
        if symbol in TAKE_OPEN_OBJ and TAKE_OPEN_OBJ[symbol]['status'] != 'end':
            TAKE_OPEN_OBJ[symbol]['status'] = 'end'
            FUNCTION_CLIENT.send_lark_msg_limit_one_min(symbol + ' end trade')
    except Exception as e:
        ex = traceback.format_exc()
        FUNCTION_CLIENT.send_lark_msg_limit_one_min(str(ex))

    return {'s': 'ok'}


def main():
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8888)


if __name__ == '__main__':
    sys.exit(main())
