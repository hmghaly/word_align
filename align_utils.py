import time, json, shelve, os, re, sys, itertools
from itertools import groupby
from math import log
import random
import numpy as np

try: import torch
except: pass


#from general import * 
sys.path.append("code_utils")
import general
import arabic_lib


#============================== Word/chunk/subword align paradigm ===================

#2025 - Word Alignment through matching chunks/n-grams/subwords
#create and update correspondence/matching matrix between chunks
class chunk_align_matrix:
  def __init__(self,src_counter,trg_counter,params={}) -> None:
    self.src_counter=src_counter
    self.trg_counter=trg_counter
    self.max_dim_size=params.get("max_dim_size",10000)
    self.min_chunk_count=params.get("min_chunk_count",5)
    self.min_chunk_size=params.get("min_size",2)
    self.max_chunk_size=params.get("max_size",4)
    self.padding=params.get("padding","#")
    self.src_chunk_counter,self.trg_chunk_counter={},{}
    for s_tk0,s_tk_count0 in self.src_counter.items():
      char_ngrams=general.get_char_ngrams(s_tk0,max_size=self.max_chunk_size,min_size=self.min_chunk_size,padding=self.padding)
      for ng0 in char_ngrams: self.src_chunk_counter[ng0]=self.src_chunk_counter.get(ng0,0)+s_tk_count0
    for t_tk0,t_tk_count0 in self.trg_counter.items():
      char_ngrams=general.get_char_ngrams(t_tk0,max_size=self.max_chunk_size,min_size=self.min_chunk_size,padding=self.padding)
      for ng0 in char_ngrams: self.trg_chunk_counter[ng0]=self.trg_chunk_counter.get(ng0,0)+t_tk_count0

    src_n_gram_counter_items=list(self.src_chunk_counter.items())
    src_n_gram_counter_items.sort(key=lambda x:-x[-1])
    src_n_gram_counter_items=[v for v in src_n_gram_counter_items if v[1]>=self.min_chunk_count]
    if self.max_dim_size!=None: src_n_gram_counter_items=src_n_gram_counter_items[:self.max_dim_size]
    self.src_map=dict(iter([(v,i) for i,v in enumerate([v[0] for v in src_n_gram_counter_items])]))

    trg_n_gram_counter_items=list(self.trg_chunk_counter.items())
    trg_n_gram_counter_items.sort(key=lambda x:-x[-1])
    trg_n_gram_counter_items=[v for v in trg_n_gram_counter_items if v[1]>=self.min_chunk_count]
    if self.max_dim_size!=None: trg_n_gram_counter_items=trg_n_gram_counter_items[:self.max_dim_size]
    self.trg_map=dict(iter([(v,i) for i,v in enumerate([v[0] for v in trg_n_gram_counter_items])]))


    # self.src_sw_list=sorted(list(src_sw_counter.keys()))
    # self.trg_sw_list=sorted(list(trg_sw_counter.keys()))
    # self.src_map=dict(iter([(v,i) for i,v in enumerate(self.src_sw_list)]))
    # self.trg_map=dict(iter([(v,i) for i,v in enumerate(self.trg_sw_list)]))
    self.n_src=len(src_n_gram_counter_items)
    self.n_trg=len(trg_n_gram_counter_items)
    #self.correspondence_array=np.zeros((self.n_src,self.n_trg))
    self.correspondence_array = np.full((self.n_src,self.n_trg), 0.5)
  def get_ids(self,input_src_chunks,input_trg_chunks,only_id=True):
    src_ids,trg_ids=[],[]
    for src_sw0 in list(set(input_src_chunks)):
      s_id0=self.src_map.get(src_sw0)
      if s_id0!=None:
        if only_id: src_ids.append(s_id0)
        else: src_ids.append((src_sw0,s_id0))
    for trg_sw0 in list(set(input_trg_chunks)):
      t_id0=self.trg_map.get(trg_sw0)
      if t_id0!=None:
        if only_id: trg_ids.append(t_id0)
        else: trg_ids.append((trg_sw0,t_id0))
    return src_ids,trg_ids


  def update(self,input_src_tokens,input_trg_tokens,inc=0.01):

    src_chunks,trg_chunks=[],[]
    for s_tk0 in input_src_tokens:
      char_ngrams=general.get_char_ngrams(s_tk0,max_size=self.max_chunk_size,min_size=self.min_chunk_size,padding=self.padding)
      src_chunks.extend(char_ngrams)
    for t_tk0 in input_trg_tokens:
      char_ngrams=general.get_char_ngrams(t_tk0,max_size=self.max_chunk_size,min_size=self.min_chunk_size,padding=self.padding)
      trg_chunks.extend(char_ngrams)
    src_ids,trg_ids=self.get_ids(src_chunks,trg_chunks)
    self.correspondence_array=update_corr_matrix(self.correspondence_array,src_ids,trg_ids, inc=inc)

  def retr(self,input_src_chunks,input_trg_chunks): #retrieve corr values given pairs of subwords lists
    src_sw_ids,trg_sw_ids=self.get_ids(input_src_chunks,input_trg_chunks,only_id=False)
    #print("src_sw_ids",src_sw_ids)
    #print("trg_sw_ids",trg_sw_ids)
    cur_sw_corr_dict={}
    for s_tk0,s_id0 in src_sw_ids:
      for t_tk0,t_id0 in trg_sw_ids:

        val0=float(self.correspondence_array[s_id0][t_id0])
        #print(s_tk0, t_tk0,val0)
        cur_sw_corr_dict[(s_tk0,t_tk0)]=val0
    return cur_sw_corr_dict

  # def normalize(self):
  #   self.correspondence_array=normalize_array(self.correspondence_array)
  def match(self,input_src_toks,input_trg_toks):
    cur_src_chars,cur_trg_chars=[],[]
    src_tok_chars_dict,trg_tok_chars_dict={},{}
    for s_tk0 in list(set(input_src_toks)):
      src_char_ngrams=general.get_char_ngrams(s_tk0,max_size=params0.get("max_size",3),min_size=params0.get("min_size",3),include_span=True)
      src_tok_chars_dict[s_tk0]=src_char_ngrams
      cur_src_chars.extend([v[0] for v in src_char_ngrams])
    for t_tk0 in list(set(input_trg_toks)):
      trg_char_ngrams=general.get_char_ngrams(t_tk0,max_size=params0.get("max_size",3),min_size=params0.get("min_size",3),include_span=True)
      trg_tok_chars_dict[t_tk0]=trg_char_ngrams
      cur_trg_chars.extend([v[0] for v in trg_char_ngrams])

    corr_dict0=self.retr(cur_src_chars,cur_trg_chars)

    corr_dict_items0=list(corr_dict0.items())
    corr_dict_items0.sort(key=lambda x:-x[-1])

    final_match_dict={}
    for s_tk0,s_chars_spans0 in src_tok_chars_dict.items():
      for t_tk0,t_chars_spans0 in trg_tok_chars_dict.items():
        #print(s_tk0,t_tk0)
        #char_corr_val_dict={}
        cur_corr_list=[]
        for s_char0,s_span0 in s_chars_spans0:
          for t_char0,t_span0 in t_chars_spans0:

            corr_val0=corr_dict0.get((s_char0,t_char0),0)
            #print(s_char0,t_char0,corr_val0)
            char_pair0=s_char0,t_char0
            span_pair=s_span0,t_span0
            cur_corr_list.append((char_pair0,span_pair,corr_val0))
        cur_corr_list.sort(key=lambda x:-x[-1])
        used_src_i_list,used_trg_i_list=[],[]
        #for a in cur_corr_list[:5]: print(a)
        valid_vals=[]
        for char_pair0,span_pair,corr_val0 in cur_corr_list:
          src_span0,trg_span0=span_pair
          cur_src_i_list=list(range(src_span0[0],src_span0[1]))
          cur_trg_i_list=list(range(trg_span0[0],trg_span0[1]))
          if set(used_src_i_list).intersection(set(cur_src_i_list)): continue
          if set(used_trg_i_list).intersection(set(cur_trg_i_list)): continue
          used_src_i_list.extend(cur_src_i_list)
          used_trg_i_list.extend(cur_trg_i_list)
          #print(char_pair0,span_pair,corr_val0)
          valid_vals.append(corr_val0)

        max_corr_val=max(valid_vals)
        avg_corr_val=sum(valid_vals)/len(valid_vals)
        avg_max_wt0=(max_corr_val+avg_corr_val)/2
        #print(s_tk0,t_tk0,valid_vals,max_corr_val,avg_corr_val)
        #print(s_tk0,t_tk0,round(avg_max_wt0,4))
        final_match_dict[(s_tk0,t_tk0)]=avg_max_wt0

        #print("--------")
    return final_match_dict
  def expand_update(self,src_tok_list,trg_tok_list,ex_params={}):
    #iterate over a list of pairs of tokenized src/trg sentences
    #calculate chunk freq src/trg to update the src/trg counter dicts
    #update matrix size and dimensions accordingly
    #and then update correspondences with each pair of tokenized sentences
    pass



#3 May 2025 
#apply increments to rows and columns of a matrix according to row/cols indexes - increment for correspondence coordinates
#and decrement otherwise for rows/cols indexes
def update_corr_matrix(matrix,row_indexes,col_indexes, inc=0.01):
  up_ratio,down_ratio=1+inc,1-inc
  for r_i in row_indexes:
    row_copy=matrix[r_i]
    #col_vals=row_copy[col_indexes]*up_ratio
    col_vals=row_copy[col_indexes]#*up_ratio
    col_vals_inc=(1-col_vals)*inc #increment col vals up according to how far from 1
    col_vals=col_vals+col_vals_inc


    row_copy=row_copy*down_ratio
    row_copy[col_indexes]=col_vals
    matrix[r_i]=row_copy

  for c_i in col_indexes:
    col_copy=matrix[:,c_i]
    row_vals=col_copy[row_indexes]
    col_copy=col_copy*down_ratio
    col_copy[row_indexes]=row_vals
    matrix[:,c_i]=col_copy
  return matrix

#18 May 2025
#populate corresppondence matrix between src/trg tokens
def get_sent_matching_matrix(src_tokens,trg_tokens,matching_dict,max_val=1.0):
  corr_matrix_vals=[]
  for t_0 in trg_toks0:
    cur_matrix_rows=[]
    for s_0 in src_toks0:
      if t_0==s_0: val0=max_val
      else: val0=matched.get((s_0,t_0),0)
      cur_matrix_rows.append(val0)
    corr_matrix_vals.append(cur_matrix_rows)
  return corr_matrix_vals

#18 May 2025
#create data for an excel table to visualize alignment (rows +headers)
def get_corr_table(src_tokens,trg_tokens,matching_dict):
  corr_matrix_vals0=get_sent_matching_matrix(src_tokens,trg_tokens,matching_dict)
  header_items=[""]+src_tokens
  all_rows=[]
  for row_i0,row0 in enumerate(corr_matrix_vals0):
    t_0=trg_tokens[row_i0]
    #row_items=[t_0]+[str(round(v,4)) for v in row0]
    row_items=[t_0]+[round(v,4) for v in row0]
    all_rows.append(row_items)
  return all_rows, header_items

#18 May 2025
#identify adjeacent points - horizontal - vertical diagonal (up & down)
#to create spans out of pairs of adjacent points 
def get_adj_pts(x,y,x_dim,y_dim,max_offset=2):
  next_x_list=[]
  next_y_list=[]
  prev_y_list=[]
  for of0 in range(1,max_offset+1): #get possible horizontal offsets
    next_x0=x+of0
    if next_x0>=x_dim: break
    next_x_list.append(next_x0)
  for of0 in range(1,max_offset+1): #get possible vertical offsets (next)
    next_y0=y+of0
    if next_y0>=y_dim: break
    next_y_list.append(next_y0)
  for of0 in range(1,max_offset+1): #get possible vertical offsets (prev)
    prev_y0=y-of0
    if prev_y0<0: break
    prev_y_list.append(prev_y0)

  all_next_pts=[]
  all_next_pts.extend([(x,y1) for y1 in next_y_list]) #vertical next points
  all_next_pts.extend([(x1,y) for x1 in next_x_list]) #horizontal next points
  all_next_pts.extend([(x1,y1) for x1 in next_x_list for y1 in next_y_list+prev_y_list]) #diagonal adjacent points
  return sorted(all_next_pts)






#5 May 2025
#for pairs of items with their weights, and we want to get the top items without duplication
#of any src/trg part of each item, or we want to make sure each src/trg element gets the
#top corresponding one - mainly used for word alignment
def get_corr_top(src_items,trg_items, pair_corr_dict,fill_all=True):
  corr_items=sorted(list(pair_corr_dict.items()),key=lambda x:-x[-1])
  used_src_items,used_trg_items=[],[]
  min_size0=min(len(src_items),len(trg_items)) #possibly this will not be needed
  max_size0=max(len(src_items),len(trg_items))

  #first run
  final_items=[]
  for pair0,wt0 in corr_items:
    s_0,t_0=pair0
    if not s_0 in src_items or not t_0 in trg_items: continue
    
    if s_0 in used_src_items or t_0 in used_trg_items: continue
    used_src_items.append(s_0)
    used_trg_items.append(t_0)
    final_items.append((pair0,wt0))
    if len(final_items)==min_size0: break
  if len(final_items)==max_size0: return final_items 

  #second run - to make sure all rows/cols (src/trg) items are covered
  if not fill_all: return final_items
  for pair0,wt0 in corr_items:
    s_0,t_0=pair0
    if not s_0 in src_items or not t_0 in trg_items: continue

    if s_0 in used_src_items and t_0 in used_trg_items: continue
    final_items.append((pair0,wt0))
    if len(final_items)==max_size0: break
  return final_items


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

#get lines of a file by going to each item in the index list (file locations)
def get_lines_simple(file_obj,index_list):
  line_list=[]
  for a in index_list:
    line_loc=int(a)
    file_obj.seek(line_loc)
    line0=file_obj.readline()
    line_list.append(line0.strip())
  return line_list

#Most important functions
def get_index_matching(src_tokens0,trg_tokens0,src_index0,trg_index0,max_phrase_length=3,min_intersection_count=10): #match src/trg phrase based on index matching intersection/ratio
  src_phrase_index_loc_dict=retr_sent_phrase_indexes(src_tokens0,src_index0,max_phrase_length=max_phrase_length)
  trg_phrase_index_loc_dict=retr_sent_phrase_indexes(trg_tokens0,trg_index0,max_phrase_length=max_phrase_length)  
  matching_list=[]
  matching_dict={}
  for src_phrase0,src_locs_indexes0 in src_phrase_index_loc_dict.items():
    src_locs0,src_indexes0=src_locs_indexes0
    
    src_key=tuple(src_phrase0.split())
    src_n_tokens=len(src_key)
    for trg_phrase0,trg_locs_indexes0 in trg_phrase_index_loc_dict.items():
      trg_locs0,trg_indexes0=trg_locs_indexes0
      #trg_n_tokens=len(trg_phrase0.split())
      trg_key=tuple(trg_phrase0.split())
      trg_n_tokens=len(trg_key)      
      #if trg_n_tokens<2 and src_n_tokens>3: continue #avoid pairs where the source is much longer than target

      if src_phrase0==trg_phrase0: ratio1,intersection1=0.5,100 #we do not match indexes for identical phrases, but assign them arbitrary values
      else: ratio1,intersection1=get_src_trg_intersection(src_indexes0,trg_indexes0)
      #if int(round(ratio1))==1 and (src_n_tokens>1 or trg_n_tokens>1): continue #avoid coincidences of cooccurence of some phrases
      # test_phrase="united nations"
      # if src_phrase0==test_phrase: print(src_phrase0,trg_phrase0, ratio1,intersection1)
      if intersection1<min_intersection_count: continue
      adj_ratio=ratio1
      # matching_key=(src_key,trg_key)
      # matching_dict[matching_key]=adj_ratio
      # intersection1=10*int(intersection1*0.1)

      #print("src_phrase0",src_phrase0,"trg_phrase0",trg_phrase0,round(ratio1,4),intersection1)
      # len_diff=abs(len(src_phrase0.split())-len(trg_phrase0.split()))
      # adj_ratio=ratio1-0.00001*len_diff
      
      #if intersection1<100: adj_ratio=adj_ratio*(0.01*intersection1)
      matching_list.append((src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection1,adj_ratio))
  return matching_list
  #final_matching_list=

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
  # for a,b in phrase_index_loc_dict.items():
  #   print(a,b)



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

