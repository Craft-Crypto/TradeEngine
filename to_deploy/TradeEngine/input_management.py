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

from aioconsole import ainput
from TradeEngine.tele_api_calls import TeleBot
from CraftCrypto_Helpers.Helpers import file_path, is_float, copy_prec
import sys


async def manage_input(self, msg):
    if msg.lower() == 'setup':
        await self.my_msg('Setup Exchange API Keys? (Y/n)')
        msg = await ainput(">")
        if msg.lower() in ['y', 'yes']:
            await self.set_api_keys()

        await self.my_msg('Set BasicBot Trading? (Y/n)')
        msg = await ainput(">")
        if msg.lower() in ['y', 'yes']:
            await self.set_bb_strat()

        await self.my_msg('Setup Telegram Notifications? (Y/n)')
        msg = await ainput(">")
        if msg.lower() in ['y', 'yes']:
            await self.q.put('set tele keys')

    elif msg == 'set API keys':
        await self.set_api_keys()

    elif msg == 'set tele keys':
        await self.my_msg('Setting Up Telegram Bot...')
        if self.tele_bot:
            await self.my_msg('Telegram Bot already active. Reset? (Y/n)')
            msg = await ainput(">")
            if msg.lower() in ['y', 'yes']:
                await self.my_msg('Stopping Telegram Bot...')
                await self.tele_bot.stop_bot()
                del self.tele_bot
            else:
                return

        await self.my_msg('*******')
        await self.my_msg('TradeCraft Lite can be controlled through a Telegram Bot. '
                          'However, you need to make your own.')
        await self.my_msg('This process is automated where it can be, '
                          'but Telegram requires a human to kick it off.')
        await self.my_msg('Creating a bot is straightforward, however. '
                          'Create a Bot by starting a conversation on Telegram with @Botfather.')
        await self.my_msg('When the bot is complete, enter the following:')
        await self.my_msg('Telegram Chat Bot Key:')
        msg = await ainput(">")

        try:
            self.tele_bot = TeleBot(msg, '', self)
            await self.tele_bot.set_commands()
            await self.tele_bot.set_dispatcher()
            await self.my_msg('Bot added. Press /start in Telegram Bot')
        except Exception as e:
            msg = 'Telegram Error: ' + str(e)
            await self.my_msg(msg)

        await self.my_msg('Enter Telegram Chat Chat ID:')
        msg = await ainput(">")
        self.tele_bot.chat_id = msg
        await self.my_msg('Telegram Bot Activated', to_tele=True)

        await self.save()
        self.pause_msg = False

    elif msg == 'set bb strat':
        await self.set_bb_strat()

    elif msg == 'activate bb':
        self.bb_active = True
        await self.my_msg('Basic Bot Enabled.', to_tele=True, to_broad=True)

    elif msg == 'pause bb':
        self.bb_active = False
        await self.my_msg('Basic Bot Paused.', to_tele=True, to_broad=True)

    elif msg == 'bb now':
        self.bb_active = True
        msg = 'Starting Basic Bot checks now.'
        await self.my_msg(msg, to_tele=True, to_broad=True)
        await self.check_bot_cards(self.bb_strat.candle)

    elif msg == 'bb card status':
        for card in self.bb_cards:
            print(card)

    elif msg == 'ab card status':
        for card in self.ab_cards:
            print(card)

    elif msg == 'bb status':
        msg = '*******'
        msg += 'Basic Bot Status:'
        msg += '\n-Active: ' + str(self.bb_active)
        msg += '\n-Strategy: ' + str(self.bb_strat.title)
        msg += '\n-Exchange: ' + str(self.bb_strat.exchange)
        msg += '\n-Pair: ' + str(self.bb_strat.pair)
        msg += '\n-Pair Min Mult: ' + str(self.bb_strat.pair_minmult)
        msg += '\n-Trade Limit: ' + str(self.bb_trade_limit)
        await self.my_msg(msg, to_tele=True, to_broad=False)

    elif msg == 'activate ab':
        self.ab_active = True
        await self.my_msg('Advanced Bot Enabled.', to_tele=True, to_broad=True)

    elif msg == 'pause ab':
        self.ab_active = False
        await self.my_msg('Advanced Bot Paused.', to_tele=True, to_broad=True)

    elif msg in ['bb trades', 'ab trades']:
        trades = []
        if 'bb' in msg:
            await self.my_msg('*******\nBasic Bot Trades:', to_tele=True, to_broad=False)
            trades = self.bb_trades
        else:
            await self.my_msg('*******\nAdvanced Bot Trades:', to_tele=True, to_broad=False)
            trades = self.ab_trades

        if trades:
            for tr in trades:
                msg = tr.coin + '/' + tr.pair + '  ' + tr.gl_per + '%'
                if tr.sold:
                    msg += ' - Sold'
                if len(tr.childs) > 1:
                    msg += '\n- DCA Buys:'
                    for child in tr.childs:
                        gl = float(tr.now_price) / float(child['buy_price']) * 100 - 100
                        # print(tc.coin, tc.pair, tc.now_price, tc.buy_price, tc.gl_per)
                        child_gl = str(round(gl, 2))
                        msg += '\n-- {0} at {1} {2}%'.format(child['amount'], child['buy_price'], str(child_gl))
                msg += '\n- Last Updated: ' + tr.last_update
                await self.my_msg(msg, to_tele=True, to_broad=False)
        else:
            await self.my_msg('No trades found. Use \'activate bb\' or \'activate ab\' to begin trading.', to_tele=True)

    elif msg in ['bb detailed trades', 'ab detailed trades']:
        trades = []
        if 'bb' in msg:
            await self.my_msg('*******\nBasic Bot Trades (Detailed):', to_tele=True)
            trades = self.bb_trades
        else:
            await self.my_msg('*******\nAdvanced Bot Trades (Detailed):', to_tele=True)
            trades = self.ab_trades
        if trades:
            for tr in self.bb_trades:
                msg = tr.coin + '/' + tr.pair + '  ' + tr.gl_per + '%'
                if tr.sold:
                    msg += ' - Sold'
                # await self.my_msg(msg, False, True)
                if len(tr.childs) > 1:
                    msg += '\n- DCA Buys:'
                    for child in tr.childs:
                        gl = float(tr.now_price) / float(child['buy_price']) * 100 - 100
                        # print(tc.coin, tc.pair, tc.now_price, tc.buy_price, tc.gl_per)
                        child_gl = str(round(gl, 2))
                        msg += '\n-- {0} at {1} {2}%'.format(child['amount'], child['buy_price'], str(child_gl))
                else:
                    msg += '\n- Amount: ' + tr.amount
                    msg += '\n- Buy Price: ' + tr.buy_price
                if tr.sold:
                    msg += '\n- Sold Price: ' + tr.sold_price
                else:
                    msg += '\n- Current Price: ' + tr.now_price
                msg += '\n- Take Profit: ' + tr.sell_price + ' (' + tr.sell_per + '%)'
                msg += '\n- Average Buy Price: ' + tr.buy_price
                msg += '\n- DCA Price: ' + tr.dca_buyback_price + ' (-' + tr.dca_buyback_per + '%)'
                msg += '\n- Stop Loss: ' + tr.stop_price + ' (-' + tr.stop_per + '%)'
                msg += '\n- Trail Price: ' + tr.trail_price + ' (' + tr.trail_per + '%)'
                msg += '\n- Last Updated: ' + tr.last_update
                await self.my_msg(msg, to_tele=True)
        else:
            await self.my_msg('No trades found. Use \'activate bb\' or \'activate ab\' to begin trading.', to_tele=True)

    elif msg in ['clear bb trades', 'clear ab trades']:
        await self.my_msg(
            'About to Delete all Trade Data. This cannot be undone. Enter\'yes\' to continue.')
        msg = await ainput(">")
        if msg == 'yes':
            if 'bb' in msg:
                self.bb_trades = []
            else:
                self.ab_trades = []
            await self.my_msg('Trades Deleted')
        else:
            await self.my_msg('Canceled')

    elif msg == 'save':
        await self.save()

    elif msg == 'verbose':
        self.verbose = not self.verbose
        msg = 'Verbose: ' + str(self.verbose)
        await self.my_msg(msg)

    elif msg in ['collect bb', 'collect ab']:
        if 'bb' in msg:
            self.collect_sells(True)
        else:
            self.collect_sells(False)

    elif msg in ['sell positive bb', 'sell positive ab']:
        if 'bb' in msg:
            self.make_positive_sells(True)
        else:
            self.make_positive_sells(False)

    elif msg == 'balance':
        await self.collect_balance()

    elif msg.split(',')[0] == 'quick trade':
        if msg == 'quick trade':
            await self.quick_trade()
        else:
            data = msg.split(',')
            kind = data[1]
            ex = self.exchange_selector(data[2])
            cp = data[3]
            amount = data[4]
            await self.quick_trade([kind, ex, cp, amount])

    elif msg == 'exit':
        self.exit()

    elif msg == 'waiting commands':
        msg = f'Commands waiting on Exchanges: {str(self.in_waiting)}'
        await self.my_msg(msg, to_tele=True)

    elif msg == 'clock':
        msg = 'Binance Servers require requests to be within 1000ms of their server time. However, there are times' \
              'when a computer\'s time may shift.' \
              '\n Here are some ways that you can try and fix it on your computer:' \
              '\n Method 1: From control panel > date and time > internet time. ' \
              'Then change the server to >>>> time.nist.gov' \
              '\n Method 2: From the Run box, enter “services.msc”. This will bring up the Services window. ' \
              'You can search in the control panel for it as well. ' \
              'Make sure the \'Windows Time\' service is running. ' \
              '\nFrom PowerShell as admin, run following commands to sync time:' \
              '\nnet stop w32time' \
              '\nw32tm /unregister' \
              '\nw32tm /register' \
              '\nnet start w32time' \
              '\nw32tm /resync'

        await self.my_msg(msg, to_tele=True)


    #
    #     elif msg[0] == 'check_key':
    #         asyncio.ensure_future(self.check_cc_key(msg[1], [msg[2], msg[3]]))
    #
    #     elif msg[0] == 'stop':
    #         print('stopping....')
    #         self.running = False
    #         self.sched.shutdown()
    #         self.loop.stop()
    #         # super(Worker, self).stop()
    #         print('stopped?')
    #
    #
    #     # # elif msg[0] == 'bot_sells':
    #     # #     if not self.sells_lock:
    #     # #         asyncio.ensure_future(self.check_bot_sells(literal_eval(msg[1]), literal_eval(msg[2])))
    #     #
    #     # elif msg[0] == 'basic_bot_sells':
    #     #     if not self.sells_lock:
    #     #         asyncio.ensure_future(self.basic_check_bot_sells(literal_eval(msg[1]), literal_eval(msg[2])))
    #     #
    #     # # elif msg[0] == 'bot_trade_data':
    #     # #     asyncio.ensure_future(self.check_aibot_cards(literal_eval(msg[1]), literal_eval(msg[2]), msg[3], msg[4]))
    #     #
    #     # elif msg[0] == 'basic_data':
    #     #     print('got basic data')
    #     #     asyncio.ensure_future(self.check_basic_bot(literal_eval(msg[1]), literal_eval(msg[2]), msg[3], msg[4]))
    #     #     print('end basic')
    #     #
    #     # # elif msg[0] == 'bot_active':
    #     # #     self.bot_active = msg[1]
    #     #
    #     # elif msg[0] == 'basic_active':
    #     #     self.basic_active = msg[1]
    #
    #     # elif msg[0] == 'verify':
    #     #     ex = self.exchange_selector(msg[1])
    #     #     await self.a_debit_exchange(ex, 1)
    #     #     await ex.load_markets(reload=True)
    #     #     if msg[2] in ex.markets:
    #     #         info = ex.market(msg[2])
    #     #         await self.q.coro_put(['verified', msg[1], msg[2],
    #     #                                   str(info['limits']['amount']['min']),
    #     #                                   str(info['limits']['cost']['min']), True])
    #     #     else:
    #     #         await self.q.coro_put(['verified', msg[1], msg[2], 'Coin/Pair Not Listed',
    #     #                                   'Coin/Pair Not Listed', True])
    #
    #     # elif msg[0] == 'manual_buy':
    #     #     #'manual_bought': #cp, amount
    #     #     ex = self.exchange_selector(msg[1])
    #     #     amount = ex.amount_to_precision(msg[2], msg[3])
    #     #     pr, amount = await self.buy_sell_now(ex, msg[2], amount, True, True)
    #     #     if pr == 'No Bal':
    #     #         print('No Balance to trade sell')
    #     #         msg = 'Not enough balance for Manual Trade of: ' + msg[2]
    #     #         await self.q.coro_put(['msg', msg])
    #     #         await self.q.coro_put(['manual_bought', msg[2], '0'])
    #     #     else:
    #     #         await self.q.coro_put(['manual_bought', msg[2], amount])
    #     #
    #     # elif msg[0] == 'manual_sell':
    #     #     #'manual_bought': #cp, amount
    #     #     ex = self.exchange_selector(msg[1])
    #     #     amount = ex.amount_to_precision(msg[2], msg[3])
    #     #     pr, amount = await self.buy_sell_now(ex, msg[2], amount, False, True)
    #     #     if pr == 'No Bal':
    #     #         print('No Balance to trade sell')
    #     #         msg = 'Not enough balance for Manual Trade of: ' + msg[2]
    #     #         await self.q.coro_put(['msg', msg])
    #     #         await self.q.coro_put(['manual_bought', msg[2], '0'])
    #     #     else:
    #     #         await self.q.coro_put(['manual_sold', msg[2], amount])
    #
    #     elif msg[0] == 'reload':
    #         ex = self.exchange_selector(msg[1])
    #         await self.a_debit_exchange(ex, 1)
    #         await ex.load_markets(reload=True)
    #
    #     elif msg[0] == 'quick_buy':
    #         # 'quick_buy': #ex, pair, cp, %
    #         ex = self.exchange_selector(msg[1])
    #         amount = float(ex.balance[msg[2]]) * float(msg[4])
    #         amount = amount / float(ex.prices[msg[3].replace('/', '')])
    #         await self.buy_sell_now(ex, msg[3], amount, True, True)
    #
    #     elif msg[0] == 'quick_sell':
    #         ex = self.exchange_selector(msg[1])
    #         amount = float(ex.balance[msg[2]]) * float(abs(float(msg[4])))
    #         await self.buy_sell_now(ex, msg[3], amount, False, True)
    #
    #     elif msg[0] == 'convert':
    #         if not self.convert_lock:
    #             asyncio.ensure_future(self.convert(msg[1], msg[2], msg[3]))
    #         else:
    #             print('convert locked')
    #
    #     # elif msg[0] == 'backtest':
    #     #     print('got command')
    #     #     asyncio.ensure_future(self.backtest(literal_eval(msg[1]), literal_eval(msg[2])))
    #     #
    #     # elif msg[0] == 'get_history':
    #     #     asyncio.ensure_future(self.get_history(msg[1]))
    #
    #     elif msg[0] == 'send_bot':
    #         try:
    #             await bot.send_message(chat_id=bot.chat_id, text=msg[1])
    #         except Exception as e:
    #             print('tele error', e)
    #
    #     elif msg[0] == 'tele_init':
    #         try:
    #             bot.__init__(token=msg[1])
    #             bot.worker = self
    #             await bot.set_my_commands(c)
    #             if not dp.is_polling():
    #                 asyncio.ensure_future(dp.start_polling())
    #             await self.q.coro_put(['msg', 'Bot added. Press /start in Telegram Bot'])
    #         except Exception as e:
    #             msg = 'Telegram Error: ' + str(e)
    #             await self.q.coro_put(['msg', msg])
    #
    #     elif msg[0] == 'tele_check':
    #         bot.chat_id = msg[1]
    #         await self.q.coro_put(['send_bot', 'Telegram Bot Activated'])
    #
    #     elif msg[0] == 'update_bals':
    #         await self.gather_update_bals()
    #
    #     # elif msg[0] == 'get_bot_trade_data':
    #     #     await self.q.coro_put(['get_bot_trade_data', msg[1]])
    #
    #     elif msg[0] == 'get_basic_data':
    #         await self.q.coro_put(['get_basic_data', msg[1]])
    #
    #     else:
    #         print(msg)
    #
    #     asyncio.ensure_future(self.get_user_input())
    elif msg == 'help':
        msg = 'TradeEngine can be fully controlled through TradeCraft Pro. However, the following commands ' \
              'can also be used. Any changes made in TradeEngine will also be reflected in TradeCraft Pro.'
        msg += '\nList of Bot commands:'
        msg += '\n>setup - Starts the process of setting exchanges and keys. This can be done through TradeCraft Pro'
        msg += '\n>set API keys - Add API Keys for Exchanges'
        msg += '\n>set tele keys - Add Keys for Telegram Integration'
        msg += '\n>set bb strat - Configure the Basic Bot'
        msg += '\n>bb status - Hows the current strategy for the Basic Bot'
        msg += '\n>activate bb - Start the Basic Bot'
        msg += '\n>pause bb - Pause the Basic Bot'
        msg += '\n>bb now - Starts the Basic Bot, and also evaluates all the coins immediately'
        msg += '\n>bb card status - Prints the cards used in Basic Bot trading (not easily readable... yet)'
        msg += '\n>ab card status - Prints the cards used in Advanced Bot trading (not easily readable... yet)'
        msg += '\n>activate ab - Start the Advanced Bot'
        msg += '\n>pause ab - Pause the Advanced Bot'
        msg += '\n>bb trades - Prints overview of trades made by Basic Bot'
        msg += '\n>bb detailed trades - Prints detailed overview of trades made by Basic Bot'
        msg += '\n>clear bb trades - Deletes all trades made by Basic Bot'
        msg += '\n>collect bb - Clears all completed trades made by Basic Bot'
        msg += '\n>sell positive bb - Sells all trades that are positive for Basic Bot'
        msg += '\n>ab trades - Prints overview of trades made by Advanced Bot'
        msg += '\n>ab detailed trades - Prints detailed overview of trades made by Advanced Bot'
        msg += '\n>clear ab trades - Deletes all trades made by Advanced Bot'
        msg += '\n>collect ab - Clears all completed trades made by Advanced Bot'
        msg += '\n>sell positive ab - Sells all trades that are positive for Advanced Bot'
        msg += '\n>balance - Shows current account balances'
        msg += '\n>quick trade - Starts a trade outside of the Bots'
        msg += '\n>save - Save Data'
        msg += '\n>verbose - Give more detailed running information on the Bot'
        msg += '\n>exit - Closes TradeEngine (ungracefully for now)'
        msg += '\nFor more information, please visit craft-crypto.com'
        await self.my_msg(msg, False, False)
    else:
        await self.my_msg(
            'Command ' + str(msg) + ' not understood. Use \'help\' for a list of commands.', False,
            False)