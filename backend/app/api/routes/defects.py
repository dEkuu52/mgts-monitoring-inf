from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_auth
from app.core.responses import ok
from app.schemas.common import Envelope
from app.schemas.defect import DefectCreate, DefectRead, DefectUpdate
from app.services import defect_service

router = APIRouter(
    prefix="/defects",
    tags=["Дефекты"],
    dependencies=[Depends(require_auth)],
)


@router.get("", response_model=Envelope[list[DefectRead]])
async def list_defects(session: SessionDep):
    return ok(await defect_service.list_defects(session))


@router.get("/{defect_id}", response_model=Envelope[DefectRead])
async def get_defect(defect_id: int, session: SessionDep):
    return ok(await defect_service.get_defect(session, defect_id))


@router.post("", response_model=Envelope[DefectRead], status_code=status.HTTP_201_CREATED)
async def create_defect(payload: DefectCreate, session: SessionDep):
    return ok(await defect_service.create_defect(session, payload))


@router.put("/{defect_id}", response_model=Envelope[DefectRead])
async def update_defect(defect_id: int, payload: DefectUpdate, session: SessionDep):
    return ok(await defect_service.update_defect(session, defect_id, payload))


@router.delete("/{defect_id}", response_model=Envelope[bool])
async def delete_defect(defect_id: int, session: SessionDep):
    await defect_service.delete_defect(session, defect_id)
    return ok(True)
