import time, json, shelve, os, re, sys
from itertools import groupby
from math import log
import random


#from general import * 
sys.path.append("code_utils")
import general
import arabic_lib

def filter_toks(tok_list0,params={}):
  cur_excluded_words=params.get("excluded_words",[])
  if params.get("lower",True): tok_list0=[v.lower() for v in tok_list0] #make all words lower case or not
  if cur_excluded_words!=[]: tok_list0=[v if not v in cur_excluded_words else "" for v in tok_list0] #ignore stop words
  if params.get("exclude_single_chars",False): tok_list0=[v if len(v)>1 else "" for v in tok_list0] #ignore single character tokens
  if params.get("exclude_punc",True): tok_list0=[v if not general.is_punct(v) else "" for v in tok_list0] #ignore punctuation
  
  if params.get("ignore_ar_pre_suf",True): tok_list0=["" if v.startswith("ـ") or v.endswith("ـ") else v for v in tok_list0] #ignore arabic prefixes and suffixes
  if params.get("remove_ar_diacritics",True): tok_list0=[general.remove_diactitics(v) for v in tok_list0] #remove Arabic diacritics
  if params.get("remove_al",True): tok_list0=[v.replace("ال_","") for v in tok_list0] #remove alif laam for the beginning of Arabic words
  if params.get("normalize_taa2_marbootah",False): tok_list0=[v[:-1]+"ت"  if v.endswith("ة") else v for v in tok_list0] #normalize taa2 marbootah
  if params.get("normalize_digits",False): tok_list0=["5"*len(v) if v.isdigit() else v for v in tok_list0] #normalize numbers to just the number of digits 1995 > 5555
  #if params.get("stemming",False): tok_list0=[v else v for v in tok_list0] #stem each word or not
  #remove_al=params0.get("remove_al", False) #remocve alif laam in Arabic 
  return tok_list0

def get_size_factor(size0): #account for larger phrases - such as month names - by giving a small factor to increase their weight
  factor0=log(10+size0)/2
  return factor0

def go2line(fpath0,loc0,size0=None):
  fopen0=open(fpath0)
  fopen0.seek(loc0)
  #line0=fopen0.readline()
  if size0!=None: line0=fopen0.read(size0)
  else: line0=fopen0.readline()
  line0=line0.split("\n")[0]
  fopen0.close()
  return line0

def get_unigram_locs(tok_list0):
  enum_list=[(v,i) for i,v in enumerate(tok_list0)]
  enum_list.sort()
  grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(enum_list,lambda x:x[0])]
  loc_dict0=dict(iter(grouped))
  return loc_dict0

def count_results(result_dict0):
  count0=0
  for a,b in result_dict0.items():count0+=len(b)
  return count0

def list_results(result_dict0):
  res_list0=[]
  for a,b in result_dict0.items():res_list0.extend(b)#count0+=len(b)
  return res_list0


def offset_results(result_dict0,offset0,max_sent_size0=1000):
  new_dict0={}
  for a,b in result_dict0.items():
    new_b=[v-(offset0/max_sent_size0) for v in b]
    new_dict0[a]=new_b
  return new_dict0

def offset_indexes(index_list0,offset0,max_sent_size0=1000):
  return [v-(offset0/max_sent_size0) for v in index_list0]  

def get_tok_indexes(cur_tok,cur_index_dict): #retrieving inverted index for a token from a multi-inverted index dict
    output={}
    for index_id,inv_index_dict in cur_index_dict.items():
        output[index_id]=inv_index_dict.get(cur_tok,[])
    return output

def retr(phrase_tokens,inv_index): #retrieve a phrase
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


def get_index_intersection(index_dict1,offset_index_dict2): #when we are getting phrase indexes of multiple tokens
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

def combine_els(el1,el2):
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

def get_span_dist(span1,span2):
  span1_x1,span1_x2=span1
  span2_x1,span2_x2=span2
  d1=abs(span1_x2-span1_x1)
  d2=abs(span2_x2-span2_x1)
  max_x=max(span1_x1,span1_x2,span2_x1,span2_x2)
  min_x=min(span1_x1,span1_x2,span2_x1,span2_x2)
  d_total=max_x-min_x
  return d_total-d1-d2

def get_rec_el_children(el0,el_child_dict0,el_list0=[],only_without_children=False):
  cur_children0=el_child_dict0.get(el0,[])
  if only_without_children and cur_children0==[]: el_list0.append(el0)
  else: el_list0.append(el0)
  for ch0 in cur_children0:
    el_list0=get_rec_el_children(ch0,el_child_dict0,el_list0,only_without_children)
  return el_list0


