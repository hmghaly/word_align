#import re, json
from collections import defaultdict
#spaCy part
import os, re, shelve, sys, string, json
import spacy
from spacy.tokenizer import Tokenizer
from itertools import groupby
sys.path.append("code_utils")

cur_lib_path=os.path.split(__file__)[0]
sys.path.append(cur_lib_path)


import general
import rnn_utils


# 10 December 2025 - New Parsing approach CFG/GPSG

import re, copy
import itertools
from itertools import product
import torch
import numpy as np

#27 December 2025 Update
import re, copy
import itertools
from itertools import product
#from code_utils.parsing_lib import *

#31 December 2025
class Parser:
  def __init__(self,rules_list=[],word_features_list=[],params={}) -> None:
    self.unknown_tags=params.get("unknown_tags",["N","V","JJ","RB"]) #maybe get the actual distribution of these tags from corpora
    self.sent_padding=params.get("sent_padding",False)
    self.default_wt=params.get("default_wt",0.5) #to apply on unknown tags
    self.min_pos_wt=params.get("min_pos_wt",0.2)
    self.pos_model_path=params.get("pos_model_path")
    self.final_word_features_dict=params.get("final_word_features_dict",{})
    self.xpos_ft_dict=params.get("xpos_ft_dict",{})
    self.max_n_phrases=params.get("max_n_phrases",10) #max n phrases per key
    self.djk_max_span_distance=params.get("djk_max_span_distance",3) #max difference between two spans when applying djekstra's algorithm
    self.djk_distance_penalty_ratio=params.get("djk_distance_penalty_ratio",0.5) #penalty applied dpending on the distance between two consecutive spans on djk path
    self.djk_use_negative_wt=params.get("djk_use_negative_wt",False) #whether to use actual weight or negative weight to get the optimum path

    self.max_skip_distance=params.get("max_skip_distance",3) #max number of tokens to skip between phrases
    self.debug=params.get("debug",False)

    self.combined_fragmented=params.get("combined_fragmented",False) #combine fragmented phrases



    self.rerank_params=params.get("rerank_params",{}) #rerank/parse scoring parameters, including reranking neural model 

    self.max_cat_proj=params.get("max_cat_proj",100) #maximum number of times to project a category for a particular head token
    self.pos_tagger=POS(self.pos_model_path)

    self.unknown_token_tags=[("N","noun"),("V","verb"),("JJ","adj"),("RB","adv")]
    self.unknown_token_tags_wt_dict={}
    #process all word features

    #process all rules
    self.all_processed_rules=[]
    self.cat_fwd_index=[]
    self.feat_fwd_index=[]
    for i0,r0 in enumerate(rules_list):
      processed_rule=process_rule(r0)
      if processed_rule==None: continue
      processed_rule["rule_i"]=i0
      self.all_processed_rules.append(processed_rule)

    for i0, processed_rule in enumerate(self.all_processed_rules):
      last_child=processed_rule["children"][-1]
      last_child_cat=last_child["cat"]
      last_child_features=last_child["feat"]
      self.cat_fwd_index.append((last_child_cat,i0))
      for ft0 in last_child_features: self.feat_fwd_index.append((ft0,i0))
    self.cat_fwd_index.sort()
    self.feat_fwd_index.sort()
    self.cat_inv_index=dict(iter([(key,[v[1] for v in list(group)]) for key,group in groupby(self.cat_fwd_index,lambda x:x[0])]))
    self.feat_inv_index=dict(iter([(key,[v[1] for v in list(group)]) for key,group in groupby(self.feat_fwd_index,lambda x:x[0])]))
    #self.phrase_list=[]


  def parse(self,tokens):
    self.phrase_list=[] #list of all phrase objects, with spans, weights, children
    self.cat_phrase_index={}
    self.feat_phrase_index={}

    self.end_start_phrase_dict={} #dict[end][start][cat]=[{phrase_obj1},{phrase_obj2},{phrase_obj3}]
    self.span_wt_dict={} #dict[(start,end)]=wt
    self.span_phrase_dict={} #dict[(start,end)]={phrase_obj}
    self.phrase_key_obj_dict={} #dict[phrase_key]=phrase_obj


    self.projection_counter={}
    self.head_loc_cat_projection_counter={} #counting how many times this category was projected from the same head token dict[(head_loc,cat)]=count


    tokens_pos_list=self.pos_tagger.tag_words(tokens,min_wt=self.min_pos_wt)
    self.cur_tokens_pos_list=tokens_pos_list

    self.tag_wt_list=[]

    if self.debug: print(tokens_pos_list)
    for token_i,a in enumerate(tokens_pos_list): #process each token
      token0=a["word"]
      if self.debug: print(token_i,token0,len(self.phrase_key_list))

      xpos0=a.get("xpos",[])
      start0,end0=token_i,token_i
      wt=self.default_wt
      outcome=self.final_word_features_dict.get(token0.lower(),[]) #outcome is multiple tag/cat options, with their features
      outcome_wt=[(cat0,feat0,1) for cat0,feat0 in outcome] #use a weight of 1 for the specific closed class words
      temp_used_cat_list=[v[0] for v in outcome_wt]
      for xpos_tag0,xpos_wt0 in xpos0:
        if xpos_tag0 in temp_used_cat_list: continue
        xpos_ft0=self.xpos_ft_dict.get(xpos_tag0,[])
        outcome_wt.append((xpos_tag0,xpos_ft0,xpos_wt0))
      #if nothing found
      if outcome_wt==[]:
        for cat0,feat0 in self.unknown_token_tags: outcome_wt.append((cat0,feat0,self.default_wt))

      self.tag_wt_list.append((token0,outcome_wt))
      #for the current token, identify all the outcomes with their weights
      #print("token0",token0)
      all_token_new_phrases=[]
      for cat0,feat_split,wt0 in outcome_wt:
        if cat0=="": continue
        #only one phrase object per cat/features pair
        cur_phrase_obj={"wt":wt0,"span":1,"start":start0,"end":end0,"cat":cat0,"feat":feat_split,"head_loc":start0,"children":[],"level":0}
        check_added_phrases=self.add_phrase3(cur_phrase_obj)
        
        #print(check_added_phrases,"Projecting:",cur_phrase_obj)
        new_phrases=self.project_phrase3(cur_phrase_obj)  
        # for a in new_phrases:
        #   print("NEW:",a)
        all_token_new_phrases.extend(new_phrases)
      while all_token_new_phrases:
        all_token_new_phrases_copy=copy.deepcopy(all_token_new_phrases)
        all_token_new_phrases=[]
        for ph0 in all_token_new_phrases_copy:
          check_added_phrases=self.add_phrase3(ph0)
          #print("recursive check/project:", check_added_phrases,ph0)
          if check_added_phrases==False: continue
          projected_new_phrases=self.project_phrase3(ph0)
           
          all_token_new_phrases.extend(projected_new_phrases)          



    final_parse_phrases=[]
    final_raw_parses=[]
    end_of_sentence_dict=self.end_start_phrase_dict.get(len(tokens)-1,{})
    
    full_span_sub_dict=end_of_sentence_dict.get(0,{}) #first getting the parses that span the full sentence
    for cat0,phrases0 in full_span_sub_dict.items():
      final_parse_phrases.extend(phrases0)
      for ph0 in phrases0:
        dep0,const0=self.export_parse2(tokens,ph0,True)
        final_raw_parses.append((ph0,dep0,const0))

    #full_span_phrases=end_of_sentence_dict.get(0,[])

    #combine_exported_deps(words,dep_list)
    djk_phrases=self.optimum_path(tokens,self.span_phrase_dict) #then get djk optimum path phrases
    if djk_phrases:
      temp_dep_list=[]
      combined_const=[]
      for djk_ph0 in djk_phrases:
        dep0,const0=self.export_parse2(tokens,djk_ph0,False)
        temp_dep_list.append(dep0)
        combined_const.extend(const0)
      combined_djk_phrase=self.combine_phrases(djk_phrases,{}) #combine all phrases on djk path into one phrase
      combined_djk_phrase["cat"]="DJK-combined"
      self.combined_dep=combine_exported_deps(tokens,temp_dep_list)
      final_raw_parses.append((combined_djk_phrase,self.combined_dep,combined_const))

    #finally include additional top phrases based on weight and span
    span_wt_items=list(self.span_wt_dict.items())
    span_wt_items.sort(key=lambda x:-x[-1])

    #create a parse of multiple phrases by combining the highest phrases with non-overlapping spans
    #basically combining fragmented phrases
    if self.combined_fragmented:
      valid_sorted_span_phrases=[]
      used_indexes=[]
      for span0,wt0 in span_wt_items: 
        i0,i1=span0
        if i0==i1: continue
        cur_span_indexes=list(range(i0,i1+1))
        overlap_with_used=list(set(used_indexes).intersection(set(cur_span_indexes)))
        valid=False
        if overlap_with_used==[]:
          used_indexes.extend(cur_span_indexes)
          valid=True
        if valid: 
          ph0=self.span_phrase_dict.get(span0)
          if ph0!=None: valid_sorted_span_phrases.append(ph0)

      if valid_sorted_span_phrases:
        combined_phrase=self.combine_phrases(valid_sorted_span_phrases)
        combined_phrase["cat"]="COMBINED"
        dep0,const0=self.export_parse2(tokens,combined_phrase,True)
        final_raw_parses.append((ph0,dep0,const0))




    cur_max=max(0,self.max_n_phrases-len(final_raw_parses))  #remaining number of parses till we get to the maximum n_parses/prases per span
    for span0,wt0 in span_wt_items[:cur_max]:
      ph0=self.span_phrase_dict.get(span0)
      if ph0==None: continue
      dep0,const0=self.export_parse2(tokens,ph0,True)
      final_raw_parses.append((ph0,dep0,const0))

    temp_wt_score_parse_list=[]
    for ph0,dep0,const0 in final_raw_parses:
      ph_wt0=ph0["wt"]
      dep_score0=self.score_dep_obj(dep0)
      temp_wt_score_parse_list.append((ph0,dep0,const0,ph_wt0,dep_score0))

    temp_wt_score_parse_list.sort(key=lambda x:(-x[-1],-x[-2])) #sort by the dependency score then the top phrase weight
    final_sorted_parses=[v[:3] for v in temp_wt_score_parse_list]

    outcome_dict={}
    outcome_dict["pos"]=self.tag_wt_list
    outcome_dict["parses"]=final_sorted_parses


  

    # if final_parse_phrases==[]:
    #   span_wt_items=list(self.span_wt_dict.items())
    #   span_wt_items.sort(key=lambda x:-x[-1])
    #   for span0,wt0 in span_wt_items[:5]:
    #     start0,end0=span0
    #     cat_phrases_subdict=self.end_start_phrase_dict[end0][start0]
    #     for cat0,phrases0 in cat_phrases_subdict.items():
    #       for ph0 in phrases0: final_parse_phrases.append(ph0) #print(ph0)


    #return self.tag_wt_list
    # final_raw_parses=[]
    # final_parse_phrases.sort(key=lambda x:(-x["span"],-x["wt"]))
    # for fp0 in final_parse_phrases[:self.max_n_phrases]:
    #   dep0,const0=self.export_parse2(tokens,fp0)
    #   final_raw_parses.append((fp0,dep0,const0))
    return outcome_dict

  def score_dep_obj(self,dep_obj,rerank_params=None):
    if rerank_params==None: cur_rerank_params=rerank_params
    else: cur_rerank_params=self.rerank_params
    n_heads=0
    n_unparsed=0
    for d0 in dep_obj:
      cur_head=d0["head"]
      if cur_head=="0": n_heads+=1
      if cur_head=='-' or cur_head=="": n_unparsed+=1
    multi_head_penalty=n_heads-1 #if we have only one head, penalty is zero
    multi_head_unparsed_score=(len(dep_obj)-multi_head_penalty-n_unparsed) /len(dep_obj)
    dep_score0=multi_head_unparsed_score
    return dep_score0




  def project_phrase3(self,phrase_obj0): #only for maximum binary branching
    #print("projecting:",phrase_obj0)
    new_level=phrase_obj0.get("level",0)+1
    wt_inc=new_level*0.00001 #weight increment - to give a higher weight for the higher level projection phrases
    #wt_inc=0

    #phrase_obj0["level"]=phrase_obj0.get("level",0)+1
    cur_phrase_key=self.get_phrase_key(phrase_obj0)
    self.projection_counter[cur_phrase_key]=self.projection_counter.get(cur_phrase_key,0)+1
    if self.projection_counter.get(cur_phrase_key,0)>10: return []
    cur_start0=phrase_obj0["start"]


    cur_rules_numbers=self.get_rules(phrase_obj0)
    cur_rules_obj_list=[self.all_processed_rules[r_i] for r_i in cur_rules_numbers]
    cur_rules_obj_list.sort(key=lambda x:len(x["children"]))
    all_combined_phrases=[]
    for cur_rule_obj in cur_rules_obj_list:

      cur_rule_children=cur_rule_obj["children"]
      first_child,last_child=cur_rule_children[0],cur_rule_children[-1] #unary or binary rules
      first_child_cat=first_child["cat"] #we will only use categories for first cat now, but later we can do features

      match_last=match_rule(phrase_obj0,last_child)
      if not match_last: continue
      if len(cur_rule_children)==1:
        new_combined_phrase=self.combine_phrases([phrase_obj0],cur_rule_obj)
        new_combined_phrase["level"]=new_level
        new_combined_phrase["wt"]+=wt_inc
        all_combined_phrases.append(new_combined_phrase)
        #print("new_combined_phrase",new_combined_phrase)
      else:
        min_prev_end=max(0,cur_start0-self.max_skip_distance)
        for temp_end0 in range(min_prev_end,cur_start0):
          corr_start_dict=self.end_start_phrase_dict.get(temp_end0,{})
          for temp_start0,temp_start_sub_dict0 in corr_start_dict.items():
            temp_phrases=temp_start_sub_dict0.get(first_child_cat,[])
            for tph0 in temp_phrases:
              new_combined_phrase=self.combine_phrases([tph0,phrase_obj0],cur_rule_obj)
              #we want to monitor projection from same rule e.g. VP --> VP^ PP or NP --> NP NP^
              #and limit having so many projections from the same head phrase according to the same rule
              # new_combined_phrase_head_key=new_combined_phrase["head_phrase"] #checking the key/phrase of the new combined phrase
              # new_combined_phrase_head_phrase=self.phrase_key_obj_dict.get(new_combined_phrase_head_key)
              # if new_combined_phrase_head_phrase==None: continue
              # new_combined_phrase_head_phrase_rule=new_combined_phrase_head_phrase.get("rule")
              # same_rule_proj_level=new_combined_phrase.get("same_rule_proj_level",0)
              # if new_combined_phrase_head_phrase_rule==cur_rule_obj:  same_rule_proj_level+=1 
              # new_combined_phrase["same_rule_proj_level"]=same_rule_proj_level

              new_combined_phrase["level"]=new_level
              new_combined_phrase["wt"]+=wt_inc
              all_combined_phrases.append(new_combined_phrase)

    return all_combined_phrases



  def export_parse2(self,words,cur_phrase,export_full_sent=True):
    start0,end0=cur_phrase["start"],cur_phrase["end"]
    phrase_key0=self.get_phrase_key(cur_phrase)
    # print(cur_phrase)
    # return 
    #phrase_head_loc_dict={cur_phrase["i"]: cur_phrase["head_loc"]} #identify the head location for each phrase obj/key is phrase number/phrase index in the phrase list
    phrase_head_loc_dict={phrase_key0: cur_phrase["head_loc"]} #identify the head location for each phrase obj/key is phrase number/phrase index in the phrase list

    dep_dict={} #identify which phrase head loc depends on which phrase head loc
    root_index=cur_phrase["head_loc"] #the root of the current phrase

    cur_tokens_xpos_dict={}
    #unsorted_phrases=sorted(final_phrases,key=lambda x:x["i"]) #they should be sorted anyway by their original order of being added to the list
    parse_phrases=[cur_phrase] #these are the phrases to be used for constituency parsing
    children=cur_phrase.get("children",[])
    new_children=[]

    while children: #go on a semi-recursive way to identify children and subchildren of current main phrase
      for ch0 in children:
        # ch_phrase_key=self.phrase_key_list[ch0]
        # child_phrase=self.main_phrase_dict[ch_phrase_key][0]

        ch_phrase_key=ch0
        #child_phrase=self.phrase_key_obj_dict[ch_phrase_key]
        child_phrase=self.phrase_key_obj_dict.get(ch_phrase_key)
        if child_phrase==None:
          start,end,cat,feat=ch_phrase_key
          span=end-start+1
          child_phrase={"wt":0, "start":start,"end":end,"cat":cat, "feat":feat.split(), "head_loc":start,"children":[],"span":span}
        phrase_head_loc_dict[ch0]=child_phrase["head_loc"]
        if child_phrase["span"]==1 and child_phrase["children"]==[]: #identify the matching XPOS for terminal phrases
          cur_tokens_xpos_dict[child_phrase["start"]]=child_phrase["cat"]
        parse_phrases.append(child_phrase)
        sub_children=child_phrase.get("children",())
        sub_children=list(sub_children)
        for sc in sub_children:
          if sc==ch0: continue
          new_children.append(sc) #print("sc",sc)
      children=new_children
      new_children=[]

    for a in parse_phrases:
      cur_children=a["children"]
      cur_phrase_head_loc=a["head_loc"]
      for ch0 in cur_children: #for each child of the current phrase, identify its head_loc
        ch_head_loc=phrase_head_loc_dict[ch0]
        if ch_head_loc==cur_phrase_head_loc: continue #skip if the head_loc for current child is the same as of the main phrase
        dep_dict[ch_head_loc]=cur_phrase_head_loc #update dependency dict between heads of two phrases

    final_dep_list=[]
    for i0,w0 in enumerate(words): #create dependency info for each word
      cur_id0=i0+1
      if not export_full_sent: #export only the tokens and dependency info within the span of the exported phrase 
        if i0<start0 or i0>end0: continue

      #identify head index
      if i0==root_index: #root word
        cur_dep="0"
        head_word="^"
        offset=0
      else:
        cur_dep=dep_dict.get(i0)
        if cur_dep==None:  #word without attachment
          cur_dep="-"
          head_word=""
          offset=100 #any random number for no offset
        else: #any other word
          head_word=words[cur_dep]
          offset=i0-cur_dep
          cur_dep=str(cur_dep+1)

      cur_xpos0=cur_tokens_xpos_dict.get(i0,"-")
      final_dep_list.append({"id":str(cur_id0),"word": w0,"head":cur_dep,"xpos":cur_xpos0,"head_word":head_word,"offset":offset})
    return final_dep_list, parse_phrases

  def add_phrase3(self,phrase_obj0): #only for maximum binary branching
    span0=start0,end0=phrase_obj0["start"],phrase_obj0["end"]
    wt0=phrase_obj0["wt"]
    found_span_wt0=self.span_wt_dict.get(span0,0)
    # phrase_has_top_span_wt=False

    cat0,children0=phrase_obj0["cat"],phrase_obj0["children"]

    phrase_key0=self.get_phrase_key(phrase_obj0)
    self.phrase_key_obj_dict[phrase_key0]=phrase_obj0


    used_phrase_key_dict={}

    
    temp_end_sub_dict=self.end_start_phrase_dict.get(end0,{}) #get the sub dict for phrases having this end loc
    temp_start_sub_dict2=temp_end_sub_dict.get(start0,{}) #get the subdict with the start loc
    cur_phrases=temp_start_sub_dict2.get(cat0,[]) #get the list of phrases with the [end][start][cat] keys
    if cur_phrases==[]:
      cur_phrases=[phrase_obj0]
    else:
      cur_top_phrase,cur_bottom_phrase=cur_phrases[0],cur_phrases[-1]
      if len(cur_phrases)>=self.max_n_phrases and wt0<cur_bottom_phrase["wt"]: 
        #print("1","cur_phrases",len(cur_phrases))
        return False
      for cur_ph0 in cur_phrases:
        cur_ph0_cat,cur_ph0_children=cur_ph0["cat"],cur_ph0["children"]
        
        
        # if cur_ph0_cat==cat0 and cur_ph0_children==children0 and len(children0)>1: 
        #   #print("2","cur_ph0_cat",cur_ph0_cat,"cat0",cat0)
        #   return False #and wt0<=cur_top_phrase["wt"]: return False


      cur_phrases+=[phrase_obj0]
      cur_phrases.sort(key=lambda x:-x["wt"])
    
    temp_start_sub_dict2[cat0]=cur_phrases[:self.max_n_phrases]
    temp_end_sub_dict[start0]=temp_start_sub_dict2
    self.end_start_phrase_dict[end0]=temp_end_sub_dict

    if cur_phrases[0]["wt"]>found_span_wt0: 
      self.span_wt_dict[span0]=cur_phrases[0]["wt"]
      self.span_phrase_dict[span0]=cur_phrases[0]


    head_loc0=phrase_obj0["head_loc"]
    head_loc_cat_pair=(head_loc0,cat0)
    updated_head_loc_cat_proj_level=self.head_loc_cat_projection_counter.get(head_loc_cat_pair,0)+1
    #if updated_head_loc_cat_proj_level>self.max
    self.head_loc_cat_projection_counter[head_loc_cat_pair]=updated_head_loc_cat_proj_level


    return True


  def combine_phrases(self,phrase_obj_list,applied_rule={}):
    parent_phrase_obj={}
    #cur_child_keys=[v["i"] for v in phrase_obj_list]
    cur_child_keys=[self.get_phrase_key(v) for v in phrase_obj_list]

    levels=[vw["level"] for vw in phrase_obj_list]

    parent_phrase_obj["wt"]=sum([vw["wt"] for vw in phrase_obj_list])
    phrase_start0=min([vw["start"] for vw in phrase_obj_list])
    phrase_end0=max([vw["end"] for vw in phrase_obj_list])

    parent_phrase_obj["span"]=phrase_end0-phrase_start0+1
    parent_phrase_obj["start"]=phrase_start0
    parent_phrase_obj["end"]=phrase_end0

    if applied_rule!={}:
      parent_phrase_obj["cat"]=applied_rule["parent"]["cat"]
      parent_phrase_obj["feat"]=applied_rule["parent"]["feat"]
      rule_head_i=applied_rule["head_i"]
    else:
      parent_phrase_obj["cat"]=""
      parent_phrase_obj["feat"]=[]
      rule_head_i=0




    parent_phrase_obj["children"]=cur_child_keys
    head_phrase_index=cur_child_keys[rule_head_i] #which of the child phrases is the head
    
    parent_phrase_obj["head_phrase"]=head_phrase_index
    # head_phrase_key=self.phrase_key_list[head_phrase_index]
    head_phrase_obj=phrase_obj_list[rule_head_i]  #self.main_phrase_dict[head_phrase_key][0]


    parent_phrase_obj["head_loc"]=head_phrase_obj["head_loc"]

    parent_phrase_obj["rule"]=applied_rule

    parent_phrase_obj["level"]=max(levels)+1

    return parent_phrase_obj
    #parent_phrase_obj["level"]=new_level



  def get_phrase_key(self,phrase_obj0): #check an obj for corresponding key
    start0,end0,cat0,feat_split0=phrase_obj0["start"],phrase_obj0["end"],phrase_obj0["cat"],phrase_obj0["feat"]
    ft_str0=" ".join(feat_split0)
    cur_phrase_key=(start0,end0,cat0,ft_str0)
    return cur_phrase_key


  def get_rules(self,cur_phrase_obj):
    #given a token or phrase with cat/feat pair, identify the rules that apply
    all_rules=[]
    phrase_obj_cat,phrase_obj_feat=cur_phrase_obj["cat"],cur_phrase_obj["feat"]
    cur_cat_rules=self.cat_inv_index.get(phrase_obj_cat,[])
    all_rules.extend(cur_cat_rules)
    for s_feat0 in phrase_obj_feat:
      corr_rules=self.feat_inv_index.get(s_feat0,[])
      all_rules.extend(corr_rules)
    return list(set(all_rules))

  def get_children(self,phrase_obj):
    all_phrases=[phrase_obj]
    children=phrase_obj.get("children",[])
    new_children=[]
    while children: #go on a semi-recursive way to identify children and subchildren of current main phrase
      for ch0 in children:
        ch_phrase_key=self.phrase_key_list[ch0]
        child_phrase=self.main_phrase_dict[ch_phrase_key][0]
        all_phrases.append(child_phrase)
        sub_children=child_phrase.get("children",())
        sub_children=list(sub_children)
        for sc in sub_children:
          if sc==ch0: continue
          new_children.append(sc) #print("sc",sc)
      children=new_children
      new_children=[]
    return all_phrases
  def inspect_span(self,start,end,cat=None):
    end_temp_dict=self.end_start_phrase_dict.get(end,{})
    final_temp_dict=end_temp_dict.get(start,{})
    if cat!=None: final_temp_dict=final_temp_dict.get(cat,{})
    return final_temp_dict
  
  
  def optimum_path(self,words,span_phrase_dict): #apply Djkestra's algorithm to get the optimum path of phrases
    inc0=self.djk_max_span_distance
    dist_penalty0=self.djk_distance_penalty_ratio
    use_negative=self.djk_use_negative_wt

    span_list=sorted(list(span_phrase_dict.keys()))
    span_list=[v for v in span_list if (v[1]-v[0])>0] #only choose multi word phrases
    first_pt0=(-1,-1)
    last_pt0=(len(words),len(words))
    span_list=[first_pt0]+span_list+[last_pt0]
    grouped=[(key,list(group)) for key,group in groupby(span_list,lambda x:x[0])]
    grouped_dict=dict(iter(grouped))
    

    transition_dict={}
    for span0 in span_list:
      span0_start,span0_end=span0
      transition_dict[span0]={}
      all_corr_spans=[]
      for span1_start in range(span0_end+1,span0_end+inc0+1):
        corr_spans=grouped_dict.get(span1_start,[])
        span_dist=span1_start-span0_end-1
        cur_dist_penalty=span_dist*dist_penalty0
        for span1 in corr_spans:
          cur_phrase=span_phrase_dict.get(span1,{})
          span1_wt=cur_phrase.get("wt",0)
          adj_wt=span1_wt-cur_dist_penalty
          if use_negative: adj_wt=-adj_wt
          transition_dict[span0][span1]=adj_wt
      if transition_dict[span0]=={}: transition_dict[span0]={last_pt0:0}

    path0,path_wt0=general.djk(first_pt0,last_pt0,transition_dict,pt_list0=span_list)

    final_top_phrases=[]
    for span0 in path0:
      corr_phrase=span_phrase_dict.get(span0)
      if corr_phrase!=None: final_top_phrases.append(corr_phrase)
    return final_top_phrases





