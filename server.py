import http.server
import urllib.request
import urllib.parse
import json
import os
import sys

PORT = 8080

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_notify()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_notify()
        else:
            self.send_error(404)

    def proxy_notify(self):
        """Forward request to Qmsg or Server酱 API with CORS headers."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            params = json.loads(body)

            channel = params.get('channel', 'qmsg')  # 'qmsg' or 'serverchan'

            if channel == 'serverchan':
                self._proxy_serverchan(params)
            else:
                self._proxy_qmsg(params)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False, 'reason': 'JSON 解析失败', 'code': -1
            }).encode())
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'reason': str(e), 'code': -1}).encode())

    def _proxy_qmsg(self, params):
        """Proxy request to Qmsg酱 API."""
        key = params.get('key', '')
        msg = params.get('msg', '')
        qq = params.get('qq', '')

        if not key:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False, 'reason': 'Key 不能为空', 'code': -1
            }).encode())
            return

        qmsg_url = f'https://qmsg.zendee.cn/jsend/{key}'
        payload_data = {'msg': msg}
        if qq:
            payload_data['qq'] = qq
        payload = json.dumps(payload_data).encode()

        try:
            req = urllib.request.Request(
                qmsg_url,
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            err_body = e.read() if e.fp else b'{}'
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(err_body)

    def _proxy_serverchan(self, params):
        """Proxy request to Server酱 (ServerChan) API.

        Server酱文档: https://sct.ftqq.com/
        注册后在 https://sct.ftqq.com/sendkey 获取 SendKey
        """
        sendkey = params.get('key', '')
        title = params.get('title', '丫丫计时器')
        desp = params.get('msg', '')

        if not sendkey:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False, 'reason': 'SendKey 不能为空', 'code': -1
            }).encode())
            return

        # Server酱 API v2
        url = f'https://sctapi.ftqq.com/{sendkey}.send'
        # Use form-encoded data as Server酱 expects
        form_data = urllib.parse.urlencode({
            'title': title,
            'desp': desp
        }).encode('utf-8')

        try:
            req = urllib.request.Request(
                url,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            err_body = e.read() if e.fp else b'{}'
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(err_body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f'[Yaya Timer] http://localhost:{PORT}')
print(f'[Qmsg Proxy]   /api/qmsg/send')
print(f'[ServerChan]   /api/serverchan/send')
sys.stdout.flush()
http.server.HTTPServer(('127.0.0.1', PORT), ProxyHandler).serve_forever()
