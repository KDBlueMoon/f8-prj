"""Enum dùng chung cho model và schema — khớp đúng enum trong openapi.yaml."""

from enum import Enum


class UserRole(str, Enum):
    CANDIDATE = "CANDIDATE"
    EMPLOYER = "EMPLOYER"
    ADMIN = "ADMIN"


class CompanyStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class VerificationTier(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


class JobType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    FREELANCE = "FREELANCE"
    INTERNSHIP = "INTERNSHIP"


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    NOT_REQUIRED = "NOT_REQUIRED"


class SalaryType(str, Enum):
    RANGE = "RANGE"
    AGREEMENT = "AGREEMENT"
    UP_TO = "UP_TO"
    MINIMUM = "MINIMUM"


class JobStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
