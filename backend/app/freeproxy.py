import asyncio, random, time, ipaddress
from urllib.parse import urlsplit
import httpx

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
]
TEST_URL = "https://www.google.com/generate_204"
CHECK_TIMEOUT = 6.0
MAX_LATENCY = 5.0
MAX_CONCURRENT_CHECKS = 60
DEFAULT_POOL_SIZE = 10
DEFAULT_SAMPLE_SIZE = 600


def _log(log, msg):
    try:
        log(msg)
    except Exception:
        print(msg)


def normalize_proxy(p):
    """Return host:port, or None if malformed/unsupported."""
    if not p:
        return None
    p = p.strip()
    if not p or p.startswith("#") or p.startswith(("https://", "socks")):
        return None
    if p.startswith("http://"):
        p = p[7:]
    if "://" in p:
        return None
    try:
        u = urlsplit("//" + p)
        host, port = u.hostname, u.port
        if not host or not port or not (1 <= port <= 65535):
            return None
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if any(c.isspace() for c in host):
                return None
        return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"
    except (ValueError, TypeError):
        return None


def proxy_url(p):
    """Accepts host:port or a full URL (paid proxies with credentials) -> URL."""
    if not p:
        return None
    return p if "://" in p else f"http://{p}"


async def fetch_proxies():
    found = set()
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        for src in PROXY_SOURCES:
            try:
                r = await c.get(src)
                r.raise_for_status()
                for line in r.text.splitlines():
                    n = normalize_proxy(line)
                    if n:
                        found.add(n)
            except Exception:
                pass
    return list(found)


async def check_proxy(p):
    try:
        t = time.perf_counter()
        async with httpx.AsyncClient(proxy=proxy_url(p), timeout=CHECK_TIMEOUT,
                                     trust_env=False) as c:
            r = await c.get(TEST_URL)
        dt = time.perf_counter() - t
        if r.status_code == 204 and dt <= MAX_LATENCY:
            return p
    except Exception:
        pass
    return None


async def fill_pool(pool, log=print, stop=None, max_pool=DEFAULT_POOL_SIZE,
                    sample=DEFAULT_SAMPLE_SIZE):
    """Adds working proxies to `pool` (a list) as each one passes."""
    cands = await fetch_proxies()
    if not cands:
        _log(log, "[Proxy] Could not download any proxy lists")
        return
    random.shuffle(cands)
    cands = cands[:sample]
    _log(log, f"[Proxy] Testing {len(cands)} free proxies in the background")
    sem = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)

    async def one(p):
        if (stop and stop.is_set()) or len(pool) >= max_pool:
            return
        async with sem:
            if (stop and stop.is_set()) or len(pool) >= max_pool:
                return
            ok = await check_proxy(p)
        if ok and ok not in pool and len(pool) < max_pool:
            pool.append(ok)
            _log(log, f"[Proxy] Working proxy found ({len(pool)} in pool)")

    await asyncio.gather(*(one(p) for p in cands), return_exceptions=True)
    if not pool:
        _log(log, "[Proxy] No free proxy passed the test (normal for free lists)")


async def wait_for_pool(pool, timeout):
    end = time.time() + timeout
    while not pool and time.time() < end:
        await asyncio.sleep(1)
    return bool(pool)


if __name__ == "__main__":
    async def _main():
        pool = []
        await fill_pool(pool)
        print("Working:", pool)
    asyncio.run(_main())