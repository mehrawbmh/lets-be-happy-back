from typing import Any

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse, Response
from starlette.datastructures import URL

from app.core.services.service import Service


class ResponseService(Service):
    @staticmethod
    def __create_error_detail(message) -> dict:
        return {
            'success': False,
            'message': message,
        }

    @staticmethod
    def __create_success_detail(content: Any = '') -> Any:
        if isinstance(content, str):
            return {
                'success': True,
                'message': content if content else None,
            }

        return content

    def success_200(self, content='successfully done'):
        return JSONResponse(
            self.__create_success_detail(content),
            status.HTTP_200_OK
        )

    def success_201(self, content: Any = 'successfully created'):
        return JSONResponse(
            self.__create_success_detail(content),
            status.HTTP_201_CREATED
        )

    def success_204(self):
        return Response(None, status.HTTP_204_NO_CONTENT)

    def redirect(self, url: str, status_code: int = 307):
        url = URL(url)
        return RedirectResponse(url, status_code=status_code)

    def error_400(self, message: str = 'bad request provided'):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            self.__create_error_detail(message)
        )

    def error_401(self, message: str = 'you have to login first!'):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            self.__create_error_detail(message)
        )

    def error_403(self, message: str = "you are not permitted for this action"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            self.__create_error_detail(message)
        )

    def error_404(self, message: str = 'not found!'):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            self.__create_error_detail(message)
        )

    def error_500(self, message: str = 'Something went wrong!'):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            self.__create_error_detail(message)
        )

    def error_501(self):
        raise HTTPException(
            status.HTTP_501_NOT_IMPLEMENTED,
            self.__create_error_detail('this feature is not implemented yet. try later =)')
        )

    def operation_response(self, operation_status: bool, success_message: str = "operation is done successfully",
                           error_message: str = "Something went wrong"):
        return self.success_200(success_message) if operation_status else self.error_500(error_message)


responseService = ResponseService()
