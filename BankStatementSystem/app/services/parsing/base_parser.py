"""Base class for bank statement parsers.

All concrete parsers must inherit from this class and implement the
``extract_account_details`` and ``extract_transactions`` methods. The
methods receive a ``document`` object – for now this is the raw text
extracted from the PDF (or a dict containing per‑page data). The
return value should be a ``dict`` with the relevant fields defined in
the data model (e.g. ``account_holder_name``, ``masked_account_number``
for account details and a list of transaction dicts).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseBankParser(ABC):
    """Abstract base class for bank‑specific parsers.

    Sub‑classes must provide concrete implementations for the two
    public methods. ``document`` is intentionally loosely typed – parsers
    can decide whether they want the raw extracted text, the per‑page
    structures produced by ``pdf_processor``, or any other intermediate
    representation.
    """

    @abstractmethod
    def extract_account_details(self, document: Any) -> Dict[str, Any]:
        """Return a mapping of account‑level metadata.

        Expected keys (may be ``None`` if unavailable):
            - bank_name
            - account_holder_name
            - masked_account_number
            - ifsc_code
            - account_type
            - statement_start_date
            - statement_end_date
            - opening_balance
            - closing_balance
            - currency
        """
        raise NotImplementedError

    @abstractmethod
    def extract_transactions(self, document: Any) -> List[Dict[str, Any]]:
        """Return a list of transaction dictionaries.

        Each transaction dict should contain the fields defined in the
        ``Transaction`` model (see ``app/models/transaction.py``).
        """
        raise NotImplementedError
