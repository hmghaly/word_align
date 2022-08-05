import h5py
import re, time
from collections import Counter
import numpy as np
import numpy.linalg as lin
from numpy import dot
#from numpy.linalg import norm


#same as the one we use for classification_utils, but we copy here to avoid importing it
def get_words_vector(words,wv_model,excluded_words=[]):
  wd_counter=Counter(words)
  flag=False
  total_count0=0
  wd_vector_dict={}
  for wd0,wd0_n in wd_counter.items():
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

def get_h5_words_vec(words0,h5_obj0):
  tmp_dict={} #get a temporary dict from the found words in the opened h5 file
  for w0 in words0:
    out=h5_obj0.get(w0)
    if out!=None: tmp_dict[w0]=np.array(out)
  cur_overall_vec,cur_wd_vec=get_words_vector(words0,tmp_dict,excluded_words=[])
  return cur_overall_vec,cur_wd_vec

def cos_sim(a,b):
  return dot(a, b)/(lin.norm(a)*lin.norm(b))


if __name__=="__main__":
  sent="agricultural tractors"
  words=re.findall("\w+",sent.lower())
  sent2="artistic paintinings"
  words2=re.findall("\w+",sent2.lower())
  h5_fopen = h5py.File("au_wv.hdf5", "r")
  t0=time.time()
  cur_vec0,wd_vec0=get_h5_words_vec(words,h5_fopen)
  cur_vec2,wd_vec2=get_h5_words_vec(words2,h5_fopen)
  cur_sim=cos_sim(cur_vec0,cur_vec2)
  t1=time.time()
  h5_fopen.close()
  print(cur_vec0,t1-t0, "cur_sim",cur_sim)  