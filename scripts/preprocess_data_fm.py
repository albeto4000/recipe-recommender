import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse import hstack
import argparse

import isodate
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler, MultiLabelBinarizer
from sklearn.decomposition import PCA

def clean_recipes(recipes):
    ''' Step 1 of data preprocessing '''
    # removing extra columns
    drop_cols = ['Name', 'AuthorId', 'AuthorName', 'TotalTime', 'DatePublished', 'Description',
                 'Images', 'RecipeIngredientQuantities', 'AggregatedRating', 'ReviewCount',
                 'RecipeServings', 'RecipeYield', 'RecipeInstructions', 'url', 'RecipeIngredientText',
                 'DirectionsText', 'RecipeIngredientUnits']
    df = recipes.drop(columns=drop_cols)

    # Preprocess CookTime and PrepTime
    # convert CookTime and PrepTime to integers for number of minutes
    df['CookTime'] = df.CookTime.fillna("PT0M")
    df['CookTime'] = df.CookTime.apply(lambda x: isodate.parse_duration(x)/60)
    df['CookTime'] = df['CookTime'].astype(int)/1000000
    
    df['PrepTime'] = df.PrepTime.fillna("PT0M")
    df['PrepTime'] = df.PrepTime.apply(lambda x: isodate.parse_duration(x)/60)
    df['PrepTime'] = df['PrepTime'].astype(int)/1000000
    
    # limiting max time
    df.loc[df['CookTime'] > 3*24*60, 'CookTime'] = 3*24*60
    df.loc[df['PrepTime'] > 1*24*60, 'PrepTime'] = 1*24*60

    # Preprocess Keywords and RecipeIngredientParts
    # convert Keywords and RecipeIngredientParts to list of strings
    # converting keywords string to list of strings
    keywords = df['Keywords']
    # replace " characters, then extract all characters between ()
    keywords = keywords.str.replace('"', '').str.findall(r'\((.*?)\)')
    # convert to string removing [], then split string by ', ' to form list of strings
    keywords = keywords.explode().str.split(', ')
    
    df['Keywords'] = keywords
    
    # converting RecipeIngredientParts string to list of strings
    ingredients = df['RecipeIngredientParts']
    # replace " characters, then extract all characters between ()
    ingredients = ingredients.str.replace('"', '').str.findall(r'\((.*?)\)')
    # convert to string removing [], then split string by ', ' to form list of strings
    ingredients = ingredients.explode().str.split(', ')
    
    df['RecipeIngredientParts'] = ingredients
    df = df.rename(columns={'RecipeIngredientParts':'Ingredients'})
    
    # replacing nans
    df['RecipeCategory'] = df.RecipeCategory.fillna('NaN')
    df['Keywords'] = df.Keywords.fillna('NaN')
    df['Ingredients'] = df.Ingredients.fillna('NaN')

    return df

def main(args):
    '''
    Main steps of the preprocessing are
        1. clean recipes data and extract only relevant columns
        2. apply pca to recipes features to reduce dimensionality, then save
    '''
    # loading data
    recipes = pd.read_csv(args.recipes)
    reviews = pd.read_csv(args.reviews)

    # Step 1 : cleaning, see above function
    # -------------------------------------
    recipes = clean_recipes(recipes)

    # Step 2 : PCA
    # -------------------------------------
    # now need to apply onehotencoder to RecipeCategory, Keywords, RecipeIngredientParts
    # setting up columntransformers
    passthrough_cols = ['RecipeId']
    robust_cols = ['CookTime', 'PrepTime']
    standard_cols = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent', 'SodiumContent',
                     'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']
    ohe_cols = ['RecipeCategory']
    mlb_cols = ['Keywords', 'Ingredients']
    
    pipe = FeatureUnion([
        ('robust_pipe', ColumnTransformer([('robust', RobustScaler(), robust_cols)])),
        ('standard_pipe', ColumnTransformer([('standard', StandardScaler(), standard_cols)])),
        ('ohe_pipe', ColumnTransformer([('ohe', OneHotEncoder(), ohe_cols)])),
    ])
    # cant fit MultiLabelBinarizer() into ColumnTransformer or Pipeline structure
    # so need to do it like this
    mlb_keywords = MultiLabelBinarizer()
    mlb_ingredients = MultiLabelBinarizer()
    # transform features
    encoded_cols = pipe.fit_transform(recipes)
    encoded_keywords = mlb_keywords.fit_transform(recipes['Keywords'])
    encoded_ingredients = mlb_ingredients.fit_transform(recipes['Ingredients'])
    # then concatenate
    encoded_features = hstack([encoded_cols, encoded_keywords, encoded_ingredients])

    # apply PCA to reduce dimensionality retaining 0.95 of variance
    # happens to be 35 components
    pca = PCA(svd_solver='arpack', whiten=True)
    pca_features = pca.fit_transform(encoded_features)[:,:35]

    # save pca results
    recipes_pca = pd.concat([recipes[['RecipeId']], pd.DataFrame(pca_features, columns=np.arange(1,36)).add_prefix('pca_')], axis=1)
    recipes_pca.to_csv(args.o_dir+'recipes_pca.csv', index=False)
    
    return

if __name__ == '__main__':
    # writing command-line interface
    desc = """
           Script for data preprocessing leading up to training a factorization machine
           Inputs:
               recipes: location of recipes data; file path
           Outputs:
               recipes_pca: recipes after pca; file path
           """

    parser = argparse.ArgumentParser(prog='data preprocessing before factorization machine', 
                                     description=desc)

    parser.add_argument('--recipes', help='location of recipes data', default='data/interim/top_recipes.csv')
    parser.add_argument('-o', '--o_dir', help='output directory recies_pca', default='data/processed/')

    args = parser.parse_args()
    
    main(args)
