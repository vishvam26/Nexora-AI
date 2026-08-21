from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_data = {
            "status": "online",
            "message": "Nexora AI Edge Node Ready",
            "frontend_root": "apps/frontend"
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
        return
