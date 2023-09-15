#!/usr/bin/python3
import os, re, json
import sys
import shutil
import zipfile
import random, string
import hashlib
from itertools import groupby
from difflib import SequenceMatcher
import copy
import math
import numpy as np

sys.path.append("code_utils")
import web_lib
import general

ver=sys.version_info
if ver[0]==3: 
  import html
  htmlp=html
if ver[0]==2: 
  import HTMLParser
  #HTMLParser.HTMLParser().unescape('Suzy &amp; John')  

import difflib
from nltk.stem.snowball import SnowballStemmer

#from pattern.en import lemma #make sure to install

stemmer = SnowballStemmer("english")

excluded_punc_tokens=["<s>","</s>",".","(",")",",",";","[","]",":","?","/","#","”","“","'s"]
excluded_words=["the","a","an","and","or", "of","in","on","at","to","by","with","for","from","about","against",
"is","are","was","were", "be","being", "has","have","had","it","its","they","as",
"may","would","which","so","through",
"he","she","his","her","them","that","their","those","this","such", "one","not","no",
"including","notes","hyperlink"]
all_excluded=excluded_punc_tokens+excluded_words


from scipy import spatial

def cos_sim(vector1,vector2):
  if len(vector1)==0 or len(vector2)==0: return 0
  result = 1 - spatial.distance.cosine(vector1, vector2)
  return result


def pad_list(list1,list_N): #trim list to a certain size, and pad it with empty strings if larger than this size
  list1 = (list1 + list_N * [''])[:list_N]
  return list1

def get_chunk_vector(chunk_tokens,wv_model):
  vec_list0=[]
  if wv_model==None or wv_model=={}: return [] #np.array(vec_list0)
  #vec_size0=wv_model.vector_size
  empty_vec0=[0.]*wv_model.vector_size
  #split0=chunk.split(" ")
  for token0 in chunk_tokens:
    if token0=="": tok_vec0= empty_vec0 #np.zeros(wv_model.vector_size,dtype=np.float32) #np.zeros(wv_model.vector_size)
    else:
      try: tok_vec0=wv_model.wv[token0].tolist()
      except: tok_vec0= empty_vec0 #[0.]* #np.zeros(wv_model.vector_size,dtype=np.float32) #np.zeros(wv_model.vector_size)
    vec_list0.append(tok_vec0)
  return vec_list0 #np.array(vec_list0)


def extract_ft_lb(input_dict,params={}): #extract features and labels from an input dict with context, src, trg, and outcome
  chunk_size0=params.get("chunk_size",5)
  cur_wv_model0=params.get("wv_model")
  outcome_positive=params.get("outcome_positive",False)

  include_chunks_wv=params.get("include_chunks_wv",False) #include a fixed numbers of wv features for both the pre/after context, src and trg chunks

  include_context_trg_sim=params.get("include_context_trg_sim",False)
  include_freq=params.get("include_freq",False)
  include_freq_log=params.get("include_freq_log",False)
  include_edit_types_oh=params.get("include_edit_types_oh",False)
  
  edit_types=params.get("edit_types",["other","acronym","acronym-s","capitalization","compunding","hyphenation"])
  cur_special_tokens=params.get("special_tokens",[]) #special tokens are high frequency tokens which are excluded from calculation of text vector but are important as one-hot features to determine immediate context
  cur_stop_tokens=params.get("stop_tokens",[]) #special tokens are high frequency tokens which are excluded from calculation of text vector but are important as one-hot features to determine immediate context
  
  include_null_repl_check=params.get("include_null_repl_check",False) #if src=trg

  include_prev_oh=params.get("include_prev_oh",False) #if src=trg
  include_next_oh=params.get("include_next_oh",False) #if src=trg

  include_prev_wv=params.get("include_prev_wv",False) #wv for prev token
  include_next_wv=params.get("include_next_wv",False) #wv for next token

  output_debug_dict=params.get("output_debug_dict",False) #if src=trg

  # include_paren_check=params.get("include_paren_check",False) #if surrounded by parentheses
  # include_start_check=params.get("include_start_check",False) #if repl at the start of  
  # include_end_check=params.get("include_end_check",False) #if repl at the end of sentence
  include_src_trg_char_ratio=params.get("include_src_trg_char_ratio",False) #check character ratio between src/trg
  include_trg_src_char_ratio=params.get("include_trg_src_char_ratio",False) #check character ratio between trg/src
  include_src_trg_token_ratio=params.get("include_src_trg_token_ratio",False) #check token ratio between src/trg
  include_trg_src_token_ratio=params.get("include_trg_src_token_ratio",False) #check token ratio between trg/src


  context0=input_dict["context"]
  src0=input_dict["src"]
  trg0=input_dict["trg"]
  outcome0=input_dict["outcome"]
  if outcome_positive:
    if outcome0==0: outcome0=0.5
    elif outcome0==-1: outcome0=0
  context_split=context0.split("|")
  context_pre_str,context_after_str=context_split
  context_pre_tokens=context_pre_str.strip().split(" ")
  context_after_tokens=context_after_str.strip().split(" ")
  src_tokens0=src0.split(" ")
  trg_tokens0=trg0.split(" ")
  context_pre_tokens=list(reversed(context_pre_tokens)) #reverse to make sure previous words are always in the same location
  src_tokens0=pad_list(src_tokens0,chunk_size0)
  trg_tokens0=pad_list(trg_tokens0,chunk_size0)
  context_pre_tokens=pad_list(context_pre_tokens,chunk_size0)
  context_after_tokens=pad_list(context_after_tokens,chunk_size0)
  prev_token0=context_pre_tokens[0]
  next_token0=context_after_tokens[0]
  #print("prev_token0",prev_token0,"next_token0",next_token0)



  all_cur_tokens=list(set(context_pre_tokens+context_after_tokens+src_tokens0+trg_tokens0))
  context_tokens_uq=list(set(context_pre_tokens+context_after_tokens))
  trg_tokens_uq=list(set(trg_tokens0))
  cur_vec_dict={}
  empty_vec0=[0.]*cur_wv_model0.vector_size
  for token0 in all_cur_tokens:
    try: tok_vec0=cur_wv_model0.wv[token0].tolist()
    except: tok_vec0= empty_vec0 
    cur_vec_dict[token0]=tok_vec0
    #print(token0,sum(tok_vec0))

  # print("src_tokens0",src_tokens0)
  # print("trg_tokens0",trg_tokens0)
  # print("context_pre_tokens",context_pre_tokens)
  # print("context_after_tokens",context_after_tokens)
  debug_dict={}
  combined_vec=[]
  if include_chunks_wv: #include fixed length vec for all chunk tokens
    temp=[]
    for item in [context_pre_tokens,context_after_tokens,src_tokens0,trg_tokens0]:
      cur_vec=[]
      for item_tok in item:
        found_vec=cur_vec_dict.get(item_tok,empty_vec0)
        combined_vec.extend(found_vec)
        temp.extend(found_vec)
    debug_dict["include_chunks_wv"]=temp


  if include_prev_wv:
    found_vec=cur_vec_dict.get(prev_token0,empty_vec0)
    combined_vec.extend(found_vec)  
    debug_dict["include_prev_wv"]=found_vec
  if include_next_wv:
    found_vec=cur_vec_dict.get(next_token0,empty_vec0)
    combined_vec.extend(found_vec)  
    debug_dict["include_next_wv"]=found_vec

  
  if include_null_repl_check: #check if src=trg
    repl_is_null=0
    if src0==trg0:repl_is_null=1 
    combined_vec.append(repl_is_null)
    debug_dict["include_null_repl_check"]=repl_is_null

  if include_src_trg_char_ratio: #include src/trg len ratio
    src_trg_char_ratio=len(input_dict["src"])/len(input_dict["trg"])
    combined_vec.append(src_trg_char_ratio)
    debug_dict["include_src_trg_char_ratio"]=src_trg_char_ratio

  if include_trg_src_char_ratio: #include trg/src len ratio
    trg_src_char_ratio=len(input_dict["trg"])/len(input_dict["src"])
    combined_vec.append(trg_src_char_ratio)
    debug_dict["include_trg_src_char_ratio"]=trg_src_char_ratio

  if include_freq: #include freq
    freq0=input_dict["freq"]
    combined_vec.append(freq0)
    debug_dict["include_freq"]=freq0
  if include_freq_log: #include freq log
    log_freq0=math.log(input_dict["freq"]+1)
    combined_vec.append(log_freq0)
    debug_dict["include_freq_log"]=log_freq0

  if include_context_trg_sim: #include cos similarity between trg and context
    context_vec=[]
    for c_tok in context_tokens_uq:
      if c_tok in cur_stop_tokens: continue
      cur_vec0=cur_vec_dict[c_tok]
      if sum(cur_vec0)==0: continue
      context_vec.append(cur_vec0)
    trg_vec=[]
    for t_tok in trg_tokens_uq:
      if t_tok in cur_stop_tokens: continue
      cur_vec0=cur_vec_dict[t_tok]
      if sum(cur_vec0)==0: continue
      trg_vec.append(cur_vec0)
    #print("context_vec",len(context_vec),"trg_vec",len(trg_vec))
    if context_vec==[] or trg_vec==[]: context_trg_cos_sim=-1
    else:
      mean_context_vec=np.array(context_vec).mean(axis=0)
      mean_trg_vec=np.array(trg_vec).mean(axis=0)
      context_trg_cos_sim=cos_sim(mean_trg_vec,mean_context_vec)
    combined_vec.append(context_trg_cos_sim)
    debug_dict["include_context_trg_sim"]=context_trg_cos_sim

  if include_prev_oh:
    cur_prev_oh=is_in_one_hot(prev_token0.lower().strip("_"),cur_special_tokens)
    combined_vec.extend(cur_prev_oh)
    debug_dict["include_prev_oh"]=context_trg_cos_sim

  if include_next_oh:
    cur_next_oh=is_in_one_hot(next_token0.lower().strip("_"),cur_special_tokens)
    combined_vec.extend(cur_next_oh)
    debug_dict["include_next_oh"]=cur_next_oh

  if include_edit_types_oh:
    cur_edit_type_str=identify_edit_type(src0,trg0)
    #print("cur_edit_type_str",cur_edit_type_str)
    cur_edit_type_oh=is_in_one_hot(cur_edit_type_str,edit_types)
    combined_vec.extend(cur_edit_type_oh)
    debug_dict["include_edit_types_oh"]=cur_edit_type_oh
  if output_debug_dict: return np.array(combined_vec), outcome0, debug_dict
  else: return np.array(combined_vec), outcome0

# def extract_ft_lb_OLD(input_dict,params={}): #extract features and labels from an input dict with context, src, trg, and outcome
#   chunk_size0=params.get("chunk_size",5)
#   cur_wv_model0=params.get("wv_model")
#   outcome_positive=params.get("outcome_positive",False)

#   include_context_trg_sim=ft_params.get("include_context_trg_sim",False)
#   include_freq=ft_params.get("include_freq",False)
#   include_freq_log=ft_params.get("include_freq_log",False)
#   edit_types=ft_params.get("edit_types",[])
#   cur_excluded_tokens=ft_params.get("excluded_tokens",[])

