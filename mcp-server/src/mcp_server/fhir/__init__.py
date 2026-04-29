"""FHIR client utilities."""

import os
import httpx
from typing import Any


FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir")


class FHIRClient:
    """Simple FHIR R4 client using httpx."""

    def __init__(self, base_url: str = FHIR_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Content-Type": "application/fhir+json"},
            timeout=30.0,
        )

    def search(self, resource_type: str, **params) -> dict[str, Any]:
        """Search for resources."""
        response = self.client.get(f"/{resource_type}", params=params)
        response.raise_for_status()
        return response.json()

    def read(self, resource_type: str, resource_id: str) -> dict[str, Any]:
        """Read a single resource by ID."""
        response = self.client.get(f"/{resource_type}/{resource_id}")
        response.raise_for_status()
        return response.json()

    def create(self, resource_type: str, resource: dict[str, Any]) -> dict[str, Any]:
        """Create a new resource."""
        response = self.client.post(f"/{resource_type}", json=resource)
        response.raise_for_status()
        return response.json()

    def update(self, resource_type: str, resource_id: str, resource: dict[str, Any]) -> dict[str, Any]:
        """Update an existing resource."""
        response = self.client.put(f"/{resource_type}/{resource_id}", json=resource)
        response.raise_for_status()
        return response.json()

    def delete(self, resource_type: str, resource_id: str) -> None:
        """Delete a resource."""
        response = self.client.delete(f"/{resource_type}/{resource_id}")
        response.raise_for_status()

    def close(self):
        """Close the HTTP client."""
        self.client.close()


# Global client instance
_client: FHIRClient | None = None


def get_fhir_client() -> FHIRClient:
    """Get or create the global FHIR client."""
    global _client
    if _client is None:
        _client = FHIRClient()
    return _client
