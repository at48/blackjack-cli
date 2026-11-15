# Blackjack CLI Simulator

A terminal-based Blackjack game with a **6-deck shoe** and live **basic strategy** advice.

## Features

- Realistic 6-deck shoe that depletes and reshuffles
- Full play: Hit, Stand, Double, Split (up to 4 hands)
- Insurance when dealer shows Ace
- Live basic strategy recommendation on every decision
- Hi-Lo running count + true count displayed
- Clean table view with bankroll tracking
- Blackjack pays 3:2

**Rules used:** 6 decks · Dealer hits soft 17 (H17) · Double after split allowed · No surrender

## Run

```bash
python3 blackjack_sim.py
```

No external dependencies required (pure Python standard library).

## Controls

| Key | Action   |
|-----|----------|
| `h` | Hit      |
| `s` | Stand    |
| `d` | Double   |
| `p` | Split    |
| `q` | Quit     |

The optimal move according to basic strategy is always shown so you can practice or deliberately deviate.