#   include_paren_check=ft_params.get("include_paren_check",False) #if surrounded by parentheses
#   include_start_check=ft_params.get("include_start_check",False) #if repl at the start of  
#   include_end_check=ft_params.get("include_end_check",False) #if repl at the end of sentence
#   include_src_trg_char_ratio=ft_params.get("include_src_trg_char_ratio",False) #check character ratio between src/trg
#   include_trg_src_char_ratio=ft_params.get("include_trg_src_char_ratio",False) #check character ratio between trg/src
#   include_src_trg_token_ratio=ft_params.get("include_src_trg_token_ratio",False) #check token ratio between src/trg
#   include_trg_src_token_ratio=ft_params.get("include_trg_src_token_ratio",False) #check token ratio between trg/src


#   context0=input_dict["context"]
#   src0=input_dict["src"]
#   trg0=input_dict["trg"]
#   outcome0=input_dict["outcome"]
#   if outcome_positive:
#     if outcome0==0: outcome0=0.5
#     elif outcome0==-1: outcome0=0
#   context_split=context0.split("|")
#   context_pre_str,context_after_str=context_split
#   context_pre_tokens=context_pre_str.strip().split(" ")
#   context_after_tokens=context_after_str.strip().split(" ")
#   src_tokens0=src0.split(" ")
#   trg_tokens0=trg0.split(" ")
#   context_pre_tokens=list(reversed(context_pre_tokens)) #reverse to make sure previous words are always in the same location
#   src_tokens0=pad_list(src_tokens0,chunk_size0)
#   trg_tokens0=pad_list(trg_tokens0,chunk_size0)
#   context_pre_tokens=pad_list(context_pre_tokens,chunk_size0)
#   context_after_tokens=pad_list(context_after_tokens,chunk_size0)

#   all_cur_tokens=list(set(context_pre_tokens+context_after_tokens+src_tokens0+trg_tokens0))
#   context_tokens_uq=list(set(context_pre_tokens+context_after_tokens))
#   trg_tokens_uq=list(set(trg_tokens0))
#   cur_vec_dict={}
#   empty_vec0=[0.]*wv_model.vector_size
#   for token0 in all_cur_tokens:
#     try: tok_vec0=wv_model.wv[token0].tolist()
#     except: tok_vec0= empty_vec0 #[0.]* #np.zeros(wv_model.vector_size,dtype=np.float32) #np.zeros(wv_model.vector_size)
#     cur_vec_dict[token0]=tok_vec0

#   # print("src_tokens0",src_tokens0)
#   # print("trg_tokens0",trg_tokens0)
#   # print("context_pre_tokens",context_pre_tokens)
#   # print("context_after_tokens",context_after_tokens)
#   combined_vec=[]
#   for item in [context_pre_tokens,context_after_tokens,src_tokens0,trg_tokens0]:
#     cur_vec=[]
#     for item_tok in item:
#       combined_vec.extend(cur_vec_dict.get(item_tok,empty_vec0))

#   if include_src_trg_char_ratio:
#     src_trg_char_ratio=len(input_dict["src"])/len(input_dict["trg"])
#     combined_vec.append(src_trg_char_ratio)
#   if include_trg_src_char_ratio:
#     trg_src_char_ratio=len(input_dict["trg"])/len(input_dict["src"])
#     combined_vec.append(trg_src_char_ratio)
#   if include_freq:
#     combined_vec.append(input_dict["freq"])
#   if include_freq_log:
#     combined_vec.append(math.log(input_dict["freq"]+1))

#   if include_context_trg_sim:
#     context_vec=[]
#     for c_tok in context_tokens_uq:
#       if c_tok in cur_excluded_tokens: continue
#       cur_vec0=cur_vec_dict[c_tok]
#       if sum(cur_vec0)==0: continue
#       context_vec.append(cur_vec0)
#     mean_context_vec=[]
#     trg_vec=[]
#     for t_tok in trg_tokens_uq:
#       if t_tok in cur_excluded_tokens: continue
#       cur_vec0=cur_vec_dict[t_tok]
#       if sum(cur_vec0)==0: continue
#       trg_vec.append(cur_vec0)
#     mean_trg_vec=[]
#     contect_trg_co_sim=cos_sim(mean_trg_vec,mean_trg_vec)
#     combined_vec.append(contect_trg_co_sim)


#     #vec0=get_chunk_vector(item,cur_wv_model0)
#     #combined_vec.extend(vec0)
#     #vec_array=np.array(vec0)
#   return np.array(combined_vec).ravel(), outcome0



# def get_chunk_vector(chunk,wv_model): #get a list of vectors from a space separated chunk of text
#   vec_list0=[]
#   split0=chunk.split(" ")
#   for token0 in split0:
#     try: tok_vec0=wv_model.wv[token0]
#     except: tok_vec0=np.zeros(wv_model.vector_size,dtype=np.float32) #np.zeros(wv_model.vector_size)
#     vec_list0.append(tok_vec0)
#   return np.array(vec_list0)

  

# #functions for extracting features from raw features
# def dict2ft_lb(data_dict,wv_model,ft_params={},outcome_key="outcome"): #should be "outcome" in next run
#   special_tokens_list=ft_params.get("token_list",[])
#   src_item_list=ft_params.get("src_item_list",[])
#   include_src_wv=ft_params.get("include_src_wv",False)
#   include_trg_wv=ft_params.get("include_trg_wv",False)
#   include_context_wv=ft_params.get("include_context_wv",False)
  
#   include_context_trg_sim=ft_params.get("include_context_trg_sim",False)

#   include_freq=ft_params.get("include_freq",False)
#   include_is_in_context=ft_params.get("include_is_in_context",False)
#   include_paren_check=ft_params.get("include_paren_check",False) #if surrounded by parentheses

#   include_prev_oh=ft_params.get("include_prev_oh",False)
#   include_next_oh=ft_params.get("include_next_oh",False)
#   include_trg_first_oh=ft_params.get("include_trg_first_oh",False)
#   include_trg_last_oh=ft_params.get("include_trg_last_oh",False)


#   label_list=[data_dict[outcome_key]]
#   feature_list=[]

#   main_keys=["src","trg","context"]
#   temp_vec_dict={}
#   for key0 in main_keys:
#     if key0=="src" and include_src_wv==False: continue
#     if key0=="trg" and include_trg_wv==False and include_context_trg_sim==False: continue
#     if key0=="context" and include_context_wv==False and include_context_trg_sim==False: continue

#     val0=data_dict[key0]
#     val_tokens=val0.split(" ")
#     val_tokens=[v for v in val_tokens if not v.lower().strip("_") in special_tokens_list]
#     try: val_vec=wv_model.wv.get_mean_vector(val_tokens)#.tolist()
#     except: val_vec=wv_model.wv.get_mean_vector([""])#.tolist()
#     temp_vec_dict[key0]=val_vec

#     if key0=="trg" and include_trg_wv==False: continue
#     if key0=="context" and include_context_wv==False: continue
#     feature_list.extend(val_vec.tolist())

#   if src_item_list!=[]:
#     src_oh=is_in_one_hot(data_dict["src"],src_item_list)
#     feature_list.extend(src_oh)

#   if include_context_trg_sim:
#     context_trg_sim0=-1
#     if sum(temp_vec_dict["trg"])!=0 and sum(temp_vec_dict["context"])!=0: 
#       context_trg_sim0=cos_sim(temp_vec_dict["trg"],temp_vec_dict["context"])
#     feature_list.append(context_trg_sim0)
#   if include_freq: feature_list.append(float(data_dict["freq"]))
#   if include_is_in_context: feature_list.append(data_dict["is_in_context"])

#   if include_paren_check:
#     paren_check0=0.
#     if data_dict["prev_token"].lower().strip("_")=="(" and data_dict["next_token"].lower().strip("_")==")":paren_check0=1.
#     feature_list.append(paren_check0)

#   if include_prev_oh:
#     prev_oh=is_in_one_hot(data_dict["prev_token"].lower().strip("_"),special_tokens_list)
#     feature_list.extend(prev_oh)

#   if include_next_oh:
#     next_oh=is_in_one_hot(data_dict["next_token"].lower().strip("_"),special_tokens_list)
#     feature_list.extend(next_oh)
#   trg_split=data_dict["trg"].split(" ")
#   if include_trg_first_oh:
#     first_trg_word=trg_split[0].strip("_").lower()
#     first_trg_oh=is_in_one_hot(first_trg_word,special_tokens_list)
#     feature_list.extend(first_trg_oh)

#   if include_trg_last_oh:
#     last_trg_word=trg_split[-1].strip("_").lower()
#     last_trg_oh=is_in_one_hot(last_trg_word,special_tokens_list)
#     feature_list.extend(first_trg_oh)

#   return feature_list,label_list




def is_in_one_hot(item0,list0):
  one_hot0=[0.]*len(list0)
  if item0 in list0:
    index_i=list0.index(item0)
    one_hot0[index_i]=1.
  return one_hot0

def is_valid_repl(src_repl_str0,trg_repl_str0,excluded_words=all_excluded):
  #is_valid=True
  if src_repl_str0=="" or trg_repl_str0=="": return False
  if src_repl_str0.lower()== trg_repl_str0.lower(): return False
  if src_repl_str0[0].isdigit() or trg_repl_str0[0].isdigit(): return False
  src_check=re.sub("[\d\W]","",src_repl_str0)
  trg_check=re.sub("[\d\W]","",trg_repl_str0)
  if src_check=="" or trg_check=="": return False
  if general.is_punct(src_repl_str0.strip("_")): return False
  if general.is_punct(trg_repl_str0.strip("_")): return False
  # src_repl_tokens0=src_repl_str0.split(" ")  
  # src_check_tokens=[v for v in src_repl_tokens0 if not general.is_punct(v.strip("_")) in excluded_words and not is_website(v) and not is_un_symbol(v)]
  # if src_check_tokens==[]: return False
  # trg_repl_tokens0=trg_repl_str0.split(" ")
  # trg_check_tokens=[v for v in trg_repl_tokens0 if not general.is_punct(v.strip("_")) in excluded_words and not is_website(v) and not is_un_symbol(v)]
  # if trg_check_tokens==[]: return False
  return True



