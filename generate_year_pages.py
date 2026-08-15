import argparse
import json
import re
import time
import unicodedata
from html import escape
from pathlib import Path

BASE_URL = 'https://thehistory.pro'
ROOT_PATH = Path(__file__).resolve().parent
SLIDES_PATH = ROOT_PATH / 'data' / 'slides.json'
YEAR_OUTPUT_DIR = ROOT_PATH / 'years'


def strip_tags(value):
    return re.sub(r'<[^>]+>', ' ', value or '').replace('\xa0', ' ').strip()


def first_sentences(text, limit=220):
    clean = ' '.join(strip_tags(text).split())
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + '...'


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


def build_year_page(slide, year_data, all_years):
    year_id = str(slide.get('id', '')).strip()
    year_label = slide.get('label', year_id)
    tabs = year_data.get('tabs', {})
    events = []
    year_url = f'{BASE_URL}/{year_id}/'
    legacy_year_url = f'{BASE_URL}/years/{year_id}/'

    for tab_name in ('world', 'russia'):
        tab = tabs.get(tab_name, {})
        for index, article in enumerate(tab.get('articles', []), 1):
            title = article.get('title') or article.get('button') or f'Событие {index}'
            slug = slugify(title)
            events.append({
                'title': title,
                'slug': slug,
                'tab': tab_name,
                'url': f'{BASE_URL}/{year_id}/{slug}/'
            })

    if not events:
        default_title = f'theХистори | {year_label}'
        description = f'Ключевые события и исторические материалы {year_label} года на theХистори.'
        hero_image = f'{BASE_URL}/' + str(slide.get('image', 'img/logo1.png')).replace('\\', '/')
        return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escape(default_title)}</title>
    <meta name="description" content="{escape(description)}" />
    <link rel="canonical" href="{year_url}" />
    <link rel="icon" type="image/png" href="{BASE_URL}/img/logo1.png" />
    <meta property="og:title" content="{escape(default_title)}" />
    <meta property="og:description" content="{escape(description)}" />
    <meta property="og:image" content="{hero_image}" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="{year_url}" />
</head>
<body style="font-family:Arial,sans-serif;background:#0d1117;color:#fff;padding:40px;">
    <h1>{escape(default_title)}</h1>
    <p>{escape(description)}</p>
    <p><a href="{BASE_URL}/" style="color:#66d9ef;">На главную</a></p>
</body>
</html>'''

    primary = events[0]
    primary_title = primary['title']
    all_body_parts = []
    for tab_name in ('world', 'russia'):
        for article in tabs.get(tab_name, {}).get('articles', []):
            all_body_parts.extend(article.get('body', []))
    primary_description = first_sentences(' '.join(all_body_parts)) or f'Ключевые события {year_label} года на theХистори.'
    hero_image = f'{BASE_URL}/' + str(slide.get('image', 'img/logo1.png')).replace('\\', '/')

    event_cards_html = ''.join(
        f'<li style="margin:10px 0; list-style:none;"><a href="{event["url"]}" style="color:#66d9ef; text-decoration:none;">{escape(event["title"])}</a></li>'
        for event in events
    )

    year_links_html = ''.join(
        f'<li style="margin:6px 0; list-style:none;"><a href="{BASE_URL}/{entry["id"]}/" style="color:#66d9ef; text-decoration:none;">{escape(entry["label"])}</a></li>'
        for entry in all_years if str(entry.get('id', '')) != str(year_id)
    )

    page_html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escape(primary_title)} | {year_label} | theХистори</title>
    <meta name="description" content="{escape(primary_description)}" />
    <link rel="canonical" href="{year_url}" />
    <link rel="icon" type="image/png" href="{BASE_URL}/img/logo1.png" />
    <link rel="apple-touch-icon" href="{BASE_URL}/img/logo1.png" />
    <meta property="og:title" content="{escape(primary_title)} | {year_label} | theХистори" />
    <meta property="og:description" content="{escape(primary_description)}" />
    <meta property="og:image" content="{hero_image}" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="{year_url}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{escape(primary_title)} | {year_label} | theХистори" />
    <meta name="twitter:description" content="{escape(primary_description)}" />
    <meta name="twitter:image" content="{hero_image}" />
    <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "{escape(year_label)} | theХистори",
            "description": "{escape(primary_description)}",
            "url": "{year_url}",
            "image": "{hero_image}",
            "publisher": {{
                "@type": "Organization",
                "name": "theХистори",
                "url": "{BASE_URL}/",
                "logo": "{BASE_URL}/img/logo1.png"
            }}
        }}
    </script>
</head>
<body style="font-family:Arial,sans-serif;background:#0d1117;color:#fff;padding:40px;">
    <div style="max-width:1120px;margin:0 auto;">
        <p><a href="{BASE_URL}/" style="color:#66d9ef;">← На главную</a></p>
        <h1 style="margin-bottom:8px;">{escape(year_label)} — theХистори</h1>
        <p style="color:#d1d5db;">{escape(primary_description)}</p>
        <img src="{hero_image}" alt="{escape(year_label)}" style="width:100%;max-width:900px;border-radius:16px;display:block;margin:24px 0;" />
        <h2 style="margin-top:20px;">События года</h2>
        <ul style="padding-left:0;">
            {event_cards_html}
        </ul>
        <h2 style="margin-top:24px;">Другие годы</h2>
        <ul style="padding-left:0;">
            {year_links_html}
        </ul>
    </div>
</body>
</html>'''
    return page_html


