import hashlib
import codecs
import base58
from ecdsa import SECP256k1, SigningKey

def privkey_to_wif(privkey_bytes, network='mainnet'):
    prefix = b'\xef' if network == 'testnet' else b'\x80'
    privkey_full = prefix + privkey_bytes + b'\x01'
    checksum = hashlib.sha256(hashlib.sha256(privkey_full).digest()).digest()[:4]
    return base58.b58encode(privkey_full + checksum).decode()

# Function to negate a private key
def private_negate(privkey_bytes):
    privkey_int = int.from_bytes(privkey_bytes, byteorder='big')
    negated_privkey_int = SECP256k1.order - privkey_int
    negated_privkey_bytes = negated_privkey_int.to_bytes(32, byteorder='big')
    return negated_privkey_bytes

def tagged_hash(tag, data):
    tag_hash = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()

class ECPair:
    def __init__(self, privkey_bytes):
        self.privkey = SigningKey.from_string(privkey_bytes, curve=SECP256k1)

    @classmethod
    def from_private_key(cls, privkey_bytes):
        return cls(privkey_bytes)

    def tweak(self, tweak, negate):
        if negate:
            private_key = private_negate(self.privkey.to_string())
        else:
            private_key = self.privkey.to_string()
        tweak_int = int.from_bytes(tweak, byteorder='big')
        privkey_int = int.from_bytes(private_key, byteorder='big')
        tweaked_privkey_int = (privkey_int + tweak_int) % SECP256k1.order
        tweaked_privkey_bytes = tweaked_privkey_int.to_bytes(32, byteorder='big')
        return ECPair.from_private_key(tweaked_privkey_bytes)

    def to_wif(self, network='mainnet'):
        return privkey_to_wif(self.privkey.to_string(), network)

# Helper function to decode WIF to private key bytes
def wif_to_privkey(wif):
    decoded_wif = base58.b58decode(wif)
    privkey_bytes = decoded_wif[1:-4]  # Remove network byte and checksum
    return privkey_bytes[:-1]  # Remove compression byte

def tweak_key_pair(private_key, public_key, is_test_net:bool):
    private_key_bytes = wif_to_privkey(private_key)
    public_key_bytes = codecs.decode(public_key, 'hex')
    x_only_pubkey = public_key_bytes[1:33]
    negate = public_key_bytes[0] == 3 or (public_key_bytes[0] == 4 and (public_key_bytes[64] & 0x01) == 1)

    tweaked_privkey = ECPair.from_private_key(private_key_bytes).tweak(tagged_hash("TapTweak", x_only_pubkey), negate)
    return [tweaked_privkey.to_wif('testnet' if is_test_net else 'mainnet'), x_only_pubkey.hex()]
