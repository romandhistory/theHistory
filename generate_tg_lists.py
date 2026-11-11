"""Собирает TG/Мир.xlsx и TG/Россия.xlsx (текстовые списки названий блоков)
из поля `button` статей в data/years/*.json.

Формат:
    862
        Название блока
        ...
    <пустая строка>

Год берётся из имени файла (NNN.json). Включаются все годы по порядку.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
YEARS_DIR = ROOT / 'data' / 'years'
OUTPUTS = {
    'world': ROOT / 'TG' / 'Мир.xlsx',
    'russia': ROOT / 'TG' / 'Россия.xlsx',
}


def year_files():
    files = []
    for path in YEARS_DIR.glob('*.json'):
        if path.stem.isdigit():
            files.append((int(path.stem), path))
    return sorted(files)


def build(tab):
    lines = []
    for year, path in year_files():
        data = json.loads(path.read_text(encoding='utf-8'))
        articles = ((data.get('tabs') or {}).get(tab) or {}).get('articles') or []
        buttons = [str(a.get('button') or '').strip() for a in articles]
        buttons = [b for b in buttons if b]
        if not buttons:
            continue
        lines.append(str(year))
        lines.extend('    ' + b for b in buttons)
        lines.append('')
    return '\n'.join(lines)


def main():
    for tab, out in OUTPUTS.items():
        text = build(tab)
        old = out.read_text(encoding='utf-8') if out.exists() else None
        if text != old:
            out.write_text(text, encoding='utf-8')
            print(f'updated {out.relative_to(ROOT)}')
        else:
            print(f'unchanged {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
