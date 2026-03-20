"""Base formatter abstract class."""

from abc import ABC, abstractmethod
from typing import List

from src.models import FeedItem


class BaseFormatter(ABC):
    """Abstract base class for feed item formatters."""

    @abstractmethod
    def format(self, items: List[FeedItem]) -> str:
        """Format feed items to target format.

        Args:
            items: List of FeedItem instances to format

        Returns:
            Formatted string in the target format
        """
        pass

    @abstractmethod
    def get_content_type(self) -> str:
        """Get the MIME content type for this format.

        Returns:
            MIME type string (e.g., "application/xml")
        """
        pass
