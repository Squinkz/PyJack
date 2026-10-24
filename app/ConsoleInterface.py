import os, sys, re, shutil, time, ctypes, msvcrt
from Constants import *
from Color import Color
from enum import IntEnum

class DrawMode(IntEnum):
    MESSAGES    = 0
    PLAYERSTATS = 1
    ROOMSTATS   = 2
    HELP        = 3

# ----------------
# Console
# ----------------

class ConsoleInterface:

    class ParserAliases:
        terminate   = ["q", "quit", "exit", "stop"]
        lobby       = ["l", "lobby", "m", "menu"]
        hit         = ["0", "z", "hit"]
        stand       = ["1", "x", "stnd", "stand"]
        double      = ["2", "c", "dbl", "double"]
        split       = ["3", "v", "sp", "spl", "splt", "split"]
        stats       = ["i", "info", "stats", "information", "statistics"]
        help        = ["h", "help"]
        add         = ["a", "add", "join"]
        kick        = ["k", "kick", "boot"]
        toggle      = ["t", "toggle", "switch"]
        speed       = ["sp", "speed"]

    class Colors:
        TITLE       = Color.BRIGHT_CYAN
        LONGBAR     = Color.CYAN
        DEALERBAR   = Color.BRIGHT_CYAN
        PLAYERBAR   = Color.BRIGHT_BLACK
        BET         = Color.BRIGHT_YELLOW
        BANKROLL    = Color.YELLOW
        BOT         = Color.BRIGHT_BLACK
        BUST        = Color.RED
        PUSH        = Color.YELLOW
        LOSS        = Color.RED
        WIN         = Color.GREEN
        ERROR       = Color.RED

    class DrawState:
        def __init__(self, mode, target = None):
            self.mode = mode
            self.target = target

    def __init__(self, speed = 1.0, width = 96, tabSize = 8, messageTickerHeight = 12):
        CI.EnableAnsi()
        print("\033[2J\033[H", end="")
        self.width = width
        self.height = shutil.get_terminal_size((width, 40)).lines
        self.heightPrevious = self.height
        self.widthPrevious = width
        self.tab = " " * tabSize
        self.messageTickerHeight = messageTickerHeight
        self.drawState = CI.DrawState(DrawMode.MESSAGES)
        self.speed = speed

    @staticmethod
    def EnableAnsi():
        if os.name != "nt":
            return

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)

        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)

    def CheckForInterrupt(self):
        if not msvcrt.kbhit():
            return False

        interrupted = False

        while msvcrt.kbhit():
            key = msvcrt.getwch()

            if key in ("\x00", "\xe0"):
                if msvcrt.kbhit():
                    msvcrt.getwch()
                continue

            if key == " ":
                interrupted = True

        return interrupted

    def CalcSpeed(self, wait):
        if self.speed <= 0:
            return 0.0
        return wait / self.speed

    def Wait(self, room, wait = 0.35):
        wait = self.CalcSpeed(wait)
        endTime = time.time() + wait
        while time.time() < endTime:
            self.DrawGame(room)
            if self.CheckForInterrupt():
                self.PauseAction(room)
                self.DrawGame(room)
                return
            time.sleep(0.02)

    def PauseAction(self, room):
        self.GetInput(["Paused", "Press Enter to continue"], str, room, " ")
        self.drawState = CI.DrawState(DrawMode.MESSAGES)

    def OnRoundEnd(self, room):
        self.ParseInput(["Hand Over", "Press Enter to continue"], str, room, " ")

    def GetPlayerBet(self, player):
        return self.ParseInput([player.name, "Enter bet:"], float, player.room, CURRENCY_SYMBOL)

    def GetPlayerAction(self, player):
        actions = player.GetAvailableActions()

        labels = {
            Action.HIT: "Hit",
            Action.STAND: "Stand",
            Action.DOUBLE: "Double",
            Action.SPLIT: "Split",
        }

        actionNames = [labels[action] for action in actions]
        if len(actionNames) == 2:
            actionText = actionNames[0] + " or " + actionNames[1]
        else:
            actionText = ", ".join(actionNames[:-1]) + " or " + actionNames[-1]

        prompt = [player.name if (len(player.hands) <= 1) else player.name + " (Hand " + str(player.activeHand + 1) + ")", actionText + "?"]
        action = -1
        while action == -1:
            action = self.ParseInput(prompt, str, player.room)
            if action not in actions:
                prompt = self.AddPromptMessage(prompt, "Please enter a valid action")
                action = -1

        return action

    def OverlayStrings(self, a, b):
        length = max(len(a), len(b))
        a = a.ljust(length)
        b = b.ljust(length)
        return "".join(bChar if bChar != " " else aChar for aChar, bChar in zip(a, b))

    def AddPromptMessage(self, prompt, error):
        if len(prompt) < 3:
            prompt.append(error)
        else:
            prompt[2] = error
        return prompt

    def FormatPromptLines(self, lines):
        name = lines[0]

        if len(lines) > 2:
            error = lines[2] + "   "
            errorPadded = error.rjust(self.width)

            line1 = self.OverlayStrings(name, errorPadded)

            nameEnd = len(name)
            errorStart = self.width - len(error)

            line1 = (
                Color.SetColor(CI.Colors.LONGBAR, "|| ") +
                Color.SetColor(Color.BOLD, line1[:nameEnd]) +
                line1[nameEnd:errorStart] +
                Color.SetColor(CI.Colors.ERROR, line1[errorStart:])
            )
        else:
            line1 = (
                Color.SetColor(CI.Colors.LONGBAR, "|| ") +
                Color.SetColor(Color.BOLD, name)
            )

        line2 = Color.SetColor(CI.Colors.LONGBAR, "||") + lines[1].rjust(len(self.tab * 5))

        return line1 + "\n" + line2.ljust(55)


    def GetInput(self, lines, inputType, room, mark):

        def ParseGlobalCommands(command, argument, lines):

            def FindPlayer(playerName):
                for player in room.players:
                    if player.name.lower() == playerName:
                        return player
                return None

            if command in CI.ParserAliases.terminate:
                os.system('cls' if os.name == 'nt' else 'clear')
                sys.exit("Application terminated by user")
                return True, lines

            elif command in CI.ParserAliases.lobby:
                lines = self.AddPromptMessage(lines, "Lobby not yet implemented!")
                return True, lines

            elif command in CI.ParserAliases.help:
                self.drawState = CI.DrawState(DrawMode.HELP)
                self.PauseAction(room)
                return True, lines

            elif command in CI.ParserAliases.stats:

                if argument == None:
                    lines = self.AddPromptMessage(lines, "Please enter info followed by table or a player name")
                    return True, lines

                elif argument == "table" or argument == "room":
                    self.drawState = CI.DrawState(DrawMode.ROOMSTATS)
                    self.PauseAction(room)
                    return True, lines

                foundPlayer = FindPlayer(argument)
                if foundPlayer:
                    self.drawState = CI.DrawState(DrawMode.PLAYERSTATS, foundPlayer)
                    self.PauseAction(room)
                    return True, lines

                lines = self.AddPromptMessage(lines, "Could not find Player " + argument)
                return True, lines

            elif command in CI.ParserAliases.add:

                args = argument.split() if argument else []

                if len(args) == 0:
                    lines = self.AddPromptMessage(lines, "Add 'bot' or 'player'?")
                    return True, lines

                if args[0] == "bot":
                    room.botsToJoin += 1
                    lines = self.AddPromptMessage(lines, "A bot will join once the current hand ends")
                    return True, lines

                elif args[0] == "player":
                    name = None
                    cash = None

                    if len(args) >= 2:
                        name = args[1]

                    if len(args) >= 3:
                        try:
                            cash = float(args[2])
                        except ValueError:
                            cash = None

                    room.playerJoinList.append([name, cash])
                    lines = self.AddPromptMessage(lines, "A player will join once the current hand ends")
                    return True, lines

                lines = self.AddPromptMessage(lines, "Add 'bot' or 'player'?")
                return True, lines

            elif command in CI.ParserAliases.kick:
                if argument == None or argument == "":
                    lines = self.AddPromptMessage(lines, "Please enter a player name")
                    return True, lines
                elif argument == "bots":
                    for player in room.players:
                        if player.bot and player not in room.kickList:
                            room.kickList.append(player)
                            lines = self.AddPromptMessage(lines, "All bots will be kicked once the current hand ends")
                    return True, lines
                foundPlayer = FindPlayer(argument)
                if foundPlayer and foundPlayer not in room.kickList:
                    room.kickList.append(foundPlayer)
                    lines = self.AddPromptMessage(lines, "Player " + argument + " will be kicked once the current hand ends")
                    return True, lines
                lines = self.AddPromptMessage(lines, "Could not find Player " + argument)
                return True, lines

            elif command in CI.ParserAliases.toggle:
                if argument == "autojoin":
                    room.botsAutoJoin = not room.botsAutoJoin
                    if room.botsAutoJoin:
                        lines = self.AddPromptMessage(lines, "Bots will now join the table")
                    else:
                        lines = self.AddPromptMessage(lines, "Bots will no longer join the table")
                return True, lines

            elif command in CI.ParserAliases.speed:
                if argument == None or argument == "":
                    lines = self.AddPromptMessage(lines, "Speed is currently " + str(self.speed) + "x")
                    return True, lines
                try:
                    speed = float(argument)
                except (TypeError, ValueError):
                    lines = self.AddPromptMessage(lines, "Please enter a number")
                    return True, lines

                self.speed = speed
                lines = self.AddPromptMessage(lines, "Speed set to " + str(speed) + "x")
                return True, lines

            return False, lines

        while True:
            text = self.FormatPromptLines(lines)
            text += mark + " "
            self.DrawGame(room)
            inp = input("\033[2A" + "\033[2K" + text)
            self.DrawGame(room)
            inp = inp.lower().lstrip().split(" ", 1)

            command = inp[0]
            argument = inp[1] if len(inp) > 1 else None
            didAction, lines = ParseGlobalCommands(command, argument, lines)
            if didAction:
                continue

            try:
                inp[0] = inputType(inp[0])
                break
            except ValueError:
                typeName = getattr(inputType, "__name__", str(inputType))
                lines = self.AddPromptMessage(lines, "Please enter a " + typeName)

        return inp[0]

    def ParseInput(self, lines, inputType, room, mark = ">"):

        if room.state == GameState.BETTING:
            return self.GetInput(lines, inputType, room, mark)

        elif room.state == GameState.PLAYERSDRAW:
            action = -1
            while action == -1:
                inp = self.GetInput(lines, inputType, room, mark)
                inp = inp.lower()
                if inp in CI.ParserAliases.hit:
                    action = 0
                elif inp in CI.ParserAliases.stand:
                    action = 1
                elif inp in CI.ParserAliases.double:
                    action = 2
                elif inp in CI.ParserAliases.split:
                    action = 3
                else:
                    lines = self.AddPromptMessage(lines, "Please enter a valid action")
            return action

        inp = self.GetInput(lines, inputType, room, mark)
        return None

    def DrawGame(self, room):

        def BlankLine(end = "\n"):
            return " " * self.width + end

        def ColorPhrase(text, phrase, color, restoreColor = Color.RESET):
            message = ""
            i = 0

            while i < len(text):
                if text.startswith(phrase, i):
                    message += Color.SetColor(color, phrase) + restoreColor
                    i += len(phrase)
                else:
                    message += text[i]
                    i += 1

            return message

        def ColorCash(text):
            message = ""
            i = 0
            while i < len(text):
                isNegativeCurrency = (
                    text[i] == "-" and
                    i + 1 < len(text) and
                    text[i + 1] == CURRENCY_SYMBOL
                )
                isCurrency = text[i] == CURRENCY_SYMBOL
                if not isCurrency and not isNegativeCurrency:
                    message += text[i]
                    i += 1
                    continue
                start = i
                if isNegativeCurrency:
                    i += 2
                else:
                    i += 1
                while i < len(text) and text[i].isdigit():
                    i += 1
                message += Color.SetColor(CI.Colors.BET, text[start:i])
            return message

        def ColorParentheses(text, color):
            return re.sub(
                r"\([^)]*\)",
                lambda match: Color.SetColor(color, match.group(0)),
                text
            )

        def Highlight(text):
            return Color.REVERSE + text.replace(Color.RESET, Color.RESET + Color.REVERSE) + Color.RESET

        def FormatName(name, size):
            name = str(name)
            if len(name) > size:
                return name[:size - 4] + "... "
            return name.ljust(size)

        def Bar(suffix = "\n"):
            return Color.SetColor(CI.Colors.LONGBAR, ("=" * self.width) + suffix)

        def ShortBar(suffix = "\n"):
            return ("-" * (self.width - (len(self.tab) + 1))) + " " + suffix

        def Heading():
            message = Bar()
            border = Color.SetColor(CI.Colors.LONGBAR, "||")
            title = Color.SetColor(CI.Colors.TITLE, ("21 BLACKJACK (Table " + str(room.id + 1) + ")").center(self.width - 4))
            message += border + title + border + "\n"
            message += Bar()
            return message

        def DeckStatus():
            totalCards = 52 * room.rules.decksInShoe
            decksRemaining = (totalCards - room.cardsPlayed) / 52.0
            trueCount = room.count if decksRemaining == 0 else int(room.count / decksRemaining)
            countLbl =  ("  Count: " + str(room.count)).ljust(len(self.tab * 2))
            tCountLbl = ("  True Count: " + str(trueCount)).ljust(len(self.tab * 2))
            dealtLbl = ("Cards Dealt: " + str(room.cardsPlayed) + "/" + str(totalCards)).rjust(self.width - 2)

            return Color.SetColor(CI.Colors.DEALERBAR, self.OverlayStrings(countLbl + tCountLbl, dealtLbl) + "\n\n")

        def StyleText(text, color, restoreColor = Color.RESET):
            return Color.SetColor(color, text) + restoreColor

        def GetBaseMessageColor(line):
            words = line.lower()

            if "push" in words:
                return CI.Colors.PUSH
            if "paid" in words or "wins!" in words:
                return CI.Colors.WIN
            if "lost!" in words:
                return CI.Colors.LOSS

            return Color.RESET

        def ColorMessageLine(line):
            line = line.ljust(self.width)
            baseColor = GetBaseMessageColor(line)

            patterns = [
                (r"-?\$\d+", CI.Colors.BET),

                (r"\bbusts?[.!]?(?=\s|$)", CI.Colors.LOSS),

                (r"\bblackjack[.!]?(?=\s|$)", CI.Colors.WIN),
                (r"\bpush[.!]?(?=\s|$)", CI.Colors.PUSH),

                (r"\bhits[.!]?(?=\s|$)", CI.Colors.LONGBAR),
                (r"\bdoubles down[.!]?(?=\s|$)", CI.Colors.LONGBAR),
                (r"\bsplits[.!]?(?=\s|$)", CI.Colors.LONGBAR),
                (r"\bstands[.!]?(?=\s|$)", CI.Colors.PUSH),
            ]

            message = ""
            i = 0

            while i < len(line):
                matchFound = False

                for pattern, color in patterns:
                    match = re.match(pattern, line[i:], re.IGNORECASE)
                    if match:
                        text = match.group(0)
                        message += StyleText(text, color, baseColor)
                        i += len(text)
                        matchFound = True
                        break

                if not matchFound:
                    message += line[i]
                    i += 1

            if baseColor != Color.RESET:
                return Color.SetColor(baseColor, message)

            return message

        def Messages(lines):
            visible = lines[-self.messageTickerHeight:]
            visible = [""] * (self.messageTickerHeight - len(visible)) + visible

            message = ""
            for line in visible:
                if self.drawState.mode == DrawMode.MESSAGES:
                    line = ColorMessageLine(line)
                    line = ColorParentheses(line, CI.Colors.PUSH)
                else:
                    line = ColorCash(line.ljust(self.width))

                message += " " + line + "\n"

            message += Bar() + BlankLine()
            return message

        def Help():

            lines = []
            third = self.width // 3
            col = CI.Colors.LONGBAR

            a = Color.SetColor(col, "add bot".ljust(third))       + "Add a bot to the table".ljust(third)
            b = Color.SetColor(col, "add player [name] [cash]".ljust(third)) + "Add a player to the table".ljust(third)
            c = Color.SetColor(col, "kick [name]".ljust(third))   + "Kick the specified player or bot".ljust(third)
            d = Color.SetColor(col, "kick bots".ljust(third))     + "Kick all bots".ljust(third)
            e = Color.SetColor(col, "info [name]".ljust(third))   + "See stats on the specified player or bot".ljust(third)
            f = Color.SetColor(col, "info table".ljust(third))    + "See stats on the current table".ljust(third)
            g = Color.SetColor(col, "speed [value]".ljust(third)) + "Set the game speed".ljust(third)
            h = Color.SetColor(col, "toggle autojoin".ljust(third))  + "Toggle whether bots join automatically".ljust(third)

            lines.append(Color.SetColor(CI.Colors.TITLE, (" Help Menu ").center(self.width, "-")))
            lines.append(a)
            lines.append(b)
            lines.append(c)
            lines.append(d)
            lines.append(e)
            lines.append(f)
            lines.append(g)
            lines.append(h)

            while len(lines) < self.messageTickerHeight:
                lines.append("")
            return Messages(lines)

        def RoomStats():
            lines = []

            quarter = self.width // 4
            third = self.width // 3

            paidOut       = "  Cash Returned".ljust(quarter)  + FormatCurrency(room.stats.paidOut).ljust(quarter)
            takenIn       = "  Cash Taken In".ljust(quarter)  + FormatCurrency(room.stats.takenIn).ljust(quarter)
            highestPayout = "  Highest Payout".ljust(quarter) + FormatCurrency(room.stats.highestPayout).ljust(quarter)
            highestBet    = "  Highest Bet".ljust(quarter)    + FormatCurrency(room.stats.highestBet).ljust(quarter)
            cashNet       = "  House Profit".ljust(quarter)   + FormatCurrency(room.stats.takenIn - room.stats.paidOut).ljust(quarter)

            cardsDealt    = "  Cards Dealt".ljust(quarter)    + Color.SetColor(CI.Colors.PUSH, str(room.stats.cardsDealt).ljust(quarter))
            shoesDealt    = "  Shoes Cleared".ljust(quarter)  + Color.SetColor(CI.Colors.PUSH, str(room.stats.shoesDealt).ljust(quarter))
            bjDealer      = "  Dealer Blackjacks".ljust(quarter)  + Color.SetColor(CI.Colors.WIN, str(room.stats.blackjacksDealer).ljust(quarter))
            bjPlayer      = "  Player Blackjacks".ljust(quarter)  + Color.SetColor(CI.Colors.WIN, str(room.stats.blackjacksPlayers).ljust(quarter))

            lines.append(Color.SetColor(CI.Colors.TITLE, ( "Table " + str(room.id + 1)).ljust(third, "-").center(self.width, "-")))
            lines.append(cashNet + highestBet)
            lines.append(takenIn + highestPayout)
            lines.append(paidOut)
            # lines.append(highestBet)
            # lines.append(highestPayout)
            lines.append("")
            lines.append(cardsDealt + bjDealer)
            lines.append(shoesDealt + bjPlayer)

            while len(lines) < self.messageTickerHeight:
                lines.append("")

            return Messages(lines)

        def PlayerStats(player):
            lines = []

            prefix = ("(Bot)  ") if player.bot else ""

            quarter = self.width // 4
            third = self.width // 3
            half = self.width // 2

            highestCash   = "  Highest Balance".ljust(quarter) + FormatCurrency(player.stats.highestCash).ljust(quarter)
            cashWon       = "  Total Winnings".ljust(quarter)   + FormatCurrency(player.stats.totalCashWinnings).ljust(quarter)
            cashLost      = "  Total Wagered".ljust(quarter)    + FormatCurrency(player.stats.totalCashLosses).ljust(quarter)
            highestBest   = "  Largest Bet".ljust(quarter)  + FormatCurrency(player.stats.highestBet).ljust(quarter)
            highestPayout = "  Biggest Win".ljust(quarter)  + FormatCurrency(player.stats.highestPayout).ljust(quarter)
            cashNet       = "  Net Profit".ljust(quarter)   + FormatCurrency(player.stats.totalCashWinnings - player.stats.totalCashLosses).ljust(quarter)

            hands         = "  Hands Played".ljust(quarter) + Color.SetColor(CI.Colors.PUSH, str(player.stats.totalHands).ljust(quarter))

            wins          = "  Hands Won".ljust(quarter)    + Color.SetColor(CI.Colors.WIN, str(player.stats.totalWins).ljust(quarter))
            losses        = "  Hands Lost".ljust(quarter)   + Color.SetColor(CI.Colors.LOSS, str(player.stats.totalLosses).ljust(quarter))
            winStreak     = "  Win Streak".ljust(quarter)   + Color.SetColor(CI.Colors.WIN, str(player.stats.consecutiveWins).ljust(quarter))
            lossStreak    = "  Loss Streak".ljust(quarter)  + Color.SetColor(CI.Colors.LOSS, str(player.stats.consecutiveLosses).ljust(quarter))
            percent = format(((float(player.stats.totalWins) / float(player.stats.totalHands)) * 100.0) if player.stats.totalHands != 0 else 0.0, ".2f")
            winpercent    = "  Win Percent".ljust(quarter)  + Color.SetColor(CI.Colors.WIN, (str(percent) + "%").ljust(quarter))

            hits          = "  Hits".ljust(quarter)        + Color.SetColor(CI.Colors.LONGBAR, str(player.stats.hits).ljust(quarter))
            stands        = "  Stands".ljust(quarter)      + Color.SetColor(CI.Colors.LONGBAR, str(player.stats.stands).ljust(quarter))
            doubles       = "  Doubles".ljust(quarter)     + Color.SetColor(CI.Colors.LONGBAR, str(player.stats.doubles).ljust(quarter))
            splits        = "  Splits".ljust(quarter)      + Color.SetColor(CI.Colors.LONGBAR, str(player.stats.splits).ljust(quarter))
            blackjacks    = "  Blackjacks".ljust(quarter)  + Color.SetColor(CI.Colors.LONGBAR, str(player.stats.blackjacks).ljust(quarter))

            lines.append(Color.SetColor(CI.Colors.TITLE, ( " " + prefix + player.name + " -").ljust(third, "-").center(self.width, "-")))
            lines.append(hands      + winpercent)
            lines.append(wins       + cashNet)
            lines.append(winStreak  + cashWon)
            lines.append(losses     + cashLost)
            lines.append(lossStreak + highestCash)
            lines.append(blackjacks + highestBest)
            lines.append(hits       + highestPayout)
            lines.append(stands      )

            betStrat = " " * half
            playStrat = " " * half
            if player.bot:
                betStrat   = "  Bet Strategy".ljust(quarter)   + Color.SetColor(CI.Colors.PUSH, str(player._BetStrategy.name).ljust(quarter))
                playStratName = (player._PlayStrategy.name + " " + (str(player._playStrategyArgs[0]) if player._PlayStrategy.args else ""))
                playStrat  = "  Play Strategy".ljust(quarter)  + Color.SetColor(CI.Colors.PUSH, playStratName).ljust(quarter)

            lines.append(doubles + betStrat)
            lines.append(splits  + playStrat)

            while len(lines) < self.messageTickerHeight:
                lines.append("")

            return Messages(lines)

        def StyledCard(card):
            suitColor = Color.BRIGHT_RED if card.IsRed() else Color.WHITE
            cardText = Color.SetColor(suitColor, (" " + card.GetName() + card.GetSuitSymbol() + " ").rjust(5))
            padding = " " * (len(self.tab) - 5)
            return Highlight(cardText) + padding

        def DealerHand():

            dealer = room.dealer

            hand = dealer.hands[dealer.activeHand]

            message = ((self.tab * 3) + dealer.name).ljust(self.width)
            message = Color.SetColor(Color.BOLD, message) + "\n"

            message += self.tab + Color.SetColor(CI.Colors.DEALERBAR, ShortBar())

            busted = self.tab
            if hand.busted:
                busted = Color.SetColor(CI.Colors.BUST, " Bust!".ljust(len(self.tab)))
            elif dealer.HasBlackjack() and room.state > GameState.DEALERSDRAW:
                busted = Color.SetColor(CI.Colors.WIN, " BJ!".ljust(len(self.tab)))

            handLine = ""

            if dealer.room.state < GameState.DEAL:
                handLine += self.tab + ("(0)").ljust(len(self.tab))

            elif dealer.room.state < GameState.DEALERSDRAW:
                if len(hand.cards) == 0:
                    handLine += self.tab + ("(0)").ljust(len(self.tab))
                elif len(hand.cards) == 1:
                    handLine += busted + ("(" + str(hand.cards[0].GetValue()) + ")").ljust(len(self.tab))
                    handLine += StyledCard(hand.cards[0])
                else:
                    handLine += busted + ("(" + str(hand.cards[0].GetValue()) + ")").ljust(len(self.tab))
                    handLine += StyledCard(hand.cards[0])
                    handLine += Highlight(Color.SetColor(Color.BRIGHT_BLACK, ("  -  ")))

            else:
                handLine += busted + ("(" + str(hand.handValue) + ")").ljust(len(self.tab))
                for card in hand.cards:
                    handLine += StyledCard(card)

            if (len(hand.cards) + 2) * 8 < self.width:
                handLine += self.tab * ((self.width // len(self.tab)) - (len(hand.cards) + 2))

            message += handLine + "\n"
            return message + BlankLine() + BlankLine()

        def PlayerHand(player):
            message = ""

            if player == None:
                message += BlankLine() + self.tab + Color.SetColor(CI.Colors.PLAYERBAR, ShortBar(""))
                message += "\n" + self.tab + ("(0)").ljust(len(self.tab))
                return message + BlankLine() + BlankLine()

            else:

                # Name
                # --------------------------

                isActiveRow = (
                        (room.state == GameState.BETTING or
                         room.state == GameState.PLAYERSDRAW or
                         room.state == GameState.PAYOUT) and
                        player == player.room.activePlayer
                    )

                botText = "(Bot)".ljust(len(self.tab)) if player.bot else self.tab

                name = (self.tab + botText + FormatName(player.name, len(self.tab * 3))).ljust(self.width - 2)
                cash = (str(FormatCurrency(player.cash)).rjust(len(self.tab * 2)) + ("Bet: " + str(FormatCurrency(player.hands[0].bet))).rjust(len(self.tab * 2))).rjust(self.width - 2) + "  "
                message += self.OverlayStrings(name, cash)

                message = ColorCash(message)

                if player in player.room.kickList:
                    message = Color.SetColor(Color.RED, message)
                    message = ColorPhrase(message, "(Bot)", CI.Colors.BOT, Color.RED)
                else:
                    message = ColorPhrase(message, "(Bot)", CI.Colors.BOT)

                message += "\n"

                if isActiveRow:
                    message = Highlight(message)

                message += self.tab + Color.SetColor(CI.Colors.PLAYERBAR, ShortBar(""))

                # Cards
                # --------------------------

                for hand in player.hands:

                    handLine = ""

                    info = ""

                    if player.room.state == GameState.PAYOUT and hand.beenPaid:
                        if hand.lastWinResult == WinResult.PUSH:
                            info = Color.SetColor(CI.Colors.PUSH, "Push".center(len(self.tab)))
                        elif hand.lastWinResult == WinResult.WIN:
                            info = Color.SetColor(CI.Colors.WIN, "Won!".center(len(self.tab)))
                        elif hand.lastWinResult == WinResult.LOSS:
                            info = Color.SetColor(CI.Colors.LOSS, "Lost!".center(len(self.tab)))
                    elif hand.busted:
                        info = Color.SetColor(CI.Colors.BUST, "Bust!".center(len(self.tab)))
                    elif hand.IsBlackjack():
                        info = Color.SetColor(CI.Colors.WIN, "BJ!".center(len(self.tab)))
                    else:
                        info = self.tab

                    isActiveRow = (
                        room.state == GameState.PLAYERSDRAW and
                        player == player.room.activePlayer and
                        player.hands[player.activeHand] == hand
                    )

                    if isActiveRow:
                        handLine += "\n" + info + ("(" + str(hand.handValue) + ") >>").ljust(len(self.tab))
                    else:
                        handLine += "\n" + info + ("(" + str(hand.handValue) + ")").ljust(len(self.tab))

                    for card in hand.cards:
                        handLine += StyledCard(card)
                    if (len(hand.cards) + 2) * 8 < self.width:
                        handLine += self.tab * ((self.width // len(self.tab)) - (len(hand.cards) + 2))

                    message += handLine

                return message + BlankLine() + BlankLine()

        def Menu():
            twoTab = len(self.tab * 2)
            option1 = "Quit"
            option2 = "Help"
            option3 = "Info"
            option4 = "Lobby"
            message = option4.rjust(twoTab) + option3.rjust(twoTab) + option2.rjust(twoTab) + option1.rjust(twoTab)
            message = message.rjust(self.width - 2) + "  "
            message = ColorPhrase(
                        ColorPhrase(
                            ColorPhrase(
                                ColorPhrase(
                                    message, "Q", Color.UNDERLINE
                                    ), "H", Color.UNDERLINE
                                ), "I", Color.UNDERLINE
                            ), "L", Color.UNDERLINE
                        )
            message += "\n" + Bar("") + "\n"
            return message

        self.widthPrevious = self.width
        self.heightPrevious = self.height

        size = shutil.get_terminal_size((96, 40))
        self.width = min(max(size.columns, 64), 96)
        self.height = size.lines

        if self.widthPrevious != self.width or self.heightPrevious != self.height:
            os.system('cls' if os.name == 'nt' else 'clear')

        screen  = Heading()
        screen += DeckStatus()

        match self.drawState.mode:
            case DrawMode.MESSAGES:
                screen += Messages(room.log.messages)
            case DrawMode.HELP:
                screen += Help()
            case DrawMode.PLAYERSTATS:
                screen += PlayerStats(self.drawState.target)
            case DrawMode.ROOMSTATS:
                screen += RoomStats()

        screen += DealerHand()

        for player in room.players:
            if self.drawState.mode == DrawMode.PLAYERSTATS:
                if self.drawState.target == player:
                    screen += PlayerHand(self.drawState.target)
                else:
                    screen += PlayerHand(None)
            else:
                screen += PlayerHand(player)
        if len(room.players) < room.seats:
            for _ in range(room.seats - len(room.players)):
                screen += PlayerHand(None)

        screen += Menu()

        # Prompt area:
        screen += BlankLine() + BlankLine()

        lineCount = len(screen.splitlines())
        if lineCount > self.height:
            os.system('cls' if os.name == 'nt' else 'clear')

        print("\033[H" + screen, end="")

CI = ConsoleInterface