#End of new parser def

def combine_exported_deps(words,dep_list):
  temp_dep_dict={}
  for dep1 in dep_list:
    for d1 in dep1: 
      cur_id1=d1["id"]
      temp_dep_dict[d1["id"]]=d1
  final_dep_lines=[]
  for i0,w0 in enumerate(words):
    cur_id0=str(i0+1)
    found_line_obj=temp_dep_dict.get(cur_id0)
    temp_line_obj={"id":cur_id0,"word": w0,"head":'-',"xpos":'-',"head_word":"","offset":100}
    #print(cur_id0, found_line_obj)
    if found_line_obj==None: found_line_obj=temp_line_obj
    final_dep_lines.append(found_line_obj)
  return final_dep_lines




#4 Jan 2026
def viz_parse(dep,const):
  table_items=[]
  ids=[d0["id"] for d0 in dep]
  tokens=[d0["word"] for d0 in dep]
  heads=[d0["head"] for d0 in dep]
  # ids_labels=["IDs"]+ids
  # tokens_labels=["Words"]+tokens
  # heads_labels=["Heads"]+heads
  border_style='style="border: 2px solid black;"'
  colored_background_style='style="background-color: #F0FFFF;"' #azure

  ids_labels=["<td>IDs</td>"]+[f"<td {border_style}>{v}</td>" for v in ids]
  tokens_labels=["<td>Words</td>"]+[f"<td {border_style}>{v}</td>" for v in tokens]
  heads_labels=["<td>Heads</td>"]+[f"<td {border_style}>{v}</td>" for v in heads]

  ids_row="<tr>"+"".join(ids_labels)+"</tr>"
  tokens_row="<tr>"+"".join(tokens_labels)+"</tr>"
  head_row=f"<tr {colored_background_style}>"+"".join(heads_labels)+"</tr>"



  # ids_row="<tr>"+"".join([f"<td {border_style}>{v}</td>" for v in ids_labels])+"</tr>"
  # tokens_row="<tr>"+"".join([f"<td {border_style}>{v}</td>" for v in tokens_labels])+"</tr>"
  # head_row="<tr>"+"".join([f"<td {border_style}>{v}</td>" for v in heads_labels])+"</tr>"
  table_items+=[ids_row,tokens_row,head_row]
  head_phrase_keys_dict={}
  child_check_dict={}
  max_level=0
  min_updated_level=0
  for c0 in const:
    if c0.get('head_phrase')!=None: head_phrase_keys_dict[c0["head_phrase"]]=True
    for ch0 in c0.get("children",[]): child_check_dict[ch0]=True
    if c0["level"]>max_level: max_level=c0["level"]

  reverse_sorted_const_by_span=sorted(const,key=lambda x:-x.get("span",100))
  adj_const=[]
  adj_level_dict={}
  for c_i in range(len(reverse_sorted_const_by_span)):
    cur_const_obj=reverse_sorted_const_by_span[c_i]
    cur_const_obj_key=get_phrase_key2(cur_const_obj)
    found_adj_level=adj_level_dict.get(cur_const_obj_key)
    if child_check_dict.get(cur_const_obj_key,False): #if a phrase is not a child of something, assign maximum level
      cur_const_obj["level"]=max_level 
    if found_adj_level!=None: 
      #print("original level",cur_const_obj["level"],"adj level",found_adj_level)
      cur_const_obj["level"]=found_adj_level

    cur_const_obj_level=cur_const_obj["level"]
    cur_obj_children=cur_const_obj["children"]
    
    for ch_key0 in cur_obj_children: 
      updated_level=cur_const_obj["level"]-1
      if updated_level<min_updated_level: min_updated_level=updated_level
      adj_level_dict[ch_key0]=updated_level
    #if len(cur_obj_children)==0: cur_const_obj["level"]=0
    adj_const.append(cur_const_obj)
  adj_const1=[]
  for i0 in range(len(adj_const)):
    cur_c0=adj_const[i0]
    if len(cur_c0["children"])==0: cur_c0["level"]=min_updated_level-1
    adj_const1.append(cur_c0)
  # for a,b in head_phrase_keys_dict.items():
  #   print(a,b)
  #sorted_const_by_level=sorted(const,key=lambda x:x.get("level",100))
  sorted_const_by_level=sorted(adj_const1,key=lambda x:x.get("level",100))
  grouped_by_level=[(key,list(group)) for key,group in groupby(sorted_const_by_level,lambda x:x.get("level",100))]
  level_counter=0
  for key0,gl0 in grouped_by_level: 
    #print(key0,gl0) #phrases at this level
    level_phrases_start_dict={}
    for g0 in gl0: 
      start0=g0["start"]
      level_phrases_start_dict[start0]=g0
    cell_i=0
    first_cell=f'<td></td>'
    if level_counter==0: first_cell=f'<td>Tags</td>'
    level_counter+=1
    cur_row_items=[first_cell]
    while cell_i<len(dep):
      found_phrase=level_phrases_start_dict.get(cell_i)
      span0=1
      content=""
      if found_phrase!=None: 
        phrase_key0=get_phrase_key2(found_phrase)
        is_head=head_phrase_keys_dict.get(phrase_key0,False)
        #print("cell_i", cell_i,"is_head",is_head,"found_phrase",found_phrase)


        cat0=found_phrase["cat"]
        span0=found_phrase["span"]
        head_loc=found_phrase["head_loc"]
        head_word=tokens[head_loc]
        
        content=f"{cat0}"
        if span0>1: content=f"{cat0} | {head_word}"
        if is_head: content=f'<b><i>{content}</i></b>'
        #content=f"{cat0} | {head_word}"
        #print("content",content)
      cell_html=f'<td colspan="{span0}"  {border_style}>{content}</td>'
      if content=="": cell_html=f'<td colspan="{span0}">{content}</td>'
      
      cur_row_items.append(cell_html)
      cell_i+=span0
    combined_row_items_str="".join(cur_row_items)
    cur_row=f'<tr>{combined_row_items_str}</tr>'
    table_items.append(cur_row)
  table_rows_str="\n".join(table_items)
  table_str=f'<table style="width: 100%;text-align: center;">{table_rows_str}</table>'
  return table_str

