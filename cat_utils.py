#!/usr/bin/python3
import os, re, json
import sys
import shutil
import zipfile
import random, string
import hashlib
from itertools import groupby
from difflib import SequenceMatcher
import copy

sys.path.append("code_utils")
import web_lib
import general

ver=sys.version_info
if ver[0]==3: 
  import html
  htmlp=html
if ver[0]==2: 
  import HTMLParser
  #HTMLParser.HTMLParser().unescape('Suzy &amp; John')  

excluded_punc_tokens=["<s>","</s>",".","(",")",",",";","[","]"]
excluded_words=["the","a","an","and","of","in","on","at","to","by","is","are","has","have","had","it","its","with","for"]
all_excluded=excluded_punc_tokens+excluded_words

#functions for extracting features from raw features
def dict2ft_lb(data_dict,wv_model,ft_params={},outcome_key="outcome"): #should be "outcome" in next run
  special_tokens_list=ft_params.get("token_list",[])
  include_src_wv=ft_params.get("include_src_wv",False)
  include_trg_wv=ft_params.get("include_trg_wv",False)
  include_context_wv=ft_params.get("include_context_wv",False)
  include_context_trg_sim=ft_params.get("include_context_trg_sim",False)

  include_include_freq=ft_params.get("include_include_freq",False)
  include_is_in_context=ft_params.get("include_is_in_context",False)

  include_prev_oh=ft_params.get("include_prev_oh",False)
  include_next_oh=ft_params.get("include_next_oh",False)
  include_trg_first_oh=ft_params.get("include_trg_first_oh",False)
  include_trg_last_oh=ft_params.get("include_trg_last_oh",False)


  label_list=[data_dict[outcome_key]]
  feature_list=[]

  main_keys=["src","trg","context"]
  temp_vec_dict={}
  for key0 in main_keys:
    if key0=="src" and include_src_wv==False: continue
    if key0=="trg" and include_trg_wv==False and include_context_trg_sim==False: continue
    if key0=="context" and include_context_wv==False and include_context_trg_sim==False: continue

    val0=data_dict[key0]
    val_tokens=val0.split(" ")
    val_tokens=[v for v in val_tokens if not v.lower().strip("_") in special_tokens_list]
    try: val_vec=wv_model.wv.get_mean_vector(val_tokens)#.tolist()
    except: val_vec=wv_model.wv.get_mean_vector([""])#.tolist()
    temp_vec_dict[key0]=val_vec

    if key0=="trg" and include_trg_wv==False: continue
    if key0=="context" and include_context_wv==False: continue
    feature_list.extend(val_vec.tolist())
  if include_context_trg_sim:
    context_trg_sim0=-1
    if sum(temp_vec_dict["trg"])!=0 and sum(temp_vec_dict["context"])!=0: 
      context_trg_sim0=cos_sim(temp_vec_dict["trg"],temp_vec_dict["context"])
    feature_list.append(context_trg_sim0)
  if include_include_freq: feature_list.append(float(data_dict["freq"]))
  if include_is_in_context: feature_list.append(data_dict["is_in_context"])

  if include_prev_oh:
    prev_oh=is_in_one_hot(data_dict["prev_token"].lower().strip("_"),special_tokens_list)
    feature_list.extend(prev_oh)

  if include_next_oh:
    next_oh=is_in_one_hot(data_dict["next_token"].lower().strip("_"),special_tokens_list)
    feature_list.extend(next_oh)
  trg_split=data_dict["trg"].split(" ")
  if include_trg_first_oh:
    first_trg_word=trg_split[0].strip("_").lower()
    first_trg_oh=is_in_one_hot(first_trg_word,special_tokens_list)
    feature_list.extend(first_trg_oh)

  if include_trg_last_oh:
    last_trg_word=trg_split[-1].strip("_").lower()
    last_trg_oh=is_in_one_hot(last_trg_word,special_tokens_list)
    feature_list.extend(first_trg_oh)

  return feature_list,label_list
  
def is_in_one_hot(item0,list0):
  one_hot0=[0.]*len(list0)
  if item0 in list0:
    index_i=list0.index(item0)
    one_hot0[index_i]=1.
  return one_hot0


def extract_repl_raw_features_labels(src_tokens,trg_tokens,first_repl_dict,window_size=5): #check each possible replacement for context and other features
  #src_tokens0,trg_tokens0=src_tokens,trg_tokens
  #possible_replacements=get_possible_replacements(src_tokens,first_repl_dict)
  final_repl_list=[]
  edit_list=compare_repl(src_tokens,trg_tokens)
  possible_repl_list=get_possible_replacements(src_tokens,first_repl_dict)
  actual_repl_dict={}
  for el in edit_list:
    match_type,repl_src_token0,repl_trg_token0,src_span0,trg_span0=el
    if match_type=="equal": continue
    repl_src0=" ".join(repl_src_token0)
    repl_trg0=" ".join(repl_trg_token0)
    a_key=(repl_src0,src_span0) #actual replacement key
    actual_repl_dict[a_key]=repl_trg0

  p_ft_dict_list=[]
  for repl_src0,trg_repl_dict0,span0 in possible_repl_list:
    #if repl_src0!="UK": continue
    p_key=(repl_src0,span0)
    actual_trg_repl0=actual_repl_dict.get(p_key)
    temp_ft_dict=extract_context_ft(src_tokens,span0,window_size=window_size)
    temp_ft_dict["src"]=repl_src0
    context0=temp_ft_dict.get("context","")
    context_words_lower0=[v.lower() for v in context0.split(" ") if v!="|"]

    # print("repl_src0,trg_repl_dict0,span0",repl_src0,trg_repl_dict0,span0)
    # print(temp_ft_dict)
    # print("actual_trg_repl0",actual_trg_repl0)
    for trg_repl0,freq0 in trg_repl_dict0.items():
      temp_ft_dict1=copy.deepcopy(temp_ft_dict)
      temp_ft_dict1["trg"]=trg_repl0
      temp_ft_dict1["freq"]=freq0
      outcome=0
      is_in_context=0
      if trg_repl0==actual_trg_repl0: outcome=1

      repl_trg_tokens_lower=trg_repl0.lower().split()
      if general.is_in(repl_trg_tokens_lower,context_words_lower0): is_in_context=1
      temp_ft_dict1["outcome"]=outcome
      temp_ft_dict1["is_in_context"]=is_in_context
      #print(temp_ft_dict1)
      final_repl_list.append(temp_ft_dict1)
  return final_repl_list

