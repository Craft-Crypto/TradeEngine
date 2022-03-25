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

from CraftCrypto_Helpers.Helpers import is_float, copy_prec, sym_to_cp
import time
import asyncio
from MarketMath import calculate_market_indicators, determine_buy_sell
from CraftCrypto_Helpers.BaseRecord import BaseRecord
from aioconsole import ainput
from .trade_api_calls import broadcast


async def add_mt_tab(self, cp, exchange, *args):
    print('maybe')
    new_tab = BaseRecord()
    new_tab.coin, new_tab.pair = sym_to_cp(cp)
    new_tab.symbol = cp
    new_tab.exchange = exchange
    new_tab.my_id = await self.get_my_id()
    self.mt_cards.append(new_tab)
    await broadcast({'action': 'add_mt_tab', 'tab': new_tab.to_dict()})
    print('there')

def search_add_follow_up(parent, my_id, new_trade):
    # if parent['my_id'] == my_id:
    #     parent['childs'].append(replacement)
    #     return parent
    # else:
    try:
        for child in parent['childs']:
            found_id = None
            if child['my_id'] == my_id:
                found_id = child
                child['childs'].append(new_trade)
                break
                # return found_id
            if child['childs']:
                search_add_follow_up(child, my_id, new_trade)
            # if found_id:
                # return found_id
    except:
        for child in parent.childs:
            found_id = None
            if child['my_id'] == my_id:
                found_id = child
                child['childs'].append(new_trade)
                break
                # return found_id
            if child['childs']:
                search_add_follow_up(child, my_id, new_trade)


def search_edit_trade(parent, new_trade):
    try:
        for i, child in enumerate(parent['childs']):
            print('looking through', parent['childs'])
            if child['my_id'] == new_trade['my_id']:
                print('found edit')
                parent['childs'][i] = new_trade
                break
            if child['childs']:
                search_edit_trade(child, new_trade)
    except:
        for i, child in enumerate(parent.childs):
            print('looking through 222', parent.childs)
            if child['my_id'] == new_trade['my_id']:
                print('found edit222')
                parent.childs[i] = new_trade
                break
            if child['childs']:
                search_edit_trade(child, new_trade)


async def add_mt_trade(self, tab_id, new_trade_data, follow_up_id, *args):
    print(tab_id, new_trade_data['my_id'])
    for tab in self.mt_cards:
        #find which parent it belongs to
        if tab.my_id == tab_id:
            print('found parent', len(tab.childs), new_trade_data, tab.childs)
            if new_trade_data['my_id'] == '0':
                print('found new trade')
                new_trade_data['my_id'] = await self.get_my_id()
                if follow_up_id:
                    print('it is follow up')
                    search_add_follow_up(tab, follow_up_id, new_trade_data)
                else:
                    tab.childs.append(new_trade_data)
            else:
                print('need to edit')
                search_edit_trade(tab, new_trade_data)
            # #find if the trade already is there an if I need to edit
            # add_new = True
            # try:
            #     if follow_up_id:
            #         add_trade_childs(tab.childs, follow_up_id, new_trade_data)
            #     else:
            #         for i, trade in enumerate(tab.childs):
            #             print(i, trade['my_id'], new_trade_data['my_id'])
            #             if new_trade_data['my_id'] == trade['my_id']:
            #                 print('found new')
            #                 # tab.childs[i] = new_trade_data
            #                 trade = new_trade_data
            #                 add_new = False
            #                 break
            #
            # except Exception as e:
            #     print(e)
            # print(add_new)
            # if add_new:
            #     print('add new')
            #     tab.childs.append(new_trade_data)
            print('broadcasting')
            await broadcast({'action': 'add_mt_trade', 'tab': tab.to_dict()})

