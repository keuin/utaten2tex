import re
import sys
import abc
import dataclasses
import enum
import typing

import bs4
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
        if isinstance(ele, bs4.NavigableString):
            # text
            t = ele.text.strip()
            if not t:
                continue
            yield TextToken(t)
        elif isinstance(ele, bs4.Tag):
            if ele.name == 'span':
                yield from process_notated(ele)
            elif ele.name == 'br':
                # newline
                yield newline
            else:
                print(f'** Ignore HTML element <unknown block {ele.name}>', file=sys.stderr)
        else:
            print(f'** Ignore {type(ele)}', file=sys.stderr)


class LatexGenerator:
    centering: bool
    cjk: CJKProvider
    artist: typing.Optional[str]
    title: typing.Optional[str]
    cjk_font_main: typing.Optional[str]
    cjk_font_sans: typing.Optional[str]
    cjk_font_mono: typing.Optional[str]

    def __init__(self):
        self.artist, self.title = None, None
        self.cjk_font_main, self.cjk_font_sans, self.cjk_font_mono = None, None, None

    def generate_lyric(self, lyric_tokens: typing.Iterator[Token]) -> str:
        injectors = []
        injectors.append(LatexDocInjectionInfo([], [r'\usepackage{pxrubrica}'], []))
        injectors.append(LatexDocInjectionInfo([], [r'\usepackage{setspace}', r'\doublespacing'], []))
        injectors.append(LatexDocInjectionInfo([], [
            r'\usepackage{geometry}',
            r'\geometry{a4paper,left=20mm,right=20mm,top=10mm,bottom=20mm}',
        ], []))
        injectors.append(LatexDocInjectionInfo([], [x for x in [
            r'\setCJKmainfont{%s}' % self.cjk_font_main if self.cjk_font_main else None,
            r'\setCJKsansfont{%s}' % self.cjk_font_sans if self.cjk_font_sans else None,
            r'\setCJKmonofont{%s}' % self.cjk_font_mono if self.cjk_font_mono else None,
        ] if x], []))
        injectors.append(LatexDocInjectionInfo([], [
            r'\author{%s}' % (self.artist or ''),
            r'\title{%s}' % (self.title or ''),
            r'\date{}',
        ], []))
        injectors.append(LatexDocInjectionInfo([], [r'\begin{document}'], [r'\end{document}']))
        injectors.append(LatexDocInjectionInfo([], [r'\maketitle'], []))
        if self.centering:
            injectors.append(LatexDocInjectionInfo([], [r'\begin{center}'], [r'\end{center}']))
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


@dataclasses.dataclass
class LyricInfo:
    utaten_id: str
    tex_source: str
    artist: typing.Optional[str]
    title: typing.Optional[str]


def html_extract_lyric_info(html) -> LyricInfo:
    p = BeautifulSoup(html, "html5lib")
    meta_url_info = p.select_one('meta[property="og:url"]')
    if not meta_url_info:
        raise RuntimeError('Cannot parse meta URL info from given HTML')
    utaten_id = re.findall(r'/lyric/([a-z0-9]+)', str(meta_url_info['content']))[0]
    lyric = p.select_one('.hiragana')
    if not lyric:
        raise RuntimeError('Cannot find lyric element `.hiragana`')
    tokens = tokenize(lyric)
    tokens = optimize_typography(tokens)
    gen = LatexGenerator()
    gen.centering = True
    gen.cjk = CJKProvider.xeCJK
    title = None
    artist = None
    for s in p.select('script'):
        if not s.string or 'cf_page_artist' not in s.string:
            continue
        entries = re.findall(r'cf_(.+) = "(.+)"', s.string)
        for k, v in entries:
            if k == 'page_artist':
                artist = v
            elif k == 'page_song':
                title = v
    gen.artist, gen.title = artist, title
    # FIXME hardcoded CJK font
    gen.cjk_font_main = 'Noto Serif CJK JP'
    return LyricInfo(
        utaten_id=utaten_id,
        tex_source=gen.generate_lyric(tokens),
        artist=artist,
        title=title,
    )


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
    print(html_extract_lyric_info(html).tex_source)


if __name__ == '__main__':
    main()
