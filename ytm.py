"""Keyless YouTube Music lookups for Dialed. UNOFFICIAL. Python standard library only.

Calls the same web endpoints the music.youtube.com site itself uses, from this computer,
for song search, playlists and track details. Playback still goes through YouTube's own
embedded player. This is not an official API: it goes against YouTube's terms of service,
can change or stop working without notice, and is used at your own risk.
The request format follows the open-source ytmusicapi project (MIT).
"""
import gzip
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get('DIALED_YTM_BASE', 'https://music.youtube.com/youtubei/v1/')
KEY = 'AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30'          # YouTube Music's own public web-client key (not a Google Cloud key)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
P_SONGS = 'EgWKAQIIAWoMEA4QChADEAQQCRAF'                 # search filter: songs
P_FEATURED = 'EgeKAQQoADgBagwQDhAKEAMQBBAJEAU%3D'        # search filter: featured playlists
P_COMMUNITY = 'EgeKAQQoAEABagwQDhAKEAMQBBAJEAU%3D'       # search filter: community playlists
MIN_GAP = float(os.environ.get('DIALED_YTM_GAP', '0.4'))  # seconds between requests: stay gentle
TIMEOUT = 12


class YtmError(Exception):
    def __init__(self, message, code='http'):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------- transport
_net_lock = threading.Lock()
_last = [0.0]


def _context():
    return {'context': {'client': {'clientName': 'WEB_REMIX', 'clientVersion': '1.' + time.strftime('%Y%m%d', time.gmtime()) + '.01.00', 'hl': 'en'}, 'user': {}}}


def _ct(token):
    if not token:
        return ''
    if not re.fullmatch(r'[A-Za-z0-9_%.=~+/-]{8,3000}', token):
        raise YtmError('Bad page token.', 'http')
    t = urllib.parse.quote(token, safe='')
    return '&ctoken=' + t + '&continuation=' + t


def post(endpoint, body, extra=''):
    data = _context()
    data.update(body)
    req = urllib.request.Request(
        BASE + endpoint + '?alt=json&key=' + KEY + extra, data=json.dumps(data).encode('utf-8'), method='POST',
        headers={'User-Agent': UA, 'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Content-Type': 'application/json',
                 'Origin': 'https://music.youtube.com', 'Cookie': 'SOCS=CAI'})
    with _net_lock:                                   # one request at a time, spaced out
        wait = MIN_GAP - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                raw, enc = r.read(), r.headers.get('Content-Encoding', '')
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                raise YtmError('YouTube Music refused the request (HTTP %d). It may be limiting this connection for a while.' % e.code, 'blocked')
            raise YtmError('YouTube Music answered with HTTP %d.' % e.code, 'http')
        except (urllib.error.URLError, OSError) as e:
            raise YtmError("Couldn't reach music.youtube.com (%s)." % getattr(e, 'reason', e), 'net')
    if 'gzip' in enc:
        raw = gzip.decompress(raw)
    try:
        return json.loads(raw.decode('utf-8'))
    except ValueError:
        raise YtmError('YouTube Music sent something unexpected (not JSON). It may be asking for a consent or verification page.', 'parse')


# ---------------------------------------------------------------- cache
_cache, _cache_lock = {}, threading.Lock()


def cached(ttl):
    def deco(fn):
        def wrap(*a):
            key, now = (fn.__name__,) + a, time.time()
            with _cache_lock:
                hit = _cache.get(key)
                if hit and hit[0] > now:
                    return hit[1]
            val = fn(*a)
            with _cache_lock:
                if len(_cache) > 300:
                    _cache.clear()
                _cache[key] = (now + ttl, val)
            return val
        wrap.__name__ = fn.__name__
        return wrap
    return deco


