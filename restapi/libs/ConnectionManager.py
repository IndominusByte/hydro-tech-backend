import logging, json
from fastapi import WebSocket
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import MissingTokenError
from controllers.ChatController import ChatCrud, ChatFetch
from controllers.UserController import UserFetch
from controllers.ReportController import ReportCrud
from controllers.SettingUserController import SettingUserFetch
from controllers.AlertController import AlertCrud, AlertLogic
from schemas.chats.ChatSchema import ChatData
from schemas.reports.ReportSchema import ReportCreate
from schemas.dashboard.DashboardSchema import (
    DashboardSetValueServo,
    DashboardSetValueHydro,
    DashboardHydroData,
)
from pydantic import ValidationError
from user_agents import parse
from typing import List, Union
from config import settings
from redis import Redis

logger = logging.getLogger("uvicorn.info")

class ConnectionManager:
    async def connect(
        self,
        websocket: WebSocket,
        authorize: AuthJWT,
        csrf_token: str = None,
        token: str = None
    ):
        await websocket.accept()

        # user authentication
        if csrf_token:
            authorize.jwt_required("websocket",websocket=websocket,csrf_token=csrf_token)  # check user login
            decode_token = authorize.get_raw_jwt()
        elif token:
            authorize.jwt_required("websocket",token=token)  # check IoT device login
            decode_token = authorize.get_raw_jwt(token)
        else:
            raise MissingTokenError(status_code=1008,message="Missing access token from Query or Path")

        # set state to websocket
        user_agent = websocket.headers.get('user-agent')
        if user_agent != 'arduino-WebSocket-Client':
            websocket.state.type = "user"
            websocket.state.device = str(parse(user_agent))
        else:
            websocket.state.type = "IoT"
            websocket.state.device = user_agent

        websocket.state.ip = websocket.client.host
        websocket.state.user_id = decode_token['sub']

        # remove all duplicate connection
        for connection in self.active_connections:
            if self.check_duplicate_connection(connection,websocket) is True:
                await self.disconnect(connection,'duplicate')

        self.active_connections.append(websocket)

    def check_duplicate_connection(self, connection: WebSocket, websocket: WebSocket) -> bool:
        return connection.state.type == websocket.state.type and \
            connection.state.device == websocket.state.device and \
            connection.state.ip == websocket.state.ip and \
            connection.state.user_id == websocket.state.user_id

    async def send_data(self, kind: str, connection: WebSocket, data: Union[str, bytes]) -> None:
        try:
            if kind == 'text': await connection.send_text(data)
            if kind == 'bytes': await connection.send_bytes(data)
        except RuntimeError:
            await self.disconnect(connection,'invalid_data')

    async def disconnect(self, websocket: WebSocket, msg: str):
        try:
            logger.info(f'{tuple(websocket.client)} - "WebSocket {websocket.url.path}" [disconnect-{msg}]')
            self.active_connections.remove(websocket)
            await websocket.close()
        except ValueError:
            pass

