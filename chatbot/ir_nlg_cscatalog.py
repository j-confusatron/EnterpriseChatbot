import os
import collections
import tensorflow_hub as hub
import tensorflow as tf
import numpy as np 
import pandas as pd 
from collections import defaultdict
from neo4j import GraphDatabase
import chatbot.nerclassifier as nerclassifier
from chatbot.usersession import UserSession

D_KG_TOP = True
VERBOSE = True

# Define our db properties and methods for retrieving labels.
DB_URI = 'bolt://localhost:7687'
DB_USER = 'neo4j'
DB_PASS = 'cse590'

class Question2Cypher():
    """ Natural Language to Graph DB query(Cypher) Converter"""
    
    def __init__(self):
        # Had to add in some Tensorflow v1 compatability code.
        tf.compat.v1.disable_eager_execution()
        self.sess = tf.compat.v1.Session()

        csv_filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'text2cypher_questions.csv')
        #ner model
        self.ner_model = nerclassifier.NerClassifier(modelName=nerclassifier.CSE_MODEL)
        #gazetter
        self.build_entity_dic()
        #templeate dictionary {sentence : query}
        self.build_template_dic(csv_filepath)
        #Sentence encoder
        module_url ="https://tfhub.dev/google/universal-sentence-encoder-large/3"      
        self.encoder = hub.Module(module_url)
        self.build_template_mat()
        
        self._x = tf.compat.v1.placeholder(tf.string, shape=(None))
        self._embed = self.encoder(self._x)

    def netagger(self, input_text):
        entities = []

        # Do some input cleanup.
        if input_text.strip()[-1] == '?':
            input_text = input_text.strip()[:-1]+" ?"
        input_text = input_text.replace("'s","")
        
        # Split out some 2grams-6grams, to match known entities in Neo4j.
        candit = input_text.split()
        temp = candit[:]
        for i in range(len(temp)-1): #2 gram
            candit.append(temp[i]+" "+temp[i+1])
        for i in range(len(temp)-2): #3 gram
            candit.append(temp[i]+" "+temp[i+1]+" "+temp[i+2])
        for i in range(len(temp)-3): #4 gram
            candit.append(temp[i]+" "+temp[i+1]+" "+temp[i+2]+" "+temp[i+3])
        for i in range(len(temp)-4): #5 gram
            candit.append(temp[i]+" "+temp[i+1]+" "+temp[i+2]+" "+temp[i+3]+" "+temp[i+4])
        for i in range(len(temp)-5): #6 gram
            candit.append(temp[i]+" "+temp[i+1]+" "+temp[i+2]+" "+temp[i+3]+" "+temp[i+4]+" "+temp[i+5])

        # Replace matced Neo4j entities with their tag.
        for c in reversed(candit):
            if c.lower() in self.gaz_keys:
                entities.append(c)
                input_text = input_text.replace(c,self.gazetter[c.lower()])

        # Run the CSE NER tagger over the input, to find other entities.
        cse_entities = self.ner_model.getEntities(input_text)
        for tag, tag_entities in cse_entities.items():
            if D_KG_TOP and tag == 'C_TOPIC': continue
            for ent in tag_entities:
                entities.append(ent)
                input_text = input_text.replace(ent,"<"+tag+">")

        return input_text, entities

    def build_template_dic(self, csv_filepath):
        self.tmplt2query = defaultdict(str)
        self.tmplt2result = defaultdict(str)
        self.tmplt2noresult = defaultdict(str)
        data = pd.read_csv(csv_filepath, sep=",") 
        for i in range(len(data)):
            self.tmplt2query[data[:]["TAGGED_NAT_LANG"][i].replace('>','').replace('<','')[:-1].strip()+" ?"] =  data[:]["QUERY"][i]
            self.tmplt2result[data[:]["TAGGED_NAT_LANG"][i].replace('>','').replace('<','')[:-1].strip()+" ?"] =  data[:]["RESULT_RESPONSE"][i]
            self.tmplt2noresult[data[:]["TAGGED_NAT_LANG"][i].replace('>','').replace('<','')[:-1].strip()+" ?"] =  data[:]["NO_RESULT_RESPONSE"][i]

        self.tmplt = list(self.tmplt2query.keys())

    def build_template_mat(self):
        embeddings = self.encoder(self.tmplt)
        self.sess.run([tf.compat.v1.global_variables_initializer(), tf.compat.v1.tables_initializer()])
        self.tmplt_mat = self.sess.run(embeddings) # already normalized

    def text2query(self, tagged_text):
        ### get query string 
        query=[]
        query.append(tagged_text.replace('>','').replace('<',''))

        ### get query vectors
        query_mat = self.sess.run(self._embed, feed_dict={self._x: query})

        ### get similarity 
        result= query_mat@self.tmplt_mat.T #query size by sent size matrix
        #rank_idx=(result).argsort()[:,-1]
        sim_scores = 1.0 - np.arccos(result)
        rank_idx = np.argmax(sim_scores,axis=1)

        # Retrieve and return the query and responses.
        score = result[0][rank_idx[0]]
        query = self.tmplt2query[self.tmplt[rank_idx[0]]]
        result_response = self.tmplt2result[self.tmplt[rank_idx[0]]]
        no_result_response = self.tmplt2noresult[self.tmplt[rank_idx[0]]]
        return query, result_response, no_result_response, score
    
    def build_entity_dic(self):
        self.gazetter = collections.defaultdict()
        self.gaz_keys = []

        # Load all of the data from Neo4j and load it as known entities.
        neo4jData = getNeo4jData()
        for program in neo4jData['programs']:
            self.gazetter[program['title'].lower()] = '<C_PRG_TITLE>'
            self.gazetter[program['abbreviation'].lower()] = '<C_PRG_ABBR>'
        for level in neo4jData['levels']:
            self.gazetter[level['number']] = '<C_LEVEL>'
        for topic in neo4jData['topics']:
            self.gazetter[topic['label'].lower()] = '<C_TOPIC>'
        for course in neo4jData['courses']:
            self.gazetter[course['title'].lower()] = '<C_TITLE>'
            self.gazetter[course['number'].lower()] = '<C_ID>'
            
        self.gaz_keys.extend(self.gazetter.keys())

    def convert(self, intent, input_text):
        tagged_text, entities = self.netagger(input_text)
        cypher_query, result_response, no_result_response, score = self.text2query(intent+" "+tagged_text)
        return cypher_query, entities, result_response, no_result_response, score


