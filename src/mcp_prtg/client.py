"""HTTP client for PRTG Network Monitor API."""

import re
from html import unescape

import httpx

from .config import get_settings


class PRTGError(Exception):
    """Base exception for PRTG API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PRTGAuthError(PRTGError):
    """Authentication failed."""
    pass


class PRTGNotFoundError(PRTGError):
    """Resource not found."""
    pass


class PRTGClient:
    """Async HTTP client for PRTG API."""

    HTML_TAG_RE = re.compile(r"<[^>]+>")

    def __init__(self):
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    @staticmethod
    def strip_html(text: str) -> str:
        """Strip HTML tags and unescape entities from PRTG message fields."""
        if not text or not isinstance(text, str):
            return text
        cleaned = PRTGClient.HTML_TAG_RE.sub("", text)
        return unescape(cleaned).strip()

    def _clean_record(self, record: dict) -> dict:
        """Strip HTML from known message fields in a record."""
        for key in ("message", "message_raw", "status", "status_raw",
                     "lastmessage", "info", "comments"):
            if key in record and isinstance(record[key], str):
                record[key] = self.strip_html(record[key])
        return record

    def _clean_records(self, records: list[dict]) -> list[dict]:
        """Strip HTML from all records."""
        return [self._clean_record(r) for r in records]

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.base_url,
                timeout=self.settings.timeout,
                verify=True
            )
        return self._client

    async def request(
        self,
        endpoint: str,
        params: dict | None = None
    ) -> dict:
        """Make authenticated GET request to PRTG API.

        Args:
            endpoint: API endpoint path (e.g. /api/table.json)
            params: Query parameters (apitoken added automatically)

        Returns:
            Parsed JSON response dict.
        """
        client = await self._get_client()

        if params is None:
            params = {}
        params["apitoken"] = self.settings.api_token

        response = await client.get(endpoint, params=params)

        if response.status_code == 401 or response.status_code == 403:
            raise PRTGAuthError(
                f"Authentication failed: {response.text}",
                response.status_code
            )

        if response.status_code == 404:
            raise PRTGNotFoundError(
                f"Not found: {endpoint}",
                response.status_code
            )

        if response.status_code >= 400:
            raise PRTGError(
                f"API error {response.status_code}: {response.text}",
                response.status_code
            )

        return response.json()

    async def table(
        self,
        content: str,
        columns: str,
        count: int = 500,
        filters: dict | None = None,
        extra_params: dict | None = None
    ) -> list[dict]:
        """Query the PRTG table API.

        Args:
            content: Content type (sensors, devices, groups, probes, channels, messages)
            columns: Comma-separated column names
            count: Max records to return
            filters: Optional filter parameters (e.g. {"filter_name": "@sub(server)"})
            extra_params: Any additional query parameters

        Returns:
            List of record dicts with HTML stripped from message fields.
        """
        params = {
            "content": content,
            "columns": columns,
            "count": count,
            "output": "json"
        }
        if filters:
            params.update(filters)
        if extra_params:
            params.update(extra_params)

        data = await self.request("/api/table.json", params)

        records = data.get(content, data.get("rows", []))
        # Some PRTG versions nest differently
        if not records and isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list):
                    records = data[key]
                    break

        return self._clean_records(records)

    async def historic_data(
        self,
        sensor_id: int,
        average: int = 300,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> list[dict]:
        """Get historical data for a sensor.

        Args:
            sensor_id: Sensor object ID
            average: Averaging interval in seconds (300 = 5min)
            start_date: Start date (YYYY-MM-DD-HH-MM-SS)
            end_date: End date (YYYY-MM-DD-HH-MM-SS)

        Returns:
            List of historical data records.
        """
        params = {
            "id": sensor_id,
            "avg": average,
            "output": "json"
        }
        if start_date:
            params["sdate"] = start_date
        if end_date:
            params["edate"] = end_date

        data = await self.request("/api/historicdata.json", params)
        records = data.get("histdata", [])
        return self._clean_records(records)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


_client: PRTGClient | None = None


def get_client() -> PRTGClient:
    """Get or create client singleton."""
    global _client
    if _client is None:
        _client = PRTGClient()
    return _client


def reset_client() -> None:
    """Reset client for testing."""
    global _client
    _client = None
