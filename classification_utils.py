#!/usr/bin/env python
import gensim
from gensim.models import KeyedVectors
import gensim.downloader as api
import time, json, re, os, sys
import pandas as pd
from itertools import groupby
from collections import Counter
url_noise_words=["archive", "archives", "forms", "shop", "eshop", "docs", "webmail", "outlook", "mail", "library", "portal", 
"intranet", "login", "alumni", "booking", "bookings"]
noise_words=["www",'download','online','click','homepage',
  "http","email","https","com","net","upload","uploads","login","site",
             "website","browse","wordpress","text","html","navigation","coming","soon","please"]
en_stop_words=['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", 
               "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 
               'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 
               'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 
               'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 
               'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
               'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 
               'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 
               'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 
               'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 
               'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 
               'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', 
               "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 
               'won', "won't", 'wouldn', "wouldn't"]

from gensim import utils
from numpy import array
import numpy as np
from scipy import spatial
import re

class doc2vec_text:
  def __init__(self,words):
    self.words=words
    self.tags=[]

def doc2vec_train(doc_word_list,vector_size=50, min_count=2, epochs=30,max_doc_n_words=500):
  data_for_training=[]
  for doc_words0 in  doc_word_list:  
    cur_obj=doc2vec_text(doc_words0[:max_doc_n_words])
    data_for_training.append(cur_obj)
  print("started training")
  doc2vec_model = gensim.models.doc2vec.Doc2Vec(vector_size=vector_size, min_count=min_count, epochs=epochs)
  doc2vec_model.build_vocab(data_for_training)
  doc2vec_model.train(data_for_training, total_examples=doc2vec_model.corpus_count, epochs=doc2vec_model.epochs)
  meta_dict={}
  meta_dict["max_doc_n_words"]=max_doc_n_words
  doc2vec_model.comment=json.dumps(meta_dict)
  return doc2vec_model

def get_avg_doc2vec(doc_word_list):
  pass


def norm(str0): #to normalize category name
  str0=str0.lower().strip()
  normalized=re.sub("\W+","-",str0)
  return normalized.strip("-")

def get_doc_vector(doc_fpath,wv_model):
  fopen=open(doc_fpath)
  content=fopen.read()
  fopen.close()
  words=utils.simple_preprocess(content)
  return get_words_vector(words,wv_model)

def get_words_vector(words,wv_model,excluded_words=[],top_n=500):
  wd_counter=Counter(words)
  flag=False
  total_count0=0
  wd_vector_dict={}
  for wd0,wd0_n in wd_counter.most_common(top_n):
  #for wd0,wd0_n in wd_counter.items():
    if wd0 in excluded_words: continue
    try: cur_vec0=wv_model[wd0]
    except: continue
    wd_vector_dict[wd0]=cur_vec0
    weighted_vec0=cur_vec0*wd0_n
    if flag==False: total_vec0=weighted_vec0
    else: total_vec0+=weighted_vec0
    flag=True
    total_count0+=wd0_n
  if total_count0==0: return [],{}
  avg_vec=total_vec0/total_count0
  return avg_vec,wd_vector_dict

def get_words_vector_OLD(words,wv_model,excluded_words=[]):
  all_vectors=[]
  wd_vector_dict={}
  #print("words:",words[:20])
  for wd in words:
    if wd in excluded_words: continue
    #print(wd)
    #cur_vec0=wv_model[wd]
    try: 
      cur_vec0=wv_model[wd]
      all_vectors.append(cur_vec0)
      wd_vector_dict[wd]=cur_vec0
    except: pass
  #print("get_words_vector: word vector dict", list(wd_vector_dict.keys())[:20])
  if all_vectors==[]: return [],{}
  cur_avg_vector=[]
  for i in range(len(all_vectors[0])):
    sum_val=sum([v[i] for v in all_vectors])
    avg_val=float(sum_val)/len(all_vectors)
    #print(avg_val)
    cur_avg_vector.append(avg_val)
  model_word_vector = np.array( cur_avg_vector, dtype='f')
  return model_word_vector,wd_vector_dict

