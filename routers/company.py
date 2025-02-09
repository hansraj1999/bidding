from fastapi import APIRouter, Depends, HTTPException
from backend.handler import mongo_client
import socket
import logging
import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

company_router = APIRouter()


class RegisterCompany(BaseModel):
    name: str = Field(..., description="Name of the company")
    tennet: str = Field("FYND", description="Tennet of the company")


class BankDetails(BaseModel):
    account_number: str = Field(..., description="account number")
    ifsc: str = Field(..., description="ifsc code")
    bank_name: str = Field(..., description="bank name")
    vpa: str = Field(..., description="vpa")
    account_type: str = Field(..., description="account type can be current or saving")
    beneficiary_name: str = Field(..., description="benificary_name")
    mobile_number: str = Field(..., description="Mobile number of the company")
    mail_id: str = Field(..., description="Mail id of the company")


@company_router.post("/register/{company_id}")
async def register_company(company_id: int, request: RegisterCompany):
    try:
        company = mongo_client.get_collection("company")
        print(request.dict(), "onfonfonf")
        res = company.find_one({"company_id": company_id})
        if res:
            return {"message": "Company already registered", "success": False}
        print(company.insert_one(
            {
                "mail_id": request.mail_id,
                "mobile_number": request.mobile_number,
                "company_id": company_id, "name": request.name,
                "tennet": request.tennet, "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now(),
                "rating": 0, "total_bids": 0, "total_wins": 0
            }
        ))
        return {"message": "Company registered", "success": True}
    except Exception as e:
        print(e)
        return {"message": "Company not registered", "success": False}


@company_router.post("/register/{company_id}/phone")
async def update_phone_number(company_id: int, mobile_number: str):
    company = mongo_client.get_collection("company")
    print(company.update_one({"company_id": company_id}, {"$set": {
        "mobile_number": mobile_number,
        "updated_at": datetime.datetime.now()
    }}))
    return {"message": "Phone Number Updated", "success": True}


@company_router.post("/register/{company_id}/banking")
async def add_banking_details(company_id: int, bank_details: BankDetails):
    company = mongo_client.get_collection("company")
    print(company.update_one({"company_id": company_id}, {"$set": {
        **bank_details.dict(),
        "updated_at": datetime.datetime.now()
    }}))
    return {"message": "Bank Details Updated", "success": True}

@company_router.get("/{company_id}/details")
async def get_company_details(company_id: int):
    company = mongo_client.get_collection("company")
    res = company.find_one({"company_id": company_id})
    if not res:
        return {"message": "Company not found", "success": False}
    del res["_id"]
    r = {}
    r["success"] = True
    r["data"] = res
    
    return r