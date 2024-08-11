import json
from typing import List
from httpx import Timeout

from pydantic import ValidationError
from openai import OpenAI
import tiktoken

from models import JobPosting, JobPostings


class DataExtractorModel:
    def __init__(self, model_key: str, model: str):
        self.valid_gpt_models = [
            # Models must support structured data extraction
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4o-2024-08-06"
        ]

        if isinstance(model, str):
            if model not in self.valid_gpt_models:
                raise ValueError(
                    f"Invalid model. Available GPT models: {', '.join(_model for _model in self.valid_gpt_models)}"
                )
        self.model = model
        self.client = OpenAI(api_key=model_key)
        self.token_encoding = tiktoken.encoding_for_model(self.model)

        self.system_role_prompt = """
        You are a data extraction expert that extracts job posting data based on a list of job postings you are provided.
        Important rules:
        - There can be many roles to one posting in these cases the comment_id is will be the same for the related roles.
        - Make sure if a job title has 'and' or '&' in it that you split the job title into more than one job postings."""

    def get_token_estimate(self, content: str) -> int:
        return self.token_encoding.encode(content)

    def extract(self, content) -> List[JobPosting]:
        try:
            content_json = json.dumps(content)
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                response_format=JobPostings,
                messages=[
                    {"role": "system", "content": self.system_role_prompt},
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
