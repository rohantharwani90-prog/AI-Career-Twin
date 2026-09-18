"""Custom exceptions for the AI Career Twin application."""


class InvalidStudentProfileError(ValueError):
    """Raised when student profile data fails validation."""
    pass


class InvalidSkillError(ValueError):
    """Raised when a skill name or proficiency level is invalid."""
    pass


class InvalidCareerRoleError(ValueError):
    """Raised when an unrecognised career role is provided."""
    pass


class InvalidInterviewAnswerError(ValueError):
    """Raised when a submitted interview answer is blank or otherwise invalid."""
    pass


class DataStorageError(IOError):
    """Raised when the JSON persistence layer fails to read or write."""
    pass
