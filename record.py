from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Any

@dataclass_json
@dataclass
class Record:
    # Base Information
    children: Any = ''  # Follow up trades, DCA Trades, etc. changes to list
    my_id: str = '0'
    symbol: str = 'BTC/USD'
    exchange: str = 'Binance'
    ex_icon: str = 'Binance_icon.jpg'
    coin: str = 'BTC'
    pair: str = 'USD'
    candle: str = '1m'
    status: str = ''
    active: bool = False
    error: str = ''
    last_update: str = ''

    # Amount to Buy
    pair_per: str = ''
    pair_amt: str = ''
    pair_minmult: str = ''

    # Selling Parameters
    take_profit_per: str = '0'
    take_profit_price: str = '0'
    stop_per: str = '0'
    stop_price: str = '0'
    trail_per: str = '0'
    trail_price: str = '0'
    dca_buyback_per: str = '0'
    dca_buyback_price: str = '0'

    # Trade Details
    trade_amount: str = '0'
    buy_price: str = '0'
    sold_price: str = '0'
    gl_per: str = '0'
    now_price: str = '0'
    trade_id: str = '0'
    buy_trade_id: str = '0'
    sell_trade_id: str = '0'
    kind: str = ''  # market, limit, loop, strat name for basic, NEED TO PUT ADVANCED
    is_buy: bool = True  # false is sell
    ready_sell: bool = False  # for all the trading data
    leverage: str = '0'
    sell_now: bool = False
    buy_now: bool = False

    # Trading Pair Details
    coin_bal: str = '0'
    pair_bal: str = '0'
    coin_min_trade: str = '0'
    cost_min_trade: str = '0'
    precision: str = '.1111111111'
    trade_vol: str = '0'
    average_buys: str = '0'
    average_sells: str = '0'
    average_per_gain: str = '0'
    num_trades: str = '0'
    num_buys: str = '0'
    num_sells: str = '0'
    buy_vol: str = '0'
    sell_vol: str = '0'

    # Technical Indicator Data
    ema: str = ''  # Length
    ema_val: str = ''  # Value of EMA now
    ema_percent: str = ''  # Amount to modify EMA
    ema_buy: bool = False
    ema_sell: bool = False

    sma: str = ''
    sma_val: str = ''
    sma_buy: bool = False
    sma_sell: bool = False
    sma_percent: str = ''

    ema_cross_fast: str = ''
    ema_cross_slow: str = ''
    ema_cross_val_fast: str = ''
    ema_cross_val_slow: str = ''
    ema_cross_buy: bool = False
    ema_cross_sell: bool = False

    sma_cross_fast: str = ''
    sma_cross_slow: str = ''
    sma_cross_val_fast: str = ''
    sma_cross_val_slow: str = ''
    sma_cross_buy: bool = False
    sma_cross_sell: bool = False

    ema_sma_cross_fast: str = ''
    ema_sma_cross_slow: str = ''
    ema_sma_cross_val_fast: str = ''
    ema_sma_cross_val_slow: str = ''
    ema_sma_cross_buy: bool = False
    ema_sma_cross_sell: bool = False

    rsi_val: str = ''
    rsi_buy: str = ''
    rsi_sell: str = ''

    bb_width_val: str = ''
    bb_under_val: str = ''
    bb_over_val: str = ''
    bb_buy: str = ''  # %above/below upper band
    bb_sell: str = ''

    macd_val: str = ''
    macd_signal_val: str = ''
    macd_cross_buy: bool = False
    macd_cross_sell: bool = False
    macd_0_buy: bool = False
    macd_0_sell: bool = False
    macd_color_buy: bool = False
    macd_color_sell: bool = False

    stoch_cross_buy: bool = False
    stoch_cross_sell: bool = False

    stoch_k_val: str = ''
    stoch_d_val: str = ''
    stoch_val_buy: bool = False
    stoch_val_sell: bool = False

    psar_val: str = ''
    psar_cross_buy: bool = False
    psar_cross_sell: bool = False

    def set_record(self, rec):
        for key in rec:
            try:
                setattr(self, key, rec[key])
            except Exception as e:
                print('Error setting', key, e)


def convert_record(old_rec):
    # This converts the old style records into new records.
    '''
    class Record(EventDispatcher):
        def __init__(self, **kwargs):
            self.trigs = ['ema', 'ema_buy', 'ema_sell', 'ema_cross_fast', 'ema_cross_slow', 'ema_cross_buy',
                          'ema_cross_sell', 'sma', 'sma_buy', 'ema_percent', 'sma_percent',
                          'sma_sell', 'sma_cross_fast', 'sma_cross_slow', 'sma_cross_buy', 'sma_cross_sell',
                          'ema_sma_cross_fast', 'ema_sma_cross_slow', 'ema_sma_cross_buy',
                          'ema_sma_cross_sell', 'rsi_buy', 'rsi_sell', 'bb_buy', 'bb_sell', 'macd_cross_buy',
                          'macd_cross_sell', 'macd_0_buy', 'macd_0_sell', 'macd_color_buy', 'macd_color_sell',
                          'stoch_cross_buy', 'stoch_cross_sell', 'stoch_val_buy', 'stoch_val_sell', 'psar_cross_buy',
                          'psar_cross_sell',
                          'sell_per', 'stop_per', 'trail_per', 'dca_buyback_per',
                          ]

            self.base = ['symbol', 'coin', 'pair', 'nope_coin', 'candle', 'pair_per', 'pair_amt', 'pair_minmult',
                         'exchange', 'ex_icon', 'my_id', 'coin_min', 'pair_min', 'kind', 'side', 'leverage',
                         'trade_id', 'buy_trade_id', 'sell_trade_id', 'check_rate']

            self.trade_data = ['gl_per', 'ema_val', 'ema_cross_val_fast', 'ema_cross_val_slow', 'sma_val',
                               'sma_cross_val_fast',
                               'sma_cross_val_slow', 'ema_sma_cross_val_fast', 'ema_sma_cross_val_slow', 'rsi_val',
                               'bb_width_val', 'bb_under_val', 'bb_over_val', 'close_diff_val', 'macd_val',
                               'macd_signal_val',
                               'k_val', 'd_val', 'psar_val', 'sellover', 'status', 'enable_buy', 'error',
                               'last_update', 'trade_vol', 'prec', 'sell_price', 'buy_price', 'stop_price',
                               'trail_price',
                               'buy_price', 'sold_price', 'amount', 'now_price', 'coin_bal', 'pair_bal', 'average_buys',
                               'average_sells', 'dca', 'buyback_price', 'last_price', 'last_buy_price', 'indicators',
                               'trade_vol', 'trade_price', 'per_gain', 'num_trades', 'num_buys', 'num_sells', 'buy_vol',
                               'sell_vol', 'price'
                               ]

            self.create_property('childs', value=[])

            self.trues = ['active', 'ready_sell', 'sold', 'selected', 'sell_now', 'buy_now', 'verified', 'very_sent',
                          'is_stop', 'buy_enabled', 'sell_enabled']

            for key in self.base:
                self.create_property(key, value='')

            for key in self.trigs:
                self.create_property(key, value='')

            for key in self.trade_data:
                self.create_property(key, value='')

            for key in self.trues:
                self.create_property(key, value=False)


    trouble ones: Yes/No to True/False
     'ema_buy', 'ema_sell'
    '''
    pass



if __name__ == '__main__':
    pass

