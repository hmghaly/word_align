import sys, os, re
from time import time

excluded_src_tokens=["the","a","an","and","of","its","his","her","to","is","are","am","been", "have","has","had", "in", "on", "at", "with", "from","for","that","he","she","it"] #we will need to update this
excluded_trg_tokens=["من","على","في","مع", "إلى","له","تم","إلى","في"]


from itertools import groupby
import unicodedata
def is_punct(token):
    if len(token)==0: return True
    unicode_check=unicodedata.category(token[0])
    if len(unicode_check)>0: return unicode_check[0]=="P"
    print(token, unicode_check)
    return True

def phrase_in_phrase(small,big): #check if a phrase is inside another phrase
  found_locs=[]
  for wi,word in enumerate(big):
    if small[0]==word:
      if big[wi:wi+len(small)]==small:
        found_locs.append(wi)
  return found_locs

def rtrv_idx(tokens,idx_dict): #get the indexes of a phrase - we can extend it to as many tokens as we want
    cur_indexes=idx_dict.get(tokens[0],[])
    for ti,ta in enumerate(tokens[1:]):
        cur_offset=ti+1
        cur_raw_idx=idx_dict.get(ta,[])
        cur_offset_idx=[(v[0],v[1]-cur_offset) for v in cur_raw_idx]
        cur_indexes=list(set(cur_indexes).intersection(set(cur_offset_idx)))
    cur_indexes=[v[0] for v in cur_indexes]
    cur_indexes=sorted(list(set(cur_indexes)))
    return cur_indexes

def idx_match(idx1,idx2,min_common=5): #This function is to give a ratio of matching between the inverted indexes for two words
    if len(idx1)==0 or len(idx2)==0: return 0
    intersection=len(list(set(idx1).intersection(set(idx2))))
    union=len(idx1)+len(idx2)-intersection
    if union==0: return 0
    if intersection<min_common: return 0    
    return float(intersection)/union

def match_sentences_indexes(cur_src,cur_trg,src_inverted_index,trg_inverted_index):
  #excluded_src_tokens=["the","a","an","and","of","its","his","her","to","is","are","am","with"] #we will need to update this
  #excluded_trg_tokens=[]

  #src_sent=["<s>"]+cur_src+["</s>"] #adding start and end sentences
  #trg_sent=["<s>"]+cur_trg+["</s>"]
  src_sent=cur_src
  trg_sent=cur_trg

  #array1=np.zeros((len(trg_sent), len(src_sent))) #starting to populate the numpy probability array with zeros
  wt_list=[]
  #TODO: optimize the code for using sentence indexes for words, to save calculations for words occuring more than once in the sentence
  for j_ in range(len(trg_sent)): #now we identify the probability of matching between each pair of src and trg words
    t_tok=trg_sent[j_]
    #TODO: do generic steps for exluding stopwords in both source and target words
    if "ـ" in t_tok: t_indexes=[] #if an Arabic word has tatweel in our tokenization scheme it is a prefix or suffix, so it is excluded from matching
    elif t_tok in excluded_trg_tokens: t_indexes=[] #if target token is a stop word in target tokens (excluded_trg_tokens)
    else: t_indexes=trg_inverted_index.get(t_tok,[])    #else get the indexes from the inverted index
    for i_ in range(len(src_sent)):
      s_tok=src_sent[i_]
      if s_tok==t_tok and s_tok in ["<s>","</s>"]: ratio=1
      elif s_tok in excluded_src_tokens: ratio=0
      else: 
        s_indexes=src_inverted_index.get(s_tok,[])
        ratio=idx_match(s_indexes,t_indexes)
      
      #array1[i_,j_]=ratio #we populate the array with the matching ratio - Maybe not needed, except for visualization, when available
      wt_list.append(((i_,j_),ratio)) #and also add the coordinates and the ratio to a list
  
  #print(array1)
  wt_list.sort(key=lambda x:-x[1]) #we sort the weight list by the probability of each coordinate
  return wt_list #return wt_list and matching probability list


class sent_cls:
  def __init__(self,raw_sent0="",raw_tokens0=[],tokens0=[],map0=[]) -> None:
      self.raw_sent=raw_sent0
      self.raw_tokens=raw_tokens0
      self.tokens=tokens0 #filtered tokens
      self.map=map0 #mapping of filtered tokens to raw tokens #raw_tokens,map