def get_ne_se_dict(all_elements0,allow_ortho=True): #elements are pairs of src/trg spans - allow othogonal - vertical horizontal spans
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

def temp_tok(txt): #temporary tokenization function
  return re.findall("\w+",txt)


def walign(src_sent0,trg_sent0,retr_align_params0={}):
  analysis_dict={}
  t0=time.time()
  filter_params0=retr_align_params0.get("filter_params",{})
  src_index_dict0=retr_align_params0.get("src_index",{})
  trg_index_dict0=retr_align_params0.get("trg_index",{})

  extra_src_index_dict0=retr_align_params0.get("extra_src_index",{})
  extra_trg_index_dict0=retr_align_params0.get("extra_trg_index",{})
  phrase_trie_dict0=retr_align_params0.get("phrase_trie_dict",{})

  lang1=retr_align_params0.get("lang1","en")
  lang2=retr_align_params0.get("lang2","ar")
  exclude_numbers=retr_align_params0.get("exclude_numbers",False)
  apply_size_factor=retr_align_params0.get("apply_size_factor",False)
  single_pass0=retr_align_params0.get("single_pass",False)  #do only one djkestra pass on the elements
  n_epochs0=retr_align_params0.get("n_epochs",10)
  min_intersection_count0=retr_align_params0.get("min_intersection_count",10)
  min_n_indexes_per_token0=retr_align_params0.get("min_n_indexes_per_token",10)
  allow_ortho0=retr_align_params0.get("allow_ortho",False) 
  min_freq_without_penalty0=retr_align_params0.get("min_freq_without_penalty",10)
  penalty0=retr_align_params0.get("penalty",0.25)

  max_phrase_len=retr_align_params0.get("max_phrase_len",8) #when we get the phrases from a sentence
  max_sent_len=retr_align_params0.get("max_sent_len",30) #when we get the phrases from a sentence
  max_phrase_dist=retr_align_params0.get("max_phrase_dist",10) #maximum distance when combining two phrases
  min_phrase_wt=retr_align_params0.get("min_phrase_wt",0.01)
  tok_fn=retr_align_params0.get("tok_fn",general.tok)
  lang2_tok_fn=retr_align_params0.get("lang2_tok_fn")
  only_without_children0=retr_align_params0.get("only_without_children",False) #get only the elements without children 
  reward_combined_phrases=retr_align_params0.get("reward_combined_phrases",True)

  punc_pairs0=retr_align_params0.get("punc_pairs",{}) 
  src_tokens=tok_fn(src_sent0)
  if lang2=="ar" and lang2_tok_fn!=None: trg_tokens=lang2_tok_fn(trg_sent0)
  else: trg_tokens=tok_fn(trg_sent0)
  analysis_dict["params loading time"]=time.time()-t0
  t0=time.time()

  analysis_dict["src_tokens"]=len(src_tokens)
  analysis_dict["trg_tokens"]=len(trg_tokens)


  src_tokens_filtered=filter_toks(src_tokens,filter_params0)
  trg_tokens_filtered=filter_toks(trg_tokens,filter_params0) #need to make filter_tokens > OLD
  unique_src_tokens=list(set([v for v in src_tokens_filtered if v!=""]))
  unique_trg_tokens=list(set([v for v in trg_tokens_filtered if v!=""]))
  src_tokens_padded=["<s>"]+src_tokens+["</s>"] #filter_toks(self.src_tokens,filter_params0)
  trg_tokens_padded=["<s>"]+trg_tokens+["</s>"]
  src_tok_loc_dict=get_unigram_locs(src_tokens_padded)
  trg_tok_loc_dict=get_unigram_locs(trg_tokens_padded)
  src_tokens_filtered_padded=["<s>"]+src_tokens_filtered+["</s>"] #main list to be aligned
  trg_tokens_filtered_padded=["<s>"]+trg_tokens_filtered+["</s>"]

  result_dict0={}
  result_dict0["src"]=src_tokens_padded
  result_dict0["trg"]=trg_tokens_padded
  analysis_dict["tokenization and processing time"]=time.time()-t0

  if len(src_tokens)>max_sent_len or len(trg_tokens)>max_sent_len: n_epochs0=1#return result_dict0

  #Now we load the indexes for our tokens
  t0=time.time()
  src_index_dict,trg_index_dict={},{}
  src_retr_dict={}
  for ut in unique_src_tokens: 
    if ut.isdigit() and exclude_numbers: continue
    #src_index_dict[ut]=get_word_indexes(ut,"src",retr_align_params0)
    src_index_dict[ut]={}
    src_index_dict[ut]["main"]=src_index_dict0.get(ut,[])
    src_index_dict[ut]["extra"]=extra_src_index_dict0.get(ut,[])
  for ut in unique_trg_tokens: 
    if ut.isdigit() and exclude_numbers: continue
    #trg_index_dict[ut]=get_word_indexes(ut,"trg",retr_align_params0)
    trg_index_dict[ut]={}
    trg_index_dict[ut]["main"]=trg_index_dict0.get(ut,[])
    trg_index_dict[ut]["extra"]=extra_trg_index_dict0.get(ut,[])
  elapsed=time.time()-t0
  elapsed_loading_indexes=time.time()-t0
  analysis_dict["loaded indexes time"]=elapsed_loading_indexes
  #print("elapsed_loading_indexes",elapsed_loading_indexes)

  #print("src:",len(unique_src_tokens),"trg:",len(unique_trg_tokens),"elapsed:",round(elapsed,4))
  #print("now mtaching src -trg tokens/phrases")
  #Now we start the matching between src/trg tokens
  t0=time.time()

  src_output=get_phrase_locs_indexes(src_tokens_filtered_padded,src_index_dict,max_phrase_len)
  trg_output=get_phrase_locs_indexes(trg_tokens_filtered_padded,trg_index_dict,max_phrase_len)
  analysis_dict["get locs indexes"]=time.time()-t0
  t0=time.time()
  matching_list=[]
  phrase_count_src_dict,phrase_count_trg_dict={},{} #how many instances of each src/trg phrases
  for src_phrase_str,src_indexes_locs in src_output.items(): phrase_count_src_dict[src_phrase_str]=len(src_indexes_locs[0])
  for trg_phrase_str,trg_indexes_locs in trg_output.items(): phrase_count_trg_dict[trg_phrase_str]=len(trg_indexes_locs[0])

  # phrase_count_src_dict_items=list(phrase_count_src_dict.items())
  # phrase_count_src_dict_items.sort(key=lambda x:-len(x[0]))
  # for a in phrase_count_src_dict_items[:20]:
  #   print(a)
  # for trg_phrase_str,trg_indexes_locs in trg_output.items():
  #   trg_locs0,trg_indexes0=trg_indexes_locs
  #   cur_indexes=trg_indexes0.get("main",[])
  #   #print(trg_indexes0.keys())
  #   print("trg: >>", trg_phrase_str,trg_locs0, len(cur_indexes), cur_indexes[:5])


  match_item_counter=0

  for src_phrase_str,src_indexes_locs in src_output.items():
    src_locs0,src_indexes0=src_indexes_locs
    #if len(src_indexes0)<min_n_indexes_per_token0: continue
    for trg_phrase_str,trg_indexes_locs in trg_output.items():
      trg_locs0,trg_indexes0=trg_indexes_locs
      #if len(src_indexes0)<min_n_indexes_per_token0: continue
      if src_phrase_str==trg_phrase_str: 
        ratio1,intersection1=0.5, 1000
      else: 
        match_item_counter+=1
        ratio1,intersection1=get_index_match_ratio_count(src_indexes0,trg_indexes0)
      min_locs_count=min(len(src_locs0),len(trg_locs0)) #we subtract from the number of locs of each phrase the minimum
      if ratio1==0: continue
      if ratio1<min_phrase_wt: continue
      if intersection1<min_intersection_count0: continue
      if apply_size_factor: 
        avg_size=(len(src_locs0)+len(trg_locs0))/2
        ratio1=ratio1*get_size_factor(avg_size)
      matching_list.append((src_phrase_str,trg_phrase_str,src_locs0,trg_locs0,min_locs_count,intersection1,ratio1))
  # sorted_matching_list=sorted(matching_list,key=lambda x:x[-2])
  # for a in sorted_matching_list[:10]: print(a)

  matching_list.sort(key=lambda x:-x[-1])
  analysis_dict["match_item_counter"]=match_item_counter
  elapsed_got_matching_list=time.time()-t0
  analysis_dict["got matching list"]=elapsed_got_matching_list
  t0=time.time()
  # for ml1 in matching_list:
  #   src_phrase_str1,trg_phrase_str1,src_locs1,trg_locs1,min_locs_count1,intersection1,ratio1=ml1
  #   if " ".join(src_phrase_str1)=="multilateral": print(ml1)
  
  new_matching_list=[] #exclude src/trg phrases used more than the count of either
  for ml in matching_list:
    src_phrase_str,trg_phrase_str,src_locs0,trg_locs0,min_locs_count,intersection1,ratio1=ml
    #if len(trg_phrase_str)>1: print(">>>",ml)
    # if phrase_count_src_dict[src_phrase_str]>=-1 or phrase_count_trg_dict[trg_phrase_str]>=-1:
    #   print(">>>",ml)
    if phrase_count_src_dict[src_phrase_str]>0 or phrase_count_trg_dict[trg_phrase_str]>0:
      new_matching_list.append((src_phrase_str,trg_phrase_str,src_locs0,trg_locs0,intersection1,ratio1))
    phrase_count_src_dict[src_phrase_str]=phrase_count_src_dict[src_phrase_str]-min_locs_count #subtract the minimum count of instances from both src and trg
    phrase_count_trg_dict[trg_phrase_str]=phrase_count_trg_dict[trg_phrase_str]-min_locs_count

  analysis_dict["excluded used src/trg phrases"]=time.time()-t0
  t0=time.time()

  for excluded_src_tok0,excluded_src_locs0 in src_tok_loc_dict.items(): #check matching tokens with their src/trg locs from the filtered out tokens
    if excluded_src_tok0 in src_tokens_filtered_padded: continue
    excluded_trg_locs0=trg_tok_loc_dict.get(excluded_src_tok0,[])
    if excluded_trg_locs0==[]: continue
    ex_src_locs=[[v] for v in excluded_src_locs0]
    ex_trg_locs=[[v] for v in excluded_trg_locs0]
    ratio1,intersection1=0.5, 1000
    new_matching_list.append((excluded_src_tok0,excluded_src_tok0,ex_src_locs,ex_trg_locs,intersection1,ratio1))
  analysis_dict["added exact match tokens"]=time.time()-t0
  t0=time.time()

  
  for src_punc0,trg_punc0 in punc_pairs0.items(): #now let's match punctuation from the original tokens
    punc_src_locs=src_tok_loc_dict.get(src_punc0,[])
    if punc_src_locs==[]: continue
    punc_trg_locs=trg_tok_loc_dict.get(trg_punc0,[])
    if punc_trg_locs==[]: continue
    ratio1,intersection1=0.2, 100
    src_punc0,trg_punc0=tuple([src_punc0]),tuple([trg_punc0])
    punc_src_locs=[[v] for v in punc_src_locs]
    punc_trg_locs=[[v] for v in punc_trg_locs]
    new_matching_list.append((src_punc0,trg_punc0,punc_src_locs,punc_trg_locs,intersection1,ratio1))

  analysis_dict["added custom punc/prep items"]=time.time()-t0
  t0=time.time()


  new_matching_list.sort(key=lambda x:-x[-1])
  #elapsed=time.time()-t0
  span_matching_list=[]
  #print("finished matching words and phrases:", elapsed)
  #Now we have the matching list - let's align
  # el_dict={} #weight of each element
  # el_child_dict={} #children of each element
  for a in new_matching_list:
    #print(a)
    src_phrase_str,trg_phrase_str,src_locs0,trg_locs0,intersection1,ratio1=a
    for sl0 in src_locs0:
      s_min,s_max=sl0[0],sl0[-1]
      src_span0=(s_min,s_max)
      for tl0 in trg_locs0:
        t_min,t_max=tl0[0],tl0[-1]
        trg_span0=(t_min,t_max)
        span_matching_list.append((src_span0,trg_span0,ratio1,intersection1))
  analysis_dict["processed matching items to get aligned path"]=time.time()-t0
  t0=time.time()


  align_list_wt0=get_aligned_path(src_tokens_padded,trg_tokens_padded,span_matching_list, n_epochs=n_epochs0, only_without_children=only_without_children0)
  analysis_dict["obtained aligned path"]=time.time()-t0
  t0=time.time()  
  result_dict0["align"]=align_list_wt0
  result_dict0["analysis_dict"]=analysis_dict
  return result_dict0

