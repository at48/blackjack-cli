#!/usr/bin/env python3
"""
Blackjack CLI Simulator — 6-deck shoe + live basic strategy advice
Rules: 6 decks, Dealer Hits Soft 17 (H17), DAS allowed, No surrender, BJ pays 3:2
"""

import os
import random
import sys
from collections import namedtuple
from typing import List, Optional, Tuple

# ──────────────────────────────────────────────
# Card & Shoe
# ──────────────────────────────────────────────

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['♠', '♥', '♦', '♣']
RANK_VALUE = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

Card = namedtuple('Card', ['rank', 'suit'])

def card_str(c: Card) -> str:
    return f"{c.rank}{c.suit}"

def hand_str(cards: List[Card]) -> str:
    return "  ".join(card_str(c) for c in cards)

class Shoe:
    def __init__(self, num_decks: int = 6):
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self.running_count = 0  # Hi-Lo
        self.shuffle()

    def shuffle(self):
        self.cards = [Card(r, s) for _ in range(self.num_decks)
                      for r in RANKS for s in SUITS]
        random.shuffle(self.cards)
        self.running_count = 0

    def deal(self) -> Card:
        if len(self.cards) < 20:          # reshuffle when low
            self.shuffle()
        c = self.cards.pop()
        # Hi-Lo update
        if c.rank in ('2', '3', '4', '5', '6'):
            self.running_count += 1
        elif c.rank in ('10', 'J', 'Q', 'K', 'A'):
            self.running_count -= 1
        return c

    def decks_remaining(self) -> float:
        return len(self.cards) / 52.0

    def true_count(self) -> float:
        decks = max(0.5, self.decks_remaining())
        return self.running_count / decks

# ──────────────────────────────────────────────
# Hand helpers
# ──────────────────────────────────────────────

def hand_value(cards: List[Card]) -> Tuple[int, bool]:
    """Return (best total, is_soft)"""
    total = 0
    aces = 0
    for c in cards:
        total += RANK_VALUE[c.rank]
        if c.rank == 'A':
            aces += 1
    while total > 21 and aces:
        total -= 10
        aces -= 1
    is_soft = aces > 0 and total <= 21
    return total, is_soft

def is_blackjack(cards: List[Card]) -> bool:
    return len(cards) == 2 and hand_value(cards)[0] == 21

def is_pair(cards: List[Card]) -> bool:
    return len(cards) == 2 and RANK_VALUE[cards[0].rank] == RANK_VALUE[cards[1].rank]

# ──────────────────────────────────────────────
# Basic Strategy (6-deck, H17, DAS, no surrender)
# ──────────────────────────────────────────────

def basic_strategy(player_cards: List[Card], dealer_up: Card,
                   can_double: bool, can_split: bool) -> str:
    """
    Returns recommended action: 'Hit', 'Stand', 'Double', 'Split'
    """
    total, soft = hand_value(player_cards)
    up = dealer_up.rank
    up_val = 11 if up == 'A' else RANK_VALUE[up]

    # Pair splitting first (only on exactly two cards)
    if can_split and is_pair(player_cards):
        r = player_cards[0].rank
        # Always split Aces and 8s
        if r == 'A' or r == '8':
            return 'Split'
        # Never split 5s or 10s
        if r in ('5', '10', 'J', 'Q', 'K'):
            pass  # fall through to hard total
        elif r == '9':
            if up_val in (2, 3, 4, 5, 6, 8, 9):
                return 'Split'
            else:
                return 'Stand'
        elif r == '7':
            if up_val <= 7:
                return 'Split'
        elif r == '6':
            if up_val <= 6:
                return 'Split'
        elif r in ('2', '3'):
            if up_val <= 7:
                return 'Split'
        elif r == '4':
            if up_val in (5, 6):
                return 'Split'

    # Soft totals
    if soft:
        # Soft 13-14 (A2/A3)
        if total in (13, 14):
            if up_val in (5, 6) and can_double:
                return 'Double'
            return 'Hit'
        # Soft 15-16 (A4/A5)
        if total in (15, 16):
            if up_val in (4, 5, 6) and can_double:
                return 'Double'
            return 'Hit'
        # Soft 17 (A6)
        if total == 17:
            if up_val in (3, 4, 5, 6) and can_double:
                return 'Double'
            return 'Hit'
        # Soft 18 (A7) — H17 adjustments
        if total == 18:
            if up_val in (3, 4, 5, 6) and can_double:
                return 'Double'
            if up_val == 2 and can_double:          # H17: double vs 2
                return 'Double'
            if up_val in (2, 7, 8):
                return 'Stand'
            return 'Hit'                            # vs 9,10,A
        # Soft 19 (A8)
        if total == 19:
            if up_val == 6 and can_double:          # H17: double vs 6
                return 'Double'
            return 'Stand'
        # Soft 20+
        return 'Stand'

    # Hard totals
    if total <= 8:
        return 'Hit'
    if total == 9:
        if up_val in (3, 4, 5, 6) and can_double:
            return 'Double'
        return 'Hit'
    if total == 10:
        if up_val <= 9 and can_double:
            return 'Double'
        return 'Hit'
    if total == 11:
        # H17: double vs Ace too
        if can_double:
            return 'Double'
        return 'Hit'
    if total == 12:
        if up_val in (4, 5, 6):
            return 'Stand'
        return 'Hit'
    if total in (13, 14, 15, 16):
        if up_val <= 6:
            return 'Stand'
        return 'Hit'
    # 17+
    return 'Stand'

