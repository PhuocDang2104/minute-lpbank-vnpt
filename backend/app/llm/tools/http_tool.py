import httpx


async def http_get(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return {"status": resp.status_code, "body": resp.text[:200]}