def extract_context_ft(src_tokens,src_repl_span,window_size=5,input_ft_dict={}):
  #temp_ft_dict={}
  #p_repl_src_tokens0,p_repl_trg_tokens0,freq0=triple0
  # repl_src0=" ".join(repl_src_tokens)
  # repl_trg0=" ".join(repl_trg_tokens)

  prev_token,next_token="",""
  x0,x1=src_repl_span
  #full_window=src_tokens0[max(0,x0-window_size):x1+window_size+1]

  full_window=src_tokens[max(0,x0-window_size):x0]+["|"]+ src_tokens[x1+1:x1+window_size+1]
  if x0>0: prev_token=src_tokens[x0-1]
  if x1<len(src_tokens)-1: next_token=src_tokens[x1+1]

  input_ft_dict["context"]=" ".join(full_window)
  input_ft_dict["prev_token"]=prev_token
  input_ft_dict["next_token"]=next_token
  return input_ft_dict

#==================================



def is_un_symbol(str0):
  out=False
  if str0[0].isupper() and str0[-1].isdigit() and "/" in str0: out=True
  return out



def unescape(text_with_html_entities):
  if sys.version_info[0]==3:
    import html
    return html.unescape(text_with_html_entities)
  else:
    import HTMLParser
    return HTMLParser.HTMLParser().unescape(text_with_html_entities)

#from code_utils.general import *
#from code_utils.extract_docx import *

def simple_hash(input_str,size=10):
  input_str=input_str.encode('utf-8')
  return hashlib.md5(input_str).hexdigest()[:size]

def str2key(str0):
  str0=htmlp.unescape(str0)
  str0=str0.strip()
  str0=re.sub("\W+","_",str0)
  return str0

def tsv2dict(tsv_fpath0,skip_first=False):
  out_dict={}
  fopen0=open(tsv_fpath0)
  for line in fopen0:
    line_split=line.strip("\n\r\t").split("\t")
    if len(line_split)<2: continue
    key=str2key(line_split[0])
    out_dict[key]=line_split[1]
  return out_dict