def extract_repl_instances(src_tokens,trg_tokens,first_repl_dict,params={}): #check each possible replacement for context and other features
  window_size=params.get("window_size",5)
  null_repl_outcome=params.get("null_repl_outcome",0) #default value for no replacment (src=trg)
  include_null_repl=params.get("include_null_repl",False) #whether to include null replacments or not

  src_tokens=general.add_padding(src_tokens)
  trg_tokens=general.add_padding(trg_tokens)
  final_repl_list=[]
  if trg_tokens!=[]: edit_list=compare_repl(src_tokens,trg_tokens) #if we have both src and trg
  else: edit_list=[] #if we have only src
  
  possible_repl_list=get_possible_replacements(src_tokens,first_repl_dict)
  actual_repl_dict={}
  actual_repl_span_list=[]
  for el in edit_list:
    match_type,repl_src_token0,repl_trg_token0,src_span0,trg_span0=el
    if match_type=="equal": continue
    repl_src0=" ".join(repl_src_token0)
    repl_trg0=" ".join(repl_trg_token0)
    #a_key=(repl_src0,src_span0) #actual replacement key
    actual_repl_dict[src_span0]=repl_trg0
    actual_repl_span_list.append((repl_src0,repl_trg0,src_span0))
  p_ft_dict_list=[]
  used_span_trg_dict={}
  for repl_src0,trg_repl_dict0,span0 in possible_repl_list:

    #p_key=(repl_src0,span0)
    actual_trg_repl0=actual_repl_dict.get(span0) #check the correspodning target (repl) for current span
    temp_ft_dict=extract_context_ft(src_tokens,span0,window_size=window_size)
    if temp_ft_dict["context"]=='|': continue

    temp_ft_dict["src"]=repl_src0
    temp_ft_dict["span"]=span0
    
    #context0=temp_ft_dict.get("context","")
    if include_null_repl: trg_repl_dict0[repl_src0]=0 #copy src into trg - null edit - freq irrelevant
    apply_null=True #null replacement 
    
    if actual_trg_repl0!=None: apply_null=False #trg_repl_dict0[repl_src0]=1 
    

    for trg_repl0,freq0 in trg_repl_dict0.items():
      used_span_trg_dict[(span0,trg_repl0)]=True
      temp_ft_dict1=copy.deepcopy(temp_ft_dict)
      if temp_ft_dict1["context"]=='|': continue

      temp_ft_dict1["trg"]=trg_repl0
      temp_ft_dict1["freq"]=freq0
      outcome=0
      if apply_null and trg_repl0==repl_src0: outcome=null_repl_outcome
      if trg_repl0==actual_trg_repl0: outcome=1
      temp_ft_dict1["outcome"]=outcome
      final_repl_list.append(temp_ft_dict1)
  if trg_tokens!=[]: #going over unprocessed actual edits - to get more positive instances
    for repl_src0,repl_trg0,repl_span0 in actual_repl_span_list:
      used_check=used_span_trg_dict.get((repl_span0,repl_trg0),False)
      if used_check==True: continue
      is_valid_repl_check=is_valid_repl(repl_src0,repl_trg0)
      if is_valid_repl_check==False: continue
      temp_ft_dict2=extract_context_ft(src_tokens,repl_span0,window_size=window_size,input_ft_dict={})
      temp_ft_dict2["src"]=repl_src0
      temp_ft_dict2["trg"]=repl_trg0
      temp_ft_dict2["span"]=repl_span0
      temp_ft_dict2["freq"]=0
      temp_ft_dict2["outcome"]=1
      final_repl_list.append(temp_ft_dict2)

  return final_repl_list


def get_span_repl_instances(src_tokens,trg_tokens,first_repl_dict,params={}):
  repl_list0=extract_repl_instances(src_tokens,trg_tokens,first_repl_dict,params=params)
  repl_list0.sort(key=lambda x:x["span"])
  grouped=[(key,list(group)) for key,group in groupby(repl_list0,lambda x:x["span"])]
  span_repl_dict=dict(iter(grouped))
  return span_repl_dict



# def extract_repl_instances(src_tokens,trg_tokens,first_repl_dict,window_size=5): #check each possible replacement for context and other features
#   src_tokens=general.add_padding(src_tokens)
#   trg_tokens=general.add_padding(trg_tokens)
#   final_repl_list=[]
#   if trg_tokens!=[]: edit_list=compare_repl(src_tokens,trg_tokens) #if we have both src and trg
#   else: edit_list=[] #if we have only src
  
#   possible_repl_list=get_possible_replacements(src_tokens,first_repl_dict)
#   actual_repl_dict={}
#   actual_repl_span_list=[]
#   for el in edit_list:
#     match_type,repl_src_token0,repl_trg_token0,src_span0,trg_span0=el
#     if match_type=="equal": continue
#     repl_src0=" ".join(repl_src_token0)
#     repl_trg0=" ".join(repl_trg_token0)
#     #a_key=(repl_src0,src_span0) #actual replacement key
#     actual_repl_dict[src_span0]=repl_trg0
#     actual_repl_span_list.append((repl_src0,repl_trg0,src_span0))
#   p_ft_dict_list=[]
#   used_span_trg_dict={}
#   for repl_src0,trg_repl_dict0,span0 in possible_repl_list:
#     #p_key=(repl_src0,span0)
#     actual_trg_repl0=actual_repl_dict.get(span0) #check the correspodning target (repl) for current span
#     temp_ft_dict=extract_context_ft(src_tokens,span0,window_size=window_size)
#     temp_ft_dict["src"]=repl_src0
#     temp_ft_dict["span"]=span0
    
#     #context0=temp_ft_dict.get("context","")
#     trg_repl_dict0[repl_src0]=0 #copy src into trg - null edit - freq irrelevant
#     apply_null=True #null replacement 
    
#     if actual_trg_repl0!=None: apply_null=False #trg_repl_dict0[repl_src0]=1 
    

#     for trg_repl0,freq0 in trg_repl_dict0.items():
#       used_span_trg_dict[(span0,trg_repl0)]=True
#       temp_ft_dict1=copy.deepcopy(temp_ft_dict)
#       temp_ft_dict1["trg"]=trg_repl0
#       temp_ft_dict1["freq"]=freq0
#       outcome=0
#       if apply_null and trg_repl0==repl_src0: outcome=1
#       if trg_repl0==actual_trg_repl0: outcome=1
#       temp_ft_dict1["outcome"]=outcome
#       final_repl_list.append(temp_ft_dict1)
#   if trg_tokens!=[]: #going over unprocessed actual edits - to get more positive instances
#     for repl_src0,repl_trg0,repl_span0 in actual_repl_span_list:
#       #print("????",repl_src0,repl_trg0,repl_span0)
#       if used_span_trg_dict.get((repl_span0,repl_trg0),False): continue
#       is_valid_repl_check=is_valid_repl(repl_src0,repl_trg0)
#       if is_valid_repl_check==False: continue
#       # if repl_src0=="" or repl_trg0=="": continue
#       # if repl_src0.lower()== repl_trg0.lower(): continue
#       # if repl_src0[0].isdigit() or repl_trg0[0].isdigit(): continue
#       # src_check=re.sub("[\d\W]","",repl_src0)
#       # trg_check=re.sub("[\d\W]","",repl_trg0)
#       # if src_check=="" or trg_check=="": continue
#       temp_ft_dict2=extract_context_ft(src_tokens,repl_span0,window_size=window_size,input_ft_dict={})
#       temp_ft_dict2["src"]=repl_src0
#       temp_ft_dict2["trg"]=repl_trg0
#       temp_ft_dict2["span"]=repl_span0
#       temp_ft_dict2["freq"]=0
#       temp_ft_dict2["outcome"]=1
#       final_repl_list.append(temp_ft_dict2)

#   return final_repl_list



# def extract_repl_instances_OLD(src_tokens,trg_tokens,first_repl_dict,window_size=5): #check each possible replacement for context and other features
#   src_tokens=general.add_padding(src_tokens)
#   trg_tokens=general.add_padding(trg_tokens)
#   final_repl_list=[]
#   if trg_tokens!=[]: edit_list=compare_repl(src_tokens,trg_tokens) #if we have both src and trg
#   else: edit_list=[] #if we have only src
  
#   possible_repl_list=get_possible_replacements(src_tokens,first_repl_dict)
#   actual_repl_dict={}
#   actual_repl_span_list=[]
#   for el in edit_list:
#     match_type,repl_src_token0,repl_trg_token0,src_span0,trg_span0=el
#     if match_type=="equal": continue
#     repl_src0=" ".join(repl_src_token0)
#     repl_trg0=" ".join(repl_trg_token0)
#     #a_key=(repl_src0,src_span0) #actual replacement key
#     actual_repl_dict[src_span0]=repl_trg0
#     actual_repl_span_list.append((repl_src0,repl_trg0,src_span0))
#   p_ft_dict_list=[]
#   used_span_trg_dict={}
#   for repl_src0,trg_repl_dict0,span0 in possible_repl_list:
#     #p_key=(repl_src0,span0)
#     actual_trg_repl0=actual_repl_dict.get(span0)
#     temp_ft_dict=extract_context_ft(src_tokens,span0,window_size=window_size)
#     temp_ft_dict["src"]=repl_src0
#     temp_ft_dict["span"]=span0
    
#     #context0=temp_ft_dict.get("context","")
#     trg_repl_dict0[repl_src0]=0 #copy src into trg - null edit - freq irrelevant
#     for trg_repl0,freq0 in trg_repl_dict0.items():
#       used_span_trg_dict[(span0,trg_repl0)]=True
#       temp_ft_dict1=copy.deepcopy(temp_ft_dict)
#       temp_ft_dict1["trg"]=trg_repl0
#       temp_ft_dict1["freq"]=freq0
#       outcome=-1
#       if trg_repl0==repl_src0: outcome=0
#       elif trg_repl0==actual_trg_repl0: outcome=1
#       temp_ft_dict1["outcome"]=outcome
#       final_repl_list.append(temp_ft_dict1)
#   if trg_tokens!=[]: #going over unprocessed actual edits - to get more positive instances
#     for repl_src0,repl_trg0,repl_span0 in actual_repl_span_list:
#       #print("????",repl_src0,repl_trg0,repl_span0)
#       if used_span_trg_dict.get((repl_span0,repl_trg0),False): continue
#       if repl_src0=="" or repl_trg0=="": continue
#       if repl_src0.lower()== repl_trg0.lower(): continue
#       if repl_src0[0].isdigit() or repl_trg0[0].isdigit(): continue
#       src_check=re.sub("[\d\W]","",repl_src0)
#       trg_check=re.sub("[\d\W]","",repl_trg0)
#       if src_check=="" or trg_check=="": continue
#       temp_ft_dict2=extract_context_ft(src_tokens,repl_span0,window_size=window_size,input_ft_dict={})
#       temp_ft_dict2["src"]=repl_src0
#       temp_ft_dict2["trg"]=repl_trg0
#       temp_ft_dict2["span"]=repl_span0
#       temp_ft_dict2["freq"]=0
#       temp_ft_dict2["outcome"]=1
#       final_repl_list.append(temp_ft_dict2)

#   return final_repl_list




# def extract_repl_raw_features_labels_OLD(src_tokens,trg_tokens,first_repl_dict,window_size=5): #check each possible replacement for context and other features
#   #src_tokens0,trg_tokens0=src_tokens,trg_tokens
#   #possible_replacements=get_possible_replacements(src_tokens,first_repl_dict)
#   final_repl_list=[]
#   edit_list=compare_repl(src_tokens,trg_tokens)
#   possible_repl_list=get_possible_replacements(src_tokens,first_repl_dict)
#   actual_repl_dict={}
#   for el in edit_list:
#     match_type,repl_src_token0,repl_trg_token0,src_span0,trg_span0=el
#     if match_type=="equal": continue
#     repl_src0=" ".join(repl_src_token0)
#     repl_trg0=" ".join(repl_trg_token0)
#     a_key=(repl_src0,src_span0) #actual replacement key
#     actual_repl_dict[a_key]=repl_trg0

