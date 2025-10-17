import os
import time
from typing import Optional, Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware


def get_env(key: str, default: Optional[str] = None) -> str:
    return os.getenv(key, default) or (default or "")


def add_cors(app: FastAPI):
    origins = [o.strip() for o in get_env("CORS_ORIGINS", "").split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def add_request_logging(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        response.headers["X-Process-Time-ms"] = str(duration_ms)
        return response


class SimpleRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 300):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.buckets: Dict[str, Dict[str, int]] = {}

    def is_allowed(self, key: str) -> bool:
        now = int(time.time())
        bucket = self.buckets.get(key) or {"count": 0, "reset": now + self.window_seconds}
        if now > bucket["reset"]:
            bucket = {"count": 0, "reset": now + self.window_seconds}
        bucket["count"] += 1
        self.buckets[key] = bucket
        return bucket["count"] <= self.max_requests


rate_limiter = SimpleRateLimiter(max_requests=int(get_env("RATE_LIMIT_MAX", "100")), window_seconds=int(get_env("RATE_LIMIT_WINDOW", "300")))


def add_rate_limiter(app: FastAPI):
    @app.middleware("http")
    async def limit_requests(request: Request, call_next):
        # Use IP as key; fall back to host
        client_ip = request.headers.get("X-Forwarded-For") or request.client.host or "unknown"
        # Exempt docs and health
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/health"):
            return await call_next(request)
        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        return await call_next(request)


def global_exception_handler(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "error": str(exc)})


def suggest_portion_and_meal(weight: Optional[float], activity_level: Optional[str]) -> Dict[str, str]:
    if not weight:
        return {"portion": "N/A", "meal_type": "balanced"}
    base = 2.5  # percent of body weight
    if activity_level == "high":
        base += 0.5
    elif activity_level == "low":
        base -= 0.5
    portion_kg = round(weight * (base / 100.0), 2)
    meal_type = "high-protein" if activity_level == "high" else "balanced"
    return {"portion": f"{portion_kg} kg/day", "meal_type": meal_type}