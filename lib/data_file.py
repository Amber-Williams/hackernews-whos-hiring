import os
from typing import List

import pandas as pd

from lib.csv_to_markdown import Csv2Markdown


class DataFile:
    def __init__(self, write_dir: str, read_dir: str):
        self.write_dir = write_dir
        self.read_dir = read_dir
            
        if not os.path.exists(self.write_dir):
            os.makedirs(self.write_dir, exist_ok=True)

    def read_df(self, file_name: str):
        file_path = f"{self.read_dir}/{file_name}"
        if os.path.exists(file_path):
            return pd.read_csv(file_path, index_col=0)
        raise FileNotFoundError(f"File not found: {file_path}")

    def write_df(self, df: pd.DataFrame, file_name: str, partial: bool = False):
        if partial:
            if not os.path.exists(f"{self.write_dir}/batch"):
                os.makedirs(f"{self.write_dir}/batch", exist_ok=True)
            df.to_csv(f"{self.write_dir}/batch/{file_name}")
        else:
            df.to_csv(f"{self.write_dir}/{file_name}")

    def write_md_from_csv(self, csv_file_name: str, md_file_name: str):
        csv_file = f"{self.read_dir}/{csv_file_name.replace('.csv', '')}.csv"
        md_file = f"{self.write_dir}/{md_file_name.replace('.md', '')}.md"
        md = Csv2Markdown(filepath=csv_file)
        md.save_table(md_file)

    def join_partial_df(self, indices: List[int], file_name: str):
        batch_csvs = []
        for index in indices:
            batch_df = self.read_df(file_name=f"batch/{index}.csv")
            batch_csvs.append(batch_df)
        df = pd.concat(batch_csvs)
        df = df.reset_index(drop=True)
        self.write_df(df=df, file_name=file_name)
        return df
