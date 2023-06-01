import asyncio
import contextlib
import hashlib
import os
import shutil
import typing
import subprocess


@contextlib.contextmanager
def temp_dir(path: str):
    os.mkdir(path)
    try:
        yield path
    finally:
        # shutil.rmtree(path)
        pass


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
            with subprocess.Popen(
                    [
                        'xelatex',
                        '-interaction=nonstopmode',
                        '-halt-on-error',
                        # this seems not working, as the output file name is always set to default `texput.pdf`
                        f'-jobname={job_name}',
                    ],
                    cwd=workdir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    shell=True,
            ) as proc:
                stdout, stderr = proc.communicate(input=tex_source, timeout=self._task_timeout)
                print('STDOUT', stdout)
                print('STDERR', stderr)
                if proc.returncode != 0:
                    raise TexGenerationError(f'xelatex process exited with non-zero code {proc.returncode}')

        os.rename(os.path.join(workdir, f'{job_name}.pdf'), cache_file_path)
        return cache_file_path
