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
  if params.get("exclude_single_chars",True): tok_list0=[v if len(v)>1 else "" for v in tok_list0] #ignore single character tokens
  if params.get("exclude_punc",True): tok_list0=[v if not general.is_punct(v) else "" for v in tok_list0] #ignore punctuation
  
  if params.get("ignore_ar_pre_suf",True): tok_list0=["" if v.startswith("ـ") or v.endswith("ـ") else v for v in tok_list0] #ignore arabic prefixes and suffixes
  if params.get("remove_ar_diacritics",True): tok_list0=[general.remove_diactitics(v) for v in tok_list0] #remove Arabic diacritics
  if params.get("remove_al",True): tok_list0=[v.replace("ال_","") for v in tok_list0] #remove alif laam for the beginning of Arabic words
  if params.get("normalize_taa2_marbootah",False): tok_list0=[v[:-1]+"ت"  if v.endswith("ة") else v for v in tok_list0] #normalize taa2 marbootah
  if params.get("normalize_digits",False): tok_list0=["5"*len(v) if v.isdigit() else v for v in tok_list0] #normalize numbers to just the number of digits 1995 > 5555
  #if params.get("stemming",False): tok_list0=[v else v for v in tok_list0] #stem each word or not
  #remove_al=params0.get("remove_al", False) #remocve alif laam in Arabic 
  return tok_list0

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
  
  # combined_first_matched_list=[]
  # for a,b in matching_dict.items():
  #   first_src=a[0][0]
  #   combined_first_matched_list.append((first_src,a,b))
  # combined_first_matched_list.sort(key=lambda x:x[0])
  # grouped=[(key,[v[1:] for v in list(group)]) for key,group in groupby(combined_first_matched_list,lambda x:x[0])]
  # first_dict=dict(iter(grouped))
  # child_dict={}
  # new_matching_dict={} #dict(matching_dict)
  # all_matching_items=list(matching_dict.items())
  # all_matching_items.sort(key=lambda x:len(x[0][0]+x[0][1]))
  # for pair,wt in all_matching_items:
    
  #   final_wt=wt
  #   new_matching_dict[pair]=final_wt
  #   src_tuple0,trg_tuple0=pair
  #   #if len(src_tuple0)==1 and len(trg_tuple0)==1: continue
  #   #print(">>>>",pair,wt)
  #   for tok0 in src_tuple0:
  #       if tok0=="": continue
  #       candidate_child_pairs=first_dict.get(tok0,[])
  #       for cd_pair,cd_wt in candidate_child_pairs:
  #           if cd_pair==pair: continue
  #           cd_src,cd_trg=cd_pair
  #           if general.is_in(cd_src,src_tuple0) and general.is_in(cd_trg,trg_tuple0):
  #               final_wt+=cd_wt
  #               new_matching_dict[pair]=final_wt
  #               child_dict[pair]=child_dict.get(pair,[])+[cd_pair]
  # new_matching_dict_items=list(new_matching_dict.items())
  # new_matching_dict_items.sort(key=lambda x:-x[-1])
  # for a in new_matching_dict_items[:20]:
  #   print(">>>",a,child_dict.get(a[0]))



  #Let's try to avoid doing this
  # matching_list.sort(key=lambda x:(-round(x[-1],1),-x[-2],-len(x[0])-len(x[1])))
  # used_src_phrases=[]
  # used_trg_phrases=[]
  # final_matching_list=[]
  # src_used_counter_dict,trg_used_counter_dict={},{}
  # #print("matching_list",len(matching_list))
  # for i,a in enumerate(matching_list):
  #   src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection1,ratio1=a
  #   if i<50: print(">>>>",a)
  #   # min_n_locs=min(len(src_locs0),len(trg_locs0))
  #   # # src_check=src_used_counter_dict.get(src_phrase0,len(src_locs0))
  #   # # trg_check=trg_used_counter_dict.get(trg_phrase0,len(trg_locs0))
  #   # src_check=src_used_counter_dict.get(src_phrase0)
  #   # trg_check=trg_used_counter_dict.get(trg_phrase0)
  #   # # if src_check==None or trg_check==None: #either phrase is the top phrase/not used before
  #   # #     if not a in final_matching_list: final_matching_list.append(a)
  #   # if src_check==None: src_check=len(src_locs0)
  #   # if trg_check==None: trg_check=len(trg_locs0)


  #   # # valid=False
  #   # # if src_check==len(src_locs0) or trg_check==len(trg_locs0): valid=True
  #   # # elif src_check>0 and trg_check>0: valid=True #final_matching_list.append(a)
  #   # # if not valid: continue
  #   # # print(src_check,trg_check,a)
  #   # src_used_counter_dict[src_phrase0]=src_check-min_n_locs
  #   # trg_used_counter_dict[trg_phrase0]=trg_check-min_n_locs
  #   # # final_matching_list.append(a)
  #   # # #if src_phrase0=='document': print(a)
  #   if src_phrase0 in used_src_phrases: continue
  #   if trg_phrase0 in used_trg_phrases: continue
  #   used_src_phrases.append(src_phrase0)
  #   used_trg_phrases.append(trg_phrase0)
  #   #final_matching_list.append(a)
  #   if not a in final_matching_list: final_matching_list.append(a)
  # for a in matching_list:
  #   src_phrase0,trg_phrase0,src_locs0,trg_locs0,intersection1,ratio1=a
  #   valid=False
  #   if not src_phrase0 in used_src_phrases: valid=True
  #   if not trg_phrase0 in used_trg_phrases: valid=True
  #   if valid:
  #       used_src_phrases.append(src_phrase0)
  #       used_trg_phrases.append(trg_phrase0)
  #       if not a in final_matching_list: final_matching_list.append(a)

  # matching_list.sort(key=lambda x:x[0]) #group for source phrase
  # matching_list_grouped=[list(group) for key,group in groupby(matching_list,lambda x:x[0])]
  # for grp0 in matching_list_grouped:
  #   grp0.sort(key=lambda x:-x[-1])
  #   if not grp0[0] in final_matching_list: final_matching_list.append(grp0[0])  
  #   for a in grp0:
  #       if a in final_matching_list: continue
  #       final_matching_list.append(a)
  #       break
  # matching_list.sort(key=lambda x:x[1]) #group for target phrase
  # matching_list_grouped=[list(group) for key,group in groupby(matching_list,lambda x:x[1])]
  # for grp0 in matching_list_grouped:
  #   grp0.sort(key=lambda x:-x[-1])
  #   if not grp0[0] in final_matching_list: final_matching_list.append(grp0[0])  
  #   for a in grp0:
  #       if a in final_matching_list: continue
  #       final_matching_list.append(a)
  #       break
    # for s1 in src_locs0:
    #   for t1 in trg_locs0:
    #     final_matching_list.append((s1,t1,ratio1,intersection1))
  # return final_matching_list


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

