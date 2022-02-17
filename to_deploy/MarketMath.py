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

from statistics import stdev
from CraftCrypto_Helpers.Helpers import is_float, copy_prec
# This might get ported to Craft-Crypto Helpers too

def calculate_market_indicators(closes, ohlc, card):
    my_ema = EMA(closes, int(card.ema)) if is_float(card.ema) else None
    my_sma = SMA(closes, int(card.sma)) if is_float(card.sma) else None

    my_ema_fast = EMA(closes, int(card.ema_cross_fast)) if is_float(card.ema_cross_fast) else None
    my_ema_slow = EMA(closes, int(card.ema_cross_slow)) if is_float(card.ema_cross_slow) else None

    my_sma_fast = SMA(closes, int(card.sma_cross_fast)) if is_float(card.sma_cross_fast) else None
    my_sma_slow = SMA(closes, int(card.sma_cross_slow)) if is_float(card.sma_cross_slow) else None

    my_emasma_fast = EMA(closes, int(card.ema_sma_cross_fast)) if is_float(card.ema_sma_cross_fast) else None
    my_emasma_slow = SMA(closes, int(card.ema_sma_cross_slow)) if is_float(card.ema_sma_cross_slow) else None

    rsi_val = RSI(closes, 14) if (is_float(card.rsi_buy) or is_float(card.rsi_sell)) else None

    bb_high, bb_low = BB(closes) if (is_float(card.bb_buy) or is_float(card.bb_sell)) else None, None

    macd_sig = MACD(closes) if [card.macd_cross_buy, card.macd_color_buy,
                                card.macd_0_buy, card.macd_cross_sell,
                                card.macd_color_sell, card.macd_0_sell].count('Yes') > 0 else None

    k_d = STOCH(ohlc) if [card.stoch_cross_buy, card.stoch_cross_sell].count('Yes') > 0 or \
                         is_float(card.stoch_val_buy) or is_float(card.stoch_val_sell) else None

    psar_val = PSAR(ohlc, .02, .02, .2) if (card.psar_cross_buy or card.psar_cross_sell) else None
    
    indicators = [my_ema, my_sma, my_ema_fast, my_ema_slow, my_sma_fast, my_sma_slow, my_emasma_fast, my_emasma_slow,
                  rsi_val, bb_high, bb_low, macd_sig, k_d, psar_val]
        
    return indicators