def get_src_trg_intersection(src_list0,trg_list0):
  src_list0=[int(v) for v in src_list0]
  trg_list0=[int(v) for v in trg_list0]
  intersection0=list(set(src_list0).intersection(set(trg_list0)))
  ratio0=len(intersection0)/(len(src_list0)+len(trg_list0)-len(intersection0))
  return ratio0,len(intersection0)

#17 March 2023
def get_aligned_path(matching_list,n_epochs=5,max_dist=4,max_span=None,min_wt=0.001):
  matching_list.sort(key=lambda x:(-round(x[-1],1),x[-2],-len(x[0])-len(x[1]),x[-1])) #sorting criteria - rounded weight, frequency,length, and then just weight
  el_dict={}
  el_child_dict={}
  src_span_el_dict,trg_span_el_dict={},{}
  
  ml_new=[]
  #original_ml=[]
  used_src_phrases,used_trg_phrases=[],[]
  for a in matching_list: #we process the matching list in order to obtain the top matches with their spans
    #TODO: use the counter of used instances spans of src/trg phrases based on the number of spans of a valid pair
    src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection0,ratio0=a
    valid=True
    for src_span0 in src_locs0:
      for trg_span0 in trg_locs0: 
        el0=(src_span0,trg_span0)
        #original_ml.append((el0,ratio0)) 
        src_span_el_dict[src_span0]=src_span_el_dict.get(src_span0,[])+[(el0,ratio0)] 
        trg_span_el_dict[trg_span0]=trg_span_el_dict.get(trg_span0,[])+[(el0,ratio0)] 
    if src_phrase0 in used_src_phrases or trg_phrase0 in used_trg_phrases: valid=False
    if ratio0<min_wt: valid=False

    if not valid: continue
    used_src_phrases.append(src_phrase0)
    used_trg_phrases.append(trg_phrase0)   
    ml_new.append(a) #this is where we store the valid matching phrases with their weights and spans
    #print(">>>>>>>>",a)

  for a in ml_new: #now we create the elements of span pairs
    src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection0,ratio0=a
    for src_span0 in src_locs0:
      src_start0,src_end0=src_span0
      for trg_span0 in trg_locs0:
        el0=(src_span0,trg_span0)
        found_wt=el_dict.get(el0,0)
        if ratio0>found_wt: 
          el_dict[el0]=ratio0
          #print("added el to dict:", el0,ratio0)
  
  child_dict={}
  used_pair_wt_dict={}
  cur_max_wt0=0
  for epoch0 in range(n_epochs):
    el_items=list(el_dict.items())
    #print("epoch0",epoch0,"items:",len(el_items))
    for i0,item0 in enumerate(el_items):
      el0,wt0=item0
      src_span0,trg_span0=el0
      for item1 in el_items[i0+1:]:
        el1,wt1=item1
        cur_pair_key=(el0,el1)
        combined_wt_check=used_pair_wt_dict.get(cur_pair_key)
        #if pair was used before, and its combined wt is equal to what it was before, skip
        if combined_wt_check==None or combined_wt_check<wt0+wt1: used_pair_wt_dict[cur_pair_key]=wt0+wt1
        else: continue
        src_span1,trg_span1=el1
        cur_src_dist=get_span_dist(src_span0,src_span1)
        cur_trg_dist=get_span_dist(trg_span0,trg_span1) 
        if cur_src_dist>max_dist or cur_trg_dist>max_dist: continue
        if cur_src_dist<0 or cur_trg_dist<0: continue
        if cur_src_dist<1 and src_span0!=src_span1: continue
        if cur_trg_dist<1 and trg_span0!=trg_span1: continue
        if src_span0==src_span1 and cur_trg_dist>2: continue
        if trg_span0==trg_span1 and cur_src_dist>2: continue
        combined_wt01=wt0+wt1
        combined_el01=combine_els(el0,el1) 
        combined_src_span,combined_trg_span=combined_el01
        if max_span!=None and combined_src_span[1]-combined_src_span[0]>max_span: continue #if larger than max span
        if max_span!=None and combined_trg_span[1]-combined_trg_span[0]>max_span: continue

        found_wt=el_dict.get(combined_el01,0)
        if combined_wt01>found_wt:
          el_dict[combined_el01]=combined_wt01
          child_dict[combined_el01]=(el0,el1)

    el_items=list(el_dict.items())
    el_items.sort(key=lambda x:-x[-1])
    used_src,used_trg=[],[]
    filled_used_src,filled_used_trg=[],[] #used src/trg for filling purposes - corresponding to src/trg locs already filled by elements without children
    epoch_final_els0=[]
    src_span_dict,trg_span_dict={},{}
    for el0,el_wt0 in el_items: #we refine the el_dict items to get the most highly weighted elements and their children as our solution
      src_span0,trg_span0=el0
      src_range0=list(range(src_span0[0],src_span0[1]+1))
      trg_range0=list(range(trg_span0[0],trg_span0[1]+1))
      if any([v in used_src for v in src_range0]): continue
      if any([v in used_trg for v in trg_range0]): continue
      used_src.extend(src_range0)
      used_trg.extend(trg_range0)
      epoch_final_els0.append((el0,el_wt0))
    final_total_wt=sum([v[1] for v in epoch_final_els0])
    #print("final_total_wt",final_total_wt)
    #for a in epoch_final_els0:
    #   print("final el0:",a)
    # print("==================================")
    if cur_max_wt0>0 and cur_max_wt0==final_total_wt: break
    cur_max_wt0=final_total_wt
  final_els=[]
  for el0,wt0 in epoch_final_els0:  
    children=get_rec_el_children(el0,child_dict,[])
    #final_els.append((el0,wt0,children))
    for ch0 in children:
      sub_children=child_dict.get(ch0,[])
      final_els.append((ch0,el_dict.get(ch0,0),sub_children))
  return final_els

#2 Jan 2023
def get_aligned_path_OLD(matching_list,n_epochs=3,max_dist=4,max_src_span=6,dist_penalty=0.1,top_n=2):
  #matching_list.sort(key=lambda x:-x[-1])
  matching_list.sort(key=lambda x:(-round(x[-1],1),x[-2],-len(x[0])-len(x[1]),x[-1])) #sorting criteria - rounded weight, frequency,length, and then just weight
  #print("all_matching",len(matching_list))
  #src_start_dict,src_end_dict={},{}
  el_dict={}
  el_child_dict={}
  src_span_el_dict,trg_span_el_dict={},{}
  
  ml_new=[]
  original_ml=[]
  used_src_phrases,used_trg_phrases=[],[]
  for a in matching_list: #we process the matching list in order to obtain the top matches with their spans
    #TODO: use the counter of used instances spans of src/trg phrases based on the number of spans of a valid pair
    src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection0,ratio0=a
    valid=True
    for src_span0 in src_locs0:
      for trg_span0 in trg_locs0: 
        el0=(src_span0,trg_span0)
        original_ml.append((el0,ratio0)) 
        src_span_el_dict[src_span0]=src_span_el_dict.get(src_span0,[])+[(el0,ratio0)] 
        trg_span_el_dict[trg_span0]=trg_span_el_dict.get(trg_span0,[])+[(el0,ratio0)] 
    if src_phrase0 in used_src_phrases or trg_phrase0 in used_trg_phrases: valid=False
    if ratio0<0.01: valid=False

    if not valid: continue
    used_src_phrases.append(src_phrase0)
    used_trg_phrases.append(trg_phrase0)   
    ml_new.append(a) #this is where we store the valid matching phrases with their weights and spans
    #print(">>>>>>>>",a)

  for a in ml_new: #now we create the elements of span pairs
    src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection0,ratio0=a
    for src_span0 in src_locs0:
      src_start0,src_end0=src_span0
      for trg_span0 in trg_locs0:
        el0=(src_span0,trg_span0)
        found_wt=el_dict.get(el0,0)
        if ratio0>found_wt: el_dict[el0]=ratio0
          
  cur_items=list(el_dict.items()) #we do an intial iterative run to get a basic alignment
  new_combined_items=combine_items_rec(cur_items,el_dict)
  for a in new_combined_items:
    new_el,new_el_wt,new_el_children=a
    found_wt=el_dict.get(new_el,0)
    if new_el_wt>found_wt:
      el_dict[new_el]=new_el_wt
      el_child_dict[new_el]=new_el_children

  el_items=list(el_dict.items()) #now the el_dict is populated with also bigger elements by combining smaller ones
  el_items.sort(key=lambda x:-x[-1])
  used_src,used_trg=[],[]
  filled_used_src,filled_used_trg=[],[] #used src/trg for filling purposes - corresponding to src/trg locs already filled by elements without children
  final_els0=[]
  without_children=[]
  src_span_dict,trg_span_dict={},{}
  for el0,el_wt0 in el_items: #we refine the el_dict items to get the most highly weighted elements and their children as our solution
    src_span0,trg_span0=el0
    src_range0=list(range(src_span0[0],src_span0[1]+1))
    trg_range0=list(range(trg_span0[0],trg_span0[1]+1))
    if any([v in used_src for v in src_range0]): continue
    if any([v in used_trg for v in trg_range0]): continue
    used_src.extend(src_range0)
    used_trg.extend(trg_range0)
    children=get_rec_el_children(el0,el_child_dict,[])
    for ch0 in children:
      sub_children=el_child_dict.get(ch0,[])
      final_els0.append((ch0,el_dict.get(ch0,0),sub_children))
      if sub_children==[]: 
        without_children.append((ch0,el_dict.get(ch0,0)))
        ch_src_span0,ch_trg_span0=ch0
        ch_src_range0=list(range(ch_src_span0[0],ch_src_span0[1]+1))
        ch_trg_range0=list(range(ch_trg_span0[0],ch_trg_span0[1]+1)) 
        filled_used_src.extend(ch_src_range0) #we obtain the src/trg range used for each child element      
        filled_used_trg.extend(ch_trg_range0) 
        src_span_dict[ch_src_span0]=ch0
        trg_span_dict[ch_trg_span0]=ch0 
  
  #Now we start to work on elements not covered in the solution, mainly ortho elements: elements with vertical and horizontal spans
  new_el_dict=dict(el_dict)
  new_el_child_dict=dict(el_child_dict)
  for el0,el_wt0 in without_children:
    new_el_dict[el0]=el_wt0
    src_span0,trg_span0=el0
    cur_src_range0,cur_trg_range0=get_el_ranges(el0)
    net_src_range=list(set(filled_used_src).difference(set(cur_src_range0))) 
    net_trg_range=list(set(filled_used_trg).difference(set(cur_trg_range0)))
    corr_src_span_els=src_span_el_dict.get(src_span0,[]) #we get elements matching same src/trg
    corr_trg_span_els=trg_span_el_dict.get(trg_span0,[]) 
    valid_src_els=[(el0,el_wt0)]
    valid_trg_els=[(el0,el_wt0)]
    for corr_el0,corr_el_wt0 in corr_src_span_els: #but are valid as they don't violate the used src/trg locs from the solution
      if corr_el0==el0: continue
      corr_src_span0,corr_trg_span0=combine_els(el0,corr_el0) 
      check_corr_src0=check_span_in_list(corr_src_span0,net_src_range)
      check_corr_trg0=check_span_in_list(corr_trg_span0,net_trg_range)
      if check_corr_src0 or check_corr_trg0: continue
      valid_src_els.append((corr_el0,corr_el_wt0)) #in this case, we add the new element 
    for corr_el0,corr_el_wt0 in corr_trg_span_els:
      if corr_el0==el0: continue
      corr_src_span0,corr_trg_span0=combine_els(el0,corr_el0) 
      check_corr_src0=check_span_in_list(corr_src_span0,net_src_range)
      check_corr_trg0=check_span_in_list(corr_trg_span0,net_trg_range)
      if check_corr_src0 or check_corr_trg0: continue
      valid_trg_els.append((corr_el0,corr_el_wt0))
    # print("valid_src_els",valid_src_els)
    # print("valid_trg_els",valid_trg_els)
    new_src_els,new_trg_els=[],[] #we start to combine ortho elements together to make bigger elements
    if len(valid_src_els)>1: new_src_els=combine_items_rec(valid_src_els,el_dict,n_epochs0=1, allow_ortho=True) #match_el_lists(valid_src_els,valid_src_els,el_dict,allow_ortho=True)
    if len(valid_trg_els)>1: new_trg_els=combine_items_rec(valid_trg_els,el_dict,n_epochs0=1,allow_ortho=True) #match_el_lists(valid_trg_els,valid_trg_els,el_dict,allow_ortho=True)
    #TODO: multiple iterations to account for longer ortho elements such as acronyms
    for vs in new_src_els: #and now we populate the new element dictionary with the new ortho elements
      vs_el0,vs_el_wt0,vs_children=vs
      found_wt=new_el_dict.get(vs_el0,0)
      if vs_el_wt0>found_wt: 
        new_el_dict[vs_el0]=vs_el_wt0
        new_el_child_dict[vs_el0]=vs_children
    for vt in new_trg_els: 
      vt_el0,vt_el_wt0,vt_children=vt
      found_wt=new_el_dict.get(vt_el0,0)
      if vt_el_wt0>found_wt: 
        new_el_dict[vt_el0]=vt_el_wt0
        new_el_child_dict[vt_el0]=vt_children      
  for el0,el_wt0 in original_ml: #we also look into the original values, in case something was left out
    src_span0,trg_span0=el0
    check_corr_src0=check_span_in_list(src_span0,filled_used_src)
    check_corr_trg0=check_span_in_list(trg_span0,filled_used_trg)
    if check_corr_src0 or check_corr_trg0: continue    
    found_wt=new_el_dict.get(el0,0)
    if el_wt0>found_wt: new_el_dict[el0]=el_wt0

  #Now obtaining the final solution, after we identify the new ortho/unused elements in addition to the current solution
  all_items=list(new_el_dict.items())
  new_combined_items=combine_items_rec(cur_items,el_dict,allow_ortho=False)
  for a in new_combined_items:
    new_el,new_el_wt,new_el_children=a
    found_wt=new_el_dict.get(new_el,0)
    if new_el_wt>found_wt:
      new_el_dict[new_el]=new_el_wt
      new_el_child_dict[new_el]=new_el_children

  #And here is the final solution
  el_items=list(new_el_dict.items())
  el_items.sort(key=lambda x:-x[-1])
  final_els0=[]
  used_src,used_trg=[],[]
  without_children=[]
  for el0,el_wt0 in el_items:
    src_span0,trg_span0=el0
    src_range0=list(range(src_span0[0],src_span0[1]+1))
    trg_range0=list(range(trg_span0[0],trg_span0[1]+1))
    if any([v in used_src for v in src_range0]): continue
    if any([v in used_trg for v in trg_range0]): continue
    used_src.extend(src_range0)
    used_trg.extend(trg_range0)
    children=get_rec_el_children(el0,new_el_child_dict,[])
    for ch0 in children:
      sub_children=new_el_child_dict.get(ch0,[])
      final_els0.append((ch0,new_el_dict.get(ch0,0),sub_children))
  return final_els0

