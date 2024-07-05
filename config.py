
"""
This module contains the configuration for the coins.
"""
from dotenv import load_dotenv
import os

MIN_SATOSHIS = 546

load_dotenv()

WALLET_MNEMONIC = os.getenv('WALLET_MNEMONIC', '').strip('"')

URCHAIN_KEY = os.getenv('URCHAIN_KEY', '1234567890').strip('"')

BTC_URCHAIN_HOST = os.getenv('BTC_URCHAIN_HOST', 'https://btc.urchain.com/api/').strip('"')

BTC_URCHAIN_HOST_TESTNET = \
    os.getenv('BTC_URCHAIN_HOST_TESTNET', 'https://btc-testnet4.urchain.com/api/').strip('"')


class CoinConfig:
    """
    Coin configuration class.
    """
    def __init__(self, name, symbol, decimal, path_r, path_r_s1, path_r_s2, base_symbol, network, explorer, faucets,
                  P2SH, P2PKH, P2WSH, P2TR, min_dust_threshold, bip21, urchain):
        self.name = name
        self.symbol = symbol
        self.decimal = decimal
        self.path_r = path_r
        self.path_r_s1 = path_r_s1
        self.path_r_s2 = path_r_s2
        self.base_symbol = base_symbol
        self.network = network
        self.explorer = explorer
        self.faucets = faucets
        self.P2SH = P2SH
        self.P2PKH = P2PKH
        self.P2WSH = P2WSH
        self.P2TR = P2TR
        self.min_dust_threshold = min_dust_threshold
        self.bip21 = bip21
        self.urchain = urchain

coins = [
    CoinConfig(
        name="Bitcoin",
        symbol="BTC",
        decimal=8,
        path_r=44,
        path_r_s1=0,
        path_r_s2=0,
        base_symbol="Satoshi",
        network="livenet",
        explorer=[
            {
                "homepage": "https://explorer.noteprotocol.org/",
                "tx": "https://explorer.noteprotocol.org/transaction?txId=${txId}&blockchain=BTClivenet",
                "address": "https://explorer.noteprotocol.org/address?q=${address}&blockchain=BTClivenet",
                "block": "https://explorer.noteprotocol.org/block?hash=${blockHash}&blockchain=BTClivenet",
                "blockheight": "https://explorer.noteprotocol.org/block?height=${blockHeight}&blockchain=BTClivenet",
            },
            {
              "homepage": "https://mempool.space/",
              "tx": "https://mempool.space/tx/${txId}",
              "address": "https://mempool.space/address/${address}",
              "block": "https://mempool.space/block/${blockHash}",
              "blockheight": "https://mempool.space/block/${blockHeight}",
            },
            {
              "homepage": "https://blockstream.info/",
              "tx": "https://blockstream.info/tx/${txId}",
              "address": "https://blockstream.info/address/${address}",
              "block": "https://blockstream.info/block/${blockHash}",
              "blockheight": "https://blockstream.info/block-height/${blockHeight}",
            },
        ],
        faucets=None,
        P2SH=True,
        P2PKH=True,
        P2WSH=True,
        P2TR=True,
        min_dust_threshold=546,
        bip21="",
        urchain={
            "host": BTC_URCHAIN_HOST,
            "apiKey": URCHAIN_KEY,
        },
    ),
    CoinConfig(
        name="Bitcoin",
        symbol="BTC",
        decimal=8,
        path_r=44,
        path_r_s1=1,
        path_r_s2=0,
        base_symbol="Satoshi",
        network="testnet",
        explorer=[
            {
                "homepage": "https://testnet4.noteprotocol.org/",
                "tx": "https://testnet4.noteprotocol.org/transaction?txId=${txId}&blockchain=BTCtestnet4",
                "address": "https://testnet4.noteprotocol.org/address?q=${address}&blockchain=BTCtestenet",
                "block": "https://testnet4.noteprotocol.org/block?hash=${blockHash}&blockchain=BTCtestnet",
                "blockheight": "https://testnet4.noteprotocol.org/block?height=${blockHeight}&blockchain=BTCtestnet",
            },
            {
              "homepage": "https://mempool.space/testnet4/",
              "tx": "https://mempool.space/testnet4/tx/${txId}",
              "address": "https://mempool.space/testnet4/address/${address}",
              "block": "https://mempool.space/testnet4/block/${blockHash}",
              "blockheight": "https://mempool.space/testnet4/block/${blockHeight}",
            },
        ],
        faucets=[
            "https://testnet4.anyone.eu.org/",
            "https://mempool.space/testnet4/faucet",
          ],
        P2SH=True,
        P2PKH=True,
        P2WSH=True,
        P2TR=True,
        min_dust_threshold=546,
        bip21="",
        urchain={
            "host": BTC_URCHAIN_HOST_TESTNET,
            "apiKey": URCHAIN_KEY,
        },
    ),
]