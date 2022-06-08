import json
import os
import random

DATA_DIR = os.path.join('chatbot', 'data')

with open(os.path.join(DATA_DIR, 'new_cse_intents.json')) as f:
    data = json.load(f)

random.shuffle(data)

with open(os.path.join(DATA_DIR, 'raw_intent_sentences.txt'), 'w') as f:
    for sample in data:
        f.write(sample[0]+'\n')