#2 June 2023
class docx:
  def __init__(self,docx_fpath,keep_copy=True): #openning the docx file, by unzipping it
    self.TEMP_DOCX = docx_fpath
    self.closed=False
    self.COPY_DOCX = docx_fpath+"2"
    shutil.copy(self.TEMP_DOCX, self.COPY_DOCX) #keep a temp copy of out file, just in case
    self.file_extension="."+docx_fpath.split(".")[-1]
    self.TEMP_ZIP = docx_fpath.replace(self.file_extension,".zip")
    self.TEMP_FOLDER = docx_fpath.replace(self.file_extension,"")
    if os.path.exists(self.TEMP_ZIP):
      os.remove(self.TEMP_ZIP)
    if os.path.exists(self.TEMP_FOLDER):
      shutil.rmtree(self.TEMP_FOLDER)
    os.rename(self.TEMP_DOCX, self.TEMP_ZIP) #rename the original docx to zip extension
    # unzip file zip to specific folder
    z_open=zipfile.ZipFile(self.TEMP_ZIP, 'r')
    z_open.extractall(self.TEMP_FOLDER)
    z_open.close()
    os.rename(self.COPY_DOCX, self.TEMP_DOCX) #keep the original file
  def save_as(self,out_fpath):
    if os.path.exists(out_fpath): #remove any of these if already exists
      os.remove(out_fpath)
    #self.OUT_ZIP = out_fpath.replace(".docx",".zip")
    #shutil.make_archive(self.OUT_ZIP, 'zip', self.TEMP_FOLDER)
    shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
    os.rename(self.TEMP_ZIP, out_fpath)
  def extract_paras(self,cat_file_path=""): 
    self.paras=[]
    self.para_path_dict={}
    if self.TEMP_DOCX.lower().endswith(".docx"): main_dir="word"
    if self.TEMP_DOCX.lower().endswith(".pptx"): main_dir="ppt/slides"
    if self.TEMP_DOCX.lower().endswith(".xlsx"): main_dir="xl"

    extracted_dir=os.path.join(self.TEMP_FOLDER, main_dir)
    for xml_fname in os.listdir(extracted_dir):
      #print(xml_fname)
      skip_file=True
      if xml_fname in ["document.xml", "footnotes.xml","endnotes.xml","sharedStrings.xml"]: skip_file=False
      if xml_fname.startswith("slide"): skip_file=False
      if xml_fname.startswith("sheet"): skip_file=False
      if xml_fname.startswith("header"): skip_file=False
      if xml_fname.startswith("footer"): skip_file=False
      if skip_file: continue
      # if xml_fname in ["document.xml", "footnotes.xml","endnotes.xml"] or xml_fname.startswith("header") or xml_fname.startswith("footer"): pass
      # else: continue
      #if not xml_fname=="document.xml" and not xml_fname.startswith("header") and not xml_fname.startswith("footer"): continue
      cur_xml_path=os.path.join(extracted_dir,xml_fname)
      with open(cur_xml_path) as fopen:
        xml_content=fopen.read()
      xml_dom_obj=web_lib.DOM(xml_content)
      cur_tag_name="w:p" #xml tag for docx files
      if self.TEMP_DOCX.lower().endswith(".pptx"): cur_tag_name="a:p"
      
      cur_paras=xml_dom_obj.get_el_by_tag_name(cur_tag_name)
      tmp_xml_path=os.path.join(main_dir,xml_fname)
      for para0 in cur_paras:
        para_hash=simple_hash(para0)
        cur_para_key="%s|%s"%(tmp_xml_path,para_hash)
        self.paras.append((cur_para_key,para0))
        self.para_path_dict[cur_para_key]=para0
      
      # cur_wps=get_xml_elements(xml_content,el_name=cur_tag_name)
      # for i0,wp_xml in enumerate(cur_wps):
      #   #wp_text=get_wr_text(wp_xml)
      #   wp_text=get_el_text(wp_xml)        
      #   para_obj=para()
      #   para_obj.path=cur_xml_path
      #   para_obj.xml=wp_xml
      #   para_obj.text=wp_text
      #   para_obj.i=i0
      #   para_obj.tag_name=cur_tag_name        
      #   found_ids=re.findall('paraId="(.+?)"',wp_xml) 
      #   if found_ids: para_obj.id=  found_ids[0]
      #   self.paras.append(para_obj)
      # if cat_file_path!="": #save paragraphs with their info to cat file
      #   cat_fopen=open(cat_file_path,"w")
      #   for p_obj in self.paras:
      #     cur_text=p_obj.text.replace("\t"," <tab> ").replace("\n"," <br> ")
      #     json_obj={}
      #     json_obj["path"]=p_obj.path
      #     json_obj["i"]=p_obj.i
      #     json_obj["id"]=p_obj.id
      #     json_obj["tag_name"]=p_obj.tag_name          
      #     json_obj["text"]=cur_text
      #     json_obj_str=json.dumps(json_obj) 
      #     line=json_obj_str+"\n"
      #     #line="%s\t%s\t%s\t%s\n"%(p_obj.path,p_obj.i,p_obj.id,cur_text)
      #     cat_fopen.write(line)
      #   cat_fopen.close()

    return self.paras,self.para_path_dict
  

  def update_tbl_rtl(self):
    extracted_dir=os.path.join(self.TEMP_FOLDER, "word")
    cur_xml_path=os.path.join(extracted_dir,"document.xml")
    fopen_read=open(cur_xml_path)
    xml_content=fopen_read.read()
    fopen_read.close()
    xml_content=xml_content.replace("<w:tblPr>","<w:tblPr><w:bidiVisual/>")
    xml_content=xml_content.replace("<w:lang ","<w:rtl/><w:lang ")

    
    fopen_write=open(cur_xml_path, "wb")
    fopen_write.write(xml_content)
    fopen_write.close()


  def close(self):
    self.closed=True
    os.remove(self.TEMP_ZIP)
    shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
    os.rename(self.TEMP_ZIP, self.TEMP_DOCX)
    shutil.rmtree(self.TEMP_FOLDER)

#Editing project
#2 June 2023
def get_edit_info(para_content):
  para_content=para_content.replace("<w:br/>","\n")
  para_content=para_content.replace("<w:tab/>","\t")
  para_content=para_content.replace("<w:noBreakHyphen/>","-")
  #<w:footnoteReference w:customMarkFollows="1" w:id="2"/>
  #<w:footnoteReference w:id="3"/>
  

  tags=list(re.finditer('<[^<>]*?>|\<\!\-\-.+?\-\-\>', para_content))
  open_tags=[""]
  tag_counter_dict={}
  start_i=0
  last_open_tag_str=""
  is_inserted=False
  is_deleted=False
  original_text0,final_text0="",""
  edit_segments0=[]
  for ti_, t in enumerate(tags):
    tag_str,tag_start,tag_end=t.group(0), t.start(), t.end()
    tag_str_lower=tag_str.lower()
    tag_name=re.findall(r'</?(.+?)[\s>]',tag_str_lower)[0]
    tag_type=""
    if tag_str.startswith('</'): tag_type="closing"
    elif tag_str.startswith('<!'): tag_type="comment"
    elif tag_str_lower.endswith('/>') or tag_name in ["input","link","meta","img","br","hr"]: tag_type="s" #standalone
    #elif tag_name in ["wp:posOffset"]: tag_type="exclude"
    else: tag_type="opening"

    #if tag_type=="exclude": continue

    if tag_name=="w:ins" and tag_type=="opening": is_inserted=True
    if tag_name=="w:ins" and tag_type=="closing": is_inserted=False
    if tag_name=="w:del" and tag_type=="opening": is_deleted=True
    if tag_name=="w:del" and tag_type=="closing": is_deleted=False

    inter_text=para_content[start_i:tag_start] #intervening text since last tag
    #if inter_text!="": print("inter_text",[inter_text],"last_open_tag_str",last_open_tag_str)
    #print(tag_name, inter_text,"is_inserted",is_inserted,"is_deleted",is_deleted)
    if last_open_tag_str.startswith("w:"):
      if not is_inserted: original_text0+=inter_text
      if not is_deleted: final_text0+=inter_text
      seg_class="edited_same"
      if is_inserted: seg_class="edited_inserted"
      if is_deleted: seg_class="edited_deleted"
      if inter_text!="":edit_segments0.append((inter_text,seg_class))
    start_i=tag_end
    if tag_type=="opening": last_open_tag_str=tag_name
  #edit_segments_grouped=edit_segments0[(key,"".join([v[0] for v in list(group)])) for key,group in groupby(edit_segments0,lambda x,x[0])]
  edit_segments_grouped0=[(key,"".join([v[0] for v in list(group)])) for key,group in groupby(edit_segments0,lambda x:x[1])]
  edited_text_html0=""
  for a,b in edit_segments_grouped0:
    if a=="edited_inserted": edited_text_html0+='<ins>'+b+'</ins>'
    elif a=="edited_deleted": edited_text_html0+='<del>'+b+'</del>'
    else: edited_text_html0+=b
  original_text0=general.unescape(original_text0)
  final_text0=general.unescape(final_text0)
  return original_text0,final_text0, edited_text_html0 


