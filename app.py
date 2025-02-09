import logging.config
from pydantic import BaseModel, Field
from backend.handler import mongo_client
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socket
import datetime
from backend.handler import mongo_client
from routers import company, ledger, bid
logger = logging.getLogger(__name__)


def start_server():
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(company.company_router)
    app.include_router(bid.bid_router)
    app.include_router(ledger.ledger_router)

    @app.get("/healthz")
    async def healthz():
        logger.info(f"health check done, {socket.gethostname()}")
        return {"ping": f"health check done {socket.gethostname()}"}

    @app.get("/metrics")
    async def metrics():
        logger.info("metrics endpoint called")

    return app