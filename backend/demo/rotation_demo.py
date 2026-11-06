import threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
import httpx

PORT, LIMIT, WINDOW = 8765, 5, 10      # each fake IP: 5 requests per 10 seconds
URL = f"http://127.0.0.1:{PORT}/"
hits = {}


# ---------- Test server you control (simulates a rate-limiting site) ----------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        ip = self.headers.get("X-Demo-IP", "unknown")
        now = time.time()
        if ip == "ip-dead":                       # simulates a proxy that is down
            self.send_response(502); self.end_headers(); return
        recent = [t for t in hits.get(ip, []) if now - t < WINDOW]
        if len(recent) >= LIMIT:
            wait = int(WINDOW - (now - recent[0])) + 1
            hits[ip] = recent
            self.send_response(429)
            self.send_header("Retry-After", str(wait))
            self.end_headers(); return
        recent.append(now); hits[ip] = recent
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


# ---------- Rotation logic ----------
class Pool:
    def __init__(self, ips):
        self.ips = list(ips)
        self.cool = {}                  # ip -> time when it may be used again
        self.cur = self.ips[0]

    def current(self):
        while True:
            if not self.ips:
                raise RuntimeError("No usable IPs left")
            now = time.time()
            if self.cur in self.ips and self.cool.get(self.cur, 0) <= now:
                return self.cur
            ready = [i for i in self.ips if self.cool.get(i, 0) <= now]
            if ready:
                self.cur = ready[0]
                print(f"  -> switched to {self.cur}")
                return self.cur
            wake = min(self.cool[i] for i in self.ips)
            print(f"  all IPs are rate-limited, waiting {wake - now:.0f}s")
            time.sleep(max(0.1, wake - now))

    def rate_limited(self, ip, seconds):
        self.cool[ip] = time.time() + seconds
        print(f"  {ip} hit a rate limit (429), cooling down {seconds}s")

    def dead(self, ip):
        self.ips.remove(ip)
        print(f"  {ip} is dead (connection failure), removed from pool")


def main():
    srv = HTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    pool = Pool(["ip-dead", "ip-1", "ip-2", "ip-3"])
    with httpx.Client() as c:
        for n in range(1, 31):
            while True:
                ip = pool.current()
                r = c.get(URL, headers={"X-Demo-IP": ip})
                if r.status_code == 200:
                    print(f"request {n:02d} OK via {ip}")
                    break
                if r.status_code == 429:
                    pool.rate_limited(ip, int(r.headers.get("Retry-After", "10")))
                else:
                    pool.dead(ip)
    print("Done: 30 requests completed")
    srv.shutdown()


if __name__ == "__main__":
    main()
