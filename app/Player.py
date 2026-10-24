import random
import math
from Constants import *
import BettingStrategy
import PlayingStrategy
import inspect

def GetStrategies(module):
    strategies = []

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__ and hasattr(obj, "NextMove"):
            strategies.append(obj)

    return strategies

def GetRandomStrategy(module):
    return random.choice(GetStrategies(module))

# ----------------
# Player Classes
# ----------------

MAX_NAME_LENGTH = 32

class Hand:
    def __init__(self, bet):
        self.cards = []
        self.handValue = 0
        self.busted = 0
        self.bet = bet
        self.lastWinType = WinType.PUSH
        self.lastWinResult = WinResult.PUSH
        self.beenPaid = False
        self.canBlackjack = True

    def IsBlackjack(self):
        if not self.canBlackjack:
            return False

        if (len(self.cards) != 2):
            return False

        first = self.cards[0]
        second = self.cards[1]
        return (
            first.IsTenValue() and second.IsAce() or
            second.IsTenValue() and first.IsAce()
        )

class Player:

    class Stats:
        def __init__(self):
            self.highestCash = 0.0
            self.consecutiveWins = 0
            self.consecutiveLosses = 0
            self.totalWins = 0
            self.totalLosses = 0
            self.totalCashWinnings = 0.0
            self.totalCashLosses = 0.0
            self.highestBet = 0.0
            self.highestPayout = 0.0
            self.hits = 0
            self.stands = 0
            self.doubles = 0
            self.splits = 0
            self.blackjacks = 0
            self.totalHands = 0

    def __init__(self, room, cash = 1000.0, name = "Player"):
        self.role = PlayerRole.PLAYER
        self.room = room
        self.name = name[:MAX_NAME_LENGTH].strip(CURRENCY_SYMBOL)
        self.hands = []
        self.activeHand = 0
        self.cash = cash
        self.stats = Player.Stats()
        self.lastWinType = WinType.PUSH
        self.lastWinResult = WinResult.PUSH
        self.room.players.append(self)
        self.room.stats.playerHistory.append(self)
        self.bot = False
        room.log.OnPlayerJoin(self)

    def ResetHand(self):
        self.hands = [Hand(0.0)]
        self.activeHand = 0

    def CanBet(self):
        if (self.cash < self.room.minBet):
            return False
        return True

    def SetBet(self, bet):

        if not self.CanBet():
            self.hands[self.activeHand].bet = -1.0
            self.room.log.OnBetFailed(self)
            return False

        bet = math.floor(bet / self.room.minBet) * self.room.minBet
        bet = self.cash if (bet > self.cash) else bet
        bet = self.room.minBet if (bet < self.room.minBet) else bet
        self.hands[0].bet = bet
        self.cash -= bet
        self.room.stats.takenIn += bet
        if bet > self.room.stats.highestBet:
            self.room.stats.highestBet = bet
        if bet > self.stats.highestBet:
            self.stats.highestBet = bet
        self.stats.totalCashLosses += bet
        self.room.log.OnBetPlaced(self, bet)
        return True

    def DrawCard(self, handIndex = None):
        if handIndex is None:
            handIndex = self.activeHand
        card = self.room.GetNewCard()
        self.hands[handIndex].cards.append(card)
        self.EvaluateHand(handIndex)
        self.room.log.OnDrawCard(self, card)

    def DoAction(self, action):
        hand = self.hands[self.activeHand]
        self.room.log.OnAction(self, action)
        if action != Action.STAND:
            if action == Action.SPLIT:
                newHand = Hand(hand.bet)

                hand.canBlackjack = self.room.rules.blackjackOnSplit
                newHand.canBlackjack = self.room.rules.blackjackOnSplit

                newHand.cards.append(hand.cards.pop())

                self.cash -= hand.bet
                self.room.stats.takenIn += hand.bet
                self.stats.totalCashLosses += hand.bet
                self.hands.insert(self.activeHand + 1, newHand)

                self.DrawCard(self.activeHand)
                nextHand = self.activeHand + 1
                self.DrawCard(nextHand)

                self.stats.splits += 1
                return
            elif action == Action.DOUBLE:
                if self.CanDouble():
                    self.cash -= hand.bet
                    self.room.stats.takenIn += hand.bet
                    self.stats.totalCashLosses += hand.bet
                    hand.bet *= 2.0
                    self.stats.doubles += 1
            if action == Action.HIT:
                self.stats.hits += 1
            self.DrawCard()
        if action == Action.STAND:
            self.stats.stands += 1

    def EvaluateHand(self, hand):
        value = 0
        aces = 0
        for card in self.hands[hand].cards:
            value += card.GetValue()
            if card.IsAce():
                aces += 1
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1

        self.hands[hand].busted = value > 21
        self.hands[hand].handValue = value

    def CanSplit(self):
        hand = self.hands[self.activeHand]
        return (
            len(self.hands) < self.room.rules.splitLimit and
            len(hand.cards) == 2 and
            hand.cards[0].GetValue() == hand.cards[1].GetValue() and
            self.cash >= hand.bet
        )

    def CanDouble(self):
        return (
            len(self.hands[self.activeHand].cards) == 2 and
            self.cash >= self.hands[self.activeHand].bet and
            (self.room.rules.doubleAfterSplit or len(self.hands) == 1)
        )

    def GetAvailableActions(self):
        actions = [Action.HIT, Action.STAND]

        if self.CanDouble():
            actions.append(Action.DOUBLE)

        if self.CanSplit():
            actions.append(Action.SPLIT)

        return actions

    def IsHandComplete(self):
        hand = self.hands[self.activeHand]
        return hand.busted or hand.handValue >= 21

    def HasBlackjack(self):
        return self.hands[self.activeHand].IsBlackjack()

    def RoundResult(self):
        result = 0
        hand = self.hands[self.activeHand]
        dealerHand = self.room.dealer.hands[self.room.dealer.activeHand]

        dealerBJ = self.room.dealer.HasBlackjack()
        playerBJ = self.HasBlackjack()

        if dealerBJ and playerBJ:
            result = WinType.PUSH
            self.stats.blackjacks += 1
            self.room.stats.blackjacksPlayers += 1
        elif playerBJ:
            result = WinType.PLAYERBLACKJACK
            self.stats.blackjacks += 1
            self.room.stats.blackjacksPlayers += 1
        elif dealerBJ:
            result = WinType.DEALERBLACKJACK
        elif hand.busted:
            result = WinType.PLAYERBUST
        elif dealerHand.busted:
            result = WinType.DEALERBUST
        elif hand.handValue == dealerHand.handValue:
            result = WinType.PUSH
        elif dealerHand.handValue > hand.handValue:
            result = WinType.DEALERWIN
        else:
            result = WinType.PLAYERWIN

        hand.lastWinType = result
        hand.lastWinResult = WinResult.PUSH
        if (result > WinType.DEALERBUST):   # all enums above are player wins
            hand.lastWinResult = WinResult.LOSS
        elif (result): # type 0 is push
            hand.lastWinResult = WinResult.WIN

        return result

    def Payout(self):
        result = self.RoundResult()
        payout = 0.0
        bet = self.hands[self.activeHand].bet
        match result:
            case WinType.PUSH:
                payout = bet
            case WinType.PLAYERBLACKJACK:
                payout = bet * (self.room.rules.blackjackPayout + 1.0)
            case WinType.DEALERBUST:
                payout = bet * 2.0
            case WinType.PLAYERWIN:
                payout = bet * 2.0
        self.cash += payout
        self.room.stats.paidOut += payout
        if payout > self.room.stats.highestPayout:
            self.room.stats.highestPayout = payout
        if payout > self.stats.highestPayout:
            self.stats.highestPayout = payout
        if self.cash > self.stats.highestCash:
            self.stats.highestCash = self.cash
        self.stats.totalCashWinnings += payout
        self.hands[self.activeHand].beenPaid = True
        self.room.log.OnPayout(self, result, payout)

    def UpdateRoundResult(self):
        wins = sum(1 for hand in self.hands if hand.lastWinResult == WinResult.WIN)
        losses = sum(1 for hand in self.hands if hand.lastWinResult == WinResult.LOSS)

        if wins > losses:
            result = WinType.PLAYERWIN
            self.stats.consecutiveLosses = 0
            self.stats.totalWins += 1
            self.lastWinResult = WinResult.WIN
            self.stats.consecutiveWins = (
                self.stats.consecutiveWins + 1
                if self.lastWinResult == WinResult.WIN
                else 1
            )
        elif losses > wins:
            result = WinType.DEALERWIN
            self.stats.totalLosses += 1
            self.lastWinResult = WinResult.LOSS
            self.stats.consecutiveWins = 0
            self.stats.consecutiveLosses = (
                self.stats.consecutiveLosses + 1
                if self.lastWinResult == WinResult.LOSS
                else 1
            )
        else:
            result = WinType.PUSH
            self.lastWinResult = WinResult.PUSH

        self.stats.totalHands += len(self.hands)
        self.lastWinType = result