def get_offset_intersection(index_list0,index_list1,max_sent_size0=1000):
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


#2 Jan 2023
def get_aligned_path(matching_list,n_epochs=3,max_dist=4,max_src_span=6,dist_penalty=0.1,top_n=2):
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





def get_unigrams_bigrams(token_list, exclude_numbers=True,exclude_single_chars=True): #for a list of tokens, identify all unigrams and bigrams
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
  for el0,el_wt0 in aligned_elements: #identifying aligned/unaligned locs in scr/trg tokens
    src_span0,trg_span0=el0
    src_range0,trg_range0=range(src_span0[0],src_span0[1]+1),range(trg_span0[0],trg_span0[1]+1)
    for a in src_range0:
      for b in trg_range0: all_single_pts.append((a,b)) #identifying single points (not elements)
  chunk_boundaries=[]
  for el0,el_wt0 in aligned_elements: #identifying aligned/unaligned locs in scr/trg tokens
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

#QA related functions
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


#Visual presentation of alignment
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




def random_color():
  rand = lambda: random.randint(100, 255)
  return '#%02X%02X%02X' % (rand(), rand(), rand())

def create_color_classes_css(n_classes=100):
  chars = '0123456789ABCDEF'
  css_str0='<style>\n'
  aligned_transparent_cls='.aligned-transparent {opacity: 0.25};\n'
  
  css_str0+=aligned_transparent_cls
 #  green_underline="""
 #  .green-ul {
 #  text-decoration: underline;
 #  -webkit-text-decoration-color: green; /* safari still uses vendor prefix */
 #  text-decoration-color: green;
    # }
 #  """
 #  red_underline="""
 #  .red-ul {
 #  text-decoration: underline;
 #  -webkit-text-decoration-color: red; /* safari still uses vendor prefix */
 #  text-decoration-color: red;
    # }
 #  """
  fixed_header_css="""
{margin:0;}

.navbar {
  overflow: hidden;
  background-color: lightyellow;
  position: fixed;
  top: 0;
  width: 100%;
}


.main {
  padding: 16px;
  margin-top: 80px;
  height: 1500px; /* Used in this example to enable scrolling */
}

  """
  #css_str0+=green_underline+red_underline+fixed_header_css
  css_str0+=fixed_header_css

  for class_i in range(n_classes):
    class_name="walign-%s"%(class_i)
    cur_color=random_color() #'#'+''.join(random.sample(chars,6))
    cur_css_line='.%s {background: %s;}\n'%(class_name,cur_color)
    css_str0+=cur_css_line
  no_bg_cls='.no-bg { background-color:transparent; }\n'
  css_str0+=no_bg_cls
  css_str0+='.item-highlight {color: red;background-color:#00CED1;font-weight: bold;}'
  css_str0+='.td-highlight {background-color:#F5F5DC;}'
  css_str0+='</style>\n'
  return css_str0

