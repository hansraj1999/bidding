import logging
import traceback
from fastapi import APIRouter, HTTPException, Header


logger = logging.getLogger(__name__)
router = APIRouter(tags=["short-url"], prefix="/v1")


@router.post("/shorten", response_model=ShortenUrlResponse)
async def shorten_url_endpoint(
    request: ShortenTheURLRequestBody, headers: str = Header(...)
):
    try:
        print(request)
        return {"short_url": short_url}

    except UnAuthorized as e:
        logger.exception(e)
        raise HTTPException(
            status_code=401, detail={"message": e.message, "details": e.details}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "message": "Validation Error",
                "details": e.errors(include_url=False, include_input=False),
            },
        )
    except Exception as e:
        traceback.print_exc()
        logger.exception(str(e))
        raise HTTPException(status_code=400, detail={"message": str(e), "details": []})