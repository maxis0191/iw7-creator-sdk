"""Explicit loopback-only immutable HUD FF endpoint. No game or client launch."""
import argparse
import datetime as dt
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import threading
import stat

URL_PATH = '/mods/paris_lab_hud/mod.ff'
MAX_BYTES = 1600


def snapshot(path, expected_sha256):
    path = Path(path)
    for candidate in (path, *path.parents):
        info = candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Linked HTTP artifact refused')
    # Bound allocation before reading; reject a growth race too.
    if not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError('Expected bounded nonempty HUD FF')
    with path.open('rb') as file:
        payload = file.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES or hashlib.sha256(payload).hexdigest() != expected_sha256.lower():
        raise ValueError('HTTP artifact size/hash mismatch')
    return payload


def endpoint(payload, log_path):
    digest = hashlib.sha256(payload).hexdigest()
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        timeout = 5

        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path != URL_PATH:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(payload)
            with lock, Path(log_path).open('a', encoding='utf-8') as log:
                log.write(json.dumps({'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                                      'method': 'GET', 'path': URL_PATH, 'bytes': len(payload),
                                      'sha256': digest}) + '\n')

    return HTTPServer(('127.0.0.1', 0), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ff', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--endpoint-json', required=True)
    parser.add_argument('--request-log', required=True)
    args = parser.parse_args()
    for target in (args.endpoint_json, args.request_log):
        if Path(target).exists():
            raise ValueError('Fresh evidence paths required')
    data = snapshot(args.ff, args.sha256)
    server = endpoint(data, args.request_log)
    try:
        Path(args.endpoint_json).write_text(json.dumps({'schema': 'iw7.hud-http/1',
            'base_url': 'http://127.0.0.1:' + str(server.server_port),
            'path': URL_PATH, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}, indent=2) + '\n', encoding='utf-8')
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