#   p_ft_dict_list=[]
#   for repl_src0,trg_repl_dict0,span0 in possible_repl_list:
#     #if repl_src0!="UK": continue
#     p_key=(repl_src0,span0)
#     actual_trg_repl0=actual_repl_dict.get(p_key)
#     temp_ft_dict=extract_context_ft(src_tokens,span0,window_size=window_size)
#     temp_ft_dict["src"]=repl_src0
#     context0=temp_ft_dict.get("context","")
#     context_words_lower0=[v.lower() for v in context0.split(" ") if v!="|"]

#     # print("repl_src0,trg_repl_dict0,span0",repl_src0,trg_repl_dict0,span0)
#     # print(temp_ft_dict)
#     # print("actual_trg_repl0",actual_trg_repl0)
#     for trg_repl0,freq0 in trg_repl_dict0.items():
#       temp_ft_dict1=copy.deepcopy(temp_ft_dict)
#       temp_ft_dict1["trg"]=trg_repl0
#       temp_ft_dict1["freq"]=freq0
#       outcome=0
#       is_in_context=0
#       if trg_repl0==actual_trg_repl0: outcome=1

#       repl_trg_tokens_lower=trg_repl0.lower().split()
#       if general.is_in(repl_trg_tokens_lower,context_words_lower0): is_in_context=1
#       temp_ft_dict1["outcome"]=outcome
#       temp_ft_dict1["is_in_context"]=is_in_context
#       #print(temp_ft_dict1)
#       final_repl_list.append(temp_ft_dict1)
#   return final_repl_list

def extract_context_ft(src_tokens,src_repl_span,window_size=5,input_ft_dict={}):
  #temp_ft_dict={}
  #p_repl_src_tokens0,p_repl_trg_tokens0,freq0=triple0
  # repl_src0=" ".join(repl_src_tokens)
  # repl_trg0=" ".join(repl_trg_tokens)

  prev_token,next_token="",""
  x0,x1=src_repl_span
  #full_window=src_tokens0[max(0,x0-window_size):x1+window_size+1]
  prev_tokens=src_tokens[max(0,x0-window_size):x0]
  next_tokens=src_tokens[x1+1:x1+window_size+1]
  #prev_tokens=[v for v in prev_tokens if v.strip("_")]

  full_window=prev_tokens+["|"]+ next_tokens
  # if x0>0: prev_token=src_tokens[x0-1]
  # if x1<len(src_tokens)-1: next_token=src_tokens[x1+1]

  input_ft_dict["context"]=" ".join(full_window)
  # input_ft_dict["prev_token"]=prev_token
  # input_ft_dict["next_token"]=next_token
  return input_ft_dict

#==================================



# def is_un_symbol(str0):
#   out=False
#   if str0[0].isupper() and str0[-1].isdigit() and "/" in str0: out=True
#   return out

# def is_website(str0):
#     out=False
#     if str0.lower().startswith("http:") or str0.lower().startswith("https:"): out=True
#     return out




def unescape(text_with_html_entities):
  if sys.version_info[0]==3:
    import html
    return html.unescape(text_with_html_entities)
  else:
    import HTMLParser
    return HTMLParser.HTMLParser().unescape(text_with_html_entities)

#from code_utils.general import *
#from code_utils.extract_docx import *

def simple_hash(input_str,size=10):
  input_str=input_str.encode('utf-8')
  return hashlib.md5(input_str).hexdigest()[:size]

def str2key(str0):
  str0=htmlp.unescape(str0)
  str0=str0.strip()
  str0=re.sub("\W+","_",str0)
  return str0

def tsv2dict(tsv_fpath0,skip_first=False):
  out_dict={}
  fopen0=open(tsv_fpath0)
  for line in fopen0:
    line_split=line.strip("\n\r\t").split("\t")
    if len(line_split)<2: continue
    key=str2key(line_split[0])
    out_dict[key]=line_split[1]
  return out_dict


#2 June 2023
class docx:
  def __init__(self,docx_fpath,keep_copy=True): #openning the docx file, by unzipping it
    self.TEMP_DOCX = docx_fpath
    self.closed=False
    self.COPY_DOCX = docx_fpath+"2"
    shutil.copy(self.TEMP_DOCX, self.COPY_DOCX) #keep a temp copy of out file, just in case
    self.file_extension="."+docx_fpath.split(".")[-1]
    self.TEMP_ZIP = docx_fpath.replace(self.file_extension,".zip")
    self.TEMP_FOLDER = docx_fpath.replace(self.file_extension,"")
    if os.path.exists(self.TEMP_ZIP):
      os.remove(self.TEMP_ZIP)
    if os.path.exists(self.TEMP_FOLDER):
      shutil.rmtree(self.TEMP_FOLDER)
    os.rename(self.TEMP_DOCX, self.TEMP_ZIP) #rename the original docx to zip extension
    # unzip file zip to specific folder
    z_open=zipfile.ZipFile(self.TEMP_ZIP, 'r')
    z_open.extractall(self.TEMP_FOLDER)
    z_open.close()
    os.rename(self.COPY_DOCX, self.TEMP_DOCX) #keep the original file
  def save_as(self,out_fpath):
    if os.path.exists(out_fpath): #remove any of these if already exists
      os.remove(out_fpath)
    #self.OUT_ZIP = out_fpath.replace(".docx",".zip")
    #shutil.make_archive(self.OUT_ZIP, 'zip', self.TEMP_FOLDER)
    shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
    os.rename(self.TEMP_ZIP, out_fpath)
  def extract_paras(self,cat_file_path=""): 
    self.paras=[]
    self.para_path_dict={}
    if self.TEMP_DOCX.lower().endswith(".docx"): main_dir="word"
    if self.TEMP_DOCX.lower().endswith(".pptx"): main_dir="ppt/slides"
    if self.TEMP_DOCX.lower().endswith(".xlsx"): main_dir="xl"

    extracted_dir=os.path.join(self.TEMP_FOLDER, main_dir)
    for xml_fname in os.listdir(extracted_dir):
      #print(xml_fname)
      skip_file=True
      if xml_fname in ["document.xml", "footnotes.xml","endnotes.xml","sharedStrings.xml"]: skip_file=False
      if xml_fname.startswith("slide"): skip_file=False
      if xml_fname.startswith("sheet"): skip_file=False
      if xml_fname.startswith("header"): skip_file=False
      if xml_fname.startswith("footer"): skip_file=False
      if skip_file: continue
      # if xml_fname in ["document.xml", "footnotes.xml","endnotes.xml"] or xml_fname.startswith("header") or xml_fname.startswith("footer"): pass
      # else: continue
      #if not xml_fname=="document.xml" and not xml_fname.startswith("header") and not xml_fname.startswith("footer"): continue
      cur_xml_path=os.path.join(extracted_dir,xml_fname)
      with open(cur_xml_path) as fopen:
        xml_content=fopen.read()
      xml_dom_obj=web_lib.DOM(xml_content)
      cur_tag_name="w:p" #xml tag for docx files
      if self.TEMP_DOCX.lower().endswith(".pptx"): cur_tag_name="a:p"
      
      cur_paras=xml_dom_obj.get_el_by_tag_name(cur_tag_name)
      tmp_xml_path=os.path.join(main_dir,xml_fname)
      for para0 in cur_paras:
        para_hash=simple_hash(para0)
        cur_para_key="%s|%s"%(tmp_xml_path,para_hash)
        self.paras.append((cur_para_key,para0))
        self.para_path_dict[cur_para_key]=para0
      
      # cur_wps=get_xml_elements(xml_content,el_name=cur_tag_name)
      # for i0,wp_xml in enumerate(cur_wps):
      #   #wp_text=get_wr_text(wp_xml)
      #   wp_text=get_el_text(wp_xml)        
      #   para_obj=para()
      #   para_obj.path=cur_xml_path
      #   para_obj.xml=wp_xml
      #   para_obj.text=wp_text
      #   para_obj.i=i0
      #   para_obj.tag_name=cur_tag_name        
      #   found_ids=re.findall('paraId="(.+?)"',wp_xml) 
      #   if found_ids: para_obj.id=  found_ids[0]
      #   self.paras.append(para_obj)
      # if cat_file_path!="": #save paragraphs with their info to cat file
      #   cat_fopen=open(cat_file_path,"w")
      #   for p_obj in self.paras:
      #     cur_text=p_obj.text.replace("\t"," <tab> ").replace("\n"," <br> ")
      #     json_obj={}
      #     json_obj["path"]=p_obj.path
      #     json_obj["i"]=p_obj.i
      #     json_obj["id"]=p_obj.id
      #     json_obj["tag_name"]=p_obj.tag_name          
      #     json_obj["text"]=cur_text
      #     json_obj_str=json.dumps(json_obj) 
      #     line=json_obj_str+"\n"
      #     #line="%s\t%s\t%s\t%s\n"%(p_obj.path,p_obj.i,p_obj.id,cur_text)
      #     cat_fopen.write(line)
      #   cat_fopen.close()

    return self.paras,self.para_path_dict
  

  def update_tbl_rtl(self):
    extracted_dir=os.path.join(self.TEMP_FOLDER, "word")
    cur_xml_path=os.path.join(extracted_dir,"document.xml")
    fopen_read=open(cur_xml_path)
    xml_content=fopen_read.read()
    fopen_read.close()
    xml_content=xml_content.replace("<w:tblPr>","<w:tblPr><w:bidiVisual/>")
    xml_content=xml_content.replace("<w:lang ","<w:rtl/><w:lang ")

    
    fopen_write=open(cur_xml_path, "wb")
    fopen_write.write(xml_content)
    fopen_write.close()


  def close(self):
    self.closed=True
    os.remove(self.TEMP_ZIP)
    shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
    os.rename(self.TEMP_ZIP, self.TEMP_DOCX)
    shutil.rmtree(self.TEMP_FOLDER)


def get_ndiff(str0,str1):
  cur_ndiff=sum([i[0] != ' '  for i in difflib.ndiff(str0, str1)])/2
  return cur_ndiff

