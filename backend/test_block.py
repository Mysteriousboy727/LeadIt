import asyncio, os
os.environ["RATE_LIMIT_WAIT_SECONDS"] = "2"   # short waits so the test is quick
os.environ["RATE_LIMIT_RETRIES"] = "2"

from app.scraper import Connection, Blocked, NoConnection


class FakeCtx:
    def __init__(self, proxy): self.proxy = proxy
    async def route(self, *a): pass
    async def close(self): pass


class FakeBrowser:
    async def new_context(self, proxy=None, **kw):
        return FakeCtx(proxy["server"] if proxy else None)


def log(m): print("   LOG:", m)


async def scenario1():
    print("\n--- 1. Google blocks twice, then lets the request through ---")
    tries = {"n": 0}
    async def fn(ctx):
        tries["n"] += 1
        if tries["n"] <= 2:
            raise Blocked("Google showed a captcha page")
        return "listing data"
    conn = Connection(FakeBrowser(), [], log, None)
    print("   RESULT:", await conn.call(fn), "| attempts:", tries["n"])


async def scenario2():
    print("\n--- 2. Google keeps blocking ---")
    async def fn(ctx):
        raise Blocked("Google flagged unusual traffic")
    conn = Connection(FakeBrowser(), [], log, None)
    try:
        await conn.call(fn)
    except Blocked as e:
        print(f"   RESULT: job stops -> STOPPED: {e}. Leads already saved are kept.")


async def scenario3():
    print("\n--- 3. The proxy itself is dead (connection error, not a block) ---")
    pool = ["1.1.1.1:8080", "2.2.2.2:8080"]
    async def fn(ctx):
        if "1.1.1.1" in (ctx.proxy or ""):
            raise Exception("net::ERR_PROXY_CONNECTION_FAILED")
        return "ok via " + ctx.proxy
    conn = Connection(FakeBrowser(), pool, log, "1.1.1.1:8080")
    print("   RESULT:", await conn.call(fn), "| pool now:", pool)


async def main():
    await scenario1()
    await scenario2()
    await scenario3()
    print("\nDone.")

asyncio.run(main())