#7 july
def get_edit_html(tokens1,tokens2):
  edit_list=get_seq_edits(tokens1,tokens2)
  final_str_items=[]
  for edit_type0,chunk0 in edit_list:
    cur_chunk_str=general.de_tok2str(chunk0)
    cur_chunk_str=safe_xml(cur_chunk_str)
    if edit_type0=="delete": final_str_items.append('<del>%s</del>'%cur_chunk_str)
    elif edit_type0=="insert": final_str_items.append('<ins>%s</ins>'%cur_chunk_str)
    else: final_str_items.append(cur_chunk_str)
  final_str=" ".join(final_str_items)
  return final_str


def safe_xml(txt):
  txt=txt.replace("&","&amp;")
  txt=txt.replace("<","&lt;")
  txt=txt.replace(">","&gt;")
  return txt  


def get_seq_replace(tokens1,tokens2):
  match_obj=SequenceMatcher(None,tokens1,tokens2)
  final_list=[]
  for a in match_obj.get_opcodes():
    match_type,x0,x1,y0,y1=a
    deleted_tokens,inserted_tokens=[],[]
    if match_type=="delete":
      deleted_tokens=tokens1[x0:x1]
      #final_list.append(("deleted",tokens1[x0:x1]))
    if match_type=="equal":
      #final_list.append(("equal",tokens1[x0:x1]))
      pass
    if match_type=="replace":
      deleted_tokens=tokens1[x0:x1]
      inserted_tokens=tokens2[y0:y1]
      #final_list.append(("delete",tokens1[x0:x1]))
      #final_list.append(("insert",tokens2[y0:y1]))
    if match_type=="insert":
      #final_list.append(("insert",tokens2[y0:y1]))
      inserted_tokens=tokens2[y0:y1]
    final_list.append((match_type,deleted_tokens,inserted_tokens,(x0,x1),(y0,y1)))
  return final_list


def get_seq_edits(tokens1,tokens2):
  match_obj=SequenceMatcher(None,tokens1,tokens2)
  final_list=[]
  for a in match_obj.get_opcodes():
    match_type,x0,x1,y0,y1=a
    if match_type=="delete":
      final_list.append(("deleted",tokens1[x0:x1]))
    if match_type=="equal":
      final_list.append(("equal",tokens1[x0:x1]))
    if match_type=="replace":
      final_list.append(("delete",tokens1[x0:x1]))
      final_list.append(("insert",tokens2[y0:y1]))
    if match_type=="insert":
      final_list.append(("insert",tokens2[y0:y1]))
  return final_list


def compare_repl(tokens1,tokens2,window_size=5): #make all changes as replacements - add sentence boundaries for whole segment edits
  tokens1=general.add_padding(tokens1)
  tokens2=general.add_padding(tokens2)
  match_obj=SequenceMatcher(None,tokens1,tokens2)
  final_list=[]
  for a in match_obj.get_opcodes():
    match_type,x0,x1,y0,y1=a
    if match_type in ["insert","delete"]: #for insertaions/deletions, get preceding+following token to make it a replacement
      x0=x0-1
      x1=x1+1
      y0=y0-1
      y1=y1+1
      match_type="replace"
  
    old0=tokens1[x0:x1]
    new0=tokens2[y0:y1]
    span_old0=(x0,x1-1) #adjust the end of the span to reflect the index of the last token
    span_new0=(y0,y1-1)
    final_list.append((match_type,old0,new0,span_old0,span_new0))
  return final_list


def get_corr_freq_dict(file_gen): #iterting file lines, each line is json dict, with keys "src","trg"
  corr_dict0={}
  for line0 in file_gen:
    line_dict0=json.loads(line0)
    src0=line_dict0["src"]
    trg0=line_dict0["trg"]
    temp_dict=corr_dict0.get(src0,{})
    temp_dict[trg0]=temp_dict.get(trg0,0)+1
    corr_dict0[src0]=temp_dict
  return corr_dict0
  # items=list(corr_dict.items())
  # items.sort(key=lambda x:-sum(x[1].values()))
def filter_freq_dict(freq_dict,min_freq=2):
  new_freq_dict={}
  for key,val_dict in freq_dict.items():
    temp_val_dict={}
    for sub_key,freq in val_dict.items():
      if freq<min_freq: continue
      temp_val_dict[sub_key]=freq
    if temp_val_dict!={}: new_freq_dict[key]=temp_val_dict
  return new_freq_dict