def get_words_vector_test(words,wv_model,excluded_words=[]):
  all_vectors=[]
  wd_vector_dict={}
  cummulative_vec=None
  counter=0
  for wd in words:
    if wd in excluded_words: continue
    try: 
      cur_vec0=wd_vector_dict.get(wd)
      if cur_vec0==None: cur_vec0=wv_model[wd]
      all_vectors.append(cur_vec0)
      wd_vector_dict[wd]=cur_vec0
      if cummulative_vec==None: cummulative_vec=cur_vec0
      else: cummulative_vec = [cummulative_vec + cur_vec0 for a, b in zip(list1, list2)]
      counter+=1
    except: pass
  if all_vectors==[]: return [],{}
  cur_avg_vector=[float(v)/counter for v in cummulative_vec]
  # cur_avg_vector=[]
  # for i in range(len(all_vectors[0])):
  #   sum_val=sum([v[i] for v in all_vectors])
  #   avg_val=float(sum_val)/len(all_vectors)
  #   #print(avg_val)
  #   cur_avg_vector.append(avg_val)
  model_word_vector = np.array( cur_avg_vector, dtype='f')
  return model_word_vector,wd_vector_dict

#cosine similarity between word vectors
def cos_sim(vector1,vector2):
  if len(vector1)==0 or len(vector2)==0: return 0
  result = 1 - spatial.distance.cosine(vector1, vector2)
  return result

#creating a custom category vector from a keyword dictionary keyword_dict["cat_name"]=["word1","word2","word3"...]
def create_cat_vector(input_keyword_dict,wv_model):
  tmp_category_vector_dict={}
  for key,words in input_keyword_dict.items():
    if len(words)==0: continue
    #words=re.findall("\w+",val)
    #print(words) 
    cur_vec,_=get_words_vector(words,wv_model)
    tmp_category_vector_dict[key]=cur_vec
  return tmp_category_vector_dict


class text_classification:
  def __init__(self,text_input,wv_model_input,category_vector_dict_input,excluded_words=[],pred_n=5,related_words_n=5):
    self.wv_model=wv_model_input
    self.category_vector_dict=category_vector_dict_input
    # tmp_text_split=text_input.split(" ")
    # self.url=tmp_text_split[0]
    self.text=text_input #" ".join(tmp_text_split[1:])
    self.excluded_words=excluded_words+noise_words
    self.words=[v.lower() for v in re.findall("\w+",self.text) if not v in self.excluded_words and not v[0].isdigit() and len(v)>2]
    self.text_vec,self.word_vec_dict=get_words_vector(self.words,self.wv_model,self.excluded_words)
    # print("self.words",self.words[:10])
    # print("self.text_vec", self.text_vec)
    self.preds=[]
    self.word_counts=Counter(self.words)
    self.top_preds=[] #top predictions with their values and associated words

    if self.text_vec==[]: return
    for cat,vec0 in self.category_vector_dict.items():
      similarity_val=cos_sim(vec0,self.text_vec)
      self.preds.append((cat,similarity_val))
      #print(cat,similarity_val)
    self.preds.sort(key=lambda x:-x[1])
    for pred_cat,pred_val in self.preds[:pred_n]:
      pred_vec=self.category_vector_dict[pred_cat]
      wd_sim_list=[]
      for wd0,vec0 in self.word_vec_dict.items():
        wd_cat_sim_val=cos_sim(pred_vec,vec0)
        wd_sim_list.append((wd0,wd_cat_sim_val))
      wd_sim_list.sort(key=lambda x:-x[1])
      related_words=[v[0] for v in wd_sim_list[:related_words_n]]
      self.top_preds.append((pred_cat,round(pred_val,4),related_words))
    # print(self.top_preds)
    # print(self.words[:30])
    # print("--------")

