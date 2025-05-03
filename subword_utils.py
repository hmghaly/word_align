
import math, re
import numpy as np

#this file is for helping with working with subwords, n-grams, character clusters, and so forth

#==== Subword tokenization
#25 April 2025
class subword: #create a subword tokenization model based on the token counter dict and certain parameters
  def __init__(self,counter_dict,params={}) -> None:
    self.min_size=params.get("min_size",2)
    self.max_size=params.get("max_size",4)
    self.min_token_size=params.get("min_token_size",2) #do not split into subwords if a token is equal to or less then this size
    self.padding="#"
    self.n_gram_counter={}
    for a,b in counter_dict.items():
      char_ngrams=get_char_ngrams(a,max_size=self.max_size,min_size=self.min_size,padding=self.padding)
      for ng0 in char_ngrams: self.n_gram_counter[ng0]=self.n_gram_counter.get(ng0,0)+b
  def tok(self,word):
    padded=self.padding+word+self.padding
    ng_list0=get_char_ngrams(word,max_size=self.max_size,min_size=self.min_size,padding=self.padding,include_span=True)
    list0=[]
    for ng0,span0 in ng_list0:
      count0=self.n_gram_counter.get(ng0,0)+1
      log_count0=math.log10(count0)
      log_len0=len(ng0)#*10
      wt0=log_count0*log_len0 #TODO - maybe experiment with different ways to determine weight

      list0.append((ng0, span0,wt0))    
    list0.sort(key=lambda x:-x[-1])
    used_indexes=[]
    final_list=[]
    for li0 in list0:
      ng0, span0,wt0=li0
      x0,x1=span0
      cur_indexes=list(range(x0,x1))
      intersection=list(set(cur_indexes).intersection(set(used_indexes)))
      if intersection: continue
      used_indexes.extend(cur_indexes)
      final_list.append(li0)

    #TODO - improve filling of remaining indexes
    remaining_indexes=list(set(range(len(padded))).difference(set(used_indexes)))
    for ri0 in remaining_indexes:
      span0=(ri0,ri0+1)
      chunk0=padded[ri0]
      final_list.append((chunk0,span0,0))
    final_list.sort(key=lambda x:x[1])

    return [v[0] for v in final_list]

#tokenize a token list into subwords
def tok_sw(tokens,sw_model,only_sw=True):
  final_sw_list=[]
  for t_i0,tk0 in enumerate(tokens): 
    cur_sw_list0=sw_model.tok(tk0)
    for sw0 in cur_sw_list0:
      sw_i0=len(final_sw_list)
      if only_sw: final_sw_list.append(sw0)
      else: final_sw_list.append((sw0,sw_i0,t_i0)) #include both subword index, and token index
  return final_sw_list

#create and update correspondence/matching matrix between subwords
class sw_matrix:
  def __init__(self,src_sw_counter,trg_sw_counter) -> None:
    self.src_sw_counter=src_sw_counter
    self.trg_sw_counter=trg_sw_counter
    self.src_sw_list=sorted(list(src_sw_counter.keys()))
    self.trg_sw_list=sorted(list(trg_sw_counter.keys()))
    self.src_map=dict(iter([(v,i) for i,v in enumerate(self.src_sw_list)]))
    self.trg_map=dict(iter([(v,i) for i,v in enumerate(self.trg_sw_list)]))
    self.n_src=len(self.src_sw_list)
    self.n_trg=len(self.trg_sw_list)
    #self.correspondence_array=np.zeros((self.n_src,self.n_trg))
    self.correspondence_array = np.full((self.n_src,self.n_trg), 0.5)
  def get_ids(self,input_src_sw,input_trg_sw,only_id=True):
    src_ids,trg_ids=[],[]
    for src_sw0 in list(set(input_src_sw)):
      s_id0=self.src_map.get(src_sw0)
      if s_id0!=None: 
        if only_id: src_ids.append(s_id0)
        else: src_ids.append((src_sw0,s_id0))
    for trg_sw0 in list(set(input_trg_sw)):
      t_id0=self.trg_map.get(trg_sw0)
      if t_id0!=None: 
        if only_id: trg_ids.append(t_id0)
        else: trg_ids.append((trg_sw0,t_id0))
    return src_ids,trg_ids
      

  def update(self,input_src_sw,input_trg_sw,inc=0.01):
    src_ids,trg_ids=self.get_ids(input_src_sw,input_trg_sw)
    #offset_matrix0=create_offset_matrix(src_ids,trg_ids,self.n_src,self.n_trg,inc=inc)
    self.correspondence_array=update_corr_matrix(self.correspondence_array,src_ids,trg_ids, inc=inc)

  def retr(self,input_src_sw,input_trg_sw): #retrieve corr values given pairs of subwords lists
    src_sw_ids,trg_sw_ids=self.get_ids(input_src_sw,input_trg_sw,only_id=False)
    #print("src_sw_ids",src_sw_ids)
    #print("trg_sw_ids",trg_sw_ids)
    cur_sw_corr_dict={}
    for s_tk0,s_id0 in src_sw_ids:
      for t_tk0,t_id0 in trg_sw_ids:

        val0=float(self.correspondence_array[s_id0][t_id0])
        #print(s_tk0, t_tk0,val0)
        cur_sw_corr_dict[(s_tk0,t_tk0)]=val0
    return cur_sw_corr_dict

  def normalize(self):
    self.correspondence_array=normalize_array(self.correspondence_array)

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





