import re

from fastapi import FastAPI

app = FastAPI()

utaten_pattern = re.compile(r'[a-z0-9]+')


@app.get("/utaten/{item_id}/pdf")
def get_utaten_lyric_pdf(item_id: str):
    raise NotImplementedError