class Bot(Player):

    names = [
        "Remi",         "Max",          "Ben",          "Ninja",        "Crone",        "Deadeye",
        "Jericho",      "Albert",       "Cigaro",       "Tiger",        "Flash",        "Princess",
        "Dartagnan",    "Razor",        "Dagger",       "Reaper",       "Diesel",       "Bishop",
        "Hammer",       "Juno",         "Kodiak",       "The Baron",    "Blade",        "Maverick",
        "Gremlin",      "Cobra",        "Drifter",      "Warden",       "Bolt",         "Psycho",
        "Scar",         "Lazarus",      "Muzzle",       "Striker",      "Phantom",      "Ghost",
        "Fang",         "The Duke",     "Mantis",       "Grifter",      "Scab",         "Nero",
        "Spike",        "Tycoon",       "Voodoo",       "Priest",       "Iggy",         "Nova",
        "Dove",         "Calico",       "Rue",          "Rogue",        "Lark",         "Sable",
        "Vesper",       "Iris",         "Scythe",       "Banshee",      "Spite",        "Ransom",
        "Vandal",       "Static",       "Rivet",        "President",    "The Don",      "Veronica",
        "Calavera",     "Domino",       "Alyssa",       "Axe",          "Raven",        "Kane",
        "Echo",         "Octavia",      "Olivia",       "Ringo",        "Skeet",        "Pike",
        "Rider",        "Paxton",       "Blaine",       "Maya",         "Dante",        "Luna",
        "Vera",         "Aurora",       "Venom",        "Harry",        "Neon",         "Orlando",
        "Oracle",       "Switch",       "Axel",         "Roland",       "Colt",         "Victor",
        "Lyra",         "Gambino",      "Flint",        "Snake-eye",    "Kade",         "Hogan",
        "Casper",       "Maestro",      "Sloth",        "Grace",        "Azure",        "Angel",
        "Void",         "Marshall",     "Basil",        "Ant",          "Finch",        "Comet",
        "Gloom",        "Shadow",       "Tango",        "Hound",        "Rebus",        "Zion",
        "Sapphire",     "Fox",          "Ruby",         "Chief",        "Diablo",       "Quake",
        "Crow",         "Griffin",      "Savant",       "Hoax",         "Goose",        "Zor",
        "Kincaid",      "Hurg",
        ]

    def __init__(self, room, playStrategy = None,
                 _playStrategyArgs = None, betStrategy = None,
                 cash = None, name = "", startingBet = None):

        self.role = PlayerRole.BOT

        if _playStrategyArgs is None:
            _playStrategyArgs = []

        if name is None or name == "":
            usedNames = [player.name for player in room.players]
            name = random.choice(Bot.names)
            while name in usedNames:
                name = random.choice(Bot.names)

        if cash == None:
            cash = room.minBet * 20.0
        if startingBet == None:
            startingBet = room.minBet

        if playStrategy is None:
            playStrategy = GetRandomStrategy(PlayingStrategy)
            if not _playStrategyArgs and playStrategy.args:
                _playStrategyArgs = playStrategy.GetRandomArgs()

        if betStrategy is None:
            betStrategy = GetRandomStrategy(BettingStrategy)

        Player.__init__(self, room, cash, name)

        self.bot = True

        self._PlayStrategy = playStrategy
        self._playStrategyArgs = _playStrategyArgs
        self._BetStrategy = betStrategy
        self.startingBet = startingBet
        self.betScalar = 1.0

    def GetAction(self):
        actions = self.GetAvailableActions()
        action = self._PlayStrategy.NextMove(self)
        if action in actions:
            return action
        elif action == Action.DOUBLE:
            return Action.HIT
        return Action.STAND

