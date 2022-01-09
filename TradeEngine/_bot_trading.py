from helper_functions import is_float, copy_prec
import time
import asyncio
from MarketMath import calculate_market_indicators, determine_buy_sell
from record import Record
from aioconsole import ainput


async def check_bot_cards(self, candle):
    bb_cards = [card for card in self.bb_cards if card.candle == candle]
    tasks = []
    self.bb_active_trades = '0'
    for tc in self.bb_trades:
        if not tc['sold']:
            self.bb_active_trades = str(int(self.bb_active_trades) + 1)

    if self.bb_active and bb_cards:
        for card in bb_cards:
            tasks.append(asyncio.create_task(self.do_check_bot_cards(candle, card, self.bb_trades,
                                                                     self.bb_trade_limit, self.bb_active_trades)))
        data = await asyncio.gather(*tasks)
        # await self.do_check_bot_cards(candle, card, self.bb_trades, self.bb_trade_limit, self.bb_active_trades)
    tasks = []
    self.ab_active_trades = '0'
    for tc in self.ab_trades:
        if not tc['sold']:
            self.ab_active_trades = str(int(self.ab_active_trades) + 1)
    ab_cards = [card for card in self.ab_cards if card.candle == candle]
    if self.ab_active and ab_cards:
        for card in ab_cards:
            tasks.append(asyncio.create_task(self.do_check_bot_cards(candle, card, self.ab_trades,
                                                                     self.ab_trade_limit, self.ab_active_trades)))
        data = await asyncio.gather(*tasks)


async def do_check_bot_cards(self, candle, card, trades, trade_limit, count):
    # We can gain some effeciency by checking on the cards with trades first, and then going on to others. this way if over limit, that is cool.
    ex = self.exchange_selector(card.exchange)
    if card.active: #ex.balance[card.pair] > 0 and card.active:  # Can be better by determining min buy and checking this first before continuing
        for coin in card.coin.split(','):
            cp = coin.strip() + '/' + card.pair
            if cp in ex.symbols:
                # needed_ohlc.append([ex, cp, card.candle, card.my_id])
                msg = 'Starting checks of ' + cp
                await self.my_msg(msg, True, False)
                ohlc = await self.async_get_ohlc(ex, cp, candle, 1000)
                make_buy = False
                make_sell = False
                try:
                    if ohlc:
                        make_buy, make_sell, price = check_card_trade(ex, card, cp, ohlc)
                except Exception as e:
                    msg = 'Error in calculating trade data for ' + cp + ': ' + str(e)
                    await self.my_msg(msg, False, True)
                    card.active = False

                dca_trade = False
                if make_buy:
                    for tc in trades:
                        if (tc.coin == card.coin and tc.pair == card.pair
                                and not tc.sold and tc.exchange == card.exchange):
                            if is_float(tc.buyback_price):
                                if float(tc.now_price) > float(tc.buyback_price):
                                    make_buy = False
                                    msg = 'Wanted to buy {0}, but price is not below buyback price'.format(cp)
                                    await self.my_msg(msg, True, False)
                                else:
                                    dca_trade = True
                            else:
                                make_buy = False
                                msg = 'Wanted to buy {0}, but there is an existing active trade'.format(cp)
                                await self.my_msg(msg, True, False)
                            break

                num_check = True
                if is_float(trade_limit):
                    if float(count) >= float(trade_limit):
                        num_check = False

                # print('3 checks', make_buy, num_check, dca_trade)

                if make_buy and (num_check or dca_trade):
                    if is_float(price):
                        msg = 'Making a Buy for ' + cp
                        await self.my_msg(msg, True, False)
                        count = str(int(count) + 1)
                        await self.make_bot_buy(card)

                        # print('2nd count and limit', count, trade_limit)
                    else:
                        msg = 'Wanted to by ' + cp + ' but no price data yet'
                        await self.my_msg(msg, True, False)

                if make_sell:
                    # if it said make sell, I think all we do is say that it is ready, and let our checker do the rest
                    msg = cp + ' ready to sell.'
                    await self.my_msg(msg, True, False)
                    card.ready_sell = True


def check_card_trade(ex, card, cp, ohlc, *args):
    # print('starting cp', cp)
    closes = [p[4] for p in ohlc if p[5] > 0]
    # print(closes)
    test = '.11111111111'
    test_binance = ex.price_to_precision(cp, test)
    test = copy_prec(test, test_binance, 2)

    card.prec = test
    if card.prec == '':
        card.prec = '.11111111'

    # print('reference price', test, card['prec'], cp)

    indicators = calculate_market_indicators(closes, ohlc, card)

    make_buy, make_sell, p = determine_buy_sell(indicators, card, closes, -2)
    # print(cp, len(closes), len(indicators))
    card.last_update = time.strftime('%I:%M:%S %p %m/%d/%y')