def determine_buy_sell(indicators, card, closes, i, ): 
    # i typically = -2 for last value
    make_buy = True
    make_sell = True

    [my_ema, my_sma, my_ema_fast, my_ema_slow, my_sma_fast, my_sma_slow, my_emasma_fast, my_emasma_slow,
     rsi_val, bb_high, bb_low, macd_sig, k_d, psar_val] = indicators

    p = closes[i]
    card.last_price = copy_prec(p, card.precision)

    ema_per = float(card.ema_percent) if is_float(card.ema_percent) else 0
    sma_per = float(card.sma_percent) if is_float(card.sma_percent) else 0

    if card.ema_buy == 'Yes':
        card.ema_val = copy_prec(my_ema[i], card.precision)
        if not (p < my_ema[i] * (100 - ema_per) / 100):
            make_buy = False
            # count += 1

    if card.sma_buy == 'Yes':
        card.sma_val = copy_prec(my_sma[i], card.precision)
        if not (p < my_sma[i] * (100 - sma_per) / 100):
            make_buy = False

    if card.ema_cross_buy == 'Yes':
        card.ema_cross_val_fast = copy_prec(my_ema_fast[i], card.precision)
        card.ema_cross_val_slow = copy_prec(my_ema_slow[i], card.precision)
        if not (my_ema_fast[i] > my_ema_slow[i] and my_ema_fast[i-1] < my_ema_slow[i-1]):
            make_buy = False

    if card.sma_cross_buy == 'Yes':
        card.sma_cross_val_fast = copy_prec(my_sma_fast[i], card.precision)
        card.sma_cross_val_slow = copy_prec(my_sma_slow[i], card.precision)
        if not (my_sma_fast[i] > my_sma_slow[i] and my_sma_fast[i-1] < my_sma_slow[i-1]):
            make_buy = False

    if card.ema_sma_cross_buy == 'Yes':
        card.ema_sam_cross_val_fast = copy_prec(my_emasma_fast[i], card.precision)
        card.ema_sam_cross_val_slow = copy_prec(my_emasma_slow[i], card.precision)
        if not (my_emasma_fast[i] > my_emasma_slow[i] and my_emasma_fast[i-1] < my_emasma_slow[i-1]):
            make_buy = False

    if is_float(card.rsi_buy):
        card.rsi_val = str(round(rsi_val[i], 1))
        if not (rsi_val[i] < int(card.rsi_buy)):
            make_buy = False

    if is_float(card.bb_buy):
        card.bb_under_val = copy_prec(bb_low[i], card.precision, 1)
        bb_mult = (100 - float(card.bb_buy)) / 100 * bb_low[i]
        if not (p < bb_mult):
            make_buy = False

    if card.macd_cross_buy == 'Yes':
        card.macd_val = copy_prec(macd_sig[0][i], card.precision, 2)
        card.macd_signal_val = copy_prec(macd_sig[1][i], card.precision, 2)
        if not (macd_sig[0][i] > macd_sig[1][i] and macd_sig[0][i-1] < macd_sig[1][i-1]):
            make_buy = False

    if card.macd_color_buy == 'Yes':
        card.macd_val = copy_prec(macd_sig[0][i], card.precision, 2)
        card.macd_signal_val = copy_prec(macd_sig[1][i], card.precision, 2)
        if not (macd_sig[0][i] < macd_sig[1][i]):
            make_buy = False

    if card.macd_0_buy == 'Yes':
        card.macd_val = copy_prec(macd_sig[0][i], card.precision, 2)
        card.macd_signal_val = copy_prec(macd_sig[1][i], card.precision, 2)
        if not (macd_sig[0][i] < 0 and macd_sig[1][i] < 0):
            make_buy = False

    if is_float(card.stoch_val_buy):
        card.k_val = str(round(k_d[0][i], 1))
        card.d_val = str(round(k_d[1][i], 1))
        if not (k_d[0][i] < float(card.stoch_val_buy) and
                k_d[1][i] < float(card.stoch_val_buy)):
            make_buy = False

    if card.stoch_cross_buy == 'Yes':
        card.k_val = str(round(k_d[0][i], 1))
        card.d_val = str(round(k_d[1][i], 1))
        if not (k_d[0][i] > k_d[1][i] and k_d[0][i-1] < k_d[1][i-1]):
            make_buy = False

    if card.psar_cross_buy == 'Yes':
        card.psar_val = copy_prec(psar_val[i], card.precision)
        if not psar_val[i] > p:
            make_buy = False

    if card.ema_sell == 'Yes':
        card.ema_val = copy_prec(my_ema[i], card.precision)
        if not (p > my_ema[i] * (100 + ema_per) / 100):
            make_sell = False

    if card.sma_sell == 'Yes':
        card.sma_val = copy_prec(my_sma[i], card.precision)
        if not (p > my_sma[i] * (100 + sma_per) / 100):
            make_sell = False

    if card.ema_cross_sell == 'Yes':
        card.ema_cross_val_fast = copy_prec(my_ema_fast[i], card.precision)
        card.ema_cross_val_slow = copy_prec(my_ema_slow[i], card.precision)
        if not (my_ema_fast[i] < my_ema_slow[i] and my_ema_fast[i-1] > my_ema_slow[i-1]):
            make_sell = False
        if make_sell:
            print('cross down!')

    if card.sma_cross_sell == 'Yes':
        card.sma_cross_val_fast = copy_prec(my_sma_fast[i], card.precision)
        card.sma_cross_val_slow = copy_prec(my_sma_slow[i], card.precision)
        if not (my_sma_fast[i] < my_sma_slow[i] and my_sma_fast[i-1] > my_sma_slow[i-1]):
            make_sell = False

    if card.ema_sma_cross_sell == 'Yes':
        card.ema_sma_cross_val_fast = copy_prec(my_emasma_fast[i], card.precision)
        card.ema_sma_cross_val_slow = copy_prec(my_emasma_slow[i], card.precision)
        if not (my_emasma_fast[i] < my_emasma_slow[i] and my_emasma_fast[i-1] > my_emasma_slow[i-1]):
            make_sell = False

    if is_float(card.rsi_sell):
        card.rsi_val = str(round(rsi_val[i], 1))
        if not (rsi_val[i] > int(card.rsi_sell)):
            make_sell = False

    if is_float(card.bb_sell):
        card.bb_under_val = copy_prec(bb_high[i], card.precision, 1)
        bb_mult = (100 + float(card.bb_sell)) / 100 * bb_high[i]
        if not (p > bb_mult):
            make_sell = False

    if card.macd_cross_sell == 'Yes':
        card.macd_val = copy_prec(macd_sig[0][i], card.precision, 2)
        card.macd_signal_val = copy_prec(macd_sig[1][i], card.precision, 2)
        if not (macd_sig[0][i] < macd_sig[1][i] and macd_sig[0][i-1] > macd_sig[1][i-1]):
            make_sell = False

    if card.macd_color_sell == 'Yes':
        card.macd_val = copy_prec(macd_sig[0][i], card.precision, 2)
        card.macd_signal_val = copy_prec(macd_sig[1][i], card.precision, 2)
        if not (macd_sig[0][i] > macd_sig[1][i]):
            make_sell = False

    if card.macd_0_sell == 'Yes':
        card.macd_val = copy_prec(macd_sig[0][i], card.precision, 2)
        card.macd_signal_val = copy_prec(macd_sig[1][i], card.precision, 2)
        if not (macd_sig[0][i] > 0 and macd_sig[1][i] > 0):
            make_sell = False

    if is_float(card.stoch_val_sell):
        card.k_val = str(round(k_d[0][i], 1))
        card.d_val = str(round(k_d[1][i], 1))
        if not (k_d[0][i] > float(card.stoch_val_sell) and k_d[1][i] > float(card.stoch_val_sell)):
            make_sell = False

    if card.stoch_cross_sell == 'Yes':
        card.k_val = str(round(k_d[0][i], 1))
        card.d_val = str(round(k_d[1][i], 1))
        if not (k_d[0][i] < k_d[1][i] and k_d[0][i-1] > k_d[1][i-1]):
            make_sell = False

    if card.psar_cross_sell == 'Yes':
        card.psar_val = copy_prec(psar_val[i], card.precision)
        if not psar_val[i] < p:
            make_sell = False
    
    return make_buy, make_sell, p



