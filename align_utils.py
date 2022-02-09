def upload(local_dir,local_fname,remote_dir,server_name="",username="",password=""): #upload a file to the server
  local_fpath= os.path.join(local_dir,local_fname)
  remote_fpath= os.path.join(remote_dir,local_fname)

  #session = ftplib.FTP(server_name,username,password)
  session = ftplib.FTP('champolu.com','arbsquser','Abc1234!')
  file = open(local_fpath,'rb')                  # file to send
  session.storbinary('STOR %s'%remote_fpath, file)     # send the file
  file.close()                                    # close file and FTP
  session.quit()


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


#Word Alignmnet pipeline
def tok_OLD(txt):
  #txt=txt.replace(u'\x01'," ")
  txt=txt.replace(u'\u2019',"'")
  
  txt=txt.replace("'s ","_s ")
  txt=txt.replace("'re ","_re ")
  txt=txt.replace("can't ","cann_t ")
  txt=txt.replace("n't ","n_t ")
  txt=re.sub("(?u)(\W)",r" \1 ", txt)
  txt=txt.replace("_s ", " 's ")
  txt=txt.replace("_re "," 're ")
  txt=txt.replace("n_t "," n't ")
  
  out=re.split("\s+",txt)
  return [v for v in out if v]

def phrase_in_phrase(small,big): #check if a phrase is inside another phrase
  found_locs=[]
  for wi,word in enumerate(big):
    if small[0]==word:
      if big[wi:wi+len(small)]==small:
        found_locs.append(wi)
  return found_locs


def index_bitext(bitext_fpath,ignore_punc=True):
  fwd_index_src=[]
  fwd_index_trg=[]
  all_src_sentences=[]
  all_trg_sentences=[]
  bitext_fopen=open(bitext_fpath)
  for sent_i,s0_t0 in enumerate(bitext_fopen):
    #print(counter)
    split=s0_t0.strip("\n\r").split("\t")
    if len(split)!=2: continue
    s0,t0=split
    raw_src_toks=[v.lower() for v in tok(s0)]
    raw_trg_toks=[v.lower() for v in tok(t0)]
    #print(raw_trg_toks)
    if ignore_punc:
      raw_src_toks=[v for v in raw_src_toks if not is_punct(v)]
      raw_trg_toks=[v for v in raw_trg_toks if not is_punct(v)]
    
    s_toks=[(v,sent_i,s_i) for s_i,v in enumerate(raw_src_toks)]
    t_toks=[(v,sent_i,t_i) for t_i,v in enumerate(raw_trg_toks)]

    all_src_sentences.append(raw_src_toks)
    all_trg_sentences.append(raw_trg_toks)

    fwd_index_src.extend(s_toks)
    fwd_index_trg.extend(t_toks)

  fwd_index_src.sort()
  fwd_index_trg.sort()
  src_grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(fwd_index_src,lambda x:x[0])]
  trg_grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(fwd_index_trg,lambda x:x[0])]

  src_inverted=dict(iter(src_grouped))
  trg_inverted=dict(iter(trg_grouped))
  return src_inverted, trg_inverted, all_src_sentences, all_trg_sentences

def filter_tokens(token_list0, lang="en",stop_words=[], ignore_punc=False,ignore_ar_pre_suf=False,remove_al=True,index_words=True,lower=True,stemming=False):
  tokens_original=list(token_list0)
  tokens_copy_enum=[(i,v) for i,v in enumerate(tokens_original)]   
  #if lang=="ar": tokens=tok_ar(tokens,count_dict) #tok_ar(tokens)
  if ignore_punc: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not is_punct(v)]
  if ignore_ar_pre_suf: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not v.startswith("ـ") and not v.endswith("ـ")]
  if stop_words: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not v.lower() in stop_words]
  if remove_al: tokens_copy_enum=[(i,v.replace("ال_","")) for i,v in tokens_copy_enum if not v.lower() in stop_words]
  tokens_out=[v[1] for v in tokens_copy_enum]
  if lower: tokens_out=[v.lower() for v in tokens_out]
  cur_mapping=[v[0] for v in tokens_copy_enum]
  return tokens_out,cur_mapping

