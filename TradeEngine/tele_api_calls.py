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
                     {'command': 'accounts', 'description': 'Get update on balances of coins'},
                     {'command': 'trade', 'description': 'Buy/Sell Crypto'},
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

        @self.dp.message_handler(commands=['accounts'])
        async def tele_get_accounts(message: types.Message):
            no_bal = True
            for exchange in self.worker.exchanges:
                ex = self.worker.exchange_selector(exchange)
                if ex.balance:
                    msg = exchange + ' Balance:'
                    for bal in ex.balance:
                        msg += '\n' + bal + ': ' + str(ex.balance[bal])
                    await message.answer(msg)
                    no_bal = False
            if no_bal:
                await message.answer('No Balances Found. Please check API Keys.')

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



