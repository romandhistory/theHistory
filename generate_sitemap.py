import json
import re
import unicodedata
from pathlib import Path

BASE_URL = 'https://thehistory.pro'
ROOT_PATH = Path(__file__).resolve().parent
SLIDES_PATH = ROOT_PATH / 'data' / 'slides.json'
FIGURES_PATH = ROOT_PATH / 'data' / 'figures.json'
SITEMAP_PATH = ROOT_PATH / 'sitemap.xml'
ROBOTS_PATH = ROOT_PATH / 'robots.txt'


def slugify(value):
    text = str(value or '').strip()
    if not text:
        return 'event'

    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z',
        'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'ъ': '', 'ь': ''
    }

    normalized = unicodedata.normalize('NFKD', text.lower())
    translit = ''.join(mapping.get(ch, ch) for ch in normalized)
    translit = translit.encode('ascii', 'ignore').decode('ascii')
    translit = re.sub(r'[^a-z0-9\s-]', '', translit)
    translit = re.sub(r'\s+', '-', translit)
    translit = re.sub(r'-+', '-', translit).strip('-')
    return translit or 'event'


def load_slides(path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_year(path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def build_urls(slides):
    urls = [f'{BASE_URL}/']
    for slide in slides:
        if slide.get('locked'):
            continue
        year_id = str(slide.get('id', '')).strip()
        if not year_id:
            continue

        urls.append(f'{BASE_URL}/{year_id}/')

        content_value = str(slide.get('content', '') or '').strip()
        if not content_value:
            continue
        content_path = ROOT_PATH / content_value
        if not content_path.is_file():
            continue

        year_data = load_year(content_path)
        for tab_name in ('world', 'russia'):
            for index, article in enumerate(year_data.get('tabs', {}).get(tab_name, {}).get('articles', []), 1):
                title = article.get('button') or article.get('title') or f'Событие {index}'
                urls.append(f'{BASE_URL}/{year_id}/{slugify(title)}/')

    return urls


def build_cast_urls():
    if not FIGURES_PATH.exists():
        return []

    with FIGURES_PATH.open('r', encoding='utf-8') as f:
        figures = json.load(f)

    return [
        f'{BASE_URL}/cast/{slugify(figure.get("figure", ""))}/'
        for figure in figures
        if figure.get('events')
    ]


def write_sitemap(path, urls):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for url in urls:
        lines.extend([
            '  <url>',
            f'    <loc>{url}</loc>',
            '  </url>'
        ])
    lines.append('</urlset>')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_robots(path):
    path.write_text(
        'User-agent: *\n'
        'Allow: /\n'
        f'Sitemap: {BASE_URL}/sitemap.xml\n',
        encoding='utf-8'
    )


if __name__ == '__main__':
    slides = load_slides(SLIDES_PATH)
    urls = build_urls(slides) + build_cast_urls()
    write_sitemap(SITEMAP_PATH, urls)
    write_robots(ROBOTS_PATH)
    print(f'Wrote {len(urls)} URLs to {SITEMAP_PATH}')
    print(f'Wrote robots.txt to {ROBOTS_PATH}')
