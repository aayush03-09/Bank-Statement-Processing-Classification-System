from .base_parser import BaseBankParser

class SBIParser(BaseBankParser):
    """Parser for State Bank of India statements.
    Currently a placeholder – implement extraction logic based on
    known SBI layout patterns.
    """

    def extract_account_details(self, document):
        # Placeholder implementation – return empty dict
        return {}

    def extract_transactions(self, document):
        # Placeholder – return empty list
        return []