class indexing: #get a list of sentences, outputs indexes
  def __init__(self,raw_sentences0,tok_function, lang="en",stop_words=[], ignore_punc=False,ignore_ar_pre_suf=False,remove_al=True,index_words=True,lower=True,stemming=False):
    self.fwd_index=[]
    self.all_tok_sentences=[]
    self.all_tok_original_sentences=[]
    self.all_mappings=[]
    self.inv_index={}
    for sent_i,sent0 in enumerate(raw_sentences0):
      if sent_i%5000==0: print(sent_i)
      tokens=tok_function(sent0)
#       tokens_original=list(tokens)
#       tokens_copy_enum=[(i,v) for i,v in enumerate(tokens_original)]
#       self.all_tok_original_sentences.append(tokens_original)
      
#       #if lang=="ar": tokens=tok_ar(tokens,count_dict) #tok_ar(tokens)
#       if ignore_punc: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not is_punct(v)]
#       if ignore_ar_pre_suf: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not v.startswith("ـ") and not v.endswith("ـ")]
#       if stop_words: tokens_copy_enum=[(i,v) for i,v in tokens_copy_enum if not v.lower() in stop_words]
#       if remove_al: tokens_copy_enum=[(i,v.replace("ال_","")) for i,v in tokens_copy_enum if not v.lower() in stop_words]
#       tokens=[v[1] for v in tokens_copy_enum]
#       cur_mapping=[v[0] for v in tokens_copy_enum] #mapping of token locations to original after excluding some elements
      tokens,cur_mapping=filter_tokens(tokens, lang,stop_words, ignore_punc,ignore_ar_pre_suf,remove_al,index_words,lower,stemming)
      self.all_mappings.append(cur_mapping)
      
      #tokens_lower=[v.lower() for v in tokens]
      #if lower: tokens=[v.lower() for v in tokens] #enumerated_toks=[(v,sent_i,s_i) for s_i,v in enumerate(tokens_lower)]
      enumerated_toks=[(v,sent_i,s_i) for s_i,v in enumerate(tokens)]
      self.all_tok_sentences.append(tokens)
      self.fwd_index.extend(enumerated_toks)
    self.fwd_index.sort()
    grouped=[(key,[v[1:] for v in list(group)]) for key,group in groupby(self.fwd_index,lambda x:x[0])]
    self.inv_index=dict(iter(grouped))
    
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

def get_candidate_pts(wt_list,src_size,trg_size): #based on the weights of the all point pairs, we start to identify which of these to further process
  final_list=[]
  src_side_dict=dict(iter([(i,[0]*trg_size) for i in range(src_size)] )) #dict with keys corresponding to src sent word indexes, and values are the probability of each target word index
  trg_side_dict=dict(iter([(i,[0]*src_size) for i in range(trg_size)] )) #dict with keys corresponding to trg


  #we collect the coordinates with the highest probability across the matrix, with unique x,y/i,j coordinates
  used_i,used_j=[],[] #if an index (i or j) is used once in a coordinate, it is excluded 
  #final_list=[]
  for ij,wt in wt_list: #while we go in a descending order in all the coordinates with their weights
    if wt==0: continue
    i0,j0=ij
    src_side_dict[i0][j0]=wt
    trg_side_dict[j0][i0]=wt

    #if i0==0 and j0!=0: continue
    #if i0!=0 and j0==0: continue
    if i0 in used_i or j0 in used_j: continue
    #if i0 in used_i and j0 in used_j: continue
    if not (i0,j0) in final_list: 
      final_list.append((i0,j0)) #these unique coordinates are also added to the final candidate points
      #array1[i0,j0]+=25
    used_i.append(i0)
    used_j.append(j0)

    for i_ in range(src_size): #get the maximum coordinates corresponding to each source word
      corr=src_side_dict[i_]
      max_corr=max(corr)
      if max_corr==0: continue
      max_j_indexes=[k0 for k0,v in enumerate(corr) if v==max_corr]
      for j_ in max_j_indexes:
        final_list.append((i_,j_))

    for j_ in range(trg_size): #and the maximum corresponding to each target word
      corr=trg_side_dict[j_]
      max_corr=max(corr)
      if max_corr==0: continue
      max_i_indexes=[k0 for k0,v in enumerate(corr) if v==max_corr]
      for i_ in max_i_indexes:
        final_list.append((i_,j_)) 
  final_list=list(set(final_list)) #now we have the final list of possible points, that we can process with dynamic programming
  final_list.sort()
  return final_list #return candidate points, which are maximum points in rows and columns and overall

