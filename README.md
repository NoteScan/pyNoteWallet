# pyNoteWallet

A simple CLI tool to manage Bitcoin and NOTE crypto assets.
Port from https://github.com/NoteProtocol/NoteWallet

## Installation


```
pip install -r requirements.txt
```

Install libsecp256k1:
https://github.com/bitcoin-core/secp256k1

## Setup
Rename `.env.example` to `.env`, fill your wallet WALLET_MNEMONIC, if you keep empty, the tool will generate a new one and save to `.env`.

## Start
```
python3 note_cmd.py
```

## Choose Network
```
use livenet
```
or
```
use testnet
```

## Show token list and balance
```
tokenlist [--address address]
```

## Publish Smart Contract
```
publish [json_path]
```
Your should compile your smart contract to json file first.

## Deploy Token
```
deploy [tick] [max] [lim] [dec] [--bitwork bitwork] [--sch sch] [ --start start_height] [--desc description] [--logo logo_url] [--web web_url]
```

## Mint Token
```
mint [tick] [--amount amount_per_mint] [--loop loop_mint] [--bitwork bitwork] [--stop stop_on_fail]
```
e.g.
```
mint DID --a 39.0625 --l 10
```

Other commands are same as original version.