# if not args:
#     self.out_q.put(['update_cc', card])
    # print('ending cp', cp)
    return make_buy, make_sell, p


async def make_bot_buy(self, card, *args):
    # cp for advanced bot is in card. for bb it is in args
    coin = card.coin
    pair = card.pair
    kind = card.kind

    cp = coin + '/' + pair
    ex = self.exchange_selector(card.exchange)
    buy_amt = 0
    await self.a_debit_exchange(ex, 1)

    info = ex.market(cp)
    min_coin_amt = float(info['limits']['amount']['min'])
    min_cost_amt = float(info['limits']['cost']['min'])
    price = float(ex.prices[cp.replace('/', '')])

    if not price:
        msg = kind + ' attempted to buy ' + cp + ' But no price has been recorded.'
        await self.my_msg(msg, True, False)
        card.buy_now = False

    num_coin_on_cost = min_cost_amt / price
    while num_coin_on_cost > min_coin_amt:
        min_coin_amt += float(info['limits']['amount']['min'])

    pair_bal = float(ex.balance[card.pair]) * .99
    msg = 'Balance Data for ' + cp + ': \nPair Balance: ' + str(pair_bal) + '\nMin Trade Amount: ' + str(min_cost_amt)
    await self.my_msg(msg, True, False)

    if pair_bal > min_cost_amt:
        # get how much to buy
        pair_amt = 0  # of pair
        coin_amt = 0  # of coin, what we are going to use to buy
        if is_float(card.pair_per):
            # percentage of balance
            pair_amt = float(card.pair_per) / 100 * pair_bal
            coin_amt = pair_amt / price
            if min_coin_amt > coin_amt:
                coin_amt = min_coin_amt
        elif is_float(card.pair_amt):
            pair_amt = float(card.pair_amt)
            coin_amt = pair_amt / price
            if min_coin_amt > coin_amt:
                coin_amt = min_coin_amt
        elif is_float(card.pair_minmult):
            # pair_amt = float(card.pair_minmult.strip('x')) * min_cost_amt
            coin_amt = float(card.pair_minmult.strip('x')) * min_coin_amt

        coin_amt = float(ex.amount_to_precision(cp, coin_amt * self.sell_mod))

        if coin_amt:
            msg = 'Trade Data for ' + cp + ': \nCoin Amount: ' + str(coin_amt) + '\nPair Amount: ' + str(pair_amt)
            await self.my_msg(msg, True, False)

            try:
                ordr = await ex.create_market_buy_order(cp, coin_amt)
            except Exception as e:
                if 'MIN_NOTIONAL' in str(e) or 'insufficient balance' in str(e) or '1013' in str(e):
                    msg = 'Trade Error: Too Low of trade amount. Trying to trade all...'
                    await self.my_msg(msg, True, False)
                    ordr = await self.try_trade_all(cp, True)
                else:
                    msg = kind + ' error in making buy of ' + cp + ': ' + str(e)
                    await self.my_msg(msg, False, True)
                    ordr = None

            msg = 'Order Details: ' + str(ordr)
            await self.my_msg(msg, True, False)
            if ordr:
                if is_float(ordr['average']):
                    pr = copy_prec(ordr['average'], '.11111111')
                elif is_float(ordr['price']):
                    pr = copy_prec(ordr['price'], '.11111111')
                else:
                    pr = str(ex.prices[cp.replace('/', '')])

                if is_float(ordr['filled']):
                    buy_amount = float(ordr['filled'])
                else:
                    buy_amount = coin_amt

                # Now it is time to add our buy to the stash
                await self.add_trade_card(args, cp, card, pr, buy_amount)

                msg = kind + ' bought ' + str(buy_amount) + ' ' + coin + ' at ' + str(pr) + ' ' + pair + '.'
                await self.my_msg(msg, False, True)
                await self.gather_update_bals(str(ex))
            elif not args:
                card.active = False

            card.buy_now = False

        else:
            msg = '{0} insufficient balance to buy {1}. Attempted to buy {1} with {2} {3}.'.format(kind, cp, str(pair_bal), pair)
            await self.my_msg(msg, False, True)

    # if not args:
    #     for old_card in self.ab_coincards:
    #         if old_card.my_id == card.my_id:
    #             print('FOUND CARDS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    #             old_card.set_record(card.to_dict())