#Editing project
def identify_edit_type(src_str,trg_str,max_ndiff=2,excluded_tokens=all_excluded):
  key=src_str
  sub_key=trg_str
  no_dash_key_str="".join([v for v in key.split(" ") if v.strip("_")!="-"])
  no_dash_subkey_str="".join([v for v in sub_key.split(" ") if v.strip("_")!="-"])
  cur_ndiff0=get_ndiff(src_str,trg_str)

  edit_type="other" #["other","acronym","acronym-s","capitalization","compunding","hyphenation"]
  if src_str.replace("s","z")==trg_str: edit_type="s-z"
  elif src_str.replace("or","our")==trg_str: edit_type="or-our"
  elif re.sub('er$', 're', src_str)==trg_str or re.sub('ers$', 'res', src_str)==trg_str: edit_type="er-re"  
  elif re.sub('or$', 'er', src_str)==trg_str or re.sub('ors$', 'ers', src_str)==trg_str: edit_type="er-re"    
  elif key.lower()==sub_key.lower():
    edit_type="capitalization"
  elif src_str.isdigit() and re.findall("\d+",trg_str)==[]:
    edit_type="number"
  elif src_str[0].isdigit() and len(src_str.split(" "))==1 and src_str[-2:].lower() in ["st","nd","rd","th"]  and re.findall("\d+",trg_str)==[]:
    edit_type="number"

  elif general.norm_unicode(src_str)==general.norm_unicode(trg_str): edit_type="unicode" #deal with accents, diacrtiics and other unicode elements
  elif len(re.split("\W+",src_str))==1 and len(re.split("\W+",trg_str))==1: #only one word src/trg
    if src_str in excluded_tokens or trg_str in excluded_tokens or src_str[0].isdigit() or src_str[-1].isdigit() or trg_str[0].isdigit() or trg_str[-1].isdigit(): 
        edit_type="spelling-excluded"
    elif stemmer.stem(src_str)==stemmer.stem(trg_str): edit_type="inflection" #should use lemmas - but pattern is unstable
    elif cur_ndiff0<max_ndiff: edit_type="spelling"
    else:  edit_type="different-word"
    
  elif key.isupper():
    if key=="".join([v for v in sub_key if v.isupper()]) or key.lower()=="".join([v[0].lower() for v in sub_key.split(" ")]):
      edit_type="acronym"
  elif key[-1]=="s" and len(key)>2 and key[:-1].isupper(): #SDGs IEDs
    if key[:-1]=="".join([v for v in sub_key if v.isupper()]) or key[:-1].lower()=="".join([v[0].lower() for v in sub_key.split(" ")]):
      edit_type="acronym-s"
  elif key.replace(" ","")==sub_key.replace(" ",""):
    edit_type="compunding"
  elif no_dash_key_str==no_dash_subkey_str:
    edit_type="hyphenation"
  return edit_type

#2 June 2023
def get_edit_info(para_content):
  para_content=para_content.replace("<w:br/>","\n")
  para_content=para_content.replace("<w:tab/>","\t")
  para_content=para_content.replace("<w:noBreakHyphen/>","-")
  #<w:footnoteReference w:customMarkFollows="1" w:id="2"/>
  #<w:footnoteReference w:id="3"/>
  

  tags=list(re.finditer('<[^<>]*?>|\<\!\-\-.+?\-\-\>', para_content))
  open_tags=[""]
  tag_counter_dict={}
  start_i=0
  last_open_tag_str=""
  is_inserted=False
  is_deleted=False
  original_text0,final_text0="",""
  edit_segments0=[]
  for ti_, t in enumerate(tags):
    tag_str,tag_start,tag_end=t.group(0), t.start(), t.end()
    tag_str_lower=tag_str.lower()
    tag_name=re.findall(r'</?(.+?)[\s>]',tag_str_lower)[0]
    tag_type=""
    if tag_str.startswith('</'): tag_type="closing"
    elif tag_str.startswith('<!'): tag_type="comment"
    elif tag_str_lower.endswith('/>') or tag_name in ["input","link","meta","img","br","hr"]: tag_type="s" #standalone
    #elif tag_name in ["wp:posOffset"]: tag_type="exclude"
    else: tag_type="opening"

    #if tag_type=="exclude": continue

    if tag_name=="w:ins" and tag_type=="opening": is_inserted=True
    if tag_name=="w:ins" and tag_type=="closing": is_inserted=False
    if tag_name=="w:del" and tag_type=="opening": is_deleted=True
    if tag_name=="w:del" and tag_type=="closing": is_deleted=False

    inter_text=para_content[start_i:tag_start] #intervening text since last tag
    #if inter_text!="": print("inter_text",[inter_text],"last_open_tag_str",last_open_tag_str)
    #print(tag_name, inter_text,"is_inserted",is_inserted,"is_deleted",is_deleted)
    if last_open_tag_str.startswith("w:"):
      if not is_inserted: original_text0+=inter_text
      if not is_deleted: final_text0+=inter_text
      seg_class="edited_same"
      if is_inserted: seg_class="edited_inserted"
      if is_deleted: seg_class="edited_deleted"
      if inter_text!="":edit_segments0.append((inter_text,seg_class))
    start_i=tag_end
    if tag_type=="opening": last_open_tag_str=tag_name
  #edit_segments_grouped=edit_segments0[(key,"".join([v[0] for v in list(group)])) for key,group in groupby(edit_segments0,lambda x,x[0])]
  edit_segments_grouped0=[(key,"".join([v[0] for v in list(group)])) for key,group in groupby(edit_segments0,lambda x:x[1])]
  edited_text_html0=""
  for a,b in edit_segments_grouped0:
    if a=="edited_inserted": edited_text_html0+='<ins>'+b+'</ins>'
    elif a=="edited_deleted": edited_text_html0+='<del>'+b+'</del>'
    else: edited_text_html0+=b
  original_text0=general.unescape(original_text0)
  final_text0=general.unescape(final_text0)
  return original_text0,final_text0, edited_text_html0 


#7 july
def get_edit_html_OLD(tokens1,tokens2):
  edit_list=get_seq_edits(tokens1,tokens2)
  final_str_items=[]
  for edit_type0,chunk0 in edit_list:
    cur_chunk_str=general.de_tok2str(chunk0)
    cur_chunk_str=safe_xml(cur_chunk_str)
    if edit_type0=="delete": final_str_items.append('<del>%s</del>'%cur_chunk_str)
    elif edit_type0=="insert": final_str_items.append('<ins>%s</ins>'%cur_chunk_str)
    else: final_str_items.append(cur_chunk_str)
  final_str=" ".join(final_str_items)
  return final_str


#13 Sept
def get_edits_pairs(tokens1,tokens2):
  match_obj=SequenceMatcher(None,tokens1,tokens2)
  final_list=[]
  seq_pair_list=[]
  for a in match_obj.get_opcodes():
    match_type,x0,x1,y0,y1=a
    from_seq0=tokens1[x0:x1]
    to_seq0=tokens2[y0:y1]
    seq_pair_list.append((from_seq0,to_seq0))
  return seq_pair_list

def get_edit_html(tokens1,tokens2,main_class_name): #edit_pairs2html_spans: identify spans of edits for two sequences of words, include span ids and classes to work with javascript
  tokens1=general.remove_padding(tokens1)
  tokens2=general.remove_padding(tokens2)  
  cur_seq_pairs=get_edits_pairs(tokens1,tokens2)
  chunks=[]
  for pair0 in cur_seq_pairs:
    from_seq0,to_seq0=pair0
    if from_seq0==to_seq0:
      cur_chunk=general.de_tok2str(to_seq0)
    else:
      cur_id=general.gen_id(4)
      from_str=general.de_tok2str(from_seq0)
      to_str=general.de_tok2str(to_seq0)
      cur_chunk=f'<span id="{cur_id}" class="replacement {main_class_name} tentative"><span class="from_repl">{from_str}</span> <span class="to_repl">{to_str}</span></span>'
    chunks.append(cur_chunk)
  return " ".join(chunks)




# def get_edit_html_NEW(tokens1,tokens2,use_spans=True):
#   edit_list=get_seq_edits(tokens1,tokens2)
#   final_str_items=[]
#   for edit_type0,chunk0 in edit_list:
#     cur_chunk_str=general.de_tok2str(chunk0)
#     cur_chunk_str=safe_xml(cur_chunk_str)
#     if edit_type0=="delete": final_str_items.append('<del>%s</del>'%cur_chunk_str)
#     elif edit_type0=="insert": final_str_items.append('<ins>%s</ins>'%cur_chunk_str)
#     else: final_str_items.append(cur_chunk_str)
#   final_str=" ".join(final_str_items)
#   return final_str



def safe_xml(txt):
  txt=txt.replace("&","&amp;")
  txt=txt.replace("<","&lt;")
  txt=txt.replace(">","&gt;")
  return txt  


def get_seq_replace(tokens1,tokens2):
  match_obj=SequenceMatcher(None,tokens1,tokens2)
  final_list=[]
  for a in match_obj.get_opcodes():
    match_type,x0,x1,y0,y1=a
    deleted_tokens,inserted_tokens=[],[]
    if match_type=="delete":
      deleted_tokens=tokens1[x0:x1]
      #final_list.append(("deleted",tokens1[x0:x1]))
    if match_type=="equal":
      #final_list.append(("equal",tokens1[x0:x1]))
      pass
    if match_type=="replace":
      deleted_tokens=tokens1[x0:x1]
      inserted_tokens=tokens2[y0:y1]
      #final_list.append(("delete",tokens1[x0:x1]))
      #final_list.append(("insert",tokens2[y0:y1]))
    if match_type=="insert":
      #final_list.append(("insert",tokens2[y0:y1]))
      inserted_tokens=tokens2[y0:y1]
    final_list.append((match_type,deleted_tokens,inserted_tokens,(x0,x1),(y0,y1)))
  return final_list


def get_seq_edits(tokens1,tokens2):
  match_obj=SequenceMatcher(None,tokens1,tokens2)
  final_list=[]
  for a in match_obj.get_opcodes():
    match_type,x0,x1,y0,y1=a
    if match_type=="delete":
      final_list.append(("deleted",tokens1[x0:x1]))
    if match_type=="equal":
      final_list.append(("equal",tokens1[x0:x1]))
    if match_type=="replace":
      final_list.append(("delete",tokens1[x0:x1]))
      final_list.append(("insert",tokens2[y0:y1]))
    if match_type=="insert":
      final_list.append(("insert",tokens2[y0:y1]))
  return final_list


def compare_repl(tokens1,tokens2,window_size=5): #make all changes as replacements - add sentence boundaries for whole segment edits
  tokens1=general.add_padding(tokens1)
  tokens2=general.add_padding(tokens2)
  match_obj=SequenceMatcher(None,tokens1,tokens2)
  final_list=[]
  for a in match_obj.get_opcodes():
    match_type,x0,x1,y0,y1=a
    if match_type in ["insert","delete"]: #for insertaions/deletions, get preceding+following token to make it a replacement
      x0=x0-1
      x1=x1+1
      y0=y0-1
      y1=y1+1
      #match_type="replace"
  
    old0=tokens1[x0:x1]
    new0=tokens2[y0:y1]
    span_old0=(x0,x1-1) #adjust the end of the span to reflect the index of the last token
    span_new0=(y0,y1-1)
    final_list.append((match_type,old0,new0,span_old0,span_new0))
  return final_list


def get_corr_freq_dict(file_gen): #iterting file lines, each line is json dict, with keys "src","trg"
  corr_dict0={}
  for line0 in file_gen:
    line_dict0=json.loads(line0)
    src0=line_dict0["src"]
    trg0=line_dict0["trg"]
    temp_dict=corr_dict0.get(src0,{})
    temp_dict[trg0]=temp_dict.get(trg0,0)+1
    corr_dict0[src0]=temp_dict
  return corr_dict0
  # items=list(corr_dict.items())
  # items.sort(key=lambda x:-sum(x[1].values()))
def filter_freq_dict(freq_dict,min_freq=2,exclude_casing=True,exclude_punct=True):
  new_freq_dict={}
  for key,val_dict in freq_dict.items():
    temp_val_dict={}
    for sub_key,freq in val_dict.items():
      if min_freq!=None and freq<min_freq: continue
      if exclude_casing and key.lower()==sub_key.lower(): continue
      if exclude_punct and general.is_punct(key.strip("_")): continue
      temp_val_dict[sub_key]=freq
    if temp_val_dict!={}: new_freq_dict[key]=temp_val_dict
  return new_freq_dict

