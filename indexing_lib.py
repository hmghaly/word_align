import time, json, shelve, os, re, sys
from itertools import groupby
from math import log
import random


#from general import * 
sys.path.append("code_utils")
import general
import arabic_lib

excluded_src_tokens=["the","a","an","and","of","its","his","her","their","them","to","is","are","am","been","was","were","be",
                     "have","has","had", "in", "on", "at", "with", "from","for","that","he","she","it","would",
                     "as","by","they","whose","which"] #we will need to update this
excluded_trg_tokens=["من","على","في","مع", "إلى",
                     "له","تم","إلى","في","عن","إن","أن","به","بها","لها","التي","كان","قد","الذي","الذين",
                     "هو","هي"]


def filter_toks(tok_list0,params={}):
  cur_excluded_words=params.get("excluded_words",[])
  keep_all_tokens=params.get("keep_all_tokens",False)
  exclude_numbers=params.get("exclude_numbers",False)
  exclude_single_chars=params.get("exclude_single_chars",True)
  exclude_punc=params.get("exclude_punc",True)
  ignore_ar_pre_suf=params.get("ignore_ar_pre_suf",True)

  if keep_all_tokens:
    cur_excluded_words=[]
    exclude_numbers=False
    exclude_single_chars=False
    exclude_punc=False
    ignore_ar_pre_suf=False

  if params.get("lower",True): tok_list0=[v.lower() for v in tok_list0] #make all words lower case or not
  
  if cur_excluded_words!=[]: tok_list0=[v if not v in cur_excluded_words else "" for v in tok_list0] #ignore stop words
  if exclude_numbers: tok_list0=[v if not v.isdigit() else "" for v in tok_list0] #ignore single character tokens
  if exclude_single_chars: tok_list0=[v if len(v)>1 else "" for v in tok_list0] #ignore single character tokens
  if exclude_punc: tok_list0=[v if not general.is_punct(v) else "" for v in tok_list0] #ignore punctuation
  if ignore_ar_pre_suf: tok_list0=["" if v.startswith("ـ") or v.endswith("ـ") else v for v in tok_list0] #ignore arabic prefixes and suffixes

  if params.get("remove_ar_diacritics",True): tok_list0=[general.remove_diactitics(v) for v in tok_list0] #remove Arabic diacritics
  if params.get("remove_al",True): tok_list0=[v.replace("ال_","") for v in tok_list0] #remove alif laam for the beginning of Arabic words
  if params.get("normalize_taa2_marbootah",False): tok_list0=[v[:-1]+"ت"  if v.endswith("ة") else v for v in tok_list0] #normalize taa2 marbootah
  if params.get("normalize_digits",False): tok_list0=["5"*len(v) if v.isdigit() else v for v in tok_list0] #normalize numbers to just the number of digits 1995 > 5555
  #if params.get("stemming",False): tok_list0=[v else v for v in tok_list0] #stem each word or not
  #remove_al=params0.get("remove_al", False) #remocve alif laam in Arabic 
  return tok_list0

def retr_sent_phrase_indexes(sent_toks,inv_index,max_phrase_length=4,min_index_size=5): #get the indexes of the phrases of the tokenized sentence, together with their location info
  phrase_index_dict={}
  phrase_loc_dict={}
  tmp_inv_index={}
  for word0 in list(set(sent_toks)): 
    cur_indexes0=inv_index.get(word0,[])
    if len(cur_indexes0)<min_index_size: continue
    tmp_inv_index[word0]=cur_indexes0
    phrase_index_dict[word0]=cur_indexes0
  for i0 in range(len(sent_toks)):
    cur_tok0=sent_toks[i0]
    tok0_indexes=tmp_inv_index.get(cur_tok0,[])
    if tok0_indexes==[]: continue
    if cur_tok0=="": continue
    for i1 in range(i0,len(sent_toks)):
      offset0=i1-i0
      if offset0>max_phrase_length: continue
      cur_tok1=sent_toks[i1]
      if cur_tok1=="": continue
      phrase_toks=sent_toks[i0:i1+1]
      phrase_str=" ".join(phrase_toks).strip()
      phrase_loc_dict[phrase_str]=phrase_loc_dict.get(phrase_str,[])+[(i0,i1)]
      if i0<i1:
        tok1_indexes=tmp_inv_index.get(cur_tok1,[])
        tok1_offset_indexes=offset_indexes(tok1_indexes,offset0)
        prev_phrase_tokens=phrase_toks[:-1]
        prev_phrase_str=" ".join(prev_phrase_tokens).strip()
        prev_phrase_indexes=phrase_index_dict.get(prev_phrase_str,[])
        #intersection0=list(set(prev_phrase_indexes).intersection(set(tok1_offset_indexes)))
        cur_intersection0=get_offset_intersection(prev_phrase_indexes,tok1_offset_indexes)
        found_indexes_check=phrase_index_dict.get(phrase_str)
        #if cur_intersection0!=[]: phrase_index_dict[phrase_str]=cur_intersection0
        if len(cur_intersection0)<min_index_size: break
        phrase_index_dict[phrase_str]=cur_intersection0
  phrase_index_loc_dict={}
  for phrase0,phrase_indexes0 in phrase_index_dict.items():
    phrase_locs0=phrase_loc_dict.get(phrase0,[])
    phrase_index_loc_dict[phrase0]=[phrase_locs0,phrase_indexes0]
  return phrase_index_loc_dict

def offset_indexes(index_list0,offset0,max_sent_size0=1000):
  return [v-(offset0/max_sent_size0) for v in index_list0] 

