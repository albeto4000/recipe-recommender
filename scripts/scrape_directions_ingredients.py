import time
import numpy as np
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import argparse

def get_url(df):
    urls = []
    for my_name, my_id in zip(df['Name'], df['RecipeId']):
        try:
            urls.append('https://www.food.com/recipe/' + re.sub(' +', '-', my_name) + '-' + str(my_id))
        except TypeError:
            urls.append('TypeError')
    df['url'] = urls
    return df

def scrape_directions_ingredients(df):
    '''
    grabs ingredient units from ingredient webpage
    '''
    # if did not grab urls first, then grab it now
    if 'url' not in df.columns:
        df = get_url(df)

    # initialize lists to store loop results
    ingredients_series = []
    directions_series = []

    headers = {'User-Agent': 'av888@drexel.edu'}
    
    # Loop through each recipe
    for i, url in enumerate(df['url']):
        # periodically print progress
        if i%1000 == 0:
            print(f"Progress: Working on {i}th recipe")

        # include a wait to avoid limit issues
        time.sleep(1)
        # get webpage
        response = requests.get(url, headers=headers)

        # if there was an error with grabbing the url
        # set ingredient unit to error
        if response.status_code != 200:
            ingredients_series.append(['error'])
            directions_series.append(['error'])

        # if no error in grabbing, then scrape page for ingredient text
        else:
            # use BeautifulSoup to parse response
            soup = BeautifulSoup(response.text, 'html.parser')

            # scrape ingredients text
            ingred_text = []
            # grab text from ingredient list
            ingredient_text = soup.find_all('span', class_='ingredient-text svelte-ik1ga1')
            for ing_text in ingredient_text:
                ingred_text.append(re.sub(r'\s+', ' ', ing_text.text).strip())
            # push loop results to initialized list
            ingredients_series.append(ingred_text)

            # scrape directions data
            directions = []
            # grab text from directions section
            directions_text = soup.find_all('li', class_='direction svelte-ik1ga1')
            for d_text in directions_text:
                directions.append(d_text.text)
            # push loop results to initialized list
            directions_series.append(directions)

    df['RecipeIngredientText'] = ingredients_series
    df['DirectionsText'] = directions_series

    return df

def get_ingredient_units(df):
    '''
    Grabbing ingredient unit from RecipeIngredientText column
    '''
    if 'RecipeIngredientText' not in df.columns:
        print('Run scrape_directions_ingredients() function before using this')
        return

    # initialize list to store loop results
    ingredient_unit_series = []

    # loop through df
    for text in df['RecipeIngredientText']:
        # ingredient text is stored as a list so will need to loop again
        units = [s.split()[0] for s in text]

        # push loop result to list
        ingredient_unit_series.append(units)

    df['RecipeIngredientUnits'] = ingredient_unit_series

    return df

def main(args):
    # load raw data
    df = pd.read_csv(args.i_dir+'recipes.csv')
    df = df.loc[args.start:args.stop]
    # scrape directions and ingredients
    df = scrape_directions_ingredients(df)
    # add ingredient units column
    df = get_ingredient_units(df)

    # save output
    df.to_csv(args.o_dir+f"recipes_{args.start}-{args.stop}.csv")
    
    return

if __name__ == '__main__':
    # writing command-line interface
    desc = """
           Script for scraping directions and ingredients data from Food.com.
           Written to augment raw data in batches.
           Inputs:
               i_file: input directory
               o_file: output directory
               start: start index of batching process
               stop: stop index of batching process
           """

    parser = argparse.ArgumentParser(prog='scrape directions and ingredients', 
                                     description=desc)

    parser.add_argument('-i', '--i_dir', help='directory containing input file', default='./')
    parser.add_argument('-o', '--o_dir', help='directory of where to put output', default='./')
    parser.add_argument('--start', help='start index to batch scraping process', default=0)
    parser.add_argument('--stop', help='stop index to batch scraping process', default=1)

    args = parser.parse_args()
    args.start = int(args.start)
    args.stop = int(args.stop)
    
    main(args)
