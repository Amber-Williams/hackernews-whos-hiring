import pandas as pd
import numpy as np

import utils
from config import settings
from chat_extractor import ChatExtractor


data_files = utils.DataFiles()

dict_ = utils.scrape_hn_hiring_to_dict()
df = pd.DataFrame(dict_)
df = utils.count_tokens(df)
data_files.write_scraped_df(df=df)

batch_size = df['token_count'].sum() / settings.TOKEN_LIMIT
batched_df = np.array_split(df, batch_size)
chat = ChatExtractor(
        model_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        max_tokens=settings.TOKEN_LIMIT
    )

processed_batches = []
for index, batch_n_df in enumerate(batched_df):
    try:
        print(f"Processing... batch: {index}")
        request_content = batch_n_df.to_dict()["text"]
        summary_batch = chat.extract(request_content)

        if not summary_batch:
            raise ValueError(f"Parsed content of batch: {index} is empty")

        summary_batch_df = pd.DataFrame.from_dict(summary_batch, orient='index')
        summary_batch_df.index = summary_batch_df.index.astype(int)
        batch_n_df = summary_batch_df.join(batch_n_df, how='outer')   # join parsed content with original comment text
        data_files.write_df(df=batch_n_df, batch=index, file_name=None)
        print(f"Saved batch: {index}")
        processed_batches.append(index)
    except Exception as e:
        print(f"Unable to parse batch: {index} {e=}...continuing...")
        continue

summary_df = data_files.write_summary_df(processed_batches=processed_batches)
data_files.write_cleaned_df(df=summary_df)