def RSI(closes, period):
    # find 1st point
    ups = []
    downs = []
    for i in range(1, period + 1):
        m = closes[i] - closes[i-1]
        if m > 0:
            ups.append(m)
        else:
            downs.append(m)
    avg_u = 0
    avg_d = 0
    if ups:
        avg_u = sum(ups) / len(ups)
    if downs:
        avg_d = abs(sum(downs) / len(downs))
    my_rsi = 0
    if avg_d == 0:
        my_rsi = [100]*15
    else:
        my_rsi = [100 - 100 / (1 + avg_u / avg_d)]*15

    for j in range(period + 1, len(closes)):
        m = closes[j] - closes[j-1]
        cg = 0
        cl = 0
        if m > 0:
            cg = m
        else:
            cl = abs(m)
        avg_u = (avg_u * 13 + cg) / 14
        avg_d = (avg_d * 13 + cl) / 14
        if avg_d:
            my_rsi.append(100 - 100 / (1 + avg_u / avg_d))
        else:
            my_rsi.append(100)

    return my_rsi


def EMA(prices, period):
    if period == 0:
        return 0
    my_ema = [prices[0]]
    for i in range(1, len(prices)):
        now_ema = prices[i] * (2 / (1 + period))
        last_ema = my_ema[i-1] * (1 - (2 / (1 + period)))
        my_ema.append(now_ema + last_ema)

    return my_ema