class cat_struct: #processing the category structure excel file
  def __init__(self,excel_fpath):
    xls = pd.ExcelFile(excel_fpath)
    categories_sheet=pd.read_excel(xls, 'categories',keep_default_na=False)
    parents_sheet=pd.read_excel(xls, 'parents',keep_default_na=False)

    #print(categories_sheet.keys())
    #print(parents_sheet.keys())
    #print(xls.sheet_names)

    self.keyword_dict={}
    self.id_dict={}
    self.child_dict={}
    self.data_dict={}
    self.icon_dict={}
    self.cat_domains_dict={} #domains at which this category applies
    self.description_dict={}
    self.parent_list=[]
    self.parent_ids=[]
    parent_child_list=[]
    #processing the parents sheet
    for row in parents_sheet.iterrows():
      cur_obj={}
      row_dict=row[1].to_dict()
      parent_name=row_dict["Parent"]
      icon=row_dict["Icon"]
      description=row_dict["Description"]
      if parent_name=="": continue
      self.parent_list.append((parent_name,norm(parent_name)))
      self.parent_ids.append(norm(parent_name))
      self.icon_dict[norm(parent_name)]=icon
      self.description_dict[norm(parent_name)]=description
    #now processing the categories sheet
    for row in categories_sheet.iterrows():
      cur_obj={}
      row_dict=row[1].to_dict()
      cat_name=row_dict["Category"]
      if cat_name=="": continue
      keywords=row_dict["Keywords"]
      parent1=row_dict["Parent1"]
      alias1=row_dict["Alias1"]
      parent2=row_dict["Parent2"]
      alias2=row_dict["Alias2"]
      parent3=row_dict.get("Parent3","")
      alias3=row_dict.get("Alias3","")
      cat_description=row_dict.get("Description","")
      cat_icon=row_dict.get("Icon","")
      cat_domains_str=row_dict.get("Domains","") #whether to keep .com/.gov
      cat_domains=re.findall("\w+",cat_domains_str.lower())
      


      norm_cat,norm_parent1,norm_parent2,norm_parent3=norm(cat_name),norm(parent1),norm(parent2),norm(parent3)
      self.id_dict[norm_cat],self.id_dict[norm_parent1],self.id_dict[norm_parent2],self.id_dict[norm_parent3]=cat_name,parent1,parent2,parent3
      self.description_dict[norm_cat]=cat_description
      self.icon_dict[norm_cat]=cat_icon
      self.cat_domains_dict[norm_cat]=cat_domains
      #print(cat_name, "=", keywords)
      if norm_parent1: 
        if alias1: cur_alias1=alias1
        else: cur_alias1=cat_name
        parent_child_list.append((norm_parent1,(norm_cat,cur_alias1)))
      if norm_parent2: 
        if alias2: cur_alias2=alias2
        else: cur_alias2=cat_name
        parent_child_list.append((norm_parent2,(norm_cat,cur_alias2)))
      if norm_parent3: 
        if alias3: cur_alias3=alias3
        else: cur_alias3=cat_name
        parent_child_list.append((norm_parent3,(norm_cat,cur_alias3)))

      self.keyword_dict[norm_cat]=re.findall("\w+",keywords.lower())

    parent_child_list.sort()
    # for pc in parent_child_list:
    #   print(pc)
    grouped=[(key,[v[1] for v in group]) for key,group in groupby(parent_child_list,lambda x:x[0])]
    #self.child_dict=dict(iter(grouped))
    #for k,v in self.child_dict.items():
    for k,v in grouped:
      self.child_dict[k]=list(set(v))
      #print(k,v)

    def get_children(child_dict0,cat_id0,level=0):
      for child in child_dict0.get(cat_id0,[]): #node['children']:
        yield child
        if cat_id0==child[0]: continue
        for grandchild in get_children(child_dict0,child[0],level+1):
          yield grandchild
    self.recursive_child_dict={}
    for key in self.child_dict:
      grand_children=list(get_children(self.child_dict,key))
      self.recursive_child_dict[key]=grand_children
    
    self.cat_list=[]
    for cat_id,cat_name in self.id_dict.items():
      if cat_id in self.parent_ids: continue 
      if cat_id: self.cat_list.append((cat_name,cat_id))
    self.cat_list.sort()    




    self.data_dict["parent_list"]=self.parent_list
    self.data_dict["icon_dict"]=self.icon_dict
    self.data_dict["description_dict"]=self.description_dict
    self.data_dict["cat_domains_dict"]=self.cat_domains_dict

    self.data_dict["id_dict"]=self.id_dict
    self.data_dict["child_dict"]=self.child_dict
    self.data_dict["recursive_child_dict"]=self.recursive_child_dict
    self.data_dict["keyword_dict"]=self.keyword_dict
    self.data_dict["cat_list"]=self.cat_list

  def save(self,json_fpath):
    data_dict_json=json.dumps(self.data_dict)
    json_fopen=open(json_fpath,"w")
    json_fopen.write(data_dict_json)
    json_fopen.close()    

