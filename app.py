import argparse
import asyncio
import os

import uvicorn
from uvicorn.loops.auto import auto_loop_setup

import web


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
    p.add_argument('-P', '--preview-pdf', action='store_true', default=False)
    args = p.parse_args()
    web.preview_pdf = args.preview_pdf
    setup_loop()
    uvicorn.run(
        'web:app',
        host=args.host,
        port=int(args.port),
        log_level='info',
        loop='none',  # use custom loop initializer
    )
