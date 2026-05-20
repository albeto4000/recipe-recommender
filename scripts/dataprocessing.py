import lenskit
from lenskit.data import Dataset
from lenskit import splitting
#from lenskit.data import ItemListCollection
import logging

# Setup logging to see LensKit messages as recommended
logging.basicConfig(level=logging.INFO)


def main():
    #Loading the Movie Lens dataset using the buidlt in load_movielens function
    print("Loading Recipe data...")
    dataset = Dataset.load("/Users/ryanpeters7/Desktop/Spring 2026/DSCI 641/final project/data/cleaned_data/recipe_dataset")

    # Performing a Global Temporal Split with 15% reserved for testing
    print("Splitting data (80/20%  train test split)...")
    split = list(splitting.crossfold_users(dataset, partitions=1 ,method=splitting.SampleFrac(0.2)))

    # Unpacking the training and test data so that they can be later saved as parquet files
    train_data = split[0].train
    test_item_data = split[0].test

    # Save the results for use in other scripts, Saving as Parquet is the native format for LensKit 2026 
    print("Saving split data...")
    
    # Save the training dataset
    train_data.save("/Users/ryanpeters7/Desktop/Spring 2026/DSCI 641/final project/data/cleaned_data/split_data/train_data")
    
    # Save the test item collection 
    test_item_data.save_parquet("/Users/ryanpeters7/Desktop/Spring 2026/DSCI 641/final project/data/cleaned_data/split_data/test_item_data.parquet")
    
    print("Data split successfully! Files saved: train_data.parquet, test_item_data.parquet")

if __name__ == "__main__":
    main()