# def walign(src_sent0,trg_sent0,retr_align_params0={}):
#   filter_params0=retr_align_params0.get("filter_params",{})
#   src_index_dict0=retr_align_params0.get("src_index",{})
#   trg_index_dict0=retr_align_params0.get("trg_index",{})

#   extra_src_index_dict0=retr_align_params0.get("extra_src_index",{})
#   extra_trg_index_dict0=retr_align_params0.get("extra_trg_index",{})
#   phrase_trie_dict0=retr_align_params0.get("phrase_trie_dict",{})

#   lang1=retr_align_params0.get("lang1","en")
#   lang2=retr_align_params0.get("lang2","ar")
#   exclude_numbers=retr_align_params0.get("exclude_numbers",False)
#   apply_size_factor=retr_align_params0.get("apply_size_factor",False)
#   single_pass=retr_align_params0.get("single_pass",False)  #do only one djkestra pass on the elements
#   max_phrase_len=retr_align_params0.get("max_phrase_len",8) #when we get the phrases from a sentence
#   max_sent_len=retr_align_params0.get("max_sent_len",30) #when we get the phrases from a sentence
#   max_phrase_dist=retr_align_params0.get("max_phrase_dist",10) #maximum distance when combining two phrases
#   min_phrase_wt=retr_align_params0.get("min_phrase_wt",0.01)
#   tok_fn=retr_align_params0.get("tok_fn",general.tok)
#   lang2_tok_fn=retr_align_params0.get("lang2_tok_fn")
#   only_without_children0=retr_align_params0.get("only_without_children",False) #get only the elements without children 
#   reward_combined_phrases=retr_align_params0.get("reward_combined_phrases",True)

