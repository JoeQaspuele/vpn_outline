import requests
import json
from urllib3.exceptions import InsecureRequestWarning

from helpers.aliases import AccessUrl, KeyId, ServerId
from helpers.classes import OutlineKey
from helpers.exceptions import KeyCreationError, KeyRenamingError, InvalidServerIdError
from settings import servers

# Отключение предупреждений SSL
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_new_key(key_name: str | None, server_id: ServerId) -> OutlineKey:
    if servers.get(server_id) is None:
        raise InvalidServerIdError

    api_response = _create_new_key(server_id)
    key_id = api_response['id']
    access_url = api_response['accessUrl']

    if key_name is None:
        key_name = "key_id:" + key_id

    _rename_key(key_id, key_name, server_id)
    _set_access_key_data_limit(key_id, 50 * 1024 * 1024 * 1024, server_id)  # Установка лимита в 50ГБ

    key = OutlineKey(kid=key_id, name=key_name, access_url=access_url)
    return key

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
            return OutlineKey(kid=key["id"], name=key["name"], access_url=key["accessUrl"])
    raise KeyError(f"Key with ID '{key_id}' not found.")

def check_api_status() -> dict:
    api_status_codes = {}
    for server_id, server in servers.items():
        url = server.api_url + '/access-keys'
        r = requests.get(url, verify=False)
        api_status_codes[server_id] = str(r.status_code)
    return api_status_codes

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
    data = {"limitInBytes": limit_in_bytes}
    r = requests.put(limit_url, headers=headers, json=data, verify=False)
    r.raise_for_status()

if __name__ == "__main__":
    print(check_api_status())