class indexing: #get a list of sentences, outputs indexes
  def __init__(self,raw_sentences0,tok_function, params0={}):
    lang=params0.get("lang","en")
    stop_words=params0.get("stop_words",[]) #excluded words
    ignore_punc=params0.get("ignore_punc",False) #skip punctuation or not
    ignore_ar_pre_suf=params0.get("ignore_ar_pre_suf",False) #ignore arabic prefixes and suffixes
    remove_al=params0.get("remove_al", True) #remocve alif laam in Arabic
    index_words=params0.get("index_words", True) #keep the index of each word in a sentence, not just the sentence number
    lower=params0.get("lower", True) #make all words lower case or not
    stemming=params0.get("stemming", False) #stem each word or not
    self.fwd_index=[]
    self.all_tok_sentences=[]
    self.all_tok_original_sentences=[]
    self.all_mappings=[]
    self.sent_obj_list=[]
    self.inv_index={}
    for sent_i,sent0 in enumerate(raw_sentences0):
      #if sent_i%5000==0: print(sent_i)
      tokens=tok_function(sent0)
      #tokens,cur_mapping,original_tokens=filter_tokens(tokens, lang,stop_words, ignore_punc,ignore_ar_pre_suf,remove_al,index_words,lower,stemming)
      tokens,cur_mapping,original_tokens=filter_tokens(tokens, params0)
      self.all_tok_original_sentences.append(original_tokens)
      self.all_mappings.append(cur_mapping)
      enumerated_toks=[(v,sent_i,s_i) for s_i,v in enumerate(tokens)]
      cur_sent_obj0=sent_cls(sent0,original_tokens,tokens,cur_mapping)
      self.sent_obj_list.append(cur_sent_obj0)
      #cur_sent_obj0
      self.all_tok_sentences.append(tokens)
      self.fwd_index.extend(enumerated_toks)
    self.fwd_index.sort()
    grouped=[(key,[v[1:] for v in list(group)]) for key,group in groupby(self.fwd_index,lambda x:x[0])]
    self.inv_index=dict(iter(grouped))

def filter_tokens(token_list0, params0={}):
#def filter_tokens(token_list0, lang="en",stop_words=[], ignore_punc=False,ignore_ar_pre_suf=False,remove_al=True,index_words=True,lower=True,stemming=False):
  tokens_original=list(token_list0)
  tokens_copy_enum=[(i,v) for i,v in enumerate(token_list0)]   
  ignore_punc=params0.get("ignore_punc",False)
  ignore_ar_pre_suf=params0.get("ignore_ar_pre_suf",False)
  remove_al=params0.get("remove_al",True)
  lower=params0.get("lower",True)
  stemming=params0.get("stemming",False)
  lang=params0.get("lang","en")
  stop_words=params0.get("stop_words",[])
  #if lang=="ar": tokens=tok_ar(tokens,count_dict) #tok_ar(tokens)
  if ignore_punc: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not is_punct(v)]
  if ignore_ar_pre_suf: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not v.startswith("ـ") and not v.endswith("ـ")]
  if stop_words: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not v.lower() in stop_words]
  if remove_al: tokens_copy_enum=[(i,v.replace("ال_","")) for i,v in tokens_copy_enum if not v.lower() in stop_words]
  tokens_out=[v[1] for v in tokens_copy_enum]
  if lower: tokens_out=[v.lower() for v in tokens_out]
  cur_mapping=[v[0] for v in tokens_copy_enum]
  return tokens_out,cur_mapping, tokens_original

def get_tok_loc(tok_list):
  tok_locs_list=[]
  for i_,cur_tok in enumerate(tok_list):
    tok_locs_list.append(((cur_tok,),(i_,i_))) #to get unigrams and their locations
    if i_<len(tok_list)-1: tok_locs_list.append(((cur_tok,tok_list[i_+1]), (i_,i_+1))) #to get bigrams and their locations
  tok_locs_list.sort(key=lambda x:x[0])
  grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(tok_locs_list,lambda x:x[0])]
  return grouped

def get_rec_el_children(el0,el_child_dict0,el_list0=[]):
  cur_children0=el_child_dict0.get(el0,[])
  if cur_children0==[]: el_list0.append(el0)
  for ch0 in cur_children0:
    el_list0=get_rec_el_children(ch0,el_child_dict0,el_list0)
  return el_list0

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


