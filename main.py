import pandas as pd
import numpy as np

import utils
from config import settings
from chat_extractor import ChatExtractor

BATCH_SIZE = 5


utils.create_hn_hiring_csv(settings.MONTH, settings.YEAR)

hiring_text_df = pd.read_csv(f"output/hn-hiring-{settings.MONTH}-{settings.YEAR}.csv")
test_hiring_text_df = np.array_split(hiring_text_df, BATCH_SIZE)

for index, df in enumerate(test_hiring_text_df):
    utils.parse_hiring_comment(
        chatextractor=ChatExtractor(model_key=settings.OPENAI_API_KEY),
        month=settings.MONTH,
        year=settings.YEAR,
        df=df,
        batch=index
    )

utils.join_batch_csvs(settings.MONTH, settings.YEAR, len(test_hiring_text_df))
utils.drop_time_wasters(settings.MONTH, settings.YEAR)
utils.turn_into_markdown(settings.MONTH, settings.YEAR)
