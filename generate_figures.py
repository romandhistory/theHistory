import difflib
import json
import re
import shutil
import sys
import unicodedata
from html import escape
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_PATH))
from generate_year_pages import render_static_shell, slugify, safe_image_src, BASE_URL  # noqa: E402

SRC_PATH = ROOT_PATH / 'TG' / 'kompanovka.xlsx'
YEARS_DIR = ROOT_PATH / 'data' / 'years'
SLIDES_PATH = ROOT_PATH / 'data' / 'slides.json'
OUT_PATH = ROOT_PATH / 'data' / 'figures.json'
CAST_DIR = ROOT_PATH / 'cast'

FUZZY_THRESHOLD = 0.72


def normalize(text):
    text = unicodedata.normalize('NFKC', text)
    text = text.replace('ё', 'е').replace('Ё', 'Е')
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def load_year(cache, year):
    if year not in cache:
        path = YEARS_DIR / f'{year}.json'
        if path.exists():
            with path.open('r', encoding='utf-8') as f:
                cache[year] = json.load(f)
        else:
            cache[year] = None
    return cache[year]


def find_article(year_data, title):
    norm_title = normalize(title)
    candidates = []
    for tab_name in ('world', 'russia'):
        articles = year_data.get('tabs', {}).get(tab_name, {}).get('articles', [])
        for idx, article in enumerate(articles, 1):
            for field in ('button', 'title'):
                value = article.get(field)
                if not value:
                    continue
                norm_value = normalize(value)
                if norm_value == norm_title:
                    return (tab_name, idx, 1.0)
                candidates.append((tab_name, idx, norm_value))

    best = None
    for tab_name, idx, norm_value in candidates:
        ratio = difflib.SequenceMatcher(None, norm_title, norm_value).ratio()
        if best is None or ratio > best[2]:
            best = (tab_name, idx, ratio)

    if best and best[2] >= FUZZY_THRESHOLD:
        return best
    return None


