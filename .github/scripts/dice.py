#!/usr/bin/env python3
import sys
import json
import random
import re
import os

DICE_EMOJI = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
DICE_BARS  = ['▒░░░░░', '▒▒░░░░', '▒▒▒░░░', '▒▒▒▒░░', '▒▒▒▒▒░', '▒▒▒▒▒▒']
DICE_MSG   = [
    "Ouch — the lowest roll possible!",
    "Not great, not terrible.",
    "Right in the middle.",
    "Above average!",
    "Almost the max!",
    "MAXIMUM ROLL! 🔥"
]

def main():
    if len(sys.argv) < 3:
        print("Usage: dice.py <issue_title> <username>")
        sys.exit(1)

    issue_title    = sys.argv[1].strip()
    player_username = sys.argv[2].strip()

    if not issue_title.lower().startswith('dice|'):
        print("INVALID")
        sys.exit(1)

    roll  = random.randint(1, 6)
    emoji = DICE_EMOJI[roll - 1]
    bar   = DICE_BARS[roll - 1]
    msg   = DICE_MSG[roll - 1]

    stats_file = 'dice_stats.json'
    if os.path.exists(stats_file):
        with open(stats_file) as f:
            stats = json.load(f)
    else:
        stats = {
            'total': 0,
            'distribution': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0},
            'last_roll': ''
        }

    stats['total'] += 1
    stats['distribution'][str(roll)] += 1
    stats['last_roll'] = f'@{player_username} rolled **{emoji} {roll}** — {msg}'

    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    d = stats['distribution']
    new_board = f"""<!-- DICE_BOARD_START -->
| ⚀ 1 | ⚁ 2 | ⚂ 3 | ⚃ 4 | ⚄ 5 | ⚅ 6 | 🎲 Total |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **{d['1']}** | **{d['2']}** | **{d['3']}** | **{d['4']}** | **{d['5']}** | **{d['6']}** | **{stats['total']}** |

> 🎲 *Last: {stats['last_roll']}*
<!-- DICE_BOARD_END -->"""

    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(
        r'<!-- DICE_BOARD_START -->.*?<!-- DICE_BOARD_END -->',
        new_board,
        content,
        flags=re.DOTALL
    )

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"RESULT:{roll}|EMOJI:{emoji}|USER:{player_username}|MSG:{msg}")

if __name__ == '__main__':
    main()