#we will need to get it out of the class
def get_phrase_key2(phrase_obj0): #check an obj for corresponding key
  start0,end0,cat0,feat_split0=phrase_obj0["start"],phrase_obj0["end"],phrase_obj0["cat"],phrase_obj0["feat"]
  ft_str0=" ".join(feat_split0)
  cur_phrase_key=(start0,end0,cat0,ft_str0)
  return cur_phrase_key




#=====================

#OLD
# class Parser:
#   def __init__(self,rules_list=[],word_features_list=[],params={}) -> None:
#     self.unknown_tags=params.get("unknown_tags",["N","V","JJ","RB"]) #maybe get the actual distribution of these tags from corpora
#     self.sent_padding=params.get("sent_padding",False)
#     self.default_wt=params.get("default_wt",0.5) #to apply on unknown tags
#     self.min_pos_wt=params.get("min_pos_wt",0.1)
#     self.pos_model_path=params.get("pos_model_path")
#     self.final_word_features_dict=params.get("final_word_features_dict",{})
#     self.xpos_ft_dict=params.get("xpos_ft_dict",{})
#     self.max_n_phrases=params.get("max_n_phrases",10) #max n phrases per key
#     self.max_skip_distance=params.get("max_skip_distance",3) #max number of tokens to skip between phrases
#     self.debug=params.get("debug",False)
    

#     self.pos_tagger=POS(self.pos_model_path)

#     self.unknown_token_tags=[("N","noun"),("V","verb"),("JJ","adj"),("RB","adv")]
#     self.unknown_token_tags_wt_dict={}
#     #process all word features

#     #process all rules
#     self.all_processed_rules=[]
#     self.cat_fwd_index=[]
#     self.feat_fwd_index=[]
#     for i0,r0 in enumerate(rules_list):
#       processed_rule=process_rule(r0)
#       if processed_rule==None: continue
#       self.all_processed_rules.append(processed_rule)

#     for i0, processed_rule in enumerate(self.all_processed_rules):
#       last_child=processed_rule["children"][-1]
#       last_child_cat=last_child["cat"]
#       last_child_features=last_child["feat"]
#       self.cat_fwd_index.append((last_child_cat,i0))
#       for ft0 in last_child_features: self.feat_fwd_index.append((ft0,i0))
#     self.cat_fwd_index.sort()
#     self.feat_fwd_index.sort()
#     self.cat_inv_index=dict(iter([(key,[v[1] for v in list(group)]) for key,group in groupby(self.cat_fwd_index,lambda x:x[0])]))
#     self.feat_inv_index=dict(iter([(key,[v[1] for v in list(group)]) for key,group in groupby(self.feat_fwd_index,lambda x:x[0])]))
#     #self.phrase_list=[]

#   def parse(self,tokens):
#     self.phrase_list=[] #list of all phrase objects, with spans, weights, children
#     self.cat_phrase_index={}
#     self.feat_phrase_index={}

#     self.phrase_key_list=[] #phrase key is (start,end,cat,feat)
#     self.phrase_key_index_dict={} #mapping the number of each key to the corresponding key
#     self.ft_phrase_key_map_dict={} #an index to map each feature to the corresponding keys
#     self.cat_phrase_key_map_dict={} #an index to map each category to the corresponding keys
#     self.span_phrase_key_map_dict={} #an index to map each span (start,end) to the corresponding keys
#     self.main_phrase_dict={} #mapping each key to the actual phrases corresponding to this key - sorting phrases by weight
#     self.main_phrase_wt_dict={} #mapping each key to the heighest weight for any of its phrases

