import logging.config
from pydantic import BaseModel, Field
from backend.handler import mongo_client
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socket
import datetime
from backend.handler import mongo_client, constants
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


    @app.on_event("startup")
    async def startup_event():
        try:
            """Initialize SMTP connection once when the FastAPI app starts."""
            import aiosmtplib
            import ssl
            import certifi

            constants.smtp_client = aiosmtplib.SMTP(hostname=constants.smtp_server, port=constants.port, tls_context=ssl.create_default_context(cafile=certifi.where()))
            await constants.smtp_client.connect()
            await constants.smtp_client.login(constants.sender_email, constants.password)
            print("✅ SMTP Client initialized and connected!")
        except Exception as e:
            print(f"🔴 Error initializing SMTP Client: {e}")
            


    @app.on_event("shutdown")
    async def shutdown_event():
        smtp_client = constants.smtp_client
        if smtp_client:
            await smtp_client.quit()
            print("🔴 SMTP Client disconnected!")

    @app.get("/healthz")
    async def healthz():
        logger.info(f"health check done, {socket.gethostname()}")
        return {"ping": f"health check done {socket.gethostname()}"}

    @app.get("/metrics")
    async def metrics():
        logger.info("metrics endpoint called")

    return app