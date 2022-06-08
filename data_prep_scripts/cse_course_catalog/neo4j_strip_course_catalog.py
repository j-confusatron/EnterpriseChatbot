'''
This script will read in the CSE course catalog, via the requests and BeautiflSoup libraries.
Each course will be parsed and written to /neo4j_data as JSON files.
The completed JSON will be loaded into Neo4j by neo4j_load_database.py.
'''

import re
import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
import os
from itertools import product, zip_longest
import sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
import chatbot.nerclassifier as nerclassifier

nerclassifier.CSE_MODEL

# Setup our library of objects to record.
# We'll hardcode programs and levels, because there aren't many.
programs = {
    'Undergraduate': {'i': 1, 'title': 'Undergraduate', 'abbreviation':'CSE', 'HAS_COURSE': set()},
    'Professional (Evening)': {'i': 2, 'title': 'Professional Master', 'abbreviation':'CSEP', 'HAS_COURSE': set()},
    'Group Meetings': {'i': 3, 'title': 'Group Meetings', 'abbreviation':'CSE', 'HAS_COURSE': set()},
    'Graduate': {'i': 4, 'title': 'Graduate', 'abbreviation':'CSE', 'HAS_COURSE': set()},
    'Graduate Seminars': {'i': 5, 'title': 'Graduate Seminars', 'abbreviation':'CSE', 'HAS_COURSE': set()},
    'Math': {'i': 6, 'title': 'Math', 'abbreviation':'MATH', 'HAS_COURSE': set()},
    'Electrical Engineering': {'i': 7, 'title': 'Electrical Engineering', 'abbreviation':'E E', 'HAS_COURSE': set()},
    'Statistics': {'i': 8, 'title': 'Statistics', 'abbreviation':'STAT', 'HAS_COURSE': set()},
    'Linquistics': {'i': 9, 'title': 'Linquistics', 'abbreviation':'LING', 'HAS_COURSE': set()},
    'Bioengineering': {'i': 10, 'title': 'Bioengineering', 'abbreviation':'BIOEN', 'HAS_COURSE': set()},
    'Entrepreneurship': {'i': 11, 'title': 'Entrepreneurship', 'abbreviation':'ENTRE', 'HAS_COURSE': set()},
    'Neurobiology & Behavior': {'i': 12, 'title': 'Neurobiology & Behavior', 'abbreviation':'NEUBEH', 'HAS_COURSE': set()},
    'Applied Mathematics': {'i': 13, 'title': 'Applied Mathematics', 'abbreviation':'AMATH', 'HAS_COURSE': set()},
    'Aeronautics & Astronautics': {'i': 14, 'title': 'Aeronautics & Astronautics', 'abbreviation':'A A', 'HAS_COURSE': set()},
    'Mechanical Engineering': {'i': 15, 'title': 'Mechanical Engineering', 'abbreviation':'M E', 'HAS_COURSE': set()}
}
programsByAbbreviation = {
    'CSE': programs['Undergraduate'],
    'CSEP': programs['Professional (Evening)'],
    'CSE P': programs['Professional (Evening)'],
    'MATH': programs['Math'],
    'E E': programs['Electrical Engineering'],
    'STAT': programs['Statistics'],
    'LING': programs['Linquistics'],
    'BIOEN': programs['Bioengineering'],
    'ENTRE': programs['Entrepreneurship'],
    'NEUBEH': programs['Neurobiology & Behavior'],
    'AMATH': programs['Applied Mathematics'],
    'A A': programs['Aeronautics & Astronautics'],
    'M E': programs['Mechanical Engineering']
}
levels = {
    '000': {'i': 1, 'number': '000', 'HAS_COURSE': set()},
    '100': {'i': 2, 'number': '100', 'HAS_COURSE': set()},
    '200': {'i': 3, 'number': '200', 'HAS_COURSE': set()},
    '300': {'i': 4, 'number': '300', 'HAS_COURSE': set()},
    '400': {'i': 5, 'number': '400', 'HAS_COURSE': set()},
    '500': {'i': 6, 'number': '500', 'HAS_COURSE': set()},
    '600': {'i': 7, 'number': '600', 'HAS_COURSE': set()},
    '700': {'i': 8, 'number': '700', 'HAS_COURSE': set()},
    '800': {'i': 9, 'number': '800', 'HAS_COURSE': set()}
}
courses = {}
courseNumbers = {}
topics = {}
currentProgram = None

# Initialize a entity extractors, to fish topics out of course descriptions and numbers out of course ids.
cseNer = nerclassifier.NerClassifier(modelName=nerclassifier.CSE_MODEL)
ner = nerclassifier.NerClassifier()

# Get the course for the given id, or a new course if the course doesn't exist.
def getCourse(number, addToCurrentProgram=True, addToProgramByAbbreviation=False):
    course = None
    if number in courses:
        course = courses[number]

    else:
        course = {'i': len(courses)+1, 'display': '', 'title': '', 'number': number, 'description': '', 'TEACHES': set(), 'TAUGHT_JOINTLY_WITH': set(), 'PREREQ': set()}
        courses[number] = course

        # Add to the current program, if required.
        if addToCurrentProgram:
            currentProgram['HAS_COURSE'].add(course['i'])
        
        # Add to a program, by program abbreviation.
        if addToProgramByAbbreviation:
            for abbr, program in programsByAbbreviation.items():
                if number.startswith(abbr):
                    program['HAS_COURSE'].add(course['i'])

        # Set the course to a course level.
        num = ''
        for s in number:
            if s.isdigit():
                num += s
                break
        num = "%s00" % (num)
        levels[num]['HAS_COURSE'].add(course['i'])

    # Return the course.
    return course

