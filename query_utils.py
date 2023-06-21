import re,json
from scipy import spatial
from itertools import groupby
# from code_utils.general import *
# from code_utils.parsing_lib import *
# from code_utils.dep_lib import *
# from code_utils.sqld_utils import *
import gensim
import gensim.downloader as api
import code_utils.sqld_utils as sqld
import code_utils.parsing_lib as parse
import code_utils.dep_lib as dep
import code_utils.general as general



cur_excluded=["the","of","for", "in","on","at","to","from","and"]

def text2parsed(text):
  conll_2d0=parse.get_conll(text)
  parse_out_dict0=dep.dep2phrases(conll_2d0)
  return parse_out_dict0

def cos_sim(vector1,vector2):
  if len(vector1)==0 or len(vector2)==0: return 0
  result = 1 - spatial.distance.cosine(vector1, vector2)
  return result

def text_split(text,excluded_words=[]):
  text_words=re.findall("\w+",text.lower())
  text_words=[v for v in text_words if not v in excluded_words]
  return text_words

def AND(vals):
  vals=[v for v in vals if v!=None]
  if vals==[]: return []
  cur_results=vals[0]
  for v1 in vals[1:]:
    cur_results=list(set(cur_results).intersection(set(v1)))
  return cur_results

def OR(vals):
  flat_list = [item for sublist in vals for item in sublist]
  return list(set(flat_list))


def retrieve_query(query,index_dict,prev_results=None):
  final_result_dict={}
  temp_output_res_dict={}
  for query_key,query_val in query.items():
    temp_output_res_dict[query_key]=index_dict[query_key].get(query_val,[])
  cur_vals=[]
  query_parameters_output=[]
  for query_key,query_val in query.items():
    if query_val==None: continue
    query_res=temp_output_res_dict.get(query_key,[])
    cur_vals.append(query_res)
    single_query_key="%s=%s"%(query_key,query_val)
    query_parameters_output.append((single_query_key,len(query_res)))
  combined=AND(cur_vals)
  new_combined=combined
  if prev_results!=None: new_combined=list(set(combined).intersection(prev_results))
  final_result_dict["query"]=query
  final_result_dict["query_parameters_output"]=query_parameters_output
  final_result_dict["n"]=len(combined)
  final_result_dict["results"]=combined
  final_result_dict["merged_results"]=new_combined
  return final_result_dict

def get_span_dist(span0,span1):
  if span0[0]>span1[0] or span0[1]>span1[1]: span0,span1=span1,span0
  return span1[0]-span0[1]

def check_used_span(span0,list_used_spans):
  for span1 in list_used_spans:
    dist0=get_span_dist(span0,span1)
    if dist0<1: return True
  return False


