from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json

BASE_URL = "https://apis.data.go.kr/1613000/ArchPmsHubService/getApBasisOulnInfo"


def fetch_sigungu(api_key, sigungu_cd):
    other = urllib.parse.urlencode({
        'sigunguCd': sigungu_cd,
        'numOfRows': '1000',
        'pageNo': '1',
        '_type': 'json'
    })
    url = f"{BASE_URL}?serviceKey={api_key}&{other}"
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('utf-8')
        data = json.loads(raw)
        body = data.get('response', {}).get('body', {})
        items_obj = body.get('items') or {}
        if not items_obj:
            return []
        items = items_obj.get('item', [])
        if isinstance(items, dict):
            items = [items]
        return items if isinstance(items, list) else []
    except Exception:
        return []


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        def gp(key, default=''):
            return qs.get(key, [default])[0]

        api_key = gp('apiKey')
        sigungu_cds = [c for c in gp('sigunguCds').split(',') if c]
        start_date = gp('startDate').replace('-', '')
        end_date = gp('endDate').replace('-', '')
        min_area = gp('minArea')
        max_area = gp('maxArea')
        main_purps_list = [p for p in gp('mainPurps').split(',') if p]
        arch_gb_list = [a for a in gp('archGb').split(',') if a]

        if not api_key:
            self._json({'success': False, 'error': 'API 키를 입력해주세요.'}, 400)
            return
        if not sigungu_cds:
            self._json({'success': False, 'error': '지역을 선택해주세요.'}, 400)
            return

        sigungu_cds = sigungu_cds[:10]

        all_items = []
        for cd in sigungu_cds:
            all_items.extend(fetch_sigungu(api_key, cd))

        filtered = []
        for item in all_items:
            stcns = (item.get('stcnsSchedYmd') or item.get('stcnsSchedPossblDe') or '').replace('-', '')

            if start_date and stcns and stcns < start_date:
                continue
            if end_date and stcns and stcns > end_date:
                continue

            try:
                area = float(item.get('totArea') or 0)
            except (ValueError, TypeError):
                area = 0

            if min_area:
                try:
                    if area < float(min_area):
                        continue
                except (ValueError, TypeError):
                    pass

            if max_area:
                try:
            if max_area:
                try:
                    if area > float(max_area):
                        continue
                except (ValueError, TypeError):
                    pass

            if main_purps_list and item.get('mainPurpsCd', '') not in main_purps_list:
                continue
            if arch_gb_list and item.get('archGbCd', '') not in arch_gb_list:
                continue

            filtered.append(item)

        filtered.sort(key=lambda x: (x.get('stcnsSchedYmd') or ''), reverse=True)
        self._json({'success': True, 'totalCount': len(filtered), 'items': filtered})

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass
