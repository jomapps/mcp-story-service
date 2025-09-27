import httpx
from typing import Dict, Any
from src.lib.error_handler import IntegrationError

class IntegrationManager:
    def __init__(self, brain_service_url: str, auto_movie_service_url: str, task_service_url: str):
        self.brain_service_url = brain_service_url
        self.auto_movie_service_url = auto_movie_service_url
        self.task_service_url = task_service_url
        self.client = httpx.AsyncClient()

    async def close(self):
        """Close the HTTP client and clean up resources."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def coordinate_with_brain(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinates with the Brain service.
        """
        try:
            response = await self.client.post(f"{self.brain_service_url}/coordinate", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise IntegrationError("Brain Service", str(e))

    async def send_to_auto_movie(self, data: Dict[str, Any]) -> None:
        """
        Sends data to the Auto-Movie service.
        """
        try:
            response = await self.client.post(f"{self.auto_movie_service_url}/update", json=data)
            response.raise_for_status()
        except httpx.RequestError as e:
            raise IntegrationError("Auto-Movie Service", str(e))

    async def get_from_task_service(self, task_id: str) -> Dict[str, Any]:
        """
        Gets data from the Task service.
        """
        try:
            response = await self.client.get(f"{self.task_service_url}/task/{task_id}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise IntegrationError("Task Service", str(e))
