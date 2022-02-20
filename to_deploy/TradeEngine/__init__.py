# -----------------------------------------------------------------------------
# Copyright (c) 2022 Tom McLaughlin @ Craft-Crypto, LLC
#
# Other libraries used in the project:
#
# Copyright (c) 2015-2019 Digital Sapphire - PyUpdater
# Copyright (c) 2017 Igor Kroitor - ccxt
# Copyright (c) 2018 P G Jones - hypercorn
# Copyright (c) 2017 P G Jones - quart
# Copyright (c) 2007 vxgmichel - aioconsole
# Copyright (c) 2013-2021 Aymeric Augustin and contributors - websockets
# Copyright (c) 2017-2018 Alex Root Junior - aiogram
# Copyright (c) 2022 Craft-Crypto, LLC - Craft-Crypto Helpers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------

import asyncio
import traceback
import time
import queue
import getpass
from aioconsole import ainput

from CraftCrypto_Helpers.BaseRecord import BaseRecord
from CraftCrypto_Helpers.Helpers import is_float, save_store, copy_prec, get_store
from TradeEngine.tele_api_calls import TeleBot
from TradeEngine.trade_api_calls import broadcast
import CraftCrypto_Helpers
CraftCrypto_Helpers.Helpers.dir_path = '/Users/' + getpass.getuser() + '/Documents/Craft-Crypto/TradeEngine/'


