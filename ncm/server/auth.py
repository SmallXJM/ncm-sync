
import hmac
import hashlib
import base64
import json
import time
from typing import Optional, Dict
from ncm.core.config import get_config_manager

class AuthHandler:
    @staticmethod
    def hash_password(password: str) -> str:
        # Use SHA256 for client-side compatibility and simplicity
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def create_access_token(data: dict, expires_delta: int = None) -> str:
        conf = get_config_manager().model().auth
        secret = conf.secret_key
        to_encode = data.copy()
        if expires_delta:
            expire = time.time() + expires_delta * 60
        else:
            expire = time.time() + conf.access_token_expire_minutes * 60
        
        to_encode.update({
            "exp": expire,
            "iat": time.time()
        })
        
        # Simple JWT implementation: Header.Payload.Signature
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")
        
        signature = hmac.new(
            secret.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        try:
            conf = get_config_manager().model().auth
            secret = conf.secret_key
            
            parts = token.split(".")
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            signature = hmac.new(
                secret.encode(),
                f"{header_b64}.{payload_b64}".encode(),
                hashlib.sha256
            ).digest()
            valid_signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
            
            # Use constant time comparison
            if not hmac.compare_digest(signature_b64, valid_signature_b64):
                return None
            
            # Decode payload
            payload_json = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)).decode()
            payload = json.loads(payload_json)
            
            # Check expiration
            if "exp" in payload and payload["exp"] < time.time():
                return None
            
            # Check if token is invalidated by password change
            # Need to check 'sub' and verify against user.password_changed_at
            if "sub" in payload and "iat" in payload:
                username = payload["sub"]
                token_iat = payload["iat"]
                
                # Find user
                for user in conf.users:
                    if user.username == username:
                        # If password was changed after token issue, invalidate
                        if token_iat < user.password_changed_at:
                            return None
                        break

            return payload
        except Exception:
            return None

    @staticmethod
    def verify_credentials(username: str, password_hash: str) -> bool:
        conf = get_config_manager().model().auth
        for user in conf.users:
            if user.username == username:
                # Compare stored password (plaintext in config) hashed with SHA256 vs provided hash
                # Server side calculation: sha256(config_password)
                # This assumes client sends sha256(password)
                stored_hash = hashlib.sha256(user.password.encode()).hexdigest()
                if hmac.compare_digest(stored_hash, password_hash):
                    return True
        return False
