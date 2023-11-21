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


class TimeoutUfanetIntercomSocketAPIError(UfanetIntercomAPIError):
    """"""


class UnknownUfanetIntercomSocketAPIError(UfanetIntercomAPIError):
    """"""


class UfanetIntercomAPI:
    def __init__(self, contract: str, password: str, log_level: int = logging.INFO):
        self._contract = contract
        self._password = password
        self._token: str | None = None
        self._base_url: str = 'https://dom.ufanet.ru/'
        self._logger: logging = logging.getLogger('UfanetIntercomAPI')
        self._logger.setLevel(log_level)

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.session: ClientSession = ClientSession(connector=TCPConnector(ssl=ssl_context),
                                                    timeout=ClientTimeout(total=60),
                                                    json_serialize=ujson.dumps)

    async def _send_request(self, url: str, method: str = 'GET',
                            json: dict[str, Any] = None) -> dict[str, Any] | list[dict[str, Any]] | None:

        while True:
            headers = {'authorization': f'JWT {self._token}'}
            request_id = uuid4().hex
            self._logger.info('Request=%s url=%s json=%s', request_id, url, json)
            try:
                async with self.session.request(method, url, json=json, headers=headers) as response:
                    if response.status == 401:
                        raise UnauthorizedUfanetIntercomAPIError
                    if response.status in (200,):
                        json_response = await response.json()
                        self._logger.info('Response=%s json=%s', request_id, json_response)
                        return json_response
                    json_response = await response.json() if 199 < response.status < 500 else None
                    self._logger.error('Response=%s UnknownUfanetIntercomSocketAPIError json=%s',
                                       request_id, json_response)
                    raise UnknownUfanetIntercomSocketAPIError(json_response)

            except asyncio.exceptions.TimeoutError:
                self._logger.error('Response=%s TimeoutUfanetIntercomSocketAPIError', request_id)
                raise TimeoutUfanetIntercomSocketAPIError

            except ClientConnectorError:
                self._logger.error('Response=%s UnknownUfanetIntercomSocketAPIError', request_id)
                raise UnknownUfanetIntercomSocketAPIError

            except UnauthorizedUfanetIntercomAPIError:
                self._logger.error('Response=%s UnauthorizedUfanetIntercomAPIError, trying get jwt', request_id)
                await self._prepare()
                continue

    async def _prepare(self):
        if self._token is None:
            await self._set_token()
        else:
            try:
                await self._token_verify(token=self._token)
            except UnauthorizedUfanetIntercomAPIError:
                await self._set_token()

    async def _set_token(self):
        response = await self._get_token()
        self._token = response['token']['refresh']

    async def _get_token(self):
        url = urljoin(self._base_url, 'api/v1/auth/auth_by_contract/')
        json = {'contract': self._contract, 'password': self._password}
        return await self._send_request(url=url, method='POST', json=json)

    async def _token_verify(self, token: str):
        url = urljoin(self._base_url, 'api-token-verify/')
        json = {'token': token}
        await self._send_request(url=url, method='POST', json=json)

    async def get_intercoms(self) -> list[int]:
        url = urljoin(self._base_url, 'api/v0/skud/shared/')
        response = await self._send_request(url=url)
        return [intercom['id'] for intercom in response]

    async def open_intercom(self, intercom_id: int) -> bool:
        url = urljoin(self._base_url, f'api/v0/skud/shared/{intercom_id}/open/')
        response = await self._send_request(url=url)
        return response['result']
