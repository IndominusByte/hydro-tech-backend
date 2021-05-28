from fastapi import APIRouter, Depends
from controllers.ChatController import ChatFetch
from dependencies.ChatDependant import get_all_query_chat
from schemas.chats.ChatSchema import ChatPaginate

router = APIRouter()

@router.get('/all-chats',response_model=ChatPaginate)
async def get_all_chats(query_string: get_all_query_chat = Depends()):
    return await ChatFetch.get_all_chats_paginate(**query_string)
