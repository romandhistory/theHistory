import json
from pathlib import Path

BASE_URL = 'https://thehistory.pro'
ROOT_PATH = Path(__file__).resolve().parent
SLIDES_PATH = ROOT_PATH / 'data' / 'slides.json'
SITEMAP_PATH = ROOT_PATH / 'sitemap.xml'
ROBOTS_PATH = ROOT_PATH / 'robots.txt'


def load_slides(path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def build_urls(slides):
    urls = [f'{BASE_URL}/']
    for slide in slides:
        if slide.get('content') and not slide.get('locked', False):
            year_id = str(slide.get('id', '')).strip()
            if year_id:
                urls.append(f'{BASE_URL}/#{year_id}')
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