#   punc_pairs0=retr_align_params0.get("punc_pairs",{}) 
#   src_tokens=tok_fn(src_sent0)
#   if lang2=="ar" and lang2_tok_fn!=None: trg_tokens=lang2_tok_fn(trg_sent0)
#   else: trg_tokens=tok_fn(trg_sent0)


#   src_tokens_filtered=filter_toks(src_tokens,filter_params0)
#   trg_tokens_filtered=filter_toks(trg_tokens,filter_params0) #need to make filter_tokens > OLD
#   unique_src_tokens=list(set([v for v in src_tokens_filtered if v!=""]))
#   unique_trg_tokens=list(set([v for v in trg_tokens_filtered if v!=""]))
#   src_tokens_padded=["<s>"]+src_tokens+["</s>"] #filter_toks(self.src_tokens,filter_params0)
#   trg_tokens_padded=["<s>"]+trg_tokens+["</s>"]
#   src_tok_loc_dict=get_unigram_locs(src_tokens_padded)
#   trg_tok_loc_dict=get_unigram_locs(trg_tokens_padded)
#   src_tokens_filtered_padded=["<s>"]+src_tokens_filtered+["</s>"] #main list to be aligned
#   trg_tokens_filtered_padded=["<s>"]+trg_tokens_filtered+["</s>"]

