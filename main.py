from lib.data_extractor_model import DataExtractorModel
from config import settings
from lib import extract_data_from_posts, get_post_df


if __name__ == "__main__":
    year = settings.YEAR
    month = settings.MONTH

    print(f"Running workflow for {year} {month}")
    extactor_model = DataExtractorModel(
            model_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL
        )
    post_df = get_post_df(extactor_model=extactor_model, year=year, month=month)
    if post_df is None:
        print(f"No new posts found for {year} {month}")
        exit()
    extract_data_from_posts(df=post_df, extactor_model=extactor_model, year=year, month=month)
