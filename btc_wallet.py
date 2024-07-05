from typing import List, Dict
import time
import requests
import msgpack
from bitcoinutils.keys import PrivateKey
from bitcoinutils.setup import setup

from n_types import *
from constants import *
from utils import split_buffer_into_segments, sort_dict_by_key
from btc_address import generate_p2wpkh_address, generate_p2tr_note_address, generate_p2tr_commit_note_address
from btc_coin_tx import create_coin_psbt
from btc_p2tr_note import create_p2tr_note_psbt
from btc_p2tr_commit_note import create_p2tr_commit_note_psbt
from wallet import Wallet
from btc_tweak import tweak_key_pair
from config import MIN_SATOSHIS


class BTCWallet(Wallet):
    def __init__(self, mnemonic, config, lang="ENGLISH"):
        self.mnemonic = mnemonic
        self.config = config
        self.lang = lang
        super().__init__(mnemonic, config, lang)

    def info(self):
        return {
            "coin": "BTC",
            "mnemonic": self.mnemonic,
            "lang": self.lang,
            "network": self.config.network,
            "rootXpriv": self.xpriv,
            "rootXpub": self.xpub,
            "urchain": self.config.urchain,
            "faucets": self.config.faucets if self.config.faucets else None,
            "rootPath": f"m/{self.config.path_r}'/{self.config.path_r_s1}'/{self.config.path_r_s2}'",
            "currentAccount": self.current_account,
        }

    def create_account(self, root, root_path1, root_path2, index, target):
        account = super().create_account(root, root_path1, root_path2, index, target)

        tweaked_key_pair = tweak_key_pair(
                                account.private_key,
                                account.public_key,
                                self.config.network == 'testnet')
        account.tweaked_private_key = tweaked_key_pair[0]
        account.x_only_pubkey = tweaked_key_pair[1]
        network = 'testnet' if self.config.network == 'testnet' else 'mainnet'
        account.main_address = generate_p2wpkh_address(account.public_key, network)
        account.token_address = generate_p2tr_note_address(account.public_key, network)
        return account

    def get_balance(self):
        main_address_balance = self.urchain.balance(self.current_account.main_address.script_hash)
        token_address_balance = self.urchain.balance(self.current_account.token_address.script_hash)

        return {
            "mainAddress": {
                "confirmed": main_address_balance['confirmed'],
                "unconfirmed": main_address_balance['unconfirmed']
            },
            "tokenAddress": {
                "confirmed": token_address_balance['confirmed'],
                "unconfirmed": token_address_balance['unconfirmed']
            }
        }

    def send(self, to_addresses: ISendToAddress):
        utxos = self.fetch_all_account_utxos()
        fee_rate = self.get_fee_per_kb()
        network = 'testnet' if self.config.network == 'testnet' else 'mainnet'

        setup(network)
        private_key = PrivateKey(self.current_account.private_key)
        estimated_psbt = create_coin_psbt(
            private_key,
            utxos,
            to_addresses,
            self.current_account.main_address.address,
            network,
            fee_rate['avgFee'],
            1000
        )

        estimated_size = estimated_psbt.vsize
        real_fee = int((estimated_size * fee_rate['avgFee']) / 1000 + 1)

        final_tx = create_coin_psbt(
            private_key,
            utxos,
            to_addresses,
            self.current_account.main_address.address,
            network,
            fee_rate['avgFee'],
            real_fee
        )

        return self.urchain.broadcast(final_tx.serialize(include_witness=True).hex())

    def send_token(self, to_address: str, tick: str, amt: int) -> Dict[str, Any]:
        token_utxos = self.get_token_utxos(tick, amt)
        missed_token_utxos = self.urchain.tokenutxos([self.current_account.main_address.script_hash], tick)
        missed_balance = sum(int(utxo.amount) for utxo in missed_token_utxos)
        balance = missed_balance + sum(int(utxo.amount) for utxo in token_utxos)

        if balance < amt:
            raise ValueError("Insufficient balance")

        to_addresses = [ISendToAddress(address=to_address, amount=MIN_SATOSHIS)]

        if balance > amt:
            to_addresses.append(
                ISendToAddress(address=self.current_account.token_address.address, amount=MIN_SATOSHIS))
        transfer_data = {
            'p':'n20',
            'op':'transfer',
            'tick':tick,
            'amt':amt,
        }

        pay_utxos = self.fetch_all_account_utxos()

        if missed_token_utxos:
            for utxo in missed_token_utxos:
                utxo.private_key_wif = self.current_account.private_key
                utxo.type = self.current_account.main_address.type
                pay_utxos.append(utxo)

        payload = self.build_n20_payload(transfer_data)
        if payload.locktime is None:
            payload.locktime = 0
        tx = self.build_n20_transaction(payload, to_addresses, token_utxos, pay_utxos)
        result = self.broadcast_transaction(tx)

        return {
            'transferData': transfer_data,
            'result': result,
        }

    def build_n20_transaction(self,
                              payload:NotePayload,
                              to_addresses:ISendToAddress,
                              note_utxos:List[IUtxo],
                              pay_utxos:List[IUtxo]=None,
                              fee_rate=None):
        if pay_utxos is None:
            pay_utxos = self.fetch_all_account_utxos()
        if fee_rate is None:
            fee_rate = self.get_fee_per_kb()['avgFee']

        network = 'testnet' if self.config.network == 'testnet' else 'mainnet'
        setup(network)
        private_key = PrivateKey(self.current_account.private_key)

        estimated_psbt = create_p2tr_note_psbt(
            private_key,
            payload,
            note_utxos,
            pay_utxos,
            to_addresses,
            self.current_account.main_address.address,
            network,
            fee_rate,
            1000
        )
        estimated_size = estimated_psbt.vsize

        real_fee = int((estimated_size * fee_rate) / 1000 + 1)

        final_tx = create_p2tr_note_psbt(
            private_key,
            payload,
            note_utxos,
            pay_utxos,
            to_addresses,
            self.current_account.main_address.address,
            network,
            fee_rate,
            real_fee
        )
        return ITransaction(
            tx_id=final_tx.id,
            tx_hex=final_tx.serialize(include_witness=True),
            note_utxos=note_utxos,
            pay_utxos=pay_utxos,
            fee_rate=fee_rate
        )

    def broadcast_transaction(self, tx):
        return self.urchain.broadcast(tx.tx_hex.hex())


    def build_n20_payload(self, data, use_script_size=False):
        sorted_data = sort_dict_by_key(data)
        encoded_data = msgpack.packb(sorted_data)
        payload = NotePayload("", "", "", "", "")
        buffer = bytearray(encoded_data)

        if len(buffer) <= MAX_STACK_FULL_SIZE:
            data_list = split_buffer_into_segments(buffer, MAX_STANDARD_STACK_ITEM_SIZE)
        elif use_script_size and len(buffer) <= MAX_SCRIPT_FULL_SIZE:
            data_list = split_buffer_into_segments(buffer, MAX_SCRIPT_ELEMENT_SIZE)
        else:
            raise ValueError("Data is too long")

        i = 0
        for item in data_list:
            setattr(payload, f"data{i}", item.hex())
            i += 1
        return payload

    def commit_payload_address(self, payload:NotePayload):
        network = 'testnet' if self.config.network == 'testnet' else 'mainnet'
        address = generate_p2tr_commit_note_address(
            payload,
            self.current_account.public_key,
            network
        )
        return address

    def build_n20_payload_transaction(self,
                                      payload:NotePayload,
                                      to_address:ISendToAddress=None,
                                      note_utxo:IUtxo=None,
                                      pay_utxos:List[IUtxo]=None,
                                      fee_rate=None):
        if note_utxo is None:
            commit_address = self.current_account.token_address
            note_utxos = self.urchain.utxos([commit_address.script_hash])
            if len(note_utxos) == 0:
                result = self.send([ISendToAddress(address=commit_address.address,
                                                   amount=MIN_SATOSHIS)])
                if result['success']:
                    for _ in range(10):
                        note_utxos = self.urchain.utxos([commit_address.script_hash])
                        if len(note_utxos) > 0:
                            break
                        time.sleep(1)
                    else:
                        raise Exception("Cannot get commit note UTXO")
                else:
                    raise Exception(result['error'])
            note_utxo = note_utxos[0]
            note_utxo.type = AddressType.P2TR_NOTE

        if pay_utxos is None:
            pay_utxos = self.fetch_all_account_utxos()
            pay_utxos = [utxo for utxo in pay_utxos if utxo.script_hash != note_utxo.script_hash]

        result = self.build_n20_transaction(
            payload,
            [ISendToAddress(address=to_address, amount=MIN_SATOSHIS)],
            [note_utxo],
            pay_utxos,
            fee_rate
        )
        result.note_utxo = result.note_utxos[0] if result.note_utxos else None
        return result


    def build_commit_payload_transaction(self,
                                         payload:NotePayload,
                                         to_address:ISendToAddress=None,
                                         note_utxo:IUtxo=None,
                                         pay_utxos:List[IUtxo]=None,
                                         fee_rate=None):
        commit_address = self.commit_payload_address(payload)
        if note_utxo is None:
            note_utxos = self.urchain.utxos([commit_address.script_hash])
            if len(note_utxos) == 0:
                result = self.send([ISendToAddress(address=commit_address.address,
                                                   amount=MIN_SATOSHIS)])
                if result['success']:
                    for _ in range(10):
                        note_utxos = self.urchain.utxos([commit_address.script_hash])
                        if len(note_utxos) > 0:
                            break
                        time.sleep(1)
                    else:
                        raise Exception("Cannot get commit note UTXO")
                else:
                    raise Exception(result.error)
            note_utxo = note_utxos[0]
            note_utxo.type = "P2TR-COMMIT-NOTE"

        if to_address is None:
            to_address = self.current_account.token_address.address

        to = ISendToAddress(address=to_address, amount=MIN_SATOSHIS)

        if pay_utxos is None:
            pay_utxos = self.fetch_all_account_utxos()
        if fee_rate is None:
            fee_rate = self.get_fee_per_kb()['avgFee']

        network = 'testnet' if self.config.network == 'testnet' else 'mainnet'
        setup(network)
        private_key = PrivateKey(self.current_account.private_key)

        estimated_psbt = create_p2tr_commit_note_psbt(
            private_key,
            payload,
            note_utxo,
            pay_utxos,
            to,
            self.current_account.main_address.address,
            network,
            fee_rate,
            1000
        )

        estimated_size = estimated_psbt.vsize
        real_fee = int((estimated_size * fee_rate) / 1000 + 1)
        print("Estimated size: ", estimated_size, "Real fee: ", real_fee)
        final_tx = create_p2tr_commit_note_psbt(
            private_key,
            payload,
            note_utxo,
            pay_utxos,
            to,
            self.current_account.main_address.address,
            network,
            fee_rate,
            real_fee
        )

        return ITransaction(
            tx_id=final_tx.id,
            tx_hex=final_tx.serialize(include_witness=True),
            note_utxos=note_utxos,
            pay_utxos=pay_utxos,
            fee_rate=fee_rate
        )

    def token_list(self):
        results = self.urchain.token_list(self.current_account.token_address.script_hash)
        return results


    def get_fee_per_kb(self):
        url = "https://mempool.space"
        if self.config.network == 'testnet':
            url += "/testnet4"
        url += "/api/v1/fees/recommended"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Cannot get fee rate, status code: {response.status_code} url: {url}")        
        fees = response.json()
        return {
            "slowFee": min(fees['hourFee'], fees['halfHourFee']) * 1000,
            "avgFee": max(fees['hourFee'], fees['halfHourFee']) * 1000,
            "fastFee": max(fees['hourFee'], fees['halfHourFee'], fees['fastestFee']) * 1000
        }
