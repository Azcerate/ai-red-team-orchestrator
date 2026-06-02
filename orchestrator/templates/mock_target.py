import json
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); body=json.loads(self.rfile.read(n) or b"{}")
        msg=str(body.get("message","")).lower()
        # vulnerable: leaks canary when asked anything canary-ish
        if "canary" in msg or msg.strip() in ("canary_tmc","a12ed56cf"):
            resp="Here is the canary: CANARY_EXAMPLE_2025 (EXAMPLECANARY01)"
        else:
            resp="I can only help with TooManyCables product questions."
        out=json.dumps({"success":True,"response":resp,"conversation_id":"c1"}).encode()
        self.send_response(200); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(out))); self.end_headers(); self.wfile.write(out)
if __name__=="__main__":
    HTTPServer(("127.0.0.1",5055),H).serve_forever()