def get_first_freq_dict(freq_dict):
  list_with_first=[]
  for a,b in freq_dict.items():
    first=a.split(" ")[0]
    list_with_first.append((first,(a,b)))
  list_with_first.sort()
  grouped0=[(key,[v[1] for v in list(group)]) for key,group in groupby(list_with_first,lambda x:x[0])]
  return dict(iter(grouped0))


def get_possible_replacements(sent_tokens,first_repl_dict): #use the repl dict (with keys as first word, value is a list of triplets (repl_src,repl_trg,wt))
  new_sent_tokens=list(sent_tokens)
  valid_replacements=[]
  for word0 in list(set(sent_tokens)):
    all_corr=first_repl_dict.get(word0,[]) #get the corresponding equivalents/freq to the current word
    for corr_key0,corr_freq_val_dict0 in all_corr:
      found_spans=general.is_in(corr_key0.split(),sent_tokens)
      for span0 in found_spans: valid_replacements.append((corr_key0,corr_freq_val_dict0,span0)) #just the phrase and the span
  return valid_replacements

# def get_possible_replacements(sent_tokens,first_repl_dict): #use the repl dict (with keys as first word, value is a list of triplets (repl_src,repl_trg,wt))
#   new_sent_tokens=list(sent_tokens)
#   valid_replacements=[]
#   for word0 in list(set(sent_tokens)):
#     all_corr=first_repl_dict.get(word0,[])
#     for corr0 in all_corr:
#       found_spans=general.is_in(corr0[0],sent_tokens)
#       for span0 in found_spans: valid_replacements.append((corr0,span0)) #just the phrase and the span
#   return valid_replacements


# def compare_repl_OLD(tokens1,tokens2,window_size=5): #make all changes as replacements - add sentence boundaries for whole segment edits
#   tokens1=add_padding(tokens1)
#   tokens2=add_padding(tokens2)
#   match_obj=SequenceMatcher(None,tokens1,tokens2)
#   final_list=[]
#   for a in match_obj.get_opcodes():
#     match_type,x0,x1,y0,y1=a
#     if match_type in ["insert","delete"]: #for insertaions/deletions, get preceding+following token to make it a replacement
#       x0=x0-1
#       x1=x1+1
#       y0=y0-1
#       y1=y1+1
#       match_type="replace"
  
#     old0=tokens1[x0:x1]
#     new0=tokens2[y0:y1]
#     span_old0=(x0,x1)
#     span_new0=(y0,y1)
#     prev_context=tokens1[max(0,x0-window_size):x0]
#     next_context=tokens1[x1:]
#     final_list.append((match_type,old0,new0,span_old0,span_new0,prev_context,next_context))
#   return final_list





#============ Replacement model ===================
def apply_replace(sent_tokens,first_repl_dict): #use the repl dict (with keys as first word, value is a list of triplets (repl_src,repl_trg,wt))
  new_sent_tokens=list(sent_tokens)
  valid_replacements=[]
  for word0 in list(set(sent_tokens)):
    all_corr=first_repl_dict.get(word0,[])
    for corr0 in all_corr:
      if not general.is_in(corr0[0],sent_tokens): continue
      valid_replacements.append(corr0)
  for repl0 in valid_replacements:
    repl_src,repl_trg,repl_wt=repl0
    new_sent_tokens=repl_phrase(new_sent_tokens,repl_src,repl_trg)
  return new_sent_tokens



def repl_phrase(sent_tokens,phrase_to_be_replaced,new_phrase): #replace a phrase within a sentence
  last_i=0
  new_tokens=[]
  found_spans=general.is_in(phrase_to_be_replaced,sent_tokens)
  for span0 in found_spans:
    span_i0,span_j0=span0
    new_tokens.extend(sent_tokens[last_i:span_i0])
    new_tokens.extend(new_phrase)
    last_i=span_j0+1
  new_tokens.extend(sent_tokens[last_i:])
  return new_tokens







def get_docx_paras_edits(docx_fpath): #main function to extract edit info, while keeping track of para path/id
  docx_obj=docx(docx_fpath)
  data_list1=[]
  all_paras,paras_dict=docx_obj.extract_paras()
  docx_obj.close()
  for para_path0,para_content0 in all_paras:
    orig0,final0,edit0=get_edit_info(para_content0)
    if orig0==final0=="": continue
    data_list1.append((para_path0,orig0,final0,edit0))
  return data_list1

# def get_docx_paras_edits_src_trg_editing(docx_fpath):
#   docx_obj=docx(docx_fpath)
#   data_list1=[]
#   all_paras,paras_dict=docx_obj.extract_paras()
#   docx_obj.close()
#   for para_path0,para_content0 in all_paras:
#     orig0,final0,edit0=get_edit_info(para_content0)
#     if orig0==final0=="": continue
#     data_list1.append((orig0,final0,edit0))
#   return data_list1

def para2sents(text):
  text=text.replace(". ",".\n")
  text=text.replace("\t","\n")
  sents0=[v.strip() for v in text.split("\n") if v.strip()]
  return sents0










##################### OLD #########################
def gen_para_id():
  return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


#OLD
w_p_exp=r"<w:p\b.*?>.*?</w:p>"
w_t_exp=r"<w:t\b.*?>.*?</w:t>"
w_t_inside_exp=r"<w:t\b.*?>(.*?)</w:t>"
w_t_inside_outside_exp=r"(<w:t\b.*?>)(.*?)(</w:t>)"

