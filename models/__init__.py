from typing import Optional, List
from enum import Enum

from pydantic import BaseModel


class RemoteEnum(str, Enum):
    YES = "yes"
    NO = "no"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    CNY = "CNY"
    AUD = "AUD"
    CHF = "CHF"
    MXN = "MXN"
    UNKNOWN = "unknown"


class EmploymentType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERN = "intern"
    UNKNOWN = "unknown"


class JobPosting(BaseModel):
    comment_id: int
    company_name: str
    job_title: str
    employment_type: EmploymentType
    currency: CurrencyEnum
    remote: RemoteEnum
    salary: Optional[str]
    remote_rules: Optional[str]
    how_to_apply: Optional[str]
    company_city: Optional[str]
    company_country: Optional[str]
    languages_and_frameworks: Optional[List[str]]


class JobPostings(BaseModel):
    postings: List[JobPosting]


class JobPostingFormatted(JobPosting):
    def to_dict(self):
        location = None
        if self.company_city and self.company_country:
            location = f"{self.company_city}, {self.company_country}"
        elif self.company_city:
            location = f"{self.company_city}, Unknown country"
        elif self.company_country:
            location = f"Unknown city, {self.company_country}"

        return {
            "Post Link": f"[Post link](https://news.ycombinator.com/item?id={self.comment_id})",
            "Company": self.company_name,
            "Job Title": self.job_title,
            "Employment Type": self.employment_type.value,
            "Salary": f"{self.salary} ({self.currency.value})" if self.currency != CurrencyEnum.UNKNOWN else self.salary,
            "Remote": self.remote.value,
            "Location": location,
            "Languages and Frameworks": ", ".join(self.languages_and_frameworks) if self.languages_and_frameworks else None,
            "Remote Rules": self.remote_rules,
            "How to Apply": self.how_to_apply,
        }
