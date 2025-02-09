from fastapi import APIRouter, Depends, HTTPException
from backend.handler import mongo_client
import socket
import logging
import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

ledger_router = APIRouter()


class Utr(BaseModel):
    utr: str = Field(..., description="ledger id")

@ledger_router.get("/{company_id}/ledger")
async def get_ledger(company_id: int,  page: int=1, limit: int=10, filter: str = 'all'): # NOSONAR filter = all, to_pay, to_be_get_paid, paid
    ledger = mongo_client.get_collection("ledger")
    query = {
        "$or": [
            {"ordering_company_id": company_id}, # from 
            {"winner_company_id": company_id} # to
        ]
    }

    if filter != "all":
        query = {}
        if filter == "to_pay":
            query["ordering_company_id"] = company_id
            query["status"] = "active"
        elif filter == "to_be_get_paid":
            query["winner_company_id"] = company_id
            query["status"] = "active"
        elif filter == "paid":
            query = {
                "$or": [
                    {"ordering_company_id": company_id}, # from 
                    {"winner_company_id": company_id} # to
                ]
            }
            query["status"] = "completed"
    if page < 1:
        skip = 0
    else:
        skip = (page - 1) * limit
    print(query, "ofnmmfn")
    res = list(ledger.find(query).sort({"created_at": -1}).skip(skip).limit(limit))
    for r in res:
        del r["_id"]

    return {
        "total": ledger.count_documents(query),
        "page": page,
        "limit": limit,
        "ledger": res
    }


@ledger_router.post("/{company}/ledger/{ledger_id}")
async def payout_ledger(company: int, ledger_id: str, utr: Utr):
    ledger = mongo_client.get_collection("ledger")
    res = ledger.find_one({"ledger_id": ledger_id})
    if not res:
        return {"message": "Ledger not found", "success": False}
    if company != res.get("ordering_company_id"):
        return {"message": "You can't payout for this ledger", "success": False}
    if res["status"] != "active":
        return {"message": "Ledger is already completed", "success": False}
    ledger.update_one({
        "ledger_id": ledger_id},
            {"$set": {"status": "completed", "updated_at": datetime.datetime.now(),
        "utr": utr.utr
    }})
    return {"message": "Payout done successfully", "success": True}