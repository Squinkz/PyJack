
# ----------------
# Card Class
# ----------------

class Card:

    names = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    suitSymbols = ["♥", "♦", "♣", "♠"]

    def __init__(self, card, suit, deck):
        self.card = card
        self.suit = suit
        self.deck = deck

    def GetValue(self):
        if self.card == 0:
            return 11
        return 10 if self.card > 8 else self.card + 1

    def GetName(self):
        return Card.names[self.card]

    def GetSuitSymbol(self):
        return Card.suitSymbols[self.suit]

    def IsAce(self):
        return self.card == 0

    def IsTenValue(self):
        return self.card > 8

    def IsRed(self):
        return self.suit < 2