import multiprocessing
import os
import pandas as pd
import argparse
import sys


def run_scraper(search_content):
    os.system(f'python main.py -s="{search_content.strip()}" -t=200')


def main():  # eg. python parallel_main.py -s="boutique" -c="New York"
    # load required zip code based on city/state
    uszips = pd.read_excel("data/zip_code/uszips.xlsx")
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)  # search keyword
    parser.add_argument("-c", "--city", type=str)  # city
    parser.add_argument("-i", "--state_id", type=str)  # state ID
    args = parser.parse_args()

    # collect zip code:
    zip_code = uszips.copy()  # buffer for zip code in google search input
    zip_code["state_id"] = zip_code["state_id"].str.lower()
    if not args.search:
        print("Error occured: You must pass the -s search argument")
        sys.exit()
    search_for = args.search
    if args.city:
        city_lst = args.city.split(",")
        cities = list(city.strip().lower() for city in city_lst)
        zip_code["city"] = zip_code["city"].str.lower()
        zip_code = zip_code[zip_code["city"].isin(cities)]
    if args.state_id:
        state_id_lst = args.state_id.split(",")
        ids = list(id.strip().lower() for id in state_id_lst)
        zip_code["state_id"] = zip_code["state_id"].str.lower()
        zip_code = zip_code[zip_code["state_id"].isin(ids)]
    if (not args.city) and (not args.state_id):
        print(
            "Error occured: must pass at least one of the -c city or -i state_id argument"
        )
        sys.exit()
    if zip_code.shape[0] == 0:
        print(
            "Error occured: -c city or -i state_id might have typo. No matching city/state"
        )
        sys.exit()

    # create inputs with location info
    # Eg. California Los Angeles 90001 boutique
    inputs = []
    for index, row in zip_code.iterrows():
        search_input = f"{row['state_name']} {row['city']} {row['zip']} {search_for}"
        inputs.append(search_input)

    # Number of processes to run in parallel (adjust as needed)
    num_processes = multiprocessing.cpu_count() // 2

    # Create a pool of processes
    with multiprocessing.Pool(processes=num_processes) as pool:
        # Map the run_scraper function to the list of zipcodes
        pool.map(run_scraper, inputs)


if __name__ == "__main__":
    main()
