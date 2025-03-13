import asyncio
import logging
import ssl
from json.decoder import JSONDecodeError
from typing import (Any,
                    Dict,
                    List,
                    Union)
from urllib.parse import urljoin
from uuid import (UUID,
                  uuid4)

import certifi
from aiohttp import (ClientSession,
                     ClientTimeout,
                     TCPConnector)
from aiohttp.client_exceptions import (ClientConnectorError,
                                       ContentTypeError)

from .exceptions import (ClientConnectorUfanetIntercomAPIError,
                         TimeoutUfanetIntercomAPIError,
                         UnauthorizedUfanetIntercomAPIError,
                         UnknownUfanetIntercomAPIError)
from .models import (History,
                     HistoryData,
                     Intercom,
                     Token)


class UfanetIntercomAPI:
    def __init__(self, contract: str, password: str, timeout: int = 30, level: logging = logging.INFO):
        self._contract = contract
        self._password = password
        self._token: Union[str, None] = None
        self._base_url: str = 'https://dom.ufanet.ru/'
        self._logger: logging = logging.getLogger('UfanetIntercomAPI')
        self._logger.setLevel(level)

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.session: ClientSession = ClientSession(connector=TCPConnector(ssl=ssl_context),
                                                    timeout=ClientTimeout(total=timeout))

    async def _send_request(self, url: str, method: str = 'GET', params: Dict[str, Any] = None,
                            json: Dict[str, Any] = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:

        while True:
            headers = {'Authorization': f'JWT {self._token}'}
            request_id = uuid4().hex
            self._logger.info('Request=%s method=%s url=%s params=%s json=%s',
                              request_id, method, url, params, json)
            try:
                async with self.session.request(method, url, params=params, json=json, headers=headers) as response:
                    if response.status == 401:
                        raise UnauthorizedUfanetIntercomAPIError
                    json_response = await response.json() if 199 < response.status < 500 else None
                    if response.status in (200,):
                        self._logger.info('Response=%s json_response=%s', request_id, json_response)
                        return json_response
                    self._logger.error('Response=%s unsuccessful request json_response=%s status=%s reason=%s',
                                       request_id, json_response, response.status, response.reason)
                    raise UnknownUfanetIntercomAPIError(json_response)

            except (JSONDecodeError, ContentTypeError) as e:
                self._logger.error('Response=%s unsuccessful request status=%s reason=%s error=%s',
                                   request_id, response.status, response.reason, e)
                raise UnknownUfanetIntercomAPIError(f'Unknown error: {response.status} {response.reason}')

            except asyncio.exceptions.TimeoutError:
                self._logger.error('Response=%s TimeoutUfanetIntercomAPIError', request_id)
                raise TimeoutUfanetIntercomAPIError('Timeout error')

            except ClientConnectorError:
                self._logger.error('Response=%s ClientConnectorUfanetIntercomAPIError', request_id)
                raise ClientConnectorUfanetIntercomAPIError('Client connector error')

            except UnauthorizedUfanetIntercomAPIError:
                self._logger.error('Response=%s UnauthorizedUfanetIntercomAPIError, trying get jwt', request_id)
                await self._prepare_token()
                continue

    async def _prepare_token(self):
        if self._token is None:
            await self._set_token()
        else:
            try:
                await self.token_verify()
            except UnauthorizedUfanetIntercomAPIError:
                await self._set_token()

    async def _set_token(self):
        url = urljoin(self._base_url, 'api/v1/auth/auth_by_contract/')
        json = {'contract': self._contract, 'password': self._password}
        response = await self._send_request(url=url, method='POST', json=json)
        self._token = Token(**response['token']).refresh

    async def token_verify(self):
        url = urljoin(self._base_url, 'api-token-verify/')
        json = {'token': self._token}
        await self._send_request(url=url, method='POST', json=json)

    async def get_intercoms(self) -> List[Intercom]:
        url = urljoin(self._base_url, 'api/v0/skud/shared/')
        response = await self._send_request(url=url)
        return [Intercom(**i) for i in response]

    async def open_intercom(self, intercom_id: int) -> bool:
        url = urljoin(self._base_url, f'api/v0/skud/shared/{intercom_id}/open/')
        response = await self._send_request(url=url)
        return response['result']

    async def get_call_history(self, page: int = 1, page_size: int = 25) -> History:
        url = urljoin(self._base_url, 'api/v1/skuds/call-history/')
        params = {'page': page, 'page_size': page_size}
        response = await self._send_request(url=url, params=params)
        return History(**response)

    async def get_call_history_links(self, uuid: Union[UUID, str]) -> HistoryData:
        url = urljoin(self._base_url, 'api/v1/cctv/history/')
        json = {'uuid': str(uuid)}
        response = await self._send_request(url=url, method='POST', json=json)
        return HistoryData(**response)

    async def close(self):
        await self.session.close()
