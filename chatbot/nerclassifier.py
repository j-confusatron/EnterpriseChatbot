import spacy
import os

#spacy.prefer_gpu()

DEFAULT_MODEL = 'en_core_web_sm'
DEFAULT_LG_MODEL = 'en_core_web_lg'
CSE_MODEL = os.path.join('models', 'spacy_cse_ner', 'model-best')

class NerClassifier(object):

    def __init__(self, modelName=DEFAULT_MODEL):
        self.modelName = modelName
        self.nlp = spacy.load(self.modelName)

    def getEntities(self, prompt):
        # Declare entity trackers.
        entities = {}
        entity = ''

        # Parse the prompt and iterate over all tokens.
        doc = self.nlp(prompt)
        for token in doc:
            if token.ent_type == 0: continue
            if not token.ent_type_ in entities:
                entities[token.ent_type_] = []
            if token.ent_iob_ == 'B':
                entity = token.text
                entities[token.ent_type_].append(entity)
            else:
                entity += " %s" % (token.text)
                entities[token.ent_type_][-1] = entity

        return entities

    def getPredictionsForEval(self, prompt):
        doc = self.nlp(prompt)
        entities = []
        for token in doc:
            if token.ent_type == 0: continue
            if token.ent_iob_ == 'B':
                entities.append([token.idx, token.idx+len(token.text), token.ent_type_])
            else:
                if token.text.startswith("'"):
                    entities[-1][1] += len(token.text)
                else:
                    entities[-1][1] += len(token.text)+1
        return entities