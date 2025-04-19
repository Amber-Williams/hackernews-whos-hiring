from config import settings
from lib import create_report_from_post_data


if __name__ == "__main__":
    year = settings.YEAR
    month = settings.MONTH
    print(f"Running final report for {year} {month}")
    create_report_from_post_data(year=year, month=month)
