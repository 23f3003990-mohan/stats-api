import time
import uuid

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response

EMAIL = "23f3003990@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://dash-doklv4.example.com"

app = FastAPI()


def cors_headers(origin):
    if origin != ALLOWED_ORIGIN:
        return {}
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Expose-Headers": "X-Request-ID, X-Process-Time",
        "Access-Control-Max-Age": "600",
    }


@app.middleware("http")
async def cors_and_timing(request: Request, call_next):
    start = time.perf_counter()
    origin = request.headers.get("origin")

    if request.method == "OPTIONS":
        # Preflight: allowed origin gets 200 + ACAO; anyone else gets 403 with no ACAO.
        response = Response(status_code=200 if origin == ALLOWED_ORIGIN else 403)
    else:
        response = await call_next(request)

    for k, v in cors_headers(origin).items():
        response.headers[k] = v
    response.headers["Vary"] = "Origin"
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"
    return response


def stats(values: str):
    try:
        nums = [int(v) for v in values.replace(" ", "").split(",") if v != ""]
    except ValueError:
        return JSONResponse({"error": "values must be comma-separated integers"}, status_code=400)
    if not nums:
        return JSONResponse({"error": "no values provided"}, status_code=400)
    total = sum(nums)
    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": total,
        "min": min(nums),
        "max": max(nums),
        "mean": total / len(nums),
    }


@app.get("/{full_path:path}")
def router(full_path: str, values: str = Query(None)):
    # Vercel may pass "/stats", "/api/index/stats" or "/api/index" (with the original
    # path elsewhere), so match on the last path segment instead of an exact route.
    if full_path.rstrip("/").split("/")[-1] == "stats" or values is not None:
        if values is None:
            return JSONResponse({"error": "missing values query parameter"}, status_code=400)
        return stats(values)
    return {"status": "ok", "endpoint": "/stats?values=1,2,3", "seen_path": "/" + full_path}