def get_first_freq_dict(freq_dict):
  list_with_first=[]
  for a,b in freq_dict.items():
    first=a.split(" ")[0]
    list_with_first.append((first,(a,b)))
  list_with_first.sort()
  grouped0=[(key,[v[1] for v in list(group)]) for key,group in groupby(list_with_first,lambda x:x[0])]
  return dict(iter(grouped0))


def get_possible_replacements(sent_tokens,first_repl_dict,exclude_sent_start=True): #use the repl dict (with keys as first word, value is a list of triplets (repl_src,repl_trg,wt))
  new_sent_tokens=list(sent_tokens)
  valid_replacements=[]
  for word0 in list(set(sent_tokens)):
    if exclude_sent_start and word0=="<s>": continue
    all_corr=first_repl_dict.get(word0,[]) #get the corresponding equivalents/freq to the current word
    for corr_key0,corr_freq_val_dict0 in all_corr:
      found_spans=general.is_in(corr_key0.split(),sent_tokens)
      for span0 in found_spans: valid_replacements.append((corr_key0,corr_freq_val_dict0,span0)) #just the phrase and the span
  return valid_replacements

# def get_possible_replacements(sent_tokens,first_repl_dict): #use the repl dict (with keys as first word, value is a list of triplets (repl_src,repl_trg,wt))
#   new_sent_tokens=list(sent_tokens)
#   valid_replacements=[]
#   for word0 in list(set(sent_tokens)):
#     all_corr=first_repl_dict.get(word0,[])
#     for corr0 in all_corr:
#       found_spans=general.is_in(corr0[0],sent_tokens)
#       for span0 in found_spans: valid_replacements.append((corr0,span0)) #just the phrase and the span
#   return valid_replacements


# def compare_repl_OLD(tokens1,tokens2,window_size=5): #make all changes as replacements - add sentence boundaries for whole segment edits
#   tokens1=add_padding(tokens1)
#   tokens2=add_padding(tokens2)
#   match_obj=SequenceMatcher(None,tokens1,tokens2)
#   final_list=[]
#   for a in match_obj.get_opcodes():
#     match_type,x0,x1,y0,y1=a
#     if match_type in ["insert","delete"]: #for insertaions/deletions, get preceding+following token to make it a replacement
#       x0=x0-1
#       x1=x1+1
#       y0=y0-1
#       y1=y1+1
#       match_type="replace"
  
#     old0=tokens1[x0:x1]
#     new0=tokens2[y0:y1]
#     span_old0=(x0,x1)
#     span_new0=(y0,y1)
#     prev_context=tokens1[max(0,x0-window_size):x0]
#     next_context=tokens1[x1:]
#     final_list.append((match_type,old0,new0,span_old0,span_new0,prev_context,next_context))
#   return final_list





#============ Replacement model ===================
def apply_replace_OLD(sent_tokens,first_repl_dict): #use the repl dict (with keys as first word, value is a list of triplets (repl_src,repl_trg,wt))
  new_sent_tokens=list(sent_tokens)
  valid_replacements=[]
  for word0 in list(set(sent_tokens)):
    all_corr=first_repl_dict.get(word0,[])
    for corr0 in all_corr:
      if not general.is_in(corr0[0],sent_tokens): continue
      valid_replacements.append(corr0)
  for repl0 in valid_replacements:
    repl_src,repl_trg,repl_wt=repl0
    new_sent_tokens=repl_phrase(new_sent_tokens,repl_src,repl_trg)
  return new_sent_tokens


def get_repl_list(sent_tokens,first_repl_dict): #all possible "flat" replacements, with their freq {src:xxx,trg:xxx,span:xxx,freq:xxx} 
  initial_repl_list=get_possible_replacements(sent_tokens,first_repl_dict)
  all_instances=[]
  for src0,trg_dict0,span0 in initial_repl_list:
    for trg0,freq0 in trg_dict0.items():
      temp_dict={}
      temp_dict["src"]=src0
      temp_dict["trg"]=trg0
      temp_dict["freq"]=freq0
      temp_dict["span"]=span0
      all_instances.append(temp_dict)
  return all_instances

def apply_freq_repl(sent_tokens,first_repl_dict): #apply a first token dictionary sorted by frequency
  repl_inst_wt_list=get_repl_list(sent_tokens,first_repl_dict)
  new_sent_tokens,valid_repl_list=repl_span_phrase(sent_tokens,repl_inst_wt_list,sort_by="freq")
  return new_sent_tokens,valid_repl_list



def repl_phrase(sent_tokens,phrase_to_be_replaced,new_phrase): #replace a phrase within a sentence
  last_i=0
  new_tokens=[]
  found_spans=general.is_in(phrase_to_be_replaced,sent_tokens)
  for span0 in found_spans:
    span_i0,span_j0=span0
    new_tokens.extend(sent_tokens[last_i:span_i0])
    new_tokens.extend(new_phrase)
    last_i=span_j0+1
  new_tokens.extend(sent_tokens[last_i:])
  return new_tokens

#18 Aug 23
def repl_span_phrase(sent_tokens,repl_inst_wt_list,sort_by="wt",min_wt=0.5,min_freq=None): #apply a list of replacement instances with their weight/freq to tokenized sentence - sort instances by weight and exclude overlapping instances - outputs new sentence and valid replacemnt instances
  used_locs=[]
  valid_repl_instances=[]
  #repl_inst_wt_list.sort(key=lambda x:-x.get(sort_by,0))
  repl_inst_wt_list.sort(key=lambda x:(-x.get(sort_by,0), -x.get("freq",0)))
  for cur_repl_inst0 in repl_inst_wt_list:
    cur_wt=cur_repl_inst0.get("wt")
    cur_freq=cur_repl_inst0.get("freq")
    if cur_wt!=None and cur_wt<min_wt: continue
    if min_freq!=None and cur_freq!=None and cur_freq<min_freq: continue
    #print(">>>>>", cur_repl_inst0)
    x0,x1 = cur_repl_inst0["span"]
    cur_locs=list(range(x0,x1+1))
    found_in_used_check=any([v in used_locs for v in cur_locs])
    if found_in_used_check: continue
    else:
      used_locs.extend(cur_locs)
      valid_repl_instances.append(cur_repl_inst0)
      #print(">>>",cur_repl_inst0)
  valid_repl_instances.sort(key=lambda x:x["span"])
  new_sent_tokens=[]
  prev_i=0
  for valid_item0 in valid_repl_instances:
    #print("valid_item0",valid_item0)
    span0=valid_item0["span"]
    trg0=valid_item0["trg"]
    x0,x1=span0
    prev_chunk=sent_tokens[prev_i:x0]
    cur_chunk=trg0.split(" ")
    prev_i=x1+1
    new_sent_tokens.extend(prev_chunk+cur_chunk)
  new_sent_tokens.extend(sent_tokens[prev_i:])
  return new_sent_tokens, valid_repl_instances


# def repl_span_phrase(sent_tokens,repl_inst_wt_list,sort_by="wt",min_wt=0.5,min_freq=None):
#   used_locs=[]
#   valid_repl_instances=[]
#   repl_inst_wt_list.sort(key=lambda x:x.get("sort_by",0))
#   for cur_repl_inst0 in repl_inst_wt_list:
#     cur_wt=cur_repl_inst0.get("wt")
#     cur_freq=cur_repl_inst0.get("freq")
#     if cur_wt!=None and cur_wt<min_wt: continue
#     if min_freq!=None and cur_freq!=None and cur_freq<min_freq: continue
#     x0,x1 = cur_repl_inst0["span"]
#     cur_locs=list(range(x0,x1+1))
#     found_in_used_check=any([v in used_locs for v in cur_locs])
#     if found_in_used_check: continue
#     else:
#       used_locs.extend(cur_locs)
#       valid_repl_instances.append(cur_repl_inst0)
#       #print(">>>",cur_repl_inst0)
#   valid_repl_instances.sort(key=lambda x:x["span"])
#   new_sent_tokens=[]
#   prev_i=0
#   for valid_item0 in valid_repl_instances:
#     span0=valid_item0["span"]
#     trg0=valid_item0["trg"]
#     x0,x1=span0
#     prev_chunk=sent_tokens[prev_i:x0]
#     cur_chunk=trg0.split(" ")
#     prev_i=x1+1
#     new_sent_tokens.extend(prev_chunk+cur_chunk)
#   new_sent_tokens.extend(sent_tokens[prev_i:])
#   return new_sent_tokens












def get_docx_paras_edits(docx_fpath): #main function to extract edit info, while keeping track of para path/id
  docx_obj=docx(docx_fpath)
  data_list1=[]
  all_paras,paras_dict=docx_obj.extract_paras()
  docx_obj.close()
  for para_path0,para_content0 in all_paras:
    orig0,final0,edit0=get_edit_info(para_content0)
    if orig0==final0=="": continue
    data_list1.append((para_path0,orig0,final0,edit0))
  return data_list1

# def get_docx_paras_edits_src_trg_editing(docx_fpath):
#   docx_obj=docx(docx_fpath)
#   data_list1=[]
#   all_paras,paras_dict=docx_obj.extract_paras()
#   docx_obj.close()
#   for para_path0,para_content0 in all_paras:
#     orig0,final0,edit0=get_edit_info(para_content0)
#     if orig0==final0=="": continue
#     data_list1.append((orig0,final0,edit0))
#   return data_list1

def para2sents(text):
  text=text.replace(". ",".\n")
  text=text.replace("\t","\n")
  sents0=[v.strip() for v in text.split("\n") if v.strip()]
  return sents0



#============ Pre-editing pipeline ========================
def pre_edit(sent_str,nn_model_obj,first_token_dict,pred_threshold=0.5): #pre-edit a sentence giveb the first token dict and a neural network model object with prediction
  sent_tokens0=general.add_padding(general.tok(sent_str))
  span_repl_items=extract_repl_instances(sent_tokens0,[],first_token_dict)
  new_items=[]
  for item0 in span_repl_items:
    if item0["context"]=='|': continue
    #if nn_model_obj==None: wt0=0
    try: wt0=nn_model_obj.pred(item0)
    except: wt0=0
    #print(item0,wt0)
    #if wt0<pred_threshold: continue
    item0["wt"]=wt0
    new_items.append(item0)
  if nn_model_obj!=None: pre_edited_sent_tokens,valid_repl=repl_span_phrase(sent_tokens0,new_items,sort_by="wt",min_wt=pred_threshold)
  else: pre_edited_sent_tokens,valid_repl=repl_span_phrase(sent_tokens0,new_items,sort_by="freq",min_wt=0)
  if pre_edited_sent_tokens[0]=="<s>": pre_edited_sent_tokens=pre_edited_sent_tokens[1:]
  if pre_edited_sent_tokens[-1]=="</s>": pre_edited_sent_tokens=pre_edited_sent_tokens[:-1]
  return pre_edited_sent_tokens,valid_repl

