from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.isbp import (
    IsbpCreateIncidentRequest,
    IsbpCreateIncidentResponse,
    IsbpIncidentStatusResponse,
)


@dataclass(slots=True)
class IsbpClientError(Exception):
    message: str
    status_code: int | None = None
    payload: dict[str, Any] | None = None

    def __str__(self) -> str:
        if self.status_code is None:
            return self.message
        return f"{self.message} (HTTP {self.status_code})"


class IsbpApiClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        create_path: str | None = None,
        status_path: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ISBP_BASE_URL).rstrip("/") + "/"
        self.token = token if token is not None else settings.ISBP_STATIC_TOKEN
        self.create_path = create_path or settings.ISBP_CREATE_PATH
        self.status_path = status_path or settings.ISBP_STATUS_PATH
        self.timeout_seconds = timeout_seconds or settings.ISBP_TIMEOUT_SECONDS

    async def create_incident(
        self,
        payload: IsbpCreateIncidentRequest,
    ) -> IsbpCreateIncidentResponse:
        response_payload = await self._request_json(
            "POST",
            self.create_path,
            body=payload.model_dump(mode="json", exclude_none=True),
        )
        return IsbpCreateIncidentResponse.model_validate(response_payload)

    async def get_incident_status(
        self,
        *,
        mh_rn: int,
        diagnosis_state_id: int,
    ) -> IsbpIncidentStatusResponse:
        response_payload = await self._request_json(
            "GET",
            self.status_path,
            query={
                "mh_rn": mh_rn,
                "diagnosis_state_id": diagnosis_state_id,
            },
        )
        return IsbpIncidentStatusResponse.model_validate(response_payload)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            self._request_json_sync,
            method,
            path,
            body,
            query,
        )

    def _request_json_sync(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None,
        query: dict[str, Any] | None,
    ) -> dict[str, Any]:
        url = urljoin(self.base_url, path.lstrip("/"))
        if query:
            url = f"{url}?{urlencode(query)}"

        request_body = None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if body is not None:
            request_body = json.dumps(body, ensure_ascii=False).encode("utf-8")

        request = Request(
            url,
            data=request_body,
            headers=headers,
            method=method.upper(),
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
                return self._parse_response_body(raw_body)
        except HTTPError as error:
            raw_body = error.read().decode("utf-8", errors="replace")
            payload = self._safe_parse_response_body(raw_body)
            raise IsbpClientError(
                message=payload.get("message") or error.reason or "ISBP request failed",
                status_code=error.code,
                payload=payload,
            ) from error
        except URLError as error:
            raise IsbpClientError(
                message=f"Unable to reach ISBP: {error.reason}",
            ) from error

    @staticmethod
    def _parse_response_body(raw_body: str) -> dict[str, Any]:
        payload = IsbpApiClient._safe_parse_response_body(raw_body)
        if not isinstance(payload, dict):
            raise IsbpClientError("ISBP returned a non-object JSON response")
        return payload

    @staticmethod
    def _safe_parse_response_body(raw_body: str) -> dict[str, Any]:
        if not raw_body.strip():
            return {}
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return {"message": raw_body}
        return payload if isinstance(payload, dict) else {"response": payload}

