class BaseAiProvider:
    """Base contract for CV AI providers."""

    def extract_candidate(self, cv_text):
        raise NotImplementedError
