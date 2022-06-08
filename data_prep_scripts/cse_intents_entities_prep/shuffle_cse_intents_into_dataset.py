import json
import math
import os
import random

DATA_DIR = os.path.join('chatbot', 'data')

def loadData(*argv):
    data = []
    for arg in argv:
        with open(os.path.join(DATA_DIR, arg)) as f:
            data.append(json.load(f))
    return tuple(data)

def sortDataByIntent(data):
    byIntent = {}
    for sample in data:
        if sample[1] not in byIntent: byIntent[sample[1]] = []
        byIntent[sample[1]].append(sample)
    return byIntent

def getDataRatios(trainData, valData, testData):
    lTrain = len(trainData)
    lVal = len(valData)
    lTest = len(testData)
    total = lTrain + lVal + lTest
    rTrain = lTrain / total
    rVal = lVal / total
    rTest = lTest / total
    return (rTrain, rVal, rTest)

def writeFiles(**kwargs):
    for fName, data in kwargs.items():
        with open(os.path.join(DATA_DIR, fName+'.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# Read in all of the raw data.
trainData, valData, testData, cseData = loadData('orig_is_train.json', 'orig_is_val.json', 'orig_is_test.json', 'new_cse_intents.json')
cseSorted = sortDataByIntent(cseData)
rTrain, rVal, rTest = getDataRatios(trainData, valData, testData)

# Add the new CSE intents into the existing data collections.
for intent, cseSamples in cseSorted.items():
    lCse = len(cseSamples)
    iVal = math.floor(lCse*rTrain)
    iTest = math.floor(lCse*rVal) + iVal
    trainData = cseSamples[:iVal] + trainData
    valData = cseSamples[iVal:iTest] + valData
    testData = cseSamples[iTest:] + testData
random.shuffle(trainData)
random.shuffle(valData)
random.shuffle(testData)

# Write the new training files.
writeFiles(is_train=trainData, is_val=valData, is_test=testData)