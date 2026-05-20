import lenskit
from lenskit.data import Dataset
from lenskit import topn_pipeline, batch
from lenskit.knn import UserKNNScorer, ItemKNNScorer, SLIMScorer
from lenskit.basic import BiasScorer, PopScorer
from lenskit.als import BiasedMFScorer, ImplicitMFScorer
from lenskit.data import ItemListCollection
from lift import AssociationScorer

#for saving the models built
import os
import pickle
import logging

# Setup logging to see LensKit messages as recommended
logging.basicConfig(level=logging.INFO)

def main():

    # Adding Path to data (!!Change to your Local Path!!!)
    data_path = '/Users/ryanpeters7/Desktop/Spring 2026/DSCI 641/final project/data/'

    # Loading the Train and Test Item Collection data files to be used to run models
    print("Loading Training Data and Test Item Data....")
    train_data = Dataset.load(data_path + 'cleaned_data/split_data/train_data')

    test_item_data = ItemListCollection.load_parquet(data_path + 'cleaned_data/split_data/test_item_data.parquet')
    print("Data has successfully been loaded!")


    # Step 2: Running the Models
    print("------Running the Models-----")
    print()

    models = {
        "POPULAR" : PopScorer(),
        "BIAS" : BiasScorer(),
        "USER_USER" : UserKNNScorer(k=30, min_nbrs=2),
        "ITEM_ITEM" : ItemKNNScorer(k=20, min_nbrs=2),
        "ITEM_ITEM_IMPLICIT" : ItemKNNScorer(k=20, min_nbrs=2, feedback='implicit'),
        "EXPLICIT_MF" : BiasedMFScorer(features=64),
        "IMPLICIT_MF" : ImplicitMFScorer(features=64),
        "SLIM" : SLIMScorer(max_nbrs=200),
        'LIFT' : AssociationScorer(method="lift"),
        'BIASED_LIFT' : AssociationScorer(method="lift", damping=10)
    }

    #Grabbing the number of models so that it can be good for logging
    total_models = len(models)

    #Creating the model directory to save them (!!Change to your Local Path!!!)
    model_dir = "/Users/ryanpeters7/Desktop/Spring 2026/DSCI 641/final project/models/"

    for i, (name, scorer) in enumerate(models.items(), 1):
        print(f"\n{'='*40}")
        print(f"MODEL {i} OF {total_models}: {name}")
        print(f"{'='*40}")
        
        
        # Creating Predictions for specific models
        # Only required for: BIAS, USER-USER, ITEM-ITEM, and EXPLICIT-MF
        if name in ["BIAS", "USER_USER", "ITEM_ITEM", "EXPLICIT_MF"]:

            # Creating the topn pipeline for the models 
            pipe = topn_pipeline(scorer, n=20, predicts_ratings=True)
            
            # Training the models
            print(f"Status: Training {name} model...")
            pipe.train(train_data)

            print(f"Saving the {name} model pipeline.....")
            model_path = os.path.join(model_dir, f'{name.lower()}_pipeline.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump(pipe, f, protocol=pickle.HIGHEST_PROTOCOL)

            print(f"Status: Generating 20-item Recommendations for {name} model...")
            recs = batch.recommend(pipe, test_item_data)
            recs.save_parquet(data_path + f'recs/{name.lower()}_recs.parquet')

            print(f"Status: Generating Predictions...")

            preds = batch.predict(pipe, test_item_data)
            preds.save_parquet(data_path + f'preds/{name.lower()}_preds.parquet')
            
            print(f"Finished Computation on {name} Model!")

        else:


            # Creating the topn pipeline for the models 
            pipe = topn_pipeline(scorer, n=20)
            
            # Training the models
            print(f"Status: Training {name} model...")
            pipe.train(train_data)

            #Saving the model
            print(f"Saving the {name} model pipeline.....")
            model_path = os.path.join(model_dir, f'{name.lower()}_pipeline.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump(pipe, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Recommend (R) 20 items for top-N accuracy (nDCG/RBP)
            print(f"Status: Generating 20-item Recommendations for {name} model...")
            recs = batch.recommend(pipe, test_item_data)
            recs.save_parquet(data_path + f'recs/{name.lower()}_recs.parquet')
        
            print(f"Finished Computation on {name} Model!")


if __name__ == "__main__":
    main()