###############################################################
    def get_tab_prices(self, *args):
        return
        tradetabs = self.ids.trade_tabs.get_tab_list()
        for tt in tradetabs:
            t = tt.tab
            self.app.ws_q.put_nowait({'action': 'get_manual_price',
                                  'exchange': t.exchange,
                                  'symbol': t.symbol})

    def check_manual_trades(self, *args):
        tradetabs = self.ids.trade_tabs.get_tab_list()
        for tt in tradetabs:
            t = tt.tab
            if t.active and is_float(t.now_price):
                # print('checking man trade', cp)
                for trade in t.ids.trade_box.children:
                    if 'Loop' in trade.kind:
                        self.check_loop(trade, t)

                    else:
                        if trade.sold:
                            self.check_trade_children(trade, t)
                        else:
                            self.check_my_trade(trade, t)
                    # t.error = '0'

            # except Exception as e:
            #     # t.error += 1
            #     print(e)
                # if t.error > 2:
                #     t.active = False
                #     if 'insufficient balance' in str(e):
                #         msg = 'Not enough balance for Manual Trade in ' + t.coin + '/' + t.pair
                #         self.out_q.put(['msg', msg])
                #     else:
                #         msg = 'Manual Trade Error in ' + t.coin + '/' + t.pair + ': ' + str(e)
                #         self.out_q.put(['msg', msg])

    def check_loop(self, trade, tab):
        # cp = trade.coin + '/' + trade.pair
        cp = trade.symbol
        now_price = float(tab.now_price)
        buy_price = float(trade.buy_price)
        sell_price = float(trade.take_profit_price)
        # leverage = float(trade.leverage)

        if 'Market' in trade.kind:
            if trade.buy_enabled and now_price <= buy_price:
                self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                      'amount': trade.trade_amount, 'buy': True, 'my_id': trade.my_id})
                trade.buy_enabled = False
                trade.sell_enabled = True

            elif trade.sell_enabled and now_price >= sell_price:
                self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                      'amount': trade.trade_amount, 'buy': False, 'my_id': trade.my_id})
                trade.sell_enabled = False
                trade.buy_enabled = True

        else:
            # print(trade.buy_enabled, trade.sell_enabled, trade.buy_trade_id)
            if trade.buy_enabled and not trade.buy_trade_id:
                self.app.ws_q.put_nowait({'action': 'create_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                      'buy': True, 'stop': False, 'amount': trade.trade_amount,
                                      'price': trade.buy_price, 'my_id': trade.my_id})
                trade.buy_trade_id = '...'
                trade.buy_enabled = False
                trade.bought_price = ''
            elif not trade.buy_trade_id in ['...', 'Error']:
                self.app.ws_q.put_nowait({'action': 'check_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                      'trade_id': trade.buy_trade_id, 'my_id': trade.my_id, 'is_buy': True})

            if trade.sell_enabled and not trade.sell_trade_id:
                self.app.ws_q.put_nowait({'action': 'create_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                      'buy': False, 'stop': False, 'amount': trade.trade_amount,
                                      'price': trade.take_profit_price, 'my_id': trade.my_id})
                trade.sell_trade_id = '...'
                trade.sell_enabled = False
                trade.sold_price = ''
            elif not trade.sell_trade_id in ['...', 'Error']:
                self.app.ws_q.put_nowait({'action': 'check_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                      'trade_id': trade.sell_trade_id, 'my_id': trade.my_id, 'is_buy': False})

    def check_my_trade(self, trade, tab):
        # cp = tab.symbol
        # now_price = float(tab.now_price)
        # price = float(trade.now_price)
        # amount = float(trade.trade_amount)
        # ex = tab.exchange
        ordr = ''
        # print(trade.kind, amount, price, trade.trail_per)
        now_price = float(tab.now_price)
        trade_price = float(trade.trade_price)
        try:
            trail_price = float(trade.trail_price)
        except Exception as e:
            trail_price = '0'

        try:
            trail_per = float(trade.trail_per)
        except Exception as e:
            trail_per = trail_per = '0'

        try:
            if 'Limit' in trade.kind:
                if not trade.trade_id:
                    self.app.ws_q.put_nowait({'action': 'create_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                          'buy': trade.is_buy, 'stop': False, 'amount': trade.trade_amount,
                                          'price': trade.trade_price, 'my_id': trade.my_id})
                    trade.trade_id = '...'
                elif not trade.trade_id in ['...', 'Error']:
                    self.app.ws_q.put_nowait({'action': 'check_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                          'trade_id': trade.trade_id, 'my_id': trade.my_id})

            else:
                if trade.is_stop:
                    if trade.is_buy:
                        if now_price >= trade_price:
                            print('I need to Buy')
                            trade.sold = True
                            self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                                  'amount': trade.trade_amount, 'buy': True, 'my_id': trade.my_id})

                    else:
                        if now_price <= trade_price:
                            # self.in_q.put(['manual_sell', ex, cp, amount])
                            trade.sold = True
                            # trade.trade_price = str(now_price)
                            print('I need to sell')
                            self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                                  'amount': trade.trade_amount, 'buy': False, 'my_id': trade.my_id})

                elif is_float(trail_per):
                    if trade.is_buy:
                        if is_float(trail_price) and now_price >= trail_price:
                            # self.in_q.put(['manual_buy', ex, cp, amount])
                            trade.sold = True
                            self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                                  'amount': trade.trade_amount, 'buy': True, 'my_id': trade.my_id})
                            # trade.trade_price = str(now_price)
                            print('trailing buy')

                        elif now_price <= trade_price and not is_float(trail_price):
                            new_trail_price = now_price * (100 + trail_per) / 100
                            trade.trail_price = copy_prec(new_trail_price, now_price, 1)

                        elif is_float(trail_price):
                            # check to see if I need to update trail
                            new_trail_price = now_price * (100 + trail_per) / 100
                            if new_trail_price < trail_price:
                                trade.trail_price = copy_prec(new_trail_price, now_price, 1)

                    else:
                        if is_float(trail_price) and now_price <= trail_price:
                            # self.in_q.put(['manual_buy', ex, cp, amount])
                            trade.sold = True
                            self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                                  'amount': trade.trade_amount, 'buy': False, 'my_id': trade.my_id})
                            # trade.trade_price = str(now_price)
                            print('trailing sell')

                        elif now_price >= trade_price and not is_float(trail_price):
                            new_trail_price = now_price * (100 - trail_per) / 100
                            trade.trail_price = copy_prec(new_trail_price, now_price, 1)

                        elif is_float(trail_price):
                            # check to see if I need to update trail
                            new_trail_price = now_price * (100 - trail_per) / 100
                            if new_trail_price > trail_price:
                                trade.trail_price = copy_prec(new_trail_price, now_price, 1)

                else:
                    if trade.is_buy:
                        print(1)
                        if now_price <= trade_price:
                            # self.in_q.put(['manual_buy', ex, cp, amount])
                            trade.sold = True
                            self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                                  'amount': trade.trade_amount, 'buy': True, 'my_id': trade.my_id})
                            # trade.trade_price = str(now_price)
                            print('normal buy')

                    else:
                        print(12)
                        # print('here', now_price, price)
                        if now_price >= trade_price:
                            # self.in_q.put(['manual_sell', ex, cp, amount])
                            trade.sold = True
                            self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                                  'amount': trade.trade_amount, 'buy': False, 'my_id': trade.my_id})
                            # trade.trade_price = str(now_price)
                            print('normal Sell')

                # if trade.trail_price == '0':
                #     trail_trig = now_price * (100 + trail_per) / 100
                #     trade.trail_price = str(now_price)
                #     trade.trail_trig = copy_prec(trail_trig, tab.prec, 1)
                #     trade.update()
                #
                # # check for a sell
                # if now_price >= trail_trig > 0:
                #     self.in_q.put(['manual_buy', ex, cp, amount])
                #
                # # update trigger price
                # if trail_price > now_price:
                #     trail_trig = now_price * (100 + trail_per) / 100
                #     trade.trail_price = str(now_price)
                #     trade.trail_trig = str(self.binance.price_to_precision(cp, trail_trig))
                # # print(trail_price, trail_trig, trail_per)
                # if trade.trail_price == '0':
                #     trail_trig = now_price * (100 - trail_per) / 100
                #     trade.trail_price = str(now_price)
                #     trade.trail_trig = str(self.binance.price_to_precision(cp, trail_trig))
                #     trade.update()
                #
                # # check for a sell
                # if now_price <= trail_trig > 0:
                #     self.in_q.put(['manual_sell', ex, cp, amount])
                #
                # # update trigger price
                # if trail_price < now_price:
                #     trail_trig = now_price * (100 - trail_per) / 100
                #     trade.trail_price = str(now_price)
                #     trade.trail_trig = str(self.binance.price_to_precision(cp, trail_trig))
                #
                #     trade.update()
            trade.update()
        except Exception as e:
            print('sell error', e)
            if 'MIN_NOTIONAL' in str(e) or '-10' in str(e) or 'insufficient balance' in str(e):
                print('too low')
                msg = 'Not enough balance for trade order of ' + trade.coin + '/' + trade.pair
                self.add_msg(msg, to_tele=True)
            else:
                msg = 'Trade error: ' + str(e)
                self.add_msg(msg, to_tele=True)
                raise e

    def check_trade_children(self, trade, tab):
        for child in trade.ids.follow_up.children:
            if child.sold:
                self.check_trade_children(child, tab)
            else:
                self.check_my_trade(child, tab)

    def update_manual_trades(self, data):
        tradetabs = self.ids.trade_tabs.get_tab_list()
        my_id = data['my_id']
        for tt in tradetabs:
            t = tt.tab
            for trade in t.ids.trade_box.children:
                if 'Loop' in trade.kind:
                    if trade.my_id == my_id:
                        if 'trade_price' in data:
                            if data['is_buy']:
                                trade.bought_price = data['trade_price']
                            else:
                                trade.sold_price = data['trade_price']
                        if 'trade_id' in data:
                            if data['is_buy']:
                                trade.buy_trade_id = data['trade_id']
                            else:
                                trade.sell_trade_id = data['trade_id']
                        if 'status' in data:
                            if data['is_buy']:
                                if data['status'] == 'canceled':
                                    self.add_msg(f'Loop Limit order {trade.buy_trade_id} canceled.')
                                    trade.buy_trade_id = ''
                                    trade.buy_enabled = True
                                if data['status'] == 'closed' and not is_float(trade.bought_price) and not trade.buy_enabled:
                                    self.add_msg(f'Loop Limit order {trade.buy_trade_id} closed.')
                                    trade.bought_price = trade.buy_price
                                    if is_float(trade.sold_price):
                                        trade.sold_price = ''
                                        trade.sell_trade_id = ''

                                        trade.sell_enabled = True
                            else:
                                if data['status'] == 'canceled':
                                    self.add_msg(f'Loop Limit order {trade.sell_trade_id} canceled.')
                                    trade.sell_trade_id = ''
                                    trade.sell_enabled = True
                                if data['status'] == 'closed' and not is_float(trade.sold_price) and not trade.sell_enabled:
                                    self.add_msg(f'Loop Limit order {trade.sell_trade_id} closed.')
                                    trade.sold_price = trade.take_profit_price
                                    if is_float(trade.bought_price):
                                        trade.bought_price = ''
                                        trade.buy_trade_id = ''
                                        trade.buy_enabled = True
                        trade.update()
                        break
                else:
                    if trade.my_id == my_id:
                        if 'trade_price' in data:
                            trade.trade_done_price = data['trade_price']
                        if 'trade_id' in data:
                            trade.trade_id = data['trade_id']
                        if 'status' in data:
                            if data['status'] == 'canceled':
                                self.add_msg(f'Limit order {trade.trade_id} canceled.')
                                trade.trade_id = ''
                            if data['status'] == 'closed':
                                self.add_msg(f'Limit order {trade.trade_id} closed.')
                                trade.sold = True
                                trade.trade_done_price = trade.trade_price
                        trade.update()
                        break
                    else:
                        self.update_trade_children(trade, my_id, data)

    def update_trade_children(self, trade, my_id, data):
        for child in trade.ids.follow_up.children:
            if child.my_id == my_id:
                if 'trade_price' in data:
                    trade.trade_done_price = data['trade_price']
                if 'trade_id' in data:
                    trade.trade_id = data['trade_id']
            else:
                self.check_trade_children(child)
