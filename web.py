import argparse
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

suggest_file_name = False


@app.get("/utaten/{item_id}.pdf")
async def get_utaten_lyric_pdf(item_id: str):
    global suggest_file_name
    try:
        lyric_info = await html_cache.get_utaten_tex_source(item_id)
        pdf_path = await tex_generator.xelatex(lyric_info.tex_source)
        if not suggest_file_name:
            filename = None
        elif lyric_info.title and lyric_info.artist:
            filename = f'{lyric_info.title} - {lyric_info.artist}.pdf'
        elif not lyric_info.title and not lyric_info.artist:
            filename = f'{lyric_info.utaten_id}.pdf'
        elif lyric_info.title:
            filename = f'{lyric_info.title} - {lyric_info.utaten_id}.pdf'
        else:
            filename = f'{lyric_info.artist} - {lyric_info.utaten_id}.pdf'
        return FileResponse(pdf_path, media_type='application/pdf', filename=filename)
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


def setup_loop():
    if os.name == 'nt':
        # use ProactorEventLoop to support async subprocess on Windows
        print('Driving event loop with IOCP.')
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    auto_loop_setup()


if __name__ == '__main__':
    p = argparse.ArgumentParser(prog='utaten2tex')
    p.add_argument('-l', '--host', default='127.0.0.1')
    p.add_argument('-p', '--port', default='8080')
    p.add_argument('-s', '--suggest-file-name', action='store_true', default=False)
    args = p.parse_args()
    suggest_file_name = args.suggest_file_name
    setup_loop()
    uvicorn.run(
        'web:app',
        host=args.host,
        port=int(args.port),
        log_level='info',
        loop='none',  # use custom loop initializer
    )
