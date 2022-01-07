from quart import Quart, render_template, websocket
from quart import request, jsonify
import aiohttp
import asyncio
import time


engine_api = Quart(__name__)
pfx = '/cc/api/v1'


@engine_api.route(pfx + '/ping', methods=['GET'])
def home():
    return 'pong'


@engine_api.route(pfx + '/getohlc', methods=['GET'])
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


@engine_api.route(pfx + '/bbdata', methods=['POST'])
async def get_bb_data():
    form = await request.form
    ex = engine_api.worker.exchange_selector(form['ex'])
    return ex.prices


@engine_api.route(pfx + '/abdata', methods=['POST'])
async def get_ab_data():
    form = await request.form
    ex = engine_api.worker.exchange_selector(form['ex'])
    return ex.prices


async def activate_check_key(session, url, id):
    t = time.time()
    async with session.get(url) as resp:
        msg = await resp.json()
        print('call took', time.time()-t)
        return [msg, id]


@engine_api.route(pfx + '/cckey', methods=['POST'])
async def get_cc_key_data():
    form = await request.form
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            product_id = ['3863', '3862', '3861', '3860', '3859', '3827']
            tasks = []
            for p_id in product_id:
                endpoint = 'https://craft-crypto.com/wc/v3/?wc-api=wc-am-api'
                first = '&wc_am_action=' + form['action']
                second = '&api_key=' + form['key']
                third = '&product_id=' + p_id
                forth = '&instance=' + form['instance']
                woo_key = '&consumer_key=123&consumer_secret=abc'

                url = endpoint + first + second + third + forth + woo_key
                print(url)
                tasks.append(asyncio.ensure_future(activate_check_key(session, url, p_id)))
            data = await asyncio.gather(*tasks)


    except Exception as e:
        print('cc api error', e)

    return jsonify(data)


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