from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
import threading
from unittest.mock import Mock, patch

from criclytics_app import create_app
from criclytics_app.services.repository import JsonRepository
from criclytics_app.services.live_cache import LiveCache, atomic_json
from criclytics_app.services.json_io import read_json
from criclytics_app.services.legacy import fetch_cricapi


class RepositoryTests(unittest.TestCase):
    def test_generations_index_last_good_and_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'completed_matches.json'
            atomic_json(path, {'data': [{'id': '1', 'teams': ['A', 'B'], 'innings': [1]}]})
            repo = JsonRepository()
            self.assertEqual(repo.match(path, '1')['innings'], [1])
            value = repo.read(path)
            value['data'][0]['innings'].append(2)
            self.assertEqual(repo.match(path, '1')['innings'], [1])
            self.assertEqual(repo.parses, 1)
            path.write_text('broken')
            self.assertIsNotNone(repo.match(path, '1'))
            atomic_json(path, {'data': [{'id': '2'}]})
            self.assertIsNone(repo.match(path, '1'))
            self.assertIsNotNone(repo.match(path, '2'))
            self.assertEqual(repo.parses, 2)
            self.assertIsNone(JsonRepository().match(path, '1'))

    def test_atomic_concurrent_readers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'entry.json'
            atomic_json(path, {'value': 0})
            def writer():
                for i in range(30):
                    atomic_json(path, {'value': i, 'padding': 'x' * 1000})
            def reader():
                for _ in range(100):
                    self.assertIn('value', read_json(path))
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(writer)] + [pool.submit(reader) for _ in range(3)]
                for future in futures:
                    future.result()

    def test_redis_timestamp_age_disk_stale_and_leases(self):
        with tempfile.TemporaryDirectory() as folder:
            redis = Mock()
            stored = {}
            redis.set.side_effect = lambda key, value, **kw: stored.update({key: value})
            redis.get.side_effect = lambda key: stored.get(key)
            now = [10000]
            cache = LiveCache(folder, redis, clock=lambda: now[0])
            cache.write('one.json', {'data': [1]}, ttl_minutes=15)
            self.assertEqual(redis.set.call_args.kwargs['ex'], 900)
            now[0] += 300
            self.assertEqual(cache.age('one.json'), 5)
            stored.clear()  # Redis TTL expiry must preserve durable stale data.
            self.assertEqual(cache.age('one.json'), 5)
            self.assertEqual(cache.read('one.json'), {'data': [1]})
            owner = cache.acquire()
            other = LiveCache(folder, clock=lambda: now[0])
            self.assertIsNone(other.acquire())
            cache.release(owner, backoff=60)
            now[0] += 61
            self.assertIsNotNone(other.acquire())

    def test_bounded_cache_and_unknown_ids_never_fetch(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = LiveCache(folder, maximum=2)
            self.assertTrue(cache.write('one.json', {}))
            self.assertTrue(cache.write('two.json', {}))
            self.assertFalse(cache.write('three.json', {}))
            app = create_app({'TESTING': True, 'INITIALIZE_ENGINE': False,
                              'LIVE_FETCH_ENABLED': True, 'CRICAPI_KEY': 'not-a-real-key',
                              'LIVE_DIR': folder, 'REDIS_URL': ''})
            with app.app_context(), patch('criclytics_app.services.legacy.source_allowed',return_value=True), patch('requests.get') as request:
                for mid in range(200):
                    self.assertIsNone(fetch_cricapi('match_info', {'id': str(mid)}, f'match_{mid}.json'))
                request.assert_not_called()
            self.assertEqual(len(list(Path(folder).glob('*.json'))), 2)

    def test_two_apps_share_provider_lease_but_not_snapshots(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = {'TESTING': True, 'INITIALIZE_ENGINE': False,
                        'LIVE_FETCH_ENABLED': True, 'CRICAPI_KEY': 'not-a-real-key',
                        'LIVE_DIR': folder, 'REDIS_URL': ''}
            apps = [create_app(settings), create_app(settings)]
            self.assertIsNot(apps[0].extensions['json_repository'], apps[1].extensions['json_repository'])
            started, finish = threading.Event(), threading.Event()
            response = Mock()
            response.json.return_value = {'data': []}
            def upstream(*args, **kwargs):
                started.set()
                self.assertTrue(finish.wait(3))
                return response
            def refresh(app):
                with app.app_context():
                    return fetch_cricapi('matches', cache_file='matches.json')
            with patch('criclytics_app.services.legacy.source_allowed',return_value=True), patch('requests.get', side_effect=upstream) as request, ThreadPoolExecutor(max_workers=2) as pool:
                future = pool.submit(refresh, apps[0])
                self.assertTrue(started.wait(3))
                self.assertIsNone(refresh(apps[1]))
                finish.set()
                self.assertEqual(future.result(), {'data': []})
                request.assert_called_once()