#     self.projection_counter={}


#     tokens_pos_list=self.pos_tagger.tag_words(tokens,min_wt=self.min_pos_wt)
#     self.cur_tokens_pos_list=tokens_pos_list

#     self.tag_wt_list=[]

#     if self.debug: print(tokens_pos_list)
#     for i,a in enumerate(tokens_pos_list): #process each token
#       token0=a["word"]
#       if self.debug: 
#         proj_items=list(self.projection_counter.items())
#         proj_items.sort(key=lambda x:-x[-1])
#         first_item=None
#         if proj_items: first_item=proj_items[0]
#         print(i,token0,len(self.phrase_list),len(self.phrase_key_list),"proj_items",len(proj_items),"first_item",proj_items[:3])

#       xpos0=a.get("xpos",[])
#       start,end=i,i
#       wt=self.default_wt
#       outcome=self.final_word_features_dict.get(token0,[]) #outcome is multiple tag/cat options, with their features
#       outcome_wt=[(cat0,feat0,1) for cat0,feat0 in outcome] #use a weight of 1 for the specific closed class words
#       temp_used_cat_list=[v[0] for v in outcome_wt]
#       for xpos_tag0,xpos_wt0 in xpos0:
#         if xpos_tag0 in temp_used_cat_list: continue
#         xpos_ft0=self.xpos_ft_dict.get(xpos_tag0,[])
#         outcome_wt.append((xpos_tag0,xpos_ft0,xpos_wt0))
#       #if nothing found
#       if outcome_wt==[]:
#         for cat0,feat0 in self.unknown_token_tags: outcome_wt.append((cat0,feat0,self.default_wt))

#       self.tag_wt_list.append((token0,outcome_wt))


#       for cat0,feat0,wt0 in outcome_wt:
#         feat_split=feat0#.split()
#         #only one phrase object per cat/features pair
#         cur_token_rules=[] #retrieved rules that apply to current token

#         ft_str=" ".join(feat_split)
#         cur_phrase_key=(start,end,cat0,ft_str)
#         cur_phrase_key_i=self.phrase_key_index_dict.get(cur_phrase_key)        

#         cur_phrase_obj={"wt":wt0,"span":1,"start":start,"end":end,"cat":cat0,"feat":feat_split,"head_loc":start,"head_phrase":cur_phrase_key_i,"children":[],"i":cur_phrase_key_i,"level":0}
#         self.add_phrase(cur_phrase_obj)
#         new_phrases=self.project_phrase(cur_phrase_obj)
#         #if self.debug: print("main terminal projection", len(new_phrases),cur_phrase_obj)
#         for a in new_phrases: self.add_phrase(a)
#         while new_phrases:
#           new_phrases_copy=copy.deepcopy(new_phrases)
#           new_phrases=[]
#           for ph0 in new_phrases_copy:
#             projected_phrases=self.project_phrase(ph0)
#             #if self.debug: print("non-terminal projection", len(projected_phrases),ph0)
#             new_phrases.extend(projected_phrases)
#           for a in new_phrases: self.add_phrase(a)

#     full_sent_span=(0,len(tokens)-1)
#     full_span_keys_numbers=self.span_phrase_key_map_dict.get(full_sent_span,[])
#     full_span_keys=[self.phrase_key_list[key_i] for key_i in full_span_keys_numbers]

#     if full_span_keys==[]: #if no full span keys, we just get the top phrase key ordered by weight
#       phrase_key_wt=list(self.main_phrase_wt_dict.items())
#       phrase_key_wt.sort(key=lambda x:-x[-1])
#       full_span_keys.append(phrase_key_wt[0][0])

#     top_phrase_objects=[]
#     for cur_key_tuple in full_span_keys:
#       cur_key_phrases=self.main_phrase_dict[cur_key_tuple]
#       top_phrase_objects.extend(cur_key_phrases)

#     top_phrase_objects.sort(key=lambda x:-x["wt"])
#     final_raw_parses=[]
#     for phrase_obj0 in top_phrase_objects[:self.max_n_phrases]: 
#       dep0,const0=self.export_parse(tokens,phrase_obj0)
#       final_raw_parses.append((phrase_obj0,dep0,const0))
#     return final_raw_parses #sorted_phrase_list

#   def project_phrase(self,cur_phrase_obj):
#     #if self.debug: print("projecting:",cur_phrase_obj)
#     new_phrases=[]
#     new_phrases2=[]
#     new_level=cur_phrase_obj.get("level",0)+1

#     ft_str=" ".join(cur_phrase_obj["feat"])
#     cur_phrase_key=(cur_phrase_obj["start"],cur_phrase_obj["end"],cur_phrase_obj["cat"],ft_str)

#     self.projection_counter[cur_phrase_key]=self.projection_counter.get(cur_phrase_key,0)+1

#     if self.projection_counter.get(cur_phrase_key,0)>10: return []

#     cur_phrase_key_i=self.phrase_key_index_dict.get(cur_phrase_key)

#     rules=self.get_rules(cur_phrase_obj)
#     for r_i in rules:
#       rule_obj=self.all_processed_rules[r_i]
#       rule_children=rule_obj["children"]
#       rule_children_reversed=list(reversed(rule_children))
#       last_child=rule_children_reversed[0]
#       match_last=match_rule(cur_phrase_obj,last_child)

#       if not match_last: continue

#       rule_children_corr_phrases=[]
      
#       rule_children_corr_phrase_keys=[]
#       rule_children_corr_phrase_keys.append([cur_phrase_key_i])
#       for child0 in rule_children_reversed[1:]:
#         corr_phrases2=self.scan_phrases2(child0,cur_phrase_start=cur_phrase_obj["start"])
#         if corr_phrases2==[]: break
#         rule_children_corr_phrase_keys.append(corr_phrases2)

#       if len(rule_children_corr_phrase_keys)!=len(rule_children): continue
#       rule_children_corr_phrase_keys=list(reversed(rule_children_corr_phrase_keys))
#       phrase_combinations2 = list(product(*rule_children_corr_phrase_keys))
#       for pc in phrase_combinations2: #combinations of phrase ids
#         parent_phrase_obj={}
#         cur_child_keys=[self.phrase_key_list[vi] for vi in pc]
#         phrase_obj_list=[self.main_phrase_dict[key0][0] for key0 in cur_child_keys] #get the top phrase object corresponding to each key
#         phrase_obj_pairs=list(zip(phrase_obj_list,phrase_obj_list[1:]))
#         skip_combination=False
#         for p0,p1 in phrase_obj_pairs: 
#           distance=p1["start"]-p0["end"]-1
#           if distance<0 or distance>self.max_skip_distance: skip_combination=True
#           if skip_combination: break
#         if skip_combination: continue

#         parent_phrase_obj["wt"]=sum([vw["wt"] for vw in phrase_obj_list])
#         phrase_start0=min([vw["start"] for vw in phrase_obj_list])
#         phrase_end0=max([vw["end"] for vw in phrase_obj_list])

#         parent_phrase_obj["span"]=phrase_end0-phrase_start0+1
#         parent_phrase_obj["start"]=phrase_start0
#         parent_phrase_obj["end"]=phrase_end0

#         parent_phrase_obj["cat"]=rule_obj["parent"]["cat"]
#         parent_phrase_obj["feat"]=rule_obj["parent"]["feat"]
#         rule_head_i=rule_obj["head_i"]
#         parent_phrase_obj["children"]=pc
#         head_phrase_index=pc[rule_head_i]
#         parent_phrase_obj["head_phrase"]=head_phrase_index
#         head_phrase_key=self.phrase_key_list[head_phrase_index]

#         head_phrase_obj=self.main_phrase_dict[head_phrase_key][0]
#         parent_phrase_obj["head_loc"]=head_phrase_obj["head_loc"]

#         parent_phrase_obj["rule_i"]=r_i
#         parent_phrase_obj["level"]=new_level
        
#         new_phrases2.append(parent_phrase_obj)


#     return new_phrases2

#   def add_phrase(self,cur_phrase_obj):
#     phrase_obj_cat,phrase_obj_feat=cur_phrase_obj["cat"],cur_phrase_obj["feat"]
#     phrase_obj_start,phrase_obj_end=cur_phrase_obj["start"],cur_phrase_obj["end"]
#     phrase_obj_wt=cur_phrase_obj["wt"]
#     cur_phrase_span=(phrase_obj_start,phrase_obj_end)
#     cur_children=cur_phrase_obj["children"]

#     phrase_key=(phrase_obj_start,phrase_obj_end,phrase_obj_cat," ".join(phrase_obj_feat))
#     phrase_key_i=self.phrase_key_index_dict.get(phrase_key)

#     found_phrases=self.main_phrase_dict.get(phrase_key,[])
#     found_phrases_children=[v["children"] for v in found_phrases] #exclude 
#     if cur_children in found_phrases_children: return

#     cur_phrase_obj["i"]=phrase_key_i
#     if phrase_key_i==None: #if no key exists, we create a key, and index the 

#       phrase_key_i=len(self.phrase_key_list)
#       cur_phrase_obj["i"]=phrase_key_i
#       self.phrase_key_index_dict[phrase_key]=phrase_key_i #map the phrase key to its number in the phrase key list
#       self.phrase_key_list.append(phrase_key)
#       for ft0 in phrase_obj_feat: #update the list of phrase keys associated with each feature
#         temp_ft_key_indexes=self.ft_phrase_key_map_dict.get(ft0,[])
#         updated_temp_ft_key_indexes=temp_ft_key_indexes+[phrase_key_i]
#         self.ft_phrase_key_map_dict[ft0]=list(set(updated_temp_ft_key_indexes))

#       temp_cat_key_indexes=self.cat_phrase_key_map_dict.get(phrase_obj_cat,[]) #update list of keys corresponding to current phrase category
#       updated_temp_cat_key_indexes=temp_cat_key_indexes+[phrase_key_i]
#       self.cat_phrase_key_map_dict[phrase_obj_cat]=list(set(updated_temp_cat_key_indexes))
#       temp_span_key_indexes=self.span_phrase_key_map_dict.get(cur_phrase_span,[]) #update list of keys corresponding to current phrase span
#       updated_temp_span_key_indexes=temp_span_key_indexes+[phrase_key_i]
#       self.span_phrase_key_map_dict[cur_phrase_span]=list(set(updated_temp_span_key_indexes))

#     #adding the actual phrase to the corresponding key at the main phrase dict
#     found_wt=self.main_phrase_wt_dict.get(phrase_key,0) #update the top weight of the current key
#     if phrase_obj_wt>found_wt: self.main_phrase_wt_dict[phrase_key]=phrase_obj_wt

#     updated_found_phrases=found_phrases+[cur_phrase_obj]
#     updated_found_phrases.sort(key=lambda x:-x["wt"])
#     updated_found_phrases=updated_found_phrases[:self.max_n_phrases] #use only top n phrases for each key
#     self.main_phrase_dict[phrase_key]=updated_found_phrases

#     self.phrase_list.append(cur_phrase_obj)


#   def get_rules(self,cur_phrase_obj):
#     #given a token or phrase with cat/feat pair, identify the rules that apply
#     all_rules=[]
#     phrase_obj_cat,phrase_obj_feat=cur_phrase_obj["cat"],cur_phrase_obj["feat"]
#     cur_cat_rules=self.cat_inv_index.get(phrase_obj_cat,[])
#     all_rules.extend(cur_cat_rules)
#     for s_feat0 in phrase_obj_feat:
#       corr_rules=self.feat_inv_index.get(s_feat0,[])
#       all_rules.extend(corr_rules)
#     return list(set(all_rules))

#   def scan_phrases2(self,rule_child,cur_phrase_start=None):
#     #for any child of a given rule, scan all the phrases that match this child (both cat/feat)
#     phrases_i_list=[]
#     rule_child_info_cat,rule_child_info_feat=rule_child["cat"],rule_child["feat"]

#     negative_feat_corr_indexes=[] #identify the keys of phrases marked with a negative feature (e.g. -DET)
#     positive_feat_corr_indexes=[] #identify the keys of all other features
#     cat_corr_indexes=[] #identify keys corresponding to current category