def create_align_html_table(list_aligned_classed0):
  table_str0='<table border="1" style="width:100%;table-layout:fixed;">'
  for item0 in list_aligned_classed0:
    src_cell0,trg_cell0=item0[:2]
    tr0='<tr><td style="max-width:50%%;width:50%%;">%s</td><td dir="rtl" style="max-width:50%%;width:50%%;">%s</td></tr>'%(src_cell0,trg_cell0)
    table_str0+=tr0
  table_str0+='</table>'
  return table_str0


def create_align_html_content(aligned_html_sent_pairs,phrase_analysis_table=""):
    css_content=create_color_classes_css()
    res_html_table=create_align_html_table(aligned_html_sent_pairs)
    

    cur_srcipt="""
    var qa_obj={}
    function go2el(qa_key){
      item_highlight_class="item-highlight"
      td_highlight_class="td-highlight"
      console.log(qa_obj[qa_key])
      cur_items=qa_obj[qa_key]["items"]
      cur_i=qa_obj[qa_key]["i"]
      if (cur_i==null || cur_i==undefined) cur_i=0 
      else cur_i=cur_i+1
      if (cur_i>=len(cur_items)) cur_i=0  
      qa_obj[qa_key]["i"]=cur_i

      cur_item0=cur_items[cur_i]
      parent_td=get_parent_with_tag(cur_item0,"td")
      scroll2el(cur_item0)
      $(".item-highlight").removeClass("item-highlight");
      $(".td-highlight").removeClass("td-highlight");

      if (!cur_item0.classList.contains(item_highlight_class)) cur_item0.classList.add(item_highlight_class)
      if (!parent_td.classList.contains(td_highlight_class)) parent_td.classList.add(td_highlight_class)
    }

    function init(){
      strong_mismatch_items=get_class_el_items(".strong-mismatch")
      weak_mismatch_items=get_class_el_items(".weak-mismatch")
      strong_mismatch_exact_items=filter_items(strong_mismatch_items,"exact")
      weak_mismatch_exact_items=filter_items(weak_mismatch_items,"exact")
      strong_mismatch_normative_items=filter_items(strong_mismatch_items,"normative")
      weak_mismatch_normative_items=filter_items(weak_mismatch_items,"normative")

      qa_obj["strong-mismatch"]={"items":strong_mismatch_items}
      qa_obj["weak-mismatch"]={"items":weak_mismatch_items}
      qa_obj["strong-mismatch-exact"]={"items":strong_mismatch_exact_items} 
      qa_obj["weak-mismatch-exact"]={"items":weak_mismatch_exact_items} 
      qa_obj["strong-mismatch-normative"]={"items":strong_mismatch_normative_items}
      qa_obj["weak-mismatch-normative"]={"items":weak_mismatch_normative_items}
      console.log(qa_obj)

      //filter_items(strong_mismatch_items,"exact")

      $$("exact-strong-mismatch").innerHTML=""+len(strong_mismatch_exact_items)
      $$("exact-weak-mismatch").innerHTML=""+len(weak_mismatch_exact_items)
      $$("normative-strong-mismatch").innerHTML=""+len(strong_mismatch_normative_items)
      $$("normative-weak-mismatch").innerHTML=""+len(weak_mismatch_normative_items)

        // mismatches=$(".mismatch")
        // $("#exact-strong-mismatch").text(""+mismatches.length)
        // console.log(mismatches)
    }


    function toggle_bg(){
        $(".aligned").toggleClass("no-bg");
    }
    function toggle_transparent_aligned(){
        $(".aligned").toggleClass("aligned-transparent");
    }
    function nav_classes(){

    }

    function handle(e){
            if(e.keyCode === 13){
                e.preventDefault(); // Ensure it is only this code that runs
                //alert("Enter was pressed was presses");
                //$(".aligned").toggleClass("aligned-transparent");
                //$(".aligned").toggleClass("no-bg");
            }
        }


    """

    html_main_content="""
    <html>
    <head>
      <title>QA Analysis</title>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
      <script src="https://code.jquery.com/jquery-3.6.1.min.js" integrity="sha256-o88AwQnZB+VDvE9tvIXrMQaPlFFSUTR+nldQm1LuPXQ=" crossorigin="anonymous"></script>
      <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
      <script src="https://hmghaly.github.io/script.js"></script>
    %s  
    
    <script>%s</script>
    </head>
        <body onload="init()" onkeypress="handle(event)">
    
    <div class="navbar" id="dashboard">
      <div class="row w-100 text-center">
          <div class="col"> 
            <h6>Alignment</h6>
            <button onclick="toggle_bg()">Option1</button>
            <button onclick="toggle_transparent_aligned()">Option2</button>
          </div>
          <div class="col">
            <h6>Numbers Mismatch</h6>
             <a href="JavaScript:void(0)" onclick='go2el("strong-mismatch-exact")'>Strong: <span id="exact-strong-mismatch">0</span></a>
             <a href="JavaScript:void(0)" onclick='go2el("weak-mismatch-exact")'>Weak: <span id="exact-weak-mismatch">0</span></a>
            </div>
          <div class="col">
            <h6>Normative Mismatch</h6> 
             <a href="JavaScript:void(0)" onclick='go2el("strong-mismatch-normative")'>Strong: <span id="normative-strong-mismatch">0</span></a>
             <a href="JavaScript:void(0)" onclick='go2el("weak-mismatch-normative")'>Weak: <span id="normative-weak-mismatch">0</span></a>

          </div>
          <div class="col">Terminology Mismatch</div>
          <div class="col">Spelling Mistakes</div>
    </div>
    </div>   

    <div class="main"> 


    %s

    <h2>Phrase Matching Analysis</h2>
    %s
    </div>
    </body>
    </html>
    """%(css_content,cur_srcipt,res_html_table,phrase_analysis_table)
    return html_main_content

