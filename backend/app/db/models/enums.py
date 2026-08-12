"""Enum dùng chung cho model và schema.

Giá trị (`.value`) chính là chuỗi lưu trong DB và trả ra API, nên đổi giá trị
là breaking change — phải kèm migration.
"""

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


class CompanySize(str, Enum):
    S_1_9 = "1-9"
    S_10_24 = "10-24"
    S_25_99 = "25-99"
    S_100_499 = "100-499"
    S_500_1000 = "500-1000"
    S_1000_PLUS = "1000+"


class MemberRole(str, Enum):
    OWNER = "OWNER"
    RECRUITER = "RECRUITER"


class JobType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    FREELANCE = "FREELANCE"


class ExperienceLevel(str, Enum):
    NO_EXP = "NO_EXP"
    UNDER_1 = "UNDER_1"
    E_1_2 = "1_2"
    E_2_3 = "2_3"
    E_3_5 = "3_5"
    OVER_5 = "OVER_5"


class Gender(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    MALE = "MALE"
    FEMALE = "FEMALE"


class SalaryType(str, Enum):
    RANGE = "RANGE"
    FROM = "FROM"
    UP_TO = "UP_TO"
    AGREEMENT = "AGREEMENT"


class JobStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    TAKEN_DOWN = "TAKEN_DOWN"


class ApplicationStatus(str, Enum):
    PENDING = "PENDING"
    VIEWED = "VIEWED"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"
    HIRED = "HIRED"