def pre_edit_docx(docx_fpath,nn_model_obj,first_token_dict,pred_threshold=0.5,pre_edit_original=True): #prediting the original of a docx file
  cur_docx_edit_list=get_docx_paras_edits(docx_fpath)
  new_edit_pre_edit_list=[]
  all_repl_inst_list=[]
  for docx_para_edit_item in cur_docx_edit_list:
    para_path0,original0,final0,edited0=docx_para_edit_item
    original_tokens=general.tok(original0)
    final_tokens=general.tok(final0)
    if original0.strip()=="" or final0.strip()=="": pre_edit_out=original0
    if pre_edit_original: pre_edit_out_tokens,valid_repl=pre_edit(original0,nn_model_obj,first_token_dict,pred_threshold)
    else: pre_edit_out_tokens,valid_repl=pre_edit(original0,nn_model_obj,first_token_dict,pred_threshold) #if we want to pre-edit the final

    pre_edit_out_str=general.de_tok2str(pre_edit_out_tokens)
    pre_edit_html=get_edit_html(original_tokens,pre_edit_out_tokens,class_name="automatic")
    token_edited_html=get_edit_html(original_tokens,final_tokens,class_name="human")
    new_edit_pre_edit_list.append((para_path0,original0,final0,edited0,token_edited_html,pre_edit_out_str,pre_edit_html))
    all_repl_inst_list.extend(valid_repl)
  return new_edit_pre_edit_list,all_repl_inst_list



def analyze_pre_edit_docx(docx_fpath,nn_model_obj,first_token_dict,pred_threshold=0.5,pre_edit_original=True): #check how much of the actual replacements the model was able to predict
  analysis_dict={}
  n_human_edits=0 #excluding capitalization
  n_model_edits=0
  n_correct_model_edits=0
  n_incorrect_model_edits=0

  cur_docx_edit_list=get_docx_paras_edits(docx_fpath)
  new_edit_pre_edit_list=[]
  all_repl_inst_list=[]
  for docx_para_edit_item in cur_docx_edit_list:
    para_path0,original0,final0,edited0=docx_para_edit_item
    original_tokens= general.add_padding(general.tok(original0)) 
    final_tokens=general.add_padding(general.tok(final0)) 
    if original0.strip()=="" or final0.strip()=="": pre_edit_out=original0
    if pre_edit_original: pre_edit_out_tokens,valid_repl=pre_edit(original0,nn_model_obj,first_token_dict,pred_threshold)
    else: pre_edit_out_tokens,valid_repl=pre_edit(final0,nn_model_obj,first_token_dict,pred_threshold) #if we want to pre-edit the final
    n_model_edits+=len(valid_repl)

    valid_compare_repl_spans_dict={} #check which spans are used in the human edits (excluding capitalization edits)
    compare_repl_list=compare_repl(original_tokens,final_tokens)
    for repl_item in compare_repl_list:
      
      if repl_item[0]=="equal": continue
      if " ".join(repl_item[1]).lower()==" ".join(repl_item[2]).lower(): continue
      #print("repl_item",repl_item)
      n_human_edits+=1
      valid_compare_repl_spans_dict[repl_item[3]]=True

    #print("valid_compare_repl_spans_dict",valid_compare_repl_spans_dict)
    pre_edit_out_str=general.de_tok2str(pre_edit_out_tokens)
    pre_edit_html=get_edit_html(original_tokens,pre_edit_out_tokens,class_name="automatic")
    token_edited_html=get_edit_html(original_tokens,final_tokens,class_name="human")
    new_edit_pre_edit_list.append((para_path0,original0,final0,edited0,token_edited_html,pre_edit_out_str,pre_edit_html))
    #new_edit_pre_edit_list.append((para_path0,original0,final0,edited0,token_edited_html,pre_edit_out_str,pre_edit_html))
    for model_repl_inst in valid_repl:
      cur_span=model_repl_inst["span"]
      if valid_compare_repl_spans_dict.get(cur_span,False): n_correct_model_edits+=1
      else: n_incorrect_model_edits+=1
      all_repl_inst_list.append(model_repl_inst)
      #all_repl_inst_list.extend(valid_repl)
  analysis_dict["n_human_edits"]=n_human_edits
  analysis_dict["n_model_edits"]=n_model_edits
  analysis_dict["n_correct_model_edits"]=n_correct_model_edits
  analysis_dict["n_incorrect_model_edits"]=n_incorrect_model_edits
  recall0=0
  precision0=0
  if n_human_edits>0: recall0=round(n_correct_model_edits/n_human_edits,2)
  if n_model_edits>0: precision0=round(n_correct_model_edits/n_model_edits,2)
  analysis_dict["simple_recall"]=recall0
  analysis_dict["simple_precision"]=precision0


  return new_edit_pre_edit_list,all_repl_inst_list,analysis_dict



def edit_list2html(edit_list,out_fpath,template_fpath="templates/pre-editing_table_template.html"):
  table_content0=""
  for i0,tag_item0 in enumerate(edit_list):
    original0,final0,edited0=tag_item0
    table_class="table-light"
    if i0%2!=0: table_class="table-dark text-dark"
    cur_tr0='<tr class="%s"><td>%s</td><td>%s</td><td>%s</td></tr>'%(table_class,original0,final0,edited0)
    table_content0+=cur_tr0

  #template_fpath="templates/pre-editing_table_template.html"
  template_fopen=open(template_fpath)
  template_content=template_fopen.read()
  template_fopen.close()
  template_dom_obj=web_lib.DOM(template_content)
  repl_dict={"#data_display_table_body":table_content0}
  out_html=template_dom_obj.replace(repl_dict)

  out_fopen=open(out_fpath,"w")
  out_fopen.write(out_html)
  out_fopen.close()





def gen_para_id():
  return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


##################### OLD #########################



#OLD
w_p_exp=r"<w:p\b.*?>.*?</w:p>"
w_t_exp=r"<w:t\b.*?>.*?</w:t>"
w_t_inside_exp=r"<w:t\b.*?>(.*?)</w:t>"
w_t_inside_outside_exp=r"(<w:t\b.*?>)(.*?)(</w:t>)"

def get_xml_elements(xml_content0,el_name="w:p"):
  open_tag="<"+el_name
  closing_tag="</"+el_name+">"
  all_split=re.split(r"%s\b"%open_tag,xml_content0)
  #all_split=xml_content0.split(open_tag)
  all_elements=[]
  for as0 in all_split[1:]:
    if not closing_tag in as0: continue
    #if not as0[0] in " >": continue #if the first character after the open tag e.g. <w:r is not a space or >, it is a different tag
    split_closing_tag=as0.split(closing_tag)
    el_outer_xml=open_tag+split_closing_tag[0]+closing_tag
    all_elements.append(el_outer_xml)
  return all_elements

def get_para_by_id(xml_fpath0,id0): #given the paragraph ID and path of the xml file, get the outer XML element 
  fopen=open(xml_fpath0)
  content=fopen.read()
  fopen.close()
  found_i=content.find(id0)
  para_xml_i0=content[:found_i].rfind('<w:p')
  para_xml_i1=found_i+content[found_i:].find('</w:p>')+len('</w:p>')
  para_xml_slice=content[para_xml_i0:para_xml_i1]
  return para_xml_slice

def get_para_by_index(xml_fpath0,i0): #given the paragraph index and path of the xml file, get the outer XML element 
  fopen=open(xml_fpath0)
  xml_content0=fopen.read()
  fopen.close()
  cur_wps=get_xml_elements(xml_content0,el_name="w:p")
  para_xml_slice=cur_wps[i0]
  return para_xml_slice


def save_tmp2docx(tmp_dir_path,new_docx_fpath): #convert the temp directory with them XML files making the original docx into a new docx file
  if os.path.exists(new_docx_fpath): os.remove(new_docx_fpath) #remove any of these if already exists
  shutil.make_archive(tmp_dir_path, 'zip', tmp_dir_path)
  os.rename(tmp_dir_path+".zip", new_docx_fpath)






# def update_para_OLD(para_id0,xml_path0,new_text0,rtl=True,style={}): #get an xml element by ID, update it with new text and style, save the new XML with this updated element
#   fopen=open(xml_fpath0)
#   content=fopen.read()
#   fopen.close()
#   cur_slice=get_para_by_id(xml_fpath0,para_id0)
#   updated_slice=update_wr_text(cur_slice,new_text0)
#   if rtl: #
#     w_p_tag_exp=r"<w:p\b.*?>"
#     w_r_tag_exp=r"<w:r\b.*?>"
#     wp_tags=list(set(re.findall(w_p_tag_exp,updated_slice)))
#     wr_tags=list(set(re.findall(w_r_tag_exp,updated_slice)))
#     for wp0 in wp_tags:
#       updated_slice=updated_slice.replace(wp0,wp0+'<w:pPr><w:bidi/></w:pPr>')
#     for wr0 in wr_tags:
#       updated_slice=updated_slice.replace(wr0,wr0+'<w:rPr><w:rtl/></w:rPr>')




#     # wp_tags=re.findall(w_p_tag_exp,updated_slice)
#     # updated_slice=updated_slice.replace("<w:rtl/>","")  
#     # updated_slice=updated_slice.replace("<w:lang ","<w:rtl/><w:lang ")
#     # #updated_slice=updated_slice.replace('/></w:rPr>','w:bidi="ar-MA"/></w:rPr>')
    
#   content=content.replace(cur_slice,updated_slice)
#   fopen1=open(xml_fpath0,"w")
#   fopen1.write(content)
#   fopen1.close()  
#   return updated_slice

def update_para_by_index(para_i0,xml_fpath0,new_text0,rtl=True,style={}): #get an xml element by its index, update it with new text and style, save the new XML with this updated element
  fopen=open(xml_fpath0)
  content=fopen.read()
  fopen.close()
  cur_slice0=get_para_by_index(xml_fpath0,para_i0)
  #print(">>>> <<<???",cur_slice0)
  updated_slice=update_wr_text(cur_slice0,new_text0)
  if rtl: #
    # updated_slice=updated_slice.replace("<w:rtl/>","")  
    # updated_slice=updated_slice.replace("<w:lang ","<w:rtl/><w:lang ")
    #updated_slice=updated_slice.replace('/></w:rPr>','w:bidi="ar-MA"/></w:rPr>')
    w_p_tag_exp=r"<w:p\b.*?>"
    w_r_tag_exp=r"<w:r\b.*?>"
    wp_tags=list(set(re.findall(w_p_tag_exp,updated_slice)))
    wr_tags=list(set(re.findall(w_r_tag_exp,updated_slice)))
    for wp0 in wp_tags:
      updated_slice=updated_slice.replace(wp0,wp0+'<w:pPr><w:bidi/></w:pPr>')
    for wr0 in wr_tags:
      updated_slice=updated_slice.replace(wr0,wr0+'<w:rPr><w:rtl/></w:rPr>')
    #print(updated_slice)
  content=content.replace(cur_slice0,updated_slice)
  fopen1=open(xml_fpath0,"w")
  fopen1.write(content)
  fopen1.close()  
  return updated_slice
  

def get_xml_wrs(xml_content):
  cur_chunks=find_iter_split(w_p_exp,xml_content)
  return cur_chunks


