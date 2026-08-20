import argparse
import json
import re
import shutil
import time
import unicodedata
from html import escape
from pathlib import Path

BASE_URL = 'https://thehistory.pro'
ROOT_PATH = Path(__file__).resolve().parent
SLIDES_PATH = ROOT_PATH / 'data' / 'slides.json'


def strip_tags(value):
    return re.sub(r'<[^>]+>', ' ', value or '').replace('\xa0', ' ').strip()


def first_sentences(text, limit=220):
    clean = ' '.join(strip_tags(text).split())
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + '...'


def safe_image_src(src, fallback='img/logo1.png'):
    value = str(src or '').strip()
    if not value or value == '--':
        return fallback
    normalized = value.replace('\\', '/').lstrip('/')
    return normalized if normalized else fallback


def img_tag(src, alt='', css=''):
    safe_src = safe_image_src(src)
    safe_alt = escape(str(alt or ''))
    style = f' style="{css}"' if css else ''
    return f'<img src="{BASE_URL}/{safe_src}" alt="{safe_alt}"{style} onerror="this.onerror=null;this.src=\'{BASE_URL}/img/logo1.png\';" />'


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


def render_static_shell(title, description, page_url, hero_image, body_html, page_type='year'):
    redirect_script = r'''
    <script>
        (function () {
            const match = window.location.pathname.match(/^\/(\d+)(?:\/([^/]+))?\/?$/);
            if (!match) return;
            const year = match[1];
            const slug = match[2] ? '/' + match[2] + '/' : '/';
            const target = '/?route=' + encodeURIComponent('/' + year + slug);
            window.location.replace(target);
        })();
    </script>
    '''
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(description)}" />
    <link rel="canonical" href="{page_url}" />
    <link rel="icon" type="image/png" href="{BASE_URL}/img/logo1.png" />
    <link rel="apple-touch-icon" href="{BASE_URL}/img/logo1.png" />
    <meta property="og:title" content="{escape(title)}" />
    <meta property="og:description" content="{escape(description)}" />
    <meta property="og:image" content="{hero_image}" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="{page_url}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{escape(title)}" />
    <meta name="twitter:description" content="{escape(description)}" />
    <meta name="twitter:image" content="{hero_image}" />
    {redirect_script}
    <style>
        :root {{
            --bg: #0d1117;
            --panel: #111827;
            --panel-2: #1f2937;
            --text: #f3f4f6;
            --muted: #d1d5db;
            --accent: #66d9ef;
            --accent-2: #7dd3fc;
            --border: rgba(255,255,255,0.08);
            --shadow: rgba(0,0,0,0.35);
        }}
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; background: var(--bg); color: var(--text); }}
        body {{ line-height: 1.6; }}
        a {{ color: var(--accent); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .page-shell {{ max-width: 1120px; margin: 0 auto; padding: 30px 20px 40px; }}
        .site-topbar {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 0 20px; border-bottom: 1px solid var(--border); margin-bottom: 28px; }}
        .brand {{ font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text); }}
        .top-links {{ display: flex; gap: 14px; flex-wrap: wrap; }}
        .hero-image {{ width: 100%; max-width: 900px; border-radius: 18px; display: block; margin: 28px 0; border: 1px solid var(--border); box-shadow: 0 18px 45px var(--shadow); }}
        .content-card {{ background: rgba(17,24,39,0.8); border: 1px solid var(--border); border-radius: 18px; padding: 24px; box-shadow: 0 18px 45px var(--shadow); }}
        h1, h2, h3 {{ margin: 0 0 12px; color: var(--text); }}
        p {{ margin: 0 0 14px; color: var(--muted); }}
        ul {{ padding-left: 18px; margin: 14px 0 0; color: var(--muted); }}
        li {{ margin: 8px 0; }}
        .meta-tag {{ display: inline-block; font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: var(--accent-2); margin-bottom: 14px; }}
        .muted {{ color: var(--muted); }}
        @media (max-width: 640px) {{
            .page-shell {{ padding: 18px 14px 30px; }}
            .site-topbar {{ flex-direction: column; align-items: flex-start; }}
            .content-card {{ padding: 18px; }}
        }}
    </style>
</head>
<body>
    <div class="page-shell">
        <div class="site-topbar">
            <div class="brand">theХистори</div>
            <div class="top-links">
                <a href="{BASE_URL}/">На главную</a>
                <a href="{BASE_URL}/">Главная лента</a>
            </div>
        </div>
        {body_html}
    </div>
