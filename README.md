# PyJack

A console blackjack game written in Python for Windows. Play against the dealer alongside bots, or let the bots play and watch how their playing and betting strategies unfold.

This is an unfinished personal project. The idea was to compose the game from separate rooms, players, rules, and strategies, with a console interface that could eventually be swapped for a graphical one. That separation still needs work.

All code is hand-written, only this README document was partly generated with an LLM.

## Running

Requires Windows and Python 3.10 or newer. There are no third-party dependencies.

Run it in a terminal that supports ANSI colors and card suit characters. Give the window plenty of height, especially when players split their hands.

From the repository root:

```powershell
python app/main.py
```

By default, the game starts a four-seat table with six decks, a \$50 minimum bet, and a player named Squink with \$2,000. Bots join automatically. You can change the rules and starting players in `app/main.py`.

## Playing and entering commands

At the betting prompt, enter a number such as `50` or `100`, without the `$`. Bets are rounded down to a multiple of the table minimum, then limited to your available cash and the minimum bet. Inputs such as `nan` and `inf` can crash the game.

On your turn, type an action and press `Enter`. The prompt shows your available actions:

| Action | Accepted inputs |
| --- | --- |
| Hit | `hit`, `0`, `z` |
| Stand | `stand`, `stnd`, `1`, `x` |
| Double down | `double`, `dbl`, `2`, `c` |
| Split | `split`, `spl`, `splt`, `3`, `v` |

You can also enter the commands below at any bet, action, or end-of-round prompt. While the game is running, press `Space` to pause and enter commands.

After a command, the prompt stays open so you can enter another. Press `Enter` on an empty pause prompt to resume, or at the end of a hand to start the next round. Press `Enter` to close help and statistics screens too.

Commands and player lookups ignore case. Enter one command per line, with a single space before its arguments. Use the player's full name for lookups. Names entered with `add player` must be one word; the parser converts them to lowercase.

### Global commands

Arguments in `[brackets]` are optional. Replace `<name>` and `<number>` with a value. Aliases work in place of the first word: for example, `a bot` is the same as `add bot`.

| Command | Aliases | Effect |
| --- | --- | --- |
| `help` | `h` | Show the help screen. |
| `info table` | `i`, `stats`, `information`, `statistics` | Show table statistics. `info room` also works. |
| `info <name>` | `i`, `stats`, `information`, `statistics` | Show statistics and strategy details for a seated player or bot. |
| `add bot` | `a`, `join` | Add a bot next round, if a seat is available. |
| `add player [name] [cash]` | `a`, `join` | Add a human player next round. Defaults to `Player` with `1000` cash. To set cash, supply a name too. |
| `kick <name>` | `k`, `boot` | Remove a player or bot next round. |
| `kick bots` | `k`, `boot` | Remove all current bots next round. |
| `toggle autojoin` | `t`, `switch` | Enable or disable automatic bot joining. |
| `speed` | `sp` | Display the current speed multiplier. |
| `speed <number>` | `sp` | Set the speed multiplier: `1` is normal and `2` halves delays. Zero or negative values remove delays. |
| `quit` | `q`, `exit`, `stop` | Exit the application. |
| `lobby` | `l`, `m`, `menu` | Not implemented; displays a message. |

Examples:

```text
add player squink 2000
info squink
speed 2
toggle autojoin
kick bots
```

A few input quirks:

- `sp` runs the speed command, even though it is also listed as a split alias in the code. Use `split`, `v`, or `3` to split.
- Zero or negative speed skips the delays that check for `Space`, so pausing only works at a positive speed.
- Joining and removal are deferred until the next round. Queued joins are discarded if the table is full.

## Project layout

| File | Responsibility |
| --- | --- |
| `app/main.py` | Configure and launch the game. |
| `app/PyJack.py` | Coordinate rooms and the betting, dealing, action, and payout phases. |
| `app/Room.py` | Store table rules, shoe state, card count, and room statistics. |
| `app/Player.py` | Implement players, bots, dealer, hands, actions, and payouts. |
| `app/PlayingStrategy.py` | Bot playing strategies. |
| `app/BettingStrategy.py` | Bot betting strategies. |
| `app/ConsoleInterface.py` | Console drawing, input parsing, pauses, and display timing. |
| `app/RoomLog.py` | Format game messages and retain their history. |
| `app/Card.py`, `app/Constants.py`, `app/Color.py` | Card representation, shared values, and console colors. |

## Status

The game runs, but there are known bugs in input validation, split-hand statistics, and the displayed card count. It isn't suitable for drawing reliable conclusions about betting strategies.

There are no automated tests, and I may or may not come back to finish it.

## License

Released under the [MIT License](LICENSE).
