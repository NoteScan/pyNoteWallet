from utils import string_to_hexstring


def deploy_token(wallet,
                 tick: str,
                 max_supply: int,
                 lim: int,
                 dec: int,
                 bitwork:str,
                 sch,
                 start,
                 desc,
                 logo,
                 web):

    if start is None:
        start = wallet.best_block()['height']

    deploy_data = {
        'p': "n20",
        'op': "deploy",
        'tick': tick,
        'max': max_supply * 10 ** dec,
        'lim': lim * 10 ** dec,
        'dec': dec,
        'sch': sch,
        'start': start,
        'bitwork': string_to_hexstring(bitwork),
        'desc': desc,
        'logo': logo,
        'web': web,
    }

    if sch is None:
        deploy_data.pop('sch')
    if desc is None:
        deploy_data.pop('desc')
    if logo is None:
        deploy_data.pop('logo')
    if web is None:
        deploy_data.pop('web')

    payload = wallet.build_n20_payload(deploy_data)
    to_address = wallet.current_account.main_address.address

    tx = wallet.build_commit_payload_transaction(payload, to_address)
    return wallet.broadcast_transaction(tx)
