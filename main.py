import pandas as pd
import numpy as np

import utils
from config import settings
from chat_extractor import ChatExtractor, JobPosting, CurrencyEnum


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


data_files = utils.DataFiles()

try:
    df = data_files.read_scraped_df()
except FileNotFoundError:
    dict_ = utils.scrape_hn_hiring_to_dict()
    df = pd.DataFrame(dict_)
    df = utils.count_tokens(df)
    data_files.write_scraped_df(df=df)

batch_size = df['token_count'].sum() / settings.TOKEN_LIMIT
batched_df = np.array_split(df, batch_size)
if len(batched_df) > 30:
    raise ValueError(f"Batch size is too large: {len(batched_df)}")

chat = ChatExtractor(
        model_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL
    )

processed_batches = []
for index, batch_n_df in enumerate(batched_df):
    try:
        print(f"Processing... batch: {index}")
        request_content = batch_n_df.reset_index().apply(
            lambda row: {"text": row['comment_text'], "comment_id": row['comment_id']},
            axis=1
        ).tolist()
        jobs = chat.extract(request_content)
        summary_batch_df = pd.DataFrame([JobPostingFormatted(**job.model_dump()).to_dict() for job in jobs])
        data_files.write_df(df=summary_batch_df, batch=index, file_name=None)
        print(f"Saved batch: {index}")
        processed_batches.append(index)
    except Exception as e:
        print(f"Unable to parse batch: {index} {e=}...continuing...")
        continue

summary_df = data_files.write_summary_df(processed_batches=processed_batches)
data_files.write_summary_md()