# The original text2cypher uses saved CSVs to define known-entities, to get around NER tagging failures.
# Since we already have all of our pre-known entities saved off in Neo4j, we'll just load them in from there.
# C_ID = Course.number
# C_TITLE = Course.title
# C_TOPIC = Topic.label
# C_PRG_TITLE = Program.title
# C_PRG_ABBR = Program.abbreviation
# C_LEVEL = Level.number
def getPrograms(tx):
    query = "MATCH (p:Program) RETURN p.title AS title, p.abbreviation AS abbreviation"
    result = tx.run(query)
    return [record for record in result]
def getLevels(tx):
    query = "MATCH (l:Level) RETURN l.number AS number"
    result = tx.run(query)
    return [record for record in result]
def getTopics(tx):
    query = "MATCH (t:Topic) RETURN t.label AS label"
    result = tx.run(query)
    return [record for record in result]
def getCourses(tx):
    query = "MATCH (c:Course) RETURN c.title AS title, c.number as number"
    result = tx.run(query)
    return [record for record in result]
def getNeo4jData():
    data = {}
    driver = GraphDatabase.driver(DB_URI, auth=(DB_USER, DB_PASS))
    with driver.session() as session:
        data['programs'] = session.read_transaction(getPrograms)
        data['levels'] = session.read_transaction(getLevels)
        data['topics'] = [] if D_KG_TOP else session.read_transaction(getTopics)
        data['courses'] = session.read_transaction(getCourses)
    driver.close()
    return data


# Support for running queries retrieved by the model.
def runCypher(tx, query, tag2ne):
    result = tx.run(query, tag2ne)
    return [record for record in result]

def fillInResponse(response, results):
    # Replace new lines.
    response = response.replace('\\n', '\n')

    # Break the response into parts.
    responseParts = response.split('[')
    sBeforeResults = responseParts[0]
    responseParts = responseParts[1].split(']')
    sResults = responseParts[0]
    sAfterResults = responseParts[1]

    # Build the response.
    builtResponse = sBeforeResults
    for rec in results:
        sRec = sResults
        for node in rec:
            for property, value in node.items():
                sRec = sRec.replace("<"+property+">", str(value))
        builtResponse += sRec
    builtResponse += sAfterResults
    return builtResponse

