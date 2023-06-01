import re

import aiohttp
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse

import main
import texgen

app = FastAPI()

utaten_pattern = re.compile(r'[a-z0-9]+')
tex_generator = texgen.TexGenerator('pdf_cache', 'temp', 20)


class TexSourceGenerationError(Exception):
    pass


async def _get_utaten_tex_source(item_id: str) -> str:
    async with aiohttp.ClientSession() as ses:
        async with ses.get(f'https://utaten.com/lyric/{item_id}/') as r:
            if not r.ok:
                raise TexSourceGenerationError('HTTP request failed when reading page source')
            html = await r.text()
            return main.html_to_tex(html)


@app.get("/utaten/{item_id}.pdf")
async def get_utaten_lyric_pdf(item_id: str):
    try:
        print('_get_utaten_tex_source')
        tex = await _get_utaten_tex_source(item_id)
        print('xelatex')
        pdf_path = await tex_generator.xelatex(tex)
        return FileResponse(pdf_path, media_type='application/pdf')
    except texgen.TexGenerationError as e:
        return Response(content=f'Failed to generate tex file: {e}', status_code=502)


@app.get("/utaten/{item_id}.tex")
async def get_utaten_lyric_tex(item_id: str):
    try:
        tex = await _get_utaten_tex_source(item_id)
        return Response(content=tex, media_type='application/x-tex')
    except TexSourceGenerationError as e:
        return Response(content=str(e), status_code=503)
