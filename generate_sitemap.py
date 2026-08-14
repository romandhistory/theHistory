import json
import re
import unicodedata
from pathlib import Path

BASE_URL = 'https://thehistory.pro'
ROOT_PATH = Path(__file__).resolve().parent
SLIDES_PATH = ROOT_PATH / 'data' / 'slides.json'
SITEMAP_PATH = ROOT_PATH / 'sitemap.xml'
ROBOTS_PATH = ROOT_PATH / 'robots.txt'


def slugify(value):
    text = str(value or '').strip()
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text.lower())
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text or 'event'


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

        urls.append(f'{BASE_URL}/years/{year_id}/')

        content_path = ROOT_PATH / str(slide.get('content', ''))
        if not content_path.exists():
            continue

        year_data = load_year(content_path)
        for tab_name in ('world', 'russia'):
            for article in year_data.get('tabs', {}).get(tab_name, {}).get('articles', []):
                title = article.get('title') or article.get('button') or 'event'
                urls.append(f'{BASE_URL}/years/{year_id}/{slugify(title)}/')

    return urls


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
    urls = build_urls(slides)
    write_sitemap(SITEMAP_PATH, urls)
    write_robots(ROBOTS_PATH)
    print(f'Wrote {len(urls)} URLs to {SITEMAP_PATH}')
    print(f'Wrote robots.txt to {ROBOTS_PATH}')
