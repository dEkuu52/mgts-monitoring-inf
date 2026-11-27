from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import Response

from app.api.deps import SessionDep, require_auth
from app.core.responses import ok
from app.schemas.common import Envelope
from app.schemas.infrastructure_object import (
    InfrastructureObjectCreate,
    InfrastructureObjectRead,
    InfrastructureObjectUpdate,
)
from app.services import object_service

router = APIRouter(
    prefix="/infrastructure-objects",
    tags=["Объекты инфраструктуры"],
    dependencies=[Depends(require_auth)],
)


@router.get("", response_model=Envelope[list[InfrastructureObjectRead]])
async def list_objects(session: SessionDep):
    return ok(await object_service.list_objects(session))


@router.get("/{object_id}", response_model=Envelope[InfrastructureObjectRead])
async def get_object(object_id: int, session: SessionDep):
    return ok(await object_service.get_object(session, object_id))


@router.post(
    "",
    response_model=Envelope[InfrastructureObjectRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_object(payload: InfrastructureObjectCreate, session: SessionDep):
    return ok(await object_service.create_object(session, payload))


@router.put("/{object_id}", response_model=Envelope[InfrastructureObjectRead])
async def update_object(
    object_id: int,
    payload: InfrastructureObjectUpdate,
    session: SessionDep,
):
    return ok(await object_service.update_object(session, object_id, payload))


@router.delete("/{object_id}", response_model=Envelope[bool])
async def delete_object(object_id: int, session: SessionDep):
    await object_service.delete_object(session, object_id)
    return ok(True)


@router.post(
    "/{object_id}/photo",
    response_model=Envelope[InfrastructureObjectRead],
    summary="Загрузить или заменить фото объекта",
)
async def upload_object_photo(
    object_id: int,
    session: SessionDep,
    file: UploadFile = File(..., description="JPEG, PNG или WebP, не больше 5 МБ"),
):
    return ok(await object_service.set_object_photo(session, object_id, file))


@router.get(
    "/{object_id}/photo",
    summary="Получить фото объекта",
    responses={200: {"content": {"image/jpeg": {}, "image/png": {}, "image/webp": {}}}},
)
async def get_object_photo(object_id: int, session: SessionDep):
    data, media_type = await object_service.get_object_photo(session, object_id)
    return Response(
        content=data,
        media_type=media_type,
        headers={"Cache-Control": "no-cache"},
    )


@router.delete(
    "/{object_id}/photo",
    response_model=Envelope[InfrastructureObjectRead],
    summary="Удалить фото объекта",
)
async def delete_object_photo(object_id: int, session: SessionDep):
    return ok(await object_service.remove_object_photo(session, object_id))
