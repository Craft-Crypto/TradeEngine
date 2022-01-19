from aioconsole import ainput
from TradeEngine._tele_api_calls import TeleBot
from helper_functions import file_path, is_float, copy_prec

async def manage_input(self, msg):
    if msg.lower() == 'setup':
        await self.my_msg('Setup Exchange API Keys? (Y/n)', False, False)
        msg = await ainput(">")
        if msg.lower() in ['y', 'yes']:
            await self.set_api_keys()

        await self.my_msg('Set BasicBot Trading? (Y/n)', False, False)
        msg = await ainput(">")
        if msg.lower() in ['y', 'yes']:
            await self.set_bb_strat()

        await self.my_msg('Setup Telegram Notifications? (Y/n)', False, False)
        msg = await ainput(">")
        if msg.lower() in ['y', 'yes']:
            await self.q.put('set tele keys')

    elif msg == 'set API keys':
        await self.set_api_keys()

    elif msg == 'set tele keys':
        await self.my_msg('Setting Up Telegram Bot...', False, False)
        if self.tele_bot:
            await self.my_msg('Telegram Bot already active. Reset? (Y/n)', False, False)
            msg = await ainput(">")
            if msg.lower() in ['y', 'yes']:
                await self.my_msg('Stopping Telegram Bot...', False, False)
                await self.tele_bot.stop_bot()
                del self.tele_bot
            else:
                return

        await self.my_msg('*******', False, False)
        await self.my_msg('TradeCraft Lite can be controlled through a Telegram Bot. '
                          'However, you need to make your own.', False, False)
        await self.my_msg('This process is automated where it can be, '
                          'but Telegram requires a human to kick it off.', False, False)
        await self.my_msg('Creating a bot is straightforward, however. '
                          'Create a Bot by starting a conversation on Telegram with @Botfather.', False,
                          False)
        await self.my_msg('When the bot is complete, enter the following:', False, False)
        await self.my_msg('Telegram Chat Bot Key:', False, False)
        msg = await ainput(">")

        try:
            self.tele_bot = TeleBot(msg, '', self)
            await self.tele_bot.set_commands()
            await self.tele_bot.set_dispatcher()
            await self.my_msg('Bot added. Press /start in Telegram Bot', False, False)
        except Exception as e:
            msg = 'Telegram Error: ' + str(e)
            await self.my_msg(msg)

        await self.my_msg('Enter Telegram Chat Chat ID:', False, False)
        msg = await ainput(">")
        self.tele_bot.chat_id = msg
        await self.my_msg('Telegram Bot Activated', False, True)

        await self.save()
        self.pause_msg = False

    elif msg == 'set strat':
        await self.set_bb_strat()

    elif msg == 'activate bb':
        self.bb_active = True
        await self.my_msg('Basic Bot Enabled.', False, True)

    elif msg == 'pause bb':
        self.bb_active = False
        await self.my_msg('Basic Bot Paused.', False, True)

    elif msg == 'bb now':
        self.bb_active = True
        await self.check_bot_cards(self.bb_strat.candle)

    elif msg == 'bb card status':
        for card in self.bb_cards:
            print(card)

    elif msg == 'bb status':
        msg = '*******'
        msg += 'Basic Bot Status:'
        msg += '\n-Strategy: ' + str(self.bb_strat.kind)
        msg += '\n-Exchange: ' + str(self.bb_strat.exchange)
        msg += '\n-Pair: ' + str(self.bb_strat.pair)
        msg += '\n-Pair Min Mult: ' + str(self.bb_strat.pair_minmult)
        msg += '\n-Trade Limit: ' + str(self.bb_trade_limit)
        await self.my_msg(msg, False, True)

    elif msg == 'activate ab':
        self.ab_active = True
        await self.my_msg('Advanced Bot Enabled.', False, True)

    elif msg == 'pause ab':
        self.ab_active = False
        await self.my_msg('Advanced Bot Paused.', False, True)

    elif msg == 'eula':
        msg = '*******\n'
        file = open(file_path('EULA.txt'))
        msg += file.read()
        file.close()
        await self.my_msg(msg, False, False)

    elif msg in ['bb trades', 'ab trades']:
        trades = []
        if 'bb' in msg:
            await self.my_msg('*******\nBasic Bot Trades:', False, True)
            trades = self.bb_trades
        else:
            await self.my_msg('*******\nAdvanced Bot Trades:', False, True)
            trades = self.ab_trades

        if trades:
            for tr in trades:
                msg = tr.coin + '/' + tr.pair + '  ' + tr.gl_per + '%'
                if tr.sold:
                    msg += ' - Sold'
                if len(tr.children) > 1:
                    msg += '\n- DCA Buys:'
                    for child in tr.children:
                        gl = float(tr.now_price) / float(child['buy_price']) * 100 - 100
                        # print(tc.coin, tc.pair, tc.now_price, tc.buy_price, tc.gl_per)
                        child_gl = str(round(gl, 2))
                        msg += '\n-- {0} at {1} {2}%'.format(child['amount'], child['buy_price'], str(child_gl))
                msg += '\n- Last Updated: ' + tr.last_update
                await self.my_msg(msg, False, True)
        else:
            await self.my_msg('No trades found. Use \'activate bb\' or \'activate ab\' to begin trading.', False, True)

    elif msg in ['bb detailed trades', 'ab detailed trades']:
        trades = []
        if 'bb' in msg:
            await self.my_msg('*******\nBasic Bot Trades (Detailed):', False, True)
            trades = self.bb_trades
        else:
            await self.my_msg('*******\nAdvanced Bot Trades (Detailed):', False, True)
            trades = self.ab_trades
        if trades:
            for tr in self.bb_trades:
                msg = tr.coin + '/' + tr.pair + '  ' + tr.gl_per + '%'
                if tr.sold:
                    msg += ' - Sold'
                # await self.my_msg(msg, False, True)
                if len(tr.children) > 1:
                    msg += '\n- DCA Buys:'
                    for child in tr.children:
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
                msg += '\n- DCA Price: ' + tr.buyback_price + ' (-' + tr.dca_buyback_per + '%)'
                msg += '\n- Stop Loss: ' + tr.stop_price + ' (-' + tr.stop_per + '%)'
                msg += '\n- Trail Price: ' + tr.trail_price + ' (' + tr.trail_per + '%)'
                msg += '\n- Last Updated: ' + tr.last_update
                await self.my_msg(msg, False, True)
        else:
            await self.my_msg('No trades found. Use \'activate bb\' or \'activate ab\' to begin trading.', False, True)

    elif msg in ['clear bb trades', 'clear ab trades']:
        await self.my_msg(
            'About to Delete all Trade Data. This cannot be undone. Enter\'yes\' to continue.'
            , False, False)
        msg = await ainput(">")
        if msg == 'yes':
            if 'bb' in msg:
                self.bb_trades = []
            else:
                self.ab_trades = []
            await self.my_msg('Trades Deleted', False, False)
        else:
            await self.my_msg('Canceled', False, False)

    elif msg == 'save':
        await self.save()

    elif msg == 'verbose':
        self.verbose = not self.verbose
        msg = 'Verbose: ' + str(self.verbose)
        await self.my_msg(msg, False, False)

    elif msg in ['collect bb', 'collect ab']:
        per = 0
        num = 0
        trades = []
        if 'bb' in msg:
            trades = self.bb_trades
        else:
            trades = self.ab_trades
        if trades:
            for tc in self.trades:
                if tc['sold']:
                    if is_float(tc['gl_per']):
                        per += float(tc['gl_per'])
                    num += 1
            msg = 'Collected ' + str(num) + ' trades for a Gain/Loss of ' + str(round(per, .11)) + '%'
            await self.my_msg(msg, False, True)
        else:
            await self.my_msg('No Trades to Collect', False, True)

        if 'bb' in msg:
            self.bb_trades = [tc for tc in self.bb_trades if not tc['sold']]
        else:
            self.ab_trades = [tc for tc in self.ab_trades if not tc['sold']]

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
        msg = 'List of Bot commands:'
        msg += '\nset cc key - Start process of adding new Craft-Crypto Key'
        msg += '\nreplace key - Replace Craft-Crypto Key'
        msg += '\nset API keys - Add API Keys for Exchanges'
        msg += '\nset tele keys - Add Keys for Telegram Integration'
        msg += '\nset strat - Choose which Strategy for the Bot to follow'
        msg += '\nactivate - Allow the Bot to Trade'
        msg += '\npause - Pause Bot Trading'
        msg += '\nstatus - Status of the Bot'
        msg += '\ntrades - List of trades and their Status'
        msg += '\ndetailed trades - Detailed list of trades and their Status'
        msg += '\nquick trade - Make a manual Buy or Sell'
        msg += '\ncollect - Collect sold Trades and Give Report'
        msg += '\nclear trades - Deletes all Trades in Bot. Does not trade on the Exchange'
        msg += '\nbalance - Display Coin Balances from Exchanges'
        msg += '\nsave - Save Data'
        msg += '\nverbose - Give more detailed running information on the Bot'
        msg += '\neula - Display End User License Agreement'
        msg += '\nFor more information, please visit craft-crypto.com'
        await self.my_msg(msg, False, False)
    else:
        await self.my_msg(
            'Command ' + str(msg) + ' not understood. Use \'help\' for a list of commands.', False,
            False)