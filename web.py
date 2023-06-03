import asyncio
import os
import re

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from uvicorn.loops.auto import auto_loop_setup

import htmlcache
import texgen

app = FastAPI()

utaten_pattern = re.compile(r'[a-z0-9]+')
tex_generator = texgen.TexGenerator('pdf_cache', 'temp', 20)
html_cache = htmlcache.HtmlCache('html_cache')


@app.get("/utaten/{item_id}.pdf")
async def get_utaten_lyric_pdf(item_id: str):
    try:
        tex = await html_cache.get_utaten_tex_source(item_id)
        pdf_path = await tex_generator.xelatex(tex)
        return FileResponse(pdf_path, media_type='application/pdf')
    except texgen.TexGenerationError as e:
        return Response(content=f'Failed to generate tex file: {e}', status_code=502)


@app.get("/utaten/{item_id}.tex")
async def get_utaten_lyric_tex(item_id: str):
    try:
        tex = await html_cache.get_utaten_tex_source(item_id)
        return Response(content=tex, media_type='application/x-tex')
    except htmlcache.TexSourceGenerationError as e:
        return Response(content=str(e), status_code=503)


@app.on_event("startup")
async def startup_event():
    pass


def setup_loop():
    if os.name == 'nt':
        # use ProactorEventLoop to support async subprocess on Windows
        print('Driving event loop with IOCP.')
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    auto_loop_setup()


if __name__ == '__main__':
    setup_loop()
    uvicorn.run(
        'web:app',
        host='127.0.0.1',
        port=8000,
        log_level='info',
        loop='none',  # use custom loop initializer
    )
