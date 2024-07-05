from typing import List
from btclib.psbt.psbt import Psbt, PsbtIn, PsbtOut, extract_tx
from btclib.tx.tx import TxOut, Tx, TxIn
from btclib.tx.out_point import OutPoint
from btclib.script import ScriptPubKey, witness

from bitcoinutils.keys import PrivateKey

from btc_psbt import sign_psbt_input, add_psbt_pay_utxos
from btc_notes import generate_p2tr_commit_note_info

from config import MIN_SATOSHIS
from constants import MAX_SEQUENCE
from n_types import *


def create_p2tr_commit_note_psbt(
        private_key,
        note_payload: NotePayload,
        note_utxo: IUtxo,
        pay_utxos: List[IUtxo],
        to,
        change: str,
        network: str,
        fee_rate: int,
        fee: int = 1000
        ):

    pubkey = private_key.get_public_key().to_hex()
    p2note = generate_p2tr_commit_note_info(note_payload, pubkey, network)

    tap_leaf_script = {
        p2note['noteP2TR']['witness']: (
            p2note['noteRedeem']['output'],
            p2note['noteRedeem']['redeemVersion']
        )
    }

    total_input = 0
    psbt_in = []
    tx_in = []
    # Add note UTXOs to PSBT
    script = p2note['noteP2TR']['output'].hex()
    tx_in.append(
            TxIn(prev_out=OutPoint(tx_id=note_utxo.tx_id, vout=note_utxo.output_index),
                sequence=MAX_SEQUENCE
            ))
    psbt_in.append(PsbtIn(
            witness_utxo=TxOut(value=note_utxo.satoshis, script_pub_key=ScriptPubKey(script)),
            taproot_leaf_scripts=tap_leaf_script,
            ))
    total_input += note_utxo.satoshis

    # Add payment UTXOs to PSBT
    total_input += add_psbt_pay_utxos(private_key, psbt_in, tx_in, pay_utxos, network)

    psbt_out = []
    tx_out = []
    # Add outputs
    total_output = 0

    psbt_out.append(PsbtOut())
    tx_out.append(TxOut(to.amount, ScriptPubKey.from_address(to.address)))
    total_output += to.amount

    value = total_input - total_output - fee

    if value < 0:
        raise ValueError("NoFund")
    if value > MIN_SATOSHIS:
        psbt_out.append(PsbtOut())
        tx_out.append(TxOut(value, ScriptPubKey.from_address(change)))

    if note_payload.locktime is None:
        note_payload.locktime = 0

    psbt = Psbt(tx=Tx(version=2, lock_time=note_payload.locktime, vin=tx_in, vout=tx_out),
                inputs=psbt_in, outputs=psbt_out, hd_key_paths={}, version=0)

    # Sign inputs
    sign_psbt_input(private_key, psbt, 0)

    for i in range(1, len(psbt.inputs)):
        pay_utxo = pay_utxos[i - 1]
        if pay_utxo.private_key_wif is not None:
            privkey = PrivateKey(pay_utxo.private_key_wif)
        else:
            privkey = private_key
        sign_psbt_input(privkey, psbt, i)

    script_solution = [
        list(psbt.inputs[0].taproot_script_spend_signatures.values())[0]
    ]
    script_solution.append(p2note['noteRedeem']['output'])
    script_solution.append(p2note['noteP2TR']['witness'])

    # Finalize PSBT
    psbt.inputs[0].final_script_witness = witness.Witness(script_solution)
    psbt.inputs[0].taproot_script_spend_signatures = {}
    psbt.inputs[0].taproot_leaf_scripts = {}
    psbt.inputs[0].partial_sigs = {}
    psbt.inputs[0].sig_hash_type = None
    psbt.inputs[0].redeem_script = b""
    psbt.inputs[0].witness_script = b""
    psbt.inputs[0].hd_key_paths = {}

    for i in range(1, len(psbt.inputs)):
        if psbt.inputs[i].partial_sigs != {}:
            psbt.inputs[i].final_script_witness = witness.Witness([
                list(psbt.inputs[i].partial_sigs.values())[0],
                list(psbt.inputs[i].partial_sigs.keys())[0]])
        elif psbt.inputs[i].taproot_leaf_scripts != {}:
            psbt.inputs[i].final_script_witness = witness.Witness([
                list(psbt.inputs[i].taproot_script_spend_signatures.values())[0], 
                list(psbt.inputs[i].taproot_leaf_scripts.values())[0][0], 
                list(psbt.inputs[i].taproot_leaf_scripts.keys())[0]])

        psbt.inputs[i].partial_sigs = {}
        psbt.inputs[i].sig_hash_type = None
        psbt.inputs[i].redeem_script = b""
        psbt.inputs[i].witness_script = b""
        psbt.inputs[i].hd_key_paths = {}

        psbt.inputs[i].taproot_script_spend_signatures = {}
        psbt.inputs[i].taproot_leaf_scripts = {}

    return extract_tx(psbt)
