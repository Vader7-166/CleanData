# CleanData
A semi-automated data labeling tool for Vietnamese text.
This project builds a dictionary-based labeling system using TF-IDF to identify and assign labels to known patterns in the dataset. For data entries that are not covered by the dictionary, the system leverages PhoBERT to perform contextual prediction and automatically classify unlabeled text.

The combination of rule-based (TF-IDF dictionary) and model-based (PhoBERT) approaches helps improve labeling accuracy and coverage, especially for unseen or ambiguous data.
