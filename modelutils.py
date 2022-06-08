import chatbot.intentclassifier as intentclassifier
import chatbot.nerclassifier as nerclassifier
from torch.optim import Adam
from data_prep_scripts.cse_intents_entities_prep.docanno_to_spacy import readDoccanoData, convertDoccanoToSpacy2
from sklearn.metrics import accuracy_score, classification_report
from tqdm import tqdm
from transformers import pipeline
import pandas as pd
import os

# Control what the script should do.
BUILD_INTENT_CLASSIFIER = False
BUILD_NER_EXTRACTOR = False
EVAL_CSE_ENTITIES = False
EVAL_CSE_INTENTS = False
EVAL_SENTIMENT_ANALYSIS = True

# Built and test intent classifiers.
if BUILD_INTENT_CLASSIFIER:
    DEFAULT_HYPERPARAMETERS = {
        'optimizer': Adam,
        'learningRate': 5e-5,
        'numEpochs': 3
    }
    intentClassifier = intentclassifier.IntentClassifier(hyperparameters=DEFAULT_HYPERPARAMETERS, modelName=intentclassifier.MODEL_NAME, plotLossAccuracy=False, evalTestData=False)
    print(intentClassifier.getIntent("tell me a joke"))

#
if EVAL_CSE_INTENTS:
    intentClassifier = intentclassifier.IntentClassifier()
    intentClassifier.evalOnTestData()

# Build and test NER classification.
if BUILD_NER_EXTRACTOR:
    nerClassifier = nerclassifier.NerClassifier()
    entities = nerClassifier.getEntities("What is the current weather in San Francisco?")
    print(entities)
    cseClassifier = nerclassifier.NerClassifier(modelName='spacy_cse_ner\model-best')
    entities = cseClassifier.getEntities("Describe CSE 590")
    print(entities)

# Evaluate the CSE entity extractor.
if EVAL_CSE_ENTITIES:
    # Build out a collection of actual and predicted entities.
    cseClassifier = nerclassifier.NerClassifier(modelName='spacy_cse_ner\model-best')
    sampleData = convertDoccanoToSpacy2(readDoccanoData())
    true_text = []
    true_entities = []
    pred_entities = []
    for sample in tqdm(sampleData):
        text = sample[0]
        entities = sample[1]['entities']
        predEntities = cseClassifier.getPredictionsForEval(text)

        # Cleanup samples where white-space was selected accidently. (This will cause mismatches with Spacy tokenized text)
        for ent in entities:
            ent_text = text[ent[0]:ent[1]]
            while ent_text.startswith(' '):
                ent[0] += 1
                ent_text = text[ent[0]:ent[1]]
            while ent_text.endswith(' '):
                ent[1] -= 1
                ent_text = text[ent[0]:ent[1]]

        # Merge the true data with the predictions.
        merge = {}
        for ent in entities:
            ent_text = text[ent[0]:ent[1]]
            if ent_text not in merge: merge[ent_text] = {'true': 'O', 'pred': 'O'}
            merge[ent_text]['true'] = ent[2]
        for ent in predEntities:
            ent_text = text[ent[0]:ent[1]]
            if ent_text not in merge: merge[ent_text] = {'true': 'O', 'pred': 'O'}
            merge[ent_text]['pred'] = ent[2]
        for text, entities in merge.items():
            true_text.append(text)
            true_entities.append(entities['true'])
            pred_entities.append(entities['pred'])

    report = classification_report(true_entities, pred_entities)
    print(report)

# Evaluate performance of the Huggingface sentiment analysis model.
if EVAL_SENTIMENT_ANALYSIS:
    sentimentAnalysis = pipeline('sentiment-analysis')
    cols = ['sentiment', 'id', 'date', 'query', 'user', 'tweet']
    csv_filepath = os.path.join('chatbot', 'data', 'sentiment140.testdata.csv')

    predicted_sentiments = []
    true_sentiments = []

    data = pd.read_csv(csv_filepath, sep=",", names=cols)
    for i in range(len(data)):
        sentiment = data[:]['sentiment'][i]
        if sentiment == 2:
            continue
        tweet = data[:]['tweet'][i]
        analysis = sentimentAnalysis(tweet)[0]
        predicted = 0 if analysis['label'] == 'NEGATIVE' else 4

        predicted_sentiments.append(predicted)
        true_sentiments.append(sentiment)
    
    report = classification_report(true_sentiments, predicted_sentiments, target_names=['Negative', 'Positive'])
    print(report)