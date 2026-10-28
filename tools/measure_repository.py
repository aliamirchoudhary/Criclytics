"""Offline repository cold/warm timing and Windows working-set evidence."""
import ctypes
from ctypes import wintypes
import json
import time

from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT


def working_set():
    if not hasattr(ctypes, 'windll'):
        return None
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    query = ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if query(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        return counters.WorkingSetSize
    return None


def main():
    app = create_app({'INITIALIZE_ENGINE': False, 'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''})
    result = {'before_bytes': working_set(), 'samples': []}
    with app.test_client() as client:
        for mode in ('cold_list', 'warm_list'):
            start = time.perf_counter()
            response = client.get('/api/matches?status=completed')
            assert response.status_code == 200
            result['samples'].append({'mode': mode, 'milliseconds': round((time.perf_counter()-start)*1000, 2),
                                      'bytes': len(response.data)})
        mid = response.json['data'][0]['id']
        for mode in ('first_detail', 'warm_detail'):
            start = time.perf_counter()
            response = client.get('/api/matches/' + mid)
            assert response.status_code == 200
            result['samples'].append({'mode': mode, 'milliseconds': round((time.perf_counter()-start)*1000, 2),
                                      'bytes': len(response.data)})
        result['json_parses'] = app.extensions['json_repository'].parses
        result['after_bytes'] = working_set()
    result['limitations'] = 'Single Windows process, local files, OS cache not flushed, engine disabled. Not a hosted capacity guarantee.'
    (PROJECT_ROOT / 'docs/audit/repositories-2026-10-28.json').write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
