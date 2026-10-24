from enum import IntEnum

# ----------------
# Globals and Constants
# ----------------

CURRENCY_SYMBOL = "$"

def FormatCurrency(amount):
    if amount >= 0.0:
        return CURRENCY_SYMBOL + format(amount, ".0f")
    else:
        return "-" + CURRENCY_SYMBOL + format(abs(amount), ".0f")

# ----------------
# ENUMS
# ----------------

class GameState(IntEnum):
    IDLE = 0
    LOBBY = 1
    BETTING = 2
    DEAL = 3
    PLAYERSDRAW = 4
    DEALERSDRAW = 5
    PAYOUT = 6

class Action(IntEnum):
    HIT = 0
    STAND = 1
    DOUBLE = 2
    SPLIT = 3

class WinType(IntEnum):
    PUSH = 0
    # player wins
    PLAYERBLACKJACK = 1
    PLAYERWIN = 2
    DEALERBUST = 3 # keep DEALERBUST last in player wins
    # dealer wins
    DEALERBLACKJACK = 4
    DEALERWIN = 5
    PLAYERBUST = 6

class WinResult(IntEnum):
    PUSH = 0
    LOSS = 1
    WIN = 2

class PlayerRole(IntEnum):
    PLAYER = 0
    BOT = 1
    DEALER = 2