class Dealer(Player):

    names = [
        "Anastasia",    "Adelina",      "Adriana",      "Alina",        "Amalia",       "Ana",
        "Brina",        "Danica",       "Ivanka",       "Kalina",       "Katerina",     "Larya",
        "Elena",        "Mila",         "Mira",         "Ava",          "Darya",        "Mara",
        "Marta",        "Natalya",      "Svetlana",     "Wanda",        "Zorya",        "Toskia",
        "Sveta",        "Zorana",       "Yanka",        "Sofia",        "Nadia",        "Sonya",
        "Tatiana",      "Katya",        "Daria",        "Olena",        "Lucia",        "Valentina",
        ]

    def __init__(self, room, name = ""):
        self.role = PlayerRole.DEALER
        self.room = room
        self._playStrategyArgs = [17]
        if name == "" or name == None:
            self.GetName()
        else:
            self.name = "Dealer " + name
        self.hands = [Hand(0.0)]
        self.activeHand = 0
        self.bot = True

    def GetName(self):
        self.name = "Dealer " + random.choice(Dealer.names)

    def GetAction(self):
        return PlayingStrategy.DrawUntil.NextMove(self)

    def DoAction(self, action):
        if action != Action.STAND:
            self.DrawCard()

    def ShouldCheckForBJ(self):
        upCard = self.hands[0].cards[0]
        return upCard.IsTenValue() or upCard.IsAce()