#6 Jan 2023
def align_words_span_tags(src_tokens,trg_tokens,align_items,sent_class="sent0",only_without_children=True,max_phrase_length=6):
  src_start_dict,src_end_dict={},{}
  trg_start_dict,trg_end_dict={},{}
  for i0,align_item in enumerate(align_items):
    class_name="walign-%s"%(i0)
    el0,wt0,children0=align_item
    src_span0,trg_span0=el0
    x0,x1=src_span0
    y0,y1=trg_span0
    src_phrase0=" ".join(src_tokens[x0:x1+1]) 
    trg_phrase0=" ".join(trg_tokens[y0:y1+1])
    if "<s>" in src_phrase0 or "<s>" in trg_phrase0: continue
    if "</s>" in src_phrase0 or "</s>" in trg_phrase0: continue
    if general.is_punct(src_phrase0) or general.is_punct(trg_phrase0): continue
    valid=False
    if x1-x0<3 or children0==[]: valid=True
    if not valid: continue
    open_class_str='<span class="aligned %s %s">'%(sent_class, class_name)
    src_start_dict[x0]=src_start_dict.get(x0,"")+open_class_str
    trg_start_dict[y0]=trg_start_dict.get(y0,"")+open_class_str
    src_end_dict[x1]=src_end_dict.get(x1,"")+"</span>"
    trg_end_dict[y1]=trg_end_dict.get(y1,"")+"</span>"
  src_tok_tags,trg_tok_tags=[],[]
  for s_i,s_tok in enumerate(src_tokens):
    open0,close0=src_start_dict.get(s_i,""),src_end_dict.get(s_i,"")
    src_tok_tags.append((open0,close0))
    # print("SRC:", open0,s_tok, close0)
  for s_i,s_tok in enumerate(trg_tokens):
    open0,close0=trg_start_dict.get(s_i,""),trg_end_dict.get(s_i,"")
    trg_tok_tags.append((open0,close0))
    # print("TRG:", open0,s_tok, close0)
  return src_tok_tags,trg_tok_tags