#   result_dict0={}
#   result_dict0["src"]=src_tokens_padded
#   result_dict0["trg"]=trg_tokens_padded

#   if len(src_tokens)>max_sent_len or len(trg_tokens)>max_sent_len: return result_dict0

#   #Now we load the indexes for our tokens
#   t0=time.time()
#   src_index_dict,trg_index_dict={},{}
#   src_retr_dict={}
#   for ut in unique_src_tokens: 
#     if ut.isdigit() and exclude_numbers: continue
#     #src_index_dict[ut]=get_word_indexes(ut,"src",retr_align_params0)
#     src_index_dict[ut]={}
#     src_index_dict[ut]["main"]=src_index_dict0.get(ut,[])
#     src_index_dict[ut]["extra"]=extra_src_index_dict0.get(ut,[])
#   for ut in unique_trg_tokens: 
#     if ut.isdigit() and exclude_numbers: continue
#     #trg_index_dict[ut]=get_word_indexes(ut,"trg",retr_align_params0)
#     trg_index_dict[ut]={}
#     trg_index_dict[ut]["main"]=trg_index_dict0.get(ut,[])
#     trg_index_dict[ut]["extra"]=extra_trg_index_dict0.get(ut,[])
#   elapsed=time.time()-t0
#   #print("src:",len(unique_src_tokens),"trg:",len(unique_trg_tokens),"elapsed:",round(elapsed,4))
#   #print("now mtaching src -trg tokens/phrases")
#   #Now we start the matching between src/trg tokens
#   t0=time.time()

#   src_output=get_phrase_locs_indexes(src_tokens_filtered_padded,src_index_dict,max_phrase_len)
#   trg_output=get_phrase_locs_indexes(trg_tokens_filtered_padded,trg_index_dict,max_phrase_len)
#   matching_list=[]
#   phrase_count_src_dict,phrase_count_trg_dict={},{} #how many instances of each src/trg phrases
#   for src_phrase_str,src_indexes_locs in src_output.items(): phrase_count_src_dict[src_phrase_str]=len(src_indexes_locs[0])
#   for trg_phrase_str,trg_indexes_locs in trg_output.items(): phrase_count_trg_dict[trg_phrase_str]=len(trg_indexes_locs[0])

