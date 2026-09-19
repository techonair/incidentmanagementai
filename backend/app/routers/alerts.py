from arq import create_pool
from fastapi import APIRouter, Depends

from ..auth import require_operator
from ..config import arq_redis_settings
from ..db import serialize
from ..schemas import AlertIn
from ..services.incidents import link_or_create_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("")
async def post_alert(payload: AlertIn, user: dict = Depends(require_operator)):
    incident, created = await link_or_create_alert(payload.model_dump(), user["_id"])
    try:
        pool = await create_pool(arq_redis_settings())
        await pool.enqueue_job("correlate_alert", str(incident["_id"]))
        await pool.aclose()
    except Exception:
        pass
    return {"created_incident": created, "incident": serialize(incident)}