#=================== QA functions ==============
#15 Jan 23
def gen_ul_style(color0="black"):
  underline_style='text-decoration: underline;-webkit-text-decoration-color: %s;text-decoration-color: %s;'%(color0,color0)
  return underline_style

def is_symbol(str0): #is a UN symbol, e.g. A/75/251
  outcome=False
  if str0[0].isupper() and str0[-1].isdigit() and str0.count("/")>0: outcome=True
  return outcome

def qa_match_exact(src_sent_toks,trg_sent_toks): #match numbers, UN-symbols and other items that have to be exact in src/trg
  uq_src0=list(set(src_sent_toks))
  uq_trg0=list(set(trg_sent_toks))
  match_score=1.0
  src_digits=[v for v in uq_src0 if v.isdigit()]
  src_symbols=[v for v in uq_src0 if is_symbol(v)] #we can also add websites, twitter handles, hashtags ... etc
  all_qa_matches=[]
  for dig0 in src_digits:
    match_type="exact-number"
    if len(dig0)<2: criticality="low" #if a single digit number, which is often translated as a word
    else: criticality="high"
    cur_src_spans=general.is_in([dig0],src_sent_toks)
    cur_trg_spans=general.is_in([dig0],trg_sent_toks)
    all_qa_matches.append((dig0,dig0,cur_src_spans,cur_trg_spans,match_type,match_score,criticality))
  for sym0 in src_symbols:
    match_type="exact-UN-symbol"
    criticality="high"
    cur_src_spans=general.is_in([sym0],src_sent_toks)
    cur_trg_spans=general.is_in([sym0],trg_sent_toks)
    all_qa_matches.append((sym0,sym0,cur_src_spans,cur_trg_spans,match_type,match_score,criticality))
  return all_qa_matches

def qa_match_normative(src_sent_toks,trg_sent_toks,normative_list):
  match_score=1.0
  all_norm_matches=[]
  for norm_src0,norm_trg0,norm_type0 in normative_list: #tokenized norm src/trg items, and type
    cur_type="normative-"+norm_type0
    criticality="high"
    src_spans=general.is_in(norm_src0,src_sent_toks)
    trg_spans=general.is_in(norm_trg0,trg_sent_toks) #we'll need to think of cases where there can be multiple trg options
    if src_spans==[] and trg_spans==[]: continue
    all_norm_matches.append((" ".join(norm_src0)," ".join(norm_trg0),src_spans, trg_spans, cur_type,match_score, criticality)) 
  return all_norm_matches

