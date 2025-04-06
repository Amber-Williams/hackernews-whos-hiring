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
    comment_datetime: str
    comment_author: str
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

        # format location
        if self.company_city and self.company_city.lower() == "unknown":
            self.company_city = None

        if self.company_country and self.company_country.lower() == "unknown":
            self.company_country = None

        # format salary
        salary = None
        if self.salary and self.currency != CurrencyEnum.UNKNOWN:
            salary = f"{self.salary} ({self.currency.value})"
        elif self.salary:
            salary = self.salary

        if salary and not any(char.isdigit() for char in salary):
            salary = None

        # format tech stack
        languages_frameworks = None
        if self.languages_and_frameworks:
            languages_frameworks = ", ".join(self.languages_and_frameworks)

        # format employment type
        employment_type = self.employment_type.value
        if "unknown" in employment_type.lower():
            employment_type = EmploymentType.FULL_TIME.value

        return {
            "Post ID": self.comment_id,
            "Post Link": f"[Post link](https://news.ycombinator.com/item?id={self.comment_id})",
            "Post Date": self.comment_datetime,
            "Post Username": self.comment_author,
            "Company": self.company_name,
            "Job Title": self.job_title,
            "Employment Type": employment_type,
            "Salary": salary,
            "Remote": self.remote.value,
            "City": self.company_city,
            "Country": self.company_country,
            "Languages and Frameworks": languages_frameworks,
            "Remote Rules": self.remote_rules,
            "How to Apply": self.how_to_apply,
        }
