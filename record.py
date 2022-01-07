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
            setattr(self, key, rec[key])


    # # Not Sure if we will need these
    # close_diff_val
    # sellover

    # # Legacy?
    # def set_record(self, rec, *args):
    #     for key in rec:
    #         if args:
    #
    #         elif not key == 'active':
    #             setattr(self, key, rec[key])
    #
    # def get_record(self):
    #     new_rec = {}
    #     for key in self.base:
    #         if not getattr(self, key) == '':
    #             new_rec[key] = getattr(self, key)
    #     for key in self.trigs:
    #         if not getattr(self, key) == '':
    #             new_rec[key] = getattr(self, key)
    #     for key in self.trade_data:
    #         if not getattr(self, key) == '':
    #             new_rec[key] = getattr(self, key)
    #     for key in self.trues:
    #         if not getattr(self, key) == '':
    #             new_rec[key] = getattr(self, key)
    #     if getattr(self, 'childs'):
    #         new_rec['childs'] = getattr(self, 'childs')
    #     return new_rec
    #
    # def get_all(self):
    #     new_rec = {}
    #     for key in self.base:
    #         new_rec[key] = getattr(self, key)
    #     for key in self.trigs:
    #         new_rec[key] = getattr(self, key)
    #     for key in self.trues:
    #         new_rec[key] = getattr(self, key)
    #     for key in self.trade_data:
    #         new_rec[key] = getattr(self, key)
    #     # if getattr(self, 'childs'):
    #     new_rec['childs'] = getattr(self, 'childs')
    #     return new_rec
    #
    # def get_base(self):
    #     new_rec = {}
    #     for key in self.base:
    #         if not getattr(self, key) == '':
    #             new_rec[key] = getattr(self, key)
    #     return new_rec
    #
    # def get_trigs(self):
    #     new_rec = {}
    #     for key in self.trigs:
    #         if not getattr(self, key) == '':
    #             new_rec[key] = getattr(self, key)
    #     return new_rec
    #
    # def reset(self, *args):
    #     my_id = self.my_id
    #     for key in self.base + self.trigs + self.trade_data:
    #         if key not in args:
    #             setattr(self, key, '')
    #
    #     self.my_id = my_id
    #     self.gl_per = '0'
    #     self.buy_price = '0'
    #     self.price = '0'
    #     self.sold_price = '0'
    #     self.sell_price = '0'
    #     self.buy_price = '0'
    #     self.now_price = '0'
    #     self.average_buy = '0'
    #     self.buyback_price = '0'
    #     self.trail_price = '0'
    #     self.stop_price = '0'
    #     self.coin_min = '0'
    #     self.pair_min = '0'
    #     self.prec = '.11111111'
    #     self.exchange = 'Binance'
    #     self.ex_icon = 'Binance_icon.png'
    #
    #     self.active = True
    #
    #     self.num_sells = '0'
    #     self.sell_vol = '0'
    #     self.num_buys = '0'
    #     self.buy_vol = '0'
    #     self.leverage = '0'


if __name__ == '__main__':
    pass