def qa_match_all(src_sent_toks,trg_sent_toks,normative_list):
  all_matches=[]
  all_matches.extend(qa_match_exact(src_sent_toks,trg_sent_toks))
  all_matches.extend(qa_match_normative(src_sent_toks,trg_sent_toks,normative_list))
  all_matches.sort(key=lambda x:len(x[0].split()))
  return all_matches

def qa_add_spans_classes(src_sent_toks,trg_sent_toks,qa_match_list):
  src_start_dict,src_end_dict={},{}
  trg_start_dict,trg_end_dict={},{}
  for src0,trg0,src_spans0,trg_spans0,match_type0,match_score0,criticality0 in qa_match_list:
    match_color="black"
    match_message=""
    class_name=""
    match_type_classes0=match_type0
    if match_type0.lower().split("-")[0] in ["normative","exact"]: match_type_classes0="%s %s"%(match_type0.lower().split("-")[0],match_type0)
    # if match_type0.lower().startswith("normative"): match_type_classes0="%s %s"%("normative",match_type0)
    # if match_type0.lower().startswith("exact"): match_type_classes0="%s %s"%("exact",match_type0)
    if len(src_spans0)==0 and len(trg_spans0)==0: continue
    if len(src_spans0)>0:
      if len(trg_spans0)==len(src_spans0): 
        match_color="lightgreen"
        match_message+=" correct match"
        class_name="match"
      elif len(trg_spans0)==0: 
        match_color="red"
        match_message="target not found"
        if criticality0=="low": class_name+=" weak-mismatch mismatch %s"%match_type_classes0
        else: class_name+=" strong-mismatch mismatch %s"%match_type_classes0
      elif len(trg_spans0)!=len(src_spans0): 
        match_color="brown"
        match_message="mismatch count of instances"
        class_name+=" weak-mismatch mismatch %s"%match_type_classes0
    else:
      if len(trg_spans0)>0:
        match_color="orange"
        match_message="found in target but not in src"
        class_name+=" weak-mismatch mismatch %s"%match_type_classes0

    for x0,x1 in src_spans0:
      src_start_dict[x0]=src_start_dict.get(x0,"")+'<span class="%s" style="%s">'%(class_name,gen_ul_style(match_color))
      src_end_dict[x1]=src_end_dict.get(x1,"")+'</span>'
    for y0,y1 in trg_spans0:
      trg_start_dict[y0]=trg_start_dict.get(y0,"")+'<span class="%s" style="%s">'%(class_name,gen_ul_style(match_color))
      trg_end_dict[y1]=src_end_dict.get(y1,"")+'</span>'
  src_open_close_tags,trg_open_close_tags=[],[]
  for i0,tok0 in enumerate(src_sent_toks):
    open0=src_start_dict.get(i0,"")
    close0=src_end_dict.get(i0,"")
    src_open_close_tags.append((open0,close0))
  for i0,tok0 in enumerate(trg_sent_toks):
    open0=trg_start_dict.get(i0,"")
    close0=trg_end_dict.get(i0,"")
    trg_open_close_tags.append((open0,close0))
  return src_open_close_tags,trg_open_close_tags



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

def offset_results(result_dict0,offset0,max_sent_size0=1000):
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
  align_list=get_aligned_path(all_matching,n_epochs=cur_n_epochs,max_dist=cur_max_dist,max_src_span=cur_max_src_span,dist_penalty=0)
  results={}
  results["src"]=src_tokens
  results["trg"]=trg_tokens
  results["align"]=align_list
  results["terms"]=[v[:2] for v in term_match0]
  results["acr"]=[v[:2] for v in acr_match0]
  results["phon"]=[v[:2] for v in phon_match0]

  return results



#================= Sentence alignment
def norm_sent_size(sent_size0,step=10,max_size=400):
  if sent_size0>max_size: return max_size
  norm_val=step*round(sent_size0/step)
  return norm_val


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
