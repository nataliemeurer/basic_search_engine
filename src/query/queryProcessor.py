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
    while currentLine != '':
        if '<num>' in currentLine:
            numLine = currentLine.split('Number: ')
            currentNum = int(re.sub("\s", "", numLine[1]))
        elif '<title>' in currentLine:
            titleLine = currentLine.split('Topic: ')
            title = titleLine[1].replace('\n', '')
            queries[title] = {}
            queries[title]["number"] = currentNum
            currentTitle = title
        elif '<desc>' in currentLine:
            currentLine = queryFile.readline()
            description = ''
            while '<narr>' not in currentLine:
                description += currentLine.replace('\n', ' ')
                currentLine = queryFile.readline()
            queries[currentTitle]["description"] = description
        currentLine = queryFile.readline()
    return queries

def preprocess_query(queryString, stopTerms):
    if queryString.isspace() or queryString == "" :
        return None
    # Convert document to class format
    query = q.Query(queryString)
    # Use the same preprocessing strategy here for consistency
    query.preprocessText(stopTerms)
    # clean up document by eliminating extraneous tokens, except in cases where they fall within brackets {}
    return query

def extract_bm25_scores(query, lexicon, doc_list):
    term_info = query.extractTermInformation()
    lexicon_compressed = [item[1] for item in lexicon]
    term_ids = []
    # find term id for each term
    for term in term_info:
        term_id = lexicon_compressed.index(term)
    # retrieve posting list entries for all term ids
    posting_entries = il.read_posting_entries_to_memory(ENV.INDEX_LOCATION + ENV.QUERY_PROCESSING_INDEX.lower() + ENV.POSTING_LIST_NAME + ".txt", term_ids)
    print posting_entries
    return None

'''
    Given a query and an index object (specified in index.py), return a score list by document

    Returns
    -------
    list of documents and their scores
      [ [documentID, docScore], [documentID, docScore]]
'''
def extract_vector_space_scores(query, index):
    # get terms and term frequencies from the query in format {term: tf}
    q_term_info_dict = query.extractTermInformation()
    q_tid_info_dict = {}
    for term_name in q_term_info_dict:
        tid = index.get_term_id_by_term(term_name)
        if tid != None:
            q_tid_info_dict[tid] = q_term_info_dict[term_name]
    
    # retrieve posting list entries for all term ids in format:
    # { termId: [[doc1, tf], [doc2, tf]]}
    relevant_posting_entries = index.get_posting_entries_by_terms(q_term_info_dict.keys())

    # Step 1:
    # calculate aggregate query term weight summation (for use in query weight function)
    query_total_summation = 0.0
    for term_id in relevant_posting_entries:
        query_total_summation += np.square(calculate_tf_idf(q_tid_info_dict[term_id], index.get_df_by_term_id(term_id), index.get_collection_size()))
    
    document_weights = {}
    for term_id in relevant_posting_entries:
        term_df = index.get_df_by_term_id(term_id)
        query_term_weight = calculate_term_weight(q_tid_info_dict[term_id], term_df, index.get_collection_size(), query_total_summation)
        for doc in relevant_posting_entries[term_id]:
            doc_id = doc[0]
            doc_tf = doc[1]
            document_term_weight = calculate_term_weight(doc_tf, term_df, index.get_collection_size(), index.get_document_weight_summation(doc_id))
            if doc_id in document_weights:
                document_weights[doc_id].append([query_term_weight, document_term_weight])
            else:
                document_weights[doc_id] = [[query_term_weight, document_term_weight]]
    final_scores = []
    # for each document, we sum the product of all the weights
    for doc in document_weights:
        final_scores.append([doc, calculate_vector_space_cosine(document_weights[doc], index.get_document_weight_summation(doc))])
    max_score = final_scores[0]
    final_scores.sort(key=operator.itemgetter(1), reverse=True)
    return final_scores

def extract_language_model_scores(query, lexicon, doc_list):
    # term_info = query.extractTermInformation()
    # lexicon_compressed = [item[1] for item in lexicon]
    # term_ids = []
    # # find term id for each term
    # for term in term_info:
    #     term_id = lexicon_compressed.index(term)
    # # retrieve posting list entries for all term ids in format
    # posting_entries = il.read_posting_entries_to_memory(ENV.INDEX_LOCATION + ENV.QUERY_PROCESSING_INDEX.lower() + ENV.POSTING_LIST_NAME + ".txt", term_ids)
    return None

'''
Calculates term weights for a given query or document
'''
def calculate_term_weight(tf, df, collection_size, document_tf_idf_summation):
    return calculate_tf_idf(tf, df, collection_size) / document_tf_idf_summation

def calculate_tf_idf(tf, df, collection_size):
    return (np.log(tf) + 1) * calculate_idf(df, collection_size)

def calculate_idf(df, collection_size):
    return np.log(collection_size / df)

'''
Calculates vector space cosine.  Given a list of the following: [queryWeight, documentWeights] for each term
'''
def calculate_vector_space_cosine(qw_dw_list, document_tf_idf_summation):
    numerator_sum = 0.0
    denominator_query_sum = 0.0
    denominator_document_sum = document_tf_idf_summation
    for weight_entry in qw_dw_list:
        numerator_sum += weight_entry[0] * weight_entry[1]
        denominator_query_sum += np.square(weight_entry[0])
    return numerator_sum / np.sqrt(denominator_document_sum * denominator_query_sum)
