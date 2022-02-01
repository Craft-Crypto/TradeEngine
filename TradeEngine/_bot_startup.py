# from tele_api_calls import tele_bot, dp, tele_cmds
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers import cron
import asyncio
import time
import ccxt.async_support as a_ccxt
from hypercorn.asyncio import serve
from hypercorn.config import Config
from CraftCrypto_Helpers.Helpers import get_store, save_store
from TradeEngine._tele_api_calls import TeleBot
from TradeEngine._trade_api_calls import engine_api
from CraftCrypto_Helpers.BaseRecord import BaseRecord, convert_record


async def initialize(self):
    # Set up initial variables and such
    await self.my_msg('Initializing...', False, False)
    tt = time.time()

    await self.my_msg('Loading Exchanges...', False, False)
    self.a_binance = a_ccxt.binance({'options': {'adjustForTimeDifference': True}})
    self.a_binanceUS = a_ccxt.binanceus({'options': {'adjustForTimeDifference': True}})
    self.a_bitmex = a_ccxt.bitmex({'options': {'adjustForTimeDifference': True}})
    self.a_cbp = a_ccxt.coinbasepro({'options': {'adjustForTimeDifference': True}})
    self.a_kraken = a_ccxt.kraken({'options': {'adjustForTimeDifference': True}})
    self.a_ftx = a_ccxt.ftx({'options': {'adjustForTimeDifference': True}})

    self.exchanges = ['Binance', 'Binance US', 'BitMEX', 'Coinbase Pro', 'Kraken', 'FTX']

    for exchange in self.exchanges:
        ex = self.exchange_selector(exchange)
        ex.timeout = 30000
        ex.socket = None
        ex.socket_connected = False
        ex.api_ok = False
        ex.prices = {}
        ex.balance = {}
        ex.rate_limit = 10  # per second. Updates to more correct amount

    await self.my_msg('Checking for API Keys...', False, False)
    store = get_store('APIKeys')
    if store:
        for exchange in self.exchanges:
            ex = self.exchange_selector(exchange)
            try:
                ex.apiKey = store[exchange]['key']
                ex.secret = store[exchange]['secret']
                if exchange == 'Coinbase Pro':
                    ex.password = store[exchange]['password']
            except Exception as e:
                self.my_msg('Error in getting API Store ' + exchange, False, False)
        print('did I get here?')
        need_keys = await self.test_apis()
        if need_keys:
            await self.q.put('set API keys')
    else:
        await self.my_msg('No Keys Found...', False, False)
        # await self.q.put('set API keys')

    # Now get Telegram Going
    store = get_store('TeleKeys')
    await self.my_msg('Starting Telegram Bot...', False, False)
    token = None
    chat_id = None
    try:
        if store:
            token = store['tele_token']
            chat_id = store['tele_chat']
    except Exception as e:
        await self.my_msg('Error in Loading Telegram Keys: ' + str(e), False, False)

    if token and chat_id:
        await self.init_tele_bot(token, chat_id)
        await self.my_msg('Telegram Bot Activated.', False, True)
    else:
        await self.my_msg('No Telegram Keys Found.', False, False)
        # await self.q.put('set tele keys')

    await self.my_msg('Loading Strategies...', False, False)
    store = get_store('BasicStrats')
    if not store:
        strat = BaseRecord()
        strat.title = 'RSI DCA Minute Trading'
        strat.description = ('This strategy uses 1 minute candles and the Relative Strength Index to ' +
                             'initiate buys. It then looks for quick profit opportunities, and chances to ' +
                             'Down Cost Average on the dips.')
        strat.candle = "1m"
        strat.sell_per = "2"
        strat.trail_per = ".5"
        strat.dca_buyback_per = "10"
        strat.rsi_buy = "30"

        strat1 = BaseRecord()
        strat1.title = 'MACD Stoch Long Haul'
        strat1.description = ('A Strategy that works on the 4 hour candle, but tends to find just the ' +
                              'perfect time to buy. The Long Haul waits to buy when the MACD to cross up and ' +
                              'be in the red, with a Stoch under 30, and keeps a moderate take profit, stop ' +
                              'loss, and trail.')
        strat1.candle = "4h"
        strat1.sell_per = "10"
        strat1.trail_per = "1"
        strat1.stop_per = "20"
        strat1.macd_cross_buy = "Yes"
        strat1.macd_color_buy = "Yes"
        strat1.stoch_val_buy = "30"

        strat2 = BaseRecord()
        strat2.title = 'Cross and Pop'
        strat2.description = ('Combining Simple Moving Average Crosses with Trailing Stop Losses and ' +
                              'Down Cost Averaging is a great way to earning profit off a volatile market in ' +
                              'the 5 minute candle.')
        strat2.candle = "5m"
        strat2.sell_per = "2"
        strat2.trail_per = ".5"
        strat2.dca_buyback_per = "10"
        strat2.sma_cross_fast = "17"
        strat2.sma_cross_slow = "55"
        strat2.sma_cross_buy = "Yes"

        strat_store = {'1': strat.to_dict(),
                       '2': strat1.to_dict(),
                       '3': strat2.to_dict()
        }
        save_store('BasicStrats', strat_store)

    await self.my_msg('Loading Saved Trades...', False, False)

    # Check for Legacy
    store = get_store('LiteBot')
    if store:
        for cc in store['trades']:
            new_rec = convert_record(cc)
            self.bb_trades.append(new_rec)
    else:
        store = get_store('BasicBot')
        if store:
            try:
                self.bb.set_record(store['bb_strat'])
                for cc in store['bb_cards']:
                    rec = BaseRecord()
                    rec.set_record(cc)
                    self.bb_cards.append(rec)
                for tc in store['bb_trades']:
                    rec = BaseRecord()
                    rec.set_record(tc)
                    self.bb_trades.append(rec)
                self.bb_trade_limit = store['bb_trade_limit']
                await self.my_msg('Found Basic Bot Trades:', False, False)
            except Exception as e:
                print(e)
                await self.my_msg('Error loading Basic Bot Trades', False, False)

        else:
            await self.my_msg('No Saved Basic Bot Trades Found.', False, False)
            # await self.q.put('set strat')

    store = get_store('AdvancedBot')
    if store:
        try:
            for cc in store['ab_cards']:
                rec = BaseRecord()
                rec.set_record(cc)
                self.ab_cards.append(rec)
            for tc in store['ab_trades']:
                rec = BaseRecord()
                rec.set_record(tc)
                self.ab_trades.append(rec)
            self.ab_trade_limit = store['ab_trade_limit']
            await self.my_msg('Found Advanced Bot Trades:', False, False)
        except Exception as e:
            await self.my_msg('Error loading Advanced Bot Trades', False, False)

    else:
        await self.my_msg('No Saved Advanced Bot Trades Found.', False, False)

    #
    # await self.my_msg('Strategy: ' + self.strat_name, False, False)
    # await self.my_msg('Exchange: ' + str(self.active_exchange), False, False)
    # await self.my_msg('Pair: ' + self.pair, False, False)
    # await self.my_msg('Pair Min Mult: ' + self.pair_minmult, False, False)
    # await self.my_msg('Trade Limit: ' + self.limit, False, False)

    await self.my_msg('Setting Trade Data Scheduler...', False, False)
    self.sched = AsyncIOScheduler()

    t1 = cron.CronTrigger(second=3)
    t3 = cron.CronTrigger(minute='*/3', second=5)
    t5 = cron.CronTrigger(minute='*/5', second=5)
    t15 = cron.CronTrigger(minute='*/15', second=5)
    t30 = cron.CronTrigger(minute='*/30', second=5)
    t1h = cron.CronTrigger(minute=0, second=5)
    t2h = cron.CronTrigger(hour='*/2', minute=0, second=5)
    t4h = cron.CronTrigger(hour='*/4', minute=0, second=5)
    t6h = cron.CronTrigger(hour='*/6', minute=0, second=5)
    t8h = cron.CronTrigger(hour='*/8', minute=0, second=5)
    t12h = cron.CronTrigger(hour='*/12', minute=0, second=5)
    t1d = cron.CronTrigger(hour=0, minute=0, second=5)

    candles = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d']
    trigs = [t1, t3, t5, t15, t30, t1h, t2h, t4h, t6h, t8h, t12h, t1d]

    for i in range(len(candles)):
        self.sched.add_job(self.check_bot_cards, args=[candles[i]], trigger=trigs[i])

    #
    #
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '3m'], trigger=t3)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '5m'], trigger=t5)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '15m'], trigger=t15)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '30m'], trigger=t30)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '1h'], trigger=t1h)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '2h'], trigger=t2h)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '4h'], trigger=t4h)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '6h'], trigger=t6h)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '8h'], trigger=t8h)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '12h'], trigger=t12h)
    # self.sched.add_job(self.check_bot_cards, args=['Advanced Bot', '1d'], trigger=t1d)

    #
    self.sched.add_job(self.gather_update_bals, trigger=t1)
    #

    # Set up server
    await self.my_msg('Setting Up Trade Server...', False, False)
    await asyncio.sleep(.5)
    config = Config()
    config.bind = ["0.0.0.0:8080"]  # As an exa
    self.trade_server = engine_api
    self.trade_server.worker = self
    asyncio.ensure_future(serve(self.trade_server, config))

    # Exchange Finishing Up
    await self.my_msg('Finishing Up Exchanges...', False, False)
    asyncio.ensure_future(self.refresh_api())
    self.a_binanceUS.rate_limit = 5
    await self.gather_update_bals()

    # Maybe I need a wait function here for everything to truly finish up. But Also probably not
    await asyncio.sleep(3)
    asyncio.ensure_future(self.check_prices_sells())
    self.sched.start()
    await self.my_msg('Initialization Complete.', False, False)
    await self.my_msg('*******', False, False)
    await self.my_msg('Enter \'setup\' to set up trading.', False, False)