# if card['buy_now']:
#     msg = 'Insufficient balance to buy ' + cp + '. Attempted to buy ' + card['coin']
#     msg += ' with ' + str(pair_bal) + ' ' + card['pair'] + '.'
#     await self.out_q.coro_put(['msg', msg])
# card['buy_now'] = False
# await self.out_q.coro_put(['update_cc', card])


async def add_trade_card(self, is_basic, cp, card, buy_price, buy_amount):
    if is_basic:
        trades = self.bb_trades
    else:
        trades = self.ab_trades

    coin, pair = cp.split('/')

    if is_float(card.dca_buyback_per):
        # look through and see if there is a child
        for dc in trades:
            if cp.replace('/', '') == dc.coin + dc.pair and \
                    card.exchange == dc.exchange and not dc.sold:
                rr = {}
                rr.buy_price = str(buy_price)
                rr.sold_price = '0'
                rr.amount = copy_prec(buy_amount, '.111111111')
                rr.sold = False
                dc.childs.append(rr)
                await self.cal_average_buys()
                return

    t = Record()
    t.set_record(card.to_dict())
    # print('t', t)
    # print('c', card)
    t.coin = coin
    t.pair = pair
    t.amount = copy_prec(buy_amount, '.111111111')
    t.buy_price = str(buy_price)
    t.my_id = await self.get_my_id()
    rr = {'buy_price': str(buy_price),
          'sold_price': '0',
          'amount': copy_prec(buy_amount, '.111111111'),
          'sold': False}
    t.childs.append(rr)
    if is_float(card.sell_per):
        sell = float(buy_price) * (100 + float(card.sell_per)) / 100
        t.sell_price = copy_prec(sell, card.prec)

    if is_float(card.stop_per):
        stop = float(buy_price) * (100 - float(card.stop_per)) / 100
        t.stop_price = copy_prec(stop, card.prec)

    trades.append(t)
    await self.cal_average_buys()

    if is_basic:
         self.bb_trades = trades
    else:
        self.ab_trades = trades


async def update_card_trade_data(self, trade):
    if trade.kind == 'Basic Bot':
        card_data = self.bb_cards
    else:
        card_data = self.ab_cards

    for card in card_data:
        if card.coin == trade.coin and card.pair == trade.pair \
                and card.exchange == trade.exchange:
            cp = card.coin + '/' + card.pair

            if is_float(card.num_trades):
                card.num_trades = str(int(card.num_trades) + 1)
            else:
                card.num_trades = '1'

            if is_float(card.trade_vol):
                new_trade_vol = float(trade.amount) + float(card.trade_vol)
                ex = self.exchange_selector(card.exchange)
                card.trade_vol = str(ex.amount_to_precision(cp, new_trade_vol))
            else:
                card.trade_vol = trade.amount
            # update average buys
            if is_float(card.average_buys):
                mid = float(card.average_buys) * float(card.trade_vol) + float(trade.buy_price) * \
                      float(trade.amount)
                new_avg = mid / (float(trade.amount) + float(card.trade_vol))
                card.average_buys = copy_prec(new_avg, card.prec)
            else:
                card.average_buys = trade.buy_price

            if is_float(card.average_sells):
                mid = float(card.average_sells) * float(card.trade_vol) + float(trade.sold_price) * \
                      float(trade.amount)
                new_avg = mid / (float(trade.amount) + float(card.trade_vol))
                card.average_sells = copy_prec(new_avg, card.prec)
            else:
                card.average_sells = trade.sold_price

            gain = float(card.average_sells) / float(card.average_buys) * 100 - 100
            card.per_gain = str(round(gain, 2))

            break


async def check_trade_sells(self):
    if not self.bb_sells_lock and self.bb_active:
        self.bb_sells_lock = True
        await self.do_check_trade_sells(self.bb_trades)
        self.bb_sells_lock = False

    if not self.ab_sells_lock and self.ab_active:
        self.ab_sells_lock = True
        await self.do_check_trade_sells(self.ab_trades)
        self.ab_sells_lock = False


