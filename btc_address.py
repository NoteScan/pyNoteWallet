import hashlib
from bitcoinutils.setup import setup
from bitcoinutils.keys import PublicKey, P2wpkhAddress

from btc_notes import generate_p2tr_note_info, generate_p2tr_commit_note_info
from n_types import IAddressObject, AddressType, NotePayload

def generate_p2wpkh_address(pubkey, network):
    """
    Generate a Pay-to-Witness-Public-Key-Hash (P2WPKH) address.

    Args:
      pubkey (str): The public key used to generate the address.
      network (str): The network to generate the address for.

    Returns:
      IAddressObject: An object containing the generated address, 
                      script, script hash, and address type.
    """
    setup(network)
    pubkey_obj = PublicKey(pubkey)
    address_obj = P2wpkhAddress(pubkey_obj.get_segwit_address().to_string())
    script = address_obj.to_script_pub_key().to_hex()
    script_hash = hashlib.sha256(bytes.fromhex(script)).digest()[::-1].hex()
    return IAddressObject(address=address_obj.to_string(),
                          script=script,
                          script_hash=script_hash,
                          type=AddressType.P2WPKH)

def generate_p2tr_note_address(pubkey, network):
    """
    Generates a Pay-to-Taproot (P2TR) NOTE address.

    Args:
      pubkey (str): The public key used to generate the address.
      network (str): The network to generate the address for.

    Returns:
      IAddressObject: An object containing the generated address, 
                      script, script hash, and address type.
    """
    setup(network)
    p2tr_note_info = generate_p2tr_note_info(pubkey, network)
    script = p2tr_note_info['scriptP2TR']['output'].hex()
    script_hash = hashlib.sha256(bytes.fromhex(script)).digest()[::-1].hex()
    return IAddressObject(address=p2tr_note_info['scriptP2TR']['address'],
                          script=script,
                          script_hash=script_hash,
                          type=AddressType.P2TR_NOTE)

def generate_p2tr_commit_note_address(payload, pubkey, network):
    """
    Generates a P2TR NOTE address with payload.

    Args:
      payload (bytes): The payload to be included.
      pubkey (bytes): The public key associated with the address.
      network (str): The network to generate the address for.

    Returns:
      IAddressObject: An object containing the generated address, 
                      script, script hash, and address type.
    """
    setup(network)
    p2tr_commit_note_info = generate_p2tr_commit_note_info(payload, pubkey, network)
    script = p2tr_commit_note_info['scriptP2TR']['output'].hex()
    script_hash = hashlib.sha256(bytes.fromhex(script)).digest()[::-1].hex()
    return IAddressObject(address=p2tr_commit_note_info['scriptP2TR']['address'],
                          script=script,
                          script_hash=script_hash,
                          type=AddressType.P2TR_COMMIT_NOTE)
