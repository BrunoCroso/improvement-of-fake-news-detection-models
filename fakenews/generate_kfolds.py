
'''
This script is responsible for generating datasets and sets of user IDs for k-fold cross-validation. It splits tweet data into
training, testing, and validation sets and saves them in separate directories. Additionally, it creates sets of user IDs for
each dataset and writes them to JSON files.
'''

import argparse
import os
import logging
import shutil
from sklearn.model_selection import train_test_split
import json
from sklearn.model_selection import StratifiedKFold

def write_user_sets(output_dir, train_fnames, test_fnames, val_fnames):
    '''
    This function processes the tweet data and creates sets of user IDs for the train, test, and validation datasets.
    The user IDs are extracted from the JSON representation of the tweet trees.
    '''

    trees_directory = "produced_data/trees"
    train_user_ids = set()
    for fname in train_fnames:
        path = os.path.join(trees_directory, fname)
        with open(path) as f:
           tree_json = json.load(f)
        train_user_ids.update([node["user_id"] for node in tree_json["nodes"]])

    test_user_ids = set()
    for fname in test_fnames:
        path = os.path.join(trees_directory, fname)
        with open(path) as f:
           tree_json = json.load(f)
        test_user_ids.update([node["user_id"] for node in tree_json["nodes"]])

    val_user_ids = set()
    for fname in val_fnames:
        path = os.path.join(trees_directory, fname)
        with open(path) as f:
           tree_json = json.load(f)
        val_user_ids.update([node["user_id"] for node in tree_json["nodes"]])

    path = os.path.join(output_dir, "train_user_ids.json")
    with open(path, "w") as f:
        json.dump({
            "user_ids": list(train_user_ids)
        },
        f)

    path = os.path.join(output_dir, "test_user_ids.json")
    with open(path, "w") as f:
        json.dump({
            "user_ids": list(test_user_ids)
        },
        f)

    path = os.path.join(output_dir, "val_user_ids.json")
    with open(path, "w") as f:
        json.dump({
            "user_ids": list(val_user_ids)
        },
        f)

def run(args):
    '''
    This function generates datasets for k-fold cross-validation by splitting the tweet trees into
    training, testing, and validation sets. It also creates sets of user IDs for each dataset and
    writes them to separate JSON files.
    '''

    logging.info("Generating datasets for k-fold cross validation")
    logging.info("Validation size:%s, number of folds:%s" % (args.test_size, args.k))

    kf = StratifiedKFold(n_splits=args.k, shuffle=True, random_state=1)

    trees = os.listdir("produced_data/trees")
    root_dir = os.path.join("produced_data", "datasets")

    # Tem que gerar o y antes disso
    y = []
    for tree in trees:
        if tree.endswith(".json"): 
            file_path = os.path.join("produced_data/trees", tree)
            with open(file_path, 'r') as f:
                tree_content = json.load(f)
                if tree_content["label"] == "real":
                    y.append(0)
                else:
                    y.append(1)
    train_trees, test_trees, y_train, y_test = train_test_split(trees, y, test_size=args.test_size, shuffle=True, random_state=1, stratify=y)

    print(len(trees))
    for i, (train_index, val_index) in enumerate(kf.split(train_trees, y_train)):
        train_trees = [trees[index] for index in train_index]
        val_trees = [trees[index] for index in val_index]
        #train_trees, val_trees = train_test_split(train_trees, test_size=args.val_size, shuffle=True, random_state=1)
        output_dir = os.path.join(root_dir, 'dataset' + str(i))
        logging.info("Writing files in %s directory" % (output_dir))
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)
        train_path = os.path.join(output_dir, "train")
        test_path = os.path.join(output_dir, "test")
        val_path = os.path.join(output_dir, "val")
        os.makedirs(train_path)
        os.makedirs(val_path)
        os.makedirs(test_path)

        logging.info("The dataset has %s train trees" % (len(train_trees)))
        logging.info("The dataset has %s val trees" % (len(val_trees)))
        logging.info("The dataset has %s test trees" % (len(test_trees)))
        for fname in train_trees:
            shutil.copy("produced_data/trees/%s" % (fname), os.path.join(train_path, fname))
        for fname in test_trees:
            shutil.copy("produced_data/trees/%s" % (fname), os.path.join(test_path, fname))
        for fname in val_trees:
            shutil.copy("produced_data/trees/%s" % (fname), os.path.join(val_path, fname))
        logging.info("Writing sets of user ids for train, test, validation datasets")
        write_user_sets(output_dir, train_trees, test_trees, val_trees)

        metadata = {
            'number_of_train_trees': len(train_trees),
            'number_of_validation_trees': len(val_trees),
            'number_of_test_trees': len(test_trees),
        }
        with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

if __name__ == "__main__":

    logging.basicConfig(
        format="%(asctime)-15s %(name)-15s %(levelname)-8s %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(epilog="Example: python tweets_to_trees.py")
    parser.add_argument(
        "--test-size",
        help="test size",
        dest="test_size",
        type=float,
        default=0.25,
    )
    parser.add_argument(
        "--k",
        help="Number of folds",
        dest="k",
        type=int,
        default=2,
    )

    args = parser.parse_args()
    run(args)
