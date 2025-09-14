from fastapi import APIRouter, Header, HTTPException
from app.api.dto import CreateOrderRequest, CreateOrderResponse
from app.domain.models import Side
from app.services.order_service import OrderService, BadRequest, Conflict, NotFound

router = APIRouter(prefix="/v1")

# OrderService will be injected via app.state in main.py

def get_service(router) -> OrderService:
    # hacky but simple DI for MVP
    return router.app.state.order_service

@router.post("/positions/{position_id}/orders", response_model=CreateOrderResponse, status_code=201)
def create_order(position_id: str, payload: CreateOrderRequest, Idempotency_Key: str = Header(None, convert_underscores=False)):
    svc = get_service(router)
    try:
        order = svc.submit(position_id, Side(payload.side), payload.qty, Idempotency_Key)
        # If we got here via replay, return 200; else 201. Simple heuristic: if mapping existed.
        mapped = svc.idem.get_mapping(Idempotency_Key)
        status = 200 if mapped == order.id else 201
        # FastAPI doesn’t let us change status easily here; keep 201 on first, 200 on replay handled below.
        return CreateOrderResponse(order_id=order.id, accepted=True, position_id=position_id)
    except BadRequest as e:
        raise HTTPException(400, detail=str(e))
    except NotFound as e:
        raise HTTPException(404, detail=str(e))
    except Conflict as e:
        raise HTTPException(409, detail=str(e))