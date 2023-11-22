import asyncio
import logging
import ssl
from typing import Any
from urllib.parse import urljoin
from uuid import uuid4

import certifi
import ujson
from aiohttp import (ClientSession,
                     ClientTimeout,
                     TCPConnector)
from aiohttp.client_exceptions import ClientConnectorError


class UfanetIntercomAPIError(Exception):
    """"""


class UnauthorizedUfanetIntercomAPIError(UfanetIntercomAPIError):
    """"""


class TimeoutUfanetIntercomAPIError(UfanetIntercomAPIError):
    """"""


class UnknownUfanetIntercomAPIError(UfanetIntercomAPIError):
    """"""


class UfanetIntercomAPI:
    def __init__(self, contract: str, password: str):
        self._contract = contract
        self._password = password
        self._token: str | None = None
        self._base_url: str = 'https://dom.ufanet.ru/'
        self._logger: logging = logging.getLogger('UfanetIntercomAPI')

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.session: ClientSession = ClientSession(connector=TCPConnector(ssl=ssl_context),
                                                    timeout=ClientTimeout(total=60),
                                                    json_serialize=ujson.dumps)

    async def _send_request(self, url: str, method: str = 'GET',
                            json: dict[str, Any] = None) -> dict[str, Any] | list[dict[str, Any]] | None:

        while True:
            headers = {'Authorization': f'JWT {self._token}'}
            request_id = uuid4().hex
            self._logger.info('Request=%s url=%s json=%s', request_id, url, json)
            try:
                async with self.session.request(method, url, json=json, headers=headers) as response:
                    if response.status == 401:
                        raise UnauthorizedUfanetIntercomAPIError
                    json_response = await response.json() if 199 < response.status < 500 else None
                    if response.status in (200,):
                        self._logger.info('Response=%s json=%s', request_id, json_response)
                        return json_response
                    self._logger.error('Response=%s UnknownUfanetIntercomAPIError json=%s',
                                       request_id, json_response)
                    raise UnknownUfanetIntercomAPIError(json_response)

            except asyncio.exceptions.TimeoutError:
                self._logger.error('Response=%s TimeoutUfanetIntercomAPIError', request_id)
                raise TimeoutUfanetIntercomAPIError

            except ClientConnectorError:
                self._logger.error('Response=%s UnknownUfanetIntercomAPIError', request_id)
                raise UnknownUfanetIntercomAPIError

            except UnauthorizedUfanetIntercomAPIError:
                self._logger.error('Response=%s UnauthorizedUfanetIntercomAPIError, trying get jwt', request_id)
                await self._prepare_token()
                continue

    async def _prepare_token(self):
        if self._token is None:
            await self._set_token()
        else:
            try:
                await self._token_verify()
            except UnauthorizedUfanetIntercomAPIError:
                await self._set_token()

    async def _set_token(self):
        url = urljoin(self._base_url, 'api/v1/auth/auth_by_contract/')
        json = {'contract': self._contract, 'password': self._password}
        response = await self._send_request(url=url, method='POST', json=json)
        self._token = response['token']['refresh']

    async def _token_verify(self):
        url = urljoin(self._base_url, 'api-token-verify/')
        json = {'token': self._token}
        await self._send_request(url=url, method='POST', json=json)

    async def get_intercoms(self) -> list[int]:
        url = urljoin(self._base_url, 'api/v0/skud/shared/')
        response = await self._send_request(url=url)
        return [intercom['id'] for intercom in response]

    async def open_intercom(self, intercom_id: int) -> bool:
        url = urljoin(self._base_url, f'api/v0/skud/shared/{intercom_id}/open/')
        response = await self._send_request(url=url)
        return response['result']