#1 Jan 2023
# def get_aligned_path(matching_list,max_dist=4,n_epochs=3,max_src_span=6,dist_penalty=0.1,top_n=2):
#   #matching_list.sort(key=lambda x:-x[-1])
#   matching_list.sort(key=lambda x:(-round(x[-1],1),x[-2],-len(x[0])-len(x[1]),x[-1])) #sorting criteria - rounded weight, frequency,length, and then just weight
#   #print("all_matching",len(matching_list))
#   #src_start_dict,src_end_dict={},{}
#   el_dict={}
#   el_child_dict={}
#   src_span_el_dict,trg_span_el_dict={},{}
  
#   ml_new=[]
#   original_ml=[]
#   used_src_phrases,used_trg_phrases=[],[]
#   for a in matching_list: #we process the matching list in order to obtain the top matches with their spans
#     #TODO: use the counter of used instances spans of src/trg phrases based on the number of spans of a valid pair
#     src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection0,ratio0=a
#     valid=True
#     for src_span0 in src_locs0:
#       for trg_span0 in trg_locs0: 
#         el0=(src_span0,trg_span0)
#         original_ml.append((el0,ratio0)) 
#         src_span_el_dict[src_span0]=src_span_el_dict.get(src_span0,[])+[(el0,ratio0)] 
#         trg_span_el_dict[trg_span0]=trg_span_el_dict.get(trg_span0,[])+[(el0,ratio0)] 
#     if src_phrase0 in used_src_phrases or trg_phrase0 in used_trg_phrases: valid=False
#     if ratio0<0.01: valid=False

#     if not valid: continue
#     used_src_phrases.append(src_phrase0)
#     used_trg_phrases.append(trg_phrase0)   
#     ml_new.append(a) #this is where we store the valid matching phrases with their weights and spans
#     #print(">>>>>>>>",a)

#   for a in ml_new: #now we create the elements of span pairs
#     src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection0,ratio0=a
#     for src_span0 in src_locs0:
#       src_start0,src_end0=src_span0
#       for trg_span0 in trg_locs0:
#         el0=(src_span0,trg_span0)
#         found_wt=el_dict.get(el0,0)
#         if ratio0>found_wt: el_dict[el0]=ratio0
          
#   cur_items=list(el_dict.items()) #we do an intial iterative run to get a basic alignment
#   cur_item_list0=list(cur_items)
#   cur_item_list1=list(cur_items)
#   for epoch0 in range(n_epochs): 
#     #print("cur_item_list0",len(cur_item_list0),"cur_item_list1",len(cur_item_list1))
#     new_items=match_el_lists(cur_item_list0,cur_item_list1,el_dict,penalty=dist_penalty,max_src_span=max_src_span)
#     cur_item_list0=[]
#     for a in new_items:
#       #print(">>>",a)
#       new_el,new_el_wt,new_el_children=a
#       found_wt=el_dict.get(new_el,0)
#       if new_el_wt>found_wt:
#         el_dict[new_el]=new_el_wt
#         el_child_dict[new_el]=new_el_children
#         cur_item_list0.append((new_el,new_el_wt))
#     cur_item_list1=list(el_dict.items())
#   #print("cur_item_list0",len(cur_item_list0),"cur_item_list1",len(cur_item_list1))

#   el_items=list(el_dict.items()) #now the el_dict is populated with also bigger elements by combining smaller ones
#   el_items.sort(key=lambda x:-x[-1])
#   used_src,used_trg=[],[]
#   filled_used_src,filled_used_trg=[],[] #used src/trg for filling purposes - corresponding to src/trg locs already filled by elements without children
#   final_els0=[]
#   without_children=[]
#   src_span_dict,trg_span_dict={},{}
#   for el0,el_wt0 in el_items: #we refine the el_dict items to get the most highly weighted elements and their children as our solution
#     src_span0,trg_span0=el0
#     src_range0=list(range(src_span0[0],src_span0[1]+1))
#     trg_range0=list(range(trg_span0[0],trg_span0[1]+1))
#     if any([v in used_src for v in src_range0]): continue
#     if any([v in used_trg for v in trg_range0]): continue
#     used_src.extend(src_range0)
#     used_trg.extend(trg_range0)
#     children=get_rec_el_children(el0,el_child_dict,[])
#     for ch0 in children:
#       sub_children=el_child_dict.get(ch0,[])
#       final_els0.append((ch0,el_dict.get(ch0,0),sub_children))
#       if sub_children==[]: 
#         without_children.append((ch0,el_dict.get(ch0,0)))
#         ch_src_span0,ch_trg_span0=ch0
#         ch_src_range0=list(range(ch_src_span0[0],ch_src_span0[1]+1))
#         ch_trg_range0=list(range(ch_trg_span0[0],ch_trg_span0[1]+1)) 
#         filled_used_src.extend(ch_src_range0) #we obtain the src/trg range used for each child element      
#         filled_used_trg.extend(ch_trg_range0) 
#         src_span_dict[ch_src_span0]=ch0
#         trg_span_dict[ch_trg_span0]=ch0 
  
#   #Now we start to work on elements not covered in the solution, mainly ortho elements: elements with vertical and horizontal spans
#   new_el_dict=dict(el_dict)
#   new_el_child_dict=dict(el_child_dict)
#   for el0,el_wt0 in without_children:
#     new_el_dict[el0]=el_wt0
#     src_span0,trg_span0=el0
#     cur_src_range0,cur_trg_range0=get_el_ranges(el0)
#     net_src_range=list(set(filled_used_src).difference(set(cur_src_range0))) 
#     net_trg_range=list(set(filled_used_trg).difference(set(cur_trg_range0)))
#     corr_src_span_els=src_span_el_dict.get(src_span0,[]) #we get elements matching same src/trg
#     corr_trg_span_els=trg_span_el_dict.get(trg_span0,[]) 
#     valid_src_els=[(el0,el_wt0)]
#     valid_trg_els=[(el0,el_wt0)]
#     for corr_el0,corr_el_wt0 in corr_src_span_els: #but are valid as they don't violate the used src/trg locs from the solution
#       if corr_el0==el0: continue
#       corr_src_span0,corr_trg_span0=combine_els(el0,corr_el0) 
#       check_corr_src0=check_span_in_list(corr_src_span0,net_src_range)
#       check_corr_trg0=check_span_in_list(corr_trg_span0,net_trg_range)
#       if check_corr_src0 or check_corr_trg0: continue
#       valid_src_els.append((corr_el0,corr_el_wt0)) #in this case, we add the new element 
#     for corr_el0,corr_el_wt0 in corr_trg_span_els:
#       if corr_el0==el0: continue
#       corr_src_span0,corr_trg_span0=combine_els(el0,corr_el0) 
#       check_corr_src0=check_span_in_list(corr_src_span0,net_src_range)
#       check_corr_trg0=check_span_in_list(corr_trg_span0,net_trg_range)
#       if check_corr_src0 or check_corr_trg0: continue
#       valid_trg_els.append((corr_el0,corr_el_wt0))
#     # print("valid_src_els",valid_src_els)
#     # print("valid_trg_els",valid_trg_els)
#     new_src_els,new_trg_els=[],[] #we start to combine ortho elements together to make bigger elements
#     if len(valid_src_els)>1: new_src_els=match_el_lists(valid_src_els,valid_src_els,el_dict,allow_ortho=True)
#     if len(valid_trg_els)>1: new_trg_els=match_el_lists(valid_trg_els,valid_trg_els,el_dict,allow_ortho=True)
#     #TODO: multiple iterations to account for longer ortho elements such as acronyms
#     for vs in new_src_els: #and now we populate the new element dictionary with the new ortho elements
#       vs_el0,vs_el_wt0,vs_children=vs
#       found_wt=new_el_dict.get(vs_el0,0)
#       if vs_el_wt0>found_wt: 
#         new_el_dict[vs_el0]=vs_el_wt0
#         new_el_child_dict[vs_el0]=vs_children
#     for vt in new_trg_els: 
#       vt_el0,vt_el_wt0,vt_children=vt
#       found_wt=new_el_dict.get(vt_el0,0)
#       if vt_el_wt0>found_wt: 
#         new_el_dict[vt_el0]=vt_el_wt0
#         new_el_child_dict[vt_el0]=vt_children      
#   for el0,el_wt0 in original_ml: #we also look into the original values, in case something was left out
#     src_span0,trg_span0=el0
#     check_corr_src0=check_span_in_list(src_span0,filled_used_src)
#     check_corr_trg0=check_span_in_list(trg_span0,filled_used_trg)
#     if check_corr_src0 or check_corr_trg0: continue    
#     found_wt=new_el_dict.get(el0,0)
#     if el_wt0>found_wt: new_el_dict[el0]=el_wt0

#   #Now obtaining the final solution, after we identify the new ortho/unused elements in addition to the current solution
#   all_items=list(new_el_dict.items())
#   list0=list(all_items)
#   list1=list(all_items)
#   for epoch0 in range(5): #we run it iteratively to create new bigger elements
#     new_els=match_el_lists(list0,list1,el_dict,max_src_span=6)
#     list0=[]
#     for ns in new_els: 
#       ns_el0,ns_el_wt0,ns_children=ns
#       found_wt=new_el_dict.get(ns_el0,0)
#       if ns_el_wt0>found_wt: 
#         new_el_dict[ns_el0]=ns_el_wt0
#         new_el_child_dict[ns_el0]=ns_children  
#         list0.append((ns_el0,ns_el_wt0))  
#     list1=list(new_el_dict.items())

#   #And here is the final solution
#   el_items=list(new_el_dict.items())
#   el_items.sort(key=lambda x:-x[-1])
#   final_els0=[]
#   used_src,used_trg=[],[]
#   without_children=[]
#   for el0,el_wt0 in el_items:
#     src_span0,trg_span0=el0
#     src_range0=list(range(src_span0[0],src_span0[1]+1))
#     trg_range0=list(range(trg_span0[0],trg_span0[1]+1))
#     if any([v in used_src for v in src_range0]): continue
#     if any([v in used_trg for v in trg_range0]): continue
#     used_src.extend(src_range0)
#     used_trg.extend(trg_range0)
#     children=get_rec_el_children(el0,new_el_child_dict,[])
#     for ch0 in children:
#       sub_children=new_el_child_dict.get(ch0,[])
#       final_els0.append((ch0,new_el_dict.get(ch0,0),sub_children))
#   return final_els0

#2 Jan 2023
def combine_items_rec(item_list,el_dict0={},penalty=0,max_src_span=6,n_epochs0=3,allow_ortho=False):#combine items recursively
  cur_items=list(item_list) #we do an intial iterative run to get a basic alignment
  cur_item_list0=list(cur_items)
  cur_item_list1=list(cur_items)
  final_list0=[]
  for epoch0 in range(n_epochs0): 
    new_items=match_el_lists(cur_item_list0,cur_item_list1,el_dict0,allow_ortho=allow_ortho, penalty=penalty,max_src_span=max_src_span)
    cur_item_list0=[]
    for a in new_items:
      new_el,new_el_wt,new_el_children=a
      found_wt=el_dict0.get(new_el,0)
      if new_el_wt>found_wt:
        cur_item_list0.append((new_el,new_el_wt))
        cur_item_list1.append((new_el,new_el_wt))
        final_list0.append(a)
  return final_list0


def get_el_ranges(el): #get src/trg ranges of an element
  src_span0,trg_span0=el
  src_range0=list(range(src_span0[0],src_span0[1]+1))
  trg_range0=list(range(trg_span0[0],trg_span0[1]+1))
  return  src_range0, trg_range0 

def check_span_in_list(span0,list0): #check if any point on a span is within a certain list of points
  range0=list(range(span0[0],span0[1]+1))
  return any([v in list0 for v in range0]) 

#29 Dec 2022
# def get_aligned_path(matching_list,max_dist=3,n_epochs=3,dist_penalty=0.1,top_n=2):
#   matching_list.sort(key=lambda x:-x[-1])
#   print("all_matching",len(matching_list))
#   src_start_dict,src_end_dict={},{}
#   el_dict={}
#   el_child_dict={}
#   used_src_phrases,used_trg_phrases=[],[]
#   ml_new=[]
#   original_ml=[]
#   for a in matching_list:
#     src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection0,ratio0=a
#     valid=True
#     for src_span0 in src_locs0:
#       for trg_span0 in trg_locs0: 
#         el0=(src_span0,trg_span0)
#         original_ml.append((el0,ratio0))    
#     if src_phrase0 in used_src_phrases or trg_phrase0 in used_trg_phrases: valid=False
#     used_src_phrases.append(src_phrase0)
#     used_trg_phrases.append(trg_phrase0)
#     if not valid: continue
#     ml_new.append(a)

#   matching_list.sort(key=lambda x:x[0]) #group for source phrase
#   matching_list_grouped=[list(group) for key,group in groupby(matching_list,lambda x:x[0])]
#   for grp0 in matching_list_grouped:
#     grp0.sort(key=lambda x:-x[-1])
#     corr=[]
#     for a in grp0:
#       #print("top src item", a)
#       if a[-1]<0.01 or a in ml_new: continue
#       corr.append(a)      
#       if len(corr)==top_n: break
#     ml_new.extend(corr)
#     #print("----")
#   matching_list.sort(key=lambda x:x[1]) #group for target phrase
#   matching_list_grouped=[list(group) for key,group in groupby(matching_list,lambda x:x[1])]
#   for grp0 in matching_list_grouped:
#     grp0.sort(key=lambda x:-x[-1])
#     corr=[]
#     for a in grp0:
#       #print("top trg item", a)
#       if a[-1]<0.01 or a in ml_new: continue
#       corr.append(a)      
#       if len(corr)==top_n: break
#     ml_new.extend(corr)
#     #print("-----")
#   for a in ml_new:
#     src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection0,ratio0=a
#     for src_span0 in src_locs0:
#       src_start0,src_end0=src_span0
#       for trg_span0 in trg_locs0:
#         el0=(src_span0,trg_span0)
#         found_wt=el_dict.get(el0,0)
#         if ratio0>found_wt:
#           el_dict[el0]=ratio0
#           src_start_dict[src_start0]=src_start_dict.get(src_start0,[])+[el0]
#           src_end_dict[src_end0]=src_end_dict.get(src_end0,[])+[el0]
#   cur_items=list(el_dict.items())
#   cur_item_list0=list(cur_items)
#   cur_item_list1=list(cur_items)
#   for epoch0 in range(n_epochs):
#     #print("cur_item_list0",len(cur_item_list0),"cur_item_list1",len(cur_item_list1))
#     new_items=match_el_lists(cur_item_list0,cur_item_list1,el_dict,penalty=dist_penalty)
#     cur_item_list0=[]
#     for a in new_items:
#       #print(">>>",a)
#       new_el,new_el_wt,new_el_children=a
#       found_wt=el_dict.get(new_el,0)
#       if new_el_wt>found_wt:
#         el_dict[new_el]=new_el_wt
#         el_child_dict[new_el]=new_el_children
#         cur_item_list0.append((new_el,new_el_wt))
#     cur_item_list1=list(el_dict.items())
#   #print("cur_item_list0",len(cur_item_list0),"cur_item_list1",len(cur_item_list1))

