import os

import aiohttp
from aiofile import async_open

import main


class TexSourceGenerationError(Exception):
    pass


class HtmlCache:

    def __init__(self, cache_path: str):
        self._cache_path = os.path.abspath(cache_path)

    async def get_utaten_tex_source(self, item_id: str) -> str:
        cache_file_path = os.path.join(self._cache_path, f'{item_id}.html')
        if os.path.isfile(cache_file_path):
            async with async_open(cache_file_path, 'r', encoding='utf-8') as f:
                html = await f.read()
        else:
            async with aiohttp.ClientSession() as ses:
                async with ses.get(f'https://utaten.com/lyric/{item_id}/') as r:
                    if not r.ok:
                        raise TexSourceGenerationError('HTTP request failed when reading page source')
                    html = await r.text()
                    try:
                        async with async_open(cache_file_path, 'w', encoding='utf-8') as f:
                            await f.write(html)
                    except IOError as e:
                        print(f'Failed to update cache for song `{item_id}`: {e}')
        return main.html_to_tex(html)
