"""Generate gold-lit profile cards from public GitHub data, using only the stdlib."""

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USER = 'OliverAven01'
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
INK, MUTED, BLUE = '#1D263B', '#637089', '#0071E3'


def gold_theme(source):
    """Apply warm typography, dark surfaces and ambient golden light to a card."""
    namespace = 'http://www.w3.org/2000/svg'
    ET.register_namespace('', namespace)
    tag = lambda name: f'{{{namespace}}}{name}'
    root = ET.fromstring(source)
    def polish_lighting():
        halo = root.find(f'.//{tag("radialGradient")}[@id="halo"]')
        if halo is not None:
            stops = list(halo)
            stops[0].set('stop-opacity', '0.8')
            stops[-1].set('stop-opacity', '0')
        definitions = root.find(tag('defs'))
        if definitions is not None and definitions.find(f'{tag("filter")}[@id="gold-bloom"]') is None:
            bloom = ET.SubElement(definitions, tag('filter'), {'id': 'gold-bloom', 'x': '-50%', 'y': '-50%', 'width': '200%', 'height': '200%', 'color-interpolation-filters': 'sRGB'})
            ET.SubElement(bloom, tag('feGaussianBlur'), {'stdDeviation': '3', 'result': 'bloom'})
            merge = ET.SubElement(bloom, tag('feMerge'))
            ET.SubElement(merge, tag('feMergeNode'), {'in': 'bloom'})
            ET.SubElement(merge, tag('feMergeNode'), {'in': 'SourceGraphic'})
        for element in root.iter(tag('path')):
            if element.get('d', '').startswith('M-39 -13'):
                element.set('filter', 'url(#gold-bloom)')
        return ET.tostring(root, encoding='unicode') + '\n'
    if root.find(f'.//{tag("radialGradient")}[@id="gold-ambient"]') is not None:
        return polish_lighting()
    palette = {
        '#FFFFFF': '#1B1711', '#1D1D1F': '#F6EEDC', '#1D263B': '#F6EEDC',
        '#6E6E73': '#BCAF96', '#637089': '#BCAF96', '#0071E3': '#F4CF83',
        '#0063BC': '#F1C873', '#007D72': '#EAC279', '#007E68': '#EAC279',
        '#008577': '#EAC279', '#00A58C': '#A6782F', '#075EBF': '#FFE1A0',
        '#087EF0': '#F9D98A', '#3188EF': '#D6A349', '#577BF4': '#DDA844',
        '#596FDB': '#DCAE57', '#68DCC5': '#EED59A', '#70B4FF': '#986B28',
        '#74BAFF': '#F6CF79', '#7551BC': '#E6BC6B', '#7556CF': '#F9D17C',
        '#763DD0': '#75420F', '#8863D5': '#D6A34A', '#9657CE': '#E7BC65',
        '#97A6BF': '#BDA47B', '#A85C26': '#D8AB60', '#AC58C5': '#BA8333',
        '#B1C2ED': '#D6B876', '#B6D9FF': '#5E421E', '#BADEFF': '#FFF0BE',
        '#BFA8FF': '#E8BC65', '#CC6B22': '#FFE1A0', '#D7E9FF': '#65451B',
        '#D7EEE8': '#4D3C23', '#DBE9FA': '#4D3C23', '#E1E4ED': '#544127',
        '#E29A32': '#FFEDBC', '#E2EBF7': '#282116', '#E4ECFF': '#392B19',
        '#E5E1F0': '#33291B', '#E5F6F1': '#11110E', '#E77493': '#785128',
        '#E9EDF5': '#342B1E', '#EAF2FF': '#12100D', '#ECFAF7': '#11110E',
        '#F0F7FF': '#12100D', '#F1ECFF': '#14100D', '#F2B47D': '#DCAE57',
        '#F3F8FF': '#12100D', '#F4F1FF': '#14100D', '#F8FAFE': '#15120E',
        '#FFF1E7': '#15100B',
    }
    for element in root.iter():
        for key, value in list(element.attrib.items()):
            element.set(key, re.sub(r'#[0-9a-fA-F]{6}', lambda m: palette.get(m[0].upper(), m[0]), value))
    width, height = map(float, (root.get('width'), root.get('height')))
    definitions = root.find(tag('defs'))
    if definitions is None:
        definitions = ET.Element(tag('defs'))
        root.insert(1, definitions)
    glow = ET.SubElement(definitions, tag('radialGradient'), {'id': 'gold-ambient', 'cx': '0.74', 'cy': '0', 'r': '0.9'})
    for offset, opacity in [('0', '0.26'), ('0.42', '0.10'), ('1', '0')]:
        ET.SubElement(glow, tag('stop'), {'offset': offset, 'stop-color': '#EFB84F', 'stop-opacity': opacity})
    edge = ET.SubElement(definitions, tag('linearGradient'), {'id': 'gold-rim', 'x1': '0', 'y1': '0', 'x2': '1', 'y2': '0'})
    for offset, opacity in [('0', '0'), ('0.5', '0.8'), ('1', '0')]:
        ET.SubElement(edge, tag('stop'), {'offset': offset, 'stop-color': '#FFE6AC', 'stop-opacity': opacity})
    for parent in root.iter():
        for index, element in enumerate(list(parent)):
            if (element.tag == tag('rect') and element.get('fill') not in (None, 'none')
                    and float(element.get('width', 0)) == width and float(element.get('height', 0)) == height):
                element.set('fill', '#0E0D0B')
                radius = element.get('rx', '24')
                parent.insert(index + 1, ET.Element(tag('rect'), {'width': str(width), 'height': str(height), 'rx': radius, 'fill': 'url(#gold-ambient)'}))
                parent.insert(index + 2, ET.Element(tag('rect'), {'x': '1', 'y': '1', 'width': str(width - 2), 'height': str(height - 2), 'rx': radius, 'fill': 'none', 'stroke': '#C89C4B', 'stroke-opacity': '0.22'}))
                parent.insert(index + 3, ET.Element(tag('path'), {'d': f'M{float(radius)} 1H{width - float(radius)}', 'stroke': 'url(#gold-rim)', 'stroke-width': '1.5'}))
                return polish_lighting()
    raise ValueError('Card has no full-size background')


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.counts = {}, {}
        self.tooltip, self.buffer = None, []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-date' in attrs and 'data-level' in attrs:
            self.cells[attrs['id']] = (date.fromisoformat(attrs['data-date']), int(attrs['data-level']))
        if tag == 'tool-tip':
            self.tooltip, self.buffer = attrs.get('for'), []

    def handle_data(self, data):
        if self.tooltip:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tooltip:
            label = ' '.join(''.join(self.buffer).split())
            match = re.match(r'([\d,]+) contributions?\b', label)
            if match:
                self.counts[self.tooltip] = int(match[1].replace(',', ''))
            elif label.startswith('No contributions'):
                self.counts[self.tooltip] = 0
            self.tooltip = None

    def days(self):
        if not self.cells or any(key not in self.counts for key in self.cells):
            raise ValueError('GitHub calendar markup changed or contribution counts are incomplete')
        days = sorted((day, self.counts[key], level) for key, (day, level) in self.cells.items())
        if len({day for day, _, _ in days}) != len(days):
            raise ValueError('Duplicate calendar dates')
        if any(b[0] - a[0] != timedelta(days=1) for a, b in zip(days, days[1:])):
            raise ValueError('Calendar dates are not contiguous')
        return days


