"""Dialed's tiny local web server. Python standard library only.

Serves this folder on http://localhost:8765 and labels scripts and WebAssembly files
correctly (some Windows setups get this wrong, which would stop the DJ's voice loading).
"""
import http.server
import ipaddress
import json
import os
import socket
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ytm  # noqa: E402  (keyless YouTube Music lookups, unofficial)

PORT = int(os.environ.get('DIALED_PORT', '8765'))
LAN = os.environ.get('DIALED_LAN') == '1' or '--phone' in sys.argv      # phone mode: reachable from other devices on your Wi-Fi
BIND = '0.0.0.0' if LAN else '127.0.0.1'
PRIVATE = [ipaddress.ip_network(n) for n in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '169.254.0.0/16', '100.64.0.0/10')]


def host_ok(host):
    """Only this computer's own page (or, in phone mode, a page reached by a private network address) may use the lookups.
    Requiring an address, not a name, also shuts out DNS-rebinding tricks from other websites."""
    name, sep, port = host.rpartition(':')
    if not sep or port != str(PORT):
        return False
    if name in ('localhost', '127.0.0.1'):
        return True
    if LAN:
        try:
            a = ipaddress.ip_address(name)
        except ValueError:
            return False
        return a.version == 4 and any(a in n for n in PRIVATE)
    return False


def lan_ips():
    forced = os.environ.get('DIALED_LAN_IPS')      # optional: name the address(es) yourself, e.g. when a computer has several network adapters
    if forced:
        return [i.strip() for i in forced.split(',') if i.strip()]
    found = []
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sk.settimeout(0.2)
        sk.connect(('10.255.255.255', 1))          # no traffic is sent: this just asks the OS which network address it would use
        found.append(sk.getsockname()[0])
        sk.close()
    except OSError:
        pass
    try:
        found += socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        pass
    out = []
    for ip in found:
        try:
            a = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if a.version == 4 and not a.is_loopback and any(a in n for n in PRIVATE) and ip not in out:
            out.append(ip)
    return sorted(out, key=lambda ip: ip.startswith('169.254.'))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        '.js': 'text/javascript',
        '.mjs': 'text/javascript',
        '.wasm': 'application/wasm',
        '.json': 'application/json',
        '.css': 'text/css',
        '.html': 'text/html',
        '.woff2': 'font/woff2',
        '.webmanifest': 'application/manifest+json',
        '.png': 'image/png',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def end_headers(self):
        if not getattr(self, '_api', False):
            # the big voice files never change: let the browser keep them; everything else always revalidates
            self.send_header('Cache-Control', 'public, max-age=86400' if self.path.startswith('/tts/') else 'no-cache')
        super().end_headers()

    def send_json(self, status, data):
        body = json.dumps(data).encode('utf-8')
        self._api = True
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith('/api/ytm/') or self.path.split('?')[0] == '/api/lan':
            return self.api()
        return super().do_GET()

    def api(self):
        if not host_ok(self.headers.get('Host', '')):
            return self.send_json(403, {'error': 'Not allowed.', 'code': 'forbidden'})
        u = urllib.parse.urlparse(self.path)
        q, name = dict(urllib.parse.parse_qsl(u.query)), ('lan' if u.path == '/api/lan' else u.path[len('/api/ytm/'):])
        try:
            if name == 'search':
                data = ytm.search_songs(q.get('q', ''), q.get('token') or None)
            elif name == 'playlists':
                data = {'playlists': ytm.search_playlists(q.get('q', ''))}
            elif name == 'playlist':
                data = ytm.playlist_tracks(q.get('id', ''), q.get('token') or None)
            elif name == 'video':
                data = {'tracks': ytm.video_info(tuple(i for i in q.get('ids', '').split(',') if i))}
            elif name == 'selftest':
                data = ytm.selftest()
            elif name == 'lan':
                data = {'lan': LAN, 'port': PORT, 'urls': ['http://%s:%d/' % (ip, PORT) for ip in lan_ips()] if LAN else []}
            else:
                return self.send_json(404, {'error': 'Unknown endpoint.', 'code': 'http'})
        except ytm.YtmError as e:
            return self.send_json(502, {'error': str(e), 'code': e.code})
        except Exception as e:  # never let a lookup problem take the server down
            return self.send_json(500, {'error': 'Server error: %s' % e, 'code': 'http'})
        self.send_json(200, data)

    def log_message(self, *args):
        pass


def main():
    try:
        server = http.server.ThreadingHTTPServer((BIND, PORT), Handler)
    except OSError as err:
        print("Couldn't start on port %d (%s). Is Dialed already running in another window?" % (PORT, err))
        sys.exit(1)
    if LAN:
        urls = ['http://%s:%d' % (ip, PORT) for ip in lan_ips()]
        print('Dialed is running in PHONE MODE.')
        print('  On this computer:  http://localhost:%d' % PORT)
        print('  On your phone (same Wi-Fi):  ' + (',  '.join(urls) or '(no Wi-Fi address found)'))
        print('  For a QR code, open http://localhost:%d/phone.html on this computer.' % PORT)
        print('  Windows may ask to let Python through the firewall: allow it on Private networks.')
        print('  Press Ctrl+C or close this window to stop.')
    else:
        print('Dialed is running at http://localhost:%d  (open it in Brave; press Ctrl+C or close this window to stop)' % PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
