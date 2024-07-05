import json

def publish_smart_contract(wallet, contract_path):
    with open(contract_path) as f:
        pow_json = json.load(f)

    pow_json.pop('file', None)
    pow_json.pop('sourceMapFile', None)
    payload = wallet.build_n20_payload(pow_json, True)

    to_address = wallet.current_account.main_address.address

    tx = wallet.build_commit_payload_transaction(payload, to_address)
    return wallet.broadcast_transaction(tx)
