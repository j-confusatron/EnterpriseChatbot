# EnterpriseChatbot
[Paper]()
See paper for chatbot capabilities, including supported intents and skills.

## Requirements
### Components
- Neo4j Knowledge Graph DB (hosts CSE course catalog data)
- Python 3.8

### Python Libraries
- scikit-learn
- numpy
- matplotlib
- pytorch
- transformers (huggingface transformers)
- tqdm
- spacy (Be sure to download: en_core_web_sm AND en_core_web_lg)
- requests
- spacy-transformers
- beautifulsoup4
- neo4j
- pandas
- tensorflow_hub
- tensorflow

## To Run Chatbot
1. Edit properties DB_URI, DB_USER, DB_PASS in: data_prep_scripts/cse_course_catalog/neo4j_load_database.py and chatbot/ir_nlg_cscatalog.py.
2. Install all libraries noted above.
3. Run data_prep_scripts/cse_course_catalog/neo4j_load_database.py
4. Run debugserver.py.