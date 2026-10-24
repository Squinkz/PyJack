from Constants import *
import random

# ----------------
# Betting Strategies
# ----------------

class Flat:
    name = "Flat"

    def NextMove(player):
        return player.startingBet

class Martingale:
    name = "Martingale"
    def NextMove(player):
        if player.lastWinResult == WinResult.LOSS:
            player.betScalar *= 2.0
        elif player.lastWinResult == WinResult.WIN:
            player.betScalar = 1.0
        return player.startingBet * player.betScalar

class ReverseMartingale:
    name = "Reverse Martingale"
    def NextMove(player):
        if player.lastWinResult == WinResult.LOSS:
            player.betScalar = 1.0
        elif player.lastWinResult == WinResult.WIN:
            player.betScalar *= 2.0
        return player.startingBet * player.betScalar

class DAlembert:
    name = "d'Alembert"
    def NextMove(player):
        if player.lastWinResult == WinResult.LOSS:
            player.betScalar += 2.0
        elif player.lastWinResult == WinResult.WIN:
            player.betScalar = max(1.0, player.betScalar - 1.0)
        return player.startingBet * player.betScalar

class ReverseDAlembert:
    name = "Reverse d'Alembert"
    def NextMove(player):
        if player.lastWinResult == WinResult.WIN:
            player.betScalar += 2.0
        elif player.lastWinResult == WinResult.LOSS:
            player.betScalar = max(1.0, player.betScalar - 1.0)
        return player.startingBet * player.betScalar

class CardCounter:
    name = "Card Counter"
    def NextMove(player):
        totalCards = 52 * player.room.rules.decksInShoe
        decksRemaining = (totalCards - player.room.cardsPlayed) / 52.0
        trueCount = player.room.count if decksRemaining == 0 else int(player.room.count / decksRemaining)
        if (trueCount > 1):
            player.betScalar = trueCount
        else:
            player.betScalar = 1.0
        return player.startingBet * player.betScalar

class Chaotic:
    name = "Chaotic"
    def NextMove(player):
        player.betScalar = random.random() * 8.0
        return player.startingBet * player.betScalar

class Gambler:
    name = "Gambler"
    def NextMove(player):
        return player.cash * 0.5

class CautiousGambler:
    name = "Cautious Gambler"
    def NextMove(player):
        return player.cash * 0.1

class RecklessGambler:
    name = "Reckless Gambler"
    def NextMove(player):
        return player.cash * 0.9

class AllIn:
    name = "All In"
    def NextMove(player):
        return player.cash
