import requests
import json
from urllib3.exceptions import InsecureRequestWarning
from typing import Optional

from helpers.aliases import AccessUrl, KeyId, ServerId
from helpers.classes import OutlineKey
from helpers.exceptions import KeyCreationError, KeyRenamingError, InvalidServerIdError
from settings import servers

# Отключение предупреждений SSL
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_new_key(key_name: Optional[str], server_id: ServerId, data_limit_gb: int = 50) -> OutlineKey:
    """
    Создает новый ключ с лимитом трафика (по умолчанию 50 ГБ).

    :param key_name: Имя ключа (если None, будет сгенерировано автоматически)
    :param server_id: ID сервера Outline
    :param data_limit_gb: Лимит трафика в гигабайтах
    :return: Объект OutlineKey
    """
    if servers.get(server_id) is None:
        raise InvalidServerIdError

    # Создаем ключ
    api_response = _create_new_key(server_id)
    key_id = api_response['id']
    access_url = api_response['accessUrl']

    # Устанавливаем имя (если не передано - генерируем)
    if key_name is None:
        key_name = f"key_{key_id[:8]}"

    _rename_key(key_id, key_name, server_id)

    # Устанавливаем лимит трафика
    if data_limit_gb > 0:  # Если 0 - безлимитный ключ
        _set_access_key_data_limit(key_id, data_limit_gb * 1024**3, server_id)

    return OutlineKey(kid=key_id, name=key_name, access_url=access_url)

def get_key(key_name: str, server_id: ServerId) -> OutlineKey:
    if servers.get(server_id) is None:
        raise InvalidServerIdError

    request_url = servers[server_id].api_url + '/access-keys'
    r = requests.get(request_url, verify=False)
    r.raise_for_status()

    keys = _parse_response(r)["accessKeys"]
    for key in keys:
        if key["name"] == key_name:
            return OutlineKey(kid=key["id"], name=key["name"], access_url=key["accessUrl"])
    raise KeyError(f"Key with name '{key_name}' not found.")

def get_key_by_id(key_id: str, server_id: ServerId) -> OutlineKey:
    if servers.get(server_id) is None:
        raise InvalidServerIdError

    request_url = servers[server_id].api_url + '/access-keys'
    r = requests.get(request_url, verify=False)
    r.raise_for_status()

    keys = _parse_response(r)["accessKeys"]
    for key in keys:
        if key["id"] == key_id:
            # ✅ Добавим лимит
            limit = None
            if "dataLimit" in key and "bytes" in key["dataLimit"]:
                limit = key["dataLimit"]["bytes"]

            # ✅ Добавим used
            metrics = _get_metrics(server_id)
            used = None
            if metrics and key_id in metrics:
                used = metrics[key_id]

            return OutlineKey(
                kid=key["id"],
                name=key["name"],
                access_url=key["accessUrl"],
                limit=limit,
                used=used
            )

    raise KeyError(f"Key with ID '{key_id}' not found.")

def check_api_status() -> dict:
    api_status_codes = {}
    for server_id, server in servers.items():
        url = server.api_url + '/access-keys'
        r = requests.get(url, verify=False)
        api_status_codes[server_id] = str(r.status_code)
    return api_status_codes

def _set_access_key_data_limit(key_id: KeyId, limit_in_bytes: int, server_id: ServerId) -> None:
    """
    Устанавливает лимит трафика для ключа.

    :param key_id: ID ключа
    :param limit_in_bytes: Лимит в байтах
    :param server_id: ID сервера
    """
    limit_url = servers[server_id].api_url + f'/access-keys/{key_id}/data-limit'
    headers = {"Content-Type": "application/json"}
    data = {"limit": {"bytes": limit_in_bytes}}  # Важно: Outline ожидает {"bytes": число}
    r = requests.put(limit_url, headers=headers, json=data, verify=False)
    r.raise_for_status()

def _create_new_key(server_id: ServerId) -> dict:
    request_url = servers[server_id].api_url + '/access-keys'
    r = requests.post(request_url, verify=False)

    if r.status_code != 201:
        raise KeyCreationError

    return _parse_response(r)

def _parse_response(response: requests.models.Response) -> dict:
    return json.loads(response.text)

def _rename_key(key_id: KeyId, key_name: str | None, server_id: ServerId) -> None:
    rename_url = servers[server_id].api_url + f'/access-keys/{key_id}/name'
    r = requests.put(rename_url, data={'name': key_name}, verify=False)
    if r.status_code != 204:
        raise KeyRenamingError

def _set_access_key_data_limit(key_id: KeyId, limit_in_bytes: int, server_id: ServerId) -> None:
    limit_url = servers[server_id].api_url + f'/access-keys/{key_id}/data-limit'
    headers = {"Content-Type": "application/json"}
    data = {"limit": {"bytes": limit_in_bytes}}  # Важно: именно такой формат!

    # Добавляем логирование перед запросом
    print(f"[DEBUG] Устанавливаю лимит для ключа {key_id}: {data}")

    try:
        r = requests.put(limit_url, headers=headers, json=data, verify=False)

        # Логируем ответ API
        print(f"[DEBUG] Ответ API. Статус: {r.status_code}, Текст: {r.text}")

        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Ошибка при установке лимита: {str(e)}")
        raise  # Пробрасываем исключение дальше

def _get_metrics(server_id: ServerId) -> dict[str, int]:
    url = servers[server_id].api_url + '/metrics/transfer'
    r = requests.get(url, verify=False)
    r.raise_for_status()
    data = r.json()
    return data.get("bytesTransferredByUserId", {})

def get_traffic_for_key(key_id: KeyId, server_id: ServerId) -> int:
    """Возвращает трафик в байтах для указанного ключа."""
    metrics = _get_metrics(server_id)
    return metrics.get(key_id, 0)

if __name__ == "__main__":
    print(check_api_status())
