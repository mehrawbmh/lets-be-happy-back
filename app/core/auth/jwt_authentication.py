from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.configs.settings import settings
from app.core.services.response_service import responseService
from app.models.entities.users import User
from app.models.schemas.auth.login_response import LoginResponse
from app.models.schemas.auth.token_data import UserTokenData


class JWTAuthentication:
    password_context = CryptContext(schemes=['bcrypt'])
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

    def __init__(self, token: str | None = None):
        self.token = token

    async def login_with_password(self, username: str, password: str) -> LoginResponse:
        user = await User.find_by_username(username)

        if user and self.check_password(password, user.password):
            bearer_token = self.encode(user)
            return LoginResponse(access_token=bearer_token, token_type="Bearer", role=user.role, id=user.id)

        return responseService.error_403("Invalid username or password")

    def get_user(self):
        if not self.token:
            return responseService.error_401("You have to log in first!")
        try:
            user_data = self.decode()
        except ExpiredSignatureError:
            return responseService.error_401('Token has expired')
        except JWTError:
            return responseService.error_403("Wrong login token given")

        user_data = UserTokenData.model_validate(user_data)
        return user_data

    @classmethod
    def hash_password(cls, plain_password: str):
        return cls.password_context.hash(plain_password)

    def check_password(self, plain: str, hashed: str) -> bool:
        return self.password_context.verify(plain, hashed)

    @staticmethod
    def encode(user: User, expiration_seconds: int = settings.ACCESS_TOKEN_EXPIRATION_SECONDS) -> str:
        # TODO: refactor and decouple jwt from password
        expiration = datetime.utcnow() + timedelta(seconds=expiration_seconds)
        user_data = UserTokenData.model_validate({**user.model_dump(), 'exp': expiration})

        return jwt.encode(user_data.model_dump(), settings.SECRET_KEY, settings.AUTHORIZATION_HASH_ALGORITHM)

    def decode(self) -> dict:
        return jwt.decode(self.token, settings.SECRET_KEY, settings.AUTHORIZATION_HASH_ALGORITHM)
