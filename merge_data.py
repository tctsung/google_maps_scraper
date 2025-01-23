# TODO: merge outputs from parallel_main.py into one big table (with state & city info)
import os
import re
import pandas as pd
import datetime
from tqdm import tqdm


def find_files(directory_path=".", file_extension=".json"):
    # TODO: find all files in a directory with specific file extension
    file_paths = []

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith(file_extension):
                file_paths.append(os.path.join(root, file))
    return file_paths


def main():
    excel_files = find_files("output/", ".xlsx")
    combined_df = pd.DataFrame()
    today_date = str(datetime.datetime.now().strftime("%Y_%m_%d"))
    for filepath in tqdm(excel_files):
        parts = re.split(r"[\\/]+", filepath)
        state, city = parts[1].replace("_", " "), parts[2].replace("_", " ")
        raw = pd.read_excel(filepath)
        df = raw.copy()
        df.drop_duplicates(inplace=True)
        df["State"] = state
        df["City"] = city
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    combined_df.drop_duplicates(inplace=True)
    combined_df.reset_index(drop=True, inplace=True)
    combined_df.to_excel(f"output/combined_data_{today_date}.xlsx", index=False)


if __name__ == "__main__":
    main()
