import re, os, shelve, unicodedata, sys, json, time, random, string
#import pandas as pd
import re
from itertools import groupby
from difflib import SequenceMatcher


from datetime import datetime


if sys.version[0]=="3": 
    import pickle
    from html.parser import HTMLParser
    htmlp = HTMLParser() #To decode html entities in the tika output
else: 
    import cPickle
    import HTMLParser
    htmlp = HTMLParser.HTMLParser() #To decode html entities in the tika output

################## Time and IDs ####################
def now():
  return time.time()

def today():
  date_str=datetime.today().strftime('%Y-%m-%d')
  return date_str


def gen_id(size=6): #generate a random id of specific size
  return ''.join(random.choices(string.ascii_uppercase + string.digits, k=size))


#from difflib import SequenceMatcher
def unescape(text_with_html_entities):
  if sys.version_info[0]==3:
    import html
    return html.unescape(text_with_html_entities)
  else:
    import HTMLParser
    return HTMLParser.HTMLParser().unescape(text_with_html_entities)


def similar(a, b):
  return SequenceMatcher(None, a, b).ratio()

##################### LISTS ###########################
#advanced list operations
def avg(list1):
  return float(sum(list1))/len(list1)   

def flatten(l):
  return [item for sublist in l for item in sublist]

def unique(list0): #get the unique items of a list in order
  used_dict={}
  list1=[]
  for item0 in list0:
    if used_dict.get(item0,False): continue
    list1.append(item0)
    used_dict[item0]=True
  return list1

def get_metrics(pred,actual,metrics_dict={}): #update precision/recall values with each prediction/actual pair
  tp=metrics_dict.get("tp",0)
  tn=metrics_dict.get("tn",0)
  fp=metrics_dict.get("fp",0)
  fn=metrics_dict.get("fn",0)
  if round(pred)==1:
    if round(actual)==1: tp+=1
    else: fp+=1
  else:
    if round(actual)==1: fn+=1
    else: tn+=1
  precision0,recall0,f_score=0,0,0
  if (tp+fp)>0: precision0=tp/(tp+fp)
  if (tp+fn)>0: recall0=tp/(tp+fn)
  if (precision0 + recall0)>0: f_score= (2 * precision0 * recall0) / (precision0 + recall0)
  metrics_dict["tp"]=tp
  metrics_dict["tn"]=tn
  metrics_dict["fp"]=fp
  metrics_dict["fn"]=fn

  metrics_dict["precision"]=precision0
  metrics_dict["recall"]=recall0
  metrics_dict["f_score"]=f_score
  return metrics_dict

def get_list_metrics(pred_vals,actual_vals):
  cur_metrics_dict={}
  for a,b in zip(pred_vals,actual_vals):
    cur_metrics_dict=get_metrics(a,b,cur_metrics_dict)  
  return cur_metrics_dict


def split_train_test(all_data0,train_ratio=0.8):
  train_size=int(len(all_data0)*train_ratio)
  train_set0,tes_set0=all_data0[:train_size],all_data0[train_size:]
  return train_set0,tes_set0

def transpose(list1):
  return list(map(list, zip(*list1)))

def interval_split(list1,n_intervals): #gets the boundaries between segments when dividing a list into n intervals 
  interval_size=int(len(list1)/(n_intervals-1))
  boundary_elements=[]
  for i0 in range(n_intervals-1):
    cur_i=i0*interval_size
    cur_el=list1[cur_i]
    boundary_elements.append(cur_el)
    #print(cur_i,cur_el)
  boundary_elements=sorted(list(set(boundary_elements)))
  return boundary_elements

def list_in_list(small,large,skip_punc=True): #retieves the spans of indexes where a small list exists in a big list
    mapping_dict=dict(iter([(i0,i0) for i0 in range(len(large))]))
    if skip_punc:
        small=[v for v in small if not is_punct(v)]
        if small==[]: return []
        large_toks_indexes=[(i,v) for i,v in enumerate(large) if not is_punct(v)]
        large=[v[1] for v in large_toks_indexes]
        large_indexes=[v[0] for v in large_toks_indexes]
        mapping_dict=dict(iter(enumerate(large_indexes)))

    first=small[0]
    ranges=[]
    for idx, item in enumerate(large):
        if large[idx:idx+len(small)]==small:
            range0,range1=idx,idx+len(small)-1
            #range0,range1=idx,idx+len(small)
            range0,range1=mapping_dict[range0],mapping_dict[range1]
            ranges.append((range0,range1))

            #ranges.append((idx,idx+len(small)-1))
    return ranges
def is_in(small,large,skip_punc=False): 
    return list_in_list(small,large,skip_punc=skip_punc)

def group_list(list_2): #group a list with each element is of size 2 - by the first sub-element
  out_dict={}
  list_2.sort(key=lambda x:x[0])
  grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(list_2,lambda x:x[0])]
  out_dict=dict(iter(grouped))
  return out_dict


####################### Dictionaries ######################
def check_dict_multi_keys(dict0,possible_key_list): #if we're not fully sure which key works
  key0,val0=None,None
  for key0 in possible_key_list:
    val0=dict0.get(key0)
    if val0!=None: return key0,val0
  return key0,val0

#17 Dec 23
#combine a list of dictionaries into one dictionary 
def combine_dict_list(list_of_dicts):
  combined_dict={}
  for dict0 in list_of_dicts:
    for key,val in dict0.items(): combined_dict[key]=val
  return combined_dict


####################### STRINGS ###########################
#string operations
def is_un_symbol(str0):
  out=False
  if str0[0].isupper() and str0[-1].isdigit() and "/" in str0: out=True
  return out

def is_website(str0):
  out=False
  if str0.lower().startswith("http:") or str0.lower().startswith("https:"): out=True
  return out

def is_money(str0):
  out=False
  if str0.startswith("$") or str0[-1].isdigit(): out=True
  return out