def SMA(prices, period):
    if period == 0:
        return 0
    my_sma = prices[0:period-1]
    for i in range(period, len(prices) + 1):
        my_sma.append(sum(prices[(i-period):i])/period)
    return my_sma


def MACD(closes):
    ema_12 = EMA(closes, 12)
    ema_26 = EMA(closes, 26)
    my_macd = []
    zipped = zip(ema_12, ema_26)
    for i2, t6 in zipped:
        my_macd.append(i2 - t6)
    my_signal = EMA(my_macd, 9)
    return [my_macd, my_signal]


def STOCH(ohlc):
    # 14 day period
    # d is 3 period sma of k
    k = [0]
    for i in range(1, len(ohlc) + 1):
        max_price = 0
        min_price = 1000000000000000000000000000000000
        for mp in ohlc[i-14:i]:
            if mp[2] > max_price:
                max_price = mp[2]
            if mp[3] < min_price:
                min_price = mp[3]
        if not max_price == min_price:
            k.append((ohlc[i-1][4] - min_price) / (max_price - min_price) * 100)
        else:
            k.append(0)

    avgk = SMA(k, 3)
    d = SMA(avgk, 3)

    return [avgk, d]


def BB(closes):
    # 20 period
    bb_width = []
    bb_mid = SMA(closes, 20)
    bb_lower = []
    bb_upper = []
    # get std dev
    bands = closes[0:20 - 1]
    for i in range(20, len(closes) + 1):
        bands.append(2 * stdev(closes[(i - 20):i]))
    for i in range(0, len(bb_mid)):
        w = 0
        if bb_mid[i] and bands[i] and not bb_mid[i] == bands[i]:
            w = (bb_mid[i] + bands[i])/(bb_mid[i] - bands[i])
        bb_width.append(w)
        bb_lower.append(bb_mid[i] - bands[i])
        bb_upper.append(bb_mid[i] + bands[i])

    return bb_upper, bb_lower


def PSAR(ohlc, step_val, base_val, max_val):
    # assume rising, EP is highest high, start sar at low
    rising = True
    ep = ohlc[0][2]
    my_sar = [ohlc[0][3]]
    af = base_val
    for i in range(1, len(ohlc)):
        if rising:
            next_sar = my_sar[i-1] + af * (ep - my_sar[i-1])
            # sar cannot be higher than previous 2 lows
            if i == 1:
                next_sar = my_sar[0]
            else:
                if next_sar > min(ohlc[i-1][3], ohlc[i-2][3]):
                    next_sar = min(ohlc[i-1][3], ohlc[i-2][3])
            # now check if price now broke the sar
            if ohlc[i][3] <= next_sar:
                rising = False
                next_sar = ep
                ep = ohlc[i][3]
                af = base_val
            else:
                if ohlc[i][2] > ep:
                    ep = ohlc[i][2]
                    af = af + step_val
            # print(next_sar, ep, af, rising)
            my_sar.append(next_sar)
        else:
            next_sar = my_sar[i - 1] - af * (my_sar[i - 1] - ep)
            # sar cannot be higher than previous 2 lows
            if next_sar < max(ohlc[i - 1][2], ohlc[i - 2][2]):
                next_sar = max(ohlc[i - 1][2], ohlc[i - 2][2])
            # now check if price now broke the sar
            if ohlc[i][2] >= next_sar:
                rising = True
                next_sar = ep
                ep = ohlc[i][2]
                af = base_val
            else:
                if ohlc[i][3] < ep:
                    ep = ohlc[i][3]
                    af = af + step_val
            my_sar.append(next_sar)
    return my_sar


if __name__ == '__main__':
    pass

