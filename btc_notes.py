from bitcointx import select_chain_params
from bitcointx.wallet import P2TRBitcoinTestnetAddress, TaprootScriptTree, P2TRBitcoinAddress
from bitcointx.core.key import XOnlyPubKey
from bitcointx.core import x
from bitcointx.core.script import OP_CHECKSIG, CScript
from notes import build_note_script, build_commit_note_script
from utils import to_x_only
from n_types import NotePayload


def generate_p2tr_note_info(pubkey:str, network='mainnet'):
    if network == 'testnet':
        select_chain_params('bitcoin/testnet')
    else:
        select_chain_params('bitcoin')

    x_only_pubkey = to_x_only(bytes.fromhex(pubkey))

    note_script = build_note_script(x_only_pubkey.hex())
    p2pk_script = CScript([x(x_only_pubkey.hex()), OP_CHECKSIG], name='p2pk_script')

    obj_pubkey = XOnlyPubKey(x_only_pubkey)
    root_tree = TaprootScriptTree([note_script, p2pk_script],
                                   leaf_version=192,
                                   internal_pubkey=obj_pubkey)

    if network == 'testnet':
        p2tr = P2TRBitcoinTestnetAddress.from_script_tree(stree=root_tree)
    else:
        p2tr = P2TRBitcoinAddress.from_script_tree(stree=root_tree)

    script_p2tr = {}
    note_p2tr = {}
    p2pk_p2tr = {}

    note_redeem = {
        'output': bytes.fromhex((root_tree.get_script('note_script').hex())),
        'redeemVersion': 192
    }

    p2pk_redeem = {
        'output': bytes.fromhex(root_tree.get_script('p2pk_script').hex()),
        'redeemVersion': 192
    }

    script_p2tr['address'] = p2pk_p2tr['address'] = note_p2tr['address'] = str(p2tr)
    script_p2tr['output'] = note_p2tr['output']= p2pk_p2tr['output'] = bytes.fromhex(p2tr.to_scriptPubKey().hex())
    script_p2tr['redeemVersion'] = note_p2tr['redeemVersion'] = p2pk_p2tr['redeemVersion'] = 192
    script_p2tr['scriptTree'] = note_p2tr['scriptTree'] = p2pk_p2tr['scriptTree'] = [{'output': note_redeem['output']}, {'output': p2pk_redeem['output']}]
    script_p2tr['signature'] = note_p2tr['signature'] = p2pk_p2tr['signature']  = None
    script_p2tr['redeem'] = None
    script_p2tr['witness'] = None

    note_p2tr['redeem'] = note_redeem
    note_p2tr['witness'] = bytes.fromhex(root_tree.get_script_with_control_block('note_script')[-1].hex())

    p2pk_p2tr['redeem'] = p2pk_redeem
    p2pk_p2tr['witness'] = bytes.fromhex(root_tree.get_script_with_control_block('p2pk_script')[-1].hex())

    return {
        'scriptP2TR': script_p2tr,
        'noteP2TR': note_p2tr,
        'p2pkP2TR': p2pk_p2tr,
        'noteRedeem': note_redeem,
        'p2pkRedeem': p2pk_redeem
    }

def generate_p2tr_commit_note_info(payload:NotePayload, pubkey:str, network='mainnet'):
    if network == 'testnet':
        select_chain_params('bitcoin/testnet')
    else:
        select_chain_params('bitcoin')

    x_only_pubkey = to_x_only(bytes.fromhex(pubkey))

    commit_note_script = build_commit_note_script(payload, x_only_pubkey.hex())
    p2pk_script = CScript([x(x_only_pubkey.hex()), OP_CHECKSIG], name='p2pk_script')

    obj_pubkey = XOnlyPubKey(x_only_pubkey)
    root_tree = TaprootScriptTree([commit_note_script, p2pk_script],
                                  leaf_version=192, internal_pubkey=obj_pubkey)

    if network == 'testnet':
        p2tr = P2TRBitcoinTestnetAddress.from_script_tree(stree=root_tree)
    else:
        p2tr = P2TRBitcoinAddress.from_script_tree(stree=root_tree)

    script_p2tr = {}
    note_p2tr = {}
    p2pk_p2tr = {}

    note_redeem = {
        'output': bytes.fromhex((root_tree.get_script('commit_note_script').hex())),
        'redeemVersion': 192
    }

    p2pk_redeem = {
        'output': bytes.fromhex(root_tree.get_script('p2pk_script').hex()),
        'redeemVersion': 192
    }

    script_p2tr['address'] = p2pk_p2tr['address'] = note_p2tr['address'] = str(p2tr)
    script_p2tr['output'] = note_p2tr['output']= p2pk_p2tr['output'] = bytes.fromhex(p2tr.to_scriptPubKey().hex())
    script_p2tr['redeemVersion'] = note_p2tr['redeemVersion'] = p2pk_p2tr['redeemVersion'] = 192
    script_p2tr['scriptTree'] = note_p2tr['scriptTree'] = p2pk_p2tr['scriptTree'] = [{'output': note_redeem['output']}, {'output': p2pk_redeem['output']}]
    script_p2tr['signature'] = note_p2tr['signature'] = p2pk_p2tr['signature']  = None
    script_p2tr['redeem'] = None
    script_p2tr['witness'] = None

    note_p2tr['redeem'] = note_redeem
    note_p2tr['witness'] = bytes.fromhex(root_tree.get_script_with_control_block('commit_note_script')[-1].hex())

    p2pk_p2tr['redeem'] = p2pk_redeem
    p2pk_p2tr['witness'] = bytes.fromhex(root_tree.get_script_with_control_block('p2pk_script')[-1].hex())

    return {'scriptP2TR': script_p2tr,
            'noteP2TR': note_p2tr,
            'p2pkP2TR': p2pk_p2tr,
            'noteRedeem': note_redeem,
            'p2pkRedeem': p2pk_redeem}
