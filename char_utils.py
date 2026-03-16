import os, shelve, unicodedata, sys, json, time, random, string, base64, copy, math
#import pandas as pd
import regex as re
import numpy as np

sys.path.append("code_utils")

cur_lib_path=os.path.split(__file__)[0]
sys.path.append(cur_lib_path)


import general


#convert a character to an array, to use for character-based neural network operations
def char2array(char,params={}):
  array_size=params.get("size",24)
  byte_string=char.encode("utf-8")
  bytes_array = np.frombuffer(byte_string, dtype=np.uint8)
  bit_array_np = np.unpackbits(bytes_array)
  bit_array_np1=np.pad(bit_array_np,(array_size-len(bit_array_np),0))
  return bit_array_np1



#15 March 2026
#remove non_text, ero width, non advancing chars and strings (mainly diacritics and markup tags), while keeping their location
def separate_zero_advance(text,params={}):
  final_text=""
  include_tags=params.get("include_tags",True)
  insertion_dict={}
  cur_loc=0
  tag_pattern=r"<\/?[a-zA-Z0-9]+[^<]*?>"
  if include_tags: full_pattern=r"\p{Mn}+|%s"%tag_pattern
  else: full_pattern=r"\p{Mn}+" #include only clusters of zero width chars (diacritics)
  matched_items=re.finditer(full_pattern,text)
  for it0 in matched_items:
    start0,end0,matched0=it0.start(),it0.end(), it0.group(0)
    cur_non_zero_width_text=text[cur_loc:start0]
    test_loc=len(final_text)
    if len(final_text)==0: test_loc=start0
    insertion_dict[test_loc]=insertion_dict.get(test_loc,"")+matched0 
    final_text+=cur_non_zero_width_text
    cur_loc=end0
  final_text+=text[cur_loc:]
  return final_text, insertion_dict

#insert diacritics and zero width strings into an existing clean string (reverse operation to separate_zero_advance)
def insert_zero_width_str(clean_text,insertion_dict):
  cur_loc=0
  cur_text=""
  keys=sorted(list(insertion_dict.keys()))
  for k0 in keys:
    inserted_chars=insertion_dict[k0]
    if k0==0: cur_text+=inserted_chars
    else: cur_text+=clean_text[cur_loc:k0]+inserted_chars
    cur_loc=k0
  cur_text+=clean_text[cur_loc:]
  return cur_text


  class char_ft:
  def __init__(self,params={}) -> None:
    self.params=params
    self.character_cat_list=['Cc', 'Cf', 'Cn', 'Co', 'Cs', 'Ll', 'Lm', 'Lo', 'Lt', 'Lu', 'Mc', 'Me', 'Mn', 'Nd', 'Nl', 'No', 'Pc', 'Pd', 'Pe', 'Pf', 'Pi', 'Po', 'Ps', 'Sc', 'Sk', 'Sm', 'So', 'Zl', 'Zp', 'Zs']
    self.n_char_cat=len(self.character_cat_list)
    self.character_cat_map_dict=dict(iter([(v,i) for i,v in enumerate(self.character_cat_list)]))
    self.array_size=self.params.get("size",24)
    self.n_feat= self.array_size+self.n_char_cat

  def extract(self,char):
    byte_string=char.encode("utf-8")
    cat0=unicodedata.category(char)
    cat_i0=self.character_cat_map_dict.get(cat0)
    cat_one_hot_array=np.zeros((self.n_char_cat))
    if cat_i0!=None: cat_one_hot_array[cat_i0]=1.
    #print(cat0,cat_i0)
    bytes_array = np.frombuffer(byte_string, dtype=np.uint8)
    bit_array_np = np.unpackbits(bytes_array)
    bit_array_np1=np.pad(bit_array_np,(self.array_size-len(bit_array_np),0))
    combined_arr = np.concatenate((bit_array_np1, cat_one_hot_array))

    return combined_arr #bit_array_np1,cat_one_hot_array