#     #identify the keys for phrases with positive feature, while the rule specifies that it needs to be negative 
#     for feat0 in rule_child_info_feat:
#       is_negative=False
#       if feat0.startswith("-"): is_negative=True
#       feat0=feat0.strip("-")
#       corr_indexes=self.ft_phrase_key_map_dict.get(feat0,[])
#       if is_negative: negative_feat_corr_indexes.extend(corr_indexes)
#       else: positive_feat_corr_indexes.extend(corr_indexes)
#     #subtract the set of phrases upon which the negative feature applies from the phrases upon which positive features apply
#     combined_key_indexes=list(set(positive_feat_corr_indexes).difference(set(negative_feat_corr_indexes)))
#     if rule_child_info_cat!="X": #if category is specified
#       cat_corr_indexes=self.cat_phrase_key_map_dict.get(rule_child_info_cat,[])
#       if rule_child_info_feat==[]: combined_key_indexes=cat_corr_indexes
#       else: combined_key_indexes=list(set(cat_corr_indexes).intersection(set(combined_key_indexes)))
      
#     #combined_key_indexes is a set of indexes corresponding to phrase keys, based on feature and cat of the current child

#     final_applicable_keys=[]
#     for key_i in combined_key_indexes:
#       cur_key0=self.phrase_key_list[key_i]
#       ph_start,ph_end,ph_cat,ph_feat=cur_key0
#       if cur_phrase_start!=None and ph_end>=cur_phrase_start: continue
#       final_applicable_keys.append(key_i)

#     return final_applicable_keys


#   def get_children(self,phrase_obj):
#     all_phrases=[phrase_obj]
#     children=phrase_obj.get("children",[])
#     new_children=[]
#     while children: #go on a semi-recursive way to identify children and subchildren of current main phrase
#       for ch0 in children:
#         ch_phrase_key=self.phrase_key_list[ch0]
#         child_phrase=self.main_phrase_dict[ch_phrase_key][0]
#         all_phrases.append(child_phrase)
#         sub_children=child_phrase.get("children",())
#         sub_children=list(sub_children)
#         for sc in sub_children:
#           if sc==ch0: continue
#           new_children.append(sc) #print("sc",sc)
#       children=new_children
#       new_children=[]
#     return all_phrases


#   def export_parse(self,words,phrase_obj):
#     cur_phrase=phrase_obj
#     start0,end0=cur_phrase["start"],cur_phrase["end"]
#     phrase_head_loc_dict={cur_phrase["i"]: cur_phrase["head_loc"]} #identify the head location for each phrase obj/key is phrase number/phrase index in the phrase list

#     dep_dict={} #identify which phrase head loc depends on which phrase head loc
#     root_index=cur_phrase["head_loc"] #the root of the current phrase

#     cur_tokens_xpos_dict={}
#     #unsorted_phrases=sorted(final_phrases,key=lambda x:x["i"]) #they should be sorted anyway by their original order of being added to the list
#     parse_phrases=[cur_phrase] #these are the phrases to be used for constituency parsing
#     children=cur_phrase.get("children",[])
#     new_children=[]

#     while children: #go on a semi-recursive way to identify children and subchildren of current main phrase
#       for ch0 in children:
#         ch_phrase_key=self.phrase_key_list[ch0]
#         child_phrase=self.main_phrase_dict[ch_phrase_key][0]
#         phrase_head_loc_dict[ch0]=child_phrase["head_loc"]
#         if child_phrase["span"]==1 and child_phrase["children"]==[]: #identify the matching XPOS for terminal phrases
#           cur_tokens_xpos_dict[child_phrase["start"]]=child_phrase["cat"] 
#         parse_phrases.append(child_phrase) 
#         sub_children=child_phrase.get("children",())
#         sub_children=list(sub_children)
#         for sc in sub_children:
#           if sc==ch0: continue
#           new_children.append(sc) #print("sc",sc)
#       children=new_children
#       new_children=[]

#     for a in parse_phrases:
#       cur_children=a["children"]
#       cur_phrase_head_loc=a["head_loc"]
#       for ch0 in cur_children: #for each child of the current phrase, identify its head_loc
#         ch_head_loc=phrase_head_loc_dict[ch0]
#         if ch_head_loc==cur_phrase_head_loc: continue #skip if the head_loc for current child is the same as of the main phrase
#         dep_dict[ch_head_loc]=cur_phrase_head_loc #update dependency dict between heads of two phrases

#     final_dep_list=[]
#     for i0,w0 in enumerate(words): #create dependency info for each word
#       cur_id0=i0+1

#       #identify head index
#       if i0==root_index: #root word
#         cur_dep="0"
#         head_word="^"
#         offset=0
#       else: 
#         cur_dep=dep_dict.get(i0)
#         if cur_dep==None:  #word without attachment
#           cur_dep="-"
#           head_word=""
#           offset=100 #any random number for no offset
#         else: #any other word
#           head_word=words[cur_dep]
#           offset=i0-cur_dep
#           cur_dep=str(cur_dep+1)
          
#       cur_xpos0=cur_tokens_xpos_dict.get(i0,"-")
#       final_dep_list.append({"id":str(cur_id0),"word": w0,"head":cur_dep,"xpos":cur_xpos0,"head_word":head_word,"offset":offset})
#     return final_dep_list, parse_phrases  

#End of parser definition







#21 December 2025
#convert the output of the parser (list of phrase objects) into dependency and constituency information
# def export_parse(words,main_phrase,final_phrases):

#   cur_phrase=main_phrase
#   start0,end0=cur_phrase["start"],cur_phrase["end"]
#   phrase_head_loc_dict={cur_phrase["i"]: cur_phrase["head_loc"]} #identify the head location for each phrase obj/key is phrase number/phrase index in the phrase list

#   dep_dict={} #identify which phrase head loc depends on which phrase head loc
#   root_index=cur_phrase["head_loc"] #the root of the current phrase

#   cur_tokens_xpos_dict={}
#   unsorted_phrases=sorted(final_phrases,key=lambda x:x["i"]) #they should be sorted anyway by their original order of being added to the list
#   parse_phrases=[cur_phrase] #these are the phrases to be used for constituency parsing
#   children=cur_phrase.get("children",[])
#   new_children=[]

#   while children: #go on a semi-recursive way to identify children and subchildren of current main phrase
#     for ch0 in children:
#       child_phrase=unsorted_phrases[ch0]
#       phrase_head_loc_dict[ch0]=child_phrase["head_loc"]
#       if child_phrase["span"]==1 and child_phrase["children"]==[]: #identify the matching XPOS for terminal phrases
#         cur_tokens_xpos_dict[child_phrase["start"]]=child_phrase["cat"] 
#       parse_phrases.append(child_phrase) 
#       sub_children=child_phrase.get("children",())
#       sub_children=list(sub_children)
#       for sc in sub_children:
#         if sc==ch0: continue
#         new_children.append(sc) #print("sc",sc)
#     children=new_children
#     new_children=[]

#   for a in parse_phrases:
#     cur_children=a["children"]
#     cur_phrase_head_loc=a["head_loc"]
#     for ch0 in cur_children: #for each child of the current phrase, identify its head_loc
#       ch_head_loc=phrase_head_loc_dict[ch0]
#       if ch_head_loc==cur_phrase_head_loc: continue #skip if the head_loc for current child is the same as of the main phrase
#       dep_dict[ch_head_loc]=cur_phrase_head_loc #update dependency dict between heads of two phrases

#   final_dep_list=[]
#   for i0,w0 in enumerate(words): #create dependency info for each word
#     cur_id0=i0+1

#     #identify head index
#     if i0==root_index: #root word
#       cur_dep="0"
#       head_word="^"
#       offset=0
#     else: 
#       cur_dep=dep_dict.get(i0)
#       if cur_dep==None:  #word without attachment
#         cur_dep="-"
#         head_word=""
#         offset=100 #any random number for no offset
#       else: #any other word
#         head_word=words[cur_dep]
#         offset=i0-cur_dep
#         cur_dep=str(cur_dep+1)
        
#     cur_xpos0=cur_tokens_xpos_dict.get(i0,"-")
#     final_dep_list.append({"id":str(cur_id0),"word": w0,"head":cur_dep,"xpos":cur_xpos0,"head_word":head_word,"offset":offset})
#   return final_dep_list, parse_phrases  




def match_rule(token_info,rule_child_info):
  #given cat/feat for a phrase/token, match it with the cat/feat for a child in a rule
  token_info_cat,token_info_feat=token_info["cat"],token_info["feat"]
  rule_child_info_cat,rule_child_info_feat=rule_child_info["cat"],rule_child_info["feat"]
  if rule_child_info_cat!="X" and rule_child_info_cat!=token_info_cat: return False
  feat_intersection=list(set(token_info_feat).intersection(set(rule_child_info_feat)))
  #print(feat_intersection)
  if len(feat_intersection)!=len(rule_child_info_feat): return False
  return True


def process_rule(rule_str):
  #process the string of the rule to turn it into parent and children, with objects/dict of each
  final_rule_dict={}
  rule_str=rule_str.replace("→","-->")
  rule_split=rule_str.split("-->")
  if len(rule_split)!=2: return None
  lhs,rhs=rule_split
  lhs,rhs=lhs.strip(),rhs.strip()
  lhs_cat0=lhs.split("[")[0]
  lhs_features=re.findall(r'\[(.+?)\]',lhs)
  cur_rhs_features=[]
  for ft0 in lhs_features:
    cur_rhs_features.extend(ft0.split())
  lhs_dict={"cat":lhs_cat0,"feat":cur_rhs_features}
  final_rule_dict["parent"]=lhs_dict
  rule_children=[]
  rhs_items=rhs.split()
  head_i=0 #the location of the head among the children
  for i_0, it0 in enumerate(rhs_items):
    item_dict={}
    is_head=False
    features=re.findall(r'\[(.+?)\]',it0)
    if "^" in it0: is_head=True

    if is_head: head_i=i_0
    it0=it0.replace("^","")
    item_cat0=it0.split("[")[0]
    cur_features=[]
    for ft0 in features:
      cur_features.extend(ft0.split())

    item_dict={"cat":item_cat0,"is_head":is_head,"feat":cur_features}
    rule_children.append(item_dict)
  final_rule_dict["children"]=rule_children
  final_rule_dict["head_i"]=head_i
  return final_rule_dict


#=================== Extracting features ============
#14 Dec 2025
params0={"len":True,"caps":True,"n_chars":4,"norm_digit":True,"check_hyphen":True,"check_dot":True, "max_len":15}