def get_xml_elements(xml_content0,el_name="w:p"):
  open_tag="<"+el_name
  closing_tag="</"+el_name+">"
  all_split=re.split(r"%s\b"%open_tag,xml_content0)
  #all_split=xml_content0.split(open_tag)
  all_elements=[]
  for as0 in all_split[1:]:
    if not closing_tag in as0: continue
    #if not as0[0] in " >": continue #if the first character after the open tag e.g. <w:r is not a space or >, it is a different tag
    split_closing_tag=as0.split(closing_tag)
    el_outer_xml=open_tag+split_closing_tag[0]+closing_tag
    all_elements.append(el_outer_xml)
  return all_elements

def get_para_by_id(xml_fpath0,id0): #given the paragraph ID and path of the xml file, get the outer XML element 
  fopen=open(xml_fpath0)
  content=fopen.read()
  fopen.close()
  found_i=content.find(id0)
  para_xml_i0=content[:found_i].rfind('<w:p')
  para_xml_i1=found_i+content[found_i:].find('</w:p>')+len('</w:p>')
  para_xml_slice=content[para_xml_i0:para_xml_i1]
  return para_xml_slice

def get_para_by_index(xml_fpath0,i0): #given the paragraph index and path of the xml file, get the outer XML element 
  fopen=open(xml_fpath0)
  xml_content0=fopen.read()
  fopen.close()
  cur_wps=get_xml_elements(xml_content0,el_name="w:p")
  para_xml_slice=cur_wps[i0]
  return para_xml_slice


def save_tmp2docx(tmp_dir_path,new_docx_fpath): #convert the temp directory with them XML files making the original docx into a new docx file
  if os.path.exists(new_docx_fpath): os.remove(new_docx_fpath) #remove any of these if already exists
  shutil.make_archive(tmp_dir_path, 'zip', tmp_dir_path)
  os.rename(tmp_dir_path+".zip", new_docx_fpath)






# def update_para_OLD(para_id0,xml_path0,new_text0,rtl=True,style={}): #get an xml element by ID, update it with new text and style, save the new XML with this updated element
#   fopen=open(xml_fpath0)
#   content=fopen.read()
#   fopen.close()
#   cur_slice=get_para_by_id(xml_fpath0,para_id0)
#   updated_slice=update_wr_text(cur_slice,new_text0)
#   if rtl: #
#     w_p_tag_exp=r"<w:p\b.*?>"
#     w_r_tag_exp=r"<w:r\b.*?>"
#     wp_tags=list(set(re.findall(w_p_tag_exp,updated_slice)))
#     wr_tags=list(set(re.findall(w_r_tag_exp,updated_slice)))
#     for wp0 in wp_tags:
#       updated_slice=updated_slice.replace(wp0,wp0+'<w:pPr><w:bidi/></w:pPr>')
#     for wr0 in wr_tags:
#       updated_slice=updated_slice.replace(wr0,wr0+'<w:rPr><w:rtl/></w:rPr>')




#     # wp_tags=re.findall(w_p_tag_exp,updated_slice)
#     # updated_slice=updated_slice.replace("<w:rtl/>","")  
#     # updated_slice=updated_slice.replace("<w:lang ","<w:rtl/><w:lang ")
#     # #updated_slice=updated_slice.replace('/></w:rPr>','w:bidi="ar-MA"/></w:rPr>')
    
#   content=content.replace(cur_slice,updated_slice)
#   fopen1=open(xml_fpath0,"w")
#   fopen1.write(content)
#   fopen1.close()  
#   return updated_slice

def update_para_by_index(para_i0,xml_fpath0,new_text0,rtl=True,style={}): #get an xml element by its index, update it with new text and style, save the new XML with this updated element
  fopen=open(xml_fpath0)
  content=fopen.read()
  fopen.close()
  cur_slice0=get_para_by_index(xml_fpath0,para_i0)
  #print(">>>> <<<???",cur_slice0)
  updated_slice=update_wr_text(cur_slice0,new_text0)
  if rtl: #
    # updated_slice=updated_slice.replace("<w:rtl/>","")  
    # updated_slice=updated_slice.replace("<w:lang ","<w:rtl/><w:lang ")
    #updated_slice=updated_slice.replace('/></w:rPr>','w:bidi="ar-MA"/></w:rPr>')
    w_p_tag_exp=r"<w:p\b.*?>"
    w_r_tag_exp=r"<w:r\b.*?>"
    wp_tags=list(set(re.findall(w_p_tag_exp,updated_slice)))
    wr_tags=list(set(re.findall(w_r_tag_exp,updated_slice)))
    for wp0 in wp_tags:
      updated_slice=updated_slice.replace(wp0,wp0+'<w:pPr><w:bidi/></w:pPr>')
    for wr0 in wr_tags:
      updated_slice=updated_slice.replace(wr0,wr0+'<w:rPr><w:rtl/></w:rPr>')
    #print(updated_slice)
  content=content.replace(cur_slice0,updated_slice)
  fopen1=open(xml_fpath0,"w")
  fopen1.write(content)
  fopen1.close()  
  return updated_slice
  

def get_xml_wrs(xml_content):
  cur_chunks=find_iter_split(w_p_exp,xml_content)
  return cur_chunks


def find_iter_split(expression,text): #generic function to split a text (haystack) around a certain regex
  split_text=[]
  exp_applies={} #whether the current expression applies to the current segment of the split segments
  found_objs=re.finditer(expression,text)
  indexes=[0]
  for fo in found_objs:
    start,end=fo.start(), fo.end()
    indexes.append(start)
    indexes.append(end)
    exp_applies[start]=True #in the split chunks, the regex criteria applies to some of them, and some are not, so we keep track of this
  indexes.append(len(text))
  if len(indexes)==2: return []
  counter=0
  for i0,i1 in zip(indexes,indexes[1:]):
    applies=exp_applies.get(i0,False)
    chunk=text[i0:i1] 
    split_text.append((counter,applies,chunk))
    counter+=1
  return split_text  