def build_event_page(slide, year_data, tab_name, article, article_index, all_years):
    year_id = str(slide.get('id', '')).strip()
    title = article.get('title') or article.get('button') or f'Событие {article_index}'
    slug = slugify(title)
    description = first_sentences(' '.join(article.get('body', []))) or f'{title} — события {year_id} года на theХистори.'
    image = article.get('image', {})
    image_src = image.get('src') if isinstance(image, dict) else None
    image_url = f'{BASE_URL}/' + str(image_src or slide.get('image', 'img/logo1.png')).replace('\\', '/')
    page_url = f'{BASE_URL}/{year_id}/{slug}/'

    body_html = ''.join(article.get('body', []))
    section_label = {'world': 'Мировые события', 'russia': 'Россия'}.get(tab_name, 'Событие')

    related_events = []
    for tab_name_iter in ('world', 'russia'):
        tab = year_data.get('tabs', {}).get(tab_name_iter, {})
        for idx, event in enumerate(tab.get('articles', []), 1):
            event_title = event.get('title') or event.get('button') or f'Событие {idx}'
            related_events.append({
                'title': event_title,
                'url': f'{BASE_URL}/{year_id}/{slugify(event_title)}/'
            })

    related_events_html = ''.join(
        f'<li style="margin:8px 0; list-style:none;"><a href="{entry["url"]}" style="color:#66d9ef; text-decoration:none;">{escape(entry["title"])}</a></li>'
        for entry in related_events
        if entry['url'] != page_url
    )

    year_links_html = ''.join(
        f'<li style="margin:6px 0; list-style:none;"><a href="{BASE_URL}/{entry["id"]}/" style="color:#66d9ef; text-decoration:none;">{escape(entry["label"])}</a></li>'
        for entry in all_years if str(entry.get('id', '')) != str(year_id)
    )

    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escape(title)} | {year_id} | theХистори</title>
    <meta name="description" content="{escape(description)}" />
    <link rel="canonical" href="{page_url}" />
    <link rel="icon" type="image/png" href="{BASE_URL}/img/logo1.png" />
    <link rel="apple-touch-icon" href="{BASE_URL}/img/logo1.png" />
    <meta property="og:title" content="{escape(title)} | theХистори" />
    <meta property="og:description" content="{escape(description)}" />
    <meta property="og:image" content="{image_url}" />
    <meta property="og:type" content="article" />
    <meta property="og:url" content="{page_url}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{escape(title)} | theХистори" />
    <meta name="twitter:description" content="{escape(description)}" />
    <meta name="twitter:image" content="{image_url}" />
    <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "{escape(title)}",
            "name": "{escape(title)}",
            "description": "{escape(description)}",
            "url": "{page_url}",
            "image": "{image_url}",
            "author": {{
                "@type": "Organization",
                "name": "theХистори"
            }},
            "publisher": {{
                "@type": "Organization",
                "name": "theХистори",
                "logo": "{BASE_URL}/img/logo1.png"
            }},
            "mainEntityOfPage": {{
                "@type": "WebPage",
                "@id": "{page_url}"
            }},
            "about": {{
                "@type": "Event",
                "name": "{escape(title)}",
                "startDate": "{year_id}"
            }}
        }}
    </script>
