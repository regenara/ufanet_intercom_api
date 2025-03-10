# Ufanet Intercom API

### Описание  
Обёртка для API, предназначенная для управления домофонной системой провайдера **Уфанет**.

### Description  
A wrapper for the **Ufanet** intercom system API.

## Установка / Installation
```bash
pip install ufanet_intercom_api
```
## Использование / Usage
```python
import asyncio
from ufanet_intercom_api import UfanetIntercomAPI

CONTRACT = 'your_contract'
PASSWORD = 'your_password'

async def main():
    ufanet_api = UfanetIntercomAPI(contract=CONTRACT, password=PASSWORD)

    # Получение списка домофонов / Fetching available intercoms
    intercoms = await ufanet_api.get_intercoms()
    print('Available intercoms:', intercoms)

    # Открытие всех доступных домофонов / Unlocking all available intercoms
    for i in intercoms:
        await ufanet_api.open_intercom(intercom_id=i.id)

    # Получение истории вызовов / Retrieving call history
    call_history = await ufanet_api.get_call_history()
    for call in call_history.results:
        print(f'Call UUID: {call.uuid}, Date: {call.called_at}')

    # Получение ссылок на записи вызовов / Fetching call recording links
    if call_history.results:
        links = await ufanet_api.get_call_history_links(uuid=call_history.results[0].uuid)
        print('Call history links:', links)

asyncio.run(main())

```