#word feature extraction class
class wd_ft:
  def __init__(self,params={}) -> None:
    self.params=params
    self.all_feature_slots=[]
    if self.params.get("len",True): 
      max_len0=self.params.get("max_len",20)
      for len0 in range(1,max_len0+1): self.all_feature_slots.append(f"len:{len0}")
    if self.params.get("caps",True):
      self.all_feature_slots.append(f"caps_0")
      self.all_feature_slots.append(f"caps_all")
    if self.params.get("check_hyphen",True): self.all_feature_slots.append("hyphen")
    if self.params.get("dot",True): self.all_feature_slots.append("dot")
    all_alpha_chars=string.ascii_lowercase
    if params.get("norm_digit",True): all_alpha_chars+="5"
    else: all_alpha_chars+=string.digits

    n_pre_suf_chars=self.params.get("n_chars",4)
    for char_i in range(n_pre_suf_chars):
      rev_i=-char_i-1
      if char_i==0: #apply to only first/last char
        for punc0 in string.punctuation:
          self.all_feature_slots.append(f"{punc0}|{char_i}")
          self.all_feature_slots.append(f"{punc0}|{rev_i}")
      else: #empty chars - shorter words
        self.all_feature_slots.append(f"|{char_i}")
        self.all_feature_slots.append(f"|{rev_i}")
      for char0 in all_alpha_chars: 
        self.all_feature_slots.append(f"{char0}|{char_i}")
        self.all_feature_slots.append(f"{char0}|{rev_i}")
      

    self.feature_idx_dict=dict(iter([(v,i) for i,v in enumerate(self.all_feature_slots)]))
    
    self.n_features=len(self.all_feature_slots)

  def extract(self,word):
    all_features=[]
    if self.params.get("len",True): 
      len_word=min(len(word),self.params.get("max_len",20))
      all_features.append(f"len:{len_word}")
    if self.params.get("caps",True):
      if word[0].isupper(): all_features.append(f"caps_0")
      if word.isupper(): all_features.append(f"caps_all")
    word=word.lower()
    if len(word)>3:
      if self.params.get("check_hyphen",True) and len(word.split("-"))>1: all_features.append("hyphen")
      if self.params.get("check_dot",True) and len(word.split("."))>1: all_features.append("dot")
    if self.params.get("norm_digit",True): word=re.sub(r"\d",r"5",word) 
    n_pre_suf_chars=self.params.get("n_chars",4)
    for char_i in range(n_pre_suf_chars):
      rev_i=-char_i-1
      if char_i>len(word)-1: cur_char,cur_rev_char="",""
      else:
        cur_char=word[char_i]
        cur_rev_char=word[rev_i]
      all_features.append(f"{cur_char}|{char_i}")
      all_features.append(f"{cur_rev_char}|{rev_i}")
    return all_features


  def to_vec(self,word,to_tensor=False):
    features=self.extract(word)
    #ft_vector_list=[0.]*self.n_features #len(self.all_feature_slots)
    
    #ft_vector = np.zeros(self.n_features)

    #ft_tensor0 = torch.zeros(self.n_features)
    ft_vector=[0.]*self.n_features
    #indexes=[]
    for ft0 in features:
      idx0=self.feature_idx_dict.get(ft0)
      if idx0!=None: 
        #indexes.append((ft0,idx0))
        #ft_vector_list[idx0]=1.
        #ft_tensor0[idx0]=1.
        ft_vector[idx0]=1.
    #return indexes
    #return ft_vector #ft_tensor0 #torch.tensor(ft_vector_list) #ft_vector_list
    if to_tensor: ft_vector=torch.tensor(ft_vector,dtype=torch.float32) 
    return ft_vector #torch.tensor(ft_vector,dtype=torch.float32) 
    #return torch.tensor(ft_vector,dtype=torch.float64) 

#19 December 2025
def words2ft_tensor(words,ft_obj):
  input_ft_tensor=[]
  for word0 in words:
    ft_vec0=ft_obj.to_vec(word0)
    input_ft_tensor.append(ft_vec0)
  final_ft_tensor=torch.tensor(input_ft_tensor)
  return final_ft_tensor


#============== POS Tagger ================
#20 December 2025

#given the RNN model for POS tagger, initiate and run the tagging for any given sequence of words
class POS:
  def __init__(self,rnn_model_path,params={}) -> None:
    self.params=params
    self.no_model=False
    if rnn_model_path==None or not os.path.exists(rnn_model_path): 
      self.no_model=True
      return
    self.loaded_model_dict=torch.load(rnn_model_path) #first we load the RNN POS model
    self.featex_params=self.loaded_model_dict["featex_params"]
    self.training_params=self.loaded_model_dict["training_params"]
    self.label_params=self.loaded_model_dict["label_params"]
    self.state_dict=self.loaded_model_dict.get("state_dict")
    if self.state_dict==None: self.state_dict=self.loaded_model_dict.get("state_dict_best_loss")

    self.wd_ft_obj=wd_ft(self.featex_params) #loaded from word features class from parsing lib
    self.label_proc_obj=rnn_utils.label_proc(self.label_params) #loaded from label processing class from RNN lib
    #last two true params are sigmoid & matching input output size
    self.rnn=rnn_utils.RNN(self.training_params["n_input"],self.training_params["n_hidden"],self.training_params["n_output"],self.training_params["n_layers"],True,True)
    self.rnn.load_state_dict(self.state_dict)
    self.rnn.eval()

  def tag_words(self,words,min_wt=None):
    if self.no_model: return [{"word":w0} for w0 in words]
    input_tensor=words2ft_tensor(words,self.wd_ft_obj)
    out1=self.rnn(input_tensor)
    final_pos_obj_list=[]
    for o1,w1 in zip(out1,words):
      label_out=self.label_proc_obj.decode(o1)
      cur_obj_list={"word":w1}
      for a,b in label_out.items(): 
        tag_wt_list=b
        if min_wt!=None: tag_wt_list=[(tg0,wt0) for tg0,wt0 in tag_wt_list if wt0>min_wt]
        cur_obj_list[a]=tag_wt_list
      final_pos_obj_list.append(cur_obj_list)
    return final_pos_obj_list  

#============== spaCy Utils ===============

nlp = spacy.load("en_core_web_sm")
#http://spyysalo.github.io/conllu.js/
#https://github.com/explosion/spaCy/issues/533 #spacy to output conll format
nlp.tokenizer = Tokenizer(nlp.vocab, token_match=re.compile(r'\S+').match)

#21 December 2025
def spacy_parse(tokens):
  tokens=[v.strip("_") for v in tokens]
  joined_sent=" ".join(tokens)
  doc = nlp(joined_sent)
  conll_lines=[]
  for token in doc:   
      token_i = token.i+1
      if token.i==token.head.i: head_i=0
      else: head_i = token.head.i+1
      items=[token_i,token.text, token.lemma_, token.tag_, token.pos_, "_", head_i, token.dep_,"_","_"]
      line0="\t".join([str(v) for v in items])
      conll_lines.append(line0)
  return "\n".join(conll_lines)


def tok_sent_join(sent_text): #tokenize with our function, and then join with whitespace for spacy tokenization
    tokenized_sent=general.tok(sent_text)
    tokenized_sent=[v.strip("_") for v in tokenized_sent]
    return " ".join(tokenized_sent)

def get_conll(sent_input): #Use spaCy to get CoNLL format outpus of an input sentence
    new_sent_input=tok_sent_join(sent_input) #
    doc = nlp(new_sent_input)
    conll_2d=[]
    for token in doc:   
        token_i = token.i+1
        if token.i==token.head.i: head_i=0
        else: head_i = token.head.i+1
        items=[token_i,token.text, token.lemma_, token.tag_, token.pos_, "_", head_i, token.dep_,"_","_"]
        conll_2d.append(items)
    return conll_2d

def get_pos_tags(sent_input):
    new_sent_input=tok_sent_join(sent_input) #
    doc = nlp(new_sent_input)
    tmp_pos_tags=[]
    for token in doc: tmp_pos_tags.append(token.tag_)
    return tmp_pos_tags


def get_lemmas(sent_input):
    new_sent_input=tok_sent_join(sent_input) #
    doc = nlp(new_sent_input)
    tmp_lemmas=[]
    for token in doc: tmp_lemmas.append(token.lemma_)
    return tmp_lemmas




#================= PTB utils ===================



#Penn TreeBank PTB code from dissertation work
def strip_num(txt): #to strip trailing numbers and underscores
    return txt.strip("0123456789_")


class ptb:
    def __init__(self,ptb_tree_str):
        all_labels=[]
        ptb_tree_str=ptb_tree_str.replace("\n"," ") #we remove line breaks 
        open_labels=re.finditer(r"(\(\S+)",ptb_tree_str) #get the open tags with non-space items
        open_labels2=re.finditer(r"(\(\s+)",ptb_tree_str) #get open brackets followed by space
        for op in open_labels: #for each of the open and closed labels found, we use finditer to get its exact start and end points within the tring
            all_labels.append((op.group(), op.start(),op.end())) 
        for op in open_labels2:
            all_labels.append((op.group(), op.start(),op.end())) 

        closed_labels=re.finditer(r"\)",ptb_tree_str) #get closing brackets
        for cl in closed_labels:
            all_labels.append((cl.group(), cl.start(),cl.end()))

        all_labels.sort(key=lambda x:x[1]) #we sort both the opening and closing tags/brackets by their start index in the tree string (which tags come first)

        open_tags=[] #this is to control the opening and closing of tags, signaled by brackets
        self.all_tag_ids=[]
        self.children_dict={} #showing which nodes dominates which
        tag_count_dict={} #to count the occurance of each tag type, and use it to give each node a unique ID
        self.tag_info_dict={} #to keep track of the start and end indexes within the tree string
        full_span_dict={} #to show the entire string covered by a certain node
        self.terminal_dict={} #to show if this is a terminal node or not
        #phrase_dict={} #NOT needed - to show the phrase tring covered by this node
        self.flat_dict={} #to show the terminal tokens with their token indexes
        self.vertical_dict={} #to show the open tags corresponding to each node, up to the root of the tree
        self.all_terminals=[] #to collect all the terminal tokens
        terminal_counter=0
        for al in all_labels:
            tag_str,tag_start,tag_end=al
            #print al
            prev_tag="" #initialize the previous tag
            if open_tags: prev_tag=open_tags[-1] #if we already have open tags, then our previous tag is the last of these
            if al[0][0]=="(": #if it is an open tag
                tag_name=tag_str[1:] 
                tag_count=tag_count_dict.get(tag_name,0)
                tag_id="%s_%s"%(tag_name,tag_count) #creating a unique node ID from the tag name and tag count
                self.all_tag_ids.append(tag_id)
                tag_count_dict[tag_name]=tag_count+1
                open_tags.append(tag_id) #add the current open tag to the list of open tags
                self.children_dict[prev_tag]=self.children_dict.get(prev_tag,[])+[tag_id] #add the current node to the children dict
                self.tag_info_dict[tag_id]=(tag_start,tag_end) #keep track of the start and end indexes of the current tag/node
            else: #if it is a closing tag/bracket
                prev_start,prev_end=prev_tag_info=self.tag_info_dict[prev_tag] #we identify the start and end indexes of the last open tag
                cur_span=ptb_tree_str[prev_end:tag_start] #then we identify the current span
                full_span_dict[prev_tag]=(prev_start,tag_end) #maybe not needed, just showing the full string span under the currently open node (prev_tag)
                open_tags=open_tags[:-1] #IMPORTANT - this is how we remove the last open tag from the list of open tags once we encounter a closing tag
                #test_span=re.sub("\)+",")",cur_span) #maybe not needed
                #span_items=re.findall("(\S+)\)",test_span) #maybe not needed
                #phrase_dict[prev_tag]=" ".join(span_items) #maybe not needed
                if "(" in cur_span or ")" in cur_span: continue #the following code will be excuted only if it is a terminal node
                cur_terminal=(cur_span.strip(),terminal_counter) #we need to keep both the terminal token and its index
                self.all_terminals.append(cur_terminal) #and add it to the list of terminal tokens
                for opt in open_tags: self.flat_dict[opt]=self.flat_dict.get(opt,[])+[cur_terminal] #and add it to all of the open tags (nodes dominating it)
                self.flat_dict[prev_tag]=self.flat_dict.get(prev_tag,[])+[cur_terminal] #not to forget the previous open tag which we just removed from the list of open tags
                self.vertical_dict[cur_terminal]=open_tags+[prev_tag] #and here for each terminal token with its index, we show all the nodes all the way up to the root of the tree
                self.terminal_dict[prev_tag]=cur_terminal #and here it tells us if the current open tag is a terminal node or not
                #phrase_dict[prev_tag]=cur_span.strip() #maybe not needed
                terminal_counter+=1 #to keep track of the token indexes
                self.children_dict[prev_tag]=self.children_dict.get(prev_tag,[])+[cur_terminal] #to include the terminal token in the children of terminal nodes
    def get_phrases(self):
        self.phrase_list=[]
        for fd in self.flat_dict:
            tag_name=fd.split("_")[0]
            cur_words_indexes=self.flat_dict[fd]
            cur_words=[v[0] for v in cur_words_indexes]
            cur_words_str=" ".join(cur_words)
            first,last=cur_words_indexes[0][1],cur_words_indexes[-1][1]
            self.phrase_list.append((tag_name,cur_words_str,first,last,len(self.all_terminals)))
        self.phrase_list=list(set(self.phrase_list))
        return self.phrase_list  
    def get_non_terminals(self,ignore_tags=["s1","top","root",""]):
        self.non_terminal_phrase_list=[]
        for fd in self.flat_dict:
            if self.terminal_dict.get(fd)!=None: continue
            tag_name=fd.split("_")[0]
            if tag_name.lower() in ignore_tags: continue
            cur_words_indexes=self.flat_dict[fd]
            cur_words=[v[0] for v in cur_words_indexes]
            cur_words_str=" ".join(cur_words)
            first,last=cur_words_indexes[0][1],cur_words_indexes[-1][1]
            self.non_terminal_phrase_list.append((tag_name,cur_words_str,first,last,len(self.all_terminals)))
        self.non_terminal_phrase_list=list(set(self.non_terminal_phrase_list))
        return self.non_terminal_phrase_list