async def do_check_trade_sells(self, trades):
    for tc in (tc for tc in trades if (not tc.sold and tc.active)):
        sell = False
        # Needs to be updated for BitMEX
        sym = tc.coin + '/' + tc.pair
        ex = self.exchange_selector(tc.exchange)

        try:
            if tc.sell_now:
                sell = True
            else:
                if is_float(tc.stop_price):
                    if float(tc.now_price) <= float(tc.stop_price) and is_float(tc.now_price):
                        # Sell!!! We hit our stop!
                        sell = True

                if is_float(tc.trail_per):
                    if is_float(tc.trail_price) and float(tc.now_price) <= float(tc.trail_price):
                        sell = True
                    elif float(tc.now_price) >= float(tc.sell_price) and not is_float(tc.trail_price):
                        new_trail_price = float(tc.now_price) * (100 - float(tc.trail_per)) / 100
                        tc.trail_price = copy_prec(new_trail_price, tc.now_price, 1)
                    elif is_float(tc.trail_price):
                        # check to see if I need to update trail
                        new_trail_price = float(tc.now_price) * (100 - float(tc.trail_per)) / 100
                        if new_trail_price > float(tc.trail_price):
                            tc.trail_price = copy_prec(new_trail_price, tc.now_price, 1)

                    # if no stop, continue
                    elif not sell:
                        # check if price is ready to go
                        if is_float(tc.now_price) and is_float(tc.sell_price):
                            if float(tc.now_price) >= float(tc.sell_price):
                                sell = True

                        # Check in with Trade's coin card.
                        for card in self.ab_coincards:
                            if card.coin == tc.coin and card.pair == tc.pair and card.exchange == tc.exchange:
                                # the is the combination of all selling parameters
                                sell = card.ready_sell

                                # If the card is set for DCA, and no take profit, but selling on TI, then we
                                # want to be at least even
                                if is_float(card.dca_buyback_per) and sell:
                                    if not float(tc.now_price) > float(tc.buy_price):
                                        sell = False

                        # Checks to see if TI says to sell, but it is under a take profit
                        if is_float(tc.now_price) and is_float(tc.sell_price) and sell:
                            if not float(tc.now_price) >= float(tc.sell_price):
                                sell = False

                # If the bot has logged no price yet, don't sell
                if not is_float(tc.now_price):
                    sell = False

            try:
                if sell:
                    coin_bal = is_float(ex.balance[tc.coin])

            except Exception as e:
                self.update_bals(ex)
                try:
                    coin_bal = is_float(ex.balance[tc.coin])
                except Exception as e:
                    print('No balance for trade')
                    msg = tc.kind + ' ' + tc.coin + ' balance error: ' + str(e)
                    await self.my_msg(msg, False, True)
                    sell = False
                    tc.sell_now = False

            # Finally, we are past all the filters, now we can see if we can make it happen
            if sell:
                # time to sell. let's figure out how much we are selling
                sell_amt = 0
                if len(tc.childs) > 0:
                    for child in tc.childs:
                        sell_amt += float(child.amount)
                else:
                    sell_amt = float(tc.amount)

                if sell_amt > 0:
                    await self.a_debit_exchange(ex, 1)
                    sell_amt = float(ex.amount_to_precision(sym, sell_amt * self.sell_mod))
                    msg = 'Time to Sell ' + sym + '!\n Sell Price: ' + tc.sell_price + '\nCurrent Price: ' + \
                          tc.now_price + '\nBuy Price: ' + tc.buy_price
                    await self.my_msg(msg, True, False)
                    try:
                        ordr = await ex.create_market_sell_order(sym, sell_amt)
                        await self.save()
                    except Exception as e:
                        if 'MIN_NOTIONAL' in str(e) or 'insufficient balance' in str(e) or '1013' in str(e):
                            msg = 'Trade Error: Too Low of trade amount. Trying to trade all...'
                            await self.my_msg(msg, True, False)
                            ordr = await self.try_trade_all(sym, False, ex)
                        else:
                            msg = tc.kind + ' error in checking sell of ' + sym + ': ' + str(e)
                            ordr = None
                            await self.my_msg(msg, False, True)

                    msg = tc.kind + ' Order Details: ' + str(ordr)
                    await self.my_msg(msg, True, False)
                    if ordr:
                        if is_float(ordr['average']):
                            pr = copy_prec(ordr['average'], '.11111111')
                        elif is_float(ordr['price']):
                            pr = copy_prec(ordr['price'], '.11111111')
                        else:
                            pr = str(ex.prices[sym.replace('/', '')])

                        if is_float(ordr['filled']):
                            sold_amount = float(ordr['filled'])
                        else:
                            sold_amount = sell_amt

                        msg = tc.kind + ' sold ' + str(sold_amount) + ' ' + tc.coin + ' at ' + str(pr) + ' ' + tc.pair
                        await self.my_msg(msg, False, True)

                        tc.sold = True
                        tc.sold_price = pr
                        tc.sell_now = False
                        tc.now_price = pr
                        tc.amount = str(sold_amount)
                        gain = float(tc.sold_price) / float(tc.buy_price) * 100 - 100
                        tc.gl_per = str(round(gain, 2))
                    else:
                        tc.sell_now = False
                        tc.active = False
                        tc.sold_price = '0'
                        tc.gl_per = 'Error'
                        tc.now_price = '0'
                        tc.sold = True

                    await self.update_card_trade_data(tc)
                    await self.gather_update_bals(str(ex))

        except Exception as e:
            print('sell error', e)
            msg = 'Error in checking ' + tc.kind + ' sell of ' + sym + ': ' + str(e)
            await self.my_msg(msg, False, True)
            tc.sell_now = False
            tc.active = False
            tc.sold_price = '0'
            tc.gl_per = 'Error'
            tc.now_price = '0'
            tc.sold = True


