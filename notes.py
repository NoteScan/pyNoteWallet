import hashlib
import base64

from bitcointx.core import x
from bitcointx.core.script import OP_CHECKSIG, OP_2DROP, OP_FALSE, OP_CHECKSIGADD, OP_EQUAL, CScript
from ecdsa import SigningKey, VerifyingKey, SECP256k1

from constants import NOTE_PROTOCOL_ENVELOPE_ID


def build_note_script(x_only_pubkey):
    """
    Builds a NOTE script using the given x_only_pubkey.

    Parameters:
    - x_only_pubkey: The x-only public key to be included in the NOTE script.

    Returns:
    - script: The constructed NOTE script.

    """
    note_hex = NOTE_PROTOCOL_ENVELOPE_ID.encode().hex()
    script = CScript([x(note_hex),
                      OP_2DROP,
                      OP_2DROP,
                      OP_2DROP,
                      x(x_only_pubkey),
                      OP_CHECKSIG],
                    name='note_script')
    return script

def build_commit_note_script(payload, x_only_pubkey):
    """
    Builds a NOTE script based on the given payload and public key.

    Args:
        payload: The payload data for the NOTE script.
        x_only_pubkey: The public key used for the NOTE script.

    Returns:
        The NOTE script as a CScript object.
    """
    script = CScript([x(payload.data0) if payload.data0 else OP_FALSE,
                      x(payload.data1) if payload.data1 else OP_FALSE,
                      x(payload.data2) if payload.data2 else OP_FALSE,
                      x(payload.data3) if payload.data3 else OP_FALSE,
                      x(payload.data4) if payload.data4 else OP_FALSE,
                      x(NOTE_PROTOCOL_ENVELOPE_ID.encode('utf-8').hex()),
                      OP_2DROP,
                      OP_2DROP,
                      OP_2DROP,
                      x(x_only_pubkey),
                      OP_CHECKSIG],
                name='commit_note_script')
    return script

def build_note_muliti_sig_script(pubkeys, n):
    """
    Builds a multi-signature script for NOTE.

    Args:
        pubkeys (list): A list of public keys.
        n (int): The number of signatures required.

    Returns:
        CScript: The multi-signature script.

    Raises:
        AssertionError: If n is greater than the length of pubkeys or if pubkeys is empty.
    """
    assert n <= len(pubkeys), "n should be less than pubkeys.length"
    assert len(pubkeys) > 0, "pubkeys should not be empty"
    script_asm = [x(NOTE_PROTOCOL_ENVELOPE_ID.encode('utf-8').hex()),
                  OP_2DROP,
                  OP_2DROP,
                  OP_2DROP,
                  x(pubkeys[0].hex()),
                  OP_CHECKSIG]
    for pubkey in pubkeys[1:]:
        script_asm.append(x(pubkey.hex()))
        script_asm.append(OP_CHECKSIGADD)
    script_asm.append(n)
    script_asm.append(OP_EQUAL)
    return CScript(script_asm)

def sha256ripemd160(content):
    return hashlib.new('ripemd160', hashlib.sha256(content).digest()).digest()

def hash256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).hexdigest()

def sign_content(content, private_key):
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    signature = sk.sign(content)
    return base64.b64encode(signature).decode('utf-8')

def check_content_sig(content, signature, public_key):
    vk = VerifyingKey.from_string(public_key, curve=SECP256k1)
    return vk.verify(base64.b64decode(signature), content)