</head>
<body style="font-family:Arial,sans-serif;background:#0d1117;color:#fff;padding:40px;">
    <div style="max-width:980px;margin:0 auto;">
        <p><a href="{BASE_URL}/{year_id}/" style="color:#66d9ef;">← К году {year_id}</a></p>
        <p style="text-transform:uppercase;letter-spacing:.12em;color:#66d9ef;font-size:12px;">{escape(section_label)}</p>
        <h1>{escape(title)}</h1>
        <img src="{image_url}" alt="{escape(title)}" style="width:100%;max-width:760px;border-radius:16px;display:block;margin:20px 0;" />
        <div style="color:#d1d5db;line-height:1.8;">{body_html}</div>
        <h2 style="margin-top:24px;">Другие события этого года</h2>
        <ul style="padding-left:0;">
            {related_events_html}
        </ul>
        <h2 style="margin-top:24px;">Другие годы</h2>
        <ul style="padding-left:0;">
            {year_links_html}
        </ul>
        <p style="margin-top:30px;"><a href="{BASE_URL}/" style="color:#66d9ef;">На главную</a></p>
    </div>
</body>
</html>'''


def generate_pages():
    with SLIDES_PATH.open('r', encoding='utf-8') as f:
        slides = json.load(f)

    YEAR_OUTPUT_DIR.mkdir(exist_ok=True)

    for slide in slides:
        year_id = str(slide.get('id', '')).strip()
        if not year_id or slide.get('locked'):
            continue
        content_path = ROOT_PATH / str(slide.get('content', ''))
        if not content_path.exists():
            continue

        with content_path.open('r', encoding='utf-8') as f:
            year_data = json.load(f)

        legacy_year_dir = YEAR_OUTPUT_DIR / year_id
        legacy_year_dir.mkdir(exist_ok=True)
        year_page = build_year_page(slide, year_data, slides)
        (legacy_year_dir / 'index.html').write_text(year_page, encoding='utf-8')

        short_year_dir = ROOT_PATH / year_id
        short_year_dir.mkdir(exist_ok=True)
        (short_year_dir / 'index.html').write_text(year_page, encoding='utf-8')

        for tab_name in ('world', 'russia'):
            tab = year_data.get('tabs', {}).get(tab_name, {})
            for article_index, article in enumerate(tab.get('articles', []), 1):
                title = article.get('title') or article.get('button') or f'Событие {article_index}'
                slug = slugify(title)

                event_page = build_event_page(slide, year_data, tab_name, article, article_index, slides)

                legacy_event_dir = legacy_year_dir / slug
                legacy_event_dir.mkdir(exist_ok=True)
                (legacy_event_dir / 'index.html').write_text(event_page, encoding='utf-8')

                short_event_dir = short_year_dir / slug
                short_event_dir.mkdir(exist_ok=True)
                (short_event_dir / 'index.html').write_text(event_page, encoding='utf-8')

    print(f'Generated year and event pages in {YEAR_OUTPUT_DIR}')


def main():
    parser = argparse.ArgumentParser(description='Generate static year and event SEO pages.')
    parser.add_argument('--watch', action='store_true', help='Regenerate when source data files change.')
    parser.add_argument('--interval', type=float, default=2.0, help='Polling interval in seconds for --watch mode.')
    args = parser.parse_args()

    if args.watch:
        generation_files = [
            SLIDES_PATH,
            *sorted((ROOT_PATH / 'data' / 'years').glob('*.json')),
        ]
        last_mtime = {str(path): path.stat().st_mtime for path in generation_files if path.exists()}

        print('Watching data files for changes...')
        generate_pages()

        try:
            while True:
                current = {str(path): path.stat().st_mtime for path in generation_files if path.exists()}
                if current != last_mtime:
                    print('Detected data change, regenerating pages...')
                    generate_pages()
                    last_mtime = current
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print('\nStopped watching.')
        return

    generate_pages()


if __name__ == '__main__':
    main()