def get_wr_text(wr_chunk):
  all_text=""
  wt_chunks=find_iter_split(w_t_exp,wr_chunk)
  for wt in wt_chunks:
    wt_counter,wt_applies,wt_chunk=wt
    wt_content=[""]
    if wt_applies: wt_content=re.findall(w_t_inside_exp,wt_chunk)
    elif "<w:br/>" in wt_chunk: wt_content=["\n"]
    elif "<w:tab/>" in wt_chunk: wt_content=["\t"]
    all_text+=wt_content[0]
  return all_text

def striphtml(data):
  p = re.compile(r'<.*?>')
  return p.sub('', data)

def get_el_text(el_xml):
  el_xml=el_xml.replace("<w:br/>","\n")
  el_xml=el_xml.replace("<w:tab/>","\t")
  text=striphtml(el_xml)
  return text



def update_wr_text(wr_xml,new_text):
   wt_chunks=find_iter_split(w_t_exp,wr_xml)
   new_text=safe_xml(new_text)
   new_wr_content=""
   replaced=False
   for wt in wt_chunks:
     wt_counter,wt_applies,wt_chunk=wt
     if wt_applies:
       first_tag=wt_chunk[:wt_chunk.find(">")+1]
       last_tag=wt_chunk[wt_chunk.rfind("<"):]
       if replaced==False: #we replace only the first wt 
         wt_content=first_tag+new_text+last_tag
         replaced=True
       else: wt_content=first_tag+last_tag
       new_wr_content+=wt_content
     else: new_wr_content+=wt_chunk#.decode("utf-8")
   return new_wr_content






# class docx_OLD:
#   def __init__(self,docx_fpath,keep_copy=True): #openning the docx file, by unzipping it
#     self.TEMP_DOCX = docx_fpath
#     self.closed=False
#     self.COPY_DOCX = docx_fpath+"2"
#     shutil.copy(self.TEMP_DOCX, self.COPY_DOCX) #keep a temp copy of out file, just in case
#     self.file_extension="."+docx_fpath.split(".")[-1]
#     self.TEMP_ZIP = docx_fpath.replace(self.file_extension,".zip")
#     self.TEMP_FOLDER = docx_fpath.replace(self.file_extension,"")
#     if os.path.exists(self.TEMP_ZIP):
#       os.remove(self.TEMP_ZIP)
#     if os.path.exists(self.TEMP_FOLDER):
#       shutil.rmtree(self.TEMP_FOLDER)
#     os.rename(self.TEMP_DOCX, self.TEMP_ZIP) #rename the original docx to zip extension
#     # unzip file zip to specific folder
#     z_open=zipfile.ZipFile(self.TEMP_ZIP, 'r')
#     z_open.extractall(self.TEMP_FOLDER)
#     z_open.close()
#     os.rename(self.COPY_DOCX, self.TEMP_DOCX) #keep the original file
#   def save_as(self,out_fpath):
#     if os.path.exists(out_fpath): #remove any of these if already exists
#       os.remove(out_fpath)
#     #self.OUT_ZIP = out_fpath.replace(".docx",".zip")
#     #shutil.make_archive(self.OUT_ZIP, 'zip', self.TEMP_FOLDER)
#     shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
#     os.rename(self.TEMP_ZIP, out_fpath)
#   def extract_paras(self,cat_file_path=""): 
#     self.paras=[]
#     if self.TEMP_DOCX.lower().endswith(".docx"): main_dir="word"
#     if self.TEMP_DOCX.lower().endswith(".pptx"): main_dir="ppt/slides"
#     if self.TEMP_DOCX.lower().endswith(".xlsx"): main_dir="xl"

#     extracted_dir=os.path.join(self.TEMP_FOLDER, main_dir)
#     for xml_fname in os.listdir(extracted_dir):
#       #print(xml_fname)
#       skip_file=True
#       if xml_fname in ["document.xml", "footnotes.xml","endnotes.xml","sharedStrings.xml"]: skip_file=False
#       if xml_fname.startswith("slide"): skip_file=False
#       if xml_fname.startswith("sheet"): skip_file=False
#       if xml_fname.startswith("header"): skip_file=False
#       if xml_fname.startswith("footer"): skip_file=False
#       if skip_file: continue
#       # if xml_fname in ["document.xml", "footnotes.xml","endnotes.xml"] or xml_fname.startswith("header") or xml_fname.startswith("footer"): pass
#       # else: continue
#       #if not xml_fname=="document.xml" and not xml_fname.startswith("header") and not xml_fname.startswith("footer"): continue
#       cur_xml_path=os.path.join(extracted_dir,xml_fname)
#       with open(cur_xml_path) as fopen:
#         xml_content=fopen.read()
#       cur_tag_name="w:p" #xml tag for docx files
#       if self.TEMP_DOCX.lower().endswith(".pptx"): cur_tag_name="a:p"
#       cur_wps=get_xml_elements(xml_content,el_name=cur_tag_name)
#       for i0,wp_xml in enumerate(cur_wps):
#         #wp_text=get_wr_text(wp_xml)
#         wp_text=get_el_text(wp_xml)        
#         para_obj=para()
#         para_obj.path=cur_xml_path
#         para_obj.xml=wp_xml
#         para_obj.text=wp_text
#         para_obj.i=i0
#         para_obj.tag_name=cur_tag_name        
#         found_ids=re.findall('paraId="(.+?)"',wp_xml) 
#         if found_ids: para_obj.id=  found_ids[0]
#         self.paras.append(para_obj)
#       if cat_file_path!="": #save paragraphs with their info to cat file
#         cat_fopen=open(cat_file_path,"w")
#         for p_obj in self.paras:
#           cur_text=p_obj.text.replace("\t"," <tab> ").replace("\n"," <br> ")
#           json_obj={}
#           json_obj["path"]=p_obj.path
#           json_obj["i"]=p_obj.i
#           json_obj["id"]=p_obj.id
#           json_obj["tag_name"]=p_obj.tag_name          
#           json_obj["text"]=cur_text
#           json_obj_str=json.dumps(json_obj) 
#           line=json_obj_str+"\n"
#           #line="%s\t%s\t%s\t%s\n"%(p_obj.path,p_obj.i,p_obj.id,cur_text)
#           cat_fopen.write(line)
#         cat_fopen.close()

