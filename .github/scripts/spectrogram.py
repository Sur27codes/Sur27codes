#!/usr/bin/env python3
"""
Renders GitHub contribution data as a city skyline at night.
Each week column = one building. Height = weekly commit count.
"""

import os, sys, requests
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


def render(cal):
    weeks  = cal['weeks']
    total  = cal['totalContributions']
    today  = datetime.now().strftime('%Y-%m-%d')
    NW     = len(weeks)

    # ── Layout ──────────────────────────────────────────────────────────────
    SVG_W   = 860
    FLOOR_Y = 175          # y of the ground line
    MAX_H   = 130          # tallest building height (px)
    MIN_H   = 8            # quietest week still gets a sliver
    COL_W   = (SVG_W - 20) / NW   # width per column
    GAP     = max(1, int(COL_W * 0.12))
    B_W     = max(4, int(COL_W - GAP))
    SVG_H   = 240

    # weekly totals
    week_totals = []
    month_marks = {}
    prev_month  = None
    for w_idx, wk in enumerate(weeks):
        s = sum(d['contributionCount'] for d in wk['contributionDays'])
        week_totals.append(s)
        if wk['contributionDays']:
            dt = datetime.strptime(wk['contributionDays'][0]['date'], '%Y-%m-%d')
            m  = dt.strftime('%b')
            if m != prev_month:
                month_marks[m] = w_idx
                prev_month = m

    max_t = max(week_totals) if week_totals else 1

    def building_h(t):
        if t == 0: return MIN_H // 2
        frac = (t / max_t) ** 0.55   # power curve — small weeks still visible
        return int(MIN_H + frac * (MAX_H - MIN_H))

    def building_color(t):
        """Gradient: very dim → purple → lavender → near-white based on height."""
        if t == 0: return '#111827', '#1a2035'
        frac = t / max_t
        if frac < 0.25: return '#1e1040', '#2d1878'
        if frac < 0.50: return '#4c1d95', '#6d28d9'
        if frac < 0.75: return '#7c3aed', '#a78bfa'
        return '#a78bfa', '#e0d7ff'

    L = []
    def e(s): L.append(s)

    # ── SVG open ────────────────────────────────────────────────────────────
    e(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">')
    e(f'<defs>')
    e(f'  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">')
    e(f'    <stop offset="0%"  stop-color="#050810"/>')
    e(f'    <stop offset="70%" stop-color="#0a0d1a"/>')
    e(f'    <stop offset="100%" stop-color="#0f1330"/>')
    e(f'  </linearGradient>')
    # Horizon glow
    e(f'  <radialGradient id="hglow" cx="50%" cy="100%" r="60%">')
    e(f'    <stop offset="0%"  stop-color="#6d28d9" stop-opacity="0.18"/>')
    e(f'    <stop offset="100%" stop-color="#6d28d9" stop-opacity="0"/>')
    e(f'  </radialGradient>')
    # Reflection gradient (buildings reflected below ground)
    e(f'  <linearGradient id="ref" x1="0" y1="0" x2="0" y2="1">')
    e(f'    <stop offset="0%"  stop-color="#000000" stop-opacity="0.5"/>')
    e(f'    <stop offset="100%" stop-color="#000000" stop-opacity="0"/>')
    e(f'  </linearGradient>')
    e(f'  <clipPath id="skycp"><rect x="0" y="0" width="{SVG_W}" height="{FLOOR_Y}"/></clipPath>')
    e(f'  <clipPath id="refcp"><rect x="0" y="{FLOOR_Y}" width="{SVG_W}" height="{SVG_H - FLOOR_Y - 30}"/></clipPath>')
    e(f'</defs>')

    # Sky background
    e(f'<rect width="{SVG_W}" height="{SVG_H}" fill="url(#sky)"/>')

    # Stars (scattered dots)
    import random; random.seed(42)
    for _ in range(60):
        sx = random.randint(10, SVG_W - 10)
        sy = random.randint(8, FLOOR_Y - 20)
        sr = round(random.uniform(0.4, 1.2), 1)
        so = round(random.uniform(0.3, 0.9), 1)
        bd = round(random.uniform(1.5, 4.0), 1)
        bb = round(random.uniform(0, 2.0), 1)
        e(f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="#ffffff" fill-opacity="{so}">'
          f'<animate attributeName="fill-opacity" values="{so};{max(0.1,so-0.4)};{so}" dur="{bd}s" begin="{bb}s" repeatCount="indefinite"/>'
          f'</circle>')

    # Horizon glow
    e(f'<rect width="{SVG_W}" height="{SVG_H}" fill="url(#hglow)"/>')

    # Border
    e(f'<rect x="1" y="1" width="{SVG_W-2}" height="{SVG_H-2}" rx="9" fill="none" stroke="#a78bfa" stroke-width="1">'
      f'<animate attributeName="stroke-opacity" values="0.2;0.45;0.2" dur="3s" repeatCount="indefinite"/>'
      f'</rect>')

    # ── Buildings (above ground) ──────────────────────────────────────────
    # Group: clip to sky area so buildings don't go into footer
    e(f'<g clip-path="url(#skycp)">')
    for w_idx, t in enumerate(week_totals):
        h     = building_h(t)
        x     = 10 + w_idx * COL_W
        bx    = int(x + GAP / 2)
        by    = FLOOR_Y - h
        dark, light = building_color(t)

        # Building body (vertical gradient via two rects)
        e(f'<rect x="{bx}" y="{by}" width="{B_W}" height="{h}" fill="{dark}"/>')
        # Top highlight
        e(f'<rect x="{bx}" y="{by}" width="{B_W}" height="{min(4, h)}" fill="{light}" fill-opacity="0.9"/>')

        # Windows (tiny lit squares) for non-trivial buildings
        if t >= 2 and h > 14:
            win_rows = max(1, (h - 6) // 6)
            win_cols = max(1, (B_W - 2) // 5)
            for wr in range(win_rows):
                for wc in range(win_cols):
                    wx = bx + 2 + wc * 5
                    wy = by + 4 + wr * 6
                    brightness = min(1.0, t / max_t + 0.2)
                    # random seed per window for stable pattern
                    rs = hash((w_idx, wr, wc)) % 100
                    if rs > 35:  # ~65% windows lit
                        wop = round(0.4 + brightness * 0.5, 2)
                        e(f'<rect x="{wx}" y="{wy}" width="2" height="2" fill="{light}" fill-opacity="{wop}"/>')

    e(f'</g>')

    # ── Ground line ──────────────────────────────────────────────────────
    e(f'<line x1="10" y1="{FLOOR_Y}" x2="{SVG_W-10}" y2="{FLOOR_Y}" stroke="#a78bfa" stroke-width="1" stroke-opacity="0.35"/>')

    # ── Reflection (buildings mirrored below ground, fading) ─────────────
    e(f'<g clip-path="url(#refcp)" transform="translate(0,{2*FLOOR_Y}) scale(1,-1)">')
    for w_idx, t in enumerate(week_totals):
        h     = building_h(t)
        x     = 10 + w_idx * COL_W
        bx    = int(x + GAP / 2)
        by    = FLOOR_Y - h
        dark, _ = building_color(t)
        e(f'<rect x="{bx}" y="{by}" width="{B_W}" height="{h}" fill="{dark}" fill-opacity="0.3"/>')
    e(f'</g>')
    # Fade out reflection
    e(f'<rect x="0" y="{FLOOR_Y}" width="{SVG_W}" height="{SVG_H - FLOOR_Y - 30}" fill="url(#ref)"/>')

    # ── Month labels ──────────────────────────────────────────────────────
    for m, widx in month_marks.items():
        mx = int(10 + widx * COL_W)
        e(f'<text x="{mx}" y="{FLOOR_Y + 16}" font-family="\'Courier New\',Courier,monospace" '
          f'font-size="9" fill="#4d5562">{m}</text>')

    # ── Footer ────────────────────────────────────────────────────────────
    fy = SVG_H - 8
    e(f'<text x="10" y="{fy}" font-family="\'Courier New\',Courier,monospace" font-size="9" fill="#4d5562">'
      f'<tspan fill="#a78bfa" font-weight="bold">{total}</tspan> contributions  ·  {today}</text>')
    e(f'<text x="{SVG_W-10}" y="{fy}" font-family="\'Courier New\',Courier,monospace" font-size="9" '
      f'fill="#4d5562" text-anchor="end">CONTRIBUTION SKYLINE</text>')

    e('</svg>')
    return '\n'.join(L)


if __name__ == '__main__':
    print(f'Fetching contributions for {USERNAME}...', flush=True)
    try:
        cal = fetch()
    except Exception as ex:
        print(f'ERROR: {ex}', file=sys.stderr); sys.exit(1)
    print(f'Total: {cal["totalContributions"]}  Weeks: {len(cal["weeks"])}')
    svg = render(cal)
    with open('contrib.svg', 'w') as f:
        f.write(svg)
    print(f'Saved contrib.svg  ({len(svg)} bytes)')
