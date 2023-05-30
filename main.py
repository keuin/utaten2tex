import typing

from bs4 import BeautifulSoup
from bs4.element import Tag


class ParseError(Exception):
    pass


def main():
    with open('yumetourou.html', 'r', encoding='utf-8') as f:
        html = f.read()
    p = BeautifulSoup(html, "html5lib")
    lyric = p.select_one('.hiragana')
    for t in process_lyric(lyric):
        print(t, end='')


def process_notated(ele: Tag):
    ch = list(ele.children)
    if len(ch) != 2:
        # 必需是一个汉字块、一个假名块
        raise ParseError('Invalid notated node')
    yield r'\ruby{%s}{%s}' % tuple(x.text.strip() for x in ch)


def process_lyric(lyric: Tag):
    for i, ele in enumerate(lyric):
        if ele.name == 'span':
            yield from process_notated(ele)
        elif ele.name is None:
            # text
            t = ele.text.strip()
            if not t:
                continue
            yield t
        elif ele.name == 'br':
            # newline
            yield '\n\n'
        else:
            print(f'<unknown block {ele.name}>')


if __name__ == '__main__':
    main()