#   el_items=list(el_dict.items())
#   el_items.sort(key=lambda x:-x[-1])
#   used_src,used_trg=[],[]
#   filled_used_src,filled_used_trg=[],[] #used src/trg for filling purposes - corresponding to src/trg locs already filled by elements without children
#   final_els0=[]
#   without_children=[]
#   src_span_dict,trg_span_dict={},{}
#   for el0,el_wt0 in el_items:
#     src_span0,trg_span0=el0
#     src_range0=list(range(src_span0[0],src_span0[1]+1))
#     trg_range0=list(range(trg_span0[0],trg_span0[1]+1))
#     if any([v in used_src for v in src_range0]): continue
#     if any([v in used_trg for v in trg_range0]): continue
#     used_src.extend(src_range0)
#     used_trg.extend(trg_range0)
#     children=get_rec_el_children(el0,el_child_dict,[])
#     for ch0 in children:
#       sub_children=el_child_dict.get(ch0,[])
#       final_els0.append((ch0,el_dict.get(ch0,0),sub_children))
#       if sub_children==[]: 
#         without_children.append((ch0,el_dict.get(ch0,0)))
#         ch_src_span0,ch_trg_span0=ch0
#         ch_src_range0=list(range(ch_src_span0[0],ch_src_span0[1]+1))
#         ch_trg_range0=list(range(ch_trg_span0[0],ch_trg_span0[1]+1)) 
#         filled_used_src.extend(ch_src_range0)       
#         filled_used_trg.extend(ch_trg_range0) 
#         src_span_dict[ch_src_span0]=ch0
#         trg_span_dict[ch_trg_span0]=ch0 
#   #TODO: fill unused spans for ortho elements 
#   return final_els0

#29 Dec 2022
def match_el_lists(el_list0,el_list1,el_dict0,max_dist=3,max_src_span=4,allow_ortho=False,penalty=0.1): #match 2 lists of elements and their weights to expand to larger elements
  new_els=[]
  used_pair_dict={}
  el_list0.sort()
  el_list1.sort()
  for el0,el_wt0 in el_list0:
    src_span0,trg_span0=el0
    # src_start0,src_end0=src_span0
    for el1,el_wt1 in el_list1:
      if el1==el0: continue

      pair1,pair2=(el0,el1),(el1,el0)
      if used_pair_dict.get(pair1,False) or used_pair_dict.get(pair2,False): continue
      used_pair_dict[pair1]=True

      #pair=sorted(el0)
      src_span1,trg_span1=el1
      # src_start1,src_end1=src_span1
      # trg_start1,trg_end1=trg_span1
      #if src_start1==src_start0 and src_end1!=src_end0: continue
      trg_span_dist=get_span_dist(trg_span0,trg_span1)
      src_span_dist=get_span_dist(src_span0,src_span1)

      if allow_ortho==False:
        if trg_span1==trg_span0: continue
        if src_span1==src_span0: continue
        if src_span_dist<1 or src_span_dist>max_dist: continue
        if trg_span_dist<1 or trg_span_dist>max_dist: continue
      else:
        if trg_span1==trg_span0: 
          if src_span_dist<1 or src_span_dist>max_dist: continue
          if trg_span0[1]-trg_span0[0]>1: continue
        elif src_span1==src_span0: 
          if trg_span_dist<1 or trg_span_dist>max_dist: continue
          if src_span0[1]-src_span0[0]>1: continue
        else:
          if src_span_dist<1 or src_span_dist>max_dist: continue
          if trg_span_dist<1 or trg_span_dist>max_dist: continue
      combined_wt=el_wt1+el_wt0
      combined_el01=combine_els(el0,el1)
      combined_src_span0,combined_trg_span0=combined_el01
      if max_src_span!=None and combined_src_span0[1]-combined_src_span0[0]>max_src_span: continue #avoiding very large phrases
      #print("pair:", el0,el_wt0,el1,el_wt1,"span width:",combined_src_span0[1]-combined_src_span0[0])
      found_wt=el_dict0.get(combined_el01,0)
      if combined_wt>found_wt:
        #print(combined_el01, "combined_wt",combined_wt,"found_wt",found_wt)
        cur_penalty=0 #penalty*(src_span_dist+trg_span_dist-2)
        net_combined_wt=combined_wt-cur_penalty
        # el_dict[combined_el01]=net_combined_wt
        # el_child_dict[combined_el01]=(el0,el1)
        new_els.append((combined_el01,net_combined_wt,(el0,el1)))
  return new_els





def get_unigrams_bigrams(token_list, exclude_numbers=False,exclude_single_chars=False): #for a list of tokens, identify all unigrams and bigrams
  list_unigrams_bigrams0=[]
  for uni0 in list(set(token_list)):
    if exclude_numbers and uni0.isdigit():continue
    if exclude_single_chars and len(uni0)<2: continue
    if not uni0 in list_unigrams_bigrams0:list_unigrams_bigrams0.append(uni0)
  for i0 in range(len(token_list)-1):
    bi0,bi1=token_list[i0],token_list[i0+1]
    if exclude_numbers and (bi0.isdigit() or bi1.isdigit()): continue
    if exclude_single_chars and (len(bi0)<2 or len(bi1)<2): continue
    bigram0="%s %s"%(bi0,bi1)
    if not bigram0 in list_unigrams_bigrams0: list_unigrams_bigrams0.append(bigram0)
  return list_unigrams_bigrams0

def get_unigram_locs(tok_list0):
  enum_list=[(v,i) for i,v in enumerate(tok_list0)]
  enum_list.sort()
  grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(enum_list,lambda x:x[0])]
  loc_dict0=dict(iter(grouped))
  return loc_dict0  

#6 Jan 2023
def get_ngram_key(phrase0,ngram=2): #a unigram/bigram or more ngram words as a key for a src phrase, for easy retrieval
  phrase_split=phrase0.split()
  if len(phrase_split)==1: return phrase0
  return " ".join(phrase_split[:ngram])


def get_tokens_ngrams(tokens0,max_ngram_size=5):
  all_phrases=[]
  for size0 in range(1,max_ngram_size+1):
    for token_i in range(0,len(tokens0)-size0+1):
      cur_phrase_tokens=tokens0[token_i:token_i+size0]
      cur_phrase=" ".join(cur_phrase_tokens) #tokens0[token_i:token_i+size0]      
      span=(token_i,token_i+size0)
      all_phrases.append((cur_phrase, span))
  return all_phrases

# def get_tokens_ngrams(tokens0,ngram=2): #a unigram/bigram or more ngram words as a key for a src phrase, for easy retrieval
#   ngram_list=[]
#   for ng0 in range(1,ngram+1):
#   	for i0 in range(len(tokens0)-ng0):
#   		cur_phrase=" ".join()
#   #phrase_split=phrase0.split()
#   #if len(token0)==1: return 
#   return " ".join(phrase_split[:ngram])


def create_bigram_keyed_dict(input_dict0,default_wt=1,default_freq=100,adj_wt_by_len=True): #or unigram- if src phrase is one word
  bigram_keyed_dict0={}
  for src_phrase0,corr_trg_list in input_dict0.items():
    src_phrase_key0=get_ngram_key(src_phrase0)
    tmp_dict=bigram_keyed_dict0.get(src_phrase_key0,{})
    corr_with_vals=[]
    for trg_phrase0 in corr_trg_list:
      if adj_wt_by_len: tmp_wt=default_wt*(len(src_phrase0.split())+len(trg_phrase0.split()))*0.5 #adjust the default weight by the average length of src/trg phrases
      else: tmp_wt=default_wt
      corr_with_vals.append((trg_phrase0,(default_freq,tmp_wt)))
    tmp_dict[src_phrase0]=corr_with_vals
    bigram_keyed_dict0[src_phrase_key0]=tmp_dict
  return bigram_keyed_dict0


def match_keyed_dict(src_tokens,trg_tokens,keyed_dict): #match unigram/bigramed keyed dict (phrase table/terms/acronyms/custom)
  all_matching_list=[]
  src_unigrams_bigrams=get_unigrams_bigrams(src_tokens)
  for ub in src_unigrams_bigrams:
    corr_dict=keyed_dict.get(ub)
    if corr_dict==None: continue
    for src_phrase0,corr_trg_vals in corr_dict.items():
      src_span0=general.is_in(src_phrase0.split(),src_tokens)
      if not src_span0: continue
      for trg_phrase0,trg_val0 in corr_trg_vals:
        trg_span0=general.is_in(trg_phrase0.split(),trg_tokens)
        if not trg_span0: continue
        freq0,wt0=trg_val0
        all_matching_list.append((src_phrase0,trg_phrase0,src_span0,trg_span0,freq0,wt0))
  return all_matching_list


def qa_keyed_dict(src_tokens,trg_tokens,keyed_dict,dict_type="",filter_params={}): #inspect if for a keyed dict, each phrase found in source have corresponding trg phrase
  all_qa_list=[]
  #print("testing")
  filter_params={"keep_all_tokens":True}
  src_tokens=filter_toks(src_tokens,filter_params)
  trg_tokens=filter_toks(trg_tokens,filter_params)
  src_unigrams_bigrams=get_unigrams_bigrams(src_tokens)
  for ub in src_unigrams_bigrams:
    #print(ub)
    corr_dict=keyed_dict.get(ub)
    #print(corr_dict)
    if corr_dict==None: continue
    for src_phrase0,corr_trg_vals in corr_dict.items(): #phrase is a token-ready string
      #print(src_phrase0)
      src_phrase_tokens0=src_phrase0.split()
      src_phrase_tokens0=filter_toks(src_phrase_tokens0,filter_params)
      src_span0=general.is_in(src_phrase_tokens0,src_tokens)
      new_src_span=[]
      for ss in src_span0:
        start0,end0=ss
        if end0-start0==len(src_phrase_tokens0)-1: new_src_span.append(ss)
      if not new_src_span: continue
      #the src phrase exists
      #print(src_phrase0)
      corr_trg_vals.append((src_phrase0,0)) #to account for situations where the corresponding term is also in English
      trg_corr=[]
      for trg_phrase0,trg_val0 in corr_trg_vals:
        trg_phrase_tokens0=trg_phrase0.split()
        #print(trg_phrase_tokens0)
        trg_phrase_tokens0=filter_toks(trg_phrase_tokens0,filter_params)
        trg_span0=general.is_in(trg_phrase_tokens0,trg_tokens)
        trg_corr.append((trg_phrase0,trg_span0))
      all_qa_list.append((src_phrase0,src_span0,dict_type,trg_corr))
        # if not trg_span0: continue
        # freq0,wt0=trg_val0
        # all_matching_list.append((src_phrase0,trg_phrase0,src_span0,trg_span0,freq0,wt0))
  return all_qa_list

# def qa_keyed_dict(src_tokens,trg_tokens,keyed_dict,dict_type="",filter_params={}): #inspect if for a keyed dict, each phrase found in source have corresponding trg phrase
#   all_qa_list=[]
#   #print("testing")
#   src_tokens=filter_toks(src_tokens,filter_params)
#   trg_tokens=filter_toks(trg_tokens,filter_params)
#   src_unigrams_bigrams=get_unigrams_bigrams(src_tokens)
#   for ub in src_unigrams_bigrams:
#     #print(ub)
#     corr_dict=keyed_dict.get(ub)
#     #print(corr_dict)
#     if corr_dict==None: continue
#     for src_phrase0,corr_trg_vals in corr_dict.items(): #phrase is a token-ready string
#       #print(src_phrase0)
#       src_phrase_tokens0=src_phrase0.split()
#       src_phrase_tokens0=filter_toks(src_phrase_tokens0,filter_params)
#       src_span0=general.is_in(src_phrase_tokens0,src_tokens)
#       new_src_span=[]
#       for ss in src_span0:
#         start0,end0=ss
#         if end0-start0==len(src_phrase_tokens0)-1: new_src_span.append(ss)
#       if not new_src_span: continue
#       #the src phrase exists
#       corr_trg_vals.append((src_phrase0,0)) #to account for situations where the corresponding term is also in English
#       trg_corr=[]
#       for trg_phrase0,trg_val0 in corr_trg_vals:
#         trg_phrase_tokens0=trg_phrase0.split()
#         trg_phrase_tokens0=filter_toks(trg_phrase_tokens0,filter_params)
#         trg_span0=general.is_in(trg_phrase_tokens0,trg_tokens)
#         trg_corr.append((trg_phrase0,trg_span0))
#       all_qa_list.append((src_phrase0,src_span0,dict_type,trg_corr))
#         # if not trg_span0: continue
#         # freq0,wt0=trg_val0
#         # all_matching_list.append((src_phrase0,trg_phrase0,src_span0,trg_span0,freq0,wt0))
#   return all_qa_list

# def qa_keyed_dict(src_tokens,trg_tokens,keyed_dict,filter_params={}): #inspect if for a keyed dict, each phrase found in source have corresponding trg phrase
#   all_qa_list=[]
#   src_tokens=filter_toks(src_tokens,filter_params)
#   trg_tokens=filter_toks(trg_tokens,filter_params)
#   src_unigrams_bigrams=get_unigrams_bigrams(src_tokens)
#   for ub in src_unigrams_bigrams:
#     corr_dict=keyed_dict.get(ub)
#     if corr_dict==None: continue
#     for src_phrase0,corr_trg_vals in corr_dict.items(): #phrase is a token-ready string
#       src_phrase_tokens0=src_phrase0.split()
#       src_phrase_tokens0=filter_toks(src_phrase_tokens0,filter_params)
#       src_span0=general.is_in(src_phrase_tokens0,src_tokens)
#       new_src_span=[]
#       for ss in src_span0:
#         start0,end0=ss
#         if end0-start0==len(src_phrase_tokens0)-1: new_src_span.append(ss)
#       if not new_src_span: continue
#       #the src phrase exists
#       corr_trg_vals.append((src_phrase0,0)) #to account for situations where the corresponding term is also in English
#       trg_corr=[]
#       for trg_phrase0,trg_val0 in corr_trg_vals:
#         trg_phrase_tokens0=trg_phrase0.split()
#         trg_phrase_tokens0=filter_toks(trg_phrase_tokens0,filter_params)
#         trg_span0=general.is_in(trg_phrase_tokens0,trg_tokens)
#         trg_corr.append((trg_phrase0,trg_span0))
#       all_qa_list.append((src_phrase0,src_span0,trg_corr))
#         # if not trg_span0: continue
#         # freq0,wt0=trg_val0
#         # all_matching_list.append((src_phrase0,trg_phrase0,src_span0,trg_span0,freq0,wt0))
#   return all_qa_list