def get_path_rect(se_span_dict,ne_span_dict,pt_dict,se): #se: south east, if the rectangles are expanding towards South East or not (towards NE: north east)
  #This is the main alignment function
  #it starts from one of the candidate points/spans, and then finds the dijkestra's shortest path to the first point
  #depending on whether we go SE or NE
  #and then we create a rectangle between each two points on the path - and create new spans accordingly
  #when iterating over this, we can get all the possible SE and NE spans and merge them to get 
  #the optimum arrangement of spans/rectangles and the points they contain
  if se: cur_span_dict=se_span_dict
  else: cur_span_dict=ne_span_dict
  keys_wts=list(cur_span_dict.items())

  path_wt_dict={} #the weight of the path till a certail span
  prev_span_dict={} #the previous span with the highest path weight to a given span

  for cur_span,cur_wt in keys_wts:
    (cur_x0,cur_y0),(cur_x1,cur_y1)=cur_span
    cur_span_path_wt=path_wt_dict.get(cur_span,cur_wt) #we check the path weight so far for the current span - if nothing, then it is the actual weight
    path_wt_dict[cur_span]=cur_span_path_wt  #we then update it
    for next_span,next_wt in keys_wts:
      (next_x0,next_y0),(next_x1,next_y1)=next_span
      #accept only spans going either SE or NE - or colinear spans
      colinear=False #check if two spans are colinear on X or Y
      if cur_span==next_span: continue #eliminate if same span
      if next_x0<cur_x1: continue #eliminate if the start x of the next span is less than the end x of current
      if se and next_y0<cur_y1: continue
      if not se and next_y0>cur_y1: continue
      if next_x0==cur_x1:
        if cur_x0==cur_x1==next_x0==next_x1: 
          colinear=True #msg="colinear X"
          if abs(next_y0-cur_y1)>5: continue #maximum number of words between colinear spans
        else: continue
      if next_y0==cur_y1:
        if cur_y0==cur_y1==next_y0==next_y1: 
          colinear=True # msg="colinear Y"
          if abs(next_x0-cur_x1)>5: continue #maximum number of words between colinear spans
        else: continue    
      # col_penalty=0.8 #not sure if we'll use these
      # if colinear: next_wt=col_penalty*next_wt #apply penalty to colinear spans
      combined_span_wt=cur_span_path_wt+next_wt #include conditions for colinarity
      found_combined_span_path_wt=path_wt_dict.get(next_span,0)
      if combined_span_wt>found_combined_span_path_wt:
        path_wt_dict[next_span]=combined_span_wt
        prev_span_dict[next_span]=cur_span
  #now processing the paths from each point
  used=[] #groups of spans along a rectangle that were used before
  for k,v in prev_span_dict.items(): 
    found=v
    path=[k]
    if found: path.append(found)
    while found:
      found=prev_span_dict.get(found)
      if found: path.append(found)
    cur_path=list(reversed(path))
    cur_wts=[cur_span_dict[v] for v in cur_path]
    for i0 in range(len(cur_path)):
      for i1 in range(i0+1,len(cur_path)):
        slice_spans=cur_path[i0:i1+1]
        if slice_spans in used: continue
        used.append(slice_spans)
        span1,span2=slice_spans[0],slice_spans[-1]
        slice_pts=[]
        for sp in slice_spans: 
          found_pts=pt_dict[sp]
          slice_pts.extend(found_pts)

        mixed_spans=span1+span2 #calculate the window of the two spans
        mixed_spans_xs=[v[0] for v in mixed_spans]
        mixed_spans_ys=[v[1] for v in mixed_spans]
        min_x,max_x=min(mixed_spans_xs),max(mixed_spans_xs)
        min_y,max_y=min(mixed_spans_ys),max(mixed_spans_ys)

        full_se_span=((min_x,min_y),(max_x,max_y))
        full_ne_span=((min_x,max_y),(max_x,min_y))

        found_se_wt=se_span_dict.get(full_se_span,0)
        found_ne_wt=ne_span_dict.get(full_ne_span,0)

        slice_wts=cur_wts[i0:i1+1]
        slice_total_wt=sum(slice_wts)
        if slice_total_wt> found_se_wt and slice_total_wt>found_ne_wt: #if the newly created span has more weight that what is found in se_dict or ne_dict, update
          se_span_dict[full_se_span]=slice_total_wt
          ne_span_dict[full_ne_span]=slice_total_wt
          pt_dict[full_se_span]=slice_pts
          pt_dict[full_ne_span]=slice_pts
  return se_span_dict, ne_span_dict, pt_dict



