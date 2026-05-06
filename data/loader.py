"""CSV loading utilities."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

from .validator import DataValidator


class CSVLoader:
    """Loads CSV files and runs validation."""

    def __init__(self, validator: Optional[DataValidator] = None) -> None:
        self._validator = validator or DataValidator()

    def load_csv(self, path: str | Path) -> List[Dict[str, str]]:
        """Load a CSV file into a list of row dictionaries."""
        # TODO: Add error handling and logging.
        with Path(path).open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return list(reader)

    def load_agents(self, path: str | Path) -> List[Dict[str, str]]:
        """Load and validate agent CSV data."""
        rows = self.load_csv(path)
        # TODO: Call self._validator.validate_agents(rows).
        return rows

    def load_orders(self, path: str | Path) -> List[Dict[str, str]]:
        """Load and validate order CSV data."""
        rows = self.load_csv(path)
        # TODO: Call self._validator.validate_orders(rows).
        return rows

    def load_environment(self, path: str | Path) -> List[Dict[str, str]]:
        """Load and validate environment CSV data."""
        rows = self.load_csv(path)
        # TODO: Call self._validator.validate_environment(rows).
        return rows

    def load_constraints(self, path: str | Path) -> List[Dict[str, str]]:
        """Load and validate constraint CSV data."""
        rows = self.load_csv(path)
        # TODO: Call self._validator.validate_constraints(rows).
        return rows