async def test_apis(self, *args):
    # This can just test all of them at once
    under_test = self.exchanges
    if args:
        under_test = [args[0]]
    need_keys = True
    for ex in under_test:
        exchange = self.exchange_selector(ex)
        if exchange.apiKey and exchange.secret:
            if str(exchange) in ['Binance', 'Binance US']:
                await self.a_debit_exchange(exchange, 5)
            else:
                await self.a_debit_exchange(exchange, 1)

            try:
                await self.update_bals(exchange)
                # print(bal)
                if exchange.balance:
                    exchange.api_ok = True
                    msg = str(exchange) + ' API Keys Accepted'
                    await self.my_msg(msg, False, False)
                    # await exchange.close()
                    need_keys = False
                    for n in range(1, 5):
                        try:
                            msg = 'Attempt ' + str(n) + ' to load markets...'
                            await self.my_msg(msg, False, False)
                            await exchange.load_markets()
                            await self.my_msg('Market loaded.', False, False)
                            break
                        except Exception as e:
                            msg = 'Connection Error: ' + str(e)
                            await self.my_msg(msg, False, False)
                            if n == 5:
                                msg = 'Exceeded Maximum number of retries'
                                await self.my_msg(msg, False, False)

                    # Coinbase actually does not allow fetch tickers right now
                    if not str(exchange) == 'Coinbase Pro':
                        await self.my_msg('Collecting Market Prices...', False, False)
                        price = await exchange.fetch_tickers()
                        if str(exchange) in ['Binance', 'Binance US', 'Kraken']:
                            try:
                                for ky in price:
                                    exchange.prices[ky.replace('/', '')] = price[ky]['close']
                            except Exception as e:
                                await self.my_msg(str(exchange) + 'Fetch Ticker Error: ' + str(e), False, False)
                        elif str(exchange) == 'FTX':
                            try:
                                for ky in price:
                                    self.a_ftx.prices[ky.replace('/', '').replace('-', '')] = price[ky]['close']
                            except Exception as e:
                                await self.my_msg('FTX Fetch Ticker Error: ' + str(e), False, False)

                    if not exchange.socket:
                        await self.my_msg('Activating Web Socket...', False, False)
                        if str(exchange) == 'Binance':
                            exchange.socket = asyncio.ensure_future(self.websocket_bin())
                        elif str(exchange) == 'Binance US':
                            exchange.socket = asyncio.ensure_future(self.websocket_binUS())
                        elif str(exchange) == 'BitMEX':
                            exchange.socket = asyncio.ensure_future(self.websocket_bm())
                        elif str(exchange) == 'Coinbase Pro':
                            exchange.socket = asyncio.ensure_future(self.websocket_cbp())
                        elif str(exchange) == 'FTX':
                            exchange.socket = asyncio.ensure_future(self.websocket_ftx())
                        elif str(exchange) == 'Kraken':
                            exchange.socket = asyncio.ensure_future(self.websocket_kraken())
                    await self.my_msg(str(exchange) + ' loaded.', False, False)

            except Exception as e:
                exchange.api_ok = False
                msg = 'Error with ' + ex + ' API Keys: ' + str(e)
                await self.my_msg(msg, False, False)
        else:
            msg = 'No keys found for ' + ex
            await self.my_msg(msg, False, False)
    return need_keys


async def init_tele_bot(self, token, chat_id):
    if not self.tele_bot:
        self.tele_bot = TeleBot(token, chat_id, self)
        await self.tele_bot.set_commands()
        await self.tele_bot.set_dispatcher()
    else:
        self.tele_bot.token = token
        self.tele_bot.chat_id = chat_id
        await self.my_msg('Telegram Bot Activated', False, True)
