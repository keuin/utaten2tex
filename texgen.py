import asyncio
import asyncio.subprocess as subprocess
import contextlib
import hashlib
import os
import shutil

from aiofile import async_open


@contextlib.contextmanager
def temp_dir(path: str):
    os.mkdir(path)
    try:
        yield path
    finally:
        shutil.rmtree(path)


class TexGenerationError(Exception):
    pass


class TexGenerator:

    def __init__(self, storage_path: str, temp_path: str, task_timeout):
        self._storage_path = os.path.abspath(storage_path)
        self._temp_path = os.path.abspath(temp_path)
        self._task_timeout = task_timeout
        for p in (self._temp_path, self._storage_path):
            try:
                os.mkdir(p)
            except FileExistsError:
                pass

    async def xelatex(self, tex_source: str) -> str:
        tex_hash = hashlib.sha256(tex_source.encode('utf-8')).hexdigest()
        cache_file_path = os.path.join(self._storage_path, f'{tex_hash}.pdf')
        if os.path.exists(cache_file_path):
            return cache_file_path
        with temp_dir(os.path.join(self._temp_path, os.urandom(24).hex())) as workdir:
            job_name = 'texput'
            tex_file_path = os.path.join(workdir, f'{job_name}.tex')
            async with async_open(tex_file_path, 'w', encoding='utf-8') as f:
                await f.write(tex_source)
            proc = await subprocess.create_subprocess_exec(
                *[
                    'xelatex',
                    '-interaction=nonstopmode',
                    '-halt-on-error',
                    tex_file_path,
                ],
                cwd=workdir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(proc.wait(), timeout=10)
            except TimeoutError:
                raise TexGenerationError('xelatex timed out')
            if proc.returncode != 0:
                raise TexGenerationError(f'xelatex process exited with non-zero code {proc.returncode}')
            os.rename(os.path.join(workdir, f'{job_name}.pdf'), cache_file_path)
        return cache_file_path