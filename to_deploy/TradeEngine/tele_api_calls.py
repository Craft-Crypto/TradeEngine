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

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import asyncio

c = [{'command': 'start', 'description': 'Start bot and get Chat ID'},
     {'command': 'ping', 'description': 'Check if App is still connected'},
     {'command': 'activate', 'description': 'Allow the Bot to Trade'},
     {'command': 'pause', 'description': 'Pause Bot Trading'},
     {'command': 'trades', 'description': 'Get update on active trades'},
     {'command': 'detailedtrades', 'description': 'Get Detailed update on trades'},
     {'command': 'collect', 'description': 'Clean up completed trades and get report'},
     {'command': 'balance', 'description': 'Get update on balances of coins'},
     {'command': 'quicktrade', 'description': 'Buy/Sell Crypto'},
    ]


# States
class BuySellState(StatesGroup):
    exchange = State()
    kind = State()
    coinpair = State()
    amount = State()  # Will be represented in storage as 'Form:age'
    confirm = State()


class TeleBot(Bot):
    def __init__(self, token, chat_id, worker, **kwargs):#, app, in_q, out_q,
        super(TeleBot, self).__init__(token=token)
        self.token = token
        self.chat_id = chat_id
        self.worker = worker
        self.dp = None

    async def set_commands(self):
        tele_cmds = [{'command': 'start', 'description': 'Start bot and get Chat ID'},
                     {'command': 'ping', 'description': 'Check if App is still connected'},
                     {'command': 'balance', 'description': 'Get update on balances of coins'},
                     {'command': 'trade', 'description': 'Buy/Sell Crypto'},
                     {'command': 'bb_status', 'description': 'Get Status of Basic Bot'},
                     {'command': 'activate_bb', 'description': 'Activate Basic Bot'},
                     {'command': 'pause_bb', 'description': 'Pause Basic Bot'},
                     {'command': 'bb_now', 'description': 'Activate Basic Bot and Evaluate Cards Now'},
                     {'command': 'bb_trades', 'description': 'Get Trades from Basic Bot'},
                     {'command': 'bb_detailed_trades', 'description': 'Get Detailed Trades from Basic Bot'},
                     {'command': 'collect_bb', 'description': 'Clear completed Basic Bot Trades'},
                     {'command': 'sell_positive_bb', 'description': 'Sell positive Basic Bot trades'},

                     {'command': 'activate_ab', 'description': 'Activate Advanced Bot'},
                     {'command': 'pause_ab', 'description': 'Pause Advanced Bot'},
                     {'command': 'ab_trades', 'description': 'Get Trades from Advanced Bot'},
                     {'command': 'ab_detailed_trades', 'description': 'Get Detailed Trades from Advanced Bot'},
                     {'command': 'collect_ab', 'description': 'Clear completed Advanced Bot Trades'},
                     {'command': 'sell_positive_ab', 'description': 'Sell positive Advanced Bot trades'},
                     {'command': 'clock', 'description': 'Get infomation on how to fix timestamp errors'},
                    ]
        await self.set_my_commands(tele_cmds)

    async def stop_bot(self):
        self.dp.stop_polling()

    async def set_dispatcher(self):
        self.dp = Dispatcher(self, storage=MemoryStorage())
        asyncio.ensure_future(self.dp.start_polling())

        @self.dp.message_handler(commands=['ping'])
        async def tele_ping(message: types.Message):
            await message.answer('pong')
    
        @self.dp.message_handler(commands=['start'])
        async def tele_start(message: types.Message):
            # print('here')
            # print(self.worker.a_cbp.balance)
            msg = 'Your Chat ID is: ' + str(message.chat.id)
            await message.answer(msg)
            msg = 'Please copy/paste your Chat ID into TradeCraft Pro'
            await message.answer(msg)

        @self.dp.message_handler(commands=['balance'])
        async def tele_get_accounts(message: types.Message):
            await self.worker.manage_input('balance')

        @self.dp.message_handler(commands=['bb_status'])
        async def bb_status(message: types.Message):
            await self.worker.manage_input('bb status')

        @self.dp.message_handler(commands=['activate_bb'])
        async def activate_bb(message: types.Message):
            await self.worker.manage_input('activate bb')

        @self.dp.message_handler(commands=['pause_bb'])
        async def pause_bb(message: types.Message):
            await self.worker.manage_input('pause bb')

        @self.dp.message_handler(commands=['bb_now'])
        async def bb_now(message: types.Message):
            await self.worker.manage_input('bb now')

        @self.dp.message_handler(commands=['bb_trades'])
        async def bb_trades(message: types.Message):
            await self.worker.manage_input('bb trades')

        @self.dp.message_handler(commands=['bb_detailed_trades'])
        async def bb_detailed_trades(message: types.Message):
            await self.worker.manage_input('bb detailed trades')

        @self.dp.message_handler(commands=['collect_bb'])
        async def collect_bb(message: types.Message):
            await self.worker.manage_input('collect bb')

        @self.dp.message_handler(commands=['sell_positive_bb'])
        async def sell_positive_bb(message: types.Message):
            await self.worker.manage_input('sell positive bb')

        @self.dp.message_handler(commands=['activate_ab'])
        async def activate_ab(message: types.Message):
            await self.worker.manage_input('activate ab')

        @self.dp.message_handler(commands=['pause_ab'])
        async def pause_ab(message: types.Message):
            await self.worker.manage_input('pause ab')

        @self.dp.message_handler(commands=['ab_trades'])
        async def ab_trades(message: types.Message):
            await self.worker.manage_input('ab trades')

        @self.dp.message_handler(commands=['ab_detailed_trades'])
        async def ab_detailed_trades(message: types.Message):
            await self.worker.manage_input('ab detailed trades')

        @self.dp.message_handler(commands=['collect_ab'])
        async def collect_ab(message: types.Message):
            await self.worker.manage_input('collect ab')

        @self.dp.message_handler(commands=['sell_positive_ab'])
        async def sell_positive_ab(message: types.Message):
            await self.worker.manage_input('sell positive ab')

        @self.dp.message_handler(commands=['clock'])
        async def clock_cmd(message: types.Message):
            await self.worker.manage_input('clock')

        @self.dp.message_handler(state='*', commands='cancel')
        @self.dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
        async def cancel_handler(message: types.Message, state: FSMContext):
            """
            Allow user to cancel any action
            """
            current_state = await state.get_state()
            if current_state is None:
                return

            # Cancel state and inform user about it
            await state.finish()
            # And remove keyboard (just in case)
            await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())

        @self.dp.message_handler(commands='trade')
        async def tele_trade_start(message: types.Message):
            """
                Conversation's entry point
                """
            # Set state
            await BuySellState.exchange.set()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add("Binance", "Binance US")
            markup.add('Coinbase Pro', 'FTX')
            markup.add('Kraken', 'Cancel')
            await message.reply("Select an Exchange:", reply_markup=markup)

        @self.dp.message_handler(state=BuySellState.exchange)
        async def tele_trade_exchange(message: types.Message, state: FSMContext):
            if message.text in ['Binance', 'Binance US', 'Coinbase Pro', 'FTX', 'Kraken']:
                await state.update_data(exchange=message.text)
            else:
                await message.reply('Please use the keyboard to select exchange.')
                return

            await BuySellState.next()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add("Buy", "Sell")
            markup.add("Cancel")
            await message.reply("Buy or Sell?", reply_markup=markup)

        @self.dp.message_handler(state=BuySellState.kind)
        async def tele_trade_kind(message: types.Message, state: FSMContext):
            if message.text == 'Buy':
                await state.update_data(kind=True)
            elif message.text == 'Sell':
                await state.update_data(kind=False)
            else:
                await message.reply('Please enter Buy, Sell, or Cancel')
                return

            await BuySellState.next()
            markup = types.ReplyKeyboardRemove()
            await message.reply("Enter a Coin/Pair to trade (Example: BTC/USDT).", reply_markup=markup)

        @self.dp.message_handler(state=BuySellState.coinpair)
        async def tele_trade_coinpair(message: types.Message, state: FSMContext):
            await state.update_data(coinpair=message.text.upper())

            await BuySellState.next()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('5', '10', '25')
            markup.add('35', '50', '75')
            markup.add('100', 'Cancel')
            await message.reply("Choose a % to trade:", reply_markup=markup)

        @self.dp.message_handler(state=BuySellState.amount)
        async def tele_trade_amount(message: types.Message, state: FSMContext):
            await state.update_data(amount=message.text)
            # ask for confirmation

            await BuySellState.next()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('Confirm Trade')
            markup.add('Cancel')
            async with state.proxy() as data:
                if data['kind']:
                    type = 'buy'
                else:
                    type = 'sell'
                msg = ('Confirm ' + data['exchange'] + ' ' + type + ' of ' +
                       str(data['amount']) + '% of ' + data['coinpair'])
                await message.reply(msg, reply_markup=markup)

        @self.dp.message_handler(state=BuySellState.confirm)
        async def tele_trade_confirm(message: types.Message, state: FSMContext):
            if message.text == 'Confirm Trade':
                try:
                    async with state.proxy() as data:
                        await self.worker.buy_sell_now(data['exchange'], data['coinpair'], data['amount'],
                                                       data['kind'], True, percent=True)

                        await state.finish()
                        markup = types.ReplyKeyboardRemove()
                        # await message.reply('Trade Entered', reply_markup=markup)
                except Exception as e:
                    print('error telegram', e)
            else:
                await message.reply('Please Confirm or Cancel Trade.')



