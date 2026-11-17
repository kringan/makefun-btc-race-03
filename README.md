# makefun-btc-race-03

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/kringan/makefun-btc-race-03/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/kringan/makefun-btc-race-03/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A deep-dip mean-reversion bot for make.fun's `btc-race-24h-20261117-0603` (race a BTC trading bot live for 24 hours). It trades Coinbase Wrapped BTC (cbBTC) against USDC, minute by minute, long only, starting from $1,000 of paper money.

## Run it

```sh
node cli/makefun.mjs grade-local --kit <kit> --bot . --driver docker
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=cpb1kv57&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>

## Strategy

Deep-dip mean reversion:

- Track the highest close of the last 240 one-minute bars (4 hours).
- Buy with the full cash balance when the latest close is 2.00% (200 bps)
  below that high.
- Take profit at +1.5% above the entry close; stop loss at -0.8%.
- Once the position is +0.4% in profit, the stop moves to breakeven, so a
  reversal after a partial gain exits flat instead of at a loss.
- After any exit, wait 120 bars before buying again.

One open position at most, at most one order per reply, max slippage 1% past
the close the order was decided on.

Why this deep: the dev window is calm (BTC +0.53% over the 24h, 2.69%
high-low range), and the grid search showed shallow dips (100–125 bps)
score higher here (+$20.81 / +$22.21) but lose $50–$65 on the two
preceding falling dev windows, while a 275 bp dip never triggers at all
(the whole window's range is only 269 bp). Dip 200 bp is the robust
compromise: it still clears the dev gate here while losing the least
(-$8.55 / -$2.10) when the market falls instead of ranging.

## Results (dev window, local replay)

- Net PnL: **+$11.65** on $1,000 (dev gate: PnL > 0, pass)
- Trades: 2, max drawdown 0.62%

## Layout

- `main.py` — the bot (Python 3.13, standard library only).
- `vendor/makefun_bars.py` — byte-identical copy of the kit's
  `sdk/makefun_bars.py` shim (agent-fun/bars-replay/v1).

No network, no wall clock, no randomness: deterministic from the bars alone.