#29 Dec 2022
def get_phon_matching(src_toks,trg_toks,default_ratio=0.1):
  phon_matching_list=[]
  #src_trg_phon_list=[] #just a list of all found src/trg phonetically matched tokens
  src_tok_locs=get_unigram_locs(src_toks)
  trg_tok_locs=get_unigram_locs(trg_toks)
  for src_tok0,src_spans0 in src_tok_locs.items():
    corr_trg_spans=[]
    if not src_tok0[0].isupper(): continue
    if len(src_tok0)<3: continue
    if len(src_tok0)>8: continue
    candidates0=gen_ts8(src_tok0.lower())
    src_spans0=[(v,v) for v in src_spans0]
    for cd0 in candidates0:
      if len(cd0)<3: continue
      check_trg_corr_spans=trg_tok_locs.get(cd0)
      if check_trg_corr_spans==None: continue
      trg_spans0=[(v,v) for v in check_trg_corr_spans]
      phon_matching_list.append((src_tok0,cd0,src_spans0,trg_spans0,100,default_ratio))
  return phon_matching_list

#29 Dec 2022
def get_exact_matching(src_toks,trg_toks,default_ratio=0.75):
  exact_matching_list=[]
  src_tok_locs=get_unigram_locs(src_toks)
  trg_tok_locs=get_unigram_locs(trg_toks)
  for src_tok0,src_spans0 in src_tok_locs.items():
    corr_trg_spans0=trg_tok_locs.get(src_tok0,[])
    if corr_trg_spans0==[]: continue
    src_spans0=[(v,v) for v in src_spans0]
    corr_trg_spans0=[(v,v) for v in corr_trg_spans0]
    exact_matching_list.append((src_tok0,src_tok0,src_spans0,corr_trg_spans0,100,default_ratio))
  return exact_matching_list 


#16 Dec 2022
# def match_exact_tokens(src_toks0,trg_toks0):
#   src_tok_loc_dict=get_unigram_locs(src_toks0)
#   trg_tok_loc_dict=get_unigram_locs(trg_toks0)
#   match_list0=[]
#   for cur_src_tok0,cur_src_locs0 in src_tok_loc_dict.items():
#     trg_locs=trg_tok_loc_dict.get(cur_src_tok0)
#     if trg_locs==None: continue
#     for sloc0 in cur_src_locs0:
#       for tloc0 in trg_locs:
#         src_span0=(sloc0,sloc0)
#         trg_span0=(tloc0,tloc0)
#         match_item=(src_span0,trg_span0,0.5,1000) # ratio= 0.5 - freq = 100
#         match_list0.append(match_item)
#   match_list0=sorted(list(set(match_list0)))
#   return match_list0
          



#Supporting/helper functions
#16 Dec 2022
def add_padding(token_list):
  if token_list[0]=="<s>" and token_list[-1]=="</s>": return token_list
  return ["<s>"]+token_list+["</s>"]


#Geometric and recursive functions
#16 Dec 2022
def check_el_pair(el0,el1,allow_ortho=True,max_dist=None, max_ortho_span=2): #check if two elements can be combined -if they do not overlap, with ortho and dist requirements
  if el0==el1: return False
  src_span0,trg_span0=el0
  src_span1,trg_span1=el1
  cur_src_dist=get_span_dist(src_span0,src_span1)
  cur_trg_dist=get_span_dist(trg_span0,trg_span1)    
  if not allow_ortho: #check ortho cases -vertical/horizontal co-inciding spans
    if src_span0==src_span1 or trg_span0==trg_span1: return False
  else:
    if src_span0==src_span1:
      if src_span0[1]-src_span0[0]>max_ortho_span: return False #if els have same src span, but it is large e.g. (5,10),(5,10)
      elif cur_trg_dist<1: return False #if overlap
      elif max_dist!=None and cur_trg_dist>max_dist: return False #if further than max distance
      else: return True
    elif trg_span0==trg_span1:
      if trg_span0[1]-trg_span0[0]>max_ortho_span: return False
      elif cur_src_dist<1: return False
      elif max_dist!=None and cur_src_dist>max_dist: return False
      else: return True
  if cur_src_dist<1: return False
  if max_dist!=None and cur_src_dist>max_dist: return False
  if cur_trg_dist<1: return False
  if max_dist!=None and cur_trg_dist>max_dist: return False  
  return True


def combine_els(el1,el2): #combine two elements into a third element
  src_span1,trg_span1=el1
  src_span2,trg_span2=el2
  x1_0,x1_1=src_span1
  x2_0,x2_1=src_span2
  y1_0,y1_1=trg_span1
  y2_0,y2_1=trg_span2
  min_x=min(x1_0,x1_1,x2_0,x2_1)
  max_x=max(x1_0,x1_1,x2_0,x2_1)
  min_y=min(y1_0,y1_1,y2_0,y2_1)
  max_y=max(y1_0,y1_1,y2_0,y2_1)
  new_src_span=(min_x,max_x)
  new_trg_span=(min_y,max_y)
  return (new_src_span,new_trg_span)


def get_span_dist(span0,span1):
  if span0[0]>span1[0] or span0[1]>span1[1]: span0,span1=span1,span0
  return span1[0]-span0[1]

# def get_span_dist_OLD(span1,span2):
#   span1_x1,span1_x2=span1
#   span2_x1,span2_x2=span2
#   d1=abs(span1_x2-span1_x1)
#   d2=abs(span2_x2-span2_x1)
#   max_x=max(span1_x1,span1_x2,span2_x1,span2_x2)
#   min_x=min(span1_x1,span1_x2,span2_x1,span2_x2)
#   d_total=max_x-min_x
#   return d_total-d1-d2

def get_rec_el_children(el0,el_child_dict0,el_list0=[],only_without_children=False): #recursively get children of an element
  cur_children0=el_child_dict0.get(el0,[])
  if only_without_children and len(cur_children0)==0: el_list0.append(el0)
  else: el_list0.append(el0)
  for ch0 in cur_children0:
    el_list0=get_rec_el_children(ch0,el_child_dict0,el_list0,only_without_children)
  return el_list0

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

def index_sent_toks(sent_toks,sent_number,max_sent_size=1000):
  indexed_sent0=[(v,sent_number+vi/max_sent_size) for vi,v in enumerate(sent_toks) if vi<max_sent_size and v!=""]
  return indexed_sent0

def get_inv_index(fwd_index):
  fwd_index.sort()
  grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(fwd_index,lambda x:x[0])]
  inverted_index=dict(iter(grouped))  
  return inverted_index


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


#6 Feb 2024
def index_src_trg_toks(src_tokens,trg_tokens,params0={}):
  max_sent_n_tokens=params0.get("max_sent_n_tokens",1000)
  #t_bitext0=tok_bitext(list0,params0)
  src_fwd_index0,trg_fwd_index0=[],[]
  for cur_loc,cur_item in enumerate(zip(src_tokens,trg_tokens)):
    src_toks0,trg_toks0=cur_item
  #for cur_loc,src_toks0,trg_toks0 in t_bitext0:
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


#Working on phrases and chunks
def extract_phrases(src_tokens,trg_tokens,aligned_elements, max_phrase_size=12, discard_empty_phrases=True):
  used_xs,used_ys=[],[]
  all_single_pts=[]
  results0=[]
  for el_item0 in aligned_elements: #identifying aligned/unaligned locs in scr/trg tokens
    el0,el_wt0=el_item0[:2]
    src_span0,trg_span0=el0
    src_range0,trg_range0=range(src_span0[0],src_span0[1]+1),range(trg_span0[0],trg_span0[1]+1)
    used_xs.extend(src_range0)
    used_ys.extend(trg_range0)
    for a in src_range0:
      for b in trg_range0: all_single_pts.append((a,b)) #identifying single points (not elements)
  aligned_elements.sort()
  for src_i0 in range(0,len(src_tokens)+1):
    for src_i1 in range(src_i0,len(src_tokens)+1): #identifying a source range
      if src_i1-src_i0>max_phrase_size: continue
      elements_inside=[]
      trg_max_i,trg_min_i=0,len(trg_tokens)+1
      for el_item0 in aligned_elements:
        el0,el_wt0=el_item0[:2]
        src_span0,trg_span0=el0
        src_range0,trg_range0=range(src_span0[0],src_span0[1]+1),range(trg_span0[0],trg_span0[1]+1)
        if src_span0[0]>=src_i0 and src_span0[1]<=src_i1:
          cur_min_trg_i,cur_max_trg_i=min(trg_span0),max(trg_span0)
          if cur_min_trg_i<trg_min_i: trg_min_i=cur_min_trg_i
          if cur_max_trg_i>trg_max_i: trg_max_i=cur_max_trg_i
          elements_inside.append((el0,el_wt0))
      valid=True
      cur_wt=0
      if len(elements_inside)>0: cur_wt=sum([v[1] for v in elements_inside])
      for a,b in all_single_pts: #check if there is any point that violates consistency
        if (b>=trg_min_i and b<=trg_max_i) and (a <src_i0 or a>src_i1): 
          valid=False
          break
      if valid==False: continue #exclude src ranges if invalid    
      if discard_empty_phrases and cur_wt==0: continue #exclude src ranges with no elements and when discarding 
      new_el_src=src_i0,src_i1
      src_phrase=src_tokens[src_i0:src_i1+1]      
      if cur_wt==0:
        trg_phrase=""
        results0.append((src_phrase,trg_phrase,cur_wt))

      new_el_trg=trg_min_i,trg_max_i
      new_el=(new_el_src,new_el_trg)

      trg_phrase=trg_tokens[trg_min_i:trg_max_i+1]
      results0.append((src_phrase,trg_phrase,cur_wt))
      for inc0 in range(1,10):
        trg_start=trg_min_i-inc0
        if trg_start in used_ys or trg_start<0: break
        for inc1 in range(1,10):
          trg_end=trg_max_i+inc1
          if trg_end in used_ys or trg_end>len(trg_tokens): break
          trg_phrase=trg_tokens[trg_start:trg_end+1]
          results0.append((src_phrase,trg_phrase,cur_wt))
  return results0


def get_aligned_chunks(aligned_elements,min_phrase_len=5): #to split a sentence into contiguous aligned chunks, based on alignment information
  all_single_pts=[]
  for el_item in aligned_elements: #identifying aligned/unaligned locs in scr/trg tokens
    el0,el_wt0=el_item[:2]
    src_span0,trg_span0=el0
    src_range0,trg_range0=range(src_span0[0],src_span0[1]+1),range(trg_span0[0],trg_span0[1]+1)
    for a in src_range0:
      for b in trg_range0: all_single_pts.append((a,b)) #identifying single points (not elements)
  chunk_boundaries=[]
  for el_item in aligned_elements: #identifying aligned/unaligned locs in scr/trg tokens
    el0,el_wt0=el_item[:2]
    src_span0,trg_span0=el0
    last_x,last_y=src_span0[-1],trg_span0[-1]
    valid=True
    for x0,y0 in all_single_pts:
      if x0<last_x and y0> last_y: valid=False 
      if x0>last_x and y0< last_y: valid=False
      if not valid: break
    if valid: chunk_boundaries.append((last_x,last_y))
  cur_x,cur_y=0,0
  new_chunk_boundaries=[]
  #new_chunk_boundaries.append((cur_x,cur_y))
  for cb_x,cb_y in chunk_boundaries:
    if cb_x-cur_x<min_phrase_len: continue
    if cb_y-cur_y<min_phrase_len: continue
    new_chunk_boundaries.append((cb_x,cb_y))
    cur_x,cur_y=cb_x,cb_y
  return new_chunk_boundaries


#6 Jan 2023
def get_tsv_bitext(tsv_fpath): #extract bitext src/trg sentences even for messy tsvs pasted from eLuna
  bitext0=[]
  tsv_fopen=open(tsv_fpath)
  for i0,line0 in enumerate(tsv_fopen):
    line_split0=line0.strip().split("\t")
    cells=[v for v in line_split0 if v]
    if len(cells)<2: continue
    src0,trg0=cells[:2]
    bitext0.append((src0,trg0))
  tsv_fopen.close()
  return bitext0


#Visual presentation of alignment - display aligned phrases
def present_aligned(src_tokens0,trg_tokens0,align_list0):
    final_list0=[]
    for el0,el_wt0,has_children in align_list0:
        src_span0,trg_span0=el0
        cur_src_phrase=src_tokens0[src_span0[0]:src_span0[1]+1]
        cur_trg_phrase=trg_tokens0[trg_span0[0]:trg_span0[1]+1]
        cur_src_phrase=" ".join(cur_src_phrase)
        cur_trg_phrase=" ".join(cur_trg_phrase)
        final_list0.append((cur_src_phrase,cur_trg_phrase,el0,el_wt0))
    return final_list0

# def present_walign_results(aligned_results): #if the output is in the form of a dict results["src"]=..., results["trg"]=..., results["align"]=...
#     src_tokens0=aligned_results.get("src",[])
#     trg_tokens0=aligned_results.get("trg",[])
#     align_list0=aligned_results.get("align",[])
#     return present_aligned(src_tokens0,trg_tokens0,align_list0)









