from Constants import *
import random

# ----------------
# Playing Strategies
# ----------------

class PlayStrategy:
    args = False
    def GetRandomArgs():
        return None

class DrawUntil:
    name = "Hit until"
    args = True

    def GetRandomArgs():
        return [random.choice([12, 13, 14, 15, 16, 16, 17, 17, 17, 18, 18, 19])]

    def NextMove(player):
        if (player.hands[player.activeHand].handValue < player._playStrategyArgs[0]):
            return Action.HIT
        return Action.STAND

class Basic(PlayStrategy):
    name = "Basic"

    table = [
    #    2  3  4  5  6  7  8  9  10 A
        [0, 2, 2, 2, 2, 0, 0, 0, 0, 0], # 9
        [2, 2, 2, 2, 2, 2, 2, 2, 0, 0], # 10
        [2, 2, 2, 2, 2, 2, 2, 2, 2, 0], # 11
        [0, 0, 1, 1, 1, 0, 0, 0, 0, 0], # 12
        [1, 1, 1, 1, 1, 0, 0, 0, 0, 0], # 13
        [1, 1, 1, 1, 1, 0, 0, 0, 0, 0], # 14
        [1, 1, 1, 1, 1, 0, 0, 0, 0, 0], # 15
        [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]  # 16
    ]

    splitTable = [
    #    2  3  4  5  6  7  8  9  10 A
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # A,A
        [3, 3, 3, 3, 3, 3, 0, 0, 0, 0], # 2,2
        [3, 3, 3, 3, 3, 3, 0, 0, 0, 0], # 3,3
        [0, 0, 0, 3, 3, 0, 0, 0, 0, 0], # 4,4
        [2, 2, 2, 2, 2, 2, 2, 2, 0, 0], # 5,5
        [3, 3, 3, 3, 3, 0, 0, 0, 0, 0], # 6,6
        [3, 3, 3, 3, 3, 3, 0, 0, 0, 0], # 7,7
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # 8,8
        [3, 3, 3, 3, 3, 1, 3, 3, 1, 1], # 9,9
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 10,10
    ]

    def GetDealerIndex(player):
        dealerCard = player.room.dealer.hands[player.room.dealer.activeHand].cards[0]
        if dealerCard.IsAce():
            return 9
        return 8 if dealerCard.IsTenValue() else dealerCard.GetValue() - 1

    def GetSplitIndex(player):
        card = player.hands[player.activeHand].cards[0]
        if card.IsAce():
            return 0
        return card.GetValue() - 1

    def NextMove(player):
        strategy = player._PlayStrategy

        hand = player.hands[player.activeHand]
        dealersIndex = strategy.GetDealerIndex(player)

        if player.CanSplit():
            splitIndex = strategy.GetSplitIndex(player)
            action = strategy.splitTable[splitIndex][dealersIndex]

            if action == Action.SPLIT:
                return Action.SPLIT

            # if split table says hit/stand/double, fall through using that action
            if action == Action.DOUBLE and not player.CanDouble():
                return Action.HIT

            return action

        if hand.handValue > 16:
            return Action.STAND

        if hand.handValue < 9:
            return Action.HIT

        action = strategy.table[hand.handValue - 9][dealersIndex]

        if action == Action.DOUBLE and not player.CanDouble():
            return Action.HIT

        return action

class UnskilledBasic(Basic):
    name = "Unskilled Basic"

    table = [
    #    2  3  4  5  6  7  8  9  10 A
        [0, 0, 2, 2, 2, 0, 0, 0, 0, 0],
        [2, 2, 2, 2, 2, 2, 0, 0, 0, 0],
        [2, 2, 2, 2, 2, 2, 2, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    ]

    splitTable = [
    #    2  3  4  5  6  7  8  9  10 A
        [3, 3, 3, 3, 3, 3, 0, 0, 0, 0],
        [3, 3, 3, 3, 3, 0, 0, 0, 0, 0],
        [3, 3, 3, 3, 3, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 3, 0, 0, 0, 0, 0],
        [2, 2, 2, 2, 2, 2, 0, 0, 0, 0],
        [3, 3, 3, 3, 3, 0, 0, 0, 0, 0],
        [3, 3, 3, 3, 3, 3, 1, 0, 0, 0],
        [3, 3, 3, 3, 3, 3, 0, 0, 0, 0],
        [3, 3, 3, 3, 3, 1, 1, 3, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]

class BadBasicSplitter(Basic):
    name = "Bad Basic Splitter"

    table = [
    #    2  3  4  5  6  7  8  9  10 A
        [0, 2, 2, 2, 2, 2, 2, 0, 0, 0], # 9
        [2, 2, 2, 2, 2, 2, 2, 2, 2, 0], # 10
        [2, 2, 2, 2, 2, 2, 2, 2, 2, 0], # 11
        [1, 1, 1, 1, 1, 0, 0, 0, 0, 0], # 12
        [1, 1, 1, 1, 1, 1, 0, 0, 0, 0], # 13
        [1, 1, 1, 1, 1, 1, 0, 0, 0, 0], # 14
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0], # 15
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 16
    ]

    splitTable = [
    #    2  3  4  5  6  7  8  9  10 A
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # A,A
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # 2,2
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # 3,3
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # 4,4
        [2, 2, 2, 2, 2, 2, 2, 2, 0, 0], # 5,5
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # 6,6
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # 7,7
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # 8,8
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 9,9
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 10,10
    ]

class DealerAware(PlayStrategy):
    name = "Dealer Aware"

    def NextMove(player):

        dealerHand = player.room.dealer.hands[player.room.dealer.activeHand]
        if dealerHand.cards[0].GetValue() >= 10:
            standAt = 17
        else:
            standAt = 13

        if player.hands[player.activeHand].handValue < standAt:
            return Action.HIT

        return Action.STAND

class AlwaysHit(PlayStrategy):
    name = "Always Hit"

    def NextMove(player):
        return Action.HIT

class AlwaysStand(PlayStrategy):
    name = "Always Stand"

    def NextMove(player):
        return Action.STAND
