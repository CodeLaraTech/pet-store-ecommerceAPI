import os
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.database import init_db
from app.utils import add_cors, add_request_logging, global_exception_handler, add_rate_limiter

from app.auth.routes import router as auth_router
from app.routers.users import router as users_router
from app.routers.pets import router as pets_router
from app.routers.products import router as products_router
from app.routers.orders import router as orders_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.analytics import router as analytics_router
from app.routers.coupons import router as coupons_router
from app.routers.payments import router as payments_router
from app.routers.admin import router as admin_router

load_dotenv()

app = FastAPI(title="Pet Meals E-commerce API", version="0.1.0")

add_cors(app)
add_request_logging(app)
add_rate_limiter(app)
app.add_exception_handler(Exception, global_exception_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(pets_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(subscriptions_router)
app.include_router(analytics_router)
app.include_router(coupons_router)
app.include_router(payments_router)
app.include_router(admin_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    init_db()