#13 Feb 2025
#split a string into lists of n-grams, optionally with spans
def get_char_ngrams(word,min_size=2,max_size=5,padding="#",include_span=False):
  all_char_ngrams=[]
  word=padding+word+padding
  len_word=len(word)
  for size0 in range(min_size,max_size+1):
    for i0 in range(len_word-size0+1):
      cur_chunk=word[i0:i0+size0]
      
      if include_span: all_char_ngrams.append((cur_chunk,(i0,i0+size0)))
      else: all_char_ngrams.append(cur_chunk)
  return all_char_ngrams





#Probably no longer needed
#matrix to check coordinates of matching tokens, increment if both occur, decrement if one occurs and one doesn't
def create_offset_matrix(src_i_list,trg_i_list,matrix_n,matrix_m,inc=0.01):
  temp_offset_array=np.zeros((matrix_n,matrix_m))
  temp_offset_array[tuple(src_i_list),:]=-inc
  temp_offset_array[:,tuple(trg_i_list)]=-inc
  for temp_src_i in src_i_list:
    temp_offset_array[temp_src_i,tuple(trg_i_list)]=inc
  return temp_offset_array

def normalize_array(arr):
  min_val = np.min(arr)
  max_val = np.max(arr)
  normalized_arr = (arr - min_val) / (max_val - min_val)
  return normalized_arr

#======== subwords, charachter chunks
def get_char_chunks(word0,max_chunk_size=7,exclude_inside_chunks=False):
  all_chunks=[]
  if exclude_inside_chunks: #include only chunks from beginning or from end
    for size0 in range(1,max_chunk_size+1):
        if size0>len(word0): continue
        cur_span=(0,size0)
        cur_chunk=word0[:size0]
        all_chunks.append((cur_chunk, cur_span))
        if len(word0)==size0: continue #from the end
        cur_span=(len(word0)-size0,len(word0))
        cur_chunk=word0[len(word0)-size0:]
        all_chunks.append((cur_chunk, cur_span))

  else: #include all internal chunks
      for size0 in range(1,max_chunk_size+1):
        for char_i in range(0,len(word0)-size0+1):
          cur_chunk=word0[char_i:char_i+size0]
          span=(char_i,char_i+size0)
          all_chunks.append((cur_chunk, span))
  return all_chunks





#==== for applications such as spell checking or creating word vectors
def get_neighbor_offsets(word_i,sent_words,max_offset=3):
  #cur_word=sent_words[word_i]
  neighbor_offsets=[]
  for inc0 in range(1,max_offset+1):
    prev_word,next_word="",""
    if word_i-inc0>=0: prev_word=sent_words[word_i-inc0]
    if word_i+inc0<len(sent_words): next_word=sent_words[word_i+inc0]
    neighbor_offsets+=[(prev_word,-inc0),(next_word,inc0)]
  neighbor_offsets.sort(key=lambda x:x[1])
  return neighbor_offsets
