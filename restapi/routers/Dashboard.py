from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.exceptions import WebSocketRequestValidationError

router = APIRouter()

@router.websocket('/ws')
async def websocket(
    websocket: WebSocket,
    csrf_token: str = Query(None),
    token: str = Query(None),
    authorize: AuthJWT = Depends()
):
    dashboard = websocket.app.state.dashboard
    redis_conn = websocket.app.state.redis
    try:
        await dashboard.connect(websocket,authorize,csrf_token=csrf_token,token=token)
        while True:
            msg_data = await websocket.receive()
            if text := msg_data.get('text'):
                await dashboard.broadcast(text, websocket, redis_conn)
            if stream := msg_data.get('bytes'):
                await dashboard.streaming(stream, websocket)
    except (WebSocketDisconnect, WebSocketRequestValidationError, RuntimeError):
        await dashboard.disconnect(websocket,'websocket')
    except AuthJWTException:
        await dashboard.disconnect(websocket,'authenticate')

@router.websocket('/ws-chat')
async def websocket_chat(
    websocket: WebSocket,
    csrf_token: str = Query(None),
    authorize: AuthJWT = Depends()
):
    chat = websocket.app.state.chat
    try:
        await chat.connect(websocket,authorize,csrf_token=csrf_token)
        while True:
            msg_data = await websocket.receive()
            if text := msg_data.get('text'):
                await chat.broadcast(text, websocket)
    except (WebSocketDisconnect, WebSocketRequestValidationError, RuntimeError):
        await chat.disconnect(websocket,'websocket')
    except AuthJWTException:
        await chat.disconnect(websocket,'authenticate')
