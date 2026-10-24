from Constants import *
from Player import *
from Room import *
import random

class PyJack:
    def __init__(self, interface):
        self.rooms = []
        self.interface = interface

    def AddRoom(self, minBet = 50, rules = None, botsAutoJoin = True, seats = 4, dealerName = None):
        newRoom = Room(self.interface, float(minBet), rules, botsAutoJoin, seats, dealerName)
        newRoom.id = len(self.rooms)
        self.rooms.append(newRoom)
        return newRoom

    def AddPlayer(self, room, cash = 1000.0, name = "Player"):
        newPlayer = Player(room, cash, name)
        return newPlayer

    def AddBot(self, room, playStrategy = None,
               playStrategyArgs = None, betStrategy = None,
               cash = None, name = "", startingBet = None):
        if playStrategyArgs is None:
            playStrategyArgs = []
        newBot = Bot(room, playStrategy, playStrategyArgs, betStrategy, cash, name, startingBet)
        return newBot

    def Loop(self):
        while True:
            if not len(self.rooms):
                break

            for room in self.rooms:

                for player in room.kickList:
                    room.players.remove(player)
                room.kickList = []

                for name, cash in room.playerJoinList:
                    if len(room.players) >= room.seats:
                        break
                    kwargs = {}
                    if cash is not None:
                        kwargs["cash"] = cash
                    if name is not None:
                        kwargs["name"] = name
                    self.AddPlayer(room, **kwargs)
                room.playerJoinList = []

                if room.botsToJoin > 0:
                    for _ in range(room.botsToJoin):
                        if len(room.players) >= room.seats:
                            break
                        self.AddBot(room)
                    room.botsToJoin = 0

                if (room.botsAutoJoin and
                    len(room.players) < room.seats and
                    random.random() > 0.66):
                    self.AddBot(room)

                # BETTING PHASE
                room.SetGameState(GameState.BETTING)

                # copy player list in case someone gets kicked while betting
                playersTemp = room.players.copy()
                for player in playersTemp:
                    room.activePlayer = player
                    bet = 0.0
                    if player.bot:
                        bet = player._BetStrategy.NextMove(player)
                    else:
                        bet = self.interface.GetPlayerBet(player)
                    if player in room.players and not player.SetBet(bet):
                        room.players.remove(player)
                    if player.bot:
                        self.interface.Wait(room)
                room.activePlayer = None

                if not (len(room.players)):
                    self.AddBot(room)
                    continue

                # DEALING PHASE
                room.SetGameState(GameState.DEAL)

                for _ in range(2):
                    for player in room.players:
                        room.activePlayer = player
                        player.DrawCard()
                        self.interface.Wait(room, 0.3)
                    room.activePlayer = None
                    room.dealer.DrawCard()
                    self.interface.Wait(room, 0.3)

                self.interface.Wait(room, 0.05)

                dealerHasBlackjack = False

                if room.dealer.ShouldCheckForBJ():
                    room.log.OnDealerCheckBJ(room.dealer)
                    self.interface.Wait(room, 0.75)

                    dealerHasBlackjack = room.dealer.HasBlackjack()

                    if dealerHasBlackjack:
                        room.stats.blackjacksDealer += 1
                        room.log.OnDealerHasBJ(room.dealer)
                    else:
                        room.log.OnDealerNoBJ(room.dealer)

                    self.interface.Wait(room, 0.5)

                if not dealerHasBlackjack:

                    # PLAYER ACTION PHASE
                    room.SetGameState(GameState.PLAYERSDRAW)

                    totalBustedPlayers = 0
                    for player in room.players:
                        room.activePlayer = player
                        if player.bot:
                            self.interface.Wait(room, 0.2)
                        if player.HasBlackjack():
                            continue
                        handIdx = 0
                        while handIdx < len(player.hands):
                            player.activeHand = handIdx
                            while not player.IsHandComplete():
                                if player.bot:
                                    action = player.GetAction()
                                else:
                                    action = self.interface.GetPlayerAction(player)
                                player.DoAction(action)
                                if player.bot:
                                    self.interface.Wait(room, random.uniform(0.35, 0.75))
                                if action == Action.STAND or action == Action.DOUBLE:
                                    break
                            handIdx += 1
                        totalBustedPlayers += 1 if all(hand.busted for hand in player.hands) else 0
                    room.activePlayer = None

                    # DEALER ACTION PHASE
                    if totalBustedPlayers < len(room.players):
                        room.SetGameState(GameState.DEALERSDRAW)
                        self.interface.Wait(room, 0.5)
                        while not room.dealer.hands[room.dealer.activeHand].busted:
                            action = room.dealer.GetAction()

                            if action == Action.STAND:
                                break
                            room.dealer.DoAction(action)
                            self.interface.Wait(room, 0.5)


                # PAYOUT PHASE
                room.SetGameState(GameState.PAYOUT)

                for player in room.players:
                    room.activePlayer = player
                    for handIdx in range(len(player.hands)):
                        player.activeHand = handIdx
                        player.Payout()
                        self.interface.Wait(room)
                    player.UpdateRoundResult()
                room.activePlayer = None

                humans = 0
                for player in room.players:
                    if not player.bot:
                        humans += 1
                room.EndRound(humans)
                if humans == 0:
                    self.interface.Wait(room)

                room.SetGameState(GameState.IDLE)

