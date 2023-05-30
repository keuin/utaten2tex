import re
import sys
import abc
import dataclasses
import enum
import typing

from bs4 import BeautifulSoup
from bs4.element import Tag


class ParseError(Exception):
    pass


class Token(abc.ABC):
    def to_latex(self) -> str:
        raise NotImplementedError


class TextToken(Token):

    def __init__(self, text: str):
        self.text = text

    def to_latex(self) -> str:
        return self.text


class NotatedToken(Token):

    def __init__(self, text: str, notation: str):
        self.text = text
        self.notation = notation

    def to_latex(self) -> str:
        if len(self.text) == 1:
            return r'\ruby{%s}{%s}' % (self.text, self.notation)
        else:
            # TODO tokenize hiragana to make the annotation more accurate and beautiful
            return r'\ruby[g]{%s}{%s}' % (self.text, self.notation)


class NewLineToken(Token):

    def __init__(self):
        pass

    def to_latex(self) -> str:
        return '\n\n'


class SectionBreaker(Token):

    def __init__(self):
        pass

    def to_latex(self) -> str:
        return r'\section*{}'


def optimize_typography(tokens: typing.Iterator[Token]) -> typing.Iterator[Token]:
    prev = next(tokens)
    for t in tokens:
        if all([isinstance(x, NewLineToken) for x in (prev, t)]):
            yield NewLineToken()
            yield SectionBreaker()
        else:
            yield prev
            prev = t
    if prev:
        yield prev


@dataclasses.dataclass
class LatexDocInjectionInfo:
    packages: list[str]
    header: list[str]
    footer: list[str]


class CJKProvider(enum.Enum):
    CJK = LatexDocInjectionInfo([r'\usepackage{CJKutf8}'], [r'\begin{CJK}{UTF8}{min}'], [r'\end{CJK}'])
    xeCJK = LatexDocInjectionInfo([r'\usepackage{xeCJK}'], [], [])


def process_notated(ele: Tag):
    ch = list(ele.children)
    if (ln := len(ch)) != 2:
        # Expecting a (kanji block, hiragana block)
        raise ParseError(f'Invalid notated node length: {ln} != 2')
    yield NotatedToken(*(x.text.strip() for x in ch))


def tokenize(lyric: Tag) -> typing.Iterator[Token]:
    newline = NewLineToken()
    for i, ele in enumerate(lyric):
        if ele.name == 'span':
            yield from process_notated(ele)
        elif ele.name is None:
            # text
            t = ele.text.strip()
            if not t:
                continue
            yield TextToken(t)
        elif ele.name == 'br':
            # newline
            yield newline
        else:
            print(f'<unknown block {ele.name}>')


class LatexGenerator:
    centering: bool
    cjk: CJKProvider

    def __init__(self):
        pass

    def generate_lyric(self, lyric_tokens: typing.Iterator[Token], title) -> str:
        injectors = []
        injectors.append(LatexDocInjectionInfo([], [r'\usepackage{pxrubrica}'], []))
        injectors.append(LatexDocInjectionInfo([], [r'\usepackage{setspace}', r'\doublespacing'], []))
        injectors.append(LatexDocInjectionInfo([], [
            r'\usepackage{geometry}',
            r'\geometry{a4paper,left=20mm,right=20mm,top=10mm,bottom=20mm}',
        ], []))
        injectors.append(LatexDocInjectionInfo([], [
            r'\setCJKmainfont{Noto Serif CJK TC}',
            r'\setCJKsansfont{Noto Sans CJK TC}',
            r'\setCJKmonofont{Noto Sans Mono CJK TC}',
        ], []))
        injectors.append(LatexDocInjectionInfo([], [r'\begin{document}'], [r'\end{document}']))
        if self.centering:
            injectors.append(LatexDocInjectionInfo([], [r'\begin{center}'], [r'\end{center}']))
        if title:
            injectors.append(LatexDocInjectionInfo([], [r'\section*{%s}' % title], []))
        injectors.append(self.cjk.value)

        def _inject(injectors, getter) -> str:
            doc = ''
            for i in injectors:
                for s in getter(i):
                    doc += s
                    doc += '\n'
            return doc

        doc = r'\documentclass{article}' + '\n'
        doc += _inject(injectors, lambda _i: _i.packages)
        doc += _inject(injectors, lambda _i: _i.header)

        for t in lyric_tokens:
            doc += t.to_latex()

        doc += _inject(injectors[::-1], lambda _i: _i.footer)

        return doc


def main():
    if len(sys.argv) > 2:
        print(f'Usage: <{sys.argv[0]}> [path_to_html_file]')
        exit(0)
    if len(sys.argv) == 2:
        file_name = sys.argv[1]
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                html = f.read()
        except FileNotFoundError:
            print(f'File does not exist: {file_name}')
            exit(1)
    else:
        # read html from STDIN
        html = sys.stdin.read()
    p = BeautifulSoup(html, "html5lib")
    lyric = p.select_one('.hiragana')
    tokens = tokenize(lyric)
    tokens = optimize_typography(tokens)
    gen = LatexGenerator()
    gen.centering = True
    gen.cjk = CJKProvider.xeCJK
    title = ''
    artist = ''
    for s in p.select('script'):
        if not s.string or 'cf_page_artist' not in s.string:
            continue
        entries = re.findall(r'cf_(.+) = "(.+)"', s.string)
        for k, v in entries:
            if k == 'page_artist':
                artist = v
            elif k == 'page_song':
                title = v
    print(gen.generate_lyric(tokens, f'{title} - {artist}' if title and artist else None))


if __name__ == '__main__':
    main()
