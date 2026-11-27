from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_auth
from app.core.responses import ok
from app.schemas.common import Envelope
from app.schemas.status import StatusCreate, StatusRead, StatusUpdate
from app.services import status_service

router = APIRouter(
    prefix="/statuses",
    tags=["Статусы"],
    dependencies=[Depends(require_auth)],
)


@router.get("", response_model=Envelope[list[StatusRead]])
async def list_statuses(session: SessionDep):
    return ok(await status_service.list_statuses(session))


@router.get("/{status_id}", response_model=Envelope[StatusRead])
async def get_status(status_id: int, session: SessionDep):
    return ok(await status_service.get_status(session, status_id))


@router.post("", response_model=Envelope[StatusRead], status_code=status.HTTP_201_CREATED)
async def create_status(payload: StatusCreate, session: SessionDep):
    return ok(await status_service.create_status(session, payload))


@router.put("/{status_id}", response_model=Envelope[StatusRead])
async def update_status(status_id: int, payload: StatusUpdate, session: SessionDep):
    return ok(await status_service.update_status(session, status_id, payload))


@router.delete("/{status_id}", response_model=Envelope[bool])
async def delete_status(status_id: int, session: SessionDep):
    await status_service.delete_status(session, status_id)
    return ok(True)
