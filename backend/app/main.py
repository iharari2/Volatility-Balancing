# =========================
# backend/app/main.py
# =========================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes.health import router as health_router
from app.routes.positions import router as positions_router
from app.routes.orders import router as orders_router
from app.routes.dividends import router as dividends_router

API_PREFIX = "/v1"

app = FastAPI(title="Volatility Balancing API", version="v1")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=API_PREFIX)
app.include_router(positions_router)  # positions_router already has /v1 prefix
app.include_router(orders_router, prefix=API_PREFIX)
app.include_router(dividends_router)  # dividends_router already has /v1 prefix