def walign(src_obj0,trg_obj0,src_inv_dict0,trg_inv_dict0,walign_params0={}):
  min_retrieved_index_count=walign_params0.get("min_retrieved_index_count",3) #3
  max_dist=walign_params0.get("max_dist",10)
  min_ratio=walign_params0.get("min_ratio",0.05)
  max_sent_size=walign_params0.get("max_sent_size")
  n_epochs=walign_params0.get("n_epochs",20)
  output={}

  span_el_dict={} #which elements corresponds to this span - sorted by weight
  start_span_dict={} #show all the spans corresponding to a src location
  el_child_dict={} #show which elements are children of which
  el_wt_dict={} #show the weight of each element

  
  span_wt_dict={} #wight of each span -> the weight of the highest element it includes
  span_child_dict={} #which subspans this span consists of
  span_top_elms_dict={} #show the top elements for each span
  
  
  
  all_phrase_pairs=[]
  src0,trg0=src_obj0.tokens, trg_obj0.tokens
  original_src0,original_trg0=src_obj0.raw_tokens, trg_obj0.raw_tokens
  map_src0,map_trg0=src_obj0.map, trg_obj0.map
  #trg0=trg_obj0.tokens #raw_tokens,map
  #if len(src0)>35: return


  src0=['<s>']+src0+['</s>'] #first we pad the sentence tokens with start and end sentence markers
  trg0=['<s>']+trg0+['</s>'] #for both src and trg
  original_src0=['<s>']+original_src0+['</s>'] #first we pad the sentence tokens with start and end sentence markers
  original_trg0=['<s>']+original_trg0+['</s>'] #for both src and trg

  output["src"]=original_src0
  output["trg"]=original_trg0
  

  
  if max_sent_size!=None and len(src0)>max_sent_size: return output


  # self.src0=src0
  # self.trg0=trg0
  #print(src0)
  src_grouped=get_tok_loc(src0) #group all the locations for a list of consecutive tokens (src then trg)
  trg_grouped=get_tok_loc(trg0)
  src_side,trg_side=[],[] #mapping unigrams and bigrams to both their locations within the sentence and retrieved indexes from inverted dict
  src_locs_count_dict={} #how many times did the current token/bigram/phrase appeared in the src sent tokens
  trg_locs_count_dict={} #and same for trg
  for s_toks0,s_locs_grp0 in src_grouped: #retrive the indexes for each token sequence, map them to the locations
    src_indexes0= rtrv_idx(s_toks0,src_inv_dict0)
    s_toks_str0=" ".join(s_toks0) 
    src_side.append((s_toks_str0,s_locs_grp0,src_indexes0))
    src_locs_count_dict[s_toks_str0]=len(s_locs_grp0)
  for t_toks0,t_locs_grp0 in trg_grouped:
    trg_indexes0= rtrv_idx(t_toks0,trg_inv_dict0)
    t_toks_str0=" ".join(t_toks0)
    trg_side.append((t_toks_str0,t_locs_grp0,trg_indexes0))
    trg_locs_count_dict[t_toks_str0]=len(t_locs_grp0)

  #now starting the match the indexes of both src and trg token locations and get the corresponding rations/weights
  matching_list=[]
  all_elements=[] #to create elements (pairs of src-trg spans)
  tmp_ratio_dict={}
  for src_item0 in src_side: #examining all src tokens/bigrams with their locs/spans and retrieved indexes
    s_toks_str0,s_locs_grp0,src_indexes0=src_item0
    for trg_item0 in trg_side: #and get also all trg tokens/bigrams with locs/spand and retrieved indexes
      t_toks_str0,t_locs_grp0,trg_indexes0=trg_item0
      cur_ratio=0
      if s_toks_str0==t_toks_str0: cur_ratio=1.0 #if the src equals the target (e.g. numbers), the matching ratio is 1
      else: 
        if len(src_indexes0)<min_retrieved_index_count or len(trg_indexes0)<min_retrieved_index_count: continue #if the number of retrieved indexes is less than certain threshold, we keep the ratio as zero
        cur_ratio=idx_match(src_indexes0,trg_indexes0,5)
      if cur_ratio==0: continue
      matching_list.append(([s_toks_str0,s_locs_grp0],[t_toks_str0,t_locs_grp0], cur_ratio))

  #####
  #Now filtering the matching list
  matching_list.sort(key=lambda x:-x[-1])
  valid_list=[] #the final list of acceptable phrase pairs, their locs, and matching ratio
  for ml in matching_list:
    a,b,r=ml
    src_phrase0,src_locs=a #for the current src phrase and how many locations it occurs in the current sentence
    trg_phrase0,trg_locs=b #and same for trg phrase
    min_count=min(len(src_locs), len(trg_locs)) #and we get the minimum occurance between the src and trg phrase
    found_src_count=src_locs_count_dict[src_phrase0] #and then we check whether the src phrase was used before
    found_trg_count=trg_locs_count_dict[trg_phrase0] #and same for trg phrase
    if found_src_count<1 or found_trg_count<1: continue #if either was used before, their count would be zero or less, so we exclude current pair
    src_locs_count_dict[src_phrase0]=found_src_count-min_count #if not, we proceed, abd subtract the minimum count from the "unused" count of the current src phrase
    trg_locs_count_dict[trg_phrase0]=found_trg_count-min_count #and same for trg
    valid_list.append(ml)
  #Now we star processing the valid pairs, with their actual geometric spans and weights
  #first populate the main dictionaries: span_el_dict,  start_span_dict, el_child_dict, el_wt_dict
  span_el_list=[] #list of spans and elements
  all_src_spans=[]
  for vl in valid_list:
    #print(">>>", vl)
    a,b,cur_ratio=vl
    src_phrase0,src_locs=a #for the current src phrase and how many locations it occurs in the current sentence
    trg_phrase0,trg_locs=b #and same for trg phrase
    for sl0 in src_locs:
      if not sl0 in all_src_spans: all_src_spans.append(sl0)
      for tl0 in trg_locs:
        cur_el=(sl0,tl0) #an element is a tuple containing the span of src indexes and span of trg indexes
        el_wt_dict[cur_el]=cur_ratio #initially populating the element weight dict
        span_el_list.append((sl0,cur_el,cur_ratio))
  span_el_list.sort(key=lambda x:x[0])
  span_el_list_grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(span_el_list,lambda x:x[0])]
  all_src_spans.sort()
  all_src_spans_grouped=[(key,list(group)) for key,group in groupby(all_src_spans,lambda x:x[0])]
  for sp0,elements0 in span_el_list_grouped: span_el_dict[sp0]=elements0 #initially populating the span-elements dict
  for start_i0,spans0 in all_src_spans_grouped: start_span_dict[start_i0]=spans0 #initially poplating the start/spans dict
  top_score=0
  full_src_span0=(0,len(src0)-1)
  full_trg_span0=(0,len(trg0)-1)
  full_el=(full_src_span0,full_trg_span0)
  #all_top_scores=[]

  for ep0 in range(n_epochs):
    #continue
    cur_start_locs=sorted(list(set(start_span_dict.keys())))
    #print(ep0, "cur_start_locs",cur_start_locs)
    for i_,loc_i in enumerate(cur_start_locs):
      next_locs=cur_start_locs[i_+1:]
      cur_spans=start_span_dict[loc_i]
      next_spans=[]
      for nl in next_locs: next_spans.extend(start_span_dict[nl])
      #print(ep0,"cur_spans",cur_spans,"next_spans",next_spans)

      for cs in cur_spans: 
        cur_els=span_el_dict.get(cs,[])
        #print("$$$$$ cur_els",cur_els)
        for ns in next_spans:
          #if ns[0]<=cs[1]: continue #print("exclude:",cs,ns)
          x_dist=get_span_dist(cs,ns)
          #print("????", cs,ns, "x_dist",x_dist)
          if x_dist<1 or x_dist>max_dist: continue
          #else: print("++++", cs,ns)
          next_els=span_el_dict.get(ns,[])
          #print("#### next_els",next_els)
          for cur_el0 in cur_els:
            cur_wt0=el_wt_dict[cur_el0]
            cur_x_span,cur_y_span=cur_el0
            for next_el0 in next_els:
              if cur_el0==next_el0: continue
              next_x_span,next_y_span=next_el0
              y_dist=get_span_dist(cur_y_span,next_y_span)
              if y_dist<1 or y_dist>max_dist: continue #print("Excluded XXX: cur_el0",cur_el0, "next_el0",next_el0,"y_dist",y_dist)
              next_wt0=el_wt_dict[next_el0] 
              combined_wt0=cur_wt0+next_wt0
              combined_el0=combine_els(cur_el0,next_el0) #get_min_max(cur_el0,next_el0)
              found_combined_wt=el_wt_dict.get(combined_el0,0)
              #print(">>>", cur_el0, next_el0,"combined_wt0",combined_wt0,"found_combined_wt",found_combined_wt)       
              if combined_wt0>found_combined_wt:
                el_wt_dict[combined_el0]=combined_wt0
                el_child_dict[combined_el0]=[cur_el0,next_el0]
                tmp_src_span0=combined_el0[0]
                #print("tmp_src_span0",tmp_src_span0)
                found_span_elements=span_el_dict.get(tmp_src_span0,[])
                if not combined_el0 in found_span_elements: found_span_elements.append(combined_el0)
                found_span_elements.sort(key=lambda x:-el_wt_dict[x])
                span_el_dict[tmp_src_span0]=found_span_elements
                #print("span_el_dict[tmp_src_span0]",span_el_dict[tmp_src_span0])
                found_start_spans=start_span_dict.get(tmp_src_span0[0])
                if not tmp_src_span0 in found_start_spans: found_start_spans.append(tmp_src_span0)
                start_span_dict[tmp_src_span0[0]]=found_start_spans
                #print("start_span_dict[tmp_src_span0[0]]",start_span_dict[tmp_src_span0[0]])
                #print(ep0, "cur_el0",cur_el0, "next_el0",next_el0,"combined_el0",combined_el0, "combined_wt0",round(combined_wt0,4), "y_dist",y_dist)
        

    cur_score=el_wt_dict.get(full_el,0)
    wt_list=list(el_wt_dict.items())
    wt_list.sort(key=lambda x:-x[1])
    #print(ep0, wt_list[0], "cur_score",cur_score, "top",top_score)
    # for wl in wt_list[:5]:
    #   print(ep0, wl)
    # print("----")
    # print(all_top_scores)
    # all_top_scores.append(cur_score)

    if cur_score>top_score: top_score=cur_score
    elif cur_score==top_score and cur_score>0: break

  if el_wt_dict.get(full_el,0)>0:
    align_list=get_rec_el_children(full_el,el_child_dict,el_list0=[])
  else:
    top_el=wt_list[0][0]
    print("couldn't find full el:",full_el, "used the top el instead", top_el)
    align_list=get_rec_el_children(top_el,el_child_dict,el_list0=[])

  
  if align_list!=[]:
    # src0=src_obj0.tokens
    # trg0=trg_obj0.tokens
    output_align_list=[]

    # print("aligned")
    # print(src0)
    # print(trg0)
    # print(map_src0)
    # print(map_trg0)
    adj_src_map=[0]+[v+1 for v in map_src0]+[len(original_src0)-1]
    adj_trg_map=[0]+[v+1 for v in map_trg0]+[len(original_trg0)-1]
    # print(original_src0)
    # print(original_trg0)
    # print("adj_src_map",adj_src_map)
    # print("adj_trg_map",adj_trg_map)
    for a in align_list:
      src_span0,trg_span0=a
      x0,x1=src_span0
      y0,y1=trg_span0
      new_x0,new_x1=adj_src_map[x0],adj_src_map[x1]
      new_y0,new_y1=adj_trg_map[y0],adj_trg_map[y1]
      new_src_pan=new_x0,new_x1
      new_trg_span=new_y0,new_y1
      
      src_phrase0=src0[src_span0[0]:src_span0[1]+1]
      trg_phrase0=trg0[trg_span0[0]:trg_span0[1]+1]

      output_align_list.append((new_src_pan,new_trg_span))

      src_phrase1=original_src0[new_x0:new_x1+1]
      trg_phrase1=original_trg0[new_y0:new_y1+1]
    #   print(a,src_phrase0, trg_phrase0)
    #   print("src_phrase1",src_phrase1)
    #   print("trg_phrase1",trg_phrase1)
    #   print("---")
    # print("==============")
  #out["align"]=output_align_list
  output["align"]=output_align_list
  return output