#Phonemeic Matching for proper nouns written in latin 
t8_dict={'a': {'any': ['ا', ''], 'start': ['أ', 'ع', 'عا'], 'end': ['ى', 'ة']}, 'b': {'any': ['ب'], 'start': [], 'end': []}, 'c': {'any': ['س', 'ك', 'تش', 'ث'], 'start': [], 'end': []}, 'd': {'any': ['د', 'ض'], 'start': [], 'end': []}, 'e': {'any': ['ي', 'ا', ''], 'start': ['إ', 'ا'], 'end': ['ه', '']}, 'f': {'any': ['ف'], 'start': [], 'end': []}, 'g': {'any': ['ج', 'غ'], 'start': [], 'end': []}, 'h': {'any': ['ه', 'ح', ''], 'start': [], 'end': ['ة']}, 'i': {'any': ['ي', 'اي', ''], 'start': ['إ', 'ا', 'إي', 'ع'], 'end': []}, 'j': {'any': ['ج', 'خ', 'ي', 'ه'], 'start': [], 'end': []}, 'k': {'any': ['ك', 'ق'], 'start': [], 'end': []}, 'l': {'any': ['ل', ''], 'start': [], 'end': []}, 'm': {'any': ['م'], 'start': [], 'end': []}, 'n': {'any': ['ن'], 'start': [], 'end': []}, 'o': {'any': ['و', ''], 'start': ['أ', 'أو'], 'end': []}, 'p': {'any': ['ب'], 'start': [], 'end': []}, 'q': {'any': ['ك', 'ق', 'تش'], 'start': [], 'end': []}, 'r': {'any': ['ر'], 'start': [], 'end': []}, 's': {'any': ['س', 'ش', 'ز', 'ص'], 'start': [], 'end': []}, 't': {'any': ['ت', 'ط'], 'start': [], 'end': []}, 'u': {'any': ['و', 'ا', ''], 'start': ['أ', 'أو'], 'end': []}, 'v': {'any': ['ف'], 'start': [], 'end': []}, 'w': {'any': ['و', 'ف'], 'start': [], 'end': []}, 'x': {'any': ['كس', 'ز', 'ه'], 'start': [], 'end': []}, 'y': {'any': ['ي', 'اي'], 'start': [], 'end': ['يا']}, 'z': {'any': ['ز', 'س', 'تس', 'ث', 'ش'], 'start': [], 'end': []}, 'sh': {'any': ['ش'], 'start': [], 'end': []}, 'ch': {'any': ['تش', 'ش', 'خ', 'ك'], 'start': [], 'end': []}, 'th': {'any': ['ث', 'ذ', 'ت', 'تح'], 'start': [], 'end': []}, 'dh': {'any': ['ذ', 'ظ'], 'start': [], 'end': []}, 'gh': {'any': ['غ', 'ج', ''], 'start': [], 'end': []}, 'kh': {'any': ['خ', 'ك'], 'start': [], 'end': []}, 'sch': {'any': ['ش', 'سك'], 'start': [], 'end': []}, 'zh': {'any': ['ج'], 'start': [], 'end': []}, 'ck': {'any': ['ك'], 'start': [], 'end': []}, 'ae': {'any': ['اي', 'ائ', 'ي', ''], 'start': [], 'end': []}, 'oi': {'any': ['وا'], 'start': [], 'end': []}, 'll': {'any': ['ل', 'ج', 'ي', 'لل'], 'start': [], 'end': []}, 'é': {'any': ['ي', ''], 'start': [], 'end': ['يه']}, 'et': {'any': ['ت', 'يت'], 'start': [], 'end': ['يه']}, 'que': {'any': ['ك'], 'start': [], 'end': []}, 'ph': {'any': ['ف'], 'start': [], 'end': []}, 'aa': {'any': ['ا'], 'start': [], 'end': ['اء']}, 'el': {'any': ['ل', 'يل'], 'start': ['ال'], 'end': []}, 'al': {'any': ['ل', 'ال'], 'start': ['ال'], 'end': []}, 'ç': {'any': ['س'], 'start': [], 'end': []}, 'ce': {'any': ['سي', 'س', 'ثي', 'ث', 'تشي', 'تش'], 'start': [], 'end': []}, 'ci': {'any': ['سي', 'س', 'ثي', 'ث', 'تشي', 'تش'], 'start': [], 'end': []}, 'ñ': {'any': ['ني'], 'start': [], 'end': []}}


def gen_ts8(name): #generate transliteration
  found_items=[]
  for a,equiv_dict in t8_dict.items():
    locs=general.is_in(a,name)
    if locs==[]: continue
    for span0 in locs:
      cur_equiv=[]
      equiv_any,equiv_start,equiv_end=equiv_dict.get("any",[]),equiv_dict.get("start",[]),equiv_dict.get("end",[])
      if span0[0]==0 and equiv_start!=[]: cur_equiv=equiv_start
      elif span0[-1]==len(name)-1 and equiv_end!=[]: cur_equiv=list(set(equiv_any+equiv_end))
      else: cur_equiv=equiv_any
      found_items.append((a,cur_equiv, span0))
  for i0 in range(len(name)-1):
    if name[i0]==name[i0+1]:
      equiv_dict=t8_dict.get(name[i0],{})
      equiv=equiv_dict.get("any",[])
      if i0==0: equiv=equiv_dict.get("start",[])
      #double_equiv=[v+v for v in equiv]
      double_equiv=[]
      full_equiv=list(set(equiv+double_equiv))
      span0=(i0,i0+1)#[]
      found_items.append((name[i0:i0+2],full_equiv,span0))
  found_items.sort(key=lambda x:-len(x[0]))
  used_locs=[]
  final=[]
  for fi in found_items:
    src0,equiv0,span0=fi
    span_range=list(range(span0[0],span0[1]+1))
    if any([v in used_locs for v in span_range]): continue
    used_locs.extend(span_range)
    final.append((span0,equiv0))
  final.sort()
  candidates=[""]
  for f_locs,f_equivs in final:
    #print(f_locs,f_equivs)
    new_candidates=[]
    for cd0 in candidates:
      for eq0 in f_equivs: new_candidates.append(cd0+eq0)
    candidates=new_candidates
  return list(set(candidates))


#=============== This is how we reload the transliteration dict
# from code_utils.pandas_utils import *

# transliteration_link='https://docs.google.com/spreadsheets/d/e/2PACX-1vTeFLaZRLK3v2b65mxY7fiqvk4a8IRdmkPOHFStk15DEVhU8LuBsaqBalHhgY3G7T51beZYzyzbTtEN/pub?output=xlsx'
# t8_wb_obj=get_workbook_obj(transliteration_link)
# cols=["en","ar-any","ar-start","ar-end"]
# t8_data=get_sheets_cols(t8_wb_obj,["Sheet1"],cols,exclude_empty=False)
# t8_dict={}
# for item0 in t8_data:
#   en0,ar_any0,ar_start0,ar_end0=item0
#   if ar_any0.strip()=="": continue
#   tmp_dict={}
#   tmp_dict["any"]=[v if v!="-" else "" for v in ar_any0.split()]
#   tmp_dict["start"]=[v if v!="-" else "" for v in ar_start0.split()]
#   tmp_dict["end"]=[v if v!="-" else "" for v in ar_end0.split()]
#   #ar_split=[v if v!="-" else "" for v in ar0.split()]
#   t8_dict[en0]=tmp_dict





#retrieve line from a text file given the position at the file
def go2line(fpath0,loc0,size0=None):
  fopen0=open(fpath0)
  fopen0.seek(loc0)
  #line0=fopen0.readline()
  if size0!=None: line0=fopen0.read(size0)
  else: line0=fopen0.readline()
  line0=line0.split("\n")[0]
  fopen0.close()
  return line0

#Maybe needed
def temp_tok(txt): #temporary tokenization function
  return re.findall("\w+",txt)

def apply_trie(src_toks0,trg_toks0,trie0):
  match_list0=[]
  for i0 in range(len(src_toks0)):
    for i1 in range(i0,len(src_toks0)):
      src_span0=(i0,i1)
      items=src_toks0[i0:i1+1]+[""]
      cur_val=general.walk_trie(trie0,items,terminal_item="")
      if cur_val==None: continue
      for val0 in cur_val:
        trg_phrase0,trg_ratio0,trg_freq0=val0
        trg_locs=general.is_in(trg_phrase0,trg_toks0)
        for trg_span0 in trg_locs:
          match_item=(src_span0,trg_span0,trg_ratio0,trg_freq0)
          match_list0.append(match_item)
  match_list0=sorted(list(set(match_list0)))
  return match_list0




def retr(phrase_tokens,inv_index): #retrieve a phrase
    out_dict={}
    final_indexes=inv_index.get(phrase_tokens[0],[]) #get_tok_indexes(phrase_tokens[0],inv_index)
    if final_indexes==None: final_indexes=[]
    #cur_phrase=tuple([phrase_tokens[0]])
    #out_dict[cur_phrase]=final_indexes
    for token_i,cur_token in enumerate(phrase_tokens):
        if token_i==0: continue
        if cur_token=="": continue
        #if token_i>max_phrase_len: continue
        cur_phrase=tuple(phrase_tokens[:token_i+1])
        cur_token_indexes=inv_index.get(cur_token,[]) #get_tok_indexes(cur_token,inv_index)
        cur_token_indexes_offset=offset_indexes(cur_token_indexes,token_i)
        #final_indexes=get_index_intersection(final_indexes,cur_token_indexes_offset)
        #final_indexes=list(set(final_indexes).intersection(set(cur_token_indexes_offset)))
        final_indexes=get_offset_intersection(final_indexes,cur_token_indexes_offset)
        if final_indexes==[]: continue
        #out_dict[cur_phrase]=final_indexes
        #if final_indexes==None: final_indexes=inv_index0.get(cur_token)
    if final_indexes==None: final_indexes=[]
    return final_indexes



def retr_OLD(phrase_tokens,inv_index): #retrieve a phrase
    out_dict={}
    final_indexes=get_tok_indexes(phrase_tokens[0],inv_index)
    cur_phrase=tuple([phrase_tokens[0]])
    out_dict[cur_phrase]=final_indexes
    for token_i,cur_token in enumerate(phrase_tokens):
        if token_i==0: continue
        if cur_token=="": continue
        #if token_i>max_phrase_len: continue
        cur_phrase=tuple(phrase_tokens[:token_i+1])
        cur_token_indexes=get_tok_indexes(cur_token,inv_index)
        cur_token_indexes_offset=offset_results(cur_token_indexes,token_i)
        final_indexes=get_index_intersection(final_indexes,cur_token_indexes_offset)
        if final_indexes=={}: continue
        out_dict[cur_phrase]=final_indexes
        #if final_indexes==None: final_indexes=inv_index0.get(cur_token)
    return out_dict



#OLD - not needed - many of these assume results come in multiple dictionaries of indverted indexes
def get_size_factor(size0): #account for larger phrases - such as month names - by giving a small factor to increase their weight
  factor0=log(10+size0)/2
  return factor0

def count_results(result_dict0):
  count0=0
  for a,b in result_dict0.items():count0+=len(b)
  return count0

def list_results(result_dict0):
  res_list0=[]
  for a,b in result_dict0.items():res_list0.extend(b)#count0+=len(b)
  return res_list0

#OLD
def offset_results_OLD(result_dict0,offset0,max_sent_size0=1000):
  new_dict0={}
  for a,b in result_dict0.items():
    new_b=[v-(offset0/max_sent_size0) for v in b]
    new_dict0[a]=new_b
  return new_dict0

# def offset_indexes(index_list0,offset0,max_sent_size0=1000):
#   return [v-(offset0/max_sent_size0) for v in index_list0]  

def get_tok_indexes(cur_tok,cur_index_dict): #retrieving inverted index for a token from a multi-inverted index dict
    output={}
    for index_id,inv_index_dict in cur_index_dict.items():
        output[index_id]=inv_index_dict.get(cur_tok,[])
    return output

#OLD
def get_index_intersection_OLD(index_dict1,offset_index_dict2): #when we are getting phrase indexes of multiple tokens
  combined_dict0={}
  for index_id,cur_indexes in index_dict1.items():
    offset_indexes=offset_index_dict2.get(index_id,[])
    intersection0=list(set(cur_indexes).intersection(set(offset_indexes)))
    if len(intersection0)==0: continue
    combined_dict0[index_id]=intersection0
  return combined_dict0


#we start here, getting from the meta shelve the locations of the indexes of this word in each of the inverted index text files
def get_word_indexes(word1,index_prefix1,retr_params1): #index_prefix is either src/trg
  index_dir1=retr_params1.get("index_dir") #main directory where the inverted index text files are stored
  meta_suffix1=retr_params1.get("meta_suffix","meta") #suffix of the shelve meta file (usually sr-meta.shelve or trg-meta.shelve)
  max_n_index_files=retr_params1.get("max_n_index_files",50) #maximum number of inverted index files to process
  cur_meta_shelve_path=os.path.join(index_dir1,"%s-%s.shelve"%(index_prefix1,meta_suffix1))
  cur_meta_shelve_open=shelve.open(cur_meta_shelve_path)
  cur_meta_found=cur_meta_shelve_open.get(word1,{})
  result_dict={}
  
  n_results=0
  elapsed_list=[]
  t0=time.time()
  meta_index_items=list(cur_meta_found.items())
  
  if max_n_index_files!=None: meta_index_items=meta_index_items[:max_n_index_files]
  #print(meta_index_items)
  #return result_dict
  for index_id,index_loc in meta_index_items:
    #print(index_id,index_loc)
    cur_loc0,cur_size0=index_loc
    cur_txt_fpath=os.path.join(index_dir1,"%s-%s.txt"%(index_prefix1,index_id)) 
    #print(cur_txt_fpath,cur_loc0,cur_size0)
    cur_meta_line=go2line(cur_txt_fpath,cur_loc0,cur_size0)
    #cur_meta_line=go2line2(cur_txt_fpath,cur_loc0)
    cur_raw_indexes_str=cur_meta_line.strip().split("\t")[1]
    cur_raw_indexes=json.loads(cur_raw_indexes_str)
    result_dict[index_id]=cur_raw_indexes
    #n_results+=len(cur_raw_indexes)
  #result_dict["n"]=n_results
  #print(len(result_dict.keys()))
  return result_dict

def get_result_lines(result_dict1,bitext_fpath1,n_results1=20,n_items_per_meta1=50):
  final_results=[]
  for index_id,indexes0 in result_dict1.items():
    if n_items_per_meta1!=None: indexes0=indexes0[:n_items_per_meta1]
    for ind0 in indexes0:
      final_results.append((index_id,ind0))

  final_results.sort(key=lambda x:x[-1]-int(x[-1]))
  final_src_trg_items=[]
  for res0 in final_results[:n_results1]:
    index_id,ind0=res0
    #cur_line0=go2line2(bitext_fpath1,int(ind0))
    cur_line0=go2line(bitext_fpath1,int(ind0))
    cur_split0=cur_line0.strip().split("\t")
    if len(cur_split0)!=2: continue
    src0,trg0=cur_split0
    final_src_trg_items.append((src0,trg0,ind0,index_id))  
  return final_src_trg_items


def get_index_match_ratio_count(index_dict1,index_dict2): #match src/trg indexes
  index1_count,index2_count,intersection_count=0,0,0
  for index_id,cur_indexes1 in index_dict1.items():
    cur_indexes2=index_dict2.get(index_id,[])
    cur_indexes1=[int(v) for v in cur_indexes1]
    cur_indexes2=[int(v) for v in cur_indexes2]

    intersection0=list(set(cur_indexes1).intersection(set(cur_indexes2)))
    index1_count+=len(cur_indexes1)
    index2_count+=len(cur_indexes2)
    intersection_count+=len(intersection0)
  ratio0=0
  if index1_count+index2_count>0: ratio0=intersection_count/(index1_count+index2_count-intersection_count)
  return ratio0, intersection_count
    #combined_dict0[index_id]=intersection0


def get_phrase_locs(tokens0,max_phrase_len=8): #identify locations of phrases of content words - excluding empty string/filtered tokens
  content_words_locs=[w_i for w_i,wd0 in enumerate(tokens0) if wd0!=""]
  all_phrases0=[]
  for ii0,cur_loc0 in enumerate(content_words_locs):
    cur_phrase=[cur_loc0]
    all_phrases0.append(list(cur_phrase))
    next_locs=content_words_locs[ii0+1:]
    for nl in next_locs:
      cur_phrase+=[nl]
      all_phrases0.append(list(cur_phrase))
  all_phrase_locs_str=[]
  for ap0 in all_phrases0:
    phrase_tokens=tokens0[ap0[0]:ap0[-1]+1]
    if len(phrase_tokens)>max_phrase_len: continue
    all_phrase_locs_str.append((tuple(phrase_tokens),ap0))
  return all_phrase_locs_str

def combine_phrase_locs(all_phrase_locs_str0):
  phrase_locs_str_sorted=sorted(all_phrase_locs_str0)
  combined_phrase_locs=[(key,[v[1] for v in list(group)]) for key,group in groupby(phrase_locs_str_sorted,lambda x:x[0])]
  phrase_locs_dict0=dict(iter(combined_phrase_locs)) # key: phrase token strings > vals: corresponding locations
  return phrase_locs_dict0