##########################################################
 # t.my_parent = self
        # t.my_id = 'manualtrade' + str(time.time())

        # t.update()
        # self.save()

        # if self.target and not self.edit:
        #     self.target.childs.append(t.get_record())
        #     # print('here', self.target.my_id,)
        #     # print(t.get_record(), )
        #     # print(self.target.childs)
        #     self.target.update()
        #
        #     # self.target.ids.follow_up.add_widget(t)
        # elif not self.edit:
        #     self.ids.trade_box.add_widget(t)





def check_manual_trades(self, *args):
    tradetabs = self.ids.trade_tabs.get_tab_list()
    for tt in tradetabs:
        t = tt.tab
        if t.active and is_float(t.now_price):
            # print('checking man trade', cp)
            for trade in t.ids.trade_box.children:
                if 'Loop' in trade.kind:
                    self.check_loop(trade, t)

                else:
                    if trade.sold:
                        self.check_trade_children(trade, t)
                    else:
                        self.check_my_trade(trade, t)
                # t.error = '0'

        # except Exception as e:
        #     # t.error += 1
        #     print(e)
        # if t.error > 2:
        #     t.active = False
        #     if 'insufficient balance' in str(e):
        #         msg = 'Not enough balance for Manual Trade in ' + t.coin + '/' + t.pair
        #         self.out_q.put(['msg', msg])
        #     else:
        #         msg = 'Manual Trade Error in ' + t.coin + '/' + t.pair + ': ' + str(e)
        #         self.out_q.put(['msg', msg])