def parse_query(query,subject_vec_list,subject_dict,country_dict,wv_model):
  out_dict=text2parsed(query)
  phrase_info=out_dict["phrase_info"]
  word_list=general.tok(query)
  lemma_list=[v.lower() for v in out_dict["lemmas"]]
  lemma_list=["favour" if v=="favor" else v for v in lemma_list]
  el_span_list=[]
  vote_span=general.is_in(["vote"],lemma_list)
  vote_for_span=general.is_in(["vote","for"],lemma_list)
  if vote_for_span==[]: vote_for_span=general.is_in(["vote","in","favour"],lemma_list)
  vote_against_span=general.is_in(["vote","against"],lemma_list)
  vote_abstain_span=general.is_in(["abstain"],lemma_list)
  if vote_span!=[]: el_span_list.append(("voting","vote",vote_span[0],1.0))
  if vote_for_span!=[]: el_span_list.append(("voting","vote_for",vote_for_span[0],1.1))
  if vote_against_span!=[]: el_span_list.append(("voting","vote_against",vote_against_span[0],1.1))
  if vote_abstain_span!=[]: el_span_list.append(("voting","vote_abstaining",vote_abstain_span[0],1.1))

  for a,b in phrase_info.items():
    if not a.startswith("N"): continue
    cur_text=b["text"]
    cur_span=b["span"]
    corr_country=country_dict.get(cur_text.upper())
    if corr_country!=None:
      el_span_list.append(("country",corr_country,cur_span,1.1))
      continue
    corr_subject=subject_dict.get(general.str2key(cur_text))
    #print("cur_text",cur_text,corr_subject)
    if corr_subject!=None:
      el_span_list.append(("subject",corr_subject,cur_span,1.1))
      continue

    cur_text_words=text_split(cur_text)
    cur_text_vec=wv_model.wv.get_mean_vector(cur_text_words)
    #print(a,b["text"],b["span"])
    sim_list=[]
    for subj0,subj_vec0 in subject_vec_list:
      if len(cur_text.split())==1 and len(subj0.split())>1: continue
      sim0=cos_sim(subj_vec0,cur_text_vec)
      if sim0<0.5: continue
      sim_list.append((subj0,sim0))
    sim_list.sort(key=lambda x:-x[-1])

    for subj1,sim1 in sim_list[:5]:
      el_span_list.append(("subject",subj1,cur_span,sim1))
    #print("-------")
  used_spans=[]
  used_text=[]
  structured_query_elements=[]
  el_span_list.sort(key=lambda x:(-x[-1],-len(x[1])))
  for el0 in el_span_list:
    #print(">>>>", el0,len(el0))
    el_type,el_text,el_span,el_wt=el0
    if el_text in used_text: continue
    check_span_is_used=check_used_span(el_span,used_spans)
    if check_span_is_used: continue
    if el_type=="subject" and len(el_text.split())==1: pass
    else: used_spans.append(el_span)
    used_text.append(el_text)
    #print(el0)
    structured_query_elements.append(el0)
  structured_query_elements.sort()
  grouped=[(key,[v[1:] for v in list(group)]) for key,group in groupby(structured_query_elements,lambda x:x[0])]
  structured_query_dict={}
  open_tag_dict,close_tag_dict={},{}
  for key0,grp0 in grouped:
    grp0.sort(key=lambda x:-len(x[0]))
    cur_str0,cur_span0,cur_wt0=grp0[0]
    cur_open_tag='<span title="%s" class="%s">'%(cur_str0,key0)
    cur_close_tag='</span>'
    x0,x1=cur_span0
    open_tag_dict[x0]=cur_open_tag
    close_tag_dict[x1]=cur_close_tag
    #print(key0,grp0[0])
    structured_query_dict[key0]=grp0[0][0]
  
  # for a,b in structured_query_dict.items():
  #   print(a,b)
  final_tagged_query_html_items=[]
  words_space=general.de_tok_space(word_list)
  for w_i,ws0 in enumerate(words_space):
    word0,space0=ws0
    cur_open_tag=open_tag_dict.get(w_i,"")
    cur_close_tag=close_tag_dict.get(w_i,"")
    word_tag_space_str=cur_open_tag+word0+cur_close_tag+space0
    final_tagged_query_html_items.append(word_tag_space_str)
  final_tagged_query_html="".join(final_tagged_query_html_items)
  #print(final_tagged_query_html)
  return structured_query_dict,final_tagged_query_html
  

def query2output(query_text,index_dict,info_dict,subject_vec_list,subject_dict,country_dict,wv_model):
  structured_query_dict1,tagged_query1=parse_query(query_text,subject_vec_list,subject_dict,country_dict,wv_model)
  country=structured_query_dict1.get("country")
  voting=structured_query_dict1.get("voting")
  subject=structured_query_dict1.get("subject")
  print("country",country,"voting",voting,"subject",subject)
  narrative="Sorry, no information found"
  narrative_elements=[]
  
  data=[]
  if country==None: 
    narrative_elements.append("Sorry, country was mentioned.")
    return " ".join(narrative_elements),data
  cur_query_dict={}
  if subject!=None: 
    narrative_elements.append("Analyzing information for subject: %s."%subject.title())
    cur_query_dict["subjects"]=subject
  
  # for voting in ["vote_for","vote_against", "vote_abstaining"]:
  # all_voting_keys=["vote_for","vote_against", "vote_abstaining"]
  # for vote_status0 in all_voting_keys:
  #   if voting in 
  if voting in ["vote_for","vote_against", "vote_abstaining"]:
    cur_query_dict[voting]=country
    #if voting=="vote_for": 
  
  print("cur_query_dict",cur_query_dict)
  out0=retrieve_query(cur_query_dict,index_dict,prev_results=None)
  data=out0["results"]
  if voting=="vote_for": 
    if len(data)==0: narrative_elements.append("%s didn't vote in favour of any resolution."%(country))
    elif len(data)==1: narrative_elements.append("%s voted in favour of one resolution."%(country))
    else: narrative_elements.append("%s voted in favour of %s resolutions."%(country,len(data)))
  if voting=="vote_against": 
    if len(data)==0: narrative_elements.append("%s didn't vote against any resolution."%(country))
    elif len(data)==1: narrative_elements.append("%s voted against one resolution."%(country))
    else: narrative_elements.append("%s voted against %s resolutions."%(country,len(data)))
  if voting=="vote_abstaining": 
    if len(data)==0: narrative_elements.append("%s didn't abstain from voting on any resolution."%(country))
    elif len(data)==1: narrative_elements.append("%s abstained from voting on one resolution."%(country))
    else: narrative_elements.append("%s abstained from voting on %s resolutions."%(country,len(data)))
  data_with_info=[]
  for d0 in data:
    cur_info=info_dict[d0]
    symbol=cur_info["symbol"]
    title=cur_info["title"]
    adoption_date=cur_info["adoption_date"]
    data_with_info.append((symbol,title,adoption_date))

  return " ".join(narrative_elements),data_with_info  