def get_processed_urls(classified_path0): #create a dictionary from the classified list to avoid-re-classifying urls
  url_dict={}
  counter=0
  if not os.path.exists(classified_path0): return {}
  fopen=open(classified_path0)
  for i,f in enumerate(fopen):
    line=f.strip()
    if line=="": continue
    url=line.split("\t")[0]
    url_dict[url]=True
    counter+=1
  fopen.close()  
  return url_dict

def classify_cached(cached_fpath,classified_fpath,category_vector_dict0,wv_model0,max_n_words=5000):
  #n_processed_lines=file_len(classified_fpath)
  processed_urls_dict=get_processed_urls(classified_fpath)
  print("current number of classified URLS", len(processed_urls_dict.keys()))
  #return
  print("finished processing existing classified list")
  classified_fopen=open(classified_fpath,"a")
  #classified_fopen.close()
  cache_fopen=open(cached_fpath)  
  counter=0
  t0_=time.time()
  for i_,f in enumerate(cache_fopen):
    line=f.strip("\n")
    if not line: continue
    #   classified_fopen.write("\n")
    #   continue
    # if i_<n_processed_lines: continue

    if i_%5000==0: 
      t1_=time.time()
      elapsed=t1_-t0_      
      print(i_, "time:", round(elapsed,2))
      classified_fopen.close()
      classified_fopen=open(classified_fpath,"a")

      t0_=time.time()
    #if i_>2000: break
    url=line.split("<br>")[0]  
    meta=line.split("<br>")[1]
    if processed_urls_dict.get(url,False)==True: continue
    try: meta_dict=json.loads(meta)
    except: meta_dict={}
    content=" ".join(line.split("<br>")[2:])
    words=[v.lower() for v in re.findall("\w+",content)]
    if len(words)<20: continue
    words=words[:max_n_words] #only the first 10,000 words
    #print("classify_cached", words[:10])
    exclusion_phrases=["coming soon","not found","404","403","forbidden","error"]


    if "coming soon" in content.lower()[:50]: continue #print("<---- exclude")
    if "not found" in content.lower()[:50]: continue #print("<---- exclude")
    if "404" in content.lower()[:20]: continue #print("<---- exclude")
    if "403" in content.lower()[:20]: continue #print("<---- exclude")
    if "forbidden" in content.lower()[:20]: continue #print("<---- exclude")
    if "error" in content.lower()[:20]: continue #print("<---- exclude")
    if "domain" in content.lower()[:50] and "parked" in content.lower()[:50]: continue #print("<---- exclude")
    if "found" in content.lower()[:50] and "cannot" in content.lower()[:50]: continue #print("<---- exclude")
    # if ".gov" in bare_url or ".edu" in bare_url:
    #   print(url,bare_url)
    #   print(content)
    #   print("-----")
    # continue

    tc_obj=text_classification(content,wv_model0,category_vector_dict0,excluded_words=en_stop_words)
    line_items=[url]
    #print(tc_obj.url)
    top_10_words=[v[0] for v in list(tc_obj.word_counts.most_common(10))]
    top_10_words_str=", ".join(top_10_words)
    page_info_obj={}
    page_info_obj["meta"]=meta_dict
    page_info_obj["top_words"]=top_10_words
    page_info_obj["n_words"]=len(words)
    page_info_obj["top_preds"]=tc_obj.top_preds
    json_str=json.dumps(page_info_obj)
    # print("classify_cached", words[:10])
    # print("tc_obj.top_preds",tc_obj.top_preds)
    
    #print(top_10_words)
    # for p in tc_obj.top_preds:
      
    #   pred_cat,pred_val,pred_words=p
    #   pred_words_str=", ".join(pred_words)

    #   cur_pred_item="%s: %s - %s" %(pred_cat,pred_val,pred_words_str)
    #   line_items.append(cur_pred_item)
    line_items.append(top_10_words_str)
    #print("----")
    #pred_line="\t".join(line_items)+"\n"
    pred_line="%s\t%s\n"%(url,json_str)
    classified_fopen.write(pred_line)
    counter+=1

  cache_fopen.close()
  classified_fopen.close()  


