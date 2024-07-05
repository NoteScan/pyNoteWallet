import sys
from notes import hash256
from utils import string_to_hexstring

MAX_LOCKTIME = 1000000

def mint_token(wallet, tick, amount, bitwork='20'):
    note_note = None
    pay_notes = None
    fee_rate = None
    result = None
    locktime = 0  # increase locktime to change TX

    token_info = wallet.token_info(tick)
    if not token_info:
        return {
            'success': False,
            'error': "Token not found",
        }

    dec = int(token_info['dec'])
    amount = int(amount * 10 ** dec)

    lim = int(token_info['lim'])

    if amount > lim:
        return {
            'success': False,
            'error': "Amount exceeds limit",
        }

    if amount == 0:
        amount = lim
    mint_data = {
        'p': "n20",
        'op': "mint",
        'tick': tick,
        'amt': amount,
    }

    bitwork = string_to_hexstring(bitwork)

    payload = wallet.build_n20_payload(mint_data)
    to_address = wallet.current_account.token_address.address

    while locktime < MAX_LOCKTIME:
        if locktime % 1000 == 0:
            sys.stdout.write(str(locktime) + '\r')
            sys.stdout.flush()
        setattr(payload, "locktime", locktime)
        try:
            tx = wallet.build_n20_payload_transaction(
                payload,
                to_address,
                note_note,
                pay_notes,
                fee_rate)
        except Exception as error:
            return {
                'success': False,
                'error': str(error),
            }
        tx_hash256 = hash256(tx.tx_hex)
        if tx_hash256.startswith(bitwork):
            try:
                result = wallet.broadcast_transaction(tx)
            except Exception as error:
                result = wallet.broadcast_transaction(tx)
            locktime = 0
            note_note = None
            pay_notes = None
            fee_rate = None
            return result
        else:
            note_note = tx.note_utxo
            pay_notes = tx.pay_utxos
            fee_rate = tx.fee_rate
            locktime += 1

    return {
        'success': False,
        'error': "Failed to mint NotePow token",
    }
