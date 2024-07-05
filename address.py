from hashlib import sha256

from bitcoinutils.setup import setup
from bitcoinutils.keys import P2trAddress


def map_address_to_script_hash(address_str, network):
    """
    Maps an address to its corresponding script hash.

    Args:
        address_str (str): The address string to be mapped.
        network (str, optional): The network to use ('mainnet'/'testnet').

    Returns:
        dict: A dictionary containing the script hex and script hash.

    Raises:
        ValueError: If the address is not a NOTE address.
    """

    setup(network)

    try:
        address = P2trAddress(address_str)
    except ValueError as exc:
        raise ValueError("Not a NOTE address.") from exc

    return {
        'scriptHex': address.to_script_pub_key().to_hex(),
        'scriptHash': sha256(address.to_script_pub_key().to_bytes()).digest()[::-1].hex()
    }
