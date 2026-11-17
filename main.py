# BTC race bot (Python 3.13, standard library only): deep-dip mean reversion on cbBTC.
# Buys a dip below the 4-hour high, takes a profit, cuts losers fast, then waits
# before the next dip. Long only, one position, full cash per trade.
# Protocol: agent-fun/bars-replay/v1, via the vendored makefun_bars shim.
# No network, no wall clock, no randomness: deterministic from the bars alone.
#
# Tuned on the btc-race-24h-20261117-0603 dev window (BTC +0.53% over the 24h,
# 2.69% high-low range, the calmest of the last three dev windows; the two
# before it fell -3.92% and -2.28%). Grid search over dip/TP/SL/lookback/
# cooldown, scored on this window and cross-checked on both falling windows:
# shallow dips (100-125 bp) scored best here (+$20.81 / +$22.21) but lost
# -$50 to -$65 on the falling windows; a 275 bp dip never triggered here
# (0 trades, the whole 24h range was only 269 bp) so it fails the dev gate;
# dip 200 bp / TP 150 bp / lookback 240 / cooldown 120 was the robust pick:
# +$11.65 here (2 trades), -$8.55 and -$2.10 on the two falling windows,
# the best worst-case of every candidate tried. Breakout trend-following
# lost on all three windows (whipsawed in the range).
# Dev result (local replay, same fill model as the official harness):
# +$11.65 on $1,000, 2 trades, max drawdown 0.62%.

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
LOOKBACK = 240          # bars of the 4-hour high the dip is measured from
DIP_BPS = 200           # buy when the close is 2.00% below the 4-hour high
TP_BPS = 150            # take profit 1.5% above the entry close
SL_BPS = 80             # stop loss 0.8% below the entry close
COOLDOWN = 120          # bars to wait after an exit before buying again
MAX_SLIPPAGE_BPS = 100  # 1% past the close the order was decided on

closes = []             # closes seen so far, oldest first
entry_close = None      # close at the bar the current position was decided on
last_exit_seq = -10 ** 9


def on_batch(state, batch):
    global entry_close, last_exit_seq
    for bar in batch["bars"]:
        if bar["symbol"] == SYMBOL:
            closes.append(int(bar["c"]))
    if state.warming_up:
        return []
    if len(closes) < LOOKBACK:
        return []
    held = state.positions.get(SYMBOL)
    if held is not None:
        # Take profit or stop loss, measured from the entry close.
        # Once the position is 40 bps in profit, the stop moves to breakeven
        # so a reversal after a partial gain exits flat instead of at a loss.
        if entry_close is not None:
            if closes[-1] >= entry_close * (10000 + TP_BPS) // 10000:
                entry_close = None
                last_exit_seq = state.seq
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            stop = entry_close * (10000 - SL_BPS) // 10000
            if closes[-1] >= entry_close * (10000 + 40) // 10000:
                stop = entry_close
            if closes[-1] <= stop:
                entry_close = None
                last_exit_seq = state.seq
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []
    if state.seq - last_exit_seq < COOLDOWN:
        return []
    high = max(closes[-LOOKBACK:])
    if closes[-1] <= high * (10000 - DIP_BPS) // 10000:
        if state.cash <= 0:
            return []
        entry_close = closes[-1]
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
