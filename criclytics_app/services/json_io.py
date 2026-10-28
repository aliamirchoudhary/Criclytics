"""Bounded atomic JSON publication and Windows sharing-safe reads."""
import json
import os
from pathlib import Path
import tempfile
import time
from contextlib import contextmanager


@contextmanager
def json_reader(path):
    if os.name != 'nt':
        with Path(path).open(encoding='utf-8') as stream:
            yield stream
        return
    # Python's default Windows open does not share delete permission. Readers
    # must permit atomic rename of the path while retaining their own old handle.
    import ctypes
    from ctypes import wintypes
    import msvcrt
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    handle = create(str(Path(path).resolve()), 0x80000000, 7, None, 3, 128, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except Exception:
        kernel.CloseHandle(wintypes.HANDLE(handle))
        raise
    with os.fdopen(descriptor, encoding='utf-8') as stream:
        yield stream

def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.cache-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(10):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                # Windows readers can briefly deny delete-sharing. Never truncate
                # the existing last-good file while waiting for them to close.
                if attempt == 9:
                    raise
                time.sleep(min(0.01 * 2 ** attempt, 0.25))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path):
    for attempt in range(10):
        try:
            with json_reader(path) as stream:
                return json.load(stream)
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.01)