class TradeEngine(object):
    from .ex_websockets import websocket_bin, websocket_binUS, websocket_bm
    from .ex_websockets import websocket_cbp, websocket_ftx, websocket_kraken
    from .bot_startup import initialize, test_apis, init_tele_bot
    from .input_management import manage_input
    from .bot_trading import check_bot_cards, do_check_bot_cards, make_bot_buy, quick_trade
    from .bot_trading import add_trade_card, update_card_trade_data, check_trade_sells, do_check_trade_sells

    def __init__(self, **kwargs):
        # Setup Server
        self.trade_server = None
        self.ws_q = asyncio.queues.Queue()
        self.action_q = asyncio.queues.Queue()

        # Setup Telegram Bot
        # self.tele_token = None
        # self.tele_chat = None
        self.tele_bot = None #TradeEngine.tele_bot  # .__init__(token='123')
        self.tele_dp = None #TradeEngine.dp

        # Setup Exchanges
        self.a_binance = None
        self.a_binanceUS = None
        self.a_bitmex = None
        self.a_cbp = None
        self.a_kraken = None
        self.a_ftx = None

        # Setup Basic Bot
        self.bb_strat = BaseRecord()
        self.bb_strat.pair_minmult = '2'
        self.bb_strat.title = 'RSI DCA Minute Trading'
        self.bb_cards = []
        self.bb_trades = []
        self.bb_active_trades = 0
        self.bb_trade_limit = '7'
        self.bb_active = False
        self.bb_sells_lock = False

        # Setup Advanced Bot
        self.ab_cards = []
        self.ab_trades = []
        self.ab_active_trades = 0
        self.ab_trade_limit = '7'
        self.ab_active = False
        self.ab_sells_lock = False

        # Other Setup
        self.my_id = time.time()
        self.verbose = False
        self.sched = None
        self.sell_mod = 1
        self.loop = None
        self.running = False
        self.log_msgs = []
        self.msg_q = queue.Queue()
        self.tele_bot = None
        self.q = asyncio.queues.Queue()
        self.looking = False  # Input Management

    def run(self):
        # print('Im alive')
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.running = True
        while self.running:
            try:
                self.loop.run_until_complete(self.async_worker())
                self.loop.run_forever()
            except Exception as e:
                print('*********** error', traceback.format_exc(), '*************')
                # msg = str(sys.exc_info()[0]) + ' ' + str(sys.exc_info()[1])
                # self.out_q.put(['error', msg])
                self.running = False
        print('subprocess is done')

    async def async_worker(self):
        t = time.time()
        try:
            await self.initialize()
        except Exception as e:
            self.my_msg('Error in Initialization: ' + str(e))

        while self.running:
            if self.q.empty():
                if not self.looking:
                    asyncio.ensure_future(self.get_user_input())
                await asyncio.sleep(2)
            else:
                msg = await self.q.get()
                await self.manage_input(msg)

    async def get_user_input(self):
        # I need to control when I ask for something for it to look nice
        self.looking = True
        content = await ainput(">")
        await self.q.put(content)
        self.looking = False

    async def my_msg(self, text, verbose=False, to_tele=False, to_broad=False, *args):
        if verbose and self.verbose:
            print(text)

        if not verbose:
            print(text)

        if to_broad:
            await broadcast({'action': 'msgs', 'msg': text})

        if to_tele and self.tele_bot:
            if self.tele_bot.chat_id:
                try:
                    await self.tele_bot.send_message(chat_id=self.tele_bot.chat_id, text=text)
                except Exception as e:
                    msg = 'Telegram posting msg Error: ' + str(e)
                    await self.my_msg(msg, to_broad=True)

        tim = time.strftime('%I:%M:%S %p %m/%d/%y')
        self.log_msgs.append((tim + ': ' + text))

    async def set_bb_strat(self):
        await self.my_msg('*******')
        await self.my_msg('Select an Exchange for the Bot:')
        await self.my_msg('1 - Binance')
        await self.my_msg('2 - Binance US')
        await self.my_msg('3 - BitMEX')
        await self.my_msg('4 - Coinbase Pro')
        await self.my_msg('5 - FTX')
        await self.my_msg('6 - Kraken')
        msg = await ainput(">")
        ex = ''
        if msg == '1':
            ex = 'Binance'
        elif msg == '2':
            ex = 'Binance US'
        elif msg == '3':
            ex = 'BitMEX'
        elif msg == '4':
            ex = 'Coinbase Pro'
        elif msg == '5':
            ex = 'FTX'
        elif msg == '6':
            ex = 'Kraken'

        await self.my_msg('Select a Strategy for the Bot:')
        store = get_store('BasicStrats')
        if store:
            for strat_num in store:
                await self.my_msg(strat_num + ' - ' + store[strat_num]['title'])
                await self.my_msg('-- ' + store[strat_num]['description'])
        else:
            await self.my_msg('Error with Strategy Store. Please restart to remake:')

        strat_index = await ainput(">")
        # name = ''
        # if msg == '1':
        #     name = 'RSI DCA Minute Trading'
        # elif msg == '2':
        #     name = 'MACD Stoch Long Haul'
        # elif msg == '3':
        #     name = 'Cross and Pop'

        pair = ''
        await self.my_msg('Select a Trading Pair:')
        msg = await ainput(">")
        pair = msg.upper()

        await self.my_msg('Filter Out Stable Coins? (Y/n):')
        msg = await ainput(">")
        if msg.lower() == 'n':
            filter_stable = False
        else:
            filter_stable = True

        worked = await self.update_strat(ex, strat_index, pair, filter_stable)

        if worked:
            # Need to filter out stable coin/stable coin
            await self.my_msg('Basic Bot will trade the following:')
            await self.my_msg(self.bb_strat.coin)
            await self.q.put('bb status')
        # enter a way to remove ones the user doesn't want

        await self.my_msg('Enter a Pair Min Multiplier:')
        msg = await ainput(">")
        self.bb_strat.pair_minmult = msg
        for card in self.bb_cards:
            card.pair_minmult = self.bb_strat.pair_minmult

        await self.my_msg('Enter Active Trade Limit:')
        msg = await ainput(">")
        if is_float(msg):
            self.bb_trade_limit = msg

        await self.save()

    async def update_strat(self, exchange, strat_index, pair, filter_stable, *args):
        if not exchange and strat_index and pair:
            msg = 'Invalid Strategy Settings'
            await self.my_msg(msg, to_tele=True, to_broad=True)
            return False

        self.bb_strat = BaseRecord()
        strat = self.bb_strat
        store = get_store('BasicStrats')
        if store:
            strat.set_record(store[strat_index])
            strat.strat_index = strat_index
        else:
            await self.my_msg('Another Error with Strategy Store. Please restart to remake:')

        strat.pair = pair
        strat.exchange = exchange

        # Getting trading pairs for basic bot
        ex = self.exchange_selector(self.bb_strat.exchange)
        await ex.load_markets()
        self.bb_strat.coin = ''
        stable_coins = ['USDT', 'USDC', 'BUSD', 'UST', 'DAI', 'TUSD', 'USDP', 'USDN', 'FEI', 'GUSD',
                        'FRAX', 'LUSD', 'HUSD', 'OUSD']
        for coin in ex.markets:
            if coin.split('/')[1] == self.bb_strat.pair:
                if filter_stable and coin.split('/')[0] in stable_coins:
                    pass
                else:
                    if ex.market(coin)['active']:
                        self.bb_strat.coin += coin.split('/')[0] + ', '

        if self.bb_strat.coin:
            self.bb_strat.coin = self.bb_strat.coin[:-2]

        # Resetting and making coin cards
        self.bb_cards = []
        for coin in self.bb_strat.coin.split(','):
            coin = coin.strip()
            rec = BaseRecord()
            rec.set_record(self.bb_strat.to_dict())
            rec.coin = coin
            rec.kind = 'Basic Bot'
            rec.active = True
            rec.title = ''
            rec.description = ''
            rec.my_id = str(time.time())

            ex_prec = ex.price_to_precision(coin + '/' + pair, '.11111111111')
            extended_prec = ex_prec + '11'
            rec.precision = extended_prec
            if not ex_prec:
                rec.precision = '.11111111'
            self.bb_cards.append(rec)

        await self.gather_update_bals()
        await self.sync_trades_to_cards()

        return True

    async def add_ab_card(self, coins, base, trigs):
        # print('Engine Getting', coins)
        # cont = self.addition_dialog.content_cls
        # trig = self.addition_dialog.content_cls.ids.trig
        # pair = cont.pair
        # candle = cont.candle
        exchange = base['exchange']
        ex = self.exchange_selector(exchange)
        pair = base['pair']

        if '*' in coins:
            coins = [cp.split('/')[0] for cp in ex.markets if pair in cp and ex.market(cp)['active']]
            # print('Trading Engine Coins')

        for coin in coins:
            found_rec = False
            for rec in self.ab_cards:
                if rec.coin == coin and rec.pair == pair:
                    # print(rec.my_id)
                    my_id = rec.my_id
                    rec.set_record(trigs)
                    rec.set_record(base)
                    rec.my_id = my_id
                    # print(rec.my_id)
                    # found_rec = True
                    # print('FOUND rec', rec.coin, rec.pair)
                    # rec.reset('now_price', 'coin', 'pair', 'coin_bal', 'pair_bal', 'sim_gain', 'sim_trades', 'sim_date',
                    #          'per_gain', 'num_trades', 'last_price', 'last_buy_price', 'trade_vol', 'trade_price',
                    #          'candle', 'prec', 'ready_sell')
                    # rec.set_record(cont.get_base())
                    # rec.set_record(trig.get_trigs())
                    # rec.my_id = my_id
                    rec.coin = coin
                    rec.pair = pair
                    rec.ready_sell = False
                    rec.active = True
                    # self.update_data(self.ids.rv, rec.get_all())
                    found_rec = True
                    await broadcast({'action': 'update_cc', 'card': rec.to_dict()})
                    break

            if not found_rec:
                rec = BaseRecord()
                #set dicts
                # print('resetting dict')
                rec.set_record(trigs)
                rec.set_record(base)
                rec.kind = 'Advanced Bot'
                rec.coin = coin
                rec.my_id = await self.get_my_id()
                rec.ready_sell = False
                rec.active = True
                self.ab_cards.append(rec)
                # print(rec)
                # print(rec.to_dict())
                await broadcast({'action': 'update_cc', 'card': rec.to_dict()})
        await self.sync_trades_to_cards()

    async def set_api_keys(self):
        await self.my_msg('*******')
        await self.my_msg('Select an Exchange to add keys:')
        await self.my_msg('1 - Binance')
        await self.my_msg('2 - Binance US')
        await self.my_msg('3 - BitMEX')
        await self.my_msg('4 - Coinbase Pro')
        await self.my_msg('5 - FTX')
        await self.my_msg('6 - Kraken')
        msg = await ainput(">")
        ex = ''
        if msg == '1':
            ex = 'Binance'
        elif msg == '2':
            ex = 'Binance US'
        elif msg == '3':
            ex = 'BitMEX'
        elif msg == '4':
            ex = 'Coinbase Pro'
        elif msg == '5':
            ex = 'FTX'
        elif msg == '6':
            ex = 'Kraken'

        if ex:
            exchange = self.exchange_selector(ex)
            await self.my_msg('Enter ' + ex + ' API Key:')
            msg = await ainput(">")
            exchange.apiKey = msg.strip()
            await self.my_msg('Enter ' + ex + ' API Secret:')
            msg = await ainput(">")
            exchange.secret = msg.strip()
            if ex == 'Coinbase Pro':
                await self.my_msg('Enter ' + ex + ' API Password:')
                msg = await ainput(">")
                exchange.password = msg.strip()
            await self.test_apis(str(exchange))

        await self.save()

    def exchange_selector(self, ex):
        if ex == 'Binance':
            return self.a_binance
        elif ex == 'Binance US':
            return self.a_binanceUS
        elif ex == 'BitMEX':
            return self.a_bitmex
        elif ex == 'Coinbase Pro':
            return self.a_cbp
        elif ex == 'Kraken':
            return self.a_kraken
        elif ex == 'FTX':
            return self.a_ftx
        else:
            return None, None

    async def a_debit_exchange(self, exchange, deduct):
        if exchange.rate_limit < deduct:
            await asyncio.sleep(1)
            await self.a_debit_exchange(exchange, deduct)
        else:
            exchange.rate_limit -= deduct

    async def refresh_api(self):
        while self.running:
            await asyncio.sleep(1.05)
            self.a_binance.rate_limit = 20
            self.a_binanceUS.rate_limit = 20
            self.a_bitmex.rate_limit = 2
            self.a_cbp.rate_limit = 3
            self.a_kraken.rate_limit = 1
            self.a_ftx.rate_limit = 29

    async def collect_sells(self, basic, to_tcp=False, *args):
        per = 0
        num = 0
        if basic:
            trades = self.bb_trades
        else:
            trades = self.ab_trades

        if trades:
            for tc in trades:
                if tc.sold:
                    if is_float(tc.gl_per):
                        per += float(tc.gl_per)
                    num += 1
            # print(num, per)
            msg = 'Collected ' + str(num) + ' trades for a Gain/Loss of ' + str(copy_prec(per, .11)) + '%'
        else:
            msg = 'No Trades to Collect'

        await self.my_msg(msg, to_tele=True)

        if to_tcp:
            await broadcast({'action': 'collected', 'msg': msg})

        if basic:
            self.bb_trades = [tc for tc in trades if not tc.sold]
        else:
            self.ab_trades = [tc for tc in trades if not tc.sold]

    async def make_positive_sells(self, basic, *args):
        if basic:
            trades = self.bb_trades
        else:
            trades = self.ab_trades

        for tc in trades:
            if not tc.sold and tc.active and float(tc.gl_per) > 0:
                tc.sell_now = True

    async def update_bals(self, exchange):
        t = time.time()
        if str(exchange) == 'Binance' or str(exchange) == 'Binance US':
            await self.a_debit_exchange(exchange, 5)
        else:
            await self.a_debit_exchange(exchange, 1)
        exchange.balance = {}
        try:
            if exchange.apiKey:
                bal = await exchange.fetch_balance({'recvWindow': 55000})
                if str(exchange) == 'Binance' or str(exchange) == 'Binance US':
                    for coin in bal:
                        try:
                            if is_float(bal[coin]['free']):
                                exchange.balance[coin] = bal[coin]['free']
                        except:
                            continue
                elif str(exchange) in ['Coinbase Pro', 'FTX']:
                    for coin in bal['free']:
                        try:
                            if is_float(bal['free'][coin]):
                                exchange.balance[coin] = bal['free'][coin]
                        except:
                            continue
                elif str(exchange) == 'Kraken':
                    for coin in bal['total']:
                        try:
                            if is_float(bal['total'][coin]):
                                exchange.balance[coin] = bal['total'][coin]
                        except:
                            continue
            # await exchange.close()
            # print(str(exchange), 'balance took', time.time() - t)
        except Exception as e:
            exchange.api_ok = False
            # print('Error: collecting bals', str(exchange), e)
            if '502 Bad Gateway' in str(e):
                msg = 'Error with ' + str(exchange) + ' Balance: Bad Gateway... will try again.'
            else:
                msg = 'Error with ' + str(exchange) + ' Balance: ' + str(e)
            await self.my_msg(msg, to_broad=True, to_tele=True)

    async def gather_update_bals(self, *args):
        tasks = []
        my_exchanges = []
        if args:
            my_exchanges = [args[0]]
            exchange = self.exchange_selector(args[0])
            await self.update_bals(exchange)
        else:
            my_exchanges = self.exchanges
            for ex in my_exchanges:
                exchange = self.exchange_selector(ex)
                if exchange.apiKey and exchange.secret:
                    tasks.append(asyncio.ensure_future(self.update_bals(exchange)))
            data = await asyncio.gather(*tasks)

        for exchange in my_exchanges:
            ex = self.exchange_selector(exchange)
            if ex.apiKey and ex.secret and ex.prices:
                # print(str(exchange), exchange.balance)
                # Now go through and figure out usd and btc balances

                btc_bal = 0
                usd_bal = 0
                oops = None
                for coin in ex.balance:
                    cp = coin + 'BTC'
                    pc = 'BTC' + coin
                    cusd = coin + 'USD'
                    cusdt = coin + 'USDT'
                    oops = ''
                    # check for all converted to BTC
                    if cp in ex.prices.keys():
                        # find amount BTC
                        btc_bal += float(ex.balance[coin]) * float(ex.prices[cp])
                        # print(cp, exchange.prices[cp], btc_bal)
                    elif pc in ex.prices.keys():
                        btc_bal += float(ex.balance[coin]) / float(ex.prices[pc])
                        # print(pc, exchange.prices[pc], btc_bal)

                    # search for USDT first as USD is in USDT
                    elif cusdt in ex.prices.keys():
                        usd_val = float(ex.balance[coin]) * float(ex.prices[cusdt])
                        btc_bal += usd_val / float(ex.prices['BTCUSDT'])
                        # print(cusdt, exchange.prices[cusdt], btc_bal)
                    elif cusd in ex.prices.keys():
                        usd_val = float(ex.balance[coin]) * float(ex.prices[cusd])
                        btc_bal += usd_val / float(ex.prices['BTCUSD'])
                        # print(cusd, exchange.prices[cusd], btc_bal)

                    else:
                        # print('oops', coin)
                        oops += coin
                # if oops:
                #     print('couldnt find ', oops)

                # if 'BTC' in exchange.balance:
                #     btc_bal += float(exchange.balance['BTC'])
                try:
                    if str(ex) == 'Binance':
                        usd_bal = btc_bal * float(ex.prices['BTCUSDT'])
                    else:
                        usd_bal = btc_bal * float(ex.prices['BTCUSD'])
                    btc_bal = copy_prec(btc_bal, '.11111111')
                    usd_bal = copy_prec(usd_bal, '.11')

                    ex.balance['btc_val'] = btc_bal
                    ex.balance['usd_val'] = usd_bal
                    ex.balance['update_time'] = time.strftime('%I:%M:%S %p %m/%d/%y')
                    await broadcast({'action': 'get_balance', 'exchange': str(ex), 'balance': ex.balance})

                except Exception as e:
                    msg = 'Error in ' + str(ex) + ' balance update: ' + str(e)
                    await self.my_msg(msg, to_broad=True, to_tele=True)

                # Now update all the cards

                # Update Coin Cards
                try:
                    for card in self.bb_cards + self.ab_cards:
                        if card.exchange == exchange:
                            if card.coin in ex.balance:
                                card.coin_bal = str(ex.balance[card.coin])
                            else:
                                card.coin_bal = '0'
                            if card.pair in ex.balance:
                                card.pair_bal = str(ex.balance[card.pair])
                            else:
                                card.pair_bal = '0'
                except Exception as e:
                    print(e)
                    await self.my_msg('Error in updating card balances', to_broad=True, to_tele=True)

    async def collect_balance(self):
        await self.gather_update_bals()
        await self.my_msg('*******', to_tele=True)
        if len(self.a_binance.balance) > 3:
            msg = 'Binance Balance:'
            for bal in self.a_binance.balance:
                msg += '\n' + bal + ': ' + str(self.a_binance.balance[bal])
            await self.my_msg(msg, to_tele=True)
        if len(self.a_binanceUS.balance) > 3:
            msg = 'Binance US Balance:'
            for bal in self.a_binanceUS.balance:
                msg += '\n' + bal + ': ' + str(self.a_binanceUS.balance[bal])
            await self.my_msg(msg, to_tele=True)
        if len(self.a_cbp.balance) > 3:
            msg = 'Coinbase Pro Balance:'
            for bal in self.a_cbp.balance:
                msg += '\n' + bal + ': ' + str(self.a_cbp.balance[bal])
            await self.my_msg(msg, to_tele=True)
        if len(self.a_ftx.balance) > 3:
            msg = 'FTX Balance:'
            for bal in self.a_ftx.balance:
                msg += '\n' + bal + ': ' + str(self.a_ftx.balance[bal])
            await self.my_msg(msg, to_tele=True)
        if len(self.a_kraken.balance) > 3:
            msg = 'Kraken Balance:'
            for bal in self.a_kraken.balance:
                msg += '\n' + bal + ': ' + str(self.a_kraken.balance[bal])
            await self.my_msg(msg, to_tele=True)

    async def check_prices_sells(self):
        while self.running:
            await asyncio.sleep(1)
            await self.update_prices()
            await self.check_trade_sells()

    async def update_prices(self):
        try:
            for tc in self.bb_trades + self.ab_trades:
                ex = self.exchange_selector(tc.exchange)
                if not tc.sold:
                    tp = tc.coin + tc.pair
                    # print('basic price', tp)
                    if tp in ex.prices:
                        # print('updating Basic', tp)
                        price = float(ex.prices[tp])
                        if not str(tc.now_price) == str(price):
                            tc.last_update = time.strftime('%I:%M:%S %p %m/%d/%y')
                            if 'e' in str(price):
                                tc.now_price = '{:.9f}'.format(price).rstrip('0')
                            else:
                                tc.now_price = str(price)

                            try:
                                # we should probably also add in buying and selling now too
                                gl = float(tc.now_price) / float(tc.buy_price) * 100 - 100
                                tc.gl_per = str(round(gl, 2))
                                # This should probably be sent to everyone
                                await broadcast({'action': 'update_tc', 'card': tc.to_dict()})
                                # self.ws_q.put({'action': 'update_tc', 'tc': tc.to_dict()})

                            except Exception as e:
                                msg = 'Gain/Loss Error: ' + str(e)
                                await self.my_msg(msg, verbose=True, to_broad=True)

        except Exception as e:
            msg = 'Socket Error: ' + str(e)
            await self.my_msg(msg, verbose=True, to_broad=True)
            time.sleep(2)

    async def async_get_ohlc(self, ex, cp, candle, candles_needed, *args):
        try:
            if args:
                await self.my_msg('Collecting Candles....', to_tele=True, to_broad=True)
            t = time.time()
            await self.a_debit_exchange(ex, 1)

            if str(ex) == 'Coinbase Pro':
                ohlc = await ex.fetch_ohlcv(cp, candle, limit=300)
            else:
                ohlc = await ex.fetch_ohlcv(cp, candle, limit=1000)
            if ohlc:
                first = ohlc[0][0]
                last = ohlc[-1][0]
                timediff = last - first
            else:
                msg = 'Error in collecting candles for: ' + cp + ' on ' + str(ex)
                await self.my_msg(msg, to_tele=True, to_broad=True)
                return None

            while len(ohlc) < int(candles_needed):
                # print('getting more ohlc', len(ohlc))
                new_ohlc = []
                await self.a_debit_exchange(ex, 1)
                if str(ex) == 'Coinbase Pro':
                    new_ohlc = await ex.fetch_ohlcv(cp, candle, since=(first - timediff), limit=300)
                    if len(new_ohlc) < 300:
                        break
                else:
                    new_ohlc = await ex.fetch_ohlcv(cp, candle, since=(first-timediff), limit=1000)
                    if len(new_ohlc) < 1000:
                        break
                if new_ohlc:
                    first = new_ohlc[0][0]
                    ohlc = new_ohlc + ohlc
                else:
                    break

            # print('time took', cp, time.time() - t)
            return ohlc

        except Exception as e:
            msg = 'Error in collecting candles for: ' + cp + ' on ' + str(ex) + ': ' + str(e)
            await self.my_msg(msg, to_tele=True, to_broad=True)
            return None

    async def buy_sell_now(self, ex, cp, amount, is_buy, reset, percent=False, my_id=None, *args):
        try:
            # ex = self.exchange_selector(exchange)
            if type(ex) == str:
                ex = self.exchange_selector(ex)
            await self.a_debit_exchange(ex, 1)
            price = float(ex.prices[cp.replace('/', '')])
            coin, pair = cp.split('/')
            if percent:
                # amount is percent of amount to sell
                if is_buy:
                    amount = float(ex.balance[pair]) / price * float(amount) / 100
                else:
                    amount = float(ex.balance[coin]) * float(amount) / 100

            # print('pre', cp, amount, buy)
            amount = float(amount)
            info = ex.market(cp)
            min_coin_amt = float(info['limits']['amount']['min'])
            min_cost_amt = float(info['limits']['cost']['min'])

            num_coin_on_cost = min_cost_amt / price
            while num_coin_on_cost > min_coin_amt:
                min_coin_amt += float(info['limits']['amount']['min'])
            # print('pre mins', min_coin_amt, num_coin_on_cost)

            if amount < min_coin_amt:
                amount = min_coin_amt

            amount = ex.amount_to_precision(cp, amount)
            # print('post amounts', amount, 'buy', buy)

            try:
                if is_buy:
                    ordr = await ex.create_market_buy_order(cp, amount)
                else:
                    ordr = await ex.create_market_sell_order(cp, amount)
            except Exception as e:
                if 'MIN_NOTIONAL' in str(e) or 'insufficient balance' in str(e) or '1013' in str(e):
                    # print(cp, buy, e)
                    ordr = await self.try_trade_all(ex, cp, is_buy)
                else:
                    ordr = None

            # print(ordr)
            if ordr:
                if is_float(ordr['average']):
                    pr = copy_prec(ordr['average'], '.11111111')
                elif is_float(ordr['price']):
                    pr = copy_prec(ordr['price'], '.11111111')
                else:
                    pr = str(ex.prices[cp.replace('/', '')])

                if is_float(ordr['filled']):
                    amount = float(ordr['filled'])
                    if is_buy:
                        msg = 'Bought ' + str(amount) + ' ' + coin + ' at ' + str(pr) + ' ' + cp
                    else:
                        msg = 'Sold ' + str(amount) + ' ' + coin + ' at ' + str(pr) + ' ' + cp
                else:
                    if is_buy:
                        msg = 'Buy order of ' + str(amount) + ' ' + coin + ' at ' + str(pr) + ' ' + cp + ' sent.'
                    else:
                        msg = 'Sell order of ' + str(amount) + ' ' + coin + ' at ' + str(pr) + ' ' + cp + ' sent.'

                if reset:
                    await self.my_msg(msg, to_tele=True, to_broad=True)
                    await self.gather_update_bals()
            else:
                pr = 'Error'
                amount = '0'

            if my_id:
                await broadcast({'action': 'relay_trade', 'my_id': my_id, 'trade_price': str(pr), 'is_buy': is_buy})

            return pr, amount

        except Exception as e:
            msg = 'Error in trading ' + cp + ': ' + str(e)
            await self.my_msg(msg, to_tele=True, to_broad=True)
            if my_id:
                await broadcast({'action': 'relay_trade', 'my_id': my_id, 'trade_price': 'Error', 'is_buy': is_buy})
            return None, '0'

    async def limit_buy_sell_now(self, exchange, cp, is_buy, is_stop, amount, price, leverage, my_id=None, *args):
        try:
            ex = self.exchange_selector(str(exchange))
            await self.a_debit_exchange(ex, 1)
            amount = ex.amount_to_precision(cp, amount)
            # print('post amounts', amount, 'buy', is_buy)
            # print('pre limit', cp, is_buy, amount, price)
            coin, pair = cp.split('/')
            if is_buy:
                side = 'buy'
            else:
                side = 'sell'

            params = {}
            if is_stop:
                params = {
                    'stopPrice': str(price),  # your stop price
                    'type': 'stopLimit',
                }
                if is_buy:
                    price = price * .995
                else:
                    price = price * 1.005

            try:
                print('trying to place', cp, is_buy, amount, price)
                ordr = await ex.create_order(cp, 'limit', side, amount, price, params)

            except Exception as e:
                if 'MIN_NOTIONAL' in str(e) or 'insufficient balance' in str(e) or '1013' in str(e):
                    # print('limit order', cp, is_buy, e)
                    ordr = None
                    msg = cp + ' Loop Limit Order Error: ' + str(e)
                    await self.my_msg(msg, to_tele=True, to_broad=True)

            # print(ordr)
            if ordr:
                trade_id = ordr['id']
                print('trade_id', trade_id)

                if is_buy:
                    msg = 'Placed Limit Buy of ' + str(amount) + ' ' + coin + ' at ' + str(price) + ' ' + cp
                else:
                    msg = 'Placed Limit Sell of ' + str(amount) + ' ' + coin + ' at ' + str(price) + ' ' + cp

                await self.my_msg(msg, to_tele=True, to_broad=True)
                await self.gather_update_bals(str(ex))
            else:
                trade_id = 'Error'

            # amount = float(amount)
            # info = ex.market(cp)
            # min_coin_amt = float(info['limits']['amount']['min'])
            # min_cost_amt = float(info['limits']['cost']['min'])
            # price = float(ex.prices[cp.replace('/', '')])
            # num_coin_on_cost = min_cost_amt / price
            # while num_coin_on_cost > min_coin_amt:
            #     min_coin_amt += float(info['limits']['amount']['min'])
            # print('pre mins', min_coin_amt, num_coin_on_cost)
            #
            # if amount < min_coin_amt:
            #     amount = min_coin_amt

            # sell_amt = float(self.binance.amount_to_precision(cp, amount * self.sell_mod))
            # ordr = ''
            # side = ''

            # test = await exchange.fetch_order('771546291', 'BTCUSD')
            # # test = await exchange.create_limit_order('BTCUSD', 'buy', .001, 20000)
            # # 'orderId': '771546291', 'orderListId': '-1', 'clientOrderId': 'x-R4BD3S8263ab0ceb969b9346430ff7'
            # # 771551442
            # print('limit order', test)
            # test = await exchange.cancel_order('771546291', 'BTCUSD')
            # print(test)
            # test = await exchange.cancel_order('771551442', 'BTCUSD')
            # print(test)

            if my_id:
                await broadcast({'action': 'relay_trade', 'my_id': my_id, 'trade_id': str(trade_id), 'is_buy': is_buy})


        except Exception as e:
            msg = 'Error in Loop trading ' + cp + ': ' + str(e)
            await self.my_msg(msg, to_tele=True, to_broad=True)
            trade_id = 'Error'
            if my_id:
                await broadcast({'action': 'relay_trade', 'my_id': my_id, 'trade_id': str(trade_id), 'is_buy': is_buy})

    async def try_trade_all(self, ex, cp, buy, *args):
        try:
            # ex = self.exchange_selector(exchange)
            await self.update_bals(ex)
            await self.a_debit_exchange(ex, 1)
            coin, pair = cp.split('/')
            try:
                coin_bal = ex.balance[coin]
                pair_bal = ex.balance[pair]
            except Exception as e:
                msg = 'Error in Trading ' + cp + ': No Balance Found.'
                await self.my_msg(msg, to_tele=True, to_broad=True)
                return None

            if buy:
                amount = pair_bal * .99 / float(ex.prices[cp.replace('/', '')])
                print(amount, pair_bal, ex.prices[cp.replace('/', '')])
                amount = ex.amount_to_precision(cp, amount)
                pair_bal = ex.amount_to_precision(cp, pair_bal * .99)

            else:
                amount = ex.amount_to_precision(cp, coin_bal * .99)

            print('last chance', buy, cp, amount, coin_bal)
            if buy:
                ordr = await ex.create_market_buy_order(cp, amount)
            else:
                ordr = await ex.create_market_sell_order(cp, amount)
            print(ordr)
            return ordr
            #
            # if is_float(ordr['average']):
            #     pr = copy_prec(ordr['average'], '.11111111')
            # elif is_float(ordr['price']):
            #     pr = copy_prec(ordr['price'], '.11111111')
            # else:
            #     pr = str(ex.prices[cp.replace('/', '')])
            #
            # if is_float(ordr['filled']):
            #     buy_amount = float(ordr['filled'])
            #     if buy:
            #         msg = 'Bought ' + str(buy_amount) + ' ' + coin + ' at ' + str(pr) + ' ' + cp + '.'
            #     else:
            #         msg = 'Sold ' + str(buy_amount) + ' ' + coin + ' at ' + str(pr) + ' ' + cp + '.'
            #
            #     await self.out_q.coro_put(['msg', msg])
            #
            #     return pr, buy_amount
            # else:
            #     if buy:
            #         msg = 'Buy order of ' + str(amount) + ' ' + coin + ' at ' + str(pr) + ' ' + cp + ' sent.'
            #     else:
            #         msg = 'Sell order of ' + str(amount) + ' ' + coin + ' at ' + str(pr) + ' ' + cp + ' sent.'
            #
            #     await self.out_q.coro_put(['msg', msg])

                # return str(pr), str(amount)

        except Exception as e:
            print('sell all error', e)
            if 'MIN_NOTIONAL' in str(e) or 'insufficient balance' in str(e) or '1013' in str(e):
                print('too low')
                if buy:
                    msg = 'Insufficient balance of ' + cp + '. Attempted to buy ' + str(amount) + ' ' + coin + ' with ' + str(pair_bal) + ' ' + pair + '.'
                else:
                    msg = 'Insufficient balance of ' + cp + '. Attempted to sell ' + str(amount) + ' ' + coin + '.'
                await self.my_msg(msg, to_tele=True, to_broad=True)
            else:
                print(cp, e)
                msg = 'Error in Trade Catch ' + cp + ': ' + str(e)
                await self.my_msg(msg, to_tele=True, to_broad=True)
            return None

    async def get_trades(self, exchange, market, *args):
        ex = self.exchange_selector(exchange)
        if ex.apiKey and ex.secret:
            if exchange == 'Binance' or exchange == 'Binance US':
                await self.a_debit_exchange(ex, 10)
            else:
                await self.a_debit_exchange(ex, 1)
            return [market, await ex.fetch_my_trades(market)]
        else:
            return [None, None]

    async def get_my_id(self):
        self.my_id += 1
        return str(self.my_id)

    async def save(self, *args):
        # API Keys
        store = {
            'Binance': {'key': self.a_binance.apiKey, 'secret': self.a_binance.secret},
            'Binance US': {'key': self.a_binanceUS.apiKey, 'secret': self.a_binanceUS.secret},
            'BitMEX': {'key': self.a_bitmex.apiKey, 'secret': self.a_bitmex.secret},
            'Coinbase Pro': {'key': self.a_cbp.apiKey, 'secret': self.a_cbp.secret,
                             'password': self.a_cbp.password},
            'FTX': {'key': self.a_ftx.apiKey, 'secret': self.a_ftx.secret},
            'Kraken': {'key': self.a_kraken.apiKey, 'secret': self.a_kraken.secret},
            }
        save_store('APIKeys', store)

        # Telegram Keys
        if self.tele_bot:
            store = {
                'tele_token': self.tele_bot.token,
                'tele_chat': self.tele_bot.chat_id,
            }
            save_store('TeleKeys', store)

        # Basic Bot Data
        bb_cards = [rec.to_dict() for rec in self.bb_cards]
        bb_trades = [rec.to_dict() for rec in self.bb_trades]
        store = {
            'bb_strat': self.bb_strat.to_dict(),
            'bb_trades': bb_trades,
            'bb_cards': bb_cards,
            'bb_trade_limit': self.bb_trade_limit,
        }
        save_store('BasicBot', store)

        # Advanced Bot Data
        ab_cards = [rec.to_dict() for rec in self.ab_cards]
        ab_trades = [rec.to_dict() for rec in self.ab_trades]
        store = {
            'ab_cards': ab_cards,
            'ab_trades': ab_trades,
            'ab_trade_limit': self.ab_trade_limit,
        }
        save_store('AdvancedBot', store)

        msg = 'Saved Data.'
        await self.my_msg(msg, verbose=True)

    async def sync_trades_to_cards(self):
        try:
            for tc in self.bb_trades + self.ab_trades:
                if not tc.sold:
                    update = False
                    # hunt down card
                    for cc in self.bb_cards + self.ab_cards:
                        if (tc.coin == cc.coin and tc.pair == cc.pair and
                                tc.exchange == cc.exchange and tc.kind == cc.kind):
                            # found it
                            ex = self.exchange_selector(tc.exchange)
                            tc.precision = cc.precision
                            tc.take_profit_per = cc.take_profit_per
                            tc.trail_per = cc.trail_per
                            tc.stop_per = cc.stop_per
                            tc.dca_buyback_per = cc.dca_buyback_per
                            # print('cc', cc.coin, cc.pair, cc.take_profit_per, cc.trail_per, cc.stop_per, cc.dca_buyback_per)
                            # print(self.bb_strat.take_profit_per)
                            # print('found card and trade')
                            my_trades = []
                            reset = False
                            mid = 0
                            vol = 0
                            min_buy = 0
                            for child in tc.childs:
                                # Now tally up children
                                mid += float(child['buy_price']) * float(child['amount'])
                                vol += float(child['amount'])
                                if not min_buy > 0 or float(child['buy_price']) < min_buy:
                                    min_buy = float(child['buy_price'])

                            if vol:
                                avg_price = mid / vol
                                tc.trade_amount = copy_prec(vol, cc.precision)
                                tc.buy_price = copy_prec(avg_price, cc.precision)

                            if is_float(cc.dca_buyback_per):
                                buyback = min_buy * (1 - float(cc.dca_buyback_per) / 100)
                                tc.dca_buyback_price = copy_prec(buyback, cc.precision)
                            else:
                                tc.dca_buyback_price = ''

                            if is_float(cc.take_profit_per):
                                sell = float(tc.buy_price) * (100 + float(cc.take_profit_per)) / 100
                                tc.take_profit_price = copy_prec(sell, cc.precision)
                            else:
                                tc.take_profit_price = ''

                            if is_float(cc.stop_per):
                                stop = float(tc.buy_price) * (100 - float(cc.stop_per)) / 100
                                tc.stop_price = copy_prec(stop, cc.precision)
                            else:
                                tc.stop_price = ''
                            break


        except Exception as e:
            print('average calculation', e)
            await self.my_msg('Error in DCA Averages Calculations for ' + tc.coin + '/' + tc.pair,
                              to_tele=True, to_broad=True)
            cc.active = False
            tc.active = False