def check_loop(self, trade, tab):
    # cp = trade.coin + '/' + trade.pair
    cp = trade.symbol
    now_price = float(tab.now_price)
    buy_price = float(trade.buy_price)
    sell_price = float(trade.take_profit_price)
    # leverage = float(trade.leverage)

    if 'Market' in trade.kind:
        if trade.buy_enabled and now_price <= buy_price:
            self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                      'amount': trade.trade_amount, 'buy': True, 'my_id': trade.my_id})
            trade.buy_enabled = False
            trade.sell_enabled = True

        elif trade.sell_enabled and now_price >= sell_price:
            self.app.ws_q.put_nowait({'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                                      'amount': trade.trade_amount, 'buy': False, 'my_id': trade.my_id})
            trade.sell_enabled = False
            trade.buy_enabled = True

    else:
        # print(trade.buy_enabled, trade.sell_enabled, trade.buy_trade_id)
        if trade.buy_enabled and not trade.buy_trade_id:
            self.app.ws_q.put_nowait({'action': 'create_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                      'buy': True, 'stop': False, 'amount': trade.trade_amount,
                                      'price': trade.buy_price, 'my_id': trade.my_id})
            trade.buy_trade_id = '...'
            trade.buy_enabled = False
            trade.bought_price = ''
        elif not trade.buy_trade_id in ['...', 'Error']:
            self.app.ws_q.put_nowait({'action': 'check_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                      'trade_id': trade.buy_trade_id, 'my_id': trade.my_id, 'is_buy': True})

        if trade.sell_enabled and not trade.sell_trade_id:
            self.app.ws_q.put_nowait({'action': 'create_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                      'buy': False, 'stop': False, 'amount': trade.trade_amount,
                                      'price': trade.take_profit_price, 'my_id': trade.my_id})
            trade.sell_trade_id = '...'
            trade.sell_enabled = False
            trade.sold_price = ''
        elif not trade.sell_trade_id in ['...', 'Error']:
            self.app.ws_q.put_nowait({'action': 'check_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                      'trade_id': trade.sell_trade_id, 'my_id': trade.my_id, 'is_buy': False})


def check_my_trade(self, trade, tab):
    # cp = tab.symbol
    # now_price = float(tab.now_price)
    # price = float(trade.now_price)
    # amount = float(trade.trade_amount)
    # ex = tab.exchange
    ordr = ''
    # print(trade.kind, amount, price, trade.trail_per)
    now_price = float(tab.now_price)
    trade_price = float(trade.trade_price)
    try:
        trail_price = float(trade.trail_price)
    except Exception as e:
        trail_price = '0'

    try:
        trail_per = float(trade.trail_per)
    except Exception as e:
        trail_per = trail_per = '0'

    try:
        if 'Limit' in trade.kind:
            if not trade.trade_id:
                self.app.ws_q.put_nowait({'action': 'create_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                          'buy': trade.is_buy, 'stop': False, 'amount': trade.trade_amount,
                                          'price': trade.trade_price, 'my_id': trade.my_id})
                trade.trade_id = '...'
            elif not trade.trade_id in ['...', 'Error']:
                self.app.ws_q.put_nowait({'action': 'check_limit', 'exchange': tab.exchange, 'cp': trade.symbol,
                                          'trade_id': trade.trade_id, 'my_id': trade.my_id})

        else:
            if trade.is_stop:
                if trade.is_buy:
                    if now_price >= trade_price:
                        print('I need to Buy')
                        trade.sold = True
                        self.app.ws_q.put_nowait(
                            {'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                             'amount': trade.trade_amount, 'buy': True, 'my_id': trade.my_id})

                else:
                    if now_price <= trade_price:
                        # self.in_q.put(['manual_sell', ex, cp, amount])
                        trade.sold = True
                        # trade.trade_price = str(now_price)
                        print('I need to sell')
                        self.app.ws_q.put_nowait(
                            {'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                             'amount': trade.trade_amount, 'buy': False, 'my_id': trade.my_id})

            elif is_float(trail_per):
                if trade.is_buy:
                    if is_float(trail_price) and now_price >= trail_price:
                        # self.in_q.put(['manual_buy', ex, cp, amount])
                        trade.sold = True
                        self.app.ws_q.put_nowait(
                            {'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                             'amount': trade.trade_amount, 'buy': True, 'my_id': trade.my_id})
                        # trade.trade_price = str(now_price)
                        print('trailing buy')

                    elif now_price <= trade_price and not is_float(trail_price):
                        new_trail_price = now_price * (100 + trail_per) / 100
                        trade.trail_price = copy_prec(new_trail_price, now_price, 1)

                    elif is_float(trail_price):
                        # check to see if I need to update trail
                        new_trail_price = now_price * (100 + trail_per) / 100
                        if new_trail_price < trail_price:
                            trade.trail_price = copy_prec(new_trail_price, now_price, 1)

                else:
                    if is_float(trail_price) and now_price <= trail_price:
                        # self.in_q.put(['manual_buy', ex, cp, amount])
                        trade.sold = True
                        self.app.ws_q.put_nowait(
                            {'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                             'amount': trade.trade_amount, 'buy': False, 'my_id': trade.my_id})
                        # trade.trade_price = str(now_price)
                        print('trailing sell')

                    elif now_price >= trade_price and not is_float(trail_price):
                        new_trail_price = now_price * (100 - trail_per) / 100
                        trade.trail_price = copy_prec(new_trail_price, now_price, 1)

                    elif is_float(trail_price):
                        # check to see if I need to update trail
                        new_trail_price = now_price * (100 - trail_per) / 100
                        if new_trail_price > trail_price:
                            trade.trail_price = copy_prec(new_trail_price, now_price, 1)

            else:
                if trade.is_buy:
                    print(1)
                    if now_price <= trade_price:
                        # self.in_q.put(['manual_buy', ex, cp, amount])
                        trade.sold = True
                        self.app.ws_q.put_nowait(
                            {'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                             'amount': trade.trade_amount, 'buy': True, 'my_id': trade.my_id})
                        # trade.trade_price = str(now_price)
                        print('normal buy')

                else:
                    print(12)
                    # print('here', now_price, price)
                    if now_price >= trade_price:
                        # self.in_q.put(['manual_sell', ex, cp, amount])
                        trade.sold = True
                        self.app.ws_q.put_nowait(
                            {'action': 'buy_sell_now', 'cp': trade.symbol, 'exchange': tab.exchange,
                             'amount': trade.trade_amount, 'buy': False, 'my_id': trade.my_id})
                        # trade.trade_price = str(now_price)
                        print('normal Sell')

            # if trade.trail_price == '0':
            #     trail_trig = now_price * (100 + trail_per) / 100
            #     trade.trail_price = str(now_price)
            #     trade.trail_trig = copy_prec(trail_trig, tab.prec, 1)
            #     trade.update()
            #
            # # check for a sell
            # if now_price >= trail_trig > 0:
            #     self.in_q.put(['manual_buy', ex, cp, amount])
            #
            # # update trigger price
            # if trail_price > now_price:
            #     trail_trig = now_price * (100 + trail_per) / 100
            #     trade.trail_price = str(now_price)
            #     trade.trail_trig = str(self.binance.price_to_precision(cp, trail_trig))
            # # print(trail_price, trail_trig, trail_per)
            # if trade.trail_price == '0':
            #     trail_trig = now_price * (100 - trail_per) / 100
            #     trade.trail_price = str(now_price)
            #     trade.trail_trig = str(self.binance.price_to_precision(cp, trail_trig))
            #     trade.update()
            #
            # # check for a sell
            # if now_price <= trail_trig > 0:
            #     self.in_q.put(['manual_sell', ex, cp, amount])
            #
            # # update trigger price
            # if trail_price < now_price:
            #     trail_trig = now_price * (100 - trail_per) / 100
            #     trade.trail_price = str(now_price)
            #     trade.trail_trig = str(self.binance.price_to_precision(cp, trail_trig))
            #
            #     trade.update()
        trade.update()
    except Exception as e:
        print('sell error', e)
        if 'MIN_NOTIONAL' in str(e) or '-10' in str(e) or 'insufficient balance' in str(e):
            print('too low')
            msg = 'Not enough balance for trade order of ' + trade.coin + '/' + trade.pair
            self.add_msg(msg, to_tele=True)
        else:
            msg = 'Trade error: ' + str(e)
            self.add_msg(msg, to_tele=True)
            raise e


def check_trade_children(self, trade, tab):
    for child in trade.ids.follow_up.children:
        if child.sold:
            self.check_trade_children(child, tab)
        else:
            self.check_my_trade(child, tab)


def update_manual_trades(self, data):
    tradetabs = self.ids.trade_tabs.get_tab_list()
    my_id = data['my_id']
    for tt in tradetabs:
        t = tt.tab
        for trade in t.ids.trade_box.children:
            if 'Loop' in trade.kind:
                if trade.my_id == my_id:
                    if 'trade_price' in data:
                        if data['is_buy']:
                            trade.bought_price = data['trade_price']
                        else:
                            trade.sold_price = data['trade_price']
                    if 'trade_id' in data:
                        if data['is_buy']:
                            trade.buy_trade_id = data['trade_id']
                        else:
                            trade.sell_trade_id = data['trade_id']
                    if 'status' in data:
                        if data['is_buy']:
                            if data['status'] == 'canceled':
                                self.add_msg(f'Loop Limit order {trade.buy_trade_id} canceled.')
                                trade.buy_trade_id = ''
                                trade.buy_enabled = True
                            if data['status'] == 'closed' and not is_float(
                                    trade.bought_price) and not trade.buy_enabled:
                                self.add_msg(f'Loop Limit order {trade.buy_trade_id} closed.')
                                trade.bought_price = trade.buy_price
                                if is_float(trade.sold_price):
                                    trade.sold_price = ''
                                    trade.sell_trade_id = ''

                                    trade.sell_enabled = True
                        else:
                            if data['status'] == 'canceled':
                                self.add_msg(f'Loop Limit order {trade.sell_trade_id} canceled.')
                                trade.sell_trade_id = ''
                                trade.sell_enabled = True
                            if data['status'] == 'closed' and not is_float(trade.sold_price) and not trade.sell_enabled:
                                self.add_msg(f'Loop Limit order {trade.sell_trade_id} closed.')
                                trade.sold_price = trade.take_profit_price
                                if is_float(trade.bought_price):
                                    trade.bought_price = ''
                                    trade.buy_trade_id = ''
                                    trade.buy_enabled = True
                    trade.update()
                    break
            else:
                if trade.my_id == my_id:
                    if 'trade_price' in data:
                        trade.trade_done_price = data['trade_price']
                    if 'trade_id' in data:
                        trade.trade_id = data['trade_id']
                    if 'status' in data:
                        if data['status'] == 'canceled':
                            self.add_msg(f'Limit order {trade.trade_id} canceled.')
                            trade.trade_id = ''
                        if data['status'] == 'closed':
                            self.add_msg(f'Limit order {trade.trade_id} closed.')
                            trade.sold = True
                            trade.trade_done_price = trade.trade_price
                    trade.update()
                    break
                else:
                    self.update_trade_children(trade, my_id, data)


def update_trade_children(self, trade, my_id, data):
    for child in trade.ids.follow_up.children:
        if child.my_id == my_id:
            if 'trade_price' in data:
                trade.trade_done_price = data['trade_price']
            if 'trade_id' in data:
                trade.trade_id = data['trade_id']
        else:
            self.check_trade_children(child)