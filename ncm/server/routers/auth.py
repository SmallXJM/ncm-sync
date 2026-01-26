
from typing import Dict, Any
from ncm.server.decorators import ncm_service
from ncm.client import APIResponse
from ncm.server.auth import AuthHandler


class AuthorizationController:

    @ncm_service("/api/auth/login", ["POST"])
    async def login(self, username: str, password: str, **kwargs) -> APIResponse:
        """
        Login endpoint.
        Expects 'username' and 'password' (SHA256 hash of password + username).
        """
        if not username or not password:
            return APIResponse(status=400, body={"code": 400, "message": "用户名或密码不能为空"})

        if AuthHandler.verify_credentials(username, password):
            token = AuthHandler.create_access_token({"sub": username})
            return APIResponse(
                status=200, 
                body={
                    "code": 200, 
                    "message": "登录成功",
                    "data": {"token": token}
                }
            )
        
        return APIResponse(status=401, body={"code": 401, "message": "用户名或密码错误"})

    @ncm_service("/api/auth/check", ["GET"])
    async def check_auth(self, **kwargs) -> APIResponse:
        """
        Check if current token is valid.
        The middleware will handle the verification.
        If we reach here, it means we are authenticated.
        """
        # We can access user info from request state if middleware set it, but kwargs might not have it unless passed
        # For now just return success
        return APIResponse(status=200, body={"code": 200, "message": "Authenticated"})
