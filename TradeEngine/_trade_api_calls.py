from quart import Quart, render_template, websocket
from quart import request, jsonify
import aiohttp
import asyncio
import time
import json

engine_api = Quart(__name__)
pfx = '/cc/api/v1'


@engine_api.route(pfx + '/ping', methods=['GET'])
def home():
    return 'pong'


@engine_api.route(pfx + '/save', methods=['GET'])
async def save():
    await engine_api.worker.save()


@engine_api.route(pfx + '/get_ohlc', methods=['GET'])
async def get_ohlc():
    test = await engine_api.worker.simple_getohlc('Binance')
    return jsonify(test)


@engine_api.route(pfx + '/prices', methods=['POST'])
async def get_ex_price():
    form = await request.form
    print(form)
    ex = engine_api.worker.exchange_selector(form['ex'])
    print(ex)
    return ex.prices


@engine_api.route(pfx + '/bb_data', methods=['GET'])
async def get_bb_data():
    data = {}
    data['strat'] = engine_api.worker.bb_strat.to_json()
    data['cards'] = engine_api.worker.bb_cards
    data['trades'] = engine_api.worker.bb_trades
    data['trade_limit'] = engine_api.worker.bb_trade_limit
    data['active'] = engine_api.worker.bb_active
    return jsonify(data)


@engine_api.route(pfx + '/ab_data', methods=['GET'])
async def get_ab_data():
    data = {}
    data['cards'] = engine_api.worker.ab_cards
    data['trades'] = engine_api.worker.ab_trades
    data['trade_limit'] = engine_api.worker.ab_trade_limit
    data['active'] = engine_api.worker.ab_active
    return jsonify(data)


@engine_api.route(pfx + '/api_keys', methods=['GET'])
async def get_api_data():
    data = {}
    for exchange in engine_api.worker.exchanges:
        ex = engine_api.worker.exchange_selector(exchange)
        data[exchange] = {}
        # try:
        if ex.apiKey:
            data[exchange]['key'] = ex.apiKey
            data[exchange]['secret'] = ex.secret
            if exchange == 'Coinbase Pro':
                data[exchange]['password'] = ex.password
        else:
            data[exchange]['key'] = ''
            data[exchange]['secret'] = ''
            if exchange == 'Coinbase Pro':
                data[exchange]['password'] = ''
        # except Exception as e:
        #     await engine_api.worker.my_msg('Error in posting API data ' + exchange, False, False)
        #     return str(e)
    if engine_api.worker.tele_bot:
        try:
            data['tele_token'] = engine_api.worker.tele_bot.token
            data['tele_chat'] = engine_api.worker.tele_bot.chat_id
        except Exception as e:
            data['tele_token'] = ''
            data['tele_chat'] = ''
    else:
        data['tele_token'] = ''
        data['tele_chat'] = ''
        

    return jsonify(data)


@engine_api.route(pfx + '/set_api_keys', methods=['POST'])
async def set_api_data():
    import ast
    form = await request.form
    data = ast.literal_eval(form['data'])
    for dd in data:
        ex = engine_api.worker.exchange_selector(dd)
        # try:
        print(data, dd)
        print(data[dd])
        ex.apiKey = data[dd]['key'] 
        ex.secret = data[dd]['secret'] 
        if dd == 'Coinbase Pro':
                ex.password = data[dd]['password'] 
        
        # except Exception as e:
        #     await engine_api.worker.my_msg('Error in posting API data ' + exchange, False, False)
        #     return str(e)
    
    # # I need to put something in here that updates the tele bot
    # if engine_api.worker.tele_bot:
    #     try:
    #         data['tele_token'] = engine_api.worker.tele_bot.token
    #         data['tele_chat'] = engine_api.worker.tele_bot.chat_id
    #     except Exception as e:
    #         data['tele_token'] = ''
    #         data['tele_chat'] = ''
    # else:
    #     data['tele_token'] = ''
    #     data['tele_chat'] = ''

    return jsonify(data)


@engine_api.route(pfx + '/msgs', methods=['GET'])
async def get_msgs():
    msg = []
    while not engine_api.worker.msg_q.empty():
        msg.append(engine_api.worker.msg_q.get())
    return jsonify(msg)
    

#make message

#reload api keys from file


