from fastapi import APIRouter, Depends, HTTPException
from backend.handler import mongo_client
import socket
import logging
import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

bid_router = APIRouter()
BID_NOT_FOUND = "BID_NOT_FOUND"

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
    article_details: dict = Field(None, description="Article details of the item")
    item_details: dict = Field(None, description="Item details of the item")
    pdp_link: str = Field(None, description="PDP link of the item")


@bid_router.get("/bids/{bid_id}/applied_bids")
async def get_bids_for_a_bid(bid_id):
    applied_bids = mongo_client.get_collection("applied_bids")
    res = list(applied_bids.find({"bid_id": bid_id}).sort("created_at", -1))
    if not res:
        return {"message": "No applied bids found"}
    for _bid in res:
        del _bid["_id"]
    return res


@bid_router.get("/{company_id}/bids")
async def bids_by_company_id(company_id: int, filter_type: str=None, limit: int = 10, page: int = 0):
    bid = mongo_client.get_collection("bid")
    if page < 1:
        skip = 0
    else:
        skip = (page - 1) * limit
    print("fpfa", filter_type, company_id)
    query = {"ordering_company_id": company_id}
    if filter_type:
        query["status"] =  filter_type
    bids = list(bid.find(query).skip(skip).limit(limit))
    for _bid in bids:
        del _bid["_id"]
    return {
        "total": bid.count_documents(query),
        "page": page,
        "limit": limit,
        "bids": bids
    }


@bid_router.get("/{company_id}/bids/{bid_id}")
async def get_bid_by_bid_id_and_company_id(company_id, bid_id: int):
    logger.info(socket.gethostname())
    logger.info(socket.gethostname())
    bid = mongo_client.get_collection("bid")
    res = bid.find_one({"bid_id": bid_id, "ordering_company_id": company_id})
    if not res:
        return {"message": BID_NOT_FOUND}
    del res["_id"]
    return res


@bid_router.get("/bids")
async def get_gloabl_bids(filter: str=None, limit: int = 10, page: int = 0, exclude_company_id: int = None):
    logger.info(socket.gethostname())
    bid = mongo_client.get_collection("bid")
    if page < 1:
        skip = 0
    else:
        skip = (page - 1) * limit
    print("oonogno", exclude_company_id, type(exclude_company_id))
    query = {}
    if exclude_company_id:
        query = {"ordering_company_id": {"$ne": exclude_company_id}}
    if filter:
        query["status"] = filter 
    print(query, "ofnfonfonf")
    bids = list(bid.find(query).sort({"updated_at": -1}).skip(skip).limit(limit))
    for _bid in bids:
        del _bid["_id"]
    return {
        "total": bid.count_documents(query),
        "page": page,
        "limit": limit,
        "bids": bids
    }

@bid_router.get("/bids/{bid_id}")
async def get_gloabl_bid_by_bid_id(bid_id: str):
    logger.info(socket.gethostname())
    bid = mongo_client.get_collection("bid")
    res = bid.find_one({"bid_id": bid_id})
    if not res:
        return {"message": BID_NOT_FOUND}
    del res["_id"]
    return res

@bid_router.get("/{company_id}/bids/{bid_id}/applied")
async def get_applied_bid_by_bid_id(company_id: int, bid_id: str):
    logger.info(socket.gethostname())
    applied_bid = mongo_client.get_collection("applied_bids")
    res = applied_bid.find_one({"bid_id": bid_id, "company_id": company_id})
    if not res:
        return {}
    del res["_id"]
    return res


@bid_router.post("/{company}/register/bid")
async def create_a_bid(company: int, bid_request: BidRequest): # add validation for same bid for same article
    logger.info(socket.gethostname())
    logger.info(f"Creating bid for company {company} with request: {bid_request}")
    bid = mongo_client.get_collection("bid")
    print(bid_request.dict())
    bid_request = bid_request.dict()
    c = mongo_client.get_collection("company")
    cres = c.find_one({"company_id": company})
    if not cres:
        return {"message": "Company not found", "success": False}
    sh = bid.find_one({"shipment_id": bid_request["shipment_id"], "status": "active"})
    if sh:
        return {"message": "Bid already exists for this shipment", "success": False}
    name = cres["name"]
    bid_request["bid_id"] = str(uuid.uuid4())
    bid_request["company_name"] = name
    bid_request["status"] = "active" # enum
    bid_request["ordering_company_id"] = company
    bid_request["created_at"] = datetime.datetime.now()
    bid_request["updated_at"] = datetime.datetime.now()
    bid.insert_one(
        bid_request
    )
    return {"message": "Bid created successfully", "bid_id": str(bid_request["bid_id"]), "success": True}