async def quick_trade(self, *args):
    try:
        kind = None
        ex = None
        cp = None
        amount = None
        if not args:
            await self.my_msg('*******', False, False)
            await self.my_msg('Select an Exchange to Trade:', False, False)
            await self.my_msg('1 - Binance', False, False)
            await self.my_msg('2 - Binance US', False, False)
            await self.my_msg('3 - BitMEX', False, False)
            await self.my_msg('4 - Coinbase Pro', False, False)
            await self.my_msg('5 - FTX', False, False)
            await self.my_msg('6 - Kraken', False, False)
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
            try:
                ex = self.exchange_selector(ex)
            except Exception as e:
                await self.my_msg('Error in Exchange Selection', False, False)
                return

            await self.my_msg('Enter \'buy\' or \'sell\'', False, False)
            msg = await ainput(">")
            if msg.upper().strip() == 'buy':
                kind = 'buy'
            else:
                kind = 'sell'

            await self.my_msg('Enter a Coin/Pair to trade (Example: BTC/USDT)', False, False)
            msg = await ainput(">")
            cp = msg.strip().upper()

            await self.my_msg('Choose a % to trade (Example: 5, 10, 50, 75, 100....):', False, False)
            msg = await ainput(">")
            amount = msg.strip().strip('%')

        else:
            data = args[0]
            kind = data[0]
            ex = data[1]
            cp = data[2]
            amount = data[3]

        if kind == 'buy':
            # 'quick_buy': #ex, pair, cp, %
            amount = float(ex.balance[cp.split('/')[1]]) * float(amount) / 100
            amount = amount / float(ex.prices[cp.replace('/', '')])

        else:
            amount = float(ex.balance[cp.split('/')[0]]) * float(amount) / 100
        amount = ex.amount_to_precision(cp, amount * .99)

        await self.a_debit_exchange(ex, 1)

        price = float(ex.prices[cp.replace('/', '')])

        if not price:
            msg = 'Attempted to Quick Trade ' + cp + ' But no price has been recorded.'
            await self.my_msg(msg, True, False)
        else:
            try:
                if kind == 'buy':
                    ordr = await ex.create_market_buy_order(cp, amount)
                else:
                    ordr = await ex.create_market_sell_order(cp, amount)
            except Exception as e:
                    msg = 'Error in Quick Trade of ' + cp + ': ' + str(e)
                    await self.my_msg(msg, False, True)
                    ordr = None
                    self.pause_msg = False

            msg = 'Quick Trade Order Details: ' + str(ordr)
            await self.my_msg(msg, True, False)
            if ordr:
                if is_float(ordr['average']):
                    pr = copy_prec(ordr['average'], '.11111111')
                elif is_float(ordr['price']):
                    pr = copy_prec(ordr['price'], '.11111111')
                else:
                    pr = str(ex.prices[cp.replace('/', '')])

                if is_float(ordr['filled']):
                    amount = float(ordr['filled'])

                if kind == 'buy':
                    msg = 'Bought ' + str(amount) + ' ' + cp + ' at ' + str(pr) + '.'
                else:
                    msg = 'Sold ' + str(amount) + ' ' + cp + ' at ' + str(pr) + '.'

                await self.my_msg(msg, False, True)
                await self.gather_update_bals()

    except Exception as e:
        # print('sell all error', e)
        if 'MIN_NOTIONAL' in str(e) or 'insufficient balance' in str(e) or '1013' in str(e):
            # print('too low')
            msg = 'Quick Trade Amount too low for Exchange.'
            await self.my_msg(msg, False, True)
        else:
            msg = 'Error in Quick Trade ' + cp + ': ' + str(e)
            await self.my_msg(msg, False, True)