def streaks(days):
    """An unfinished current day does not break yesterday's active streak."""
    best = run = 0
    for _, count, _ in days:
        run = run + 1 if count else 0
        best = max(best, run)
    end = len(days) - 1
    if end >= 0 and days[end][1] == 0:
        end -= 1
    current = 0
    while end >= 0 and days[end][1]:
        current += 1
        end -= 1
    return current, best


def fetch(url):
    headers = {'User-Agent': f'{USER}-profile-stats', 'Accept-Language': 'en-US'}
    if url.startswith('https://api.github.com/'):
        headers['Accept'] = 'application/vnd.github+json'
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'Bearer {token}'
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=headers), timeout=30) as response:
                return response.read().decode('utf-8')
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def load_data(snapshot_dir=None):
    if snapshot_dir:
        folder = Path(snapshot_dir)
        profile = json.loads((folder / 'github-user.json').read_text(encoding='utf-8'))
        repos = json.loads((folder / 'github-repos.json').read_text(encoding='utf-8'))
        calendar = (folder / 'github-calendar.html').read_text(encoding='utf-8')
    else:
        profile = json.loads(fetch(f'https://api.github.com/users/{USER}'))
        repos = []
        page = 1
        while True:
            batch = json.loads(fetch(f'https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}'))
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        calendar = fetch(f'https://github.com/users/{USER}/contributions')
    parser = CalendarParser()
    parser.feed(calendar)
    days = parser.days()
    if not 300 <= len(days) <= 367:
        raise ValueError('Expected a complete annual contribution calendar')
    return profile, [r for r in repos if not r['private'] and r['owner']['login'].lower() == USER.lower()], days