#   for src_phrase_str,src_indexes_locs in src_output.items():
#     src_locs0,src_indexes0=src_indexes_locs
#     for trg_phrase_str,trg_indexes_locs in trg_output.items():
#       trg_locs0,trg_indexes0=trg_indexes_locs
#       if src_phrase_str==trg_phrase_str: 
#         ratio1,intersection1=0.5, 1000
#       else: ratio1,intersection1=get_index_match_ratio_count(src_indexes0,trg_indexes0)
#       min_locs_count=min(len(src_locs0),len(trg_locs0)) #we subtract from the number of locs of each phrase the minimum
#       if ratio1==0: continue
#       if ratio1<min_phrase_wt: continue
#       if intersection1<2: continue
#       if apply_size_factor: 
#         avg_size=(len(src_locs0)+len(trg_locs0))/2
#         ratio1=ratio1*get_size_factor(avg_size)
#       matching_list.append((src_phrase_str,trg_phrase_str,src_locs0,trg_locs0,min_locs_count,intersection1,ratio1))

#   matching_list.sort(key=lambda x:-x[-1])
#   new_matching_list=[]
#   for ml in matching_list:
#     src_phrase_str,trg_phrase_str,src_locs0,trg_locs0,min_locs_count,intersection1,ratio1=ml
#     if phrase_count_src_dict[src_phrase_str]>0 or phrase_count_trg_dict[trg_phrase_str]>0:
#       new_matching_list.append((src_phrase_str,trg_phrase_str,src_locs0,trg_locs0,intersection1,ratio1))
#     phrase_count_src_dict[src_phrase_str]=phrase_count_src_dict[src_phrase_str]-min_locs_count #subtract the minimum count of instances from both src and trg
#     phrase_count_trg_dict[trg_phrase_str]=phrase_count_trg_dict[trg_phrase_str]-min_locs_count

#   for excluded_src_tok0,excluded_src_locs0 in src_tok_loc_dict.items(): #check matching tokens with their src/trg locs from the filtered out tokens
#     if excluded_src_tok0 in src_tokens_filtered_padded: continue
#     excluded_trg_locs0=trg_tok_loc_dict.get(excluded_src_tok0,[])
#     if excluded_trg_locs0==[]: continue
#     ex_src_locs=[[v] for v in excluded_src_locs0]
#     ex_trg_locs=[[v] for v in excluded_trg_locs0]
#     ratio1,intersection1=0.5, 1000
#     new_matching_list.append((excluded_src_tok0,excluded_src_tok0,ex_src_locs,ex_trg_locs,intersection1,ratio1))

  
#   for src_punc0,trg_punc0 in punc_pairs0.items(): #now let's match punctuation from the original tokens
#     punc_src_locs=src_tok_loc_dict.get(src_punc0,[])
#     if punc_src_locs==[]: continue
#     punc_trg_locs=trg_tok_loc_dict.get(trg_punc0,[])
#     if punc_trg_locs==[]: continue
#     ratio1,intersection1=0.2, 100
#     src_punc0,trg_punc0=tuple([src_punc0]),tuple([trg_punc0])
#     punc_src_locs=[[v] for v in punc_src_locs]
#     punc_trg_locs=[[v] for v in punc_trg_locs]
#     new_matching_list.append((src_punc0,trg_punc0,punc_src_locs,punc_trg_locs,intersection1,ratio1))

#   new_matching_list.sort(key=lambda x:-x[-1])
#   elapsed=time.time()-t0
#   span_matching_list=[]
#   #print("finished matching words and phrases:", elapsed)
#   #Now we have the matching list - let's align
#   # el_dict={} #weight of each element
#   # el_child_dict={} #children of each element
#   for a in new_matching_list:
#     #print(a)
#     src_phrase_str,trg_phrase_str,src_locs0,trg_locs0,intersection1,ratio1=a
#     for sl0 in src_locs0:
#       s_min,s_max=sl0[0],sl0[-1]
#       src_span0=(s_min,s_max)
#       for tl0 in trg_locs0:
#         t_min,t_max=tl0[0],tl0[-1]
#         trg_span0=(t_min,t_max)
#         span_matching_list.append((src_span0,trg_span0,ratio1,intersection1))
        

#         #src_span0,trg_span0,ratio0,freq0
#         # el0=((s_min,s_max) ,(t_min,t_max))
#         # el_dict[el0]=ratio1

