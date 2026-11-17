# cbBTC dip catcher for make.fun btc-race-24h-20261117-0603.
# Watches the cbBTC/USDC tape one minute at a time and only steps in after a
# sharp pullback from the recent peak, then banks a quick rebound or bails out
# early. Never short, never leveraged, at most one open trade, and the whole
# cash pile goes into each trade. Talks agent-fun/bars-replay/v1 through the
# makefun_bars shim vendored next door. Pure standard library, no clock, no
# net, no dice rolls: the same bars always give the same orders.
#
# How the numbers were picked: a sweep over drop size, win/loss targets,
# window length and rest length, scored on this race's frozen 24h tape and
# then re-scored on the two earlier tapes, both of which slid hard. Shallow
# drops looked best on this tape alone (about +$21 to +$22) yet gave back
# $50-$65 on the sliding tapes; a 275 bp drop never fired once here, since
# the whole tape only spans 269 bp. A 200 bp drop with a 150 bp win target
# was the sturdiest middle ground: +$11.65 here, -$8.55 and -$2.10 on the
# sliders. Trend chasing was tried too and bled on every tape, so it stays out.
# Local replay on this tape: +$11.65 from $1,000, two round trips, worst dip
# in equity 0.62%. The replay prices fills exactly the way the official
# harness does (checked: buy-and-hold replays to the cent on this kit).

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

ASSET = "CBBTC"
WINDOW = 240        # minutes of tape behind the peak we measure the drop from
DROP_BPS = 200      # step in once the last close sits 2.00% under that peak
WIN_BPS = 150       # bank the trade 1.5% above the fill bar's close
LOSE_BPS = 80       # bail out 0.8% below it
LOCKIN_BPS = 40     # past +0.4%, pull the bail-out up to breakeven
REST_BARS = 120     # minutes to sit out after any exit
SLIP_BPS = 100      # never chase a fill more than 1% past the deciding close


def _bp(px, bps):
    return px * (10000 + bps) // 10000


def _sell(pos):
    return {"side": "sell", "symbol": ASSET, "qty": pos.qty,
            "max_slippage_bps": SLIP_BPS}


pxs = []            # closes so far, oldest first
bought_at = None    # close of the bar that triggered the open trade
freed_at = -10 ** 9  # seq of the most recent exit


def on_batch(state, batch):
    global bought_at, freed_at
    for bar in batch["bars"]:
        if bar["symbol"] == ASSET:
            pxs.append(int(bar["c"]))
    if state.warming_up or len(pxs) < WINDOW:
        return []
    now = pxs[-1]
    pos = state.positions.get(ASSET)
    if pos is not None:
        if bought_at is not None:
            if now >= _bp(bought_at, WIN_BPS):
                bought_at = None
                freed_at = state.seq
                return [_sell(pos)]
            floor = _bp(bought_at, -LOSE_BPS)
            if now >= _bp(bought_at, LOCKIN_BPS):
                floor = bought_at
            if now <= floor:
                bought_at = None
                freed_at = state.seq
                return [_sell(pos)]
        return []
    if state.seq - freed_at < REST_BARS:
        return []
    if now > _bp(max(pxs[-WINDOW:]), -DROP_BPS):
        return []
    if state.cash <= 0:
        return []
    bought_at = now
    return [{"side": "buy", "symbol": ASSET,
             "notional_quote_units": state.cash,
             "max_slippage_bps": SLIP_BPS}]


makefun_bars.run(on_batch)
