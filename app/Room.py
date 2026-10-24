import random
from Constants import *
from RoomLog import RoomLog
from Player import Dealer
from Card import Card

# ----------------
# Room Class
# ----------------

class GameRules:
    def __init__(
            self,
            decksInShoe = 6,
            splitLimit = 4,
            doubleAfterSplit = True,
            blackjackOnSplit = False,
            blackjackPayout = 3 / 2):
        self.decksInShoe = decksInShoe
        self.splitLimit = splitLimit
        self.doubleAfterSplit = doubleAfterSplit
        self.blackjackOnSplit = blackjackOnSplit
        self.blackjackPayout = blackjackPayout

class Room:

    class Stats:
        def __init__(self):
            self.cardsDealt = 0
            self.shoesDealt = 0
            self.paidOut = 0
            self.takenIn = 0
            self.highestPayout = 0
            self.highestBet = 0
            self.blackjacksDealer = 0
            self.blackjacksPlayers = 0
            self.playerHistory = []
            self.dealers = []

    def __init__(
            self,
            interface,
            minBet = 50,
            rules = None,
            botsAutoJoin = True,
            seats = 4,
            dealerName = None
    ):
        self.dealer = Dealer(self, dealerName)
        if rules == None:
            rules = GameRules()
        self.rules = rules
        self.minBet = minBet
        self.seats = seats
        self.state = GameState.IDLE
        self.previousState = GameState.IDLE
        self.count = 0
        self.cardsPlayed = 0
        self.cardsInShoe = 13 * 4 * self.rules.decksInShoe
        self.shoe = [[[False for _ in range(13)] for _ in range(4)] for _ in range(self.rules.decksInShoe)]
        self.players = []
        self.activePlayer = None
        self.stats = Room.Stats()
        self.botsAutoJoin = botsAutoJoin
        self.kickList = []
        self.playerJoinList = []
        self.botsToJoin = 0
        self.log = RoomLog(interface, self)

    def SetGameState(self, state):
        self.previousState = self.state
        self.state = state
        if (state == GameState.BETTING):
            for player in self.players:
                player.ResetHand()
            self.dealer.ResetHand()

        self.log.OnGameStateChange(state)

    def UpdateCount(self, card):
        if card.GetValue() <= 6:
            self.count += 1
        elif card.GetValue() >= 10:
            self.count -= 1

    def GetNewCard(self):

        if self.cardsPlayed >= self.cardsInShoe:
            self.ResetShoe()

        while (True):
            deck = int(random.random() * self.rules.decksInShoe)
            suit = int(random.random() * 4)
            card = int(random.random() * 13)
            if not self.shoe[deck][suit][card]:
                self.shoe[deck][suit][card] = True
                self.cardsPlayed += 1
                newCard = Card(card, suit, deck)
                self.stats.cardsDealt += 1
                self.UpdateCount(newCard)
                return newCard

    def EndRound(self, humans):
        self.log.OnRoundEnd(humans)

    def ResetShoe(self):
        self.shoe = [[[False for _ in range(13)] for _ in range(4)] for _ in range(self.rules.decksInShoe)]
        self.cardsPlayed = 0
        self.count = 0
        oldName = self.dealer.name
        self.stats.dealers.append(oldName)
        self.dealer.GetName()
        self.stats.shoesDealt += 1
        self.log.OnShoeReset(self.dealer.name, oldName)
