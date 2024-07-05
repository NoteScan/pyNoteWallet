from typing import List
from abc import abstractmethod

import msgpack
import bip32utils
from mnemonic import Mnemonic

from urchain import Urchain
from config import CoinConfig
from n_types import *

class Wallet:
    def __init__(self, mnemonic: str, config: CoinConfig, lang: str = "english"):
        self.config = config
        self.lang = lang
        self.urchain = Urchain(config.urchain['host'], config.urchain['apiKey'])
        self._account_index = 0
        self.current_account = None
        self.account_collection = {}
        self.wallet = None
        self.root_hd_private_key = None
        self.child_hd_key = None

        self.import_mnemonic(mnemonic, lang)

        self.urchain.health()

    @property
    def explorer(self):
        return self.config.explorer[0]

    @property
    def root_path(self):
        return self.config.path

    @property
    def xpriv(self):
        return self.root_hd_private_key.ExtendedKey(private=True, encoded=True)

    @property
    def xpub(self):
        return self.root_hd_private_key.ExtendedKey(private=False, encoded=True)

    @property
    def account_index(self):
        return self._account_index

    def import_mnemonic(self, mnemonic_str: str, lang: str = "english"):
        mnemonic = Mnemonic(lang)
        if mnemonic_str == '':
            print('No mnemonic provided, generating new one...')
            mnemonic_str = mnemonic.generate()

        self.mnemonic = mnemonic_str
        seed = mnemonic.to_seed(mnemonic_str)
        # Create a BIP32 root key (master key) from the seed
        self.root_hd_private_key = bip32utils.BIP32Key.fromEntropy(
            seed,
            testnet= self.config.network == "testnet")
        root_path1 = 0
        if self.config.network == "testnet":
            root_path1 = 1
        self.current_account = self.create_account(44, root_path1, 0, 0, 0)

    def create_account(self,
                       root: int,
                       root_path1: int,
                       root_path2: int,
                       index: int,
                       target: int) -> IWalletAccount:
        ext_path = f'm/{index}/{target}'
        root_hd_key = self.root_hd_private_key.ChildKey(root + bip32utils.BIP32_HARDEN).ChildKey(
            root_path1 + bip32utils.BIP32_HARDEN).ChildKey(root_path2 + bip32utils.BIP32_HARDEN)

        self.child_hd_key = root_hd_key.ChildKey(index).ChildKey(target)

        account = IWalletAccount(target=target,
                                 index=index,
                                 ext_path=ext_path,
                                 xpub=root_hd_key.ExtendedKey(private=False, encoded=True),
                                 private_key=self.child_hd_key.WalletImportFormat(),
                                 public_key=self.child_hd_key.PublicKey().hex())
        self.account_collection[ext_path] = account
        return account

    def switch_account(self, index: int):
        self._account_index = index
        exist_account = self.account_collection.get(f"{self.config.path_r}/0/{index}")
        if exist_account:
            self.current_account = exist_account
        else:
            self.current_account = self.create_account(self.config.path_r,
                                                       self.config.path_r_s1,
                                                       self.config.path_r_s2, 0, index)
        return self.current_account

    def generate_spec_accounts(self, root: int, root_s1:int, root_s2:int, n: int, target: int = 0):
        for i in range(n):
            self.create_account(root, root_s1, root_s2, i, target)
        return list(self.account_collection.keys())

    def generate_accounts(self, n: int, target: int = 0):
        return self.generate_spec_accounts(self.config.path_r,
                                           self.config.path_r_s1,
                                           self.config.path_r_s2,
                                           n,
                                           target)

    @property
    def main_script_hash_list(self):
        return [account.main_address.script_hash for account in self.account_collection.values()]

    @property
    def token_script_hash_list(self):
        return [account.token_address.script_hash for account in self.account_collection.values()]

    @property
    def main_address_list(self):
        return [account.main_address.address for account in self.account_collection.values()]

    @property
    def token_address_list(self):
        return [account.token_address.address for account in self.account_collection.values()]

    def show_utxos(self):
        return self.fetch_all_account_utxos()

    def get_token_utxos(self, tick: str, amount: Optional[int]):
        token_utxos = self.urchain.tokenutxos([self.current_account.token_address.script_hash],
                                              tick,
                                              amount)
        if len(token_utxos) == 0:
            raise Exception("No UTXOs found")
        return token_utxos

    def fetch_all_account_utxos(self, include_unbonded_token_utxos: bool = False) -> List[IUtxo]:
        all_script_hashs = []
        all_accounts = {}
        for account in self.account_collection.values():
            all_script_hashs.append(account.main_address.script_hash)
            all_accounts[account.main_address.script_hash] = account
            if include_unbonded_token_utxos:
                all_script_hashs.append(account.token_address.script_hash)
                all_accounts[account.token_address.script_hash] = account
        all_utxos = self.urchain.utxos(all_script_hashs)
        for utxo in all_utxos:
            account = all_accounts.get(utxo.script_hash)
            if account:
                utxo.private_key_wif = account.private_key
                if utxo.script_hash == account.main_address.script_hash:
                    utxo.type = account.main_address.type
                if utxo.script_hash == account.token_address.script_hash:
                    utxo.type = account.token_address.type
        return all_utxos

    @abstractmethod
    def build_n20_transaction(
        self,
        payload: NotePayload,
        token_addresses: Optional[Union[List[ISendToAddress], List[ISendToScript]]] = None,
        note_utxos: Optional[List[IUtxo]] = None,
        pay_utxos: Optional[List[IUtxo]] = None,
        fee_rate: Optional[float] = None
    ) -> ITransaction:
        pass

    @abstractmethod
    def build_n20_payload_transaction(
        self,
        payload: NotePayload,
        to_address: Optional[str] = None,
        note_utxo: Optional[IUtxo] = None,
        pay_utxos: Optional[List[IUtxo]] = None,
        fee_rate: Optional[float] = None
    ) -> ITransaction:
        pass

    def broadcast_transaction(self, tx: ITransaction) -> IBroadcastResult:
        return self.urchain.broadcast(tx.tx_hex)

    def mint(self, payload: NotePayload, _to_address: Optional[str] = None):
        tx = self.build_n20_transaction(payload)
        return self.broadcast_transaction(tx)

    def build_n20_payload(self, data: Union[str, dict], use_script_size: bool = False):
        encoded_data = msgpack.packb(data, use_bin_type=True)
        buffer = encoded_data.hex()
        payload = NotePayload(
            data0=buffer, data1="", data2="", data3="", data4="",
        )
        return payload

    def best_block(self):
        results = self.urchain.best_block()
        return results

    def token_info(self, tick: str):
        result = self.urchain.token_info(tick)
        return result

    def all_tokens(self):
        results = self.urchain.all_tokens()
        return results