class tree_diff:
    def __init__(self,ptb_gold_tree_str,ptb_guessed_tree_str,ignore_tags=["s1","top","root",""]): #indicate which spurious tags to ignore in our tree difference analysis
        gold_tree_obj=ptb(ptb_gold_tree_str)
        guessed_tree_obj=ptb(ptb_guessed_tree_str)
        self.gold_tree_nt_phrases=[v for v in gold_tree_obj.get_non_terminals() if not v[0].lower() in ignore_tags]
        self.guessed_tree_nt_phrases=[v for v in guessed_tree_obj.get_non_terminals() if not v[0].lower() in ignore_tags]
        self.common_phrases=[v for v in self.guessed_tree_nt_phrases if v in self.gold_tree_nt_phrases]
        self.missed_phrases=[v for v in self.gold_tree_nt_phrases if not v in self.guessed_tree_nt_phrases]
        self.wrong_phrases=[v for v in self.guessed_tree_nt_phrases if not v in self.gold_tree_nt_phrases]
        self.precision=0
        if len(self.guessed_tree_nt_phrases)!=0: self.precision=float(len(self.common_phrases))/len(self.guessed_tree_nt_phrases)
        self.recall=0
        if len(self.gold_tree_nt_phrases)!=0: self.recall=float(len(self.common_phrases))/len(self.gold_tree_nt_phrases)
        self.f1=0
        if self.precision+self.recall!=0: self.f1=float(2)*(self.precision*self.recall)/(self.precision+self.recall)
        #if len(self.common_phrases)==0 or len(self.guessed_tree_nt_phrases)==0 or len(self.gold_tree_nt_phrases)==0: return


        #self.precision=float(len(self.common_phrases))/len(self.guessed_tree_nt_phrases)
        #self.recall=float(len(self.common_phrases))/len(self.gold_tree_nt_phrases)
        #self.f1=2*(self.precision*self.recall)/(self.precision+self.recall)

        

class tree_diff_phrase_list: #a faster way to compare two trees if you already have the non-terminal phrase list of each
    def __init__(self,gold_tree_nt_phrases,guessed_tree_nt_phrases,ignore_tags=["s1","top","root",""]): #indicate which spurious tags to ignore in our tree difference analysis
        #gold_tree_obj=ptb(ptb_gold_tree_str)
        #guessed_tree_obj=ptb(ptb_guessed_tree_str)
        #self.gold_tree_nt_phrases=[v for v in gold_tree_obj.get_non_terminals() if not v[0].lower() in ignore_tags]
        #self.guessed_tree_nt_phrases=[v for v in guessed_tree_obj.get_non_terminals() if not v[0].lower() in ignore_tags]
        self.common_phrases=[v for v in guessed_tree_nt_phrases if v in gold_tree_nt_phrases]
        self.missed_phrases=[v for v in gold_tree_nt_phrases if not v in guessed_tree_nt_phrases]
        self.wrong_phrases=[v for v in guessed_tree_nt_phrases if not v in gold_tree_nt_phrases]
        self.precision=0
        if len(guessed_tree_nt_phrases)!=0: self.precision=float(len(self.common_phrases))/len(guessed_tree_nt_phrases)
        self.recall=0
        if len(gold_tree_nt_phrases)!=0: self.recall=float(len(self.common_phrases))/len(gold_tree_nt_phrases)
        self.f1=0
        if self.precision+self.recall!=0: self.f1=float(2)*(self.precision*self.recall)/(self.precision+self.recall)
        #if len(self.common_phrases)==0 or len(self.guessed_tree_nt_phrases)==0 or len(self.gold_tree_nt_phrases)==0: return

def extract_rules_tree_str(tree_str,start_end=False,ignore_tags=["s1","top","root",""]):
    ptb_obj=ptb(tree_str)
    return extract_rules(ptb_obj,start_end,ignore_tags)

def extract_rules(ptb_obj,start_end=False,ignore_tags=["s1","top","root",""]):
    #ptb_obj=ptb(tree_str)
    ch_dict,terminal_dict=ptb_obj.children_dict, ptb_obj.terminal_dict
    flat_dict=ptb_obj.flat_dict
    terminals=[v[0] for v in ptb_obj.all_terminals]
    #print (terminals)
    terminal_rules,non_terminal_rules=[],[]
    for ch in ch_dict:
        terminal_check=terminal_dict.get(ch)
        ch_stripped=strip_num(ch)
        if ch_stripped.lower() in ignore_tags: continue
        if terminal_check:
            cur_word=ch_dict[ch][0][0]
            terminal_rules.append((ch_stripped, cur_word))
        else: 
            if start_end: cur_nt_children=[(strip_num(v),ptb_obj.flat_dict[v]) for v in ch_dict[ch]]
            else: cur_nt_children=[strip_num(v) for v in ch_dict[ch]]
            non_terminal_rules.append((ch_stripped, cur_nt_children))
    return terminal_rules, non_terminal_rules



##====================== OLD Parsing framework =====================



#https://github.com/hmghaly/word_align/edit/master/parsing_lib.py

def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

def walk_dict(d,depth=0):
    for k,v in sorted(d.items(),key=lambda x: x[0]):
        if isinstance(v, dict):
            print ("  ")*depth + ("%s" % k)
            walk_dict(v,depth+1)
        else:
            print ("  ")*depth + "%s %s" % (k, v)         


def add2trie(cur_trie,items,val,terminal_item=""):
    new_trie=cur_trie
    for it in items:
        new_trie = new_trie.setdefault(it, {})
    new_trie[terminal_item]=val
    return cur_trie

#TO BE UPDATED WITH MORE RULES
# rules=[
#        "IN NP > PP",
#        "NP PP > NP",
#        "NP CONJ NP > NP",
#        "VP CONJ VP > VP",
#        "PP CONJ PP > PP",
#        "DT NN > NP",
#        "PRP$ NN > NP",
#        "JJ NN > NN",
#        "JJ JJ > JJ",
#        "NN NN > NN",
#        "AUX V > V",
#        "NP S/NP > NP",
#        "RB JJ > JJ"
# ]
# uni_rules=[("PRON","NP"),
#            ("NN","NP"),
#            ("JJ","ADJ"),
#            ("be","V")
#            ]
# cur_trie=defaultdict(lambda: defaultdict(dict))
# for rl in rules:
#   items_str,val=rl.split(">")
#   items_str,val=items_str.strip(),val.strip()
#   items=[v for v in items_str.split(" ") if v]
#   items_reveresed=reversed(items)
#   #print(items,val)
#   cur_trie=add2trie(cur_trie,items_reveresed,val)

def look_back(phrase_span0,all_phrase_spans0,rule_trie0,child_dict0,sequence0=[],depth=0):
  label,i0,i1=phrase_span0
  prev_phrase_spans=[v for v in all_phrase_spans0 if v[-1]+1==i0] #get all previous spans whose span end is right before the current span beginning << we can adjust this to skip
  tmp_rule_trie=rule_trie0.get(label,{})
  tmp_sequence=  sequence0+[phrase_span0]
  tmp_rule_trie=rule_trie0
  for seq in tmp_sequence:
    tmp_rule_trie=tmp_rule_trie.get(seq[0],{})
  for a,b in uni_rules: #apply uni rules first to avoid infinite loops
    if label==a:
      new_phrase_span=(b,i0,i1)
      if new_phrase_span in all_phrase_spans0: continue
      found_children=child_dict0.get(new_phrase_span,[])
      if not new_phrase_span in found_children: child_dict0[new_phrase_span]=found_children+[[phrase_span0]]
      all_phrase_spans0.append(new_phrase_span)
      child_dict0,all_phrase_spans0=look_back(new_phrase_span,all_phrase_spans0,rule_trie0,child_dict0,[],depth+1)
      #Now do recursion on the new phrase span
  for key, val in tmp_rule_trie.items():
    #print("key:",key,"val:",val)
    converged_label=val.get("") #check if there can be a label that the current sequence converges to
    # print(">>> converged_label",converged_label)
    for prev in prev_phrase_spans:
      if not prev[0]==key: continue
      if converged_label!=None:
        new_sequence=tmp_sequence+[prev]
        new_phrase_start=min([v[1] for v in new_sequence])
        new_phrase_end=max([v[2] for v in new_sequence])
        #new_phrase_span=(converged_label,prev[1],phrase_span0[2])
        new_phrase_span=(converged_label,new_phrase_start,new_phrase_end)
        found_children=child_dict0.get(new_phrase_span,[])

        if not new_phrase_span in found_children: child_dict0[new_phrase_span]=found_children+[new_sequence]
        if new_phrase_span in all_phrase_spans0: continue
        all_phrase_spans0.append(new_phrase_span)
        child_dict0,all_phrase_spans0=look_back(new_phrase_span,all_phrase_spans0,rule_trie0,child_dict0,[],depth+1)
        #print("prev >>>>", prev, "current >>>",phrase_span0, " - Converge to:",new_phrase_span)
      else:
        child_dict0,all_phrase_spans0=look_back(prev,all_phrase_spans0,rule_trie0,child_dict0,tmp_sequence,depth+1)
        pass

  return child_dict0, all_phrase_spans0

def get_children_recursive(node0,child_dict0,parent_node=(),all_nodes=[],depth=0):
  tmp_nodes=all_nodes+[(node0,parent_node,depth)]
  for ch0 in child_dict0.get(node0,[[]])[0]:
    tmp_nodes=get_children_recursive(ch0,child_dict0,node0,tmp_nodes,depth+1)
  return tmp_nodes


class parse_OLD:
  def __init__(self,sent0,cur_trie0,verb_frame_shelve_path):
    self.cur_trie=cur_trie0
    self.child_dict={}
    conll_out=get_conll(sent0)
    self.all_phrases_spans=[]
    #all_phrase_rules=[]
    tag_word_dict={}
    verb_shelve_open=shelve.open(verb_frame_shelve_path)
    verb_frame_dict={}
    for i_,co in enumerate(conll_out):
      verb_frame_dict[co[2]]=verb_shelve_open.get(co[2],[])  #create a small dictionary for the frames of the word in this sentence
    verb_shelve_open.close()
    for i_,co in enumerate(conll_out):
      word,lemma,tag,pos=co[1],co[2],co[3],co[4]
      if tag.startswith("V"): uni_rules.append((tag,"V")) #expand the UNI rules for any tverb tag to "V" to match the frames in verb frame
      if tag.startswith("JJ") and tag!="JJ": uni_rules.append((tag,"JJ"))
      if tag.startswith("NN") and tag!="NN": uni_rules.append((tag,"NN"))
      
      verb_frames=[]
      if pos in ["VERB","AUX"]: #get the frames of any word if it is a verb 
        frames=verb_frame_dict.get(lemma,[])
        for f in frames: 
          vb_frame=f[0]
          verb_frames.append(vb_frame) #add the verb frames to the trie, with their VP rules, and the slash rules
          vb_frame_items=[v for v in vb_frame.split(" ") if v]
          vb_frame_items=[v.split("-")[0] for v in vb_frame_items]
          vb_frame_items=[v.split(".")[0] for v in vb_frame_items] #just to remove things liks NP.xxx or PP-xxx
          self.cur_trie=add2trie(self.cur_trie,reversed(vb_frame_items),"S")
          np_locs=[i_ for i_, v_ in enumerate(vb_frame_items) if v_=="NP" and i_!=0]
          for np_i in np_locs: #identify NP locations in object/dative positions in frame
            list_copy=list(vb_frame_items)
            list_copy.pop(np_i)
            self.cur_trie=add2trie(self.cur_trie,reversed(list_copy),"S/NP") #create a copy with the slash rule

      for lb in co[1:5]: #we iterate over the word, its stem, its POS and tag
        cur_phrase_span=(lb,i_,i_)
        if cur_phrase_span in self.all_phrases_spans: continue
        self.all_phrases_spans.append(cur_phrase_span) #[(word,i_,i_)]
        tag_word_dict[cur_phrase_span]=(word,i_,i_)
        self.child_dict, self.all_phrases_spans=look_back(cur_phrase_span,self.all_phrases_spans,self.cur_trie,self.child_dict,[]) #now run the recursive look_back function
    self.parse_nodes=[]
    for node,children in self.child_dict.items():
      if node[1]==0 and node[2]==len(conll_out)-1:  #if a node spans the entire sentence
        self.parse_nodes=get_children_recursive(node,self.child_dict,(),[],0)
    self.parse_phrase_list=[]
    max_level=0
    if self.parse_nodes: max_level=max([v[-1] for v in self.parse_nodes])
    self.out_dict={}
    self.out_dict["n_words"]=len(conll_out)
    self.out_dict["n_levels"]=max_level
    for node,parent_node,depth in self.parse_nodes:
      node_str="-".join([str(v) for v in node])
      parent_str="-".join([str(v) for v in parent_node])
      node_i0,node_i1=node[1],node[2]
      cur_depth=max_level-depth
      self.parse_phrase_list.append((node_str,node_i0,node_i1,parent_str,cur_depth))
      corr_word_node=tag_word_dict.get(node)
      if corr_word_node!=None:
        word_node_str= "-".join([str(v) for v in corr_word_node])
        new_depth=cur_depth-1
        self.parse_phrase_list.append((word_node_str,node_i0,node_i1,node_str,new_depth))
    self.out_dict["phrases"]=self.parse_phrase_list
    self.json_out=json.dumps(self.out_dict)