def text(x, y, value, size=16, color=INK, weight=400, attrs=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" {attrs}>{escape(str(value))}</text>'


def rect(x, y, w, h, fill, radius=14, attrs=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" {attrs}/>'


def svg(width, height, title, body):
    return gold_theme(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" role="img" aria-labelledby="title">
<title id="title">{escape(title)}</title>
<g font-family="{FONT}">{body}</g>
</svg>
''')


def generate(profile, repos, days):
    owned = [r for r in repos if not r['fork']]
    total = sum(count for _, count, _ in days)
    active = sum(count > 0 for _, count, _ in days)
    current, best = streaks(days)
    updated = datetime.now(timezone.utc).strftime('%d/%m/%Y')
    overview = rect(0, 0, 1280, 250, '#F0F7FF', 24)
    overview += text(32, 39, 'GITHUB / EN CIFRAS', 12, BLUE, 600, 'letter-spacing="1.8"')
    overview += text(1248, 39, f'Actualizado {updated} · UTC', 12, MUTED, attrs='text-anchor="end"')
    metrics = [(len(repos), 'Repositorios públicos', '#0071E3'),
               (sum(r['stargazers_count'] for r in owned), 'Estrellas en repos propios', '#9657CE'),
               (profile['followers'], 'Seguidores', '#008577'),
               (total, 'Contribuciones · 12 meses', '#CC6B22')]
    for i, (value, label, color) in enumerate(metrics):
        x = 32 + i * 306
        overview += rect(x, 66, 298, 150, '#FFFFFF', 18, 'stroke="#DBE9FA"')
        overview += text(x + 22, 134, f'{value:,}', 52, color, 650, 'letter-spacing="-2"')
        overview += text(x + 22, 177, label, 15, MUTED, 500)

    langs = Counter(r['language'] for r in owned if r.get('language'))
    entries = langs.most_common(5)
    others = sum(langs.values()) - sum(count for _, count in entries)
    if others:
        entries.append(('Otros', others))
    colors = ['#087EF0', '#8863D5', '#00A58C', '#E29A32', '#E77493', '#97A6BF']
    language = rect(0, 0, 600, 340, '#F4F1FF', 22)
    language += text(28, 45, 'Lenguajes en mis repositorios', 23, weight=600, attrs='letter-spacing="-0.6"')
    language += text(28, 72, 'Por lenguaje principal · repositorios propios', 12, MUTED)
    language += '<circle cx="145" cy="205" r="74" stroke="#E5E1F0" stroke-width="23"/>'
    circumference, offset = 2 * 3.141592653589793 * 74, 0
    known = sum(langs.values())
    for i, (name, count) in enumerate(entries):
        length = circumference * count / known
        language += f'<circle cx="145" cy="205" r="74" stroke="{colors[i]}" stroke-width="23" stroke-dasharray="{length:.3f} {circumference-length:.3f}" stroke-dashoffset="{-offset:.3f}" transform="rotate(-90 145 205)"/>'
        offset += length
        y = 122 + i * 32
        language += rect(278, y - 10, 9, 9, colors[i], 3)
        language += text(299, y, name, 15, weight=500)
        language += text(558, y, str(count), 15, MUTED, attrs='text-anchor="end"')
    language += text(145, 209, known, 43, weight=650, attrs='text-anchor="middle" letter-spacing="-1.5"')
    language += text(145, 235, 'repos con lenguaje', 11, MUTED, attrs='text-anchor="middle"')

    streak = rect(0, 0, 600, 340, '#ECFAF7', 22)
    streak += text(28, 45, 'Constancia, día a día.', 25, weight=600, attrs='letter-spacing="-0.6"')
    streak += text(28, 72, 'Rachas calculadas sobre el calendario visible', 12, MUTED)
    streak += rect(28, 100, 544, 125, '#FFFFFF', 16, 'stroke="#D7EEE8"')
    streak += text(300, 162, current, 55, '#008577', 650, 'text-anchor="middle" letter-spacing="-2"')
    streak += text(300, 196, 'día de racha actual' if current == 1 else 'días de racha actual', 15, MUTED, attrs='text-anchor="middle"')
    for x, value, label in [(160, best, 'Mejor racha · 12 meses'), (440, active, 'Días activos · 12 meses')]:
        streak += text(x, 275, value, 31, '#007D72', 600, 'text-anchor="middle"')
        streak += text(x, 305, label, 12, MUTED, attrs='text-anchor="middle"')

    calendar = rect(0, 0, 1280, 300, '#F3F8FF', 24)
    calendar += text(32, 43, 'Un año de contribuciones.', 27, weight=600, attrs='letter-spacing="-0.7"')
    calendar += text(1248, 42, f'{days[0][0]:%d/%m/%Y} — {days[-1][0]:%d/%m/%Y}', 13, MUTED, attrs='text-anchor="end"')
    start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
    shades = ['#E2EBF7', '#B6D9FF', '#70B4FF', '#3188EF', '#075EBF']
    for day, count, level in days:
        week = (day - start).days // 7
        weekday = (day.weekday() + 1) % 7
        x, y = 78 + week * 21, 99 + weekday * 22
        if day.day == 1:
            calendar += text(x, 83, months[day.month - 1], 12, MUTED)
        calendar += rect(x, y, 16, 16, shades[level], 4)
    for row, label in [(1, 'lun'), (3, 'mié'), (5, 'vie')]:
        calendar += text(32, 111 + row * 22, label, 11, MUTED)
    calendar += text(32, 278, f'{total:,} contribuciones visibles · {active} días con actividad', 13, MUTED)
    calendar += text(1060, 278, 'Menos', 11, MUTED)
    for i, color in enumerate(shades):
        calendar += rect(1104 + i * 20, 266, 13, 13, color, 3)
    calendar += text(1248, 278, 'Más', 11, MUTED, attrs='text-anchor="end"')

    return {
        'stats-overview.svg': svg(1280, 250, f'{len(repos)} repositorios públicos, {metrics[1][0]} estrellas en repos propios, {profile["followers"]} seguidores y {total} contribuciones visibles en los últimos 12 meses. Actualizado {updated}.', overview),
        'stats-languages.svg': svg(600, 340, 'Repositorios propios por lenguaje principal: ' + ', '.join(f'{n}: {c}' for n, c in entries), language),
        'stats-streak.svg': svg(600, 340, f'Racha actual: {current} días. Mejor racha en el calendario: {best} días. Días activos en los últimos 12 meses: {active}.', streak),
        'stats-calendar.svg': svg(1280, 300, f'Calendario visible de {USER}: {total} contribuciones desde {days[0][0]} hasta {days[-1][0]}.', calendar),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot-dir', help='Read public API snapshots for offline rendering')
    args = parser.parse_args()
    profile, repos, days = load_data(args.snapshot_dir)
    cards = generate(profile, repos, days)
    for name, content in cards.items():
        (ROOT / 'assets' / name).write_text(content, encoding='utf-8')
    print(f'Generated {len(cards)} cards from {len(repos)} public repositories and {len(days)} calendar days.')


if __name__ == '__main__':
    main()