class ConnectionDashboard(ConnectionManager):
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    def set_type_device(self, kind: str, websocket: WebSocket) -> None:
        if kind == "Hydro": websocket.state.type = "IoT:Hydro"
        if kind == "Servo": websocket.state.type = "IoT:Servo"
        if kind == "Camera": websocket.state.type = "IoT:Camera"

    async def broadcast(self, msg_data: str, websocket: WebSocket, redis_conn: Redis) -> None:
        try:
            msg_data = dict(i.split(':') for i in msg_data.rstrip().split(','))
            web_data = ",".join([":".join([key, str(val)]) for key, val in msg_data.items()])
            # set type device IoT when make connection
            self.set_type_device(msg_data['kind'], websocket)

            # save data from hydro to db
            if msg_data['kind'] == 'Hydro':
                try:
                    m = ReportCreate(**msg_data)
                    user_id = int(websocket.state.user_id)
                    setting_user = await SettingUserFetch.filter_by_user_id(user_id)  # get setting user
                    if setting_user is not None and setting_user['planted'] is True:
                        # create alert
                        if m.tank <= 50:
                            msg = f"Water remaining {m.tank}%"
                            if await AlertLogic.check_alert(user_id,'water_tank',msg) is False:
                                await AlertCrud.create_alert(**{
                                    'type': 'water_tank',
                                    'message': msg,
                                    'user_id': user_id
                                })
                        if m.temp <= 15 or m.temp >= 30:
                            msg = "Oh no, your water temperature is abnormal," + \
                                f" water temperature right now {m.temp}°C"
                            if await AlertLogic.check_alert(user_id,'water_temp',msg) is False:
                                await AlertCrud.create_alert(**{
                                    'type': 'water_temp',
                                    'message': msg,
                                    'user_id': user_id

                                })
                        # create report
                        await ReportCrud.create_report(**m.dict(),user_id=user_id)
                except ValidationError:
                    await self.disconnect(websocket,'validation')

            for connection in self.active_connections:
                # send data web to camera for capture image & streaming
                if (
                    msg_data['kind'] in ['live_cam_true', 'live_cam_false'] and
                    connection.state.type == "IoT:Camera" and
                    connection.state.user_id == websocket.state.user_id
                ):
                    await self.send_data('text', connection, web_data)

                # send data web to camera for image calibration
                if (
                    msg_data['kind'] in ['image_cal_true','image_cal_false'] and
                    connection.state.type == "IoT:Camera" and
                    connection.state.user_id == websocket.state.user_id
                ):
                    if msg_data['kind'] == 'image_cal_true':
                        redis_conn.set(f"camera_cal:{connection.state.user_id}","true",settings.image_cal_expires)
                        await self.send_data('text', connection, 'kind:capture_image')

                    if msg_data['kind'] == 'image_cal_false':
                        redis_conn.set(f"camera_cal:{connection.state.user_id}","false",settings.image_cal_expires)

                # send data setting servo to Servo IoT
                if (
                    msg_data['kind'] == 'set_value_servo' and
                    connection.state.type == "IoT:Servo" and
                    connection.state.user_id == websocket.state.user_id
                ):
                    # validation incoming data from user
                    try:
                        DashboardSetValueServo(**msg_data)
                        await self.send_data('text', connection, web_data)
                    except ValidationError:
                        await self.disconnect(websocket,'validation')

                # send data hydro to user
                if (
                    msg_data['kind'] == 'Hydro' and
                    connection.state.type == "user" and
                    connection.state.user_id == websocket.state.user_id
                ):
                    # validation incoming data from user
                    try:
                        DashboardHydroData(**msg_data)
                        await self.send_data('text', connection, web_data)
                    except ValidationError:
                        await self.disconnect(websocket,'validation')

                # send data setting user to Hydro IoT
                if (
                    msg_data['kind'] == 'set_hydro' and
                    connection.state.type == "IoT:Hydro" and
                    connection.state.user_id == websocket.state.user_id
                ):
                    # validation incoming data from user
                    try:
                        DashboardSetValueHydro(**msg_data)
                        await self.send_data('text', connection, web_data)
                    except ValidationError:
                        await self.disconnect(websocket,'validation')

        except ValueError:
            pass

    async def streaming(self, stream: bytes, websocket: WebSocket) -> None:
        # send data streaming to user and not device IoT
        for connection in self.active_connections:
            if (
                connection.state.type == "user" and
                connection.state.user_id == websocket.state.user_id
            ):
                await self.send_data('bytes', connection, stream)

    async def reset_servo(self) -> None:
        for connection in self.active_connections:
            if connection.state.type == "IoT:Servo":
                user_id = int(connection.state.user_id)
                setting_user = await SettingUserFetch.filter_by_user_id(user_id)
                await self.send_data(
                    'text',
                    connection,
                    f"kind:set_value_servo,sh:{setting_user['servo_horizontal']},sv:{setting_user['servo_vertical']}"
                )

    async def capture_image(self) -> None:
        for connection in self.active_connections:
            if connection.state.type == "IoT:Camera":
                await self.send_data('text', connection, 'kind:capture_image')

class ConnectionChat(ConnectionManager):
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(
        self,
        websocket: WebSocket,
        authorize: AuthJWT,
        csrf_token: str = None,
    ):
        await ConnectionManager.connect(self,websocket,authorize,csrf_token=csrf_token)
        await self.list_user_status()

    async def broadcast(self, msg_data: str, websocket: WebSocket) -> None:
        if msg_data != "kind:get_list_user_status":
            # save message to database
            chat_id = await ChatCrud.create_chat(message=msg_data,user_id=int(websocket.state.user_id))
            chat_db = await ChatFetch.filter_by_id(chat_id)
            msg = ChatData(**{index:value for index,value in chat_db.items()}).dict()

            # send message to all user
            [
                await self.send_data('text', connection, json.dumps(msg,default=str))
                for connection in self.active_connections
            ]
        else: await self.list_user_status()

    async def list_user_status(self):
        user_all = await UserFetch.get_user_id()
        user_connection = [int(connection.state.user_id) for connection in self.active_connections]

        online_user = [str(x) for x in user_all if x in user_connection]
        offline_user = [str(x) for x in user_all if x not in user_connection]

        total_online = len(online_user)
        total_offline = len(offline_user)

        msg = {
            'total_online': total_online,
            'total_offline': total_offline,
            'online_user': online_user,
            'offline_user': offline_user
        }

        [
            await self.send_data('text', connection, json.dumps(msg,default=str))
            for connection in self.active_connections
        ]

    async def disconnect(self, websocket: WebSocket, msg: str):
        await ConnectionManager.disconnect(self,websocket,msg)
        await self.list_user_status()
