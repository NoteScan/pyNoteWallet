from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from pprint import PrettyPrinter

class AddressType(Enum):
    P2PKH = "P2PKH"
    P2PK_NOTE = "P2PK-NOTE"
    P2SH = "P2SH"
    P2SH_NOTE = "P2SH-NOTE"
    P2WPKH = "P2WPKH"
    P2WSH = "P2WSH"
    P2WSH_NOTE = "P2WSH-NOTE"
    P2TR = "P2TR"
    P2TR_NOTE_V1 = "P2TR-NOTE-V1"
    P2TR_NOTE = "P2TR-NOTE"
    P2TR_COMMIT_NOTE = "P2TR-COMMIT-NOTE"

class IDumpable:
    def dump(self, exclude: Optional[List[str]] = None):
        pp = PrettyPrinter(indent=4)
        if exclude:
            pp.pprint({k: v for k, v in asdict(self).items() if k not in exclude})
        else:
            pp.pprint(asdict(self))


@dataclass
class IAddressObject:
    address: Optional[str] = None
    script: Optional[str] = None
    script_hash: str = ""
    type: AddressType = AddressType.P2PKH

@dataclass
class IScriptObject:
    address: Optional[str] = None
    script: Optional[str] = None
    script_hash: str = ""
    type: AddressType = AddressType.P2PKH    

@dataclass
class IWalletAccount(IDumpable):
    target: int
    index: int
    ext_path: str
    xpub: str
    private_key: str
    public_key: str
    tweaked_private_key: Optional[str] = None
    x_only_pubkey: Optional[str] = None
    main_address: Optional[IAddressObject] = None
    token_address: Optional[IAddressObject] = None
    extra: Dict[str, Any] = None  # This field is used to store extra properties

@dataclass
class NotePayload:
    data0: str
    data1: str
    data2: str
    data3: str
    data4: str
    locktime: Optional[int] = None

@dataclass
class IUtxo(IDumpable):
    tx_id: str
    output_index: int
    satoshis: int
    script: str
    script_hash: str
    type: AddressType
    private_key_wif: Optional[str] = None
    tx_hex: Optional[str] = None
    sequence: Optional[int] = None

@dataclass
class ITransaction:
    tx_id: str
    tx_hex: str
    note_utxo: Optional[IUtxo] = None
    note_utxos: Optional[List[IUtxo]] = None
    pay_utxos: Optional[List[IUtxo]] = None
    fee_rate: Optional[float] = None

@dataclass
class IBroadcastResult:
    success: bool
    txId: Optional[str] = None
    error: Optional[Any] = None

@dataclass
class IBalance:
    confirmed: int
    unconfirmed: int
    scriptHash: Optional[str] = None

@dataclass
class ISendToScript:
    script: str
    amount: Union[int, float]

@dataclass
class ISendToAddress:
    address: str
    amount: Union[int, float]

@dataclass
class IFees:
    slowFee: int  # about 1 hour, Satoshis/KB
    avgFee: int  # about 30 minutes
    fastFee: int  # about 10 minutes

@dataclass
class ITokenUtxo(IDumpable):
    tx_id: str
    output_index: int
    satoshis: int
    type: AddressType
    amount: int = 0
    script: Optional[str] = None
    script_hash: Optional[str] = None
    private_key_wif: Optional[str] = None
    tx_hex: Optional[str] = None
    sequence: Optional[int] = None

@dataclass
class IUpN20Data:
    p: str = "n20"
    op: str = "up"
    tick: str = "NOTE"
    v: int = 0

@dataclass
class IBurnN20Data:
    p: str = "n20"
    op: str = "burn"
    tick: str = "NOTE"
    key: Any = 0

@dataclass
class IDeployN20Data:
    p: str = "n20"
    op: str = "deploy"
    tick: str = "NOTE"
    max: int = 21000000
    lim: int = 5000
    dec: int = 8
    sch: str = None
    key: Any = None

@dataclass
class IMintN20Data:
    p: str = "n20"
    op: str = "mint"
    tick: str = "NOTE"
    amt: int = 5000
    key: Any = None

@dataclass
class ITransferN20Data:
    p: str = "n20"
    op: str = "transfer"
    tick: str = "NOTE"
    amt: Union[int, list] = 0
    key: Any = None