#Use this
def get_offset_intersection(index_list0,index_list1,max_sent_size0=1000):
  if index_list0==None or index_list1==None: return []
  # list0_1000=[int(round(v*max_sent_size0)) for v in index_list0]
  # list1_1000=[int(round(v*max_sent_size0)) for v in index_list1]
  list0_1000=[round(v,3) for v in index_list0]
  list1_1000=[round(v,3) for v in index_list1]
  intersection0=list(set(list0_1000).intersection(set(list1_1000)))
  return intersection0 #[v/max_sent_size0 for v in intersection0]


def index_sent_toks(sent_toks,sent_number,max_sent_size=1000):
  indexed_sent0=[(v,sent_number+vi/max_sent_size) for vi,v in enumerate(sent_toks) if vi<max_sent_size and v!=""]
  return indexed_sent0

def get_inv_index(fwd_index):
  fwd_index.sort()
  grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(fwd_index,lambda x:x[0])]
  inverted_index=dict(iter(grouped))  
  return inverted_index


#Indexing and bitext functions
def tok_bitext(list0,params0={}):
  #cur_ar_counter_dict=params0.get("ar_counter_dict",{})
  tokenized_bitext_list0=[]
  if len(list0[0])==2: list0=[(vi,v[0],v[1]) for vi,v in enumerate(list0)] #if it is just list of src/trg sentences - else the list should be loc,src,trg 
  #for cur_loc,src_trg in enumerate(list0):
  for cur_loc,src0,trg0 in list0:
    #src0,trg0=src_trg
    try:
      src_toks0=general.tok(src0)
      #trg_toks0=general.tok(trg0)
      lang2_tok_fn=params0.get("lang2_tok_fn")
      if lang2_tok_fn==None: trg_toks0=general.tok(trg0)
      else: 
        trg_toks0=lang2_tok_fn(trg0)
      #if  retr_params["lang2_tok_fn"]=cur_ar_tok_fn
      #if params0.get("lang2")=="ar": trg_toks0=arabic_lib.tok_ar(trg_toks0,cur_ar_counter_dict)
    except Exception as ex: 
        print("tokenization error:", ex,src0,trg0)
        continue
    tokenized_bitext_list0.append((cur_loc,src_toks0,trg_toks0))
  return tokenized_bitext_list0

def index_bitext_list(list0,params0={}): #each list item = (loc/sent_id,src_tokens,trg_tokens)
  max_sent_n_tokens=params0.get("max_sent_n_tokens",1000)
  t_bitext0=tok_bitext(list0,params0)
  src_fwd_index0,trg_fwd_index0=[],[]
  for cur_loc,src_toks0,trg_toks0 in t_bitext0:
    #src_toks0,trg_toks0=t_pair0
    filtered_src0=filter_toks(src_toks0,params0)
    filtered_trg0=filter_toks(trg_toks0,params0)
    indexed_src0=[(v,cur_loc+vi/max_sent_n_tokens) for vi,v in enumerate(filtered_src0) if vi<max_sent_n_tokens and v!=""]
    indexed_trg0=[(v,cur_loc+vi/max_sent_n_tokens) for vi,v in enumerate(filtered_trg0) if vi<max_sent_n_tokens and v!=""]
    src_fwd_index0.extend(indexed_src0)
    trg_fwd_index0.extend(indexed_trg0) 
  src_fwd_index0.sort()
  trg_fwd_index0.sort()
  grouped_src=[(key,[v[1] for v in list(group)]) for key,group in groupby(src_fwd_index0,lambda x:x[0])]
  grouped_trg=[(key,[v[1] for v in list(group)]) for key,group in groupby(trg_fwd_index0,lambda x:x[0])]
  inverted_src0=dict(iter(grouped_src))  
  inverted_trg0=dict(iter(grouped_trg))  
  return inverted_src0,  inverted_trg0



def indexing_pipeline(loc_iterator,src_i,trg_i,params={}): #iterator includes both line str and line loc within a file
    cur_line="-"
    src_fwd_index0,trg_fwd_index0=[],[]
    counter=0
    bitext_list=[]
    #t0=time.time()
    while cur_line!="":
      if counter%5000==0: print(counter)
      #cur_loc=fopen.tell()
      cur_loc,f0=next(iterator) #fopen.readline()
      #print([f0])
      cur_line=f0.strip("\n\r\t")
      line_split=cur_line.split("\t")
      if len(line_split)>=max(src_i,trg_i): continue
      elif f0!="":
        src0,trg0=line_split[src_i],line_split[trg_i]
        src_toks=tok(src0)
        trg_toks=tok(trg0) #will need to use general purpose tokenization later
        src_filter_params={"exclude_numbers":True, "excluded_words":excluded_src_tokens}
        trg_filter_params={"exclude_numbers":True, "excluded_words":excluded_src_tokens}
        filtered_src=filter_toks(src_toks,params=src_filter_params) #src_toks,trg_toks
        filtered_trg=filter_toks(trg_toks,params=trg_filter_params)
        # src_sent_fwd_index=index_sent_toks(filtered_src,cur_loc)
        # trg_sent_fwd_index=index_sent_toks(filtered_trg,cur_loc)
        src_sent_fwd_index=index_sent_toks(filtered_src,cur_loc)
        trg_sent_fwd_index=index_sent_toks(filtered_trg,cur_loc)
        src_fwd_index0.extend(src_sent_fwd_index)
        trg_fwd_index0.extend(trg_sent_fwd_index)
        # for s_i,s_tok0 in enumerate(src_toks):
        #   if s_tok0.isupper():
        #     src_fwd_index0.append((s_tok0,cur_loc+0.001*s_i))
            #print((s_tok0,counter+0.001*s_i))
        #bitext_list.append((counter,cur_loc,src0,trg0))
      counter+=1
      #if counter>1000: break
    src_inv_index=get_inv_index(src_fwd_index0)
    trg_inv_index=get_inv_index(trg_fwd_index0)
    return src_inv_index,trg_inv_index
