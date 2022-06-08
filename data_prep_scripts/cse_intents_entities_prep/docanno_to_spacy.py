import json
import math
import os
import random
import spacy
from spacy.tokens import DocBin

DATA_DIR = os.path.join('chatbot', 'data')
DOCANNO_FILE = os.path.join(DATA_DIR, 'doccano.jsonl')
TRAIN_FILE = os.path.join(DATA_DIR, 'ner_train.spacy')
VAL_FILE = os.path.join(DATA_DIR, 'ner_validate.spacy')

TRAIN_PCT = 0.85

REMOVE_PREFIX = True
MERGE_LIKE_TAGS = True

# Read data from a Doccano export file.
def readDoccanoData(doccanoFile=DOCANNO_FILE):
    doccanoSamples = []
    with open(doccanoFile) as fDoccano:
        lines = fDoccano.readlines()
        for l in lines:
            doccanoSamples.append(json.loads(l))
    return doccanoSamples

# Convert Doccano data to Spacy 2.0 format.
def convertDoccanoToSpacy2(doccanoSamples, removePrefixes=REMOVE_PREFIX, mergeLikeTags=MERGE_LIKE_TAGS):
    spacy2Samples = []
    for s in doccanoSamples:
        # Pull the text and labels from the Doccano sample.
        text = s['data']
        entities = {'entities': s['label']}

        # Merge like-entities that run into each other into single entities, if required to do so.
        if mergeLikeTags:
            entityList = []
            for ent in entities['entities']:
                if ent[2].startswith('B-'):
                    entityList.append(ent)
                else:
                    entityList[-1][1] = ent[1]
            entities['entities'] = entityList
        
        # Remove the label prefix, if required to do so.
        if removePrefixes:
            for ent in entities['entities']:
                ent[2] = ent[2][2:]

        # Append the Spacy 2.0 samnple.
        spacy2Samples.append((text, entities))
    
    return spacy2Samples

# Write Spacy 2.0 samples to disk as Spacy 3 binary.
def writeSpacy2toSpacy3Binary(spacy2Samples, trainPct=TRAIN_PCT, trainFile=TRAIN_FILE, valFile=VAL_FILE):
    nlp = spacy.blank("en")
    db = DocBin()
    train_len = math.floor(len(spacy2Samples) * trainPct)
    for sampleSplit, fName in [(spacy2Samples[:train_len], trainFile), (spacy2Samples[train_len:], valFile)]:
        for text, annot in sampleSplit:
            doc = nlp.make_doc(text)
            ents = []
            for start, end, label in annot["entities"]:
                span = doc.char_span(start, end, label=label, alignment_mode="contract")
                if span is None:
                    print("Skipping entity")
                else:
                    ents.append(span)
            doc.ents = ents
            db.add(doc)
        db.to_disk(fName)


# Run the conversion.
doccanoSamples = readDoccanoData()
spacy2Samples = convertDoccanoToSpacy2(doccanoSamples)
random.shuffle(spacy2Samples)
writeSpacy2toSpacy3Binary(spacy2Samples)