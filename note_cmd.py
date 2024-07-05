import argparse
import cmd
import time
import os
import shlex
from dotenv import set_key
from pprint import pprint
from btc_wallet import BTCWallet
from config import WALLET_MNEMONIC, coins
from n_types import ISendToAddress
from mint import mint_token
from deploy import deploy_token
from publish import publish_smart_contract
from address import map_address_to_script_hash


class CommandLineWallet(cmd.Cmd):
    prompt = '> '
    intro = "Welcome to the Command Line Wallet. Type help or ? to list commands.\n"
    mnemonic = WALLET_MNEMONIC

    def __init__(self):
        super().__init__()
        self.wallets = {}
        self.current_wallet = None
        self.init_wallets()

    def init_wallets(self):
        print("Initializing wallets...")
        for coin in coins:
            if coin.symbol == "BTC":
                if coin.network == "livenet":
                    self.wallets['BTClivenet'] = BTCWallet(self.mnemonic, coin)
                    if self.wallets['BTClivenet'].mnemonic != self.mnemonic:
                        self.mnemonic = self.wallets['BTClivenet'].mnemonic
                    if len(coins) == 1:
                        self.current_wallet = self.wallets['BTClivenet']
                else:
                    self.wallets['BTCtestnet'] = BTCWallet(self.mnemonic, coin)
                    if self.wallets['BTCtestnet'].mnemonic != self.mnemonic:
                        self.mnemonic = self.wallets['BTCtestnet'].mnemonic
        self.set_prompt()

    def set_prompt(self):
        if self.current_wallet:
            self.prompt = f"{self.current_wallet.config.network} " \
                          f"{self.current_wallet.account_index}> "
        else:
            self.prompt = 'Enter use testnet/use livenet to select a wallet> '

    def do_use(self, args):
        """use [network] - select a wallet"""
        parser = argparse.ArgumentParser(prog='use', description='Select a wallet')
        parser.add_argument('network', type=str, help='BTC testnet or BTC livenet')
        try:
            parsed_args = parser.parse_args(shlex.split(args))
            network = 'BTC' + parsed_args.network
            self.current_wallet = self.wallets[network]
            if self.current_wallet:
                print(f'Using {network} wallet')
                self.set_prompt()
            else:
                print(f'Wallet for {network} not found')
        except Exception as e:
            print(e)                    
        except SystemExit:
            pass

    def do_switch(self, args):
        """switch [index] - switch account of wallet"""
        parser = argparse.ArgumentParser(prog='switch', description='Switch account of wallet')
        parser.add_argument('index', type=int, help='Account index to switch to')
        try:
            parsed_args = parser.parse_args(shlex.split(args))
            if not self.current_wallet:
                print("No wallet selected")
                return
            result = self.current_wallet.switch_account(parsed_args.index)
            result.dump()
            self.set_prompt()
        except Exception as e:
            print(e)            
        except SystemExit:
            pass

    def do_balance(self, args):
        """balance - get wallet BTC balance"""
        if not self.current_wallet:
            print("No wallet selected")
            return
        result = self.current_wallet.get_balance()
        pprint(result)

    def do_send(self, args):
        """send [address] [amount] - send BTC to address, amount in satoshis"""
        parser = argparse.ArgumentParser(prog='send', description='Send BTC')
        parser.add_argument('address', type=str, help='Receiving address')
        parser.add_argument('amount', type=int, help='Amount in satoshis')
        try:
            parsed_args = parser.parse_args(shlex.split(args))
            if not self.current_wallet:
                print("No wallet selected")
                return
            result = self.current_wallet.send([ISendToAddress(address=parsed_args.address,
                                                              amount=parsed_args.amount)])
            pprint(result)
        except Exception as e:
            print(e)
        except SystemExit:
            pass

    def do_sendtoken(self, args):
        """sendtoken [address] [tick] [amount] - send token to address, 
        amount in minimum unit of token"""

        parser = argparse.ArgumentParser(prog='sendtoken', description='Send token')
        parser.add_argument('address', type=str, help='Receiving address')
        parser.add_argument('tick', type=str, help='Token tick')
        parser.add_argument('amount', type=float, help='Amount in minimum unit of token')
        try:
            parsed_args = parser.parse_args(shlex.split(args))
            if not self.current_wallet:
                print("No wallet selected")
                return
            result = self.current_wallet.send_token(parsed_args.address,
                                                    parsed_args.tick, parsed_args.amount)
            pprint(result)
        except Exception as e:
            print(e)
        except SystemExit:
            pass

    def do_utxos(self, args):
        """utxos - get utxos"""
        if not self.current_wallet:
            print("No wallet selected")
            return
        result = self.current_wallet.show_utxos()
        pprint(result)

    def do_tokenutxos(self, args):
        """tokenutxos [tick] - get token utxos"""
        parser = argparse.ArgumentParser(prog='tokenutxos', 
                                         description='Get utxos of specified tick')
        parser.add_argument('tick', type=str, help='Token tick')
        try:
            parsed_args = parser.parse_args(shlex.split(args))
            if not self.current_wallet:
                print("No wallet selected")
                return
            result = self.current_wallet.get_token_utxos(parsed_args.tick, None)
            pprint(result)
        except Exception as e:
            print(e)
        except SystemExit:
            pass

    def do_info(self, args):
        """info - get wallet info"""
        if not self.current_wallet:
            print("No wallet selected")
            return
        result = self.current_wallet.info()
        pprint(result)

    def do_tokenlist(self, args):
        """tokenlist [--address address] - get token list and balance"""
        parser = argparse.ArgumentParser(prog='tokeninfo', description='Get token info')
        parser.add_argument('--address', type=str, help='Token address, if not specified then show tokenlist of current account')
        try:
            parsed_args = parser.parse_args(shlex.split(args))
            if not self.current_wallet:
                print("No wallet selected")
                return
            if parsed_args.address is None:
                result = self.current_wallet.token_list()
            else:
                network = 'testnet' if self.current_wallet.config.network == 'testnet' else 'mainnet'
                script_hash = map_address_to_script_hash(parsed_args.address, network)
                result = self.current_wallet.urchain.token_list(script_hash['scriptHash'])
            pprint(result)
        except Exception as e:
            print(e)
        except SystemExit:
            pass

    def do_tokeninfo(self, args):
        """tokeninfo [tick] - get token info"""
        parser = argparse.ArgumentParser(prog='tokeninfo', description='Get token info')
        parser.add_argument('tick', type=str, help='Token tick')
        try:
            parsed_args = parser.parse_args(shlex.split(args))
            if not self.current_wallet:
                print("No wallet selected")
                return
            result = self.current_wallet.token_info(parsed_args.tick)
            pprint(result)
        except Exception as e:
            print(e)
        except SystemExit:
            pass

    def do_mint(self, args):
        """mint [tick] [--amount amount_per_mint] [--loop loop_mint] [--bitwork bitwork] [--stop stop_on_fail] - mint token"""
        parser = argparse.ArgumentParser(prog='mint', description='Mint token')

        parser.add_argument('tick', type=str, help='Token tick')
        parser.add_argument('--amount', type=float, default=0, help='Amount in one unit of token, float value')
        parser.add_argument('--loop', type=int, default=1, help='Number of successful minting, default=1')
        parser.add_argument('--bitwork', type=str, default='20', help='Bitwork, default=20')
        parser.add_argument('--stop', type=bool, default=False, help='Stop loop on fail, default=False')

        try:
            parsed_args = parser.parse_args(shlex.split(args))
            print(parsed_args)
            if not self.current_wallet:
                print("No wallet selected")
                return
            n = 0
            while n < parsed_args.loop:
                print(f"Minting {parsed_args.tick} {n+1}/{parsed_args.loop}...")
                try:
                    result = mint_token(self.current_wallet, 
                                        parsed_args.tick,
                                        parsed_args.amount,
                                        parsed_args.bitwork)
                    print(result)
                    if result['success']:
                        n += 1
                    elif parsed_args.stop:
                        break
                    else:
                        time.sleep(15)
                except Exception as e:
                    print(e)
                    time.sleep(15)
        except SystemExit:
            pass

    def do_deploy(self, args):
        """deploy [tick] [max] [lim] [dec] [--bitwork bitwork] [--sch sch] [ --start start_height] [--desc description] [--logo logo_url] [--web web_url] - deploy token"""
        parser = argparse.ArgumentParser(prog='deploy', description='Deploy token')
        parser.add_argument('tick', type=str, help='Token tick name')
        parser.add_argument('max', type=int, help='Max supply')
        parser.add_argument('lim', type=int, help='Limit per mint')
        parser.add_argument('dec', type=int, help='Decimals')
        parser.add_argument('--bitwork', type=str, default='20', help='Bitwork')
        parser.add_argument('--sch', type=str, help='Schema')
        parser.add_argument('--start', type=int, help='Start block height')
        parser.add_argument('--desc', type=str, help='Description of token')
        parser.add_argument('--logo', type=str, help='Logo of token')
        parser.add_argument('--web', type=str, help='Website of token')

        try:
            parsed_args = parser.parse_args(shlex.split(args))
            print(parsed_args)
            if not self.current_wallet:
                print("No wallet selected")
                return
            try:
                result = deploy_token(self.current_wallet, parsed_args.tick,
                                    parsed_args.max, parsed_args.lim, parsed_args.dec,
                                    parsed_args.bitwork, parsed_args.sch, parsed_args.start,
                                    parsed_args.desc, parsed_args.logo, parsed_args.web)
                pprint(result)
            except Exception as e:
                print(e)
        except SystemExit:
            pass

    def do_publish(self, args):
        """publish [json_path] - publish smart contract"""
        parser = argparse.ArgumentParser(prog='publish', description='Publish smart contract')
        parser.add_argument('json_path', type=str, help='Path of smart contract file (Json format)')
        try:
            parsed_args = parser.parse_args(shlex.split(args))
            print(parsed_args)
            if not self.current_wallet:
                print("No wallet selected")
                return
            try:
                result = publish_smart_contract(self.current_wallet, parsed_args.json_path)
                pprint(result)
            except Exception as e:
                print(e)
        except SystemExit:
            pass

    def do_exit(self, args):
        """exit the wallet"""
        print("Exiting wallet")
        if self.mnemonic != WALLET_MNEMONIC:
            print('Saving to .env file...')
            env_file_path = '.env'
            if not os.path.exists(env_file_path):
                with open(env_file_path, 'w', encoding='utf-8') as env_file:
                    env_file.write('')
            set_key(env_file_path, 'WALLET_MNEMONIC', self.mnemonic)

        return True

    def default(self, line):
        print(f"Unknown command: {line}")

if __name__ == '__main__':
    CommandLineWallet().cmdloop()
