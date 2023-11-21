### Rubetek Smart Socket API wrapper
Для модели RE-3305<br>С другими моделями не проверялось, но, вероятно, будет работать

#### Перед началом работы
Необходимо отловить запросы из приложения Rubetek и достать оттуда `refresh_token`, `house_id` и `device_id`. Я использовал Android и [HTTP Toolkit](https://httptoolkit.com/). Отлавливать запросы нужно в только что установленном или предварительно разлогиненном приложении.
<br>![refresh_token](https://raw.githubusercontent.com/JakeBV/rubetek_smart_socket_api/master/images/01.jpg)
<br>![house_id](https://raw.githubusercontent.com/JakeBV/rubetek_smart_socket_api/master/images/02.jpg)
<br>![device_id](https://raw.githubusercontent.com/JakeBV/rubetek_smart_socket_api/master/images/03.jpg)
