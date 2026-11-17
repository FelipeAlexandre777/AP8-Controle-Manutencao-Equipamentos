import hashlib
import hmac
import json
import os

MASTER_SECRET = os.getenv("HMAC_MASTER_SECRET", "minefleet-lab-secret-change-me")

def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def replica_secret(node_id: str) -> bytes:
    # Em execução distribuída, cada nó recebe somente sua própria chave.
    keyring = json.loads(os.getenv("HMAC_SECRETS", "{}"))
    if node_id in keyring:
        return keyring[node_id].encode()
    if os.getenv("NODE_ID") == node_id and os.getenv("NODE_SECRET"):
        return os.getenv("NODE_SECRET").encode()
    # Chave de desenvolvimento usada pelos testes locais.
    return hmac.new(MASTER_SECRET.encode(), node_id.encode(), hashlib.sha256).digest()

def sign_payload(node_id: str, payload: dict) -> str:
    return hmac.new(replica_secret(node_id), canonical_json(payload).encode(), hashlib.sha256).hexdigest()

def verify_signature(node_id: str, payload: dict, signature: str) -> bool:
    return hmac.compare_digest(sign_payload(node_id, payload), signature)
