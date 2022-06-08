'''
neo4j_strip_course_catalog.py writes JSON files to /neo4j_data, representing the CSE course catalog.
This script will read in those files and use directly populate Neo4j with them.
This script is also responsible for creating constraints.
Prior to loading the database, this script will tear everything down first. 
'''

from neo4j import GraphDatabase
import json
import os
from tqdm import tqdm

DB_URI = 'bolt://localhost:7687'
DB_USER = 'neo4j'
DB_PASS = 'cse590'

# Commands to wipe the database.
wipe = [
    "MATCH (n) DETACH DELETE n",
    "DROP CONSTRAINT programId IF EXISTS",
    "DROP CONSTRAINT programTitle IF EXISTS",
    "DROP CONSTRAINT levelId IF EXISTS",
    "DROP CONSTRAINT levelNumber IF EXISTS",
    "DROP CONSTRAINT courseId IF EXISTS",
    "DROP CONSTRAINT courseTitle IF EXISTS",
    "DROP CONSTRAINT courseNumber IF EXISTS",
    "DROP CONSTRAINT topicId IF EXISTS"
]

# Define constraints to create.
constraints = [
    "CREATE CONSTRAINT programId ON (p:Program) ASSERT p.programId IS UNIQUE",
    "CREATE CONSTRAINT programTitle ON (p:Program) ASSERT p.title IS UNIQUE",
    "CREATE CONSTRAINT levelId ON (l:Level) ASSERT l.levelId IS UNIQUE",
    "CREATE CONSTRAINT levelNumber ON (l:Level) ASSERT l.number IS UNIQUE",
    "CREATE CONSTRAINT courseId ON (c:Course) ASSERT c.courseId IS UNIQUE",
    "CREATE CONSTRAINT courseNumber ON (c:Course) ASSERT c.number IS UNIQUE",
    "CREATE CONSTRAINT topicId ON (t:Topic) ASSERT t.topicId IS UNIQUE"
]

def loadJson(fName):
    data = {}
    with open(fName, encoding="utf8") as fJson:
        data = json.load(fJson)
    return data.values()

def createTopic(tx, topic):
    query = "CREATE (t:Topic { topicId: $topicId, label: $label }) RETURN t"
    result = tx.run(query, topicId=topic['i'], label=topic['label'])
    return result

def createProgram(tx, program):
    # Create the program.
    query = "CREATE (p:Program { programId: $programId, title: $title, abbreviation: $abbreviation }) RETURN p"
    result = tx.run(query, programId=program['i'], title=program['title'], abbreviation=program['abbreviation'])
    
    # Create the program->course relationships.
    for courseId in program['HAS_COURSE']:
        query = (
            "MATCH (p:Program { programId: $programId }) "
            "MATCH (c:Course { courseId: $courseId }) "
            "CREATE (p)-[r:HAS_COURSE]->(c)"
        )
        tx.run(query, programId=program['i'], courseId=courseId)

def createLevel(tx, level):
    # Create the level.
    query = "CREATE (l:Level { levelId: $levelId, number: $number }) RETURN l"
    result = tx.run(query, levelId=level['i'], number=level['number'])

    # Create the level->course relationships.
    for courseId in level['HAS_COURSE']:
        query = (
            "MATCH (l:Level { levelId: $levelId }) "
            "MATCH (c:Course { courseId: $courseId }) "
            "CREATE (l)-[r:HAS_COURSE]->(c)"
        )
        tx.run(query, levelId=level['i'], courseId=courseId)

def createCourse(tx, course):
    # Create the course.
    query = (
        "MERGE (c:Course { courseId: $courseId }) "
        "ON CREATE SET c.display = $display, c.title = $title, c.number = $number, c.description = $description "
        "ON MATCH SET c.display = $display, c.title = $title, c.number = $number, c.description = $description "
        "RETURN c"
    )
    result = tx.run(query, courseId=course['i'], display=course['display'], title=course['title'], number=course['number'], description=course['description'])

    # Create all teaches relationships with topics.
    for topicId in course['TEACHES']:
        query = (
            "MATCH (c:Course { courseId: $courseId }) "
            "MATCH (t:Topic { topicId: $topicId }) "
            "CREATE (c)-[r:TEACHES]->(t)"
        )
        tx.run(query, courseId=course['i'], topicId=topicId)

    # Create all taught jointly relationships with other courses.
    for jointCourseId in course['TAUGHT_JOINTLY_WITH']:
        query = (
            "MATCH (c:Course { courseId: $courseId }) "
            "MERGE (j:Course { courseId: $jointCourseId }) "
            "CREATE (c)-[r:TAUGHT_JOINTLY_WITH]->(j)"
        )
        tx.run(query, courseId=course['i'], jointCourseId=jointCourseId)
    
    # Create all prereq relationships with other courses.
    for prereqCourseId in course['PREREQ']:
        query = (
            "MATCH (c:Course { courseId: $courseId }) "
            "MERGE (p:Course { courseId: $prereqCourseId }) "
            "CREATE (c)-[r:PREREQ]->(p)"
        )
        tx.run(query, courseId=course['i'], prereqCourseId=prereqCourseId)

def runCommand(tx, command):
    result = tx.run(command)
    return result

# Connect to the database and run through the data load.
driver = GraphDatabase.driver(DB_URI, auth=(DB_USER, DB_PASS))
with driver.session() as session:
    # Wipe the database.
    print("Wiping database...")
    for w in tqdm(wipe):
        session.write_transaction(runCommand, w)

    # Build out constraints.
    print("Building constraints...")
    for c in tqdm(constraints):
        session.write_transaction(runCommand, c)
    
    # Build topics.
    print("Creating topics...")
    topics = loadJson(os.path.join('data_prep_scripts', 'cse_course_catalog', 'neo4j_data', 'topics.json'))
    for t in tqdm(topics):
        session.write_transaction(createTopic, t)
    
    # Build courses.
    print("Creating courses...")
    courses = loadJson(os.path.join('data_prep_scripts', 'cse_course_catalog', 'neo4j_data', 'courses.json'))
    for c in tqdm(courses):
        session.write_transaction(createCourse, c)
    
    # Build programs.
    print("Creating programs...")
    programs = loadJson(os.path.join('data_prep_scripts', 'cse_course_catalog', 'neo4j_data', 'programs.json'))
    for p in tqdm(programs):
        session.write_transaction(createProgram, p)

    # Build levels.
    print("Creating levels...")
    levels = loadJson(os.path.join('data_prep_scripts', 'cse_course_catalog', 'neo4j_data', 'levels.json'))
    for l in tqdm(levels):
        session.write_transaction(createLevel, l)

# Close the connection.
driver.close()