def get_phrase_locs_indexes(tokens0,res_dict0,max_phrase_len=8): 
  all_phrases_locs_str=get_phrase_locs(tokens0,max_phrase_len) #get the geometric listing of all possible phrases made of content words
  phrase_locs_dict=combine_phrase_locs(all_phrases_locs_str)
  all_phrases_locs_str.sort(key=lambda x:len(x[1])) #sort them by size
  phrase_result_dict={} #we put the results in a dictionary, where the keys are the phrase string, and the values are the index/results with proper offset
  for phrase_tokens,phrase0 in all_phrases_locs_str:
    found_phrase_indexes=phrase_result_dict.get(phrase_tokens) #check if this phrase was found in previous iterations
    if found_phrase_indexes!=None: #if it was found, we skip to the next
      #print("found already", phrase_tokens)
      continue
    #print(phrase_tokens,phrase0)
    prev_tokens=[] #to check if the phrase is just a single token or not
    last_item,prev_items=phrase0[-1],phrase0[:-1] #we need to get the location of the last token
    if len(prev_items)>0: prev_tokens=tokens0[prev_items[0]:prev_items[-1]+1] #if the phrase has multiple tokens, identify previous tokens // the ones before the last token
    first_item=phrase0[0] #the location of the first token
    last_word=tokens0[last_item] #the string of the last token
    last_offset=last_item-first_item #the offset of the last token (location of last token minus location of first token)
    cur_word_indexes=res_dict0.get(last_word,{})  #now retrieve the indexes for each word
    cur_offset_indexes=offset_results(cur_word_indexes,last_offset) #offset the indexes according to the current offset
    found_prev_tokens_index_dict=phrase_result_dict.get(tuple(prev_tokens),{}) #check if previous tokens in the phrase have indexes that were found already
    if len(prev_items)>0 and found_prev_tokens_index_dict=={}: continue #if there are previous tokens, but no indexes found for them - NEED TO CHECK
    if prev_items!=[]: 
      cur_offset_indexes=get_index_intersection(found_prev_tokens_index_dict,cur_offset_indexes) #If there are previous tokens and indexes, find the intersection -ALSO CHECK THIS
    phrase_result_dict[phrase_tokens]=cur_offset_indexes
  new_dict={}
  for a,b in phrase_locs_dict.items():
    new_dict[a]=[b,phrase_result_dict.get(a,{})]
    
  return new_dict


def get_matching_phrases_locs(phrase_start_dict,src_tokens,trg_tokens): # key: unigram-bigram string - value list of src phrases and a dict of corresponding trg phrases and their weights/freq
  new_matching_list0=[]
  cur_unigrams_bigrams=list(set(get_unigrams_bigrams(src_tokens)))
  for a in cur_unigrams_bigrams:
    res_list=phrase_start_dict.get(a,[])
    for res0 in res_list:
      res_src_phrase0,res_corr_dict=res0
      res_src_phrase_split=res_src_phrase0.split(" ")
      src_phrase_locs=general.is_in(res_src_phrase_split,src_tokens)
      if src_phrase_locs:
        for corr_trg_str0,corr_trg_vals in res_corr_dict.items():
          corr_trg_str_split=corr_trg_str0.split(" ")
          trg_freq0,trg_ratio0=corr_trg_vals
          trg_phrase_locs=general.is_in(corr_trg_str_split,trg_tokens)
          if trg_phrase_locs:
            new_matching_list0.append((res_src_phrase0,corr_trg_str0,src_phrase_locs,trg_phrase_locs,trg_freq0,trg_ratio0))  
  return new_matching_list0




def get_ne_se_dict(all_elements0,allow_ortho=False): #elements are pairs of src/trg spans - allow othogonal - vertical horizontal spans
  se_transition_dict0,ne_transition_dict0={},{} #identify the possible transitions from one element to another - southeast or northeast
  #test_transition_dict0={}
  for el0,el_wt0 in all_elements0:
    src_span0,trg_span0=el0
    se_transition_dict0[el0]={}
    ne_transition_dict0[el0]={}
    #test_transition_dict0[el0]={}
    ne_list,se_list=[],[]
    for el1,el_wt1 in all_elements0:
      if el0==el1: continue
      src_span1,trg_span1=el1
      src_span_dist=get_span_dist(src_span0,src_span1)
      trg_span_dist=get_span_dist(trg_span0,trg_span1)
      direction=None
      if src_span1[0]>src_span0[1]:
        if trg_span1[0]>trg_span0[1]: #going south east
          direction="se"
          se_transition_dict0[el0][el1]=el_wt0
        if trg_span1[1]<trg_span0[0]: #going north east
          direction="ne"
          ne_transition_dict0[el0][el1]=el_wt0
      if src_span1==src_span0 and trg_span1[0]>trg_span0[1] and src_span0[1]-src_span0[0]<2: #vertical: multiple target words/phrase corresponding to one source phrase
        direction="south"
        #se_transition_dict0[el0][el1]=el_wt0
        if allow_ortho: ne_transition_dict0[el0][el1]=el_wt0
      if trg_span1==trg_span0 and src_span1[0]>src_span0[1] and trg_span0[1]-trg_span0[0]<2: #horizontal: multiple source words/phrases corresponding to one target phrase
        direction="east"
        #ne_list.append((el1,el_wt1))
        #se_transition_dict0[el0][el1]=el_wt0
        if allow_ortho: ne_transition_dict0[el0][el1]=el_wt0

      if direction==None: continue
  return se_transition_dict0, ne_transition_dict0

def split_path_chunks(path_list0,skip_last=False): #split a path e.g. cur_list=["a","b","c","d","0"] to chunks e.g. ["a","b"], ["b","c","d"]
  path_chunks0=[]
  if skip_last: last_i0,last_i1=len(path_list0)-2,len(path_list0)-1
  else: last_i0,last_i1=len(path_list0)-1,len(path_list0)
  for path_i0 in range(last_i0):
    for path_i1 in range(path_i0+1,last_i1):
      cur_chunk=path_list0[path_i0:path_i1+1]
      path_chunks0.append(cur_chunk)
  return path_chunks0


#6 Jan 2023
def walign(src_sent,trg_sent,params0={}):
  tok_fn=params0.get("tok_fn",general.tok)
  lang2_tok_fn=params0.get("lang2_tok_fn")
  lang1=params0.get("lang1","en")
  lang2=params0.get("lang2","ar")
  cur_n_epochs=params0.get("n_epochs",5)
  cur_max_sent_size=params0.get("max_sent_size",50)
  cur_max_src_span=params0.get("max_src_span",6)
  cur_max_dist=params0.get("max_dist",3)

  src_index0=params0.get("src_index",{})
  trg_index0=params0.get("trg_index",{})
  phrase_dict0=params0.get("phrase_dict",{})
  term_dict0=params0.get("term_dict",{})
  acr_dict0=params0.get("acr_dict",{})
  custom_dict0=params0.get("custom_dict",{})
  cur_default_keyed_wt0=params0.get("default_keyed_wt",1) #default weight for keyed items (e.g. terms, acronyms, phrases)
  cur_debug=params0.get("debug",False)
  #cur_debug=False
  
  src_tokens=tok_fn(src_sent)
  if lang2_tok_fn!=None: trg_tokens=lang2_tok_fn(trg_sent)
  else: trg_tokens=tok_fn(trg_sent)
  if len(src_tokens)>cur_max_sent_size or len(trg_tokens)>cur_max_sent_size: cur_n_epochs=1
  src_tokens,trg_tokens=add_padding(src_tokens),add_padding(trg_tokens)
  src_tokens_lower=[v.lower() for v in src_tokens]
  trg_tokens_lower=[v.lower() for v in trg_tokens]
  src_tokens_filtered,trg_tokens_filtered=filter_toks(src_tokens,params0),filter_toks(trg_tokens,params0)
  all_matching=[]
  # print("src_tokens",len(src_tokens))
  # print("trg_tokens",len(trg_tokens))
  phon_match0=get_phon_matching(src_tokens,trg_tokens)
  #print("phon_match0",len(phon_match0))
  exact_match0=get_exact_matching(src_tokens,trg_tokens,default_ratio=0.25)
  #print("exact_match0",len(exact_match0))
  index_match0=get_index_matching(src_tokens_filtered,trg_tokens_filtered,src_index0,trg_index0,max_phrase_length=3,min_intersection_count=3)
  #print("index_match0",len(index_match0))
  phrase_match0=match_keyed_dict(src_tokens_lower,trg_tokens_lower,phrase_dict0)
  term_match0=match_keyed_dict(src_tokens_lower,trg_tokens_lower,term_dict0)
  acr_match0=match_keyed_dict(src_tokens,trg_tokens,acr_dict0)
  all_matching=phon_match0+exact_match0+index_match0+phrase_match0+term_match0+acr_match0

  #(matching_list,n_epochs=3,max_dist=4,max_src_span=6,dist_penalty=0.1,top_n=2)
  #align_list=get_aligned_path(all_matching,n_epochs=cur_n_epochs,max_dist=cur_max_dist,max_src_span=cur_max_src_span,dist_penalty=0)
  align_list=get_aligned_path(all_matching,n_epochs=cur_n_epochs,max_dist=cur_max_dist)
  results={}
  results["src"]=src_tokens
  results["trg"]=trg_tokens
  results["align"]=align_list
  results["terms"]=[v[:2] for v in term_match0]
  results["acr"]=[v[:2] for v in acr_match0]
  results["phon"]=[v[:2] for v in phon_match0]
  if cur_debug: results["debug"]=all_matching

  return results


#!pip install transformers==3.1.0
# import torch
# import transformers
# import itertools

# model = transformers.BertModel.from_pretrained('bert-base-multilingual-cased')
# tokenizer = transformers.BertTokenizer.from_pretrained('bert-base-multilingual-cased')

def bert_walign(src_tokens,trg_tokens,tokenizer,model,align_layer=8,n_epochs=8,max_dist=2,max_span=6):
  bert_out0=get_bert_align_list(src_tokens,trg_tokens,tokenizer=tokenizer,model=model, align_layer=align_layer)
  aligned_path0=get_aligned_path(bert_out0,n_epochs=n_epochs,max_dist=max_dist,max_span=max_span)
  return aligned_path0

def get_bert_align_list(src_tokens,trg_tokens,tokenizer,model,align_layer=8):

  #token_src, token_tgt = [tokenizer.tokenize(word) for word in sent_src], [tokenizer.tokenize(word) for word in sent_tgt]
  token_src, token_tgt = [tokenizer.tokenize(word) for word in src_tokens], [tokenizer.tokenize(word) for word in trg_tokens]
  wid_src, wid_tgt = [tokenizer.convert_tokens_to_ids(x) for x in token_src], [tokenizer.convert_tokens_to_ids(x) for x in token_tgt]
  ids_src, ids_tgt = tokenizer.prepare_for_model(list(itertools.chain(*wid_src)), return_tensors='pt', model_max_length=tokenizer.model_max_length, truncation=True)['input_ids'], tokenizer.prepare_for_model(list(itertools.chain(*wid_tgt)), return_tensors='pt', truncation=True, model_max_length=tokenizer.model_max_length)['input_ids']
  sub2word_map_src = []
  for i, word_list in enumerate(token_src):
    sub2word_map_src += [i for x in word_list]
  sub2word_map_tgt = []
  for i, word_list in enumerate(token_tgt):
    sub2word_map_tgt += [i for x in word_list]

  out_src = model(ids_src.unsqueeze(0), output_hidden_states=True)[2][align_layer][0, 1:-1]
  out_tgt = model(ids_tgt.unsqueeze(0), output_hidden_states=True)[2][align_layer][0, 1:-1]

  dot_prod = torch.matmul(out_src, out_tgt.transpose(-1, -2))

  softmax_srctgt = torch.nn.Softmax(dim=-1)(dot_prod)
  softmax_tgtsrc = torch.nn.Softmax(dim=-2)(dot_prod)

  align_dict={}
  temp_list=[]
  for i in range(len(softmax_srctgt)):
    word_i=sub2word_map_src[i]
    #src_word=sent_src[word_i] #src_tokens
    src_word=src_tokens[word_i] #src_tokens
    cur_row=softmax_srctgt[i]
    combined_row=[]
    for j in range(len(cur_row)):
      #combined_row.append((j,softmax_srctgt[i][j].item(),softmax_tgtsrc[i][j].item()))
      word_j=sub2word_map_tgt[j]
      #trg_word=sent_tgt[word_j] #trg_tokens
      trg_word=trg_tokens[word_j] #trg_tokens
      ij_val=round(softmax_srctgt[i][j].item(),4)
      ji_val=round(softmax_tgtsrc[i][j].item(),4)
      avg_val=combined_val=(ij_val+ji_val)/2
      max_val=max(ij_val,ji_val)
      new_val=0.5*(avg_val+max_val)
      #combined_val=ji_val
      if combined_val==0: continue
      if src_word=="the": continue #check - make it general
      if len(src_word.strip("_"))<2: continue
      if len(trg_word.strip("_"))<2: continue
      combined_row.append((word_j,trg_word,combined_val))
      temp_list.append(((word_i,word_j,src_word,trg_word), combined_val))
  temp_list.sort()
  grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(temp_list,lambda x:x[0])]
  raw_align_list=[]
  common_count=100
  for key0,grp0 in grouped:
    avg_val=sum(grp0)/len(grp0)
    avg_max=0.5*(max(grp0)+avg_val)
    x0,y0,src_word0,trg_word0=key0
    src_span=(x0,x0)
    trg_span=(y0,y0)
    wt0=round(avg_max,4)
    raw_align_list.append((src_word0,trg_word0,[src_span],[trg_span],common_count,wt0))
  return raw_align_list


#================= Sentence alignment
def norm_sent_size(sent_size0,step=10,max_size=400):
  if sent_size0>max_size: return max_size
  norm_val=step*round(sent_size0/step)
  return norm_val


