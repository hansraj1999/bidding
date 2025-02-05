import logging.config

from fastapi import FastAPI
# from routers import short_url
from fastapi.middleware.cors import CORSMiddleware
import logging
import socket
import datetime
from backend.handler import mongo_client

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

    # app.include_router(short_url.router)
    @app.get("/bids/{bid_id}/applied_bids")
    async def get_bids_for_a_bid(bid_id):
        applied_bids = mongo_client.get_collection("applied_bids")
        res = list(applied_bids.find({"bid_id": bid_id}))
        if not res:
            return {"message": "No applied bids found"}
        for _bid in res:
            del _bid["_id"]
        return res

    @app.get("/{company_id}/bids")
    async def bids_by_company_id(company_id: int, filter_type: str = "active", limit: int = 10, page: int = 0):
        bid = mongo_client.get_collection("bid")
        if page < 1:
            skip = 0
        else:
            skip = (page - 1) * limit
        print("fpfa", filter_type, company_id)
        bids = list(bid.find({"status": filter_type, "ordering_company_id": company_id}).skip(skip).limit(limit))
        for _bid in bids:
            del _bid["_id"]
        return {
            "total": bid.count_documents({"status": filter_type, "ordering_company_id": company_id}),
            "page": page,
            "limit": limit,
            "bids": bids
        }
        
    @app.get("/{company_id}/bids/{bid_id}")
    async def get_bid_by_bid_id_and_company_id(company_id, bid_id: int):
        logger.info(socket.gethostname())
        logger.info(socket.gethostname())
        bid = mongo_client.get_collection("bid")
        res = bid.find_one({"bid_id": bid_id, "ordering_company_id": company_id})
        if not res:
            return {"message": "Bid not found"}
        del res["_id"]
        return res

    @app.get("/bids")
    async def get_gloabl_bids(filter: str ="active", limit: int = 10, page: int = 0):
        logger.info(socket.gethostname())
        bid = mongo_client.get_collection("bid")
        if page < 1:
            skip = 0
        else:
            skip = (page - 1) * limit
        bids = list(bid.find({"status": filter}).skip(skip).limit(limit))
        for _bid in bids:
            del _bid["_id"]
        return {
            "total": bid.count_documents({"status": filter}),
            "page": page,
            "limit": limit,
            "bids": bids
        }

    @app.get("/bids/{bid_id}")
    async def get_gloabl_bid_by_bid_id(bid_id: str):
        logger.info(socket.gethostname())
        bid = mongo_client.get_collection("bid")
        res = bid.find_one({"bid_id": bid_id})
        if not res:
            return {"message": "Bid not found"}
        del res["_id"]
        return res

    from pydantic import BaseModel, Field
    from typing import Optional

    class BidRequest(BaseModel):
        initial_bid_price: Optional[float] = Field(None, description="Initial bid price for the item")
        quantity: int = Field(None, description="Quantity of the item")
        item_image: str = Field(None, description="Image URL of the item")
        item_id: str = Field(None, description="Unique ID of the item")
        brand_id: str = Field(None, description="Brand ID of the item")
        fynd_order_id: str = Field(None, description="Order ID from Fynd")
        article_id: str = Field(None, description="Article ID of the item")
        shipment_id: str = Field(None, description="Shipment ID of the item")
        external_order_id: str = Field(None, description="External Order ID of the item")
        external_shipment_id: str = Field(None, description="External Shipment ID of the item")
        delivery_details: dict = Field(None, description="Delivery details of the item")

    import uuid

    @app.post("/{company}/register/bid")
    async def create_a_bid(company: int, BidRequest: BidRequest): # add validation for same bid for same article
        logger.info(socket.gethostname())
        logger.info(f"Creating bid for company {company} with request: {BidRequest}")
        bid = mongo_client.get_collection("bid")
        print(BidRequest.dict())
        BidRequest = BidRequest.dict()
        c = mongo_client.get_collection("company")
        cres = c.find_one({"company_id": company})
        if not cres:
            return {"message": "Company not found", "success": False}
        name = cres["name"]
        BidRequest["bid_id"] = str(uuid.uuid4())
        BidRequest["company_name"] = name
        # BidRequest["applied_bids"] = []
        BidRequest["status"] = "active" # enum
        BidRequest["ordering_company_id"] = company

        res = bid.insert_one(
            BidRequest
        )
        return {"message": "Bid created successfully", "bid_id": str(BidRequest["bid_id"]), "success": True}

    class AddBid(BaseModel):
        amount: float = Field(..., description="Amount for the bid")
        # bid_id: str = Field(..., description="bid id")

    @app.post("/{company}/bid/{bid_id}")
    async def add_bid(company: int, bid_id: str, request: AddBid): # add validation for duplicate biding
        import traceback
        try:
            bid = mongo_client.get_collection("bid")
            res = bid.find_one({"bid_id": bid_id})
            c = mongo_client.get_collection("company")
            cd = c.find_one({"company_id": company})
            if not c.find_one({"company_id": company}):
                return {"message": "Company not found"}
            name = cd["name"]

            if not res:
                return {"message": "Bid not found"}
            if request.amount < res["initial_bid_price"]:
                return {"message": "Bid amount is less than initial bid price"}
            if res["status"] != "active":
                return {"message": "Bid is not active"}
            if res["ordering_company_id"] == company:
                return {"message": "You can't bid on your own bid"}

            applied_bids = mongo_client.get_collection("applied_bids")
            if applied_bids.find_one({"bid_id": bid_id, "company_id": company}):
                return {"message": "Bid is already placed by you cant update it."} # current limitation
            applied_bids.insert_one(
                {"bid_id": res["bid_id"], "company_id": company, "amount": request.amount, "status": "active", "company_name": name}
            ) # ideally it should be in a separate collection, and race condition should be handled.

        except Exception as e:
            print(traceback.format_exc())
            print(e)
        return {"message": "Bid added successfully"}

    @app.post("/{company}/bid/{bid_id}/winner")
    async def propose_winning_company(company: int, bid_id: str, winner_company_id: int):
        bid = mongo_client.get_collection("bid")
        res = bid.find_one({"bid_id": bid_id})
        if not res:
            return {"message": "Bid not found"}
        if res["ordering_company_id"] != company:
            return {"message": "You can't declare winner for this bid"}
        if res.get("winner_company_id"):
            return {"message": "Winner is already declared"}
        if res["status"] != "active":
            return {"message": "Bid is inactive"}
        applied_bids = mongo_client.get_collection("applied_bids")
        winner = applied_bids.find_one({"bid_id": bid_id, "status": "active", "company_id": winner_company_id})
        if not winner:
            return {"message": "Winner not found"}

        company = mongo_client.get_collection("company")
        company.update_one({"company_id": winner_company_id}, {"$set": {
            "total_wins": company.find_one({"company_id": winner_company_id}).get("total_wins", 0) + 1
        }})
        bid.update_one({"bid_id": bid_id}, {"$set": {"winner_company_id": winner_company_id, "status": "completed",
        "ordering_company_name": res["company_name"],
        "winnning_company_name": winner["company_name"],
                                                     }})
        ledger = mongo_client.get_collection("ledger")
        ledger_id = str(uuid.uuid4())
        ledger.insert_one(
            {
                "item_id": res["item_id"],
                "bid_id": bid_id,
                "ordering_company_id": res["ordering_company_id"],
                "ordering_company_name": res["company_name"],
                "winner_company_id": winner_company_id,
                "winnning_company_name": winner["company_name"],
                "amount": winner["amount"],
                "status": "active",
                "ledger_id": ledger_id,
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now()
            }
        )
        return {"message": "Winner declared successfully"}

    @app.get("/{company_id}/ledger")
    async def get_ledger(company_id: int,  page: int=1, limit: int=10, filter: str = 'all'): # filter = all, to_pay, to_be_get_paid, paid
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
                query["ordering_company_id"] = company_id
                query["status"] = "completed"
        if page < 1:
            skip = 0
        else:
            skip = (page - 1) * limit
        print(query, "ofnmmfn")
        res = list(ledger.find(query).skip(skip).limit(limit))
        for r in res:
            del r["_id"]

        return {
            "total": ledger.count_documents(query),
            "page": page,
            "limit": limit,
            "ledger": res
        }

    @app.post("/{company}/ledger/{ledger_id}")
    async def payout_ledger(company: int, ledger_id: str):
        ledger = mongo_client.get_collection("ledger")
        res = ledger.find_one({"ledger_id": ledger_id})
        if company != res.get("ordering_company_id"):
            return {"message": "You can't payout for this ledger"}
        if res["status"] != "active":
            return {"message": "Ledger is already completed"}
        ledger.update_one({"ledger_id": ledger_id}, {"$set": {"status": "completed", "updated_at": datetime.datetime.now()}})
        return {"message": "Payout done successfully"}

    @app.post("/{company}/bid/{bid_id}/transfer") # pending. need to implement
    async def transfer_bid_amount(bid_id: str, company_id: int, amount: float):
        bid = mongo_client.get_collection("bid")
        res = bid.find_one({"bid_id": bid_id})
        if not res:
            return {"message": "Bid not found"}
        if res["ordering_company_id"] != company_id:
            return {"message": "You can't transfer amount for this bid"}
        if res["status"] != "completed":
            return {"message": "Bid is not completed yet"}
        applied_bids = mongo_client.get_collection("applied_bids")

    @app.post("/{company}/bid/{bid_id}/cancel")
    async def cancel_bid(company: int, bid_id: str):
        bid = mongo_client.get_collection("bid")
        res = bid.find_one({"bid_id": bid_id})
        if not res:
            return {"message": "Bid not found"}
        if res["ordering_company_id"] != company:
            return {"message": "You can't cancel this bid"}
        if res["status"] != "active":
            return {"message": "Bid is already inactive"}
        bid.update_one({"bid_id": bid_id}, {"$set": {"status": "inactive"}})
        logger.info(socket.gethostname())
        return {"message": "Bid cancelled successfully"}

    class RegisterCompany(BaseModel):
        name: str = Field(..., description="Name of the company")
        mobile_number: str = Field(..., description="Mobile number of the company")
        tennet: str = Field("FYND", description="Tennet of the company")

    @app.post("/register/{company_id}")
    async def register_company(company_id: int, request: RegisterCompany):
        try:
            company = mongo_client.get_collection("company")
            print(request.dict(), "onfonfonf")
            res = company.find_one({"company_id": company_id})
            if res:
                return {"message": "Company already registered", "success": False}
            print(company.insert_one(
                {
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

    @app.post("/register/{company_id}/phone")
    async def update_phone_number(company_id: int, mobile_number: str):
        company = mongo_client.get_collection("company")
        print(company.update_one({"company_id": company_id}, {"$set": {
            "mobile_number": mobile_number,
            "updated_at": datetime.datetime.now()
        }}))
        return {"message": "Company registered", "success": True}

    class BankDetails(BaseModel):
        account_number: str = Field(..., description="account number")
        ifsc: str = Field(..., description="ifsc code")
        bank_name: str = Field(..., description="bank name")
        vpa: str = Field(..., description="vpa")

    @app.post("/register/{company_id}/banking")
    async def add_banking_details(company_id: int, BankDetails: BankDetails):
        company = mongo_client.get_collection("company")
        print(company.update_one({"company_id": company_id}, {"$set": {
            **BankDetails.dict(),
            "updated_at": datetime.datetime.now()
        }}))
        return True

    @app.get("/healthz")
    async def healthz():
        logger.info(f"health check done, {socket.gethostname()}")
        return {"ping": f"health check done {socket.gethostname()}"}

    @app.get("/metrics")
    async def metrics():
        logger.info("metrics endpoint called")

    return app