if __name__=="__main__":
  kw_dict0={}
  kw_dict0["sport"]=["game","match","player"]
  kw_dict0["construction"]=["scaffold","construction","architecture"]
  print("started to load model")
  print(sys.argv)
  xl_fname='290721.xlsx'
  cached_fpath="crawl/aug21/cached_all.txt"
  classified_fpath="crawl/aug21/classified_all5.txt"
  crawl_dir="crawl"
  run_dir="oct21_au"
  cached_fname="cached_all.txt"
  classified_fname="classified_all.txt"
  xls_fpath="14october21.xlsx"
  cat_json_fpath="data_dict_new.json"

  if len(sys.argv)>1: crawl_dir=sys.argv[1]
  if len(sys.argv)>2: run_dir=sys.argv[2]  
  if len(sys.argv)>3: cached_fname=sys.argv[3]  
  if len(sys.argv)>4: classified_fname=sys.argv[4] 
  if len(sys.argv)>5: cat_json_fpath=sys.argv[5]   
  # if len(sys.argv)>5: xls_fpath=sys.argv[5] 
  # if len(sys.argv)>6: cat_json_fpath=sys.argv[6] 

  cached_fpath=os.path.join(crawl_dir,run_dir,cached_fname)
  classified_fpath=os.path.join(crawl_dir,run_dir,classified_fname)
  #print("xl_fname",xl_fname)
  print("cat_json_fpath",cat_json_fpath)
  print("cached_fpath",cached_fpath)
  print("classified_fpath",classified_fpath)

  #TESTING
  #classify_cached(cached_fpath,classified_fpath,{},{})

  json_fopen=open(cat_json_fpath)
  cat_struct_obj=json.load(json_fopen)
  json_fopen.close()
  cur_keyword_dict=cat_struct_obj["keyword_dict"]
  cat_domains_dict=cat_struct_obj["cat_domains_dict"]
  # for a,b in cat_domains_dict.items():
  #   print(a,b)
  #sys.exit()

  # cat_struct_obj=cat_struct(xls_fpath)
  
  # cat_struct_obj.save(cat_json_fpath)
  print("loaded categorization structure, converted to dictionary")

  #sys.exit()
  #print("Hello!")
  t0=time.time()
  #cur_wv_model=KeyedVectors.load("google-news.wv",mmap='r')
  #cur_wv_model=api.load('word2vec-google-news-300', return_path=True)
  cur_wv_model= api.load("word2vec-google-news-300")
  t1=time.time()
  print("loaded WV model",t1-t0)
  t0=time.time()
  cur_cat_vector=create_cat_vector(cur_keyword_dict,cur_wv_model)  
  print("loaded categorization vector",t1-t0)
  


  t0=time.time()
  from extraction_utils import *
  
  classify_cached(cached_fpath,classified_fpath,cur_cat_vector,cur_wv_model)
  #cur_cat_vector=create_cat_vector(kw_dict0,cur_wv_model)
  t1=time.time()
  elapsed=t1-t0
  print("Time for classification:", elapsed)