#   align_list_wt0=get_aligned_path(src_tokens_padded,trg_tokens_padded,span_matching_list)
#   result_dict0["align"]=align_list_wt0
#   return result_dict0



def tok_bitext(list0,params0={}):
  cur_ar_counter_dict=params0.get("ar_counter_dict",{})
  tokenized_bitext_list0=[]
  if len(list0[0])==2: list0=[(vi,v[0],v[1]) for vi,v in enumerate(list0)] #if it is just list of src/trg sentences - else the list should be loc,src,trg 
  #for cur_loc,src_trg in enumerate(list0):
  for cur_loc,src0,trg0 in list0:
    #src0,trg0=src_trg
    try:
      src_toks0=general.tok(src0)
      trg_toks0=general.tok(trg0)
      if params0.get("lang2")=="ar": trg_toks0=arabic_lib.tok_ar(trg_toks0,cur_ar_counter_dict)
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

def match_exact_tokens(src_toks0,trg_toks0):
  src_tok_loc_dict=get_unigram_locs(src_toks0)
  trg_tok_loc_dict=get_unigram_locs(trg_toks0)
  match_list0=[]
  for cur_src_tok0,cur_src_locs0 in src_tok_loc_dict.items():
    trg_locs=trg_tok_loc_dict.get(cur_src_tok0)
    if trg_locs==None: continue
    for sloc0 in cur_src_locs0:
      for tloc0 in trg_locs:
        src_span0=(sloc0,sloc0)
        trg_span0=(tloc0,tloc0)
        match_item=(src_span0,trg_span0,0.5,1000) # ratio= 0.5 - freq = 100
        match_list0.append(match_item)
  match_list0=sorted(list(set(match_list0)))
  return match_list0
          

def get_aligned_path(src_toks0,trg_toks0,match_list,n_epochs=10,allow_ortho=False,min_freq_without_penalty=10,penalty=0.25,reward_combined_phrases=True,only_without_children=False): #we apply penalty for less frequent pairs
  match_list=sorted(list(set(match_list)))
  #Now we have the matching list - let's align
  el_dict={} #weight of each element
  el_child_dict={} #children of each element
  for a in match_list:
    src_span0,trg_span0,ratio0,freq0=a
    if freq0<min_freq_without_penalty: ratio0=ratio0*penalty
    el0=(src_span0,trg_span0)
    found_ratio=el_dict.get(el0,0)
    if ratio0>found_ratio: el_dict[el0]=ratio0
    #print("el0",el0,"ratio0",ratio0)
  
  first_src_span,first_trg_span=(0,0),(0,0)
  last_src_span=(len(src_toks0)-1,len(src_toks0)-1)
  last_trg_span=(len(trg_toks0)-1,len(trg_toks0)-1)
  ne_el=(last_src_span,first_trg_span) #north eastern element - uppermost rightmost, so we go diagonally up to the right
  se_el=(last_src_span,last_trg_span)
  #print("ne_el",ne_el, "se_el",se_el)
  el_dict[ne_el]=0
  top_wt=0
  full_src_span0=(0,len(src_toks0)-1)
  full_trg_span0=(0,len(trg_toks0)-1)
  full_el=(full_src_span0,full_trg_span0)

  #start iteration here
  
  for epoch0 in range(n_epochs):
    #print("epoch0",epoch0)
    all_elements=list(el_dict.items())
    all_elements.sort()
    se_transition_dict,ne_transition_dict=get_ne_se_dict(all_elements,allow_ortho)
    new_el_counter=0
    for cur_el,b in ne_transition_dict.items():
      next_els=list(b.keys())
      #print("ne_transition_dict", "cur_el", cur_el,"next_els",next_els)
      if len(next_els)<2: continue
      cur_pts=[cur_el]+next_els
      cur_path,cur_path_wt=general.djk(cur_el,ne_el,ne_transition_dict,cur_pts)
      path_el_wts=[(v, el_dict.get(v,0)) for v in cur_path]
      path_el_wts_chunks=split_path_chunks(path_el_wts)
      for chunk in path_el_wts_chunks:
        chunk_wt=sum([v[1] for v in chunk])
        chunk_els=[v[0] for v in chunk]
        combined_el=combine_els(chunk_els[0],chunk_els[-1])
        found_wt=el_dict.get(combined_el,0)
        found_children=el_child_dict.get(combined_el,[])
        if chunk_wt>found_wt:
          if reward_combined_phrases: chunk_wt+=0.00000001 #give advantage to combined phrases
          el_dict[combined_el]=chunk_wt#+0.00000001
          el_child_dict[combined_el]=chunk_els
          new_el_counter+=1

    all_elements=list(el_dict.items())
    all_elements.sort()
    se_transition_dict,ne_transition_dict=get_ne_se_dict(all_elements,allow_ortho)

    for cur_el,b in se_transition_dict.items():
      next_els=list(b.keys())
      #print("se_transition_dict", "cur_el", cur_el,"next_els",next_els)
      if len(next_els)<2: continue
      cur_pts=[cur_el]+next_els
      cur_path,cur_path_wt=general.djk(cur_el,se_el,se_transition_dict,cur_pts)
      path_el_wts=[(v, el_dict.get(v,0)) for v in cur_path]
      path_el_wts_chunks=split_path_chunks(path_el_wts)
      for chunk in path_el_wts_chunks:
        chunk_wt=sum([v[1] for v in chunk])
        chunk_els=[v[0] for v in chunk]
        combined_el=combine_els(chunk_els[0],chunk_els[-1])
        found_wt=el_dict.get(combined_el,0)
        found_children=el_child_dict.get(combined_el,[])
        if chunk_wt>found_wt:
          if reward_combined_phrases: chunk_wt+=0.00000001
          el_dict[combined_el]=chunk_wt
          el_child_dict[combined_el]=chunk_els
          new_el_counter+=1
    #if single_pass: break
    cur_full_wt=el_dict.get(full_el,0)
    if cur_full_wt>0 and cur_full_wt==top_wt: break
    top_wt=cur_full_wt
  align_list=get_rec_el_children(full_el,el_child_dict,el_list0=[],only_without_children=only_without_children)
  for a in align_list:
    print(a, el_child_dict[a])
  align_list_wt=[(v,el_dict.get(v,0)) for v in align_list]  
  return align_list_wt