#17 Nov 2024
class sent_align:
  def __init__(self,src_sent_list, trg_sent_list,params={}):
    self.src_sent_list=src_sent_list
    self.trg_sent_list=trg_sent_list
    self.params=params

    self.lex_dict=params.get("lex",{})

    self.default_len_ratio=params.get("default_len_ratio",1) #default length ratio between different language pairs
    src_tokenize=params.get("src_tok_function",general.tok)
    trg_tokenize=params.get("trg_tok_function",general.tok)
    self.src_tok_seg_map,self.trg_tok_seg_map=[],[]
    self.src_all_toks,self.trg_all_toks=[],[]
    self.src_fwd_index,self.trg_fwd_index=[],[]
    src_tok_counter,trg_tok_counter=0,0
    for i0,src_seg0 in enumerate(src_sent_list):
      cur_toks=src_tokenize(src_seg0)
      cur_tok_ids=[i0]*len(cur_toks)
      self.src_all_toks.extend(cur_toks)
      self.src_tok_seg_map.extend(cur_tok_ids)
      for s_tok0 in cur_toks:
        s_tok0=s_tok0.lower().strip("_")
        self.src_fwd_index.append((s_tok0,src_tok_counter))
        src_tok_counter+=1

    for j0,trg_seg0 in enumerate(trg_sent_list):
      cur_toks=trg_tokenize(trg_seg0)
      cur_tok_ids=[j0]*len(cur_toks)
      self.trg_all_toks.extend(cur_toks)
      self.trg_tok_seg_map.extend(cur_tok_ids)
      for t_tok0 in cur_toks:
        t_tok0=t_tok0.lower().strip("_")
        self.trg_fwd_index.append((t_tok0,trg_tok_counter))
        trg_tok_counter+=1

    self.src_inv_index=dict(iter([(key,[v[1] for v in list(group)]) for key,group in groupby(sorted(self.src_fwd_index,key=lambda x:x[0]),lambda x:x[0])]))
    self.trg_inv_index=dict(iter([(key,[v[1] for v in list(group)]) for key,group in groupby(sorted(self.trg_fwd_index,key=lambda x:x[0]),lambda x:x[0])]))

    self.seg_tok_matching_dict={}

    for s_tok0,s_tok_indexes0 in self.src_inv_index.items(): #TODO matching dictionary tokens #TODO matching tags
      corr_t_indexes0=self.trg_inv_index.get(s_tok0,[])
      if not corr_t_indexes0: continue
      src_seg_ids=[self.src_tok_seg_map[v] for v in s_tok_indexes0]
      trg_seg_ids=[self.trg_tok_seg_map[v] for v in corr_t_indexes0]
      #print(s_tok0,src_seg_ids,trg_seg_ids)
      for a0 in src_seg_ids:
        for b0 in trg_seg_ids:
          pt0=(a0,b0)
          self.seg_tok_matching_dict[pt0]=self.seg_tok_matching_dict.get(pt0,0)+len(s_tok0)
      #print(src_seg_ids,trg_seg_ids)

    #lexical matching
    all_src_lower=[v[0] for v in self.src_fwd_index]
    all_trg_lower=[v[0] for v in self.trg_fwd_index]

    for a,corr0 in self.lex_dict.items():

      found_src_indexes=self.src_inv_index.get(a,[])
      if len(found_src_indexes)==0: continue
      
      for src_phrase0,c_trg_phrase_list in corr0.items():
        c_src_phrase_toks=src_phrase0.split()
        src_phrase_locs=is_in(c_src_phrase_toks,all_src_lower)
        if len(src_phrase_locs)==0: continue
        src_phrase_seg_ids=[self.src_tok_seg_map[v[0]] for v in src_phrase_locs]
        src_phrase_size=len(src_phrase0)
        print(src_phrase0, src_phrase_locs,"segs",src_phrase_seg_ids, "src_phrase_size", src_phrase_size)
        for c_trg_phrase0 in c_trg_phrase_list:
          
          c_trg_phrase_toks0=c_trg_phrase0.split()
          trg_phrase_locs=is_in(c_trg_phrase_toks0,all_trg_lower)
          if len(trg_phrase_locs)==0: continue
          trg_phrase_seg_ids=[self.trg_tok_seg_map[v[0]] for v in trg_phrase_locs]
          trg_phrase_size=len(c_trg_phrase0)

          print(c_trg_phrase0,trg_phrase_locs,"trg_segs",trg_phrase_seg_ids,"trg_phrase_size",trg_phrase_size)
          avg_size0=0.5*(src_phrase_size+trg_phrase_size)
          for a0 in src_phrase_seg_ids:
            for b0 in trg_phrase_seg_ids:
              print(a0,b0, avg_size0)
              pt0=(a0,b0)
              self.seg_tok_matching_dict[pt0]=self.seg_tok_matching_dict.get(pt0,0)+avg_size0 #len(s_tok0)
        #print(c_src0,c_trg_list,c_src_toks, is_in(c_src_toks,all_src_lower),"src_size",src_size)
      #print(a,corr0,"found_src_indexes",found_src_indexes)


    self.src_len_list=[len(v) for v in src_sent_list]
    self.trg_len_list=[len(v) for v in trg_sent_list]
    self.n,self.m=len(src_sent_list), len(trg_sent_list)
    self.dp= np.full((self.n, self.m), float(0))

    self.path_dict={}
    self.span_dict={}
    self.wt_dict={}
    for i in range(self.n):
      for j in range(self.m):
        cur_val=self.dp[i][j]
        next_pt_list=[(i+1,j+1),(i+1,j+2),(i+2,j+1),(i+1,j),(i,j+1)] #TODO check further 1-many
        for next_pt in next_pt_list:
          next_i,next_j=next_pt
          next_i,next_j=min(next_i,len(self.src_len_list)),min(next_j,len(self.trg_len_list))
          src_span0,trg_span0=tuple(range(i,next_i)),tuple(range(j,next_j))
          wt0=self.cost_fn(src_span0,trg_span0)
          if next_i<self.n and next_j<self.m:
            next_val=self.dp[next_i][next_j]
            if cur_val+wt0> next_val:
              #print("updating value",next_pt,"OLD:",next_val,"NEW:",cur_val+wt0)
              self.dp[next_i][next_j]=cur_val+wt0
          next_pt_wt=self.wt_dict.get(next_pt,0)
          if cur_val+wt0> next_pt_wt:
            self.wt_dict[next_pt]=cur_val+wt0
            #next_span_pair=(tuple([next_i]),tuple([next_j]))
            self.path_dict[next_pt]=(src_span0,trg_span0)
        #print("-------")

    #for d0 in self.dp: print(d0)

    self.alignments=[]
    cur_pt=(self.n,self.m)
    next_span_pair=self.path_dict.get(cur_pt)
    while next_span_pair!=None:
      self.alignments.append(next_span_pair)
      x_offset,y_offset=len(next_span_pair[0]),len(next_span_pair[1])
      cur_pt=(cur_pt[0]-x_offset,cur_pt[1]-y_offset)
      next_span_pair=self.path_dict.get(cur_pt)

    self.alignments.reverse()
    self.aligned_pairs=[]
    self.text_pairs=[]
    for src_span0,trg_span0 in self.alignments:
      src_combined=[self.src_sent_list[v] for v in src_span0]
      trg_combined=[self.trg_sent_list[v] for v in trg_span0]
      src_text0=" ".join(src_combined)
      trg_text0=" ".join(trg_combined)
      local_align_dict={"src":{"text":src_text0,"ids":src_span0},"trg":{"text": trg_text0,"ids":trg_span0}}
      self.aligned_pairs.append(local_align_dict)
      self.text_pairs.append((src_text0,trg_text0))

  def cost_fn(self,src_span,trg_span):
    min_cost=self.params.get("min_cost",0.01)
    combined_src_len=sum([self.src_len_list[v] for v in src_span])
    combined_trg_len=sum([self.trg_len_list[v] for v in trg_span])

    #aligning with matching characters
    size_matching_chars=0
    for a0 in src_span:
      for b0 in trg_span:
        size_matching_chars+=self.seg_tok_matching_dict.get((a0,b0),0)

    combined_src_len=self.default_len_ratio*combined_src_len #adjust src len based on default length ratio

    avg_src_trg_len=(combined_src_len+combined_trg_len)/2
    len_add=combined_src_len+combined_trg_len
    len_diff=abs(combined_src_len-combined_trg_len)
    len_cost=1-(len_diff/len_add)

    matching_chars_wt=size_matching_chars/avg_src_trg_len
    len_cost+=matching_chars_wt
    if len_cost<min_cost: len_cost=min_cost
    return len_cost#+avg_src_trg_len

# #17 Nov 2024
# class sent_align:
#   def __init__(self,src_sent_list, trg_sent_list,params={}):
#     self.src_sent_list=src_sent_list
#     self.trg_sent_list=trg_sent_list
#     self.params=params

#     self.default_len_ratio=params.get("default_len_ratio",1) #default length ratio between different language pairs
#     src_tokenize=params.get("src_tok_function",general.tok)
#     trg_tokenize=params.get("trg_tok_function",general.tok)
#     self.src_tok_seg_map,self.trg_tok_seg_map=[],[]
#     self.src_all_toks,self.trg_all_toks=[],[]
#     self.src_fwd_index,self.trg_fwd_index=[],[]
#     src_tok_counter,trg_tok_counter=0,0
#     for i0,src_seg0 in enumerate(src_sent_list):
#       cur_toks=src_tokenize(src_seg0)
#       cur_tok_ids=[i0]*len(cur_toks)
#       self.src_all_toks.extend(cur_toks)
#       self.src_tok_seg_map.extend(cur_tok_ids)
#       for s_tok0 in cur_toks:
#         s_tok0=s_tok0.lower().strip("_")
#         self.src_fwd_index.append((s_tok0,src_tok_counter))
#         src_tok_counter+=1

#     for j0,trg_seg0 in enumerate(trg_sent_list):
#       cur_toks=trg_tokenize(trg_seg0)
#       cur_tok_ids=[j0]*len(cur_toks)
#       self.trg_all_toks.extend(cur_toks)
#       self.trg_tok_seg_map.extend(cur_tok_ids)
#       for t_tok0 in cur_toks:
#         t_tok0=t_tok0.lower().strip("_")
#         self.trg_fwd_index.append((t_tok0,trg_tok_counter))
#         trg_tok_counter+=1
    
#     self.src_inv_index=dict(iter([(key,[v[1] for v in list(group)]) for key,group in groupby(sorted(self.src_fwd_index,key=lambda x:x[0]),lambda x:x[0])]))
#     self.trg_inv_index=dict(iter([(key,[v[1] for v in list(group)]) for key,group in groupby(sorted(self.trg_fwd_index,key=lambda x:x[0]),lambda x:x[0])]))

#     self.seg_tok_matching_dict={}

#     for s_tok0,s_tok_indexes0 in self.src_inv_index.items(): #TODO matching dictionary tokens #TODO matching tags
#       corr_t_indexes0=self.trg_inv_index.get(s_tok0,[])
#       if not corr_t_indexes0: continue
#       src_seg_ids=[self.src_tok_seg_map[v] for v in s_tok_indexes0]
#       trg_seg_ids=[self.trg_tok_seg_map[v] for v in corr_t_indexes0]
#       #print(s_tok0,src_seg_ids,trg_seg_ids)
#       for a0 in src_seg_ids:
#         for b0 in trg_seg_ids:
#           pt0=(a0,b0)
#           self.seg_tok_matching_dict[pt0]=self.seg_tok_matching_dict.get(pt0,0)+len(s_tok0)
#       #print(src_seg_ids,trg_seg_ids)

#     self.src_len_list=[len(v) for v in src_sent_list]
#     self.trg_len_list=[len(v) for v in trg_sent_list]
#     self.n,self.m=len(src_sent_list), len(trg_sent_list)
#     self.dp= np.full((self.n, self.m), float(0))

#     self.path_dict={}
#     self.span_dict={}
#     self.wt_dict={}
#     for i in range(self.n):
#       for j in range(self.m):
#         cur_val=self.dp[i][j]
#         next_pt_list=[(i+1,j+1),(i+1,j+2),(i+2,j+1),(i+1,j),(i,j+1)] #TODO check further 1-many
#         for next_pt in next_pt_list:
#           next_i,next_j=next_pt
#           next_i,next_j=min(next_i,len(self.src_len_list)),min(next_j,len(self.trg_len_list))
#           src_span0,trg_span0=tuple(range(i,next_i)),tuple(range(j,next_j))
#           wt0=self.cost_fn(src_span0,trg_span0)
#           if next_i<self.n and next_j<self.m:
#             next_val=self.dp[next_i][next_j]
#             if cur_val+wt0> next_val:
#               #print("updating value",next_pt,"OLD:",next_val,"NEW:",cur_val+wt0)
#               self.dp[next_i][next_j]=cur_val+wt0
#           next_pt_wt=self.wt_dict.get(next_pt,0)
#           if cur_val+wt0> next_pt_wt:
#             self.wt_dict[next_pt]=cur_val+wt0
#             #next_span_pair=(tuple([next_i]),tuple([next_j]))
#             self.path_dict[next_pt]=(src_span0,trg_span0)
#         #print("-------")

#     #for d0 in self.dp: print(d0)

#     self.alignments=[]
#     cur_pt=(self.n,self.m)
#     next_span_pair=self.path_dict.get(cur_pt)
#     while next_span_pair!=None:
#       self.alignments.append(next_span_pair)
#       x_offset,y_offset=len(next_span_pair[0]),len(next_span_pair[1])
#       cur_pt=(cur_pt[0]-x_offset,cur_pt[1]-y_offset)
#       next_span_pair=self.path_dict.get(cur_pt)

#     self.alignments.reverse()
#     self.aligned_pairs=[]
#     self.text_pairs=[]
#     for src_span0,trg_span0 in self.alignments:
#       src_combined=[self.src_sent_list[v] for v in src_span0]
#       trg_combined=[self.trg_sent_list[v] for v in trg_span0]
#       src_text0=" ".join(src_combined)
#       trg_text0=" ".join(trg_combined)
#       local_align_dict={"src":{"text":src_text0,"ids":src_span0},"trg":{"text": trg_text0,"ids":trg_span0}}
#       self.aligned_pairs.append(local_align_dict)
#       self.text_pairs.append((src_text0,trg_text0))

#   def cost_fn(self,src_span,trg_span):
#     min_cost=self.params.get("min_cost",0.01)
#     combined_src_len=sum([self.src_len_list[v] for v in src_span])
#     combined_trg_len=sum([self.trg_len_list[v] for v in trg_span])

#     #aligning with matching characters
#     size_matching_chars=0
#     for a0 in src_span:
#       for b0 in trg_span:
#         size_matching_chars+=self.seg_tok_matching_dict.get((a0,b0),0)

#     combined_src_len=self.default_len_ratio*combined_src_len #adjust src len based on default length ratio

#     avg_src_trg_len=(combined_src_len+combined_trg_len)/2
#     len_add=combined_src_len+combined_trg_len
#     len_diff=abs(combined_src_len-combined_trg_len)
#     len_cost=1-(len_diff/len_add)

#     matching_chars_wt=size_matching_chars/avg_src_trg_len
#     len_cost+=matching_chars_wt
#     if len_cost<min_cost: len_cost=min_cost
#     return len_cost#+avg_src_trg_len



if __name__=="__main__":
  index_dir="indexes/un/exp3"
  params_fpath=os.path.join(index_dir,"params.json")
  with open(params_fpath) as params_fopen:
    filter_params=json.load(params_fopen) #token filtering parameteres
  #print(filter_params)
  en_ar_corpus_combined_fname="UNv1.0.en-ar-combined.txt"
  retr_params={} #retrieval parameters
  retr_params["filter_params"]=filter_params
  retr_params["index_dir"]="indexes/un/exp3"
  retr_params["meta_suffix"]="meta"
  retr_params["max_n_index_files"]=2
  retr_params["lang1"]="en"
  retr_params["lang2"]="ar"
  retr_params["exclude_numbers"]=True
  retr_params["max_phrase_dist"]=5 #maximum distance when combining two phrases while aligning
  retr_params["min_phrase_wt"]=0.0001 #minimum weight for any phrase
  retr_params["lang2_tok_fn"]=cur_ar_tok_fn
  punc_pairs={} #punctuation pairs - en/ar - we can add later phrase pairs
  punc_pairs[","]="،"
  punc_pairs[";"]="؛"
  punc_pairs["?"]="؟"
  #punc_pairs["in"]="في"
  retr_params["punc_pairs"]=punc_pairs
