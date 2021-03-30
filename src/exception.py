class MutantError(Exception):
    """Error related to Mutants"""


class OverlappingMutantError(MutantError):
    """Error related to the hash_tuple property"""