# ---------------------------------------------------------------- parsing (tolerant: finds things by name, not by exact path)
def find(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key and isinstance(v, dict):
                yield v
            elif isinstance(v, (dict, list)):
                yield from find(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from find(v, key)


def first(o, key):
    return next(find(o, key), None)


DUR_RE = re.compile(r'^\d{1,2}(?::\d{2}){1,2}$')
TYPE_WORDS = {'song', 'video', 'single', 'ep', 'album', 'playlist', 'artist', 'episode', 'podcast', 'profile'}


def dur_secs(text):
    if not DUR_RE.match(text or ''):
        return 0
    n = 0
    for part in text.split(':'):
        n = n * 60 + int(part)
    return n


def text_of(runs):
    return ''.join(r.get('text', '') for r in (runs or []) if isinstance(r, dict))


def _bid(run):
    return (((run.get('navigationEndpoint') or {}).get('browseEndpoint') or {}).get('browseId')) or ''


def parse_byline(runs):
    """'Song • Artist & Artist • Album • 3:45'  ->  artist, album, seconds."""
    out = {'artist': '', 'album': '', 'dur': 0}
    segs, cur = [], []
    for r in runs or []:
        if isinstance(r, dict) and (r.get('text') or '').strip() == '\u2022':
            segs.append(cur)
            cur = []
        else:
            cur.append(r)
    segs.append(cur)
    for i, seg in enumerate(segs):
        text = text_of(seg).strip()
        if not text:
            continue
        if DUR_RE.match(text):
            out['dur'] = dur_secs(text)
            continue
        if re.fullmatch(r'\d{4}', text) or re.search(r'\b(views?|plays?|likes?)\b', text, re.I):
            continue
        bid = next((_bid(r) for r in seg if isinstance(r, dict) and _bid(r)), '')
        if bid.startswith('MPRE'):
            out['album'] = text
            continue
        if not bid and i == 0 and len(segs) > 1 and text.lower() in TYPE_WORDS:
            continue                                   # the "Song" / "Video" type label
        if not out['artist']:
            out['artist'] = text
    return out


def _video_id(it):
    v = (it.get('playlistItemData') or {}).get('videoId')
    if v:
        return v
    for we in find(it.get('overlay') or {}, 'watchEndpoint'):
        if we.get('videoId'):
            return we['videoId']
    return ''


def _vtype(o):
    for cfg in find(o, 'watchEndpointMusicConfig'):
        if cfg.get('musicVideoType'):
            return cfg['musicVideoType'].replace('MUSIC_VIDEO_TYPE_', '')
    return ''


def _col(it, i):
    try:
        return it['flexColumns'][i]['musicResponsiveListItemFlexColumnRenderer']['text']['runs']
    except (KeyError, IndexError, TypeError):
        return []


def parse_item(it):
    vid = _video_id(it)
    title = text_of(_col(it, 0)).strip()
    if not vid or not title:
        return None                                    # greyed-out / unavailable rows have no video id
    by = parse_byline(_col(it, 1))
    dur = by['dur']
    if not dur:                                        # playlist pages keep the length in a fixed column
        for fc in it.get('fixedColumns') or []:
            t = text_of((((fc or {}).get('musicResponsiveListItemFixedColumnRenderer') or {}).get('text') or {}).get('runs')).strip()
            if DUR_RE.match(t):
                dur = dur_secs(t)
                break
    album = by['album'] or text_of(_col(it, 2)).strip()
    return {'id': vid, 'title': title, 'artist': by['artist'], 'album': album, 'dur': dur, 'type': _vtype(it)}


def parse_panel_item(d):
    if not isinstance(d, dict) or 'unplayableText' in d or not d.get('videoId'):
        return None
    title = text_of((d.get('title') or {}).get('runs')).strip()
    by = parse_byline((d.get('longBylineText') or {}).get('runs'))
    dur = dur_secs(text_of((d.get('lengthText') or {}).get('runs')).strip()) or by['dur']
    return {'id': d['videoId'], 'title': title, 'artist': by['artist'], 'album': by['album'], 'dur': dur, 'type': _vtype(d)} if title else None


def continuation_of(resp):
    c = first(resp, 'nextContinuationData')
    if c and c.get('continuation'):
        return c['continuation']
    cc = first(resp, 'continuationCommand')
    return cc.get('token') if cc and cc.get('token') else None


def _dedupe(tracks):
    seen, out = set(), []
    for t in tracks:
        if t['id'] not in seen:
            seen.add(t['id'])
            out.append(t)
    return out


# ---------------------------------------------------------------- lookups
@cached(600)
def search_songs(q, token=None):
    q = (q or '').strip()[:200]
    if not q:
        return {'tracks': [], 'next': None}
    resp = post('search', {'query': q, 'params': P_SONGS}, _ct(token))
    raw = list(find(resp, 'musicResponsiveListItemRenderer'))
    tracks = _dedupe([t for t in map(parse_item, raw) if t])
    if raw and not tracks:
        raise YtmError("YouTube Music's response changed shape, so nothing could be read from it.", 'parse')
    return {'tracks': tracks, 'next': continuation_of(resp) if tracks else None}


@cached(1800)
def search_playlists(q):
    q = (q or '').strip()[:200]
    if not q:
        return []
    out, seen = [], set()
    for params in (P_FEATURED, P_COMMUNITY):          # featured (curated) first, then community
        resp = post('search', {'query': q, 'params': params})
        for it in find(resp, 'musicResponsiveListItemRenderer'):
            bid = ((it.get('navigationEndpoint') or {}).get('browseEndpoint') or {}).get('browseId') or ''
            pid = bid[2:] if bid.startswith('VL') else ''
            if not pid:
                for w in find(it.get('overlay') or {}, 'watchPlaylistEndpoint'):
                    if w.get('playlistId'):
                        pid = w['playlistId']
                        break
            title = text_of(_col(it, 0)).strip()
            if pid and title and pid not in seen:
                seen.add(pid)
                out.append({'id': pid, 'title': title, 'meta': text_of(_col(it, 1)).strip(), 'featured': params == P_FEATURED})
    return out


@cached(1800)
def playlist_tracks(pid, token=None):
    pid = (pid or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{2,80}', pid):
        raise YtmError('Bad playlist id.', 'http')
    resp = post('browse', {'browseId': pid if pid.startswith('VL') else 'VL' + pid}, _ct(token))
    shelf = first(resp, 'musicPlaylistShelfContinuation') or first(resp, 'musicPlaylistShelfRenderer') or resp
    raw = list(find(shelf, 'musicResponsiveListItemRenderer'))
    tracks = _dedupe([t for t in map(parse_item, raw) if t])
    if raw and not tracks:
        raise YtmError("YouTube Music's response changed shape, so nothing could be read from it.", 'parse')
    return {'tracks': tracks, 'next': continuation_of(resp) if tracks else None}


@cached(3600)
def video_info(ids):
    out = []
    for vid in ids[:8]:
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
            continue
        resp = post('next', {'enablePersistentPlaylistPanel': True, 'isAudioOnly': True, 'tunerSettingValue': 'AUTOMIX_SETTING_NORMAL', 'videoId': vid})
        panel = first(resp, 'playlistPanelRenderer') or {}
        cands = []
        for item in panel.get('contents') or []:
            if 'playlistPanelVideoWrapperRenderer' in item:
                item = (item['playlistPanelVideoWrapperRenderer'].get('primaryRenderer') or {})
            t = parse_panel_item(item.get('playlistPanelVideoRenderer'))
            if t:
                cands.append(t)
        pick = next((t for t in cands if t['id'] == vid), cands[0] if cands else None)
        if pick:
            out.append(pick)
    return out


def selftest():
    t0 = time.time()
    try:
        r = search_songs('daft punk around the world')
        n = len(r['tracks'])
        return {'ok': n > 0, 'count': n, 'ms': int((time.time() - t0) * 1000), 'sample': r['tracks'][:3],
                'error': '' if n else 'The search worked but returned nothing readable.'}
    except YtmError as e:
        return {'ok': False, 'count': 0, 'ms': int((time.time() - t0) * 1000), 'code': e.code, 'error': str(e)}