def getCseData(query, tag2ne, result_response, no_result_response):
    response = ''

    # Replace the query parameters with tag2ne values.
    # Because doing this with regular expressions built into the queries is a bit of a mess, we have to be unelegeant about it.
    for key, val in tag2ne.items():
        query = query.replace(key, val)

    # Run the query ands build the response.
    driver = GraphDatabase.driver(DB_URI, auth=(DB_USER, DB_PASS))
    with driver.session() as session:
        results = session.read_transaction(runCypher, query, tag2ne)
        response = fillInResponse(result_response, results) if len(results) > 0 else no_result_response
    driver.close()

    # Return the response.
    return response


def replaceTonametag(cypher, entities):
    tag2ne = collections.defaultdict()
    tag_list =["<C_ID>","<C_TITLE>","<C_TOPIC>","<C_PRG_TITLE>","<C_PRG_ABBR>","<C_LEVEL>"]
    count=0
    for tag in tag_list:
        for i in range(cypher.count(tag)):
            if tag in cypher:
                cypher = cypher.replace(tag,"<NAME"+str(count)+">",i+1)
                count+=1

    for i,name in enumerate(entities):
        tag2ne["<NAME"+str(i)+">"] = name

    return cypher, tag2ne


# Provide an easy access method to retrieving data and generating a NL response.
cseQuestion2Cypher = Question2Cypher()
def getCseCatalogInfo(prompt, intent, entities, nerclassifier, userSession: UserSession):
    # Retrieve the executable query, confidence in the query, and entities extracted in the user prompt.
    cypher_query, entities, result_response, no_result_response, score = cseQuestion2Cypher.convert(intent, prompt)

    # Match entities to query wildcards.
    cypher_query, tag2ne = replaceTonametag(cypher_query, entities)

    # Build and return the NL response.
    response = getCseData(cypher_query, tag2ne, result_response, no_result_response)
    if VERBOSE:
        debug = "\n### CSE Debug ###\n%s\n%s\n%s\n%s\n%.4f\n%s" % (cypher_query, result_response, no_result_response, str(tag2ne), score, str(entities))
        print(debug)
    return response


# This was old code, for assignment 4 extra credit.
# text2cypher is a far batter solution, so this is no longer in use.
# Kept here only for posterity.
from spacy.symbols import nsubj, nsubjpass, VERB, pobj, dobj, aux, auxpass

def cseSemanticParse(self, prompt, entities):
    # Replace all entity text with variables, to ease the process of identifying subjects and objects.
    entity_lookup = {}
    for ent_l, ent_t in entities.items():
        for i in range(len(ent_t)):
            txt = ent_t[i]
            lbl = "%s_%d" % (ent_l, i)
            prompt = prompt.replace(txt, lbl)
            entity_lookup[lbl] = txt

    # Parse the document, record the sentence parts.
    doc = self.nerclassifier.nlp(prompt)
    frame = {'type': 'undefined', 'nsubj': [], 'verb': set(), 'pobj': [], 'dobj': []}
    wh = 'wh'
    s_order = []
    for token in doc:
        if token.dep in [nsubj, nsubjpass]:
          t = entity_lookup[token.text] if token.text.startswith('C_') else token.text
          frame['nsubj'].append(t)
          s_order.append(nsubj)
          if token.head.pos == VERB:
              frame['verb'].add(token.head)
        elif token.dep in [pobj]:
          t = entity_lookup[token.text] if token.text.startswith('C_') else token.text
          frame['pobj'].append(t)
          if token.head.pos == VERB:
              frame['verb'].add(token.head)
        elif token.dep in [dobj]:
          t = entity_lookup[token.text] if token.text.startswith('C_') else token.text
          frame['dobj'].append(t)
          if token.head.pos == VERB:
              frame['verb'].add(token.head)
        elif token.dep in [VERB] or token.text in frame['verb'] or token.pos_ == "VERB":
          s_order.append(VERB)
        elif token.dep in [aux, auxpass] or token.pos_ == "AUX":
          s_order.append(aux)
        elif token.text.lower().startswith('wh'):
          s_order.append(wh)

    # Identify the prompt type.
    if len(s_order) > 1 and s_order[0] == wh and s_order[1] == nsubj:
        frame['type'] = 'wh-subject'
    elif len(s_order) > 1 and s_order[0] == nsubj and s_order[1] == VERB:
        frame['type'] = 'declaritive'
    elif len(s_order) > 0 and s_order[0] == VERB and len(frame['nsubj']) == 0:
        frame['type'] = 'imperative'
    elif len(s_order) > 1 and s_order[0] == aux and s_order[1] == nsubj:
        frame['type'] = 'yes_no'

    # Return the generic CSE frame.
    return frame