def extract_phrases(src_tokens0,trg_tokens0,align_list0,max_size=10): #extracting phrases from aligned pairs of src/trg tokens, filling the gaps of unaligned tokens 
  src_size,trg_size=len(src_tokens0),len(trg_tokens0)
  #expanded_spans=[]
  expanded_spans=list(align_list0)
  used_src_locs,used_trg_locs=[],[]
  for i0, align_span_pair0 in enumerate(align_list0):
    src_span0,trg_span0=align_span_pair0
    used_src_locs.extend(range(src_span0[0],src_span0[1]+1))
    used_trg_locs.extend(range(trg_span0[0],trg_span0[1]+1))
  # print("used_src_locs",used_src_locs)
  # print("used_trg_locs",used_trg_locs)

  for i0, align_span_pair0 in enumerate(align_list0):
    src_span0,trg_span0=align_span_pair0
    for align_span_pair1 in align_list0[i0+1:]:
      src_span1,trg_span1=align_span_pair1
      #print(align_span_pair0, align_span_pair1)
      combined_src_span=(src_span0[0],src_span1[1])
      combined_trg_span=min(trg_span0[0],trg_span1[1]),max(trg_span0[0],trg_span1[1])
      valid=True
      for align_span_pair2 in align_list0:
        if align_span_pair2==align_span_pair0 or align_span_pair2==align_span_pair1: continue
        src_span2,trg_span2=align_span_pair2
        if (src_span2[0]>=combined_src_span[0] and src_span2[0]<=combined_src_span[1]) or (src_span2[1]>=combined_src_span[0] and src_span2[1]<=combined_src_span[1]):
          if trg_span2[1]>combined_trg_span[1] or trg_span2[0]<combined_trg_span[0]:
            valid=False
            #print("outside:",align_span_pair2)
            break
      if not valid: continue
      expanded_spans.append((combined_src_span,combined_trg_span))

      # print("combined_src_span",combined_src_span)
      # print("combined_trg_span",combined_trg_span)
  final_spans=[]
  for combined_src_span, combined_trg_span in expanded_spans:
    x0,x1=combined_src_span
    y0,y1=combined_trg_span
    if x1-x0>max_size: continue
    src_starting_locs=[x0]
    src_ending_locs=[x1]
    trg_starting_locs=[y0]
    trg_ending_locs=[y1]
    go_x_pre,go_x_post,go_y_pre,go_y_post=True,True,True, True
    for offset0 in range(1,10):
      pre_x0=x0-offset0
      if pre_x0>=0 and not pre_x0 in used_src_locs: src_starting_locs.append(pre_x0)
      else: break
    for offset0 in range(1,10):
      post_x1=x1+offset0
      if post_x1<src_size and not post_x1 in used_src_locs: src_ending_locs.append(post_x1) 
      else: break
    for offset0 in range(1,10):
      pre_y0=y0-offset0
      if pre_y0>=0 and not pre_y0 in used_trg_locs: trg_starting_locs.append(pre_y0) 
      else: break
    for offset0 in range(1,10):
      post_y1=y1+offset0
      if post_y1<trg_size and not post_y1 in used_trg_locs: trg_starting_locs.append(post_y1)
      else: break
    # print("src_starting_locs",src_starting_locs)
    # print("src_ending_locs",src_ending_locs)
    # print("trg_starting_locs",trg_starting_locs)
    # print("trg_ending_locs",trg_ending_locs)



    # print("valid",valid)
    # print("---")
    for new_x0 in src_starting_locs:
      for new_x1 in src_ending_locs:
        if new_x1-new_x0>max_size: continue
        new_src_span=(new_x0,new_x1)
        for new_y0 in trg_starting_locs:
          for new_y1 in trg_ending_locs:
            if new_y1<new_y0: continue
            new_trg_span=(new_y0,new_y1)
            final_spans.append((new_src_span,new_trg_span))
  all_phrases=[]
  for src_span,trg_span in final_spans:
    #print(src_span, trg_span)
    cur_src_phrase=" ".join(src_tokens0[src_span[0]:src_span[1]+1])
    cur_trg_phrase=" ".join(trg_tokens0[trg_span[0]:trg_span[1]+1])
    all_phrases.append((cur_src_phrase,cur_trg_phrase))

  return all_phrases



if __name__=="__main__":
  params={}
  params["lang"]="en"
  params["ignore_punc"]=True
  params["stop_words"]=[]
  params["ignore_ar_pre_suf"]=True
  params["remove_al"]=True
  params["index_words"]=True
  params["lower"]=True
  params["stemming"]=False

  walign_params={}
  walign_params["min_retrieved_index_count"]=3
  walign_params["max_dist"]=5
  walign_params["max_sent_size"]=60
  walign_params["min_ratio"]=0.05
  walign_params["n_epochs"]=5
  print(params)