def align_words_phrases_classes(aligned_src0,aligned_trg0,aligned0,sent_class0="sent0",max_aligned_phrase_len=6):
  src_open_dict,src_close_dict={},{}
  trg_open_dict,trg_close_dict={},{}
  final_src_tokens,final_trg_tokens=[],[]
  for align_i,align_item in enumerate(aligned0):
    span_name="walign-%s"%(align_i)
    al0,al_wt=align_item
    src_span0,trg_span0=al0
    src_i0,src_i1=src_span0
    trg_i0,trg_i1=trg_span0
    src_phrase0=aligned_src0[src_i0:src_i1+1]
    trg_phrase0=aligned_trg0[trg_i0:trg_i1+1]
    if len(src_phrase0)>max_aligned_phrase_len: continue
    src_open_dict[src_i0]=[span_name]+src_open_dict.get(src_i0,[])
    src_close_dict[src_i1]=[span_name]+src_close_dict.get(src_i1,[])
    trg_open_dict[trg_i0]=[span_name]+trg_open_dict.get(trg_i0,[])
    trg_close_dict[trg_i1]=[span_name]+trg_close_dict.get(trg_i1,[])
    # src_open_dict[src_i0]=src_open_dict.get(src_i0,[])+[span_name]
    # src_close_dict[src_i1]=src_close_dict.get(src_i1,[])+[span_name]
    # trg_open_dict[trg_i0]=trg_open_dict.get(trg_i0,[])+[span_name]
    # trg_close_dict[trg_i1]=trg_close_dict.get(trg_i1,[])+[span_name]

  for tok_i,src_tok0 in enumerate(aligned_src0):
    if src_tok0 in ["<s>","</s>"]: continue
    open_classes=src_open_dict.get(tok_i,[])
    close_classes=src_close_dict.get(tok_i,[])
    cur_str=""
    for class0 in open_classes: cur_str+='<span class="%s %s">'%(sent_class0, class0)
    cur_str+=src_tok0
    for class0 in close_classes: cur_str+='</span>'
    final_src_tokens.append((cur_str,src_tok0))
  for tok_i,trg_tok0 in enumerate(aligned_trg0):
    if trg_tok0 in ["<s>","</s>"]: continue
    open_classes=trg_open_dict.get(tok_i,[])
    close_classes=trg_close_dict.get(tok_i,[])
    cur_str=""
    for class0 in open_classes: cur_str+='<span class="%s %s">'%(sent_class0, class0)
    cur_str+=trg_tok0
    for class0 in close_classes: cur_str+='</span>'
    final_trg_tokens.append((cur_str,trg_tok0))
  return final_src_tokens, final_trg_tokens

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
