import os

from aiohttp import web
from aiohttp.web_request import Request

from ufanet_intercom_api import UfanetIntercomAPI


routes = web.RouteTableDef()


@routes.get('/intercoms/open')
async def open_intercoms(_: Request):
    ufanet = UfanetIntercomAPI(contract=os.getenv('CONTRACT'), password=os.getenv('PASSWORD'))
    intercom_ids = await ufanet.get_intercoms()
    [await ufanet.open_intercom(intercom_id) for intercom_id in intercom_ids]
    await ufanet.session.close()
    return web.json_response(data={'success': True})


app = web.Application()
app.add_routes(routes)
web.run_app(app)