# def get_id(input_tag,counter_dict): #this is a bad function, it takes the global variable tag_count_dict
#     tmp_tag_count=counter_dict.get(input_tag,0) #how many times this tag was used before in the parse
#     tmp_tag_id="%s_%s"%(input_tag,tmp_tag_count) #create tag ID
#     counter_dict[input_tag]=tmp_tag_count+1 #update the tag counter
#     return tmp_tag_id, counter_dict
    

# def check_back(input_trie,input_seq,input_label,input_start_index,depth=0):
#     sub_trie=input_trie.get(input_label,{})
#     keys=sub_trie.keys()
#     #print(">>>>>>>>>>> input sequence", input_seq, "depth", depth,"input_label", input_label,"input_start_index",input_start_index)
#     seq_tags=[v[0] for v in input_seq]
#     seq_start_indexes=[v[1] for v in input_seq]
#     seq_end_indexes=[v[2] for v in input_seq]
#     seq_wt=sum([v[3] for v in input_seq])
#     new_seq_start=seq_start_indexes[0]
#     new_seq_end=seq_end_indexes[-1]
#     for k in keys:
#         if k=="":
#             candidates=sub_trie[k]
#             for can in candidates:
#                 can_tag,can_wt=can
#                 new_wt=can_wt+seq_wt
#                 new_id=get_id(can_tag)
#                 found_wt=wt_dict[new_seq_start][new_seq_end][can_tag]
#                 if new_wt<=found_wt: continue #we'll need to adjust to keep track of all the generated labels
#                 #if depth>0: continue
#                 #if depth>0 and new_seq_start==new_seq_end: continue
#                 children_dict[new_id]=seq_tags
#                 tag_span_wt_dict[new_id]=(new_seq_start,new_seq_end,new_wt) #specify the properties of the current tag: span & weight
#                 label_end_dict[can_tag][new_seq_end].append(new_seq_start)
#                 cur_item=(new_id,new_seq_start,new_seq_end,new_wt)
#                 span_tag_dict[new_seq_start][new_seq_end][can_tag].append(cur_item)
#                 wt_dict[new_seq_start][new_seq_end][can_tag]=new_wt
#                 #check_back(input_trie,[cur_item],can_tag,new_seq_start,depth+1)

            
#         else:
#             found_prev_indexes=label_end_dict.get(k,{})
#             if found_prev_indexes: 
#                 for end_index in found_prev_indexes:
#                     if end_index>=input_start_index: continue
#                     starting_indexes=found_prev_indexes[end_index]
#                     for s0 in starting_indexes:
#                         cur_ids=span_tag_dict[s0][end_index][k]
#                         #print("found previous tags",input_label, input_seq, k,s0, end_index,cur_ids)
#                         check_back(sub_trie[k],cur_ids+input_seq,k,s0,depth+1)
                        
#                 #print('--------')

                    
            
        
#     #print("----")

# def merge(input_seq):
#     pass


# def back(input_label,input_trie,input_end_dict,input_index,seq=[],new_phrases=[],depth=0):
#     sub_trie=input_trie.get(input_label,{})
#     prev_labels=sub_trie.keys()
#     if depth==0: prev_labels=[v for v in prev_labels if v!=""]
#     #else: print prev_labels
#     for pl in prev_labels:
#         if pl=="":
#             final_labels=sub_trie[pl]
#             for fl in final_labels:
#                 #print "depth", depth, "input_index", input_index,  "converging", fl, "sequence", seq
#                 new_phrases.append((fl,seq))
#         else:            
#             prev_indexes=input_end_dict.get(pl)
#             if prev_indexes==None: continue
            
#             for i0,i1 in prev_indexes:
#                 if i1>=input_index: continue
#                 #print "depth", depth, "input_label: ", input_label, "input_index", input_index, "prev_label: " , pl, "prev_indexes: ", i0,i1
#                 cur_ids=input_end_dict[pl][(i0,i1)]
#                 cur_ids.sort(key=lambda x:-x[1])
#                 top_phrase=cur_ids[0]
#                 #print "found >>>", cur_ids
#                 new_phrases=back(pl,sub_trie,input_end_dict,i0,[(top_phrase[0],top_phrase[1],i0,i1)]+seq,new_phrases,depth+1)
#     return new_phrases
        

if __name__=="__main__":
    pass
    print("Hello!")
    sent="the woman I love is pretty"
    shelve_fpath="verbs.shelve"
    parse_obj=parse(sent,cur_trie,shelve_fpath)
    print(parse_obj.json_out)
    # for a in parse_obj.parse_phrase_list:
    #   print(a)

#     rule_dict={}
#     token_dict={}
#     #bw_dict={} #backwards dictionary - identifies the last tag in a rule, its previous tags, and the new tag they form
#     model_name="bnc_1000"
#     rules_fname="%s.rules.txt"%model_name
#     tokens_pos_fname="%s.tokens.pos.txt"%model_name
#     rules_fopen=open(rules_fname)
#     rule_trie = dict()
#     for ri,rf in enumerate(rules_fopen):
#         split=rf.strip("\n\r").split("\t")
#         if len(split)!=2: continue
#         key=tuple(json.loads(split[0]))
#         val=json.loads(split[1])
#         if len(key)==1: val.pop(key[0], None) #to avoid things like NP > NP > NP ... for single label rules
#         reversed_key=reversed(key)
#         current_dict = rule_trie
#         for rk in reversed_key:
#             current_dict = current_dict.setdefault(rk, {})
#         current_dict[""]=[(k0,val[k0]) for k0 in val]
#     rules_fopen.close()
#     #walk_dict(rule_trie)

#     tokens_pos_fopen=open(tokens_pos_fname) #we create a unigram dictionary for the possible tags for each token
#     for ti,tf in enumerate(tokens_pos_fopen):
#         split=tf.strip("\n\r").split("\t")
#         if len(split)!=2: continue
#         token_dict[split[0]]=json.loads(split[1])
#     tokens_pos_fopen.close()

    

#     #end_dict={} #end_dict[index][tag]=[(tag1,start_index_tag1),(tag1,start_index_tag1) ...]
#     tag_count_dict={} #to count the occurances of a certain tag to create tag ID
#     tag_span_wt_dict={} #tag_span_wt_dict[tag_id]=(start,end,wt)
#     children_dict={} #children_dict[parent_tag]=[child_tag1,child_tag2...]
#     #generic_end_dict={} #generic label with its end index, and the corresponding list of beginning indexes, e.g. generic_dict[NP][5]=[5,4]
#     #specific_tag_start_end={} #for a generic tag with a specific start and end indexes, what are the corresponding phrase IDs with their weights specific_tag_start_end[NP][0][2]=[(NP_0,5),(NP_15,2)]
#     span_tag_dict = nested_dict(3, list) #what are the phrase ids and their corresponding weights, that fall within this span with this tag e.g. span_dict[0][5][NP]=[(NP_1,15),(NP_5,20)]
#     label_end_dict = nested_dict(2, list) #for each label, and for each end indexes, what are the corresponding beginning indexes
#     wt_dict = nested_dict(3, int) #the maximum weight reached for a given span and label

#     #span_tag_dict={} #span_tag_dict[(0,1)]=tag_id
#     #span_wt_dict={} #span_wt_dict[(0,1)]=tag_wt
#     #wt_check_dict={} #wt_check_dict[(0,1,NP)]=15
#     #tag_dict = defaultdict(dict)
#     #wt_dict = defaultdict(dict)
#     #new_tag_dict = nested_dict(3, str)


#     sent=["I","will","go","there","at","the","door"]
#     stack=[]
#     for index,word in enumerate(sent):
#         print(index,word)
#         cur_tags=token_dict.get(word.lower(),{}) #we get possible tags for each token
#         #local_dict=nested_dict(1, list)
#         all_new_labels=[]
#         #print(si,s,cur_tags)
#         #print("-----")
#         for terminal_label in cur_tags:
#             #print("terminal_label",terminal_label)
#             cur_start_index,cur_end_index=index,index
#             cur_wt=cur_tags[terminal_label] #the weight of the current tag
#             cur_tag_id,tag_count_dict=get_id(terminal_label,tag_count_dict)
#             all_new_labels.append((terminal_label,cur_wt,cur_start_index,cur_end_index,cur_tag_id,"")) #last one is the child tag
#             cur_sub_trie=rule_trie.get(terminal_label,{})
#             non_terminal_labels=cur_sub_trie.get("",[])
#             for nt_label,nt_wt in non_terminal_labels:
#                 #print "terminal_label",terminal_label, cur_wt, "non_terminal_labels", nt_label, nt_wt
#                 nt_tag_id,tag_count_dict=get_id(nt_label,tag_count_dict)
#                 combined_wt=cur_wt+nt_wt
#                 all_new_labels.append((nt_label,combined_wt,cur_start_index,cur_end_index,nt_tag_id,cur_tag_id))
#                 children_dict[nt_tag_id]=[cur_tag_id]
#                 #print nt_tag_id, combined_wt
#         all_new_labels.sort(key=lambda x:-x[1])
#         used_labels=[]
#         for a in all_new_labels:
#             a_label=a[0]
#             a_wt=a[1]
#             a_id=a[-2]
#             #print a_label
#             if a_label in used_labels: 
#                 #print "excluding >>>", a
#                 continue
#             used_labels.append(a_label)
            
#             final_new_phrases=back(a_label,rule_trie,label_end_dict,index,depth=0)
#             label_end_dict[a_label][(index,index)].append((a_id,a_wt))
#             for fn in final_new_phrases:
#                 print fn
            
# ##            sub_trie=rule_trie.get(a_label,{})
# ##            label_end_dict[a_label][index].append(index)
# ##            prev_labels=sub_trie.keys()
# ##            
# ##                
# ##            print ">>>", a, a_label, index#, prev_labels
# ##            for pl in prev_labels:
# ##                prev_indexes=label_end_dict.get(pl)
# ##                if prev_indexes==None: continue
# ##                
# ##                print pl, prev_indexes
#         print '-------'


# ##    for le in label_end_dict:
# ##        print le, label_end_dict[le]
#     #walk_dict(label_end_dict)
#     #for td in label_end_dict:
#     #    print(td, label_end_dict[td])
#     #    print('------')

#   #for td in generic_end_dict:
#   #    print(td, generic_end_dict[td])
#   #    print('------')
#     #for st in stack:

#     #   print(st, tag_span_wt_dict.get(st), parent_dict.get(st))
#     #for ed in end_dict:
#     #   print(ed, end_dict[ed])
#     #   print('---')
#     #for sp in span_tag_dict:
#     #   print(">>>", sp, span_tag_dict[sp])
#     #   print('---')
        



