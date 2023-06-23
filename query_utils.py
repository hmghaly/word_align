import time, json, shelve, os, re, sys
from scipy import spatial
from itertools import groupby
# from code_utils.general import *
# from code_utils.parsing_lib import *
# from code_utils.dep_lib import *
# from code_utils.sqld_utils import *
sys.path.append("code_utils")

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
  syntax_dict=text2parsed(query)
  phrase_info=syntax_dict["phrase_info"]
  word_list=general.tok(query)
  lemma_list=[v.lower() for v in syntax_dict["lemmas"]]
  lemma_list=["favour" if v=="favor" else v for v in lemma_list]
  pos_tags=syntax_dict["pos"]
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

  #identify words by string match and by POS info
  for word_i,word0 in enumerate(word_list):
    tag0=pos_tags[word_i]
    if tag0.startswith("W"):
      el_span_list.append(("question",word0.lower(),(word_i,word_i),1.1))
    if word0.lower().startswith("a/res") or word0.lower().startswith("s/res"):
      el_span_list.append(("symbol",word0,(word_i,word_i),1.1))




  np_list_with_sim=[]
  all_nps=[]

  for a,b in phrase_info.items():
    if not a.startswith("N"): continue
    cur_text=b["text"]
    cur_span=b["span"]
    all_nps.append((cur_text,cur_span))
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
      sim_list.append((subj0,round(sim0,4)))
    sim_list.sort(key=lambda x:-x[-1])

    for subj1,sim1 in sim_list[:5]:
      el_span_list.append(("subject",subj1,cur_span,sim1))
    np_list_with_sim.append((cur_text,cur_span,el_span_list[:5]))
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
  raw_structured_query_dict={}
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
    raw_structured_query_dict[key0]=grp0[0][0]
  
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
  query_parse_dict={}
  query_parse_dict["raw_structured_query_dict"]=raw_structured_query_dict
  query_parse_dict["tagged_query_html"]=final_tagged_query_html
  query_parse_dict["syntax_dict"]=syntax_dict
  query_parse_dict["lemmas"]=lemma_list
  query_parse_dict["np_list_with_sim"]=np_list_with_sim
  query_parse_dict["all_nps"]=all_nps
  
  query_parse_dict["conll"]=dep.conll2str(syntax_dict["conll"])

  #syntax_dict
  
  
  

  return query_parse_dict #structured_query_dict,final_tagged_query_html
  

def query2output(query_text,index_dict,info_dict,subject_vec_list,subject_dict,country_dict,wv_model):
  #structured_query_dict1,tagged_query1
  query_parse_dict0=parse_query(query_text,subject_vec_list,subject_dict,country_dict,wv_model)
  raw_structured_query_dict1=query_parse_dict0["raw_structured_query_dict"]
  tagged_query1=query_parse_dict0["tagged_query_html"]

  country=raw_structured_query_dict1.get("country")
  voting=raw_structured_query_dict1.get("voting")
  subject=raw_structured_query_dict1.get("subject")
  question=raw_structured_query_dict1.get("question")
  symbol=raw_structured_query_dict1.get("symbol")

  #print("country",country,"voting",voting,"subject",subject)
  narrative="Sorry, no information found"
  narrative_elements=[]
  data=[]
  data_with_info=[]
  structured_query_dict={}

  final_out_dict={}
  final_out_dict["narrative"]=" ".join(narrative_elements)
  final_out_dict["data_with_info"]=data_with_info
  final_out_dict["query_parse_dict"]=query_parse_dict0
  final_out_dict["structured_query_dict"]=structured_query_dict
  
  query_intent=""
  structured_query_dict={}
  if subject!=None: structured_query_dict["subjects"]=subject
  if country!=None and voting in ["vote_for","vote_against", "vote_abstaining"]: structured_query_dict[voting]=country
  if symbol!=None: structured_query_dict["symbol"]=symbol

  out0=retrieve_query(structured_query_dict,index_dict,prev_results=None)
  id_list=out0["results"]
  data_with_info=[]
  for d0 in id_list:
    cur_info=info_dict[d0]
    symbol=cur_info["symbol"]
    title=cur_info["title"]
    adoption_date=cur_info["adoption_date"]
    data_with_info.append((symbol,title,adoption_date))

  if symbol!=None and question=="when" and len(id_list)>0:
    cur_info_dict=info_dict[id_list[0]]
    adoption_date=cur_info_dict["adoption_date"]
    narrative_elements.append("Resolution %s was adopted on %s"%(symbol,adoption_date))
  elif subject!=None and country==None:
    narrative_elements.append("For the subject: (%s), %s resolutions were adopted."%(subject,len(id_list)))
  elif country!=None and voting in ["vote_for","vote_against", "vote_abstaining"]:
    if subject!=None:
      narrative_elements.append("Analyzing information for subject: (%s). "%subject.title())
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
  else:
    narrative_elements.append("Sorry, no information was found.")


  #print("structured_query_dict",structured_query_dict)
  final_out_dict={}
  final_out_dict["narrative"]=" ".join(narrative_elements)
  final_out_dict["data"]=data_with_info
  final_out_dict["query_parse_dict"]=query_parse_dict0
  final_out_dict["structured_query"]=structured_query_dict
  
  #final_out_dict["narrative"]=" ".join(narrative_elements)

  return final_out_dict #" ".join(narrative_elements),data_with_info,raw_structured_query_dict1,tagged_query1  