#     elif msg[0] == 'check_key':
#     # This should just take a key and then pass back if it is valid or not
#         asyncio.ensure_future(self.check_cc_key(msg[1], [msg[2], msg[3]]))
#
#
# elif msg[0] == 'syms':
# # await self.add_ai_coin(msg[1], msg[2], msg[3], msg[4], msg[5])
# ex = self.exchange_selector(msg[1])
# syms = [t.replace('-', '/') for t in ex.markets if ex.markets[t]['active']]
# syms = [x for x in syms if '.' not in x]
# syms = [x for x in syms if x.count('/') == 1]
# print(syms)
# await self.out_q.coro_put(['syms', syms, msg[2]])
#
# elif msg[0] == 'bot_active':
# self.bot_active = msg[1]
#
# elif msg[0] == 'basic_active':
# self.basic_active = msg[1]
#
# elif msg[0] == 'verify':
# try:
#     ex = self.exchange_selector(msg[1])
#     await self.a_debit_exchange(ex, 1)
#     await ex.load_markets(reload=True)
#     if msg[2] in ex.markets:
#         info = ex.market(msg[2])
#         await self.out_q.coro_put(['verified', msg[1], msg[2],
#                                    str(info['limits']['amount']['min']),
#                                    str(info['limits']['cost']['min']), True])
#     else:
#         await self.out_q.coro_put(['verified', msg[1], msg[2], 'Coin/Pair Not Listed',
#                                    'Coin/Pair Not Listed', True])
# except Exception as e:
#     await self.out_q.coro_put(['verified', msg[1], msg[2], 'Error',
#                                'Error', True])
#
# elif msg[0] == 'manual_buy':
# # 'manual_bought': #cp, amount
# ex = self.exchange_selector(msg[1])
# try:
#     amount = ex.amount_to_precision(msg[2], msg[3])
#     pr, amount = await self.buy_sell_now(ex, msg[2], amount, True, True)
#     if pr == 'No Bal':
#         print('No Balance to trade sell')
#         msg = 'Not enough balance for Manual Trade of: ' + msg[2]
#         await self.out_q.coro_put(['msg', msg])
#         await self.out_q.coro_put(['manual_bought', msg[2], '0'])
#     else:
#         await self.out_q.coro_put(['manual_bought', msg[2], amount])
# except Exception as e:
#     msg = 'Trading Tab Error: ' + e
#     await self.out_q.coro_put(['msg', msg])
#
# elif msg[0] == 'manual_sell':
# try:
#     # 'manual_bought': #cp, amount
#     ex = self.exchange_selector(msg[1])
#     amount = ex.amount_to_precision(msg[2], msg[3])
#     pr, amount = await self.buy_sell_now(ex, msg[2], amount, False, True)
#     if pr == 'No Bal':
#         print('No Balance to trade sell')
#         msg = 'Not enough balance for Manual Trade of: ' + msg[2]
#         await self.out_q.coro_put(['msg', msg])
#         await self.out_q.coro_put(['manual_bought', msg[2], '0'])
#     else:
#         await self.out_q.coro_put(['manual_sold', msg[2], amount])
# except Exception as e:
#     msg = 'Trading Tab Error: ' + e
#     await self.out_q.coro_put(['msg', msg])
#
# elif msg[0] == 'loop_limit':  # ['loop_limit', ex, cp, 'buy', amount, buy_price, leverage, id]
# try:
#     # 'manual_bought': #cp, amount
#     ex = self.exchange_selector(msg[1])
#     # amount = ex.amount_to_precision(msg[2], msg[4])
#     id = await self.limit_buy_sell_now(msg[1], msg[2], msg[3], msg[4], msg[5], msg[6])
#
#     if id:
#         await self.out_q.coro_put(['loop_limit_id', msg[3], id, msg[-1]])
# except Exception as e:
#     msg = 'Trading Tab Loop Limit Error: ' + e
#     await self.out_q.coro_put(['msg', msg])
#
# elif msg[0] == 'loop_limit_check':  # ['loop_limit_check', ex, cp, trade.buy_trade_id]
# try:
#     # 'manual_bought': #cp, amount
#     ex = self.exchange_selector(msg[1])
#     await self.a_debit_exchange(ex, 1)
#     print(msg)
#     cp = msg[2].replace('/', '')
#     data = await ex.fetch_order(msg[3], cp)
#     if data:
#         # print('status update', data)
#         await self.out_q.coro_put(['loop_limit_status', data['status'], msg[3]])
# except Exception as e:
#     msg = 'Trading Tab Loop Status Check Error: ' + str(e)
#     await self.out_q.coro_put(['msg', msg])
#
#
# async def my_fetch_trades(self, exchange, market):
#     ex = self.exchange_selector(exchange)
#     if exchange == 'Binance' or exchange == 'Binance US':
#         await self.a_debit_exchange(ex, 10)
#     else:
#         await self.a_debit_exchange(ex, 1)
#     await self.out_q.coro_put(['getting_history', market])
#     return [market, await ex.fetch_my_trades(market)]