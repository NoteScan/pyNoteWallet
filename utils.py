from typing import List
import binascii
from constants import *

def to_x_only(pubkey: bytes):
    return pubkey[1:33]

def string_to_hexstring(s):
    return binascii.hexlify(s.encode('utf-8')).decode('utf-8')

def split_buffer_into_segments(
    buffer: bytes,
    segment_size: int = MAX_STANDARD_STACK_ITEM_SIZE,
    max_segments: int = MAX_DATA_SEGMENTS
  ) -> List[bytes]:
    """
    Splits a buffer into segments of a specified size.

    Args:
      buffer (bytes): The buffer to be split into segments.
      segment_size (int, optional): The size of each segment. Defaults to MAX_SCRIPT_ELEMENT_SIZE.
      max_segments (int, optional): The maximum number of segments allowed. Defaults to MAX_DATA_SEGMENTS.

    Returns:
      List[bytes]: A list of bytes representing the segments of the buffer.

    Raises:
      Exception: If the buffer size exceeds the maximum allowed number of segments.
    """
    if len(buffer) / segment_size > max_segments:
        raise ValueError(
            f"Buffer size exceeds the maximum allowed number of segments ({max_segments}).")

    segments = []
    i = 0
    while i < len(buffer):
        start = i
        end = min((i + segment_size), len(buffer))
        segment = buffer[start:end]
        segments.append(bytes(segment))
        i = end

    return segments

def sort_dict_by_key(d):
    """
    Recursively sorts a dictionary by keys at all levels, including dictionaries within lists.
    
    Parameters:
    d (dict): The dictionary to sort.
    
    Returns:
    dict: A new dictionary sorted by keys.
    """
    if isinstance(d, dict):
        # Sort dictionary by key
        return {k: sort_dict_by_key(v) for k, v in sorted(d.items())}
    elif isinstance(d, list):
        # If the item is a list, sort each element if it is a dictionary
        return [sort_dict_by_key(item) for item in d]
    else:
        # Return the item as is if it is neither a dictionary nor a list
        return d
