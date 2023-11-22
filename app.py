import logging
import os

from aiohttp import web
from aiohttp.web_request import Request

from ufanet_intercom_api import UfanetIntercomAPI

routes = web.RouteTableDef()

UFANET = []


@routes.get('/intercoms/open')
async def open_intercoms(_: Request):
    intercom_ids = await UFANET[0].get_intercoms()
    [await UFANET[0].open_intercom(intercom_id) for intercom_id in intercom_ids]
    return web.json_response(data={'success': True})


async def on_startup(_):
    UFANET.append(UfanetIntercomAPI(contract=os.getenv('CONTRACT'), password=os.getenv('PASSWORD')))


async def on_shutdown(_):
    await UFANET[0].session.close()


app = web.Application()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(name)s %(message)s', style='%')
app.add_routes(routes)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
web.run_app(app)
