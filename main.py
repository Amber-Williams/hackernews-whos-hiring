import os

import pandas as pd
import numpy as np

import utils


MONTH = os.environ['MONTH']
YEAR = os.environ['YEAR']

print("yay")

utils.create_hn_hiring_csv(MONTH, YEAR)

hiring_text_df = pd.read_csv(f"output/hn-hiring-{MONTH}-{YEAR}.csv")
test_hiring_text_df = np.array_split(hiring_text_df, 100)  # chunk parse data

utils.parse_hiring_comment(MONTH, YEAR, test_hiring_text_df[0], 0)

utils.join_batch_csvs(MONTH, YEAR)
utils.drop_time_wasters(MONTH, YEAR)
utils.turn_into_markdown(MONTH, YEAR)
