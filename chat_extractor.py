import json
from typing import Optional, List
from enum import Enum
from httpx import Timeout

from pydantic import BaseModel, ValidationError
from openai import OpenAI


structured_output_valid_gpt_models = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4o-2024-08-06"
]


system_role_prompt = """
    You are a data extraction expert that extracts job posting data based on a list of job postings you are provided.

    Important rules:
        There can be many roles to one posting in these cases the comment_id is will be the same for the related roles.
        Make sure if a job title has 'and' or '&' in it that you split the job title into more than one job postings.
"""


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


class ChatExtractor:
    def __init__(self, model_key: str, model: str):
        if isinstance(model, str):
            if model not in structured_output_valid_gpt_models:
                raise ValueError(
                    f"Invalid model. Available GPT models: {', '.join(_model for _model in valid_gpt_models)}"
                )
        self.model = model
        self.client = OpenAI(api_key=model_key)

    def extract(self, content) -> List[JobPosting]:
        try:
            content_json = json.dumps(content)
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                response_format=JobPostings,
                messages=[
                    {"role": "system", "content": system_role_prompt},
                    {"role": "user", "content": content_json},
                ],
                temperature=0.0,
                timeout=Timeout(60),
            )
            return completion.choices[0].message.parsed.postings
        except ValidationError as e:
            print(f"Validation error: {e}")
            raise e
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise err
