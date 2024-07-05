from typing import List

from btclib.psbt.psbt import Psbt, PsbtOut, extract_tx
from btclib.tx.tx import TxOut, Tx
from btclib.script import ScriptPubKey, witness

from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey

from btc_psbt import add_psbt_pay_utxos, sign_psbt_input
from n_types import IUtxo, ISendToAddress, AddressType
from config import MIN_SATOSHIS


def create_coin_psbt(private_key: PrivateKey,
                     utxos: List[IUtxo],
                     to: List[ISendToAddress],
                     change: str,
                     network: str,
                     fee_rate: int,
                     fee: int = 1000):
    """
    Creates a Partially Signed Bitcoin Transaction (PSBT) for minting/sending coins.

    Args:
        private_key (PrivateKey): The private key used for signing the transaction.
        utxos (List[IUtxo]): The list of unspent transaction outputs (UTXOs) to use as inputs.
        to (List[ISendToAddress]): The list of addresses and amounts to send coins to.
        change (str): The address to receive the change (if any).
        network (str): The network to use (e.g., 'mainnet', 'testnet').
        fee_rate (int): The fee rate in satoshis per byte.
        fee (int, optional): The transaction fee in satoshis. Defaults to 1000.

    Returns:
        The transaction in Tx format of btclib.

    Raises:
        Exception: If there are insufficient funds or no change address is provided.
    """
    # Add UTXOs
    tx_out = []
    tx_in = []
    psbt_in = []
    psbt_out = []

    total_input = add_psbt_pay_utxos(private_key, psbt_in, tx_in, utxos, network)

    if len(to) == 1 and to[0].amount == total_input:
        value = int(total_input - fee)
        if value < MIN_SATOSHIS:
            raise Exception("Insufficient fund")
        psbt_out.append(PsbtOut())
        tx_out.append(TxOut(value, ScriptPubKey.from_address(to[0].address)))
    else:
        total_output = 0
        for item in to:
            psbt_out.append(PsbtOut())
            tx_out.append(TxOut(item.amount, ScriptPubKey.from_address(item.address)))
            total_output += item.amount

        value = int(total_input - total_output - fee)
        if value < 0:
            raise Exception("NoFund")
        if value > MIN_SATOSHIS:
            psbt_out.append(PsbtOut())
            tx_out.append(TxOut(value, ScriptPubKey.from_address(change)))


    psbt = Psbt(tx=Tx(version=2, lock_time=0, vin=tx_in, vout=tx_out),
                inputs=psbt_in,
                outputs=psbt_out,
                hd_key_paths={},
                version=0)

    # Sign inputs
    for i in range(len(psbt.inputs)):
        utxo = utxos[i]
        sign_psbt_input(
            PrivateKey.from_wif(utxo.private_key_wif) if utxo.private_key_wif else private_key,
            psbt,
            i)

    for psbt_input in psbt.inputs:
        if psbt_input.partial_sigs != {}:
            psbt_input.final_script_witness = witness.Witness([
                list(psbt_input.partial_sigs.values())[0],
                list(psbt_input.partial_sigs.keys())[0]])
        elif psbt_input.taproot_leaf_scripts != {}:
            psbt_input.final_script_witness = witness.Witness([
                list(psbt_input.taproot_script_spend_signatures.values())[0], 
                list(psbt_input.taproot_leaf_scripts.values())[0][0], 
                list(psbt_input.taproot_leaf_scripts.keys())[0]])
        psbt_input.partial_sigs = {}
        psbt_input.sig_hash_type = None
        psbt_input.redeem_script = b""
        psbt_input.witness_script = b""
        psbt_input.hd_key_paths = {}

        psbt_input.taproot_script_spend_signatures = {}
        psbt_input.taproot_leaf_scripts = {}

    return extract_tx(psbt)
