import re
import codecs
import os
from object_definitions import query as q
import numpy as np
import utils as util
import settings as ENV
import indexLoader as il
import operator


# Pull relevant information from query file, including title, num, and description
def extractQueryInformation():
    queries = {}
    queryFile = codecs.open(ENV.QUERY_SRC, 'rb', 'utf-8')   # specify utf-8 encoding
    currentLine = queryFile.readline()
    currentNum = None
    currentTitle = ''
    count = 0
    while currentLine != '':
        if '<num>' in currentLine:
            count += 1
            numLine = currentLine.split('Number: ')
            currentNum = int(re.sub('\s', '', numLine[1]))
        elif '<title>' in currentLine:
            titleLine = currentLine.split('Topic: ')
            title = titleLine[1].replace('\n', '')
            queries[title] = {}
            queries[title]['number'] = currentNum
            currentTitle = title
        elif '<desc>' in currentLine:
            currentLine = queryFile.readline()
            description = ''
            narrative = ''
            while '<narr>' not in currentLine:
                description += currentLine.replace('\n', ' ')
                currentLine = queryFile.readline()
            currentLine = queryFile.readline()
            while '</top>' not in currentLine:
                narrative += currentLine.replace('\n', ' ')
                currentLine = queryFile.readline()
            queries[currentTitle]['description'] = description
            queries[currentTitle]['narrative'] = narrative
        currentLine = queryFile.readline()
    return queries

def preprocess_query(queryString, stopTerms):
    if queryString.isspace() or queryString == '' :
        return None
    # Convert document to class format
    query = q.Query(queryString)
    # Use the same preprocessing strategy here for consistency
    query.preprocessText(stopTerms)
    # clean up document by eliminating extraneous tokens, except in cases where they fall within brackets {}
    return query

'''
Query Processing methods that are non-specific to one retrieval method
'''
def calculate_tf_idf(tf, df, collection_size):
    return (np.log(tf) + 1) * calculate_idf(df, collection_size)

def calculate_idf(df, collection_size):
    return np.log(collection_size / df)



