from Constants import *

class RoomLog:
    def __init__(self, interface, room):
        self.room = room
        self.interface = interface
        self.messages = []
        self.history = []

    def OnGameStateChange(self, state):
        self.LogMessage("")
        if (state == GameState.BETTING):
           self.LogMessage("Betting is now open!")
        elif (state == GameState.DEAL):
            self.LogMessage("Cards are being dealt...")
        elif (state == GameState.PLAYERSDRAW):
            self.LogMessage("Players are making decisions...")
        elif (state == GameState.DEALERSDRAW):
            self.LogMessage("Dealer is drawing cards...")
            self.LogMessage(self.room.dealer.name + " shows a card. (" + self.room.dealer.hands[0].cards[1].GetName() + ")")
        elif (state == GameState.PAYOUT):
            self.LogMessage("Hand over! Payout will commence shortly...")

    def OnPlayerJoin(self, player):
        self.LogMessage(player.name + " sits down at the table.")

    def OnBetFailed(self, player):
        self.LogMessage(player.name + " has run out of funds!")
        self.LogMessage(player.name + " walks away from the table.")

    def OnBetPlaced(self, player, bet):
        self.LogMessage(player.name + " bets " + FormatCurrency(bet))

    def OnAction(self, player, action):
        if action == Action.STAND:
            self.LogMessage(player.name + " stands.")
        elif action == Action.SPLIT:
            self.LogMessage(player.name + " splits.")
        elif action == Action.DOUBLE:
            self.LogMessage(player.name + " doubles down!")
        elif action == Action.HIT:
            self.LogMessage(player.name + " hits!")

    def OnDrawCard(self, player, card):
        hand = player.hands[player.activeHand]
        if player.role == PlayerRole.DEALER:
            if len(player.hands[0].cards) == 1:
                self.LogMessage(player.name + " shows a card. (" + card.GetName() + ")")
                return
            elif player.room.state >= GameState.DEALERSDRAW:
                self.LogMessage(player.name + " draws a card. (" + card.GetName() + ")")
                if hand.busted:
                    self.LogMessage(player.name + " busts!")
                return
            return
        self.LogMessage(player.name + " is dealt a card. (" + card.GetName() + ")")
        if hand.IsBlackjack():
            self.LogMessage(player.name + " has Blackjack!")
        elif hand.busted:
            self.LogMessage(player.name + " busts!")

    def OnPayout(self, player, result, payout):
        handLabel = ""
        if len(player.hands) > 1:
            handLabel = " (hand " + str(player.activeHand + 1) + ")"

        message = ""
        match result:
            case WinType.PUSH:
                message = "It's a push for " + player.name + handLabel + "! Bet returned."
            case WinType.PLAYERBLACKJACK:
                message = player.name + handLabel + " has Blackjack! Paid out " + FormatCurrency(payout) + "!"
            case WinType.DEALERBLACKJACK:
                message = player.room.dealer.name + " has Blackjack against " + player.name + handLabel + "! Bet lost!"
            case WinType.PLAYERBUST:
                message = player.name + handLabel + " bust! Bet lost!"
            case WinType.DEALERBUST:
                message = player.room.dealer.name + " bust against " + player.name + handLabel + "! Paid out " + FormatCurrency(payout) + "!"
            case WinType.DEALERWIN:
                message = player.room.dealer.name + " wins against " + player.name + handLabel + "! Bet lost!"
            case WinType.PLAYERWIN:
                message = player.name + handLabel + " wins! Paid out " + FormatCurrency(payout) + "!"
        self.LogMessage(message)

    def OnRoundEnd(self, humans):
        if humans:
            self.interface.OnRoundEnd(self.room)
        self.ResetMessages()

    def OnShoeReset(self, dealerName, oldDealerName):
        self.LogMessage("")
        self.LogMessage("\t\tALL DECKS RESHUFFLED. SHOE HAS BEEN REPLACED")
        self.LogMessage("")
        self.LogMessage(dealerName + " takes over from " + oldDealerName + ".")

    def OnDealerCheckBJ(self, dealer):
        self.LogMessage("")
        self.LogMessage(dealer.name + " is checking for Blackjack...")

    def OnDealerHasBJ(self, dealer):
        self.LogMessage(dealer.name + " has Blackjack!")

    def OnDealerNoBJ(self, dealer):
        self.LogMessage("...No Blackjack for " + dealer.name)

    def LogMessage(self, message):
        self.messages.append(message)

    def ResetMessages(self):
        self.history.extend(self.messages)
        self.messages = []