#!/usr/bin/env python3
import sys
import json
import random
import re
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: rps.py <issue_title> <username>")
        sys.exit(1)

    issue_title = sys.argv[1].strip()
    player_username = sys.argv[2].strip()

    choices = ['rock', 'paper', 'scissors']
    emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}

    parts = issue_title.lower().split('|')
    if len(parts) < 2 or parts[1].strip() not in choices:
        print("INVALID")
        sys.exit(1)

    player_choice = parts[1].strip()
    bot_choice = random.choice(choices)

    wins = {'rock': 'scissors', 'paper': 'rock', 'scissors': 'paper'}
    if player_choice == bot_choice:
        result = 'draw'
    elif wins[player_choice] == bot_choice:
        result = 'player'
    else:
        result = 'bot'

    # Load stats
    stats_file = 'rps_stats.json'
    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            stats = json.load(f)
    else:
        stats = {'player_wins': 0, 'bot_wins': 0, 'draws': 0, 'total': 0, 'last_game': ''}

    stats['total'] += 1
    pe = emojis[player_choice]
    be = emojis[bot_choice]

    if result == 'player':
        stats['player_wins'] += 1
        stats['last_game'] = f'@{player_username} played {pe} · Bot played {be} · **You won!** 🎉'
    elif result == 'bot':
        stats['bot_wins'] += 1
        stats['last_game'] = f'@{player_username} played {pe} · Bot played {be} · **Bot won!** 🤖'
    else:
        stats['draws'] += 1
        stats['last_game'] = f'@{player_username} played {pe} · Bot played {be} · **Draw!** 🤝'

    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    # Update README scoreboard section
    new_board = f"""<!-- RPS_SCOREBOARD_START -->
| 👤 You Win | 🤖 Bot Wins | 🤝 Draws | 🎮 Total |
|:---:|:---:|:---:|:---:|
| **{stats['player_wins']}** | **{stats['bot_wins']}** | **{stats['draws']}** | **{stats['total']}** |

> 🕹️ *Last: {stats['last_game']}*
<!-- RPS_SCOREBOARD_END -->"""

    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(
        r'<!-- RPS_SCOREBOARD_START -->.*?<!-- RPS_SCOREBOARD_END -->',
        new_board,
        content,
        flags=re.DOTALL
    )

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"RESULT:{result}|PC:{player_choice}|BC:{bot_choice}|USER:{player_username}")

if __name__ == '__main__':
    main()