def getCourseNUmber(number):
    cn = courseNumbers[number] if number in courseNumbers else {'i': len(courseNumbers)+1, 'number': number}
    courseNumbers[number] = cn
    return cn

# Get the topic for the given topic, or a new topic if it doesn't exist.
def getTopic(topic):
    topic_ = topics[topic] if topic in topics else {'i': len(topics)+1, 'label': topic}
    topics[topic] = topic_
    return topic_

def normalizeTopic(topic):
    while len(topic) > 0 and not topic[-1].isalnum(): topic = topic[:-1]
    while len(topic) > 0 and not topic[0].isalnum(): topic = topic[1:]
    return topic if len(topic) > 0 else None

# Create a Course object and all dependencies, from the raw course title and description stripped from the CSE course catalog.
def parseCourse(rawTitle, rawBody):
    # Split up the raw title and populate the basic course.
    rawTitle = rawTitle.split(':')
    number = rawTitle[0].strip()
    course = getCourse(number)
    course['title'] = rawTitle[1].strip()

    # Clean up the raw course body. Unfortunately, the text is not uniform across courses, so this requires some massaging.
    rawBody = rawBody.replace('Offered: jointly with', 'Offered jointly with')
    rawBody = rawBody.split('Offered jointly with')
    jointOffer = rawBody[1].strip() if len(rawBody) > 1 else ''
    rawBody = rawBody[0].split('Prerequisite:')
    course['description'] = rawBody[0].strip()
    prereqs = rawBody[1].strip() if len(rawBody) > 1 else ''

    # Detect and record topics in the course description. We'll treat titles detected as topics.
    entities = cseNer.getEntities(course['description'])
    for label, ents in entities.items():
        for e in ents:
            e = normalizeTopic(e)
            if e:
                topic = getTopic(e)
                course['TEACHES'].add(topic['i'])
    
    # Parse joint offerings.
    if len(jointOffer) > 0:
        jointOffer = jointOffer.split('.')[0]
        jointOffer = jointOffer.split(';')[0]
        for olvl1 in jointOffer.split('/'):
            for olvl2 in olvl1.split(','):
                jointCourse = getCourse(olvl2.strip(), addToCurrentProgram=False, addToProgramByAbbreviation=not olvl2.strip().startswith('CSE'))
                course['TAUGHT_JOINTLY_WITH'].add(jointCourse['i'])
    
    # Parse prerequisites.
    for m in re.finditer(r'(([A-Z])+\s)?([A-Z])+\s\d+', prereqs):
        prereqCourse = getCourse(m.group(), addToCurrentProgram=False, addToProgramByAbbreviation=not m.group().startswith('CSE'))
        course['PREREQ'].add(prereqCourse['i'])

def getCourseNumberSynonyms(course_number):
    synonyms = []
    number_parts = course_number.split()
    for separators in product((' ', ''), repeat=len(number_parts)-1):
        synonyms.append(''.join(number+separator for number, separator in zip_longest(number_parts, separators, fillvalue='')))
    print(synonyms)

# Grab the course catalog HTML and load it into beautiful soup.
cseUrl = 'https://www.cs.washington.edu/education/courses'
cseHtml = requests.get(cseUrl).text
soup = BeautifulSoup(cseHtml, 'html.parser')
content = soup.find_all('div', attrs={'class': 'view-content'})[0]

# Iterate over the content.
# Pattern is:
# <h3></h3><h3>PROGRAM</h3> -> <div><div><span>COURSE.TITLE&ID</span>COURSE.DESC BLOB</div></div>...
for i, element in tqdm(enumerate(content.children)):
    # If the current element is h3, we're dealing with a new program, set it as current..
    if element.name == 'h3':
        programName = element.text.replace('Courses', '').strip()
        currentProgram = programs[programName]

    # Div means we're on a course listing.
    elif element.name == 'div':
        courseContent = element.div.text
        courseTitle = courseContent.split('\n')[1].strip()
        courseBody = courseContent.split('\n')[2].strip()
        parseCourse(courseTitle, courseBody)

# Dump the results to JSON, for loading into Neo4j.
fPrograms = os.path.join('data_prep_scripts', 'cse_course_catalog', 'neo4j_data', 'programs.json')
fLevels = os.path.join('data_prep_scripts', 'cse_course_catalog', 'neo4j_data', 'levels.json')
fTopics = os.path.join('data_prep_scripts', 'cse_course_catalog', 'neo4j_data', 'topics.json')
fCourses = os.path.join('data_prep_scripts', 'cse_course_catalog', 'neo4j_data', 'courses.json')

for p in programs.values(): p['HAS_COURSE'] = list(p['HAS_COURSE'])
for l in levels.values(): l['HAS_COURSE'] = list(l['HAS_COURSE'])
for c in courses.values():
    c['display'] = "%s: %s" % (c['number'], c['title']) if c['title'] else c['number'] # Give the course something that displays nicely in Neo4j.
    c['TEACHES'] = list(c['TEACHES'])
    c['TAUGHT_JOINTLY_WITH'] = list(c['TAUGHT_JOINTLY_WITH'])
    c['PREREQ'] = list(c['PREREQ'])

with open(fTopics, 'w', encoding='utf-8') as f:
    json.dump(topics, f, ensure_ascii=False, indent=4)
with open(fPrograms, 'w', encoding='utf-8') as f:
    json.dump(programs, f, ensure_ascii=False, indent=4)
with open(fLevels, 'w', encoding='utf-8') as f:
    json.dump(levels, f, ensure_ascii=False, indent=4)
with open(fCourses, 'w', encoding='utf-8') as f:
    json.dump(courses, f, ensure_ascii=False, indent=4)