#     return self.paras
  

#   def update_tbl_rtl(self):
#     extracted_dir=os.path.join(self.TEMP_FOLDER, "word")
#     cur_xml_path=os.path.join(extracted_dir,"document.xml")
#     fopen_read=open(cur_xml_path)
#     xml_content=fopen_read.read()
#     fopen_read.close()
#     xml_content=xml_content.replace("<w:tblPr>","<w:tblPr><w:bidiVisual/>")
#     xml_content=xml_content.replace("<w:lang ","<w:rtl/><w:lang ")

    
#     fopen_write=open(cur_xml_path, "wb")
#     fopen_write.write(xml_content)
#     fopen_write.close()


#   def close(self):
#     self.closed=True
#     os.remove(self.TEMP_ZIP)
#     shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
#     os.rename(self.TEMP_ZIP, self.TEMP_DOCX)
#     shutil.rmtree(self.TEMP_FOLDER)
  

class para:
  def __init__(self):
    self.xml=""
    self.text=""
    self.path=""
    self.id=""
    self.tag_name=""
    self.i=None
  def update_text(self,new_text):
    pass
  def update_style(self,new_style):
    pass

def write(content0,path0):
  fopen0=open(path0,"w")
  fopen0.write(content0)
  fopen0.close()
def read(path0):
  fopen0=open(path0)
  content0=fopen0.read()
  fopen0.close()
  return content0

def translate_doc(in_fpath,out_fpath,tsv_fpath,sentence_split_fn,out_paras_fpath=""):
  repl_dict=tsv2dict(tsv_fpath)
  test_docx_obj=docx(in_fpath)
  paras=test_docx_obj.extract_paras(out_paras_fpath)
  for p in paras:
    cur_xml_slice=p.xml
    text0=unescape(p.text)
    sents= ssplit(text0) #need to load ssplit from general utils
    eq_sents=[]
    for sent0 in sents:
      sent0_key=str2key(sent0)
      #print(sent0_key)
      test=repl_dict.get(sent0_key)
      if test==None:
        print(sent0)
        for key0 in repl_dict.keys():
          if key0[:8]==sent0_key[:8]: print(key0)
        print("------")
      equiv=repl_dict.get(sent0_key,sent0)
      eq_sents.append(equiv)
    eq_para_text=" ".join(eq_sents)
    if eq_para_text.strip()=="": continue
    cur_content=read(p.path)
    cur_wps=get_xml_elements(cur_content,el_name="w:p")
    update_para_by_index(p.i,p.path,eq_para_text,rtl=True,style={})
  save_tmp2docx(test_docx_obj.TEMP_FOLDER,out_fpath)



if __name__=="__main__":
  # out_fpath="docs/hlpf-ar-test1.docx"
  # test_docx_obj=docx("docs/hlpf.docx")
  # paras=test_docx_obj.extract_paras("docs/hlpf-cat5.txt")
  # tsv_fpath="docs/hlpf.tsv"
  # repl_dict=tsv2dict(tsv_fpath)
  # test_pptx_obj=docx("docs/annex8.pptx")
  # paras=test_pptx_obj.extract_paras("docs/annex8-cat.txt")
  from code_utils.general import *
  in_fpath="docs/mechanism2-en.docx"
  out_fpath="docs/mechanism2-ar4.docx"
  tsv_fpath="docs/mechanism2.tsv"
  paras_fpath="docs/mechanism-paras2.txt"
  translate_doc(in_fpath,out_fpath,tsv_fpath,ssplit,out_paras_fpath="")


  # for p in paras:
  #   print(">>>>", p.id,p.path, p.i, p.text) 
  #   cur_xml_slice=p.xml
  #   sents= ssplit(p.text)
  #   eq_sents=[]
  #   for sent0 in sents:
  #     sent0_key=str2key(sent0)
  #     equiv=repl_dict.get(sent0_key,sent0)
  #     eq_sents.append(equiv)
  #   eq_para_text=" ".join(eq_sents)
  #   if eq_para_text.strip()=="": continue
  #   cur_content=read(p.path)
  #   cur_wps=get_xml_elements(cur_content,el_name="w:p")
  #   print(p.path,len(cur_wps))

  # # cur_content=read(p.path)
  # # updated_slice=update_wr_text(cur_xml_slice,eq_para_text)
  #   update_para_by_index(p.i,p.path,eq_para_text,rtl=True,style={})
  # save_tmp2docx(test_docx_obj.TEMP_FOLDER,out_fpath)



