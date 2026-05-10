#!/usr/bin/env python3
"""
Renders GitHub contribution data as a code activity spectrogram SVG.
Intensity mapped to a dark→violet→purple→cyan color scale (like a signal spectrogram).
"""

import os
import sys
import requests
from datetime import datetime

USERNAME = os.environ.get('GITHUB_USERNAME', 'Sur27codes')
TOKEN    = os.environ.get('GITHUB_TOKEN', '')

GQL = '''{ user(login: "%s") { contributionsCollection {
  contributionCalendar { totalContributions weeks {
    contributionDays { contributionCount date weekday }
  }}
}}}''' % USERNAME


def fetch():
    r = requests.post(
        'https://api.github.com/graphql',
        json={'query': GQL},
        headers={'Authorization': f'bearer {TOKEN}'},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()['data']['user']['contributionsCollection']['contributionCalendar']


def color_for(n):
    # plasma-inspired: black → deep violet → purple → lavender → cyan → ice white
    if n == 0:  return '#0d1117'
    if n <= 1:  return '#1e1040'
    if n <= 3:  return '#3b0764'
    if n <= 6:  return '#6d28d9'
    if n <= 11: return '#8b5cf6'
    if n <= 18: return '#a78bfa'
    if n <= 28: return '#38bdf8'
    return '#e0f9ff'


def render(cal):
    weeks = cal['weeks']
    total = cal['totalContributions']
    today = datetime.now().strftime('%Y-%m-%d')

    # ── Layout constants ──────────────────────────────────────────────────────
    CELL  = 12          # cell square size
    GAP   = 2           # gap between cells
    STEP  = CELL + GAP  # 14 px per column/row
    LM    = 38          # left margin (day labels)
    TM    = 54          # top margin (header)
    NW    = len(weeks)  # number of week columns
    GRID_W = NW * STEP
    GRID_H = 7  * STEP  # 98 px
    CB_X  = LM + GRID_W + 18   # colorbar x
    SVG_W = CB_X + 56          # total width
    SVG_H = TM + GRID_H + 52   # header + grid + x-axis + sparkline + footer

    L = []
    def e(s): L.append(s)

    # ── SVG header ────────────────────────────────────────────────────────────
    e(f'<svg xmlns="http://www.w3.org/2000/svg" '
      f'width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">')

    # Background
    e(f'<rect width="{SVG_W}" height="{SVG_H}" rx="10" fill="#0d1117"/>')

    # Left accent bar
    e(f'<rect x="0" y="0" width="3" height="{SVG_H}" rx="1" fill="#a78bfa" fill-opacity="0.85"/>')

    # Pulsing border
    e(f'<rect x="1" y="1" width="{SVG_W-2}" height="{SVG_H-2}" rx="9" '
      f'fill="none" stroke="#a78bfa" stroke-width="1">'
      f'<animate attributeName="stroke-opacity" values="0.18;0.5;0.18" dur="3s" repeatCount="indefinite"/>'
      f'</rect>')

    # ── Header text ───────────────────────────────────────────────────────────
    e(f'<text x="{LM}" y="20" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="11" font-weight="bold" fill="#a78bfa" letter-spacing="3">'
      f'CODE ACTIVITY SPECTROGRAM</text>')
    e(f'<text x="{SVG_W-8}" y="20" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="10" fill="#6e7681" text-anchor="end">{USERNAME}</text>')
    e(f'<text x="{LM}" y="36" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="9" fill="#4d5562" letter-spacing="1">'
      f'TEMPORAL FREQUENCY ANALYSIS  ·  COMMIT INTENSITY  ·  12 MONTHS</text>')

    # Header separator
    e(f'<line x1="{LM}" y1="44" x2="{LM+GRID_W}" y2="44" stroke="#21262d" stroke-width="1"/>')

    # ── Day labels ────────────────────────────────────────────────────────────
    DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, d in enumerate(DAYS):
        y = TM + i*STEP + CELL//2
        e(f'<text x="{LM-4}" y="{y}" font-family="\'Courier New\',Courier,monospace" '
          f'font-size="9" fill="#6e7681" text-anchor="end" dominant-baseline="central">{d}</text>')

    # ── Contribution cells ────────────────────────────────────────────────────
    month_labels = {}  # month_abbr → x
    prev_month   = None
    weekly_totals = []

    for w_idx, week in enumerate(weeks):
        x = LM + w_idx * STEP
        w_total = 0

        # Month label: mark first week of each new month
        if week['contributionDays']:
            d0 = datetime.strptime(week['contributionDays'][0]['date'], '%Y-%m-%d')
            m  = d0.strftime('%b')
            if m != prev_month:
                month_labels[m] = x
                prev_month = m

        for day in week['contributionDays']:
            # GitHub weekday: 0=Sun → remap to row 0=Mon
            row   = (day['weekday'] + 6) % 7
            y     = TM + row * STEP
            count = day['contributionCount']
            w_total += count
            col   = color_for(count)
            e(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{col}"/>')

        weekly_totals.append(w_total)

    # ── X-axis line ───────────────────────────────────────────────────────────
    GRID_BOT = TM + GRID_H
    e(f'<line x1="{LM}" y1="{GRID_BOT+2}" x2="{LM+GRID_W}" y2="{GRID_BOT+2}" '
      f'stroke="#21262d" stroke-width="1"/>')

    # Month labels
    Y_MONTH = GRID_BOT + 14
    for m, mx in month_labels.items():
        e(f'<text x="{mx}" y="{Y_MONTH}" font-family="\'Courier New\',Courier,monospace" '
          f'font-size="9" fill="#6e7681">{m}</text>')

    # ── Weekly power-spectrum sparkline ───────────────────────────────────────
    # Drawn as small bars below month labels — mimics spectrogram power profile
    max_t = max(weekly_totals) if weekly_totals else 1
    SPARK_BOT = GRID_BOT + 34   # bottom of sparkline
    SPARK_H   = 10              # max bar height

    for i, t in enumerate(weekly_totals):
        if t == 0:
            continue
        bh = max(1, int((t / max_t) * SPARK_H))
        sx = LM + i * STEP
        sy = SPARK_BOT - bh
        e(f'<rect x="{sx}" y="{sy}" width="{CELL}" height="{bh}" rx="1" '
          f'fill="#a78bfa" fill-opacity="0.35"/>')

    # Sparkline base line
    e(f'<line x1="{LM}" y1="{SPARK_BOT}" x2="{LM+GRID_W}" y2="{SPARK_BOT}" '
      f'stroke="#21262d" stroke-width="1" stroke-dasharray="2 4"/>')

    # ── Colorbar ──────────────────────────────────────────────────────────────
    CB_ITEMS = [
        ('28+', '#e0f9ff'),
        ('28',  '#38bdf8'),
        ('18',  '#a78bfa'),
        ('11',  '#8b5cf6'),
        ('6',   '#6d28d9'),
        ('3',   '#3b0764'),
        ('1',   '#1e1040'),
        ('0',   '#0d1117'),
    ]
    CB_CELL = GRID_H // len(CB_ITEMS)
    e(f'<text x="{CB_X+10}" y="{TM-9}" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="8" fill="#4d5562" text-anchor="middle">n</text>')

    for i, (label, col) in enumerate(CB_ITEMS):
        cy = TM + i * CB_CELL
        e(f'<rect x="{CB_X}" y="{cy}" width="12" height="{CB_CELL-1}" fill="{col}" rx="1"/>')
        e(f'<text x="{CB_X+16}" y="{cy + CB_CELL//2}" '
          f'font-family="\'Courier New\',Courier,monospace" font-size="7" '
          f'fill="#6e7681" dominant-baseline="central">{label}</text>')

    # ── Footer ────────────────────────────────────────────────────────────────
    FY = SVG_H - 8
    e(f'<text x="{LM}" y="{FY}" font-family="\'Courier New\',Courier,monospace" font-size="9" fill="#6e7681">'
      f'<tspan fill="#a78bfa" font-weight="bold">{total}</tspan>'
      f' contributions in the last year</text>')
    e(f'<text x="{SVG_W-8}" y="{FY}" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="9" fill="#4d5562" text-anchor="end">generated {today}</text>')

    e('</svg>')
    return '\n'.join(L)


if __name__ == '__main__':
    print(f'Fetching contributions for {USERNAME}...', flush=True)
    try:
        cal = fetch()
    except Exception as ex:
        print(f'ERROR: {ex}', file=sys.stderr)
        sys.exit(1)

    print(f'Total: {cal["totalContributions"]}  Weeks: {len(cal["weeks"])}')
    svg = render(cal)

    out = 'contrib.svg'
    with open(out, 'w') as f:
        f.write(svg)
    print(f'Saved {out}  ({len(svg)} bytes)')
