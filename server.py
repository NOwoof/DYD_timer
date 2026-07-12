"""
丫丫计时器 — 通知代理（配合 Nginx 使用）
只做 API 转发，静态文件由 Nginx 直接服务
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json
import sys

PORT = 8080
BIND = '127.0.0.1'   # 只监听本地，由 Nginx 反代


class APIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except json.JSONDecodeError:
            self._reply(400, {'success': False, 'reason': 'JSON 解析失败'})
            return

        channel = body.get('channel', 'qmsg')

        if channel == 'serverchan':
            self._proxy_serverchan(body)
        else:
            self._proxy_qmsg(body)

    def _proxy_qmsg(self, p):
        key = p.get('key', '')
        if not key:
            return self._reply(400, {'success': False, 'reason': 'Key 不能为空'})

        payload = json.dumps({'msg': p.get('msg', '')}).encode()
        try:
            self._forward(
                f'https://qmsg.zendee.cn/jsend/{key}',
                payload,
                {'Content-Type': 'application/json'},
            )
        except Exception as e:
            self._reply(502, {'success': False, 'reason': str(e)})

    def _proxy_serverchan(self, p):
        key = p.get('key', '')
        if not key:
            return self._reply(400, {'success': False, 'reason': 'SendKey 不能为空'})

        payload = urllib.parse.urlencode({
            'title': p.get('title', '丫丫计时器'),
            'desp': p.get('msg', ''),
        }).encode('utf-8')
        try:
            self._forward(
                f'https://sctapi.ftqq.com/{key}.send',
                payload,
                {'Content-Type': 'application/x-www-form-urlencoded'},
            )
        except Exception as e:
            self._reply(502, {'success': False, 'reason': str(e)})

    def _forward(self, url, data, headers):
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self._reply(resp.status, json.loads(resp.read()))
        except urllib.error.HTTPError as e:
            body = json.loads(e.read()) if e.fp else {}
            self._reply(e.code, body)

    def _reply(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        print(f'[{self.log_date_time_string()}] {args[0]}', flush=True)


print(f'[API Proxy] {BIND}:{PORT}', flush=True)
HTTPServer((BIND, PORT), APIHandler).serve_forever()