def phrase_extraction(src,trg,solution,phrase_size_limit=10): #main extraction function 
  #This function accepts the source and target tokenized sentences
  #in addition to the alignment solution, showing the mapping between src and trg tokens 
  #and the maximum size of a source phrase (in tokens)
  #solution=[(j,i) for i,j in solution] #we will need to check this from the input, for some reason the dynamix programming algorithms switches the x,y (i,j) src/trg coordinates

  used_j=sorted(list(set([v[1] for v in solution]))) #we need this to extend the identified target phrase with surrounding unaligned points
  all_phrase_pairs=[]

  for i0 in range(len(src)): #iterating over the source sentence, similar to Koehn's algorithm
    for i1 in range(i0,len(src)):
      if i1-i0>phrase_size_limit-1: break
      #if i0==i1: continue
      accept=True
      j0,j1=len(trg),0 #initializing the target span 
      for ii,jj in solution:
        if ii>=i0 and ii<=i1: 
          if jj<j0: j0=jj #getting the minimum target point within the current source span (i0,i1)
          if jj>j1: j1=jj #and also the maximum point 

      if j1==0: accept=False #if there are no points within the source span, we don't accept the span 
      
      for ii,jj in solution: #and then we check if there are points within the identified target span (j0,j1) that fall outside the source span
        if jj>=j0 and jj<=j1: 
          if ii<i0 or ii>i1: 
            accept=False
            break        
      if accept: #if now the source span and target span are acceptable, we proceed
        #print("SRC:", i0,i1,src[i0:i1+1])
        src_phrase=" ".join(src[i0:i1+1]) #This is the source phrase, based on the sentence tokens and the source span
        #print("TRG:",j0,j1,trg[j0:j1+1], accept)

        #and then based on the list of used j indexes, we try to identify the previous aligned j-coordinate and the next
        #in order to extend the span for unalign points >>> I think there is an easier way
        used_j_before=[v for v in used_j if v<j0] 
        used_j_after=[v for v in used_j if v>j1]
        if used_j_before: #so we identify the starting points of the extended span
          prev_j=used_j_before[-1] #if there are aligned points before, we include all unaligned points between the current j index and the previous
          starting_pts=list(range(prev_j+1,j0+1))
        else: starting_pts=[j0] 

        if used_j_after: #we do the same for the points after
          next_j=used_j_after[0]
          ending_pts=list(range(j1,next_j+1))
        else: ending_pts=[j1] #

        for j0_ in starting_pts: #now we can add the src and trg phrases to the final phrase list
          for j1_ in ending_pts:
            #print("TRG EXTENDED:", j0_, j1_, trg[j0_:j1_+1])
            trg_phrase=" ".join(trg[j0_:j1_+1])
            all_phrase_pairs.append((src_phrase,trg_phrase))
  return all_phrase_pairs


