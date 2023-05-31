import re

import aiohttp
from fastapi import FastAPI, Response

import main

app = FastAPI()

utaten_pattern = re.compile(r'[a-z0-9]+')


@app.get("/utaten/{item_id}/pdf")
async def get_utaten_lyric_pdf(item_id: str):
    raise NotImplementedError


@app.get("/utaten/{item_id}.tex")
async def get_utaten_lyric_pdf(item_id: str, resp: Response):
    async with aiohttp.ClientSession() as ses:
        async with ses.get(f'https://utaten.com/lyric/{item_id}/') as r:
            if not r.ok:
                resp.status_code = 503
                return
            html = await r.text()
            tex = main.html_to_tex(html)
            return Response(content=tex, media_type='application/x-tex')
