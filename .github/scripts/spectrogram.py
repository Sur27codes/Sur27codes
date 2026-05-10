#!/usr/bin/env python3
"""
Renders GitHub contribution data as a radial frequency burst —
every day of the year is a bar radiating outward from center,
colored by weekday (Mon=blue … Sun=yellow). The full year forms
a glowing mandala with a live radar sweep. "Year in Orbit."
"""
import os, sys, math, random, requests
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

    SVG_W   = 860
    SVG_H   = 310
    CX      = 430
    CY      = 148

    INNER_R = 55     # inner radius (bar root)
    MAX_BAR = 72     # max bar length at peak-commit day
    MIN_BAR = 3      # minimum bar for any non-zero day
    STUB    = 0.7    # ghost stub length for zero-commit days

    COLORS = ['#60a5fa','#34d399','#a78bfa','#fb923c','#f472b6','#22d3ee','#facc15']
    LABELS = ['MON','TUE','WED','THU','FRI','SAT','SUN']

    # ── Flatten all days chronologically ────────────────────────────────
    all_days   = []
    month_idx  = {}
    prev_month = None
    for wk in weeks:
        for d in sorted(wk['contributionDays'], key=lambda x: x['date']):
            i = len(all_days)
            all_days.append(d)
            m = datetime.strptime(d['date'], '%Y-%m-%d').strftime('%b')
            if m != prev_month:
                month_idx[m] = i
                prev_month = m

    N         = len(all_days)
    max_count = max(d['contributionCount'] for d in all_days) or 1

    def bar_len(n):
        if n == 0: return STUB
        return MIN_BAR + ((n / max_count) ** 0.55) * (MAX_BAR - MIN_BAR)

    def polar(deg, r):
        a = deg * math.pi / 180
        return CX + r * math.cos(a), CY + r * math.sin(a)

    L = []
    def e(s): L.append(s)

    # ── SVG open + defs ─────────────────────────────────────────────────
    e(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">')
    e('<defs>')
    # Soft glow
    e('  <filter id="g1" x="-150%" y="-150%" width="400%" height="400%">')
    e('    <feGaussianBlur stdDeviation="2.5" result="b"/>')
    e('    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>')
    e('  </filter>')
    # Strong glow for peak days
    e('  <filter id="g2" x="-200%" y="-200%" width="500%" height="500%">')
    e('    <feGaussianBlur stdDeviation="5.5" result="b"/>')
    e('    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>')
    e('  </filter>')
    # Core aura glow
    e('  <filter id="gc" x="-150%" y="-150%" width="400%" height="400%">')
    e('    <feGaussianBlur stdDeviation="10" result="b"/>')
    e('    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>')
    e('  </filter>')
    # Background radial gradient
    e('  <radialGradient id="bg" cx="50%" cy="48%" r="55%">')
    e('    <stop offset="0%"  stop-color="#07091f"/>')
    e('    <stop offset="100%" stop-color="#020408"/>')
    e('  </radialGradient>')
    # Center core gradient
    e(f'  <radialGradient id="cr" cx="50%" cy="50%" r="50%">')
    e(f'    <stop offset="0%"   stop-color="#c4b5fd"/>')
    e(f'    <stop offset="55%"  stop-color="#7c3aed"/>')
    e(f'    <stop offset="100%" stop-color="#7c3aed" stop-opacity="0"/>')
    e(f'  </radialGradient>')
    e('</defs>')

    # ── Background ──────────────────────────────────────────────────────
    e(f'<rect width="{SVG_W}" height="{SVG_H}" fill="url(#bg)"/>')

    # Stars — only outside the chart area
    random.seed(77)
    for _ in range(110):
        sx, sy = random.randint(5, SVG_W-5), random.randint(5, SVG_H-5)
        if math.hypot(sx-CX, sy-CY) < INNER_R + MAX_BAR + 22:
            continue
        sr = round(random.uniform(0.3, 1.1), 1)
        so = round(random.uniform(0.2, 0.8), 1)
        bd = round(random.uniform(2.0, 5.5), 1)
        bb = round(random.uniform(0.0, 2.5), 1)
        e(f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="#fff" fill-opacity="{so}">'
          f'<animate attributeName="fill-opacity" values="{so};{max(0.05,so-0.4):.2f};{so}" '
          f'dur="{bd}s" begin="{bb}s" repeatCount="indefinite"/>'
          f'</circle>')

    # Border
    e(f'<rect x="1" y="1" width="{SVG_W-2}" height="{SVG_H-2}" rx="9" fill="none" stroke="#a78bfa" stroke-width="1">')
    e(f'  <animate attributeName="stroke-opacity" values="0.12;0.38;0.12" dur="4s" repeatCount="indefinite"/>')
    e(f'</rect>')

    # ── Reference rings (dashed concentric) ─────────────────────────────
    for frac, op in [(0.33, 0.5), (0.66, 0.4), (1.0, 0.6)]:
        r = INNER_R + frac * MAX_BAR
        e(f'<circle cx="{CX}" cy="{CY}" r="{r:.1f}" fill="none" '
          f'stroke="#1a2540" stroke-width="0.5" stroke-opacity="{op}" stroke-dasharray="2 5"/>')

    # Slow counter-rotating outer ring (depth effect)
    e(f'<circle cx="{CX}" cy="{CY}" r="{INNER_R + MAX_BAR + 6:.1f}" fill="none" '
      f'stroke="#a78bfa" stroke-width="0.6" stroke-opacity="0.12" stroke-dasharray="3 14">')
    e(f'  <animateTransform attributeName="transform" type="rotate" '
      f'from="0 {CX} {CY}" to="-360 {CX} {CY}" dur="40s" repeatCount="indefinite"/>')
    e(f'</circle>')

    # ── Radar sweep ─────────────────────────────────────────────────────
    sweep_R = INNER_R + MAX_BAR + 3
    spread  = 18
    ix1,iy1 = polar(0, INNER_R)
    ox1,oy1 = polar(0, sweep_R)
    ox2,oy2 = polar(spread, sweep_R)
    ix2,iy2 = polar(spread, INNER_R)
    sweep_d = (f"M{ix1:.1f},{iy1:.1f} L{ox1:.1f},{oy1:.1f} "
               f"A{sweep_R},{sweep_R} 0 0,1 {ox2:.1f},{oy2:.1f} "
               f"L{ix2:.1f},{iy2:.1f} "
               f"A{INNER_R},{INNER_R} 0 0,0 {ix1:.1f},{iy1:.1f}Z")
    e(f'<path d="{sweep_d}" fill="#22d3ee" fill-opacity="0.09">')
    e(f'  <animateTransform attributeName="transform" type="rotate" '
      f'from="0 {CX} {CY}" to="360 {CX} {CY}" dur="10s" repeatCount="indefinite"/>')
    e(f'</path>')
    # Leading edge beam
    e(f'<line x1="{CX+INNER_R:.1f}" y1="{CY}" x2="{CX+sweep_R:.1f}" y2="{CY}" '
      f'stroke="#22d3ee" stroke-width="1.2" stroke-opacity="0.55">')
    e(f'  <animateTransform attributeName="transform" type="rotate" '
      f'from="0 {CX} {CY}" to="360 {CX} {CY}" dur="10s" repeatCount="indefinite"/>')
    e(f'</line>')

    # ── Radial bars (one per day) ─────────────────────────────────────────
    for i, d in enumerate(all_days):
        n      = d['contributionCount']
        wd_m   = (d['weekday'] + 6) % 7   # GitHub weekday 0=Sun → 0=Mon
        color  = COLORS[wd_m]
        ang    = (i / N) * 360 - 90       # -90° = start at top, clockwise

        bl     = bar_len(n)
        x1,y1  = polar(ang, INNER_R)
        x2,y2  = polar(ang, INNER_R + bl)

        if n == 0:
            e(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
              f'stroke="{color}" stroke-width="0.8" stroke-opacity="0.055"/>')
        else:
            frac = n / max_count
            op   = 0.45 + 0.55 * frac
            sw   = 1.0  + 2.2  * frac
            filt = 'g2' if frac > 0.62 else 'g1'
            e(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
              f'stroke="{color}" stroke-width="{sw:.1f}" stroke-opacity="{op:.2f}" '
              f'filter="url(#{filt})"/>')

    # ── Month labels ─────────────────────────────────────────────────────
    label_r = INNER_R + MAX_BAR + 14
    for m, idx in month_idx.items():
        ang    = (idx / N) * 360 - 90
        lx, ly = polar(ang, label_r)
        ta = 'end' if lx < CX - 8 else ('start' if lx > CX + 8 else 'middle')
        e(f'<text x="{lx:.1f}" y="{ly+2.5:.1f}" font-family="\'Courier New\',Courier,monospace" '
          f'font-size="7.5" fill="#3d5070" text-anchor="{ta}">{m}</text>')

    # ── Center core ───────────────────────────────────────────────────────
    e(f'<circle cx="{CX}" cy="{CY}" r="{INNER_R}" fill="url(#cr)" fill-opacity="0.18" filter="url(#gc)">')
    e(f'  <animate attributeName="fill-opacity" values="0.13;0.30;0.13" dur="3.5s" repeatCount="indefinite"/>')
    e(f'</circle>')
    e(f'<circle cx="{CX}" cy="{CY}" r="{INNER_R-3}" fill="#030610"/>')
    e(f'<circle cx="{CX}" cy="{CY}" r="{INNER_R-3}" fill="none" stroke="#7c3aed" stroke-width="0.9" stroke-opacity="0.7"/>')
    # Total commits display
    e(f'<text x="{CX}" y="{CY-9}" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="21" font-weight="bold" fill="#e9d5ff" text-anchor="middle" filter="url(#g1)">{total}</text>')
    e(f'<text x="{CX}" y="{CY+5}" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="7" fill="#a78bfa" text-anchor="middle" letter-spacing="2">COMMITS</text>')
    e(f'<text x="{CX}" y="{CY+16}" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="5.5" fill="#3d4d6a" text-anchor="middle">{today}</text>')

    # ── Weekday legend (left/right of chart) ─────────────────────────────
    for i, (name, color) in enumerate(zip(LABELS, COLORS)):
        lx = 22        if i < 4 else SVG_W - 62
        ly = CY - 28 + (i if i < 4 else i - 4) * 18
        e(f'<circle cx="{lx+4}" cy="{ly-3}" r="3" fill="{color}" fill-opacity="0.9" filter="url(#g1)"/>')
        e(f'<text x="{lx+13}" y="{ly}" font-family="\'Courier New\',Courier,monospace" '
          f'font-size="8" fill="{color}" fill-opacity="0.65">{name}</text>')

    # ── Header ───────────────────────────────────────────────────────────
    e(f'<text x="{SVG_W//2}" y="15" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="8.5" fill="#283555" text-anchor="middle" letter-spacing="3">'
      f'YEAR IN ORBIT  ·  CONTRIBUTIONS AS RADIAL FREQUENCY</text>')

    # ── Footer ───────────────────────────────────────────────────────────
    fy = SVG_H - 9
    e(f'<text x="18" y="{fy}" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="8.5" fill="#283555">'
      f'<tspan fill="#a78bfa" font-weight="bold">{total}</tspan>'
      f' contributions  ·  {N} days tracked</text>')
    e(f'<text x="{SVG_W-18}" y="{fy}" font-family="\'Courier New\',Courier,monospace" '
      f'font-size="8.5" fill="#283555" text-anchor="end">COMMIT PULSE RADIAL</text>')

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
