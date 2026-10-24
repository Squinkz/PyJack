from PyJack import PyJack
from ConsoleInterface import ConsoleInterface
from BettingStrategy import *
from PlayingStrategy import *
from Room import GameRules

if __name__ == "__main__":

    game = PyJack(ConsoleInterface(1.0))

    room = game.AddRoom(
        minBet = 50,
        rules = GameRules(
            decksInShoe = 6,
            splitLimit = 4,
            doubleAfterSplit = True,
            blackjackOnSplit = False,
            blackjackPayout = 3 / 2
            ),
        botsAutoJoin = True,
        seats = 4
        )

    player1 = game.AddPlayer(room, 2000.0, "Squink")

    game.Loop()
