from quart import Quart, render_template, websocket
from quart import request, jsonify
import aiohttp
import asyncio
import time
import json
import ast
from functools import partial, wraps
from CraftCrypto_Helpers.Helpers import get_store

engine_api = Quart(__name__)
pfx = '/cc/api/v1'


connected_websockets = set()


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global connected_websockets
        queue = asyncio.Queue()
        connected_websockets.add(queue)
        try:
            return await func(queue, *args, **kwargs)
        finally:
            connected_websockets.remove(queue)
    return wrapper


async def broadcast(message):
    for queue in connected_websockets:
        await queue.put(message)


@engine_api.websocket(pfx + '/ws')
@collect_websocket
async def ws_v2(queue):
    while True:
        while not queue.empty():
            data = await queue.get()
            await websocket.send_json(data)
        try:
            data = await asyncio.wait_for(websocket.receive(), .25)
            data = json.loads(data)
            # await websocket.send_json(data)
            send_data = None
            if data['action'] == 'bb_data':
                send_data = await get_bb_data(True)
            elif data['action'] == 'bb_active':
                await set_bb_active()
                data['action'] = 'bb_data'
                send_data = await get_bb_data(True)
            elif data['action'] == 'bb_now':
                engine_api.worker.bb_active = True
                await engine_api.worker.check_bot_cards(engine_api.worker.bb_strat.candle)
                data['action'] = 'bb_data'
                send_data = await get_bb_data(True)
            elif data['action'] == 'ab_data':
                send_data = await get_ab_data(True)
            elif data['action'] == 'api_keys':
                send_data = await get_api_data(True)
            elif data['action'] == 'msgs':
                send_data = await get_msgs(True)

            elif data['action'] == 'send_msg':
                if engine_api.worker.tele_bot:
                    if engine_api.worker.tele_bot.chat_id:
                        try:
                            await engine_api.worker.tele_bot.send_message(chat_id=engine_api.worker.tele_bot.chat_id,
                                                                          text=data['msg'])
                        except Exception as e:
                            msg = 'WS Telegram posting msg Error: ' + str(e)
                            await engine_api.worker.my_msg(msg, to_broad=True)
            elif data['action'] == 'get_strats':
                store = get_store('BasicStrats')
                send_data = {}
                if store:
                    send_data['store'] = store
                else:
                    send_data['store'] = {'title': 'No Strategies Found',
                                          'description': 'Restart Trade Engine to remake.'}

            elif data['action'] == 'edit_strat':
                ex = data['sent_data']['exchange']
                index = data['sent_data']['strat_index']
                pair = data['sent_data']['pair']
                await engine_api.worker.update_strat(ex, index, pair, True)
                engine_api.worker.bb_trade_limit = data['sent_data']['limit']
                engine_api.worker.bb_strat.pair_minmult = data['sent_data']['pair_minmult']
                data['action'] = 'bb_data'
                send_data = await get_bb_data(True)

            elif data['action'] == 'delete_card':
                i = 0
                for card in engine_api.worker.bb_cards:
                    if card.my_id == data['my_id']:
                        del engine_api.worker.bb_cards[i]
                        break
                    i += 1
                i = 0
                for card in engine_api.worker.ab_cards:
                    if card['my_id'] == data['my_id']:
                        del engine_api.worker.ab_cards[card]
                        break
                    i += 1
                data['action'] = 'bb_data'
                send_data = await get_bb_data(True)

            elif data['action'] == 'buy_card':
                for card in engine_api.worker.bb_cards:
                    if card.my_id == data['my_id']:
                        card.buy_now = True
                        break
                for card in engine_api.worker.ab_cards:
                    if card.my_id == data['my_id']:
                        card.buy_now = True
                        break
                data['action'] = 'bb_data'
                send_data = await get_bb_data(True)

            elif data['action'] == 'toggle_card_active':
                for card in engine_api.worker.bb_cards:
                    if card.my_id == data['my_id']:
                        card.active = not card.active
                        break
                for card in engine_api.worker.ab_cards:
                    if card.my_id == data['my_id']:
                        card.active = not card.active
                        break
                data['action'] == 'bb_data'
                send_data = await get_bb_data(True)

            elif data['action'] == 'set_api_keys':
                # keys = ast.literal_eval(data['keys'])
                keys = data['keys']
                for key in keys:
                    ex = engine_api.worker.exchange_selector(key)
                    # try:
                    print(key, keys[key])
                    ex.apiKey = keys[key]['key']
                    ex.secret = keys[key]['secret']
                    if key == 'Coinbase Pro':
                        ex.password = keys[key]['password']

                await engine_api.worker.test_apis()

            elif data['action'] == 'set_tele_token':
                # keys = ast.literal_eval(data['keys'])
                if not engine_api.worker.tele_bot:
                    await engine_api.worker.init_tele_bot(data['token'], 'test_chat_id')
                else:
                    await engine_api.worker.init_tele_bot(data['token'], engine_api.worker.tele_bot.chat_id)

            elif data['action'] == 'set_tele_chat':
                # keys = ast.literal_eval(data['keys'])
                if engine_api.worker.tele_bot:
                    await engine_api.worker.init_tele_bot(engine_api.worker.tele_bot.token, data['chat_id'])


            if send_data:
                try:
                    await websocket.send_json(data | send_data)
                except Exception as e:
                    print(e)
        except asyncio.exceptions.TimeoutError:
            pass
        # except Exception as e:
        #     print('back to checking....', e, e.__class__)
        #     print(data, send_data)


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


@engine_api.route(pfx + '/all_prices', methods=['GET'])
async def get_all_prices():
    data = {}
    for exchange in engine_api.worker.exchanges:
        ex = engine_api.worker.exchange_selector(exchange)
        data[exchange] = ex.prices
    return data


@engine_api.route(pfx + '/bb_data', methods=['GET'])
async def get_bb_data(*args):
    data = {}
    data['strat'] = engine_api.worker.bb_strat.to_dict()
    data['cards'] = engine_api.worker.bb_cards
    data['trades'] = engine_api.worker.bb_trades
    data['trade_limit'] = engine_api.worker.bb_trade_limit
    data['active'] = engine_api.worker.bb_active
    if args:
        return data
    return jsonify(data)


@engine_api.route(pfx + '/bb_active', methods=['GET'])
async def set_bb_active():
    engine_api.worker.bb_active = not engine_api.worker.bb_active
    print('flipped')
    return 'flipped'


@engine_api.route(pfx + '/ab_data', methods=['GET'])
async def get_ab_data(*args):
    data = {}
    data['cards'] = engine_api.worker.ab_cards
    data['trades'] = engine_api.worker.ab_trades
    data['trade_limit'] = engine_api.worker.ab_trade_limit
    data['active'] = engine_api.worker.ab_active
    if args:
        return data
    return jsonify(data)


@engine_api.route(pfx + '/api_keys', methods=['GET'])
async def get_api_data(*args):
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
        
    if args:
        return data
    return jsonify(data)


@engine_api.route(pfx + '/set_api_keys', methods=['POST'])
async def set_api_data():
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
async def get_msgs(*args):
    msg = []
    while not engine_api.worker.msg_q.empty():
        msg.append(engine_api.worker.msg_q.get())
    if args:
        return {'msg': msg}
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