class AddBid(BaseModel):
    amount: float = Field(..., description="Amount for the bid")
    pdp_link: str = Field(None, description="PDP link of the item")
    # bid_id: str = Field(..., description="bid id")

@bid_router.post("/{company}/bid/{bid_id}")
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
            return {"message": BID_NOT_FOUND}
        if request.amount < res["initial_bid_price"]:
            return {"message": "Bid amount is less than initial bid price", "success": False}
        if res["status"] != "active":
            return {"message": "Bid is not active", "success": False}
        if res["ordering_company_id"] == company:
            return {"message": "You can't bid on your own bid", "success": False}

        applied_bids = mongo_client.get_collection("applied_bids")
        if applied_bids.find_one({"bid_id": bid_id, "company_id": company}):
            return {"message": "Bid is already placed by you cant update it."} # current limitation
        applied_bids.insert_one(
            {
                "id": str(uuid.uuid4()),
                "is_winner": False,
                "bid_id": res["bid_id"], "company_id": company, 
                "amount": request.amount, "status": "active", "company_name": name,
                "pdp_link": request.pdp_link,
                "created_at": datetime.datetime.now(), "updated_at": datetime.datetime.now()
            }
        ) # ideally it should be in a separate collection, and race condition should be handled.

    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return {"message": "Bid Failed", "success": False}

    return {"message": "Bid added successfully", "success": True}


@bid_router.post("/{company}/bid/{bid_id}/winner")
async def propose_winning_company(company: int, bid_id: str, winner_company_id: int, fynd_order_id: str):
    bid = mongo_client.get_collection("bid")
    res = bid.find_one({"bid_id": bid_id})
    if not res:
        return {"message": BID_NOT_FOUND, "success": False}
    if res["ordering_company_id"] != company:
        return {"message": "You can't declare winner for this bid"}
    if res.get("winner_company_id"):
        return {"message": "Winner is already declared", "success": False}
    if res["status"] != "active":
        return {"message": "Bid is inactive", "success": False}
    applied_bids = mongo_client.get_collection("applied_bids")
    winner = applied_bids.find_one({"bid_id": bid_id, "status": "active", "company_id": winner_company_id})
    if not winner:
        return {"message": "Winner not found", "success": False}
    applied_bids.update_one({"bid_id": bid_id, "company_id": winner_company_id}, {"$set": {"is_winner": True, "updated_at": datetime.datetime.now()}})
    company = mongo_client.get_collection("company")
    company.update_one({"company_id": winner_company_id}, {"$set": {
        "total_wins": company.find_one({"company_id": winner_company_id}).get("total_wins", 0) + 1
    }})
    bid.update_one({"bid_id": bid_id}, {"$set": {
        "winner_company_id": winner_company_id, "status": "completed",
        "ordering_company_name": res["company_name"], "new_fynd_order_id": fynd_order_id,
        "winnning_company_name": winner["company_name"], "winning_bid_amount": winner["amount"]
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
            "updated_at": datetime.datetime.now(),
            "new_fynd_order_id": fynd_order_id
        }
    )
    return {"message": "Winner declared successfully", "success": True}

@bid_router.post("/{company}/bid/{bid_id}/cancel")
async def cancel_bid(company: int, bid_id: str):
    bid = mongo_client.get_collection("bid")
    res = bid.find_one({"bid_id": bid_id})
    if not res:
        return {"message": BID_NOT_FOUND}
    if res["ordering_company_id"] != company:
        return {"message": "You can't cancel this bid"}
    if res["status"] != "active":
        return {"message": "Bid is already inactive"}
    bid.update_one({"bid_id": bid_id}, {"$set": {"status": "inactive"}})
    logger.info(socket.gethostname())
    return {"message": "Bid cancelled successfully"}

