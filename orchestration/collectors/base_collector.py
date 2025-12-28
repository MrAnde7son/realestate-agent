"""Base collector class for data collection framework."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from orchestration.location import LocationQuery, ensure_location_query


class BaseCollector(ABC):
    """Base class for all data collectors.

    This abstract base class enforces a consistent interface for all collectors
    and provides common functionality.
    """

    @abstractmethod
    def collect(self, location: Optional[LocationQuery] = None, **kwargs) -> Any:
        """Collect data from the source.

        This method must be implemented by all subclasses to provide
        a consistent interface for data collection.

        Returns:
            The collected data in a format appropriate for the collector type.
        """

    def validate_parameters(self, **kwargs) -> bool:
        """Validate input parameters for collection.

        Default implementation returns True. Subclasses can override
        to provide parameter validation.

        Returns:
            True if parameters are valid, False otherwise.
        """
        location = ensure_location_query(kwargs.get("location"))
        return bool(str(location))
