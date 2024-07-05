import requests
import json
from n_types import IUtxo, ITokenUtxo, AddressType

class Urchain:
    def __init__(self, host, api_key="1234567890"):
        self._http_client = requests.Session()
        self._http_client.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        self._base_url = host

    def _get(self, command, params=None):
        params = params or {}
        try:
            response = self._http_client.get(f'{self._base_url}/{command}', params=params)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            raise
        except Exception as err:
            print(f'Other error occurred: {err}')
            raise

    def _post(self, command, data=None):
        data = data or {}
        try:
            response = self._http_client.post(f'{self._base_url}/{command}', data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            raise
        except Exception as err:
            print(f'Other error occurred: {err}')
            raise

    def health(self):
        return self._get("health")

    def balance(self, script_hash):
        return self._post("balance", {"scriptHash": script_hash})

    def utxos(self, script_hashs, _satoshis=None):
        data = {"scriptHashs": script_hashs}
        if _satoshis is not None:
            data["satoshis"] = _satoshis
        utxos_data = self._post("utxos", data)
        result = []
        for utxo in utxos_data:
            if 'privateKeyWif' not in utxo:
                utxo['privateKeyWif'] = None
            result.append(IUtxo(
                            tx_id=utxo['txId'],
                            output_index=utxo['outputIndex'],
                            script_hash=utxo['scriptHash'],
                            script=utxo['script'],
                            satoshis=utxo['satoshis'],
                            private_key_wif=utxo['privateKeyWif'],
                            type=AddressType(utxo['type'])
                        ))
        return result

    def tokenutxos(self, script_hashs, tick, amount=None):
        data = {"scriptHashs": script_hashs, "tick": tick}
        if amount is not None:
            data["amount"] = amount
        utxos_data = self._post("token-utxos", data)
        result = []
        for utxo in utxos_data:
            result.append(ITokenUtxo(
                            tx_id=utxo['txId'],
                            output_index=utxo['outputIndex'],
                            satoshis=utxo['satoshis'],
                            amount=utxo['amount'],
                            type=AddressType.P2TR_NOTE
                        ))
        return result

    def broadcast(self, raw_hex):
        return self._post("broadcast", {"rawHex": raw_hex})

    def best_block(self):
        return self._post("best-header")

    def token_info(self, tick):
        return self._post("token-info", {"tick": tick})
    
    def token_list(self, script_hash):
        return self._post("token-list", {"scriptHash": script_hash})
    
    def all_tokens(self):
        return self._post("all-n20-tokens")
