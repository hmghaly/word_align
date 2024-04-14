from pymongo.mongo_client import MongoClient
import pymongo
import os, json, time
from itertools import groupby

def mongo_find(query,collection,sort_key=None, page_i=1,n_limit=10):
    t0=time.time()
    if page_i<1: page_i=1

    results_count = collection.count_documents(query) #get result count
    n_pages=int(results_count/n_limit)+1
    if page_i>n_pages: page_i=n_pages

    actual_page_i=page_i-1 #we enter page number as the display number (starting from 1 not zero)
    display_page_i=page_i

    skip_val=actual_page_i*n_limit
    if sort_key==None: cursor = collection.find(query, limit=n_limit).skip(skip_val) #enter the query
    else: cursor = collection.find(query, sort={sort_key:-1}, limit=n_limit).skip(skip_val) #enter the query
        
    res_list=list(cursor)
    t1=time.time()
    out_dict={}
    out_dict["results"]=res_list
    out_dict["n_pages"]=n_pages
    out_dict["page_i"]=display_page_i #for easier display
    first_pages=list(range(1,4)) #get pagination structure for easy display
    last_pages=[n_pages]
    surrounding_pages=list(range(display_page_i-1,display_page_i+2)) #the current page with the preceding and next
    surrounding_pages=[v for v in surrounding_pages if v>0 and v<n_pages]
    mid_pages=surrounding_pages
    all_pagination=sorted(list(set(first_pages+mid_pages+last_pages)))
    pagination_grouped=[[v[1] for v in list(group)] for key,group in groupby(enumerate(all_pagination),lambda x:x[1]-x[0])]

    out_dict["pagination"]=pagination_grouped #[first_pages,mid_pages,last_pages]
    prev_page_i, next_page_i=None,None
    if display_page_i>1: prev_page_i=display_page_i-1
    if display_page_i<n_pages: next_page_i=display_page_i+1
    out_dict["prev_page_i"]=prev_page_i
    out_dict["next_page_i"]=next_page_i

    
    out_dict["n_results_total"]=results_count
    out_dict["elapsed"]=t1-t0
    return out_dict

def mongo_insert_many(cur_list,cur_collection):
    out_dict={}
    if len(cur_list)==0: 
        out_dict["n_inserted"]=0
        return out_dict
    try:
        result_many = cur_collection.insert_many(cur_list, ordered=False)
        out_dict["n_inserted"]=len(result_many.inserted_ids)
    except pymongo.errors.BulkWriteError as e:
        with_errors=e.details['writeErrors']
        nInserted=e.details["nInserted"]
        out_dict["n_inserted"]=nInserted
        out_dict["n_inserted"]=len(with_errors)
    return out_dict

def match_elem(tag_key,tag_val):
    query0={tag_key: { "$elemMatch": { "$eq": tag_val } }}
    return query0

def mongo_aggregate(tag_key,match_query={}):
    agg_query=[]
    if match_query!={}: agg_query=[match_query]
    agg_query.append({ "$unwind": "$%s"%tag_key })
    agg_query.append({ "$group": { "_id": "$%s"%tag_key, "count": { "$sum": 1 } }})
    agg_query.append({ "$sort": { "count": -1 } })
    return agg_query

def q_aggr(collection,tag_key,match_query={}):
  cur_agg_query0=mongo_aggregate(tag_key=tag_key,match_query=match_query)
  cursor=collection.aggregate(cur_agg_query0)
  aggr_items=list(cursor)
  return aggr_items

# [
#    {
#       $match: {tags: { $elemMatch: { $eq: "20" } }}
#    },
#   { "$unwind": "$country" },  
#   { "$group": { "_id": "$country", "count": { "$sum": 1 } }},
#   { $sort: { count: -1 } }
# ]