def align_extract(src,trg,src_inverted_index,trg_inverted_index, n_iterations=10,max_skip=8, max_phrase_size=10): #full processing of align and extract
  src=["<s>"]+src+["</s>"] #adding start and end sentences
  trg=["<s>"]+trg+["</s>"]
  if len(src)+len(trg)>150: n_iterations=2 #when sentences are very long, do only two iterations
  cur_wt_list=match_sentences_indexes(src,trg,src_inverted_index,trg_inverted_index)
  pts=get_candidate_pts(cur_wt_list,len(src),len(trg))
  pts.sort()
  full_span=((0,0),pts[-1])
  cur_wt_dict=dict(iter(cur_wt_list))
  cur_se_span_dict,cur_ne_span_dict,cur_pt_dict={},{},{}
  for p in pts:
    wt=cur_wt_dict[p]
    cur_se_span_dict[(p,p)]=wt
    cur_ne_span_dict[(p,p)]=wt
    cur_pt_dict[(p,p)]=[p]
  prev_align_wt=0
  for _ in range(n_iterations):
    cur_se_span_dict,cur_ne_span_dict,cur_pt_dict=get_path_rect(cur_se_span_dict,cur_ne_span_dict,cur_pt_dict,True)
    cur_se_span_dict,cur_ne_span_dict,cur_pt_dict=get_path_rect(cur_se_span_dict,cur_ne_span_dict,cur_pt_dict,False)
    cur_align_wt=cur_se_span_dict[full_span]
    cur_align_pts=cur_pt_dict[full_span]
    #print("iteration #", _, "cur_align_wt",cur_align_wt,"cur_align_pts",cur_align_pts)
    if cur_align_wt==prev_align_wt: break
    prev_align_wt=cur_align_wt
  solution=cur_align_pts
  phrase_pairs=phrase_extraction(src,trg,solution, max_phrase_size)
  return solution,phrase_pairs


#===================================#



#we want to access a huge file for a certail line number
#so we encode the line number as a fixed-length string and save it into a new, smaller file
#so in the small file, we multiply the line number with the length of the fixed length string
#then decode this string to a number >>> this number is the location of the big file that 
#we can use seek and then readline to retrieve
#OR we may just use this: https://stackoverflow.com/questions/5901153/compress-large-integers-into-smallest-possible-string

def encode_num(int_number,size=6,base=128):
  num=int_number
  encoded=""
  while num>0:
    div,rem=(int(num/base), num%base)
    our_char=chr(rem)#.encode("utf-8")
    num=div
    encoded+=our_char
  encoded+=chr(0)*(size-len(encoded))
  return encoded

def decode_num(encoded_str,base=128):
  total=0
  for i,c in enumerate(encoded_str):
    total+=ord(c)*base**i
  return total

def number_file_lines(main_file_path,numbering_file_path):
  if sys.version[0]=="2": file_locs_fopen=open(numbering_file_path,"w")
  else: file_locs_fopen=open(numbering_file_path,"w",newline="")
  
  main_fopen=open(main_file_path,"r")
  #i_=0
  while True:
    loc=main_fopen.tell()
    line=main_fopen.readline()
    encoded_loc=encode_num(loc)
    file_locs_fopen.write(encoded_loc)
    if line=="": break

  main_fopen.close()
  file_locs_fopen.close()

def get_line(line_num, main_file_obj,locs_file_obj,str_size=6):
  lookup_i=line_num*str_size
  locs_file_obj.seek(lookup_i)
  chars=locs_file_obj.read(str_size)
  file_loc=decode_num(chars)
  main_file_obj.seek(file_loc)
  file_line=main_file_obj.readline()
  return file_line
