import re

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse

import htmlcache
import texgen

app = FastAPI()

utaten_pattern = re.compile(r'[a-z0-9]+')
tex_generator = texgen.TexGenerator('pdf_cache', 'temp', 20)
html_cache = htmlcache.HtmlCache('html_cache')

preview_pdf = False


@app.get("/utaten/{item_id}.pdf")
async def get_utaten_lyric_pdf(item_id: str):
    global preview_pdf
    try:
        lyric_info = await html_cache.get_utaten_tex_source(item_id)
        pdf_path = await tex_generator.xelatex(lyric_info.tex_source)
        if lyric_info.title and lyric_info.artist:
            filename = f'{lyric_info.title} - {lyric_info.artist}.pdf'
        elif not lyric_info.title and not lyric_info.artist:
            filename = f'{lyric_info.utaten_id}.pdf'
        elif lyric_info.title:
            filename = f'{lyric_info.title} - {lyric_info.utaten_id}.pdf'
        else:
            filename = f'{lyric_info.artist} - {lyric_info.utaten_id}.pdf'
        if preview_pdf:
            content_disposition_type = 'inline'
        else:
            content_disposition_type = 'attachment'
        return FileResponse(pdf_path, media_type='application/pdf', filename=filename,
                            content_disposition_type=content_disposition_type)
    except texgen.TexGenerationError as e:
        return Response(content=f'Failed to generate tex file: {e}', status_code=502)


@app.get("/utaten/{item_id}.tex")
async def get_utaten_lyric_tex(item_id: str):
    try:
        lyric_info = await html_cache.get_utaten_tex_source(item_id)
        return Response(content=lyric_info.tex_source, media_type='application/x-tex')
    except htmlcache.TexSourceGenerationError as e:
        return Response(content=str(e), status_code=503)


@app.on_event("startup")
async def startup_event():
    pass