def find_iter_split(expression,text): #generic function to split a text (haystack) around a certain regex
  split_text=[]
  exp_applies={} #whether the current expression applies to the current segment of the split segments
  found_objs=re.finditer(expression,text)
  indexes=[0]
  for fo in found_objs:
    start,end=fo.start(), fo.end()
    indexes.append(start)
    indexes.append(end)
    exp_applies[start]=True #in the split chunks, the regex criteria applies to some of them, and some are not, so we keep track of this
  indexes.append(len(text))
  if len(indexes)==2: return []
  counter=0
  for i0,i1 in zip(indexes,indexes[1:]):
    applies=exp_applies.get(i0,False)
    chunk=text[i0:i1] 
    split_text.append((counter,applies,chunk))
    counter+=1
  return split_text  

def get_wr_text(wr_chunk):
  all_text=""
  wt_chunks=find_iter_split(w_t_exp,wr_chunk)
  for wt in wt_chunks:
    wt_counter,wt_applies,wt_chunk=wt
    wt_content=[""]
    if wt_applies: wt_content=re.findall(w_t_inside_exp,wt_chunk)
    elif "<w:br/>" in wt_chunk: wt_content=["\n"]
    elif "<w:tab/>" in wt_chunk: wt_content=["\t"]
    all_text+=wt_content[0]
  return all_text

def striphtml(data):
  p = re.compile(r'<.*?>')
  return p.sub('', data)

def get_el_text(el_xml):
  el_xml=el_xml.replace("<w:br/>","\n")
  el_xml=el_xml.replace("<w:tab/>","\t")
  text=striphtml(el_xml)
  return text



def update_wr_text(wr_xml,new_text):
   wt_chunks=find_iter_split(w_t_exp,wr_xml)
   new_text=safe_xml(new_text)
   new_wr_content=""
   replaced=False
   for wt in wt_chunks:
     wt_counter,wt_applies,wt_chunk=wt
     if wt_applies:
       first_tag=wt_chunk[:wt_chunk.find(">")+1]
       last_tag=wt_chunk[wt_chunk.rfind("<"):]
       if replaced==False: #we replace only the first wt 
         wt_content=first_tag+new_text+last_tag
         replaced=True
       else: wt_content=first_tag+last_tag
       new_wr_content+=wt_content
     else: new_wr_content+=wt_chunk#.decode("utf-8")
   return new_wr_content






# class docx_OLD:
#   def __init__(self,docx_fpath,keep_copy=True): #openning the docx file, by unzipping it
#     self.TEMP_DOCX = docx_fpath
#     self.closed=False
#     self.COPY_DOCX = docx_fpath+"2"
#     shutil.copy(self.TEMP_DOCX, self.COPY_DOCX) #keep a temp copy of out file, just in case
#     self.file_extension="."+docx_fpath.split(".")[-1]
#     self.TEMP_ZIP = docx_fpath.replace(self.file_extension,".zip")
#     self.TEMP_FOLDER = docx_fpath.replace(self.file_extension,"")
#     if os.path.exists(self.TEMP_ZIP):
#       os.remove(self.TEMP_ZIP)
#     if os.path.exists(self.TEMP_FOLDER):
#       shutil.rmtree(self.TEMP_FOLDER)
#     os.rename(self.TEMP_DOCX, self.TEMP_ZIP) #rename the original docx to zip extension
#     # unzip file zip to specific folder
#     z_open=zipfile.ZipFile(self.TEMP_ZIP, 'r')
#     z_open.extractall(self.TEMP_FOLDER)
#     z_open.close()
#     os.rename(self.COPY_DOCX, self.TEMP_DOCX) #keep the original file
#   def save_as(self,out_fpath):
#     if os.path.exists(out_fpath): #remove any of these if already exists
#       os.remove(out_fpath)
#     #self.OUT_ZIP = out_fpath.replace(".docx",".zip")
#     #shutil.make_archive(self.OUT_ZIP, 'zip', self.TEMP_FOLDER)
#     shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
#     os.rename(self.TEMP_ZIP, out_fpath)
#   def extract_paras(self,cat_file_path=""): 
#     self.paras=[]
#     if self.TEMP_DOCX.lower().endswith(".docx"): main_dir="word"
#     if self.TEMP_DOCX.lower().endswith(".pptx"): main_dir="ppt/slides"
#     if self.TEMP_DOCX.lower().endswith(".xlsx"): main_dir="xl"

#     extracted_dir=os.path.join(self.TEMP_FOLDER, main_dir)
#     for xml_fname in os.listdir(extracted_dir):
#       #print(xml_fname)
#       skip_file=True
#       if xml_fname in ["document.xml", "footnotes.xml","endnotes.xml","sharedStrings.xml"]: skip_file=False
#       if xml_fname.startswith("slide"): skip_file=False
#       if xml_fname.startswith("sheet"): skip_file=False
#       if xml_fname.startswith("header"): skip_file=False
#       if xml_fname.startswith("footer"): skip_file=False
#       if skip_file: continue
#       # if xml_fname in ["document.xml", "footnotes.xml","endnotes.xml"] or xml_fname.startswith("header") or xml_fname.startswith("footer"): pass
#       # else: continue
#       #if not xml_fname=="document.xml" and not xml_fname.startswith("header") and not xml_fname.startswith("footer"): continue
#       cur_xml_path=os.path.join(extracted_dir,xml_fname)
#       with open(cur_xml_path) as fopen:
#         xml_content=fopen.read()
#       cur_tag_name="w:p" #xml tag for docx files
#       if self.TEMP_DOCX.lower().endswith(".pptx"): cur_tag_name="a:p"
#       cur_wps=get_xml_elements(xml_content,el_name=cur_tag_name)
#       for i0,wp_xml in enumerate(cur_wps):
#         #wp_text=get_wr_text(wp_xml)
#         wp_text=get_el_text(wp_xml)        
#         para_obj=para()
#         para_obj.path=cur_xml_path
#         para_obj.xml=wp_xml
#         para_obj.text=wp_text
#         para_obj.i=i0
#         para_obj.tag_name=cur_tag_name        
#         found_ids=re.findall('paraId="(.+?)"',wp_xml) 
#         if found_ids: para_obj.id=  found_ids[0]
#         self.paras.append(para_obj)
#       if cat_file_path!="": #save paragraphs with their info to cat file
#         cat_fopen=open(cat_file_path,"w")
#         for p_obj in self.paras:
#           cur_text=p_obj.text.replace("\t"," <tab> ").replace("\n"," <br> ")
#           json_obj={}
#           json_obj["path"]=p_obj.path
#           json_obj["i"]=p_obj.i
#           json_obj["id"]=p_obj.id
#           json_obj["tag_name"]=p_obj.tag_name          
#           json_obj["text"]=cur_text
#           json_obj_str=json.dumps(json_obj) 
#           line=json_obj_str+"\n"
#           #line="%s\t%s\t%s\t%s\n"%(p_obj.path,p_obj.i,p_obj.id,cur_text)
#           cat_fopen.write(line)
#         cat_fopen.close()

#     return self.paras
  

#   def update_tbl_rtl(self):
#     extracted_dir=os.path.join(self.TEMP_FOLDER, "word")
#     cur_xml_path=os.path.join(extracted_dir,"document.xml")
#     fopen_read=open(cur_xml_path)
#     xml_content=fopen_read.read()
#     fopen_read.close()
#     xml_content=xml_content.replace("<w:tblPr>","<w:tblPr><w:bidiVisual/>")
#     xml_content=xml_content.replace("<w:lang ","<w:rtl/><w:lang ")

    
#     fopen_write=open(cur_xml_path, "wb")
#     fopen_write.write(xml_content)
#     fopen_write.close()


#   def close(self):
#     self.closed=True
#     os.remove(self.TEMP_ZIP)
#     shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
#     os.rename(self.TEMP_ZIP, self.TEMP_DOCX)
#     shutil.rmtree(self.TEMP_FOLDER)
  

class para:
  def __init__(self):
    self.xml=""
    self.text=""
    self.path=""
    self.id=""
    self.tag_name=""
    self.i=None
  def update_text(self,new_text):
    pass
  def update_style(self,new_style):
    pass

def write(content0,path0):
  fopen0=open(path0,"w")
  fopen0.write(content0)
  fopen0.close()
def read(path0):
  fopen0=open(path0)
  content0=fopen0.read()
  fopen0.close()
  return content0

def translate_doc(in_fpath,out_fpath,tsv_fpath,sentence_split_fn,out_paras_fpath=""):
  repl_dict=tsv2dict(tsv_fpath)
  test_docx_obj=docx(in_fpath)
  paras=test_docx_obj.extract_paras(out_paras_fpath)
  for p in paras:
    cur_xml_slice=p.xml
    text0=unescape(p.text)
    sents= ssplit(text0) #need to load ssplit from general utils
    eq_sents=[]
    for sent0 in sents:
      sent0_key=str2key(sent0)
      #print(sent0_key)
      test=repl_dict.get(sent0_key)
      if test==None:
        print(sent0)
        for key0 in repl_dict.keys():
          if key0[:8]==sent0_key[:8]: print(key0)
        print("------")
      equiv=repl_dict.get(sent0_key,sent0)
      eq_sents.append(equiv)
    eq_para_text=" ".join(eq_sents)
    if eq_para_text.strip()=="": continue
    cur_content=read(p.path)
    cur_wps=get_xml_elements(cur_content,el_name="w:p")
    update_para_by_index(p.i,p.path,eq_para_text,rtl=True,style={})
  save_tmp2docx(test_docx_obj.TEMP_FOLDER,out_fpath)



if __name__=="__main__":
  # out_fpath="docs/hlpf-ar-test1.docx"
  # test_docx_obj=docx("docs/hlpf.docx")
  # paras=test_docx_obj.extract_paras("docs/hlpf-cat5.txt")
  # tsv_fpath="docs/hlpf.tsv"
  # repl_dict=tsv2dict(tsv_fpath)
  # test_pptx_obj=docx("docs/annex8.pptx")
  # paras=test_pptx_obj.extract_paras("docs/annex8-cat.txt")
  from code_utils.general import *
  in_fpath="docs/mechanism2-en.docx"
  out_fpath="docs/mechanism2-ar4.docx"
  tsv_fpath="docs/mechanism2.tsv"
  paras_fpath="docs/mechanism-paras2.txt"
  translate_doc(in_fpath,out_fpath,tsv_fpath,ssplit,out_paras_fpath="")


  # for p in paras:
  #   print(">>>>", p.id,p.path, p.i, p.text) 
  #   cur_xml_slice=p.xml
  #   sents= ssplit(p.text)
  #   eq_sents=[]
  #   for sent0 in sents:
  #     sent0_key=str2key(sent0)
  #     equiv=repl_dict.get(sent0_key,sent0)
  #     eq_sents.append(equiv)
  #   eq_para_text=" ".join(eq_sents)
  #   if eq_para_text.strip()=="": continue
  #   cur_content=read(p.path)
  #   cur_wps=get_xml_elements(cur_content,el_name="w:p")
  #   print(p.path,len(cur_wps))

  # # cur_content=read(p.path)
  # # updated_slice=update_wr_text(cur_xml_slice,eq_para_text)
  #   update_para_by_index(p.i,p.path,eq_para_text,rtl=True,style={})
  # save_tmp2docx(test_docx_obj.TEMP_FOLDER,out_fpath)



