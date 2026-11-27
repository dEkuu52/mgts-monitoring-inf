from __future__ import annotations

import base64
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import AppError, register_exception_handlers
from app.core.security import create_access_token
from app.db.session import get_session
from app.services import object_service, user_service


class BasicAuthenticationHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user = SimpleNamespace(id=42, username="example-admin", role="admin")
        self.session = SimpleNamespace(get=AsyncMock(return_value=self.user))
        self.authenticate = AsyncMock()
        self.list_objects = AsyncMock(return_value=[])

        self.auth_setting = patch.object(settings, "auth_required", True)
        self.auth_setting.start()
        self.authenticate_patch = patch.object(user_service, "authenticate", self.authenticate)
        self.authenticate_patch.start()
        self.objects_patch = patch.object(object_service, "list_objects", self.list_objects)
        self.objects_patch.start()

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(api_router, prefix="/api")

        async def provide_session():
            yield self.session

        app.dependency_overrides[get_session] = provide_session
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self) -> None:
        self.client.close()
        self.objects_patch.stop()
        self.authenticate_patch.stop()
        self.auth_setting.stop()

    @staticmethod
    def basic_header(username: str, password: str) -> str:
        raw_credentials = f"{username}:{password}".encode("utf-8")
        encoded = base64.b64encode(raw_credentials).decode("ascii")
        return f"Basic {encoded}"

    def get_protected_objects(self, authorization: str | None = None):
        headers = {"Authorization": authorization} if authorization is not None else {}
        return self.client.get("/api/infrastructure-objects", headers=headers)

    def test_valid_basic_credentials_authenticate_through_existing_user_service(self) -> None:
        self.authenticate.return_value = self.user
        password = "correct:with:colon"

        response = self.get_protected_objects(self.basic_header("example-admin", password))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "data": []})
        self.authenticate.assert_awaited_once_with(self.session, "example-admin", password)
        self.list_objects.assert_awaited_once_with(self.session)

    def test_missing_or_malformed_basic_credentials_are_unauthenticated_not_server_errors(self) -> None:
        malformed_headers = (
            None,
            "Basic not-base64!",
            "Basic bm8tY29sb24=",  # valid base64 without the required colon
            "Basic /w==",  # base64 that is not valid UTF-8
            "Basic " + base64.b64encode(b"example\x00admin:password").decode("ascii"),
        )

        for authorization in malformed_headers:
            with self.subTest(authorization=authorization):
                response = self.get_protected_objects(authorization)
                self.assertEqual(response.status_code, 401)
                self.assertNotEqual(response.status_code, 500)

        self.authenticate.assert_not_awaited()
        self.list_objects.assert_not_awaited()

    def test_invalid_basic_credentials_are_unauthenticated_not_server_errors(self) -> None:
        self.authenticate.side_effect = AppError(401, "Неверные данные входа", "Проверьте данные.")

        response = self.get_protected_objects(self.basic_header("example-admin", "wrong-password"))

        self.assertEqual(response.status_code, 401)
        self.assertNotEqual(response.status_code, 500)
        self.authenticate.assert_awaited_once_with(self.session, "example-admin", "wrong-password")

    def test_existing_bearer_jwt_authentication_remains_supported(self) -> None:
        token = create_access_token(subject=str(self.user.id))

        response = self.get_protected_objects(f"Bearer {token}")

        self.assertEqual(response.status_code, 200)
        self.authenticate.assert_not_awaited()
        self.session.get.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