</body>
</html>'''


def build_year_page(slide, year_data, all_years):
    year_id = str(slide.get('id', '')).strip()
    year_label = slide.get('label', year_id)
    tabs = year_data.get('tabs', {})
    events = []
    year_url = f'{BASE_URL}/{year_id}/'

    for tab_name in ('world', 'russia'):
        tab = tabs.get(tab_name, {})
        for index, article in enumerate(tab.get('articles', []), 1):
            title = article.get('button') or article.get('title') or f'Событие {index}'
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
    hero_image = f'{BASE_URL}/' + safe_image_src(slide.get('image', 'img/logo1.png')).replace('\\', '/')

    event_cards_html = ''.join(
        f'<li style="margin:10px 0; list-style:none;"><a href="{event["url"]}" style="color:#66d9ef; text-decoration:none;">{escape(event["title"])}</a></li>'
        for event in events
    )

    year_links_html = ''.join(
        f'<li style="margin:6px 0; list-style:none;"><a href="{BASE_URL}/{entry["id"]}/" style="color:#66d9ef; text-decoration:none;">{escape(entry["label"])}</a></li>'
        for entry in all_years if str(entry.get('id', '')) != str(year_id)
    )

    body_html = f'''
        <div class="content-card">
            <span class="meta-tag">{escape(year_label)} • theХистори</span>
            <h1>{escape(year_label)} — theХистори</h1>
            <p class="muted">{escape(primary_description)}</p>
            <img class="hero-image" src="{hero_image}" alt="{escape(year_label)}" onerror="this.onerror=null;this.src='{BASE_URL}/img/logo1.png';" />
        </div>
        <div class="content-card" style="margin-top:20px;">
            <h2>События года</h2>
            <ul>
                {event_cards_html}
            </ul>
        </div>
        <div class="content-card" style="margin-top:20px;">
            <h2>Другие годы</h2>
            <ul>
                {year_links_html}
            </ul>
        </div>
    '''
    return render_static_shell(
        f'{primary_title} | {year_label} | theХистори',
        primary_description,
        year_url,
        hero_image,
        body_html,
        page_type='year'
    )


def build_event_page(slide, year_data, tab_name, article, article_index, all_years):
    year_id = str(slide.get('id', '')).strip()
    title = article.get('button') or article.get('title') or f'Событие {article_index}'
    slug = slugify(title)
    description = first_sentences(' '.join(article.get('body', []))) or f'{title} — события {year_id} года на theХистори.'
    image = article.get('image', {})
    image_src = image.get('src') if isinstance(image, dict) else None
    image_url = f'{BASE_URL}/' + safe_image_src(image_src or slide.get('image', 'img/logo1.png')).replace('\\', '/')
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

    body_html = f'''
        <div class="content-card">
            <a href="{BASE_URL}/{year_id}/">← К году {year_id}</a>
            <p class="meta-tag">{escape(section_label)}</p>
            <h1>{escape(title)}</h1>
            <img class="hero-image" src="{image_url}" alt="{escape(title)}" onerror="this.onerror=null;this.src='{BASE_URL}/img/logo1.png';" />
            <div class="muted">{body_html}</div>
        </div>
        <div class="content-card" style="margin-top:20px;">
            <h2>Другие события этого года</h2>
            <ul>
                {related_events_html}
            </ul>
        </div>
        <div class="content-card" style="margin-top:20px;">
            <h2>Другие годы</h2>
            <ul>
                {year_links_html}
            </ul>
        </div>
    '''
    return render_static_shell(title, description, page_url, image_url, body_html, page_type='article')


def generate_pages():
    with SLIDES_PATH.open('r', encoding='utf-8') as f:
        slides = json.load(f)

    for slide in slides:
        year_id = str(slide.get('id', '')).strip()
        if not year_id:
            continue

        content_value = str(slide.get('content', '') or '').strip()
        content_path = ROOT_PATH / content_value if content_value else None
        if content_path and content_path.exists() and content_path.is_file():
            with content_path.open('r', encoding='utf-8') as f:
                year_data = json.load(f)
        else:
            year_data = {'tabs': {'world': {'articles': []}, 'russia': {'articles': []}}}

        current_slugs = set()
        for tab_name in ('world', 'russia'):
            tab = year_data.get('tabs', {}).get(tab_name, {})
            for article_index, article in enumerate(tab.get('articles', []), 1):
                title = article.get('button') or article.get('title') or f'Событие {article_index}'
                current_slugs.add(slugify(title))

        short_year_dir = ROOT_PATH / year_id
        short_year_dir.mkdir(exist_ok=True)

        for existing in short_year_dir.iterdir():
            if existing.is_dir() and existing.name not in current_slugs:
                shutil.rmtree(existing)

        year_page = build_year_page(slide, year_data, slides)
        (short_year_dir / 'index.html').write_text(year_page, encoding='utf-8')

        for tab_name in ('world', 'russia'):
            tab = year_data.get('tabs', {}).get(tab_name, {})
            for article_index, article in enumerate(tab.get('articles', []), 1):
                title = article.get('button') or article.get('title') or f'Событие {article_index}'
                slug = slugify(title)

                event_page = build_event_page(slide, year_data, tab_name, article, article_index, slides)

                short_event_dir = short_year_dir / slug
                short_event_dir.mkdir(exist_ok=True)
                (short_event_dir / 'index.html').write_text(event_page, encoding='utf-8')

    print(f'Generated year and event pages in {ROOT_PATH}')


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