def parse_source(path):
    figures = []
    current = None
    awaiting_intro = False

    with path.open('r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.rstrip('\n').rstrip('\r')
            if not line.strip():
                continue

            if line.lstrip().startswith('•'):
                name = line.lstrip().lstrip('•').strip()
                current = {'figure': name, 'intro': None, 'events': []}
                figures.append(current)
                awaiting_intro = True
                continue

            if current is None:
                continue

            is_indented = line[:1].isspace()
            stripped = line.strip()

            if awaiting_intro and not is_indented and '/' not in stripped:
                current['intro'] = stripped
                awaiting_intro = False
                continue
            awaiting_intro = False

            if '/' not in stripped:
                continue
            title, _, year = stripped.rpartition('/')
            title = title.strip()
            year = year.strip()
            if not year.isdigit():
                continue
            current['events'].append({'title': title, 'year': year})

    return figures


def resolve_figures():
    figures = parse_source(SRC_PATH)
    year_cache = {}
    resolved_figures = []
    unmatched = []
    fuzzy_used = []

    for figure in figures:
        resolved_events = []
        for event in figure['events']:
            year_data = load_year(year_cache, event['year'])
            match = find_article(year_data, event['title']) if year_data else None
            if not match:
                unmatched.append((figure['figure'], event['title'], event['year']))
                continue
            tab_name, idx, ratio = match
            if ratio < 1.0:
                fuzzy_used.append((figure['figure'], event['title'], ratio))
            resolved_events.append({
                'title': event['title'],
                'year': event['year'],
                'tab': tab_name,
                'article': idx
            })
        if resolved_events:
            resolved_figures.append({
                'figure': figure['figure'],
                'intro': figure['intro'],
                'events': resolved_events
            })

    return resolved_figures, unmatched, fuzzy_used, year_cache


def build_figure_page(figure, year_cache, slide_by_id):
    slug = slugify(figure['figure'])
    page_url = f'{BASE_URL}/cast/{slug}/'

    resolved_events = []
    hero_image = None
    for event in figure['events']:
        year_data = year_cache.get(event['year'])
        if not year_data:
            continue
        articles = year_data.get('tabs', {}).get(event['tab'], {}).get('articles', [])
        if event['article'] < 1 or event['article'] > len(articles):
            continue
        article = articles[event['article'] - 1]
        real_title = article.get('button') or article.get('title') or event['title']
        event_slug = slugify(real_title)
        event_url = f'{BASE_URL}/{event["year"]}/{event_slug}/'
        resolved_events.append({'year': event['year'], 'title': real_title, 'url': event_url})

        if hero_image is None:
            image = article.get('image', {})
            image_src = image.get('src') if isinstance(image, dict) else None
            slide = slide_by_id.get(event['year'])
            fallback = slide.get('image', 'img/logo1.png') if slide else 'img/logo1.png'
            hero_image = f'{BASE_URL}/' + safe_image_src(image_src or fallback).replace('\\', '/')

    if not resolved_events:
        return None

    if hero_image is None:
        hero_image = f'{BASE_URL}/img/logo1.png'

    intro = figure['intro'] or f'{figure["figure"]} — сюжетная линия из {len(resolved_events)} связанных событий на theХистори.'

    events_html = ''.join(
        f'<li style="margin:8px 0; list-style:none;">'
        f'<a href="{ev["url"]}" style="color:#66d9ef; text-decoration:none;">'
        f'<strong>{escape(ev["year"])}</strong> — {escape(ev["title"])}</a></li>'
        for ev in resolved_events
    )

    body_html = f'''
        <div class="content-card">
            <p class="meta-tag">Сюжетная линия • theХистори</p>
            <h1>{escape(figure["figure"])}</h1>
            <img class="hero-image" src="{hero_image}" alt="{escape(figure["figure"])}" onerror="this.onerror=null;this.src='{BASE_URL}/img/logo1.png';" />
            <p class="muted">{escape(intro)}</p>
        </div>
        <div class="content-card" style="margin-top:20px;">
            <h2>События</h2>
            <ul>
                {events_html}
            </ul>
        </div>
    '''

    page = render_static_shell(
        f'{figure["figure"]} | theХистори',
        intro,
        page_url,
        hero_image,
        body_html,
        page_type='figure'
    )
    return slug, page


def build():
    if not SRC_PATH.exists():
        print(f'{SRC_PATH} not found, skipping figures generation')
        return

    resolved_figures, unmatched, fuzzy_used, year_cache = resolve_figures()

    OUT_PATH.write_text(
        json.dumps(resolved_figures, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )

    slides = json.loads(SLIDES_PATH.read_text(encoding='utf-8'))
    slide_by_id = {str(s.get('id')): s for s in slides}

    CAST_DIR.mkdir(exist_ok=True)
    current_slugs = set()
    for figure in resolved_figures:
        built = build_figure_page(figure, year_cache, slide_by_id)
        if not built:
            continue
        slug, page = built
        current_slugs.add(slug)
        figure_dir = CAST_DIR / slug
        figure_dir.mkdir(exist_ok=True)
        (figure_dir / 'index.html').write_text(page, encoding='utf-8')

    for existing in CAST_DIR.iterdir():
        if existing.is_dir() and existing.name not in current_slugs:
            shutil.rmtree(existing)

    total_events = sum(len(f['events']) for f in resolved_figures)
    print(f'Wrote {len(resolved_figures)} figures / {total_events} events to {OUT_PATH}')
    print(f'Generated {len(current_slugs)} pages in {CAST_DIR}')
    if fuzzy_used:
        print(f'{len(fuzzy_used)} events matched fuzzily (wording drift) - verify these:')
        for figure_name, title, ratio in fuzzy_used:
            print(f'  [{ratio:.2f}] {figure_name}: {title}')
    if unmatched:
        print(f'{len(unmatched)} events could NOT be matched to an article:')
        for figure_name, title, year in unmatched:
            print(f'  {figure_name}: {title}/{year}')


if __name__ == '__main__':
    build()
