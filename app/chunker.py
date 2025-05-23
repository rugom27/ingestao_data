import json, math
from typing import List, Dict, Any
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
CHUNK_TARGET = 2_000  # ~⅓ of token budget


def reunioes_to_json_chunks(records: List[Dict[str, Any]]) -> List[str]:
    """
    Split list of dicts into JSON strings, each ≤ CHUNK_TARGET tokens.
    """
    chunks, current, cur_tok = [], [], 0

    for rec in records:
        j = json.dumps(rec, default=str, ensure_ascii=False)
        t = len(ENC.encode(j))

        # if the record alone is bigger than target, flush current & keep as single
        if t > CHUNK_TARGET:
            if current:
                chunks.append(json.dumps(current, default=str, ensure_ascii=False))
                current, cur_tok = [], 0
            chunks.append(json.dumps([rec], default=str, ensure_ascii=False))
            continue

        if cur_tok + t > CHUNK_TARGET:
            chunks.append(json.dumps(current, default=str, ensure_ascii=False))
            current, cur_tok = [], 0

        current.append(rec)
        cur_tok += t

    if current:
        chunks.append(json.dumps(current, default=str, ensure_ascii=False))
    return chunks
