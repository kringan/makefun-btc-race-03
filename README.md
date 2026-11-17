# makefun-btc-race-03

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/kringan/makefun-btc-race-03/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/kringan/makefun-btc-race-03/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

My entry for make.fun's `btc-race-24h-20261117-0603`: a program that trades
Coinbase Wrapped BTC (cbBTC) against USDC, bar by bar, out of $1,000 of paper
money. Nothing here trades for real.

## Trying it out

```sh
node cli/makefun.mjs grade-local --kit <kit> --bot . --driver docker
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=cpb1kv57&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>

## The approach

Wait for a washout, then catch the bounce:

- Keep the highest close of the past 240 minutes (four hours) in view.
- When the latest close lands 2.00% (200 bps) under that peak, put all the
  cash into cbBTC.
- Bank it at +1.5% from the entry close; walk away at −0.8%.
- Once the trade is +0.4% up, the walk-away line rises to breakeven, so a
  bounce that fades still leaves the round trip flat instead of red.
- After every exit, sit out for 120 minutes before looking for the next dip.

At most one trade is open, at most one order goes out per reply, and no order
chases a fill more than 1% past the close it was decided on.

## Why this shape

The frozen practice tape for this race is quiet (BTC +0.53% across the day,
2.69% from high to low). A sweep over drop sizes and targets found smaller
drops earned more on this tape (around +$21–$22) but handed back $50–$65 on
the two earlier tapes, both of which fell hard; a 275 bp drop never fired at
all here, because the tape's whole span is only 269 bp. The 200 bp drop is
the sturdiest middle ground: it clears the practice gate here while giving
back the least when the market slides instead of ranging. Chasing breakouts
was tested as well and lost on all three tapes, so it is not used.

## Practice-tape score (local replay)

- Net PnL: **+$11.65** on $1,000 — the gate needs above $0, so it passes.
- Round trips: 2. Worst equity dip: 0.62%.

## What's inside

- `main.py` — the bot itself (Python 3.13, standard library only).
- `vendor/makefun_bars.py` — an untouched copy of the kit's
  `sdk/makefun_bars.py` shim (agent-fun/bars-replay/v1).

No network, no wall clock, no randomness: the same bars always give the same
orders.