# ──────────────────────────────────────────────
# Game
# ──────────────────────────────────────────────

class BlackjackGame:
    def __init__(self):
        self.shoe = Shoe(6)
        self.bankroll = 1000.0
        self.bet = 0.0
        self.player_hands: List[List[Card]] = []
        self.hand_bets: List[float] = []
        self.dealer: List[Card] = []
        self.insurance_bet = 0.0
        self.current_hand_idx = 0

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        print("=" * 62)
        print("  BLACKJACK SIMULATOR  ·  6-Deck Shoe  ·  H17  ·  DAS")
        print("=" * 62)
        decks = self.shoe.decks_remaining()
        tc = self.shoe.true_count()
        print(f"  Bankroll: ${self.bankroll:,.2f}    "
              f"Cards left: {len(self.shoe.cards)} ({decks:.1f} decks)    "
              f"Hi-Lo RC: {self.shoe.running_count:+d}  TC: {tc:+.1f}")
        print("-" * 62)

    def print_table(self, hide_dealer: bool = True):
        self.print_header()
        print()
        # Dealer
        if hide_dealer and len(self.dealer) >= 2:
            print(f"  Dealer:  {card_str(self.dealer[0])}  ??")
        else:
            d_val, _ = hand_value(self.dealer)
            print(f"  Dealer:  {hand_str(self.dealer)}   ({d_val})")
        print()

        # Player hands
        for i, hand in enumerate(self.player_hands):
            val, soft = hand_value(hand)
            marker = "→" if i == self.current_hand_idx and hide_dealer else " "
            bj = " BLACKJACK" if is_blackjack(hand) else ""
            soft_str = " soft" if soft else ""
            print(f"  {marker} Hand {i+1}: {hand_str(hand)}   ({val}{soft_str}){bj}   bet ${self.hand_bets[i]:.0f}")
        print()

    def get_bet(self) -> float:
        while True:
            try:
                raw = input(f"  Place your bet (min $5, bankroll ${self.bankroll:,.0f}) or 'q' to quit: ").strip()
                if raw.lower() in ('q', 'quit', 'exit'):
                    print("\n  Thanks for playing!\n")
                    sys.exit(0)
                bet = float(raw)
                if bet < 5:
                    print("  Minimum bet is $5.")
                    continue
                if bet > self.bankroll:
                    print("  You don't have that much.")
                    continue
                return bet
            except ValueError:
                print("  Enter a number.")

    def deal_initial(self):
        self.player_hands = [[self.shoe.deal(), self.shoe.deal()]]
        self.hand_bets = [self.bet]
        self.dealer = [self.shoe.deal(), self.shoe.deal()]
        self.insurance_bet = 0.0
        self.current_hand_idx = 0

    def offer_insurance(self) -> None:
        if self.dealer[0].rank != 'A':
            return
        print("  Dealer shows an Ace.")
        while True:
            ans = input("  Insurance? (y/n)  [basic strategy says NO]: ").strip().lower()
            if ans in ('y', 'yes'):
                ins = self.bet / 2
                if ins > self.bankroll - self.bet:
                    print("  Not enough bankroll for insurance.")
                    return
                self.insurance_bet = ins
                self.bankroll -= ins
                print(f"  Insurance bet: ${ins:.0f}")
                return
            if ans in ('n', 'no', ''):
                return

    def check_dealer_blackjack(self) -> bool:
        if is_blackjack(self.dealer):
            return True
        return False

    def play_hand(self, hand_idx: int):
        self.current_hand_idx = hand_idx
        hand = self.player_hands[hand_idx]

        # Auto-stand on blackjack
        if is_blackjack(hand):
            return

        while True:
            val, soft = hand_value(hand)
            if val > 21:
                return  # busted

            can_double = len(hand) == 2 and self.bankroll >= self.hand_bets[hand_idx]
            can_split = (len(hand) == 2 and is_pair(hand)
                         and self.bankroll >= self.hand_bets[hand_idx]
                         and len(self.player_hands) < 4)

            advice = basic_strategy(hand, self.dealer[0], can_double, can_split)

            self.clear()
            self.print_table(hide_dealer=True)
            print(f"  ★ Optimal move:  {advice.upper()}")
            print()

            options = ["[H]it", "[S]tand"]
            if can_double:
                options.append("[D]ouble")
            if can_split:
                options.append("s[P]lit")
            print("  Options: " + "  ".join(options))
            choice = input("  Your action: ").strip().lower()

            if choice in ('h', 'hit'):
                hand.append(self.shoe.deal())
                continue
            elif choice in ('s', 'stand'):
                return
            elif choice in ('d', 'double') and can_double:
                self.bankroll -= self.hand_bets[hand_idx]
                self.hand_bets[hand_idx] *= 2
                hand.append(self.shoe.deal())
                return
            elif choice in ('p', 'split') and can_split:
                # Split
                new_card = hand.pop()
                self.bankroll -= self.hand_bets[hand_idx]
                new_hand = [new_card, self.shoe.deal()]
                hand.append(self.shoe.deal())
                self.player_hands.insert(hand_idx + 1, new_hand)
                self.hand_bets.insert(hand_idx + 1, self.hand_bets[hand_idx])
                # Aces get only one card each
                if hand[0].rank == 'A':
                    return
                continue
            else:
                print("  Invalid choice.")
                input("  Press Enter...")

    def dealer_play(self):
        while True:
            val, soft = hand_value(self.dealer)
            # H17: hit soft 17
            if val < 17 or (val == 17 and soft):
                self.dealer.append(self.shoe.deal())
            else:
                break

    def settle(self):
        self.clear()
        self.print_table(hide_dealer=False)
        d_val, _ = hand_value(self.dealer)
        dealer_bj = is_blackjack(self.dealer)

        # Insurance first
        if self.insurance_bet > 0:
            if dealer_bj:
                print(f"  Insurance pays 2:1 → +${self.insurance_bet * 2:.0f}")
                self.bankroll += self.insurance_bet * 3  # return stake + 2:1
            else:
                print("  Insurance loses.")
            self.insurance_bet = 0

        if dealer_bj:
            print("  Dealer has Blackjack.")
            for i, hand in enumerate(self.player_hands):
                if is_blackjack(hand):
                    print(f"  Hand {i+1}: Push")
                    self.bankroll += self.hand_bets[i]
                else:
                    print(f"  Hand {i+1}: Loses ${self.hand_bets[i]:.0f}")
            return

        for i, hand in enumerate(self.player_hands):
            p_val, _ = hand_value(hand)
            bet = self.hand_bets[i]

            if is_blackjack(hand):
                win = bet * 1.5
                print(f"  Hand {i+1}: BLACKJACK! +${win:.0f}")
                self.bankroll += bet + win
            elif p_val > 21:
                print(f"  Hand {i+1}: Bust — loses ${bet:.0f}")
            elif d_val > 21:
                print(f"  Hand {i+1}: Dealer busts — wins ${bet:.0f}")
                self.bankroll += bet * 2
            elif p_val > d_val:
                print(f"  Hand {i+1}: Wins ${bet:.0f}")
                self.bankroll += bet * 2
            elif p_val < d_val:
                print(f"  Hand {i+1}: Loses ${bet:.0f}")
            else:
                print(f"  Hand {i+1}: Push")
                self.bankroll += bet

    def round(self):
        self.clear()
        self.print_header()
        print()
        self.bet = self.get_bet()
        self.bankroll -= self.bet

        self.deal_initial()
        self.offer_insurance()

        # Peek for dealer blackjack
        if self.check_dealer_blackjack():
            self.settle()
            input("\n  Press Enter for next hand...")
            return

        # Player plays each hand
        i = 0
        while i < len(self.player_hands):
            self.play_hand(i)
            i += 1

        # Dealer plays if any hand still alive
        any_alive = any(hand_value(h)[0] <= 21 for h in self.player_hands)
        if any_alive:
            self.dealer_play()

        self.settle()
        input("\n  Press Enter for next hand...")

    def run(self):
        print("\n  Welcome to the Blackjack Simulator!")
        print("  Rules: 6 decks · Dealer hits soft 17 · Double after split · BJ 3:2")
        print("  Basic strategy advice is shown for every decision.\n")
        input("  Press Enter to start...")
        while self.bankroll >= 5:
            self.round()
        print("\n  Bankroll exhausted. Game over.\n")


if __name__ == "__main__":
    try:
        BlackjackGame().run()
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Bye!\n")
