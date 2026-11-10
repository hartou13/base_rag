from typing import List

from fastapi import APIRouter, Depends, File, UploadFile

from src.collections.dto.collection_dto import CollectionDto, CollectionFileDto, CreateCollectionDto
from src.collections.services.collection_service import (
    add_files_service,
    create_collection_service,
    delete_collection_service,
    list_collections_service,
    list_files_service,
)
from src.users.services.user_service import get_current_user

router = APIRouter(
    prefix="/collections",
    tags=["collections"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=CollectionDto)
async def create_collection(data: CreateCollectionDto, current_user: str = Depends(get_current_user)):
    return await create_collection_service(current_user, data)


@router.get("", response_model=List[CollectionDto])
async def list_collections(current_user: str = Depends(get_current_user)):
    return await list_collections_service(current_user)


@router.delete("/{collection_id}")
async def delete_collection(collection_id: str, current_user: str = Depends(get_current_user)):
    return await delete_collection_service(collection_id, current_user)


@router.get("/{collection_id}/files", response_model=List[CollectionFileDto])
async def list_files(collection_id: str, current_user: str = Depends(get_current_user)):
    return await list_files_service(collection_id, current_user)


@router.post("/{collection_id}/files", response_model=List[CollectionFileDto])
async def add_files(collection_id: str, files: List[UploadFile] = File(...),
                    current_user: str = Depends(get_current_user)):
    return await add_files_service(collection_id, current_user, files)