def is_number(str0):
  out=False
  if re.sub("[\d\.\,]","",str0)=="": out=True
  return out


def str2key(str0): #create_id, create_key, create_text_id
  str0=unescape(str0)
  str0=str0.lower().strip()
  str0=re.sub("\W+","_",str0).strip("_")
  return str0
from difflib import SequenceMatcher

TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(text,repl_with=""): #can also replace with spaces
  removed=TAG_RE.sub(repl_with, text)
  return re.sub("\s+"," ",removed) #remove extra spaces #TAG_RE.sub(repl_with, text)

def is_alpha(text):
  removed=re.sub("[\W\d]","",text)
  return removed!=""

#string/text/unicode functions
# Converting any string or list of strings into unicode    
def uc(w):
    if type(w) is str:
        output=w.decode('UTF-8', 'ignore')
    if type(w) is list:
        output=[v.decode('UTF-8', 'ignore') for v in w]
    return output

# Converting any string or list of strings into utf-8
def utf(w):
    if type(w) is str or type(w) is unicode:
        output=w.encode('UTF-8', 'ignore')
    elif type(w) is list:
        output=[v.encode('UTF-8', 'ignore') for v in w]
    else:
        output=w
    return output

# Normalizing Unicode String
def norm_unicode(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

import unicodedata
def is_punct(token):
    if len(token)==0: return True
    unicode_check=unicodedata.category(token[0])
    if len(unicode_check)>0: return unicode_check[0]=="P"
    print(token, unicode_check)
    return True


def normalize(tokens):
  new_tokens=["<s>"]
  for tok0 in tokens:
    tok0=tok0.lower().strip("_")
    if tok0.replace(".","").isdigit(): tok0="5"*len(tok0)
    elif tok0.startswith("http") or tok0.startswith("www."): tok0="_website_"
    elif "@" in tok0 and "." in tok0: tok0="_email_"
    elif "/" in tok0 and tok0[-1].isdigit() and tok0[0].isalpha(): tok0="_un_"
    else: pass
    new_tokens.append(tok0)
  new_tokens.append("</s>")
  return new_tokens




arabic_letter_dict={}
for i in range(10000):
  char0=chr(i)
  try: name = unicodedata.name(char0).lower()
  except: name=""
  if ('arabic' in name or 'persian' in name): arabic_letter_dict[char0]=True

def is_arabic(word):
  output=False
  if len(word)==0: return False
  if arabic_letter_dict.get(word[0],False) or arabic_letter_dict.get(word[-1],False): output=True
  return output

def get_chars(start_i,end_i,include_diacritics=False): #generate list of chars depending on the range - ar 1568,1646 
  char_list=[]
  for i in range(start_i,end_i):
    ch0=chr(i)
    ch_type=unicodedata.category(ch0)
    if include_diacritics==False and not (ch_type.startswith("Ll") or ch_type.startswith("Lo")): continue
    char_list.append(ch0)
  return char_list


def has_arabic(str0):
  for char0 in str0:
    char_ord=ord(char0)
    if char_ord>=1560 and char_ord<=1646: return True
  return False

ar_chars=get_chars(start_i=1560,end_i=1646,include_diacritics=False)
ascii_chars=get_chars(start_i=0,end_i=500,include_diacritics=False)



def get_key(txt): #normalize text by replacing non alpha items with _
  txt=re.sub("\W+","_",txt)
  txt=txt.strip("_")
  return txt.lower()


####################### TOKENIZATION ####################
#Word tokenization and sentence tokenization

multi_dot_words_lower=["e.g.","i.e.","u.s.a.","u.k.","o.k."," v."," vs."," v.s.", " et al."," etc.", " al."]
multi_dot_words=["e.g.","i.e.","U.S.A.","U.K.","o.k."," v."," vs."," v.s.", " et al."," etc.", " al."]
dot_words=["Mr","Ms","Dr","Art","art","Chap","chap","No","no","rev","Rev","Add","para","Para","Paras","paras"]
diac=u'\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\ufc62'
def tok_ar_diac(text):
  diac_list=[]
  for i0,dia0 in enumerate(diac):
    if not dia0 in text: continue
    place_holder0=f'_diac{i0}_'
    text=text.replace(dia0,place_holder0)
    diac_list.append((place_holder0,dia0))

  text=re.sub("(\W)",r" \1 ",text)
  for a,b in diac_list:
    text=text.replace(a,b)
  tokens=[v for v in re.split("\s+",text) if v]
  return tokens


def tok_multiling(text): 
  tokens=[]
  text=re.sub(u'[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\ufc62]','',text) #remove arabic diacritics
  text=re.sub('(\d+)(\w)',r'\1 \2',text) #handle numbers in chinese and japanese
  chunks=re.findall("\w+",text)
  for c in chunks:
    if ord(c[0])>10000 or ord(c[-1])>10000: 
      check_end_digits=re.findall('([0-9]+)$',c)
      if check_end_digits!=[]: c=c[:len(check_end_digits[0])]
      tokens.extend(list(c)) #if japanese or chinese, split by character
      tokens.extend(check_end_digits)
    else: tokens.append(c) #else, get the full token
  return tokens

import unicodedata
def char_is_punct(char0):
  unicode_check=unicodedata.category(char0)
  if len(unicode_check)>0: return unicode_check[0]=="P"
  return False

def tok(txt):
  txt=txt.replace('\u200b','')
  new_str=""
  txt_split=txt.split()
  punc_exists_dict={}
  for char0 in set(txt):
     if char_is_punct(char0):punc_exists_dict[char0]=True 
  #cur_punct_items=[v for v in list(set(txt)) if char_is_punct(v)]
  for item0 in txt_split:
    if punc_exists_dict.get(item0,False):
       new_str+=" %s "%item0
       continue
    begin_punc_chars,end_punc_chars="",""
    for char0 in item0: 
      if punc_exists_dict.get(char0,False): begin_punc_chars+=char0
      else: break
    for char0 in reversed(item0): 
      if punc_exists_dict.get(char0,False): end_punc_chars=char0+end_punc_chars
      else: break
    bare_token=item0[len(begin_punc_chars):len(item0)-len(end_punc_chars)]
    splitting_hyphen_slash=True
    if bare_token.lower().startswith("http") or bare_token.lower().startswith("www.") or "@" in bare_token: splitting_hyphen_slash=False
    if bare_token and bare_token[0].isupper() and bare_token[-1].isdigit() and "/" in bare_token: splitting_hyphen_slash=False
    if splitting_hyphen_slash: bare_token=bare_token.replace("-"," _-_ ") #" _-_ ".join(bare_token.split("-")) 
    if splitting_hyphen_slash: bare_token=bare_token.replace("/"," _/_ ")
    bare_token=bare_token.replace("("," (_ ")
    bare_token=bare_token.replace(")"," _) ")
    bare_token=bare_token.replace('"',' " ')
    if bare_token.endswith("'s"): bare_token=bare_token[:-2]+" _'s"
    if bare_token.endswith("’s"): bare_token=bare_token[:-2]+" _'s"
    if bare_token.startswith("و") and bare_token[1:].isdigit(): bare_token=bare_token[0]+" "+bare_token[1:]
    #print([item0,begin_punc_chars,end_punc_chars, bare_token])
    for i0,char0 in enumerate(begin_punc_chars):
      if i0==0: new_str+=char0+"_ "
      else: new_str+=" _"+char0+"_ "
    new_str+=bare_token
    if begin_punc_chars!=end_punc_chars:
      for i0,char0 in enumerate(end_punc_chars):
        if i0==len(end_punc_chars)-1: new_str+=" _"+char0
        else: new_str+=" _"+char0+"_ "
    new_str+=" "    
  return [v for v in new_str.split(" ") if v]

def de_tok_space(tokens): #outputs list of tokens with the following, whether it is followed by space or not identify which tokens are followed by space and which are not, based on latest tok
  tok_space_list=[]
  for tok_i,tok0 in enumerate(tokens):
    cur_tok=str(tok0)
    prev_tok,next_tok="",""
    if tok_i+1<len(tokens): next_tok=tokens[tok_i+1]
    if tok_i>0: prev_tok=tokens[tok_i-1]
    following=" "
    if next_tok=="": following=""
    if next_tok.startswith("_"): following=""
    if cur_tok.endswith("_"): following=""
    if next_tok.startswith("ـ"): following=""
    if cur_tok.endswith("ـ"): following=""
    if cur_tok.startswith("ال_"):
      if prev_tok.strip("ـ")=="ل":
        cur_tok=cur_tok.replace("ال_","ل")
      else: cur_tok=cur_tok.replace("ال_","ال")
    cur_item= (cur_tok.strip("_"),following)
    tok_space_list.append(cur_item)
  return tok_space_list

def de_tok2str(tokens): #detokenize tokens into string
  detok_str0=""
  tokens_with_space_info0=de_tok_space(tokens)
  for a0 in tokens_with_space_info0: detok_str0+=a0[0]+a0[1]
  return detok_str0


def add_padding(token_list): #add sentence start/end marker to a list of tokens
  if len(token_list)==0: return ["<s>","</s>"]
  if token_list[0]=="<s>" and token_list[-1]=="</s>": return token_list
  return ["<s>"]+token_list+["</s>"]

def remove_padding(token_list): #remove sentence start/end marker to a list of tokens
  if len(token_list)<2: return token_list 
  if token_list[0]=="<s>": token_list=token_list[1:]
  if token_list[-1]=='</s>': token_list=token_list[:-1]
  return token_list


#======== subwords, charachter chunks
def get_char_chunks(word0,max_chunk_size=7,exclude_inside_chunks=False):
  all_chunks=[]
  if exclude_inside_chunks: #include only chunks from beginning or from end
    for size0 in range(1,max_chunk_size+1):
        if size0>len(word0): continue
        cur_span=(0,size0)
        cur_chunk=word0[:size0]
        all_chunks.append((cur_chunk, cur_span))
        if len(word0)==size0: continue #from the end
        cur_span=(len(word0)-size0,len(word0))
        cur_chunk=word0[len(word0)-size0:]
        all_chunks.append((cur_chunk, cur_span))

  else: #include all internal chunks
      for size0 in range(1,max_chunk_size+1):
        for char_i in range(0,len(word0)-size0+1):
          cur_chunk=word0[char_i:char_i+size0]
          span=(char_i,char_i+size0)
          all_chunks.append((cur_chunk, span))
  return all_chunks



#==== for applications such as spell checking or creating word vectors
def get_neighbor_offsets(word_i,sent_words,max_offset=3):
  #cur_word=sent_words[word_i]
  neighbor_offsets=[]
  for inc0 in range(1,max_offset+1):
    prev_word,next_word="",""
    if word_i-inc0>=0: prev_word=sent_words[word_i-inc0]
    if word_i+inc0<len(sent_words): next_word=sent_words[word_i+inc0]
    neighbor_offsets+=[(prev_word,-inc0),(next_word,inc0)]
  neighbor_offsets.sort(key=lambda x:x[1])
  return neighbor_offsets

def create_one_hot_vec(hot_i,vec_size):
  zeros=[0.]*vec_size
  zeros[hot_i]=1.
  return zeros




# def tok(txt,keep_urls=True,keep_un_symbols=True,keep_numbers=False,keep_diacritics=True): #this is a tokenization scheme to preserve the punctuation also, but it is sensetive to English clitics, instead of splitting isn't as ['isn',"'","t"], it splits ["is","n't"]
#     replaced=[]
#     if keep_urls: replaced.extend(re.findall("https?\:\/\/\S+",txt))
#     if keep_un_symbols: replaced.extend(re.findall(r"[A-Z]+/\S+\d\b",txt))
#     if keep_diacritics:
#         for d0 in diac: 
#             if d0 in txt: replaced.append(d0)
#     for mdw in multi_dot_words:
#         if mdw in txt: replaced.append(mdw)

#     #if keep_numbers: replaced.extend(re.findall(r"[\d,\.]+",txt))
#     repl_dict={}
#     for i0,u0 in enumerate(replaced):
#         key="__item%s__"%i0
#         repl_dict[key]=u0
#         txt=txt.replace(u0,key)

#     #txt=txt.replace(u'\x01'," ")
#     txt=txt.replace(u'\u2019',"'")
    
#     txt=txt.replace("'s "," __a__s ") #keep apostrophe 's
#     txt=re.sub("(\w)'(\w)",r'\1__a__\2',txt) #keep any apostrophe inside a word
#     txt=re.sub("(?u)(\W)",r" \1 ", txt)
#     txt=txt.replace("__a__", "'")
#     for a,b in repl_dict.items():
#         txt=txt.replace(a,b)
    
#     out=re.split("\s+",txt)
#     return [v for v in out if v]

def tok_keep_punc(text0): #sep 2022
  non_space=text0.split() #simple split by space
  all_tokens0=[]
  for a in non_space:
    leading0,trailing0="","" #get the leading and trailing non-alpha characters
    max_val=min(len(a),3) #iterating a number of characters from the beginning and end of token
    for i0 in range(1,max_val+1): 
      if not a[-i0].isalnum():trailing0=a[-i0]+trailing0
      else: break
    for i0 in range(0,max_val): 
      if not a[i0].isalnum():leading0+=a[i0]
      else: break
    main=a[len(leading0):len(a)-len(trailing0)]
    main_trailing=main+trailing0 #combine main part of the token with the 
    add_space_after,add_space_before=True,True #if we need to add space  between lead/main/trailing parts
    if leading0!="" and leading0 in "#@": add_space_after=False #keep hashtags and mentions
    if main in dot_words or main_trailing.lower() in multi_dot_words: add_space_before=False #things like e.g. U.S.A.
    if main.isdigit() and trailing0 in ".-)(": add_space_before=False #For things like 1. 2) 
    if len(main)==1: add_space_before=False #and A. B.
    cur_items_str="" #start building the string
    if leading0!="": cur_items_str+=" ".join(list(leading0)) #split the leading chars, add them to final str
    if add_space_after: cur_items_str+=" " #if there is a space between leading and main
    cur_items_str+=main #add the main part
    if add_space_before: cur_items_str+=" " #if there is space between main and trailing
    if trailing0!="": cur_items_str+=" ".join(list(trailing0)) #split trailing chars and add them
    all_tokens0.extend(cur_items_str.split()) #split the final string and add it to the list of tokens
  return all_tokens0

def tok_old(txt,keep_urls=True,keep_un_symbols=True,keep_numbers=False): #this is a tokenization scheme to preserve the punctuation also, but it is sensetive to English clitics, instead of splitting isn't as ['isn',"'","t"], it splits ["is","n't"]
    replaced=[]
    if keep_urls: replaced.extend(re.findall("https?\:\/\/\S+",txt))
    if keep_un_symbols: replaced.extend(re.findall(r"[A-Z]+/\S+\d\b",txt))
    #if keep_numbers: replaced.extend(re.findall(r"[\d,\.]+",txt))
    repl_dict={}
    for i0,u0 in enumerate(replaced):
        key="__item%s__"%i0
        repl_dict[key]=u0
        txt=txt.replace(u0,key)

    #txt=txt.replace(u'\x01'," ")
    txt=txt.replace(u'\u2019',"'")
    
    txt=txt.replace("'s ","_s ")
    txt=txt.replace("'re ","_re ")
    txt=txt.replace("can't ","cann_t ")
    txt=txt.replace("cannot ","can not ")
    txt=txt.replace("n't ","n_t ")
    txt=re.sub("(?u)(\W)",r" \1 ", txt)
    txt=txt.replace("_s ", " 's ")
    txt=txt.replace("_re "," 're ")
    txt=txt.replace("n_t "," n't ")
    for a,b in repl_dict.items():
        txt=txt.replace(a,b)
    
    out=re.split("\s+",txt)
    return [v for v in out if v]

#sentence tokenization
#multi_dot_words=["e.g.","i.e.","U.S.A.","U.K.","O.K."," v."," vs."," v.s.", " et al."," etc.", " al."]
def ssplit(txt):
    #dot_words=["Mr","Ms","Dr","Art","art","Chap","chap","No","no","rev","Rev","Add","para","Para","Paras","paras"]
    for dw in dot_words:
        txt=txt.replace(dw+".",dw+"._")
    for mdw in multi_dot_words:
        #mdw_no_dots=mdw.replace(".","_")  
        mdw_no_dots=mdw.replace(".","_")      
        txt=txt.replace(mdw,mdw_no_dots)
    txt=re.sub(r"\b([A-Z])\. ([A-Z])",r"\1._ \2",txt) #James P. Sullivan

    #txt=re.sub("(?u)([\.\?\!\;\u061b])\s",r"\1\n",txt)
    txt=re.sub("(?u)([\.\?\!\;])\s",r"\1\n",txt)
    txt=txt.replace("\xd8\x9b ","\xd8\x9b\n")
    txt=txt.replace("\xd8\x9f ","\xd8\x9f\n")
    txt=txt.replace("\r","\n")
    txt=txt.replace("\t","\n")
    txt=txt.replace("؛","؛\n")
    txt=txt.replace("؟","؟\n")
    
    txt=txt.replace("._",".")
    for mdw in multi_dot_words:
        mdw_no_dots=mdw.replace(".","_")      
        txt=txt.replace(mdw_no_dots,mdw)

    cur_sents=[v.strip() for v in txt.split("\n")]
    cur_sents=[v for v in cur_sents if v]
    return cur_sents


def ssplit_old(txt): #split a text into sentences
    dot_words=["Mr","Ms","Dr","Art","art","Chap","chap","No","no","rev","Rev","Add"]
    #txt=re.sub("(?u)([\.\?\!\;\u061b])\s",r"\1\n",txt)
    txt=re.sub("(?u)([\.\?\!\;])\s",r"\1\n",txt)
    txt=txt.replace("\xd8\x9b ","\xd8\x9b\n")
    txt=txt.replace("\xd8\x9f ","\xd8\x9f\n")
    cur_sents=[v.strip() for v in txt.split("\n")]
    cur_sents=[v for v in cur_sents if v]
    return cur_sents


def split_sents(segs): #if we have already a list of segments, split each into sentences and return all sentences
    sents=[]
    for seg_id,s0 in enumerate(segs):
        local_sents=ssplit(s0)
        for ls in local_sents:
            if not uc(ls).strip(): continue
            if ls in ['\xe2\x80\x8f']: continue
            sents.append((seg_id,ls))
    return sents

#different tokenization schemes
def tok_uc(txt): #basic tokenization of unicode text - removes all punctuation
    txt=re.sub(r"(?u)(\W)",r" \1 ",txt)
    return [v for v in re.split("\s+",txt) if v]

def tok_zh(zh_txt0):
    tmp_toks=[]
    for n in re.findall(r'[\u4e00-\u9fff]|[^\u4e00-\u9fff]+', zh_txt0):
        if len(n.strip())==1: tmp_toks.append(n.strip())
        else: tmp_toks.extend(tok(n))
    return tmp_toks

def tok_simple(txt,full=False): #this tokenization scheme splits around punctuation - preserving punctuation as tokens
    #txt=txt.replace(u'\x01'," ")
    
    if full: txt=re.sub("(?u)(\W)",r" \1 ", txt)
    else: 
        txt=txt.replace("://","__url__")
        txt=re.sub("^(\W)",r" \1 ", txt)
        txt=re.sub("(\W)$",r" \1 ", txt)    
        txt=re.sub("\s(\W)",r" \1 ", txt)
        txt=re.sub("(\W)\s",r" \1 ", txt)
        txt=re.sub("(\W)(\W)",r" \1 \2", txt)   
        txt=txt.replace("__url__","://")    
    out=re.split("\s+",txt)
    return [v for v in out if v]






######################## BITEXTS ########################
# 21 Dec 2022
def get_html_els(content,tag_name): #identify pairs of html tags for easy and quick matching - would break if number of closing/open tags mismatch - works maily for tr/td tags 
  all_str_list=[]
  el_open_list=list(re.finditer(r'<%s\b.*?>'%tag_name,content))
  el_close_list=list(re.finditer(r'</%s>'%tag_name,content))
  for a0,b0 in zip(el_open_list,el_close_list):
    str0=content[a0.start():b0.end()]
    all_str_list.append(str0)
  return all_str_list

def get_bitext(html_content): #get tr/td and extract bitext
  all_trs=get_html_els(html_content,"tr")
  all_pairs0=[]
  for tr0 in all_trs:
    td_list=get_html_els(tr0,"td")
    href_pair=[]
    pair0=[]
    for td0 in td_list:
      href0=re.findall('href="(.+?)"',td0)+re.findall("href='(.+?)'",td0)
      if href0!=[]: href_pair.append("|".join(href0))
      pair0.append(remove_html(td0))
    if len(pair0)!=2: continue
    if href_pair: all_pairs0.append(href_pair)
    all_pairs0.append(pair0)
  return all_pairs0


def create_tsv(tsv_fpath,list_2d):
  tsv_fopen=open(tsv_fpath,"w")
  for item0 in list_2d:
    line="\t".join([str(v) for v in item0])+"\n"
    tsv_fopen.write(line)
  tsv_fopen.close()


def read_tsv(tsv_fpath):
  out_list=[]  
  tsv_fopen=open(tsv_fpath)
  for line in tsv_fopen:
    items=line.strip().split("\t")
    out_list.append(items)
  tsv_fopen.close()
  return out_list

def process_tsv_content(tsv_content):
  output0=[]
  tsv_content=tsv_content.replace("\r\n","\n")
  lines=tsv_content.split("\n")
  for i0,row0 in enumerate(lines):
    row_split=row0.split("\t")
    row_split=[v.strip() for v in row_split]
    if i0==0:
      headers=row_split
    else:
      row_dict=dict(iter(zip(headers,row_split)))
      output0.append(row_dict)
  return output0



def html_bitext2list(bitext_path):
  fopen=open(bitext_path)
  content=fopen.read()
  fopen.close()
  tr_exp=r"<tr\b.*?>"
  td_exp=r"<td\b.*?>"
  all_trs=[]
  split_content=re.split(tr_exp,content)
  for sc in split_content[1:]:
    tr=sc.split("</tr")[0]
    if tr.count("</td>")!=2: continue
    tr_split=re.split(td_exp,tr)
    tds=[]
    for tr_0 in tr_split[1:]:
      cur_td=tr_0.split("</td>")[0]
      cur_td_no_tags=remove_tags(cur_td)
      tds.append(cur_td_no_tags)
    #if not "</td>" in tr: continue
    all_trs.append(tds)
  return all_trs  

def tsv_bitext2list(tsv_fpath):
  items=[]
  fopen=open(tsv_fpath)
  for line in fopen:
    line_split=line.strip("\n\r").split("\t")
    if len(line_split)!=2: continue
    src,trg=line_split
    if src.strip()=="" or trg.strip()=="": continue
    items.append([src,trg])
  return items

###################### ARABIC - CLEANING ####################
stop_words=['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn',"would"]
alef_lam=u'\u0627\u0644'
waw=u'\u0648'
ba2=u'\u0628'
lam=u'\u0644'
kaf=u'\u0643'
ta2=u'\u062a'
qaf=u'\u0642'
ya2=u'\u064a'
alef_hamza=u'\u0623'
alef_kasra=u'\u0625'
alef=u'\u0627'

#print "testing"
def remove_diactitics(ar_txt): #arabic unicode text - removes also tatweel
    output=re.sub(u'[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\ufc62]','',ar_txt)
    return output


def from_hindi(txt): #arabic unicode text
    for i in range(10):
        num_str=str(i)
        hindi_str=chr(i+1632)
        txt=txt.replace(hindi_str,num_str)
    return txt

def norm_lam_alef(ar_txt_uc):
    ar_txt_uc=ar_txt_uc.replace(u"\ufef9",lam+alef_kasra)
    ar_txt_uc=ar_txt_uc.replace(u'\ufef7',lam+alef_hamza)
    ar_txt_uc=ar_txt_uc.replace(u'\ufefb',lam+alef)    
    return ar_txt_uc

# Clean Arabic Text from diacritics and tatweel
def clean_ar(ar_txt): #unicode text

    output=remove_diactitics(ar_txt)
    output=from_hindi(output)
    output=output.replace('/ ','/')
    output=norm_lam_alef(output)
    output=output.replace('\u200f',"").replace('\u200e',"")

    #output=re.sub("(\d) (\d)",r"\1\2",output) #to normalize the string of the numbers to their bare value
    #output=output.strip()
    return output

def clean_digit_comma(en_txt): #unicode - to normalize all numbers to their value
    #output=re.sub("(\d),(\d)",r"\1\2",en_txt)
    output=en_txt
    return output

def remove_html(el_outer_html): #remove html tags
  inner=re.sub('<([^<>]*?)>',"",el_outer_html)
  return inner

def clean_html_OLD(html_str):
    html = re.sub("[\n\r\t]+", " ", html_str)
    html=htmlp.unescape(html.decode("utf-8")) #remove html entities
    html=html.encode("utf-8")
    html=re.sub("(<!--.*?-->)", "", html) #remove HTML comments
    html = re.sub('(?i)<script.*?</script>', '', html) #remove javascript
    html = re.sub('(?i)<style.*?</style>', '', html) #remove css
    notags = re.sub("<.*?>", "  ", html) #remove tags
    return notags



##################### FILES ##################
def append2file(item,fpath): #add line to file
  file_open=open(fpath,"a")
  if item[-1]!="\n": item+="\n"
  file_open.write(item)
  file_open.close()  

def read(fpath):
    file_open=open(fpath)
    content=file_open.read()
    file_open.close()
    return content

def read_json(fpath):
    with open(fpath) as file_open0:
        cur_dict0=json.load(file_open0)
    return cur_dict0

#6 Nov 2023
def remove_dupl(fpath): #remove duplicate lines from a file
  temp_fpath=fpath+"0"
  seen = set()
  with open(fpath, 'r') as fin, open(temp_fpath, 'w') as fout:
    for line in fin:
      h = hash(line)
      if h not in seen:
        fout.write(line)
        seen.add(h)
  shutil.copy(temp_fpath,fpath)
  os.remove(temp_fpath)


####################### PICKLE AND SHELVE ######################
# ============= variable Storage (Pickling)
# CPickle
def cpk(var1,file1):
    fopen=open(file1,'wb')
    cPickle.dump(var1,fopen,protocol=2)
    fopen.close()

# UnPickle
def lpk(file1):
    fopen=open(file1,'rb')
    output=cPickle.load(fopen)
    fopen.close()
    return output
#shelve functions
def count_plus(counter_shelve_fpath,count_key="count"):
    shelve_fopen=shelve.open(counter_shelve_fpath)
    cur_count=shelve_fopen.get(count_key,0)
    new_count=cur_count+1
    shelve_fopen[count_key]=new_count
    shelve_fopen.close()
    return cur_count


################## OS FUNCTIONS ##########################
def read_file(fpath0):
    fopen0=open(fpath0)
    content0=fopen0.read()
    fopen0.close()
    return content0


#file operations
def get_file_loc_ratio(ratio,fpath): #get the line start location corresponding to a percentage of file size
  file_size=os.stat(fpath).st_size
  cur_loc0=int(file_size*ratio)
  fopen0=open(fpath)
  fopen0.seek(cur_loc0)
  # fopen0.seek(cur_loc0-1000)
  # prev_chunk=fopen0.read(1000)
  # split_br=prev_chunk.split("\n")

  cur_line=fopen0.readline()
  new_loc0=fopen0.tell()#-len(cur_line) 
  fopen0.close()
  return new_loc0

#read the file from certain percentage to certain percentage - useful for navigating large files
#and also for splitting files to training/dev/test portions
def read_file_from_to(fpath,to_ratio=None,from_ratio=0,from_loc=None,to_loc=None,yield_loc=False,apply_json=False): #process file line by line from start percentage/ratio (e.g. 0%) to an end ratio (e.g. 80%)
  file_size=os.stat(fpath).st_size
  if from_loc==None:
    if from_ratio==0: from_loc=0
    else: from_loc=get_file_loc_ratio(from_ratio,fpath)
  if to_loc==None:
    if to_ratio==None: to_loc=file_size
    else: to_loc=get_file_loc_ratio(to_ratio,fpath)
  fopen0=open(fpath)
  fopen0.seek(from_loc)
  line0="-"
  loc0=fopen0.tell()
  while line0 and loc0<=to_loc:
    temp_loc=loc0
    line0=fopen0.readline()
    loc0=fopen0.tell()
    if line0: 
      out=line0
      if apply_json: out=json.loads(line0)
      if yield_loc: yield temp_loc,out
      else: yield out
      
  fopen0.close()

def get_first_line(fpath):
  fopen0=open(fpath)
  first_line=fopen0.readline()
  fopen0.close()
  return first_line

def get_last_line(fpath,chunk_size=4000):
  if not os.path.exists(fpath): return None
  file_size=os.stat(fpath).st_size
  fopen0=open(fpath)
  fopen0.seek(file_size-chunk_size)
  cur_chunk=fopen0.read(chunk_size)
  chunk_split=[v for v in cur_chunk.split("\n") if v]
  last_line=chunk_split[-1]
  fopen0.close()
  return last_line

def seek_read_line(fpath,seek_to):
  fopen0=open(fpath)
  fopen0.seek(seek_to)
  cur_line=fopen0.readline()
  fopen0.close()
  return cur_line


def read_nlines(fpath,seek_to=0,n_lines=10):
  line_list=[]
  fopen0=open(fpath)
  fopen0.seek(seek_to)
  for _ in range(n_lines):
    cur_line=fopen0.readline()
    cur_pos=fopen0.tell()
    if cur_line=="": break
    line_list.append((cur_line.strip(),cur_pos))

  fopen0.close()
  return line_list


def shuffle_file_lines(input_fpath,output_fpath,n=50):
  shuffled_fopen=open(output_fpath,"w")
  gen_list=[]
  for i0 in range(n):
    start_ratio,end_ratio=round(i0/n,1),round((i0+1)/n,1)
    cur_gen=read_file_from_to(input_fpath,from_ratio=start_ratio,to_ratio=end_ratio,yield_loc=False)
    gen_list.append(cur_gen)
  flag=True
  counter=0
  line_counter=0
  cur_item_list=[]
  while flag==True:
    flag=False
    temp_item_list=[]
    for cur_gen in gen_list:
      try: cur_item=next(cur_gen)
      except StopIteration: cur_item=None
      if cur_item==None or cur_item=="": continue
      temp_item_list.append(cur_item)
    if temp_item_list!=[]: flag=True
    cur_item_list.extend(temp_item_list)
    if len(cur_item_list)>10000:
      random.shuffle(cur_item_list)
      shuffled_fopen.writelines(cur_item_list)
      cur_item_list=[]
    counter+=1#len(cur_item_list)
    line_counter+=len(temp_item_list)
    if counter>0 and counter%10000==0: print(counter,line_counter)
  shuffled_fopen.writelines(cur_item_list)  
  shuffled_fopen.close()
  return line_counter


#iter functions - 10 August 2023
def get_iter_chunks(iterator,chunk_size,min_i=None): #iterate certain chunk size over an iterable, with a limit min_i, excluding all iterations before
  cur_chunk=[]
  item_i=0
  while True:
    try: cur_item=next(iterator)
    except StopIteration: cur_item=None
    if min_i!=None and item_i<min_i:
      item_i+=1  
      continue
    if cur_item!=None: cur_chunk.append(cur_item)
    if len(cur_chunk)==chunk_size or cur_item==None:
      yield cur_chunk
      cur_chunk=[]
    if cur_item==None: break
    item_i+=1

#file write opertation
def append_line(text0,fpath0): #append a line to text file
  fopen0=open(fpath0,"a")
  text0=text0.replace("\n"," ")
  fopen0.write(text0+"\n")
  fopen0.close()

#OS functions
def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def get_dir_files(dir_path0,extension=None):
  all_files=[]
  for root0,dir0,files0 in os.walk(dir_path0):
    for fname in files0:
      cur_fpath=os.path.join(root0,fname)
      if extension!=None and not fname.endswith("."+extension): continue
      all_files.append(cur_fpath)
  return all_files

#https://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            #return stat.st_mtime
            return stat.st_ctime


#This is the main function to crawl into the directory structure and extract files of a particular type
#It can be set to get the files modified between start_mtime and end_mtime
#if these values are set to None, the function gets all the files under this directory with the specified filetype
def list_dir(dir_path, start_mtime=None, end_mtime=None, output_file='',file_type='doc'):
    all_files=[]
    
    walk=os.walk(dir_path)
    counter=0
    for folder_path, folders, files in walk:
        folder_mtime=os.stat(folder_path).st_mtime
        if start_mtime!=None and folder_mtime<start_mtime:
            continue
        for i,f in enumerate(files):
             
            if not f.lower().endswith(file_type):
                continue
            file_path=os.path.join(folder_path,f)
            try:
                file_mtime=os.stat(file_path).st_mtime
                if start_mtime!=None and file_mtime<start_mtime:
                    continue
                elif end_mtime!=None and file_mtime>end_mtime:
                    continue
                else:
                    counter+=1
                    if counter%100==0:
                        print(counter)
                    all_files.append(file_path)
                    #print file_path, time.ctime(file_mtime)
                    #all_files.append([file_path, time.ctime(file_mtime)])
                    # line='%s\n'%(file_path)
                    # fopen.write(line)
            except:
                pass
    if output_file!="":
      fopen=open(output_file,'w')
      for file_path in all_files:
        line='%s\n'%(file_path)
        fopen.write(line)
      fopen.close()
    return all_files


def file_len(fpath0): #get the number of lines in the cache file
  if not os.path.exists(fpath0): return 0
  with open(fpath0) as fopen:
    for i0,f0 in enumerate(fopen): pass
  return i0+1


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



########################## ZIP FILES ##################
###Utilities - zip files functions copy to general soon

import os, tempfile, json, zipfile

def write_lines_tmp(line_item_list0):
  tmp = tempfile.NamedTemporaryFile(delete=False)
  cur_path0=""
  try:
    cur_path0=tmp.name
    for it in line_item_list0:
      if len(line_item_list0)==1: cur_str=it#"%s\n"%it
      else: cur_str="%s\n"%it
      tmp.write(cur_str.encode("utf-8"))
  finally:
    tmp.close()
  return cur_path0

def write_files2zip(zip_fpath0,file_content_list0):
  zf0 = zipfile.ZipFile(zip_fpath0, "w",zipfile.ZIP_DEFLATED)
  for f_name0,f_lines0 in file_content_list0:
    tmp_fpath0=write_lines_tmp(f_lines0)
    zf0.write(tmp_fpath0, "/%s"%f_name0)
    os.remove(tmp_fpath0)
  zf0.close()
  print("zipped successfully:", zip_fpath0)

def read_zip_file_full(zip_fpath0,zipped_file_name0):
  archive0 = zipfile.ZipFile(zip_fpath0, 'r')
  target_file = archive0.open(zipped_file_name0)
  output=target_file.read()
  archive0.close()
  return output.decode("utf-8")

def read_zip_lines(zip_fpath0,zipped_file_name0): #iterate line by line of a target zipped file
  archive0 = zipfile.ZipFile(zip_fpath0, 'r')
  target_file = archive0.open(zipped_file_name0)
  for a in target_file:
    output=a.decode("utf-8")
    yield output #a.decode("utf-8")
  archive0.close()
  return 

# def iter_zipfile(zip_file_obj,zipped_file_name0=None):
#   pass

def read_zip_one_line(zip_fpath0,zipped_file_name0): #just the first line in the target zipped file
  archive0 = zipfile.ZipFile(zip_fpath0, 'r')
  target_file = archive0.open(zipped_file_name0)
  for a in target_file:
    output=a.decode("utf-8")
    break
  archive0.close()
  return output

def zip_files(file_paths,zip_fpath):
  compression = zipfile.ZIP_DEFLATED
  # create the zip file first parameter path/name, second mode
  zf = zipfile.ZipFile(zip_fpath, mode="w")
  try:
    for fpath0 in file_paths:
      fname=os.path.split(fpath0)[-1]
      zf.write(fpath0, fname, compress_type=compression)
  except FileNotFoundError:
    print("An error occurred")
  finally:
    # Don't forget to close the file!
    zf.close()
#===================================
####################### Sequences - Paths OTHERS #####################
def djk(pt0,pt1,transition_dict0,pt_list0=None):
  path_wt_dict0={}
  prev_dict0={}
  if pt_list0==None: pt_list0=list(transition_dict0.keys())
  for cur_pt in pt_list0:
    following_dict0=transition_dict0.get(cur_pt,{})
    found_cur_path_wt=path_wt_dict0.get(cur_pt,0)
    for next_pt,next_wt in following_dict0.items():
      combined_wt=found_cur_path_wt+next_wt
      found_next_wt=path_wt_dict0.get(next_pt,0)
      if combined_wt>found_next_wt:
        path_wt_dict0[next_pt]=combined_wt
        prev_dict0[next_pt]=cur_pt
  cur_pt=pt1
  out_path=[]
  while cur_pt!=None:
    out_path.append(cur_pt)
    if cur_pt==pt0: break
    cur_pt=prev_dict0.get(cur_pt)
  out_path=list(reversed(out_path))
  return out_path, path_wt_dict0.get(pt1)

def match_seq(list1,list2):
    output=[]
    s = SequenceMatcher(None, list1, list2)
    blocks=s.get_matching_blocks()
    for bl in blocks:
        #print(bl, bl.a, bl.b, bl.size)
        for bi in range(bl.size):
            cur_a=bl.a+bi
            cur_b=bl.b+bi
            output.append((cur_a,cur_b))
    return output


def get_seq_edits(tokens1,tokens2):
  match_obj=SequenceMatcher(None,tokens1,tokens2)
  final_list=[]
  for a in match_obj.get_opcodes():
    match_type,x0,x1,y0,y1=a
    if match_type=="delete":
      #print("deleted",tokens1[x0:x1])
      final_list.append(("deleted",tokens1[x0:x1]))
    if match_type=="equal":
      #print("equal",tokens1[x0:x1])
      final_list.append(("equal",tokens1[x0:x1]))
    if match_type=="replace":
      final_list.append(("delete",tokens1[x0:x1]))
      final_list.append(("insert",tokens2[y0:y1]))
    if match_type=="insert":
      final_list.append(("insert",tokens2[y0:y1]))
  return final_list

def make_html_safe(text):
  text=text.replace(">","&gt;").replace("<","&lt;")
  return text

def get_edit_html(tokens1,tokens2):
  edit_list=get_seq_edits(tokens1,tokens2)
  final_str_items=[]
  for edit_type0,chunk0 in edit_list:
    cur_chunk_str=de_tok2str(chunk0)
    cur_chunk_str=make_html_safe(cur_chunk_str)
    if edit_type0=="delete": final_str_items.append('<del>%s</del>'%cur_chunk_str) 
    elif edit_type0=="insert": final_str_items.append('<ins>%s</ins>'%cur_chunk_str) 
    else: final_str_items.append(cur_chunk_str) 
  final_str=" ".join(final_str_items)
  return final_str



def segmenting(html_content):
    segs=[v.strip() for v in re.findall('>([^<>]*?)<', html_content)]
    segs=[v for v in segs if v]
    return segs

#dict-trie functions
def add2trie(cur_trie,items,val,terminal_item=""):
    new_trie=cur_trie
    for it in items:
        new_trie = new_trie.setdefault(it, {})
    new_trie[terminal_item]=val
    return cur_trie

def walk_trie(cur_trie,items,terminal_item=""):
    new_trie=cur_trie
    for it in items:
        test=new_trie.get(it)
        if test==None: return None
        new_trie = test
    val=new_trie.get(terminal_item)
    return val

if __name__=="__main__":
    print("Hello!")
    our_trie={}
    seq=["I","think"]
    val=1
    our_trie=add2trie(our_trie,seq,val)
    seq=["I","love","her"]
    val=5
    our_trie=add2trie(our_trie,seq,val)
    seq=["where","is","he"]
    val=3
    our_trie=add2trie(our_trie,seq,val)
    seq=["where","are","we"]
    val=2

    our_trie=add2trie(our_trie,seq,val)
  
    print(our_trie)
    val0=walk_trie(our_trie,["where","are","they"])

    list1=["orange","apple","lemons","grapes"]
    list2=["pears", "orange","apple", "lemons", "cherry", "grapes"]
    for a,b in match_seq(list1,list2):
        print(a,b, list1[a],list2[b])


    #print val0
