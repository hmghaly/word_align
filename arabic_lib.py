import os, sys, time, shelve, json
from itertools import groupby
#sys.path.append("../utils")

#from general import *

#https://github.com/hmghaly/word_align/edit/master/arabic_lib.py



def tok_uc(txt):
    txt=re.sub(r"(?u)(\W)",r" \1 ",txt)
    return [v for v in re.split("\s+",txt) if v]

#Current POS tags in Arabic
pos_tags=[("NN", "Noun"),
          ("VB", "Verb"),
          ("JJ", "Adjective"),
          ("IN", "Preposition"),
          ("DEM", "Demonstrative"),
          ("C", "Complementizer"),
          ("PRO", "Pronoun"),
          ("O", "Other")] 

pos_tags_label_dict=dict(iter(pos_tags))


#MAIN Arabic data and functions
ar_letters="أاآإبتثجحخدذرزسشصضطظعغفقكلمنهويىءئؤ"
alif_prefix=["أ"]
alif_next_prefixes=["و","ف","س",""]
seen_prefix=["س"]
laam_prefix=["ل"]
al_prefix=["ال"]
ll_prefix=["لل"]
alif_laam_zero_prefixes=["و","ف",""]
alif_laam_one_prefixes=["ب","ك",""]

zero_prefixes=["و","ف",""]
one_prefixes=["ب","ك","ل",""]
all_prefixes=["0", "أ","ب","ك","ل","ف","و","س","لل","ال"]

conversion_list=[("ال","al"),("لل","ll"),("أ","a"),("ب","b"),("س","s"),("ف","f"),("ك","k"),("ل","l"),("و","w"),("ه","h"),("م","m"),("ن","n"),("ا","a"),("ي","y"), ("ت","t"),("ة","h")]

def convert_en2ar(en_str):
  for a,b in conversion_list:
    en_str=en_str.replace(b,a)
  return en_str

def convert_ar2en(ar_str):
  for a,b in conversion_list:
    ar_str=ar_str.replace(a,b)
  return ar_str


suffixes=["", "ي","ني","نا","ك","كم","كما","كن","ه","هم","هما","هن","ها"]
jalala_word=["الله","لله"]
alif_laam_words=["الذي","التي","اللذان","اللتان","اللذين","اللتين", "الذين","اللاتي","اللائي","اللواتي"]
ism_mawsool=alif_laam_words+["ما"]
ism_ishara=["هذا","هذه","هذان","هذين","هاتان","هاتين","هؤلاء","ذلك","تلك","أولئك"]
jarr=["في","على","من","عن","إلى","حتى","منذ","مع"]
pronouns=["أنا","نحن","أنت","أنتما","أنتم","أنتن","هو","هي","هما","هم","هن"]

stem_additions=["ان","ون","ين","ا","و","ي","ات","ة","وا","ت","ن",""] #for plural,dual and female, tanween, conjugations, to do basic stemming

laam_laam_words=[]
laam_laam_dict={}
laam_laam_dict["لله"]="الله"
for v in alif_laam_words:
  if "لل" in v: form = v[1:]
  else: form= "ل"+v[1:]
  laam_laam_dict[form]=v
  laam_laam_words.append(form)

combined_laam_words=jalala_word+alif_laam_words+laam_laam_words


alif_combinations=[a+b for a in alif_prefix for b in alif_next_prefixes]
simple_combinations=[a+b for a in alif_laam_zero_prefixes for b in one_prefixes]
alif_laam_combinations=[a+b+c for a in alif_laam_zero_prefixes for b in alif_laam_one_prefixes for c in al_prefix]
laam_laam_combinations=[a+b for a in alif_laam_zero_prefixes for b in ll_prefix]
seen_combinations=[a+b for a in alif_laam_zero_prefixes for b in seen_prefix]
all_prefix_combinations=alif_combinations+simple_combinations+alif_laam_combinations+laam_laam_combinations+seen_combinations

#now we get the codes for each NLP category, in latin letters
cur_prefixes=[convert_ar2en(v) for v in all_prefix_combinations]
ll0_prefixes=[]
for cp in cur_prefixes:
  if cp.endswith("ll"): ll0_prefixes.append(cp+"0")
cur_prefixes.extend(ll0_prefixes)
cur_suffixes=[convert_ar2en(v) for v in suffixes]
cur_additions=[convert_ar2en(v) for v in stem_additions]
cur_pos_tags=[v[0] for v in pos_tags]



def get_pre_suf_candidates(word1):
  valid_prefixes=[]
  valid_suffixes=[]
  for apc in all_prefix_combinations:
    if word1.startswith(apc): valid_prefixes.append(apc)
  for asc in suffixes:
    if word1.endswith(asc): valid_suffixes.append(asc)
  pre_suf_candidates=[]
  for vs in valid_suffixes:
    for vp in valid_prefixes:
      stem=word1[len(vp):len(word1)-len(vs)]
      label=convert_ar2en(vp)+"-"+convert_ar2en(vs)
      pre_suf_candidates.append((vp,stem,vs,label))
      original_laam_word=laam_laam_dict.get(stem,"")
      #print("original_laam_word",original_laam_word, ">>>", stem)
      if original_laam_word:
        stem=original_laam_word
        vp+="ل"
        label=convert_ar2en(vp)+"-"+convert_ar2en(vs)
        pre_suf_candidates.append((vp,stem,vs,label))

      if "لل" in vp and not "0" in vp:
        vp+="0"
        stem="ل"+stem
        label=convert_ar2en(vp)+"-"+convert_ar2en(vs)
        pre_suf_candidates.append((vp,stem,vs,label))
  return pre_suf_candidates


#STEP -1 : get a raw analysis of all prefixes and suffixes
def get_pre_suf_candidates(word1): #this is the main function to get the candidates without sorting them
  valid_prefixes=[]
  valid_suffixes=[]
  for apc in all_prefix_combinations:
    if word1.startswith(apc): valid_prefixes.append(apc)
  for asc in suffixes:
    if word1.endswith(asc): valid_suffixes.append(asc)
  pre_suf_candidates=[]
  for vs in valid_suffixes:
    for vp in valid_prefixes:
      stem=word1[len(vp):len(word1)-len(vs)]
      label=convert_ar2en(vp)+"-"+convert_ar2en(vs)
      pre_suf_candidates.append((vp,stem,vs,label))
      original_laam_word=laam_laam_dict.get(stem,"")
      #print("original_laam_word",original_laam_word, ">>>", stem)
      if original_laam_word:
        stem=original_laam_word
        vp+="ل"
        label=convert_ar2en(vp)+"-"+convert_ar2en(vs)
        pre_suf_candidates.append((vp,stem,vs,label))

      if "لل" in vp and not "0" in vp:
        vp+="0"
        stem="ل"+stem
        label=convert_ar2en(vp)+"-"+convert_ar2en(vs)
        pre_suf_candidates.append((vp,stem,vs,label))
  return pre_suf_candidates


#STEP 2 - get the counts of the root for each pre-suf combination, filter out the combinations that don't make sense by giving them zero weight
def sort_filter(cur_candidates,cur_counter_dict={}): #preliminary sort of candidates based on stem count and other ad-hoc criteria 
  sortable=[]
  for item in cur_candidates:
    pre,stem, suf,label = item
    if len(stem)<2: wt=0
    elif "ال" in pre and suf!="": wt=0
    elif "س" in pre and not stem[0] in "سيتن": wt=0
    else: wt=cur_counter_dict.get(stem,0)
    sortable.append((item,wt))
  sortable.sort(key=lambda x:-x[-1])
  # for s in sortable:
  #   print(s)
  return [v[0] for v in sortable]

#Main Function
def ar_pre_suf(ar_word,cur_ar_counter_dict={}): #THIS IS THE MOST IMPORTANT FUNCTION - it gives sorted combinations of possible candidates of prefixes and suffixes
  candidates=get_pre_suf_candidates(ar_word)
  sorted_candiates=sort_filter(candidates,cur_ar_counter_dict)
  new_sorted_candiates=[]
  for sc in sorted_candiates:
    utf_item=[sc0.encode("utf-8") for sc0 in sc]
    new_sorted_candiates.append(utf_item)
    #print(utf_item)
  return sorted_candiates


def anayze_pre(prefix_str): #This will be useful when extracting features
  cur_pre=[]
  if "ال" in prefix_str:
    cur_pre.append("ال")
    prefix_str=prefix_str.replace("ال","")
  if "لل" in prefix_str:
    cur_pre.append("لل")
    prefix_str=prefix_str.replace("لل","")
  for ps in prefix_str: cur_pre.append(ps)
  return cur_pre


def load_counts(counts_txt_fpath, tmp_count_dict={}): #tab separated counts txt to count dict - we can combine counts from different corpora by using the count dict from other corpora
  
  tmp_fopen=open(counts_txt_fpath)
  for f in tmp_fopen:
    f_split=f.strip("\n\r").split("\t")
    if len(f_split)!=2: continue
    word,count=f_split
    count=int(count)
    tmp_count_dict[word]=tmp_count_dict.get(word,0)+ count
    if word[-1]=="ة": 
      new_word=word[:-1]+"ت"
      tmp_count_dict[new_word]=tmp_count_dict.get(new_word,0)+count
    if word[-1]=="ى": 
      new_word=word[:-1]+"ي"
      tmp_count_dict[new_word]=tmp_count_dict.get(new_word,0)+count
      new_word=word[:-1]+"ا"
      tmp_count_dict[new_word]=tmp_count_dict.get(new_word,0)+count
    if word[-1]=="ء": 
      new_word=word[:-1]+"ئ"
      tmp_count_dict[new_word]=tmp_count_dict.get(new_word,0)+count
      new_word=word[:-1]+"ؤ"
      tmp_count_dict[new_word]=tmp_count_dict.get(new_word,0)+count
    if word[-2:]=="وا": 
      new_word=word[:-1]
      tmp_count_dict[new_word]=tmp_count_dict.get(new_word,0)+count

  tmp_fopen.close()
  return tmp_count_dict




def analyze_stem(cur_word,cur_ar_counter_dict={}): #get the stem addition possibilities based on their counts to facilitate further annotation
  possibilities=[]
  for sa in stem_additions:
    if cur_word.endswith(sa):
      stemmed_word=cur_word[:len(cur_word)-len(sa)]
      if len(stemmed_word)<2: freq=0
      else: freq=cur_ar_counter_dict.get(stemmed_word,0)
      possibilities.append((sa,freq))
    else: possibilities.append((sa,0))
  possibilities.sort(key=lambda x:(-x[-1],len(x[0])))
  # for p in possibilities:
  #   print(p)
  return [v[0] for v in possibilities]

pos_tags=[("NN", "Noun"),
          ("VB", "Verb"),
          ("JJ", "Adjective"),
          ("IN", "Preposition"),
          ("DEM", "Demonstrative"),
          ("C", "Complementizer"),
          ("PRO", "Pronoun"),
          ("O", "Other")] 

pos_tags_label_dict=dict(iter(pos_tags))

def analyze_pos(pre,root,suf): #put tentative weights to POS tags to facilitate further annotation
  tmp_pos_dict={}
  for pt in pos_tags_label_dict:
    tmp_pos_dict[pt]=0
  tmp_pos_dict["NN"]+=0.1
  tmp_pos_dict["VB"]+=0.1
  tmp_pos_dict["JJ"]+=0.1
  tmp_pos_dict["O"]+=0.05
  if len(root)<2: tmp_pos_dict["O"]+=1

  if "ال" in pre:
    tmp_pos_dict["NN"]+=1
    tmp_pos_dict["JJ"]+=1
  elif "لل" in pre:
    tmp_pos_dict["NN"]+=1
  elif "ل" in pre:
    tmp_pos_dict["NN"]+=1
    tmp_pos_dict["VB"]+=1

  if "ب" in pre:
    tmp_pos_dict["NN"]+=1
  
  if root.endswith("وا"):
    tmp_pos_dict["VB"]+=1

  if "س" in pre:
    tmp_pos_dict["VB"]+=1
  if root.endswith("ة") or root.endswith("ات"):
    tmp_pos_dict["NN"]+=1
    tmp_pos_dict["JJ"]+=1
  if root in ism_mawsool:
    tmp_pos_dict["C"]+=1
  if root in ism_ishara:
    tmp_pos_dict["DEM"]+=1
  if root in jarr:
    tmp_pos_dict["IN"]+=1
  if root in pronouns:
    tmp_pos_dict["PRO"]+=1
  pos_list=[]
  for pt in pos_tags_label_dict:
    pos_wt=tmp_pos_dict[pt]
    pos_label=pos_tags_label_dict[pt]
    pos_list.append((pos_label,pt,pos_wt))
  pos_list.sort(key=lambda x:-x[-1])
  # for pl in pos_list:
  #   print(pl)
  return [v[:-1] for v in pos_list]

#===========================


waw=u'\u0648'
fa2=u'\u0641'
alef_hamza=u'\u0623'
prefixes_zero=[alef_hamza,waw,fa2,""]
ba2=u'\u0628'
lam=u'\u0644'
kaf=u'\u0643'
seen=u'\u0633'
lam_lam=u'\u0644\u0644'
prefixes_one=[ba2,kaf,""]
#prefixes_one=[ba2,""] #we should include also kaf, but it seems more probelamtic, so we can ignore it for now, and we can also include alef hamza for questions, but even more problematic
prefixes_one_add=[seen,lam,lam_lam] #we put them separately because they can't be followed by alef-lam
alef_lam=u'\u0627\u0644'
prefixes_two=[alef_lam,""]

ta2=u'\u062a'
ya2=u'\u064a'

noon=u'\u0646'
modare3_initials=[ta2,ya2,alef_hamza,noon]

ta2_marboota=u'\u0629'
alef_layyena=u'\u0649'
hamza_nabra=u'\u0626'
hamza_waw=u'\u0624'
hamza=u'\u0621'

alef=u'\u0627'
alef_ta2=u'\u0627\u062a'
if sys.version[0]=="2": tatweel=unichr(1600)
else: tatweel=chr(1600)


#print "tatweel", tatweel, [tatweel]

#exit()
#alef_kasra=u'\u0625'

#qaf=u'\u0642'

# If we need more letters
# for i in range(1500,1700):
# 	print i, unichr(i),[unichr(i)]

def is_arabic(word_uc):
	if not word_uc: return False
	if ord(word_uc[0])>1560 and ord(word_uc[0])<1700: return True
	return False

def expand_root(word):
	forms=[word]
	if word[-1] in [hamza_nabra,hamza_waw]: forms.append(word[:-1]+hamza)
	if len(word)>2 and word[-1] in [ya2] and word[-2]!=alef: forms.append(word[:-1]+alef_layyena)
	if len(word)>2 and word[-1] in [ta2] and word[-2]!=alef: forms.append(word[:-1]+ta2_marboota)
	if len(word)>2 and word[-1] in [ta2] and word[-2]!=alef: forms.append(word[:-1])
	if word[-1] ==alef: forms.append(word[:-1])
	return forms

def morph_word(word,in_freq_dict): #split the word morphologically to different prefixes and possible suffix
	if not is_arabic(word) or word.isdigit() or len(word)<2: return [word]
	cand_found=get_candidates_ar(word)
	#print ">>>> word", word
	cand_list=[]
	for can in cand_found:
		cur_pre,cur_root,cur_suf=can
		cand_list.append((can, in_freq_dict.get(cur_root,0)))
		#print cur_pre,cur_root,cur_suf, freq_dict.get(cur_root,0), cur_wt
	cand_list.sort(key=lambda x:(-x[-1],-len(can[1])))
	can_top,can_count=cand_list[0]
	cur_pre,cur_root,cur_suf=can_top
	split_pre=pre_dict.get(cur_pre,[])
	final_tokens=[]
	for sp in split_pre:
		if not sp: continue
		if sp==lam_lam:  
			final_tokens.append(lam+tatweel)
			final_tokens.append(alef_lam+tatweel)
		else: final_tokens.append(sp+tatweel)
	final_tokens.append(cur_root)
	if cur_suf: final_tokens.append(tatweel+cur_suf)
	return final_tokens
	#print " ".join(final_tokens)


def tok_ar(ar_sent_uc,in_freq_dict):
	cleaned_sent=clean_ar(ar_sent_uc)
	ar_tokens=tok_uc(cleaned_sent)
	final_tokens=[]
	for ar0 in ar_tokens:
		final_tokens.extend(morph_word(ar0,in_freq_dict))
	return final_tokens


#print arabic_stopwords
stopwords_ar=ar_stopwords=arabic_stopwords=[u'\u0627\u0644\u0644\u0647', u'\u0644\u0644\u0647', u'\u0639\u0628\u0631', u'\u0644\u062f\u0649', u'\u0639\u0646\u062f', u'\u0628\u064a\u0646', u'\u0639\u0646', u'\u0645\u0639', u'\u0641\u064a', u'\u0639\u0644\u0649', u'\u0645\u0646', u'\u0625\u0644\u0649', u'\u0628\u0634\u0623\u0646', u'\u0647\u0630\u0627', u'\u0647\u0630\u0647', u'\u0647\u0627\u0630\u0627\u0646', u'\u0647\u0630\u0627\u0646', u'\u0647\u0627\u062a\u0627\u0646', u'\u0647\u0627\u0630\u064a\u0646', u'\u0647\u0627\u062a\u064a\u0646', u'\u0647\u0624\u0644\u0627\u0621', u'\u0623\u0648\u0644\u0626\u0643', u'\u0630\u0644\u0643', u'\u062a\u0644\u0643', u'\u062a\u0644\u0643\u0645\u0627', u'\u062a\u0644\u0643\u0645\u0627', u'\u0642\u062f', u'\u0644\u0645', u'\u0644\u0627', u'\u0644\u0646', u'\u0633\u0648\u0641', u'\u0625\u0630\u0627', u'\u0625\u0630\u0627', u'\u0625\u0630', u'\u0623\u062b\u0646\u0627\u0621', u'\u062e\u0644\u0627\u0644', u'\u0645\u0646\u0630', u'\u0628\u0639\u062f', u'\u0642\u0628\u0644', u'\u0627\u0644\u0630\u064a', u'\u0627\u0644\u062a\u064a', u'\u0627\u0644\u0630\u064a\u0646', u'\u0627\u0644\u0644\u0627\u062a\u064a', u'\u0627\u0644\u0644\u0627\u0626\u064a', u'\u0627\u0644\u0644\u0630\u0627\u0646', u'\u0627\u0644\u0644\u062a\u0627\u0646', u'\u0627\u0644\u0644\u0630\u064a\u0646', u'\u0627\u0644\u0644\u062a\u064a\u0646', u'\u0646\u062d\u0648', u'\u0625\u0646', u'\u0625\u0646', u'\u0623\u0646', u'\u0625\u0646', u'\u062b\u0644\u0627\u062b', u'\u0623\u0631\u0628\u0639', u'\u062e\u0645\u0633', u'\u0633\u062a', u'\u0633\u0628\u0639', u'\u062b\u0645\u0627\u0646', u'\u062b\u0645\u0627\u0646\u064a', u'\u062a\u0633\u0639', u'\u0639\u0634\u0631', u'\u062b\u0644\u0627\u062b\u0629', u'\u0623\u0631\u0628\u0639\u0629', u'\u062e\u0645\u0633\u0629', u'\u0633\u062a\u0629', u'\u0633\u0628\u0639\u0629', u'\u062b\u0645\u0627\u0646\u064a\u0629', u'\u062a\u0633\u0639\u0629', u'\u0639\u0634\u0631\u0629', u'\u062b\u0645\u0629', u'\u0647\u0646\u0627\u0643', u'\u0647\u0646\u0627', u'\u0647\u0646\u0627\u0644\u0643', u'\u0644\u0630\u0644\u0643', u'\u062f\u0648\u0646', u'\u0643\u0644', u'\u062c\u0645\u064a\u0639', u'\u0643\u0627\u0641\u0629', u'\u0648\u0641\u0642', u'\u062d\u0633\u0628', u'\u0645\u0627', u'\u0645\u0627', u'\u0645\u0645\u0627', u'\u0643\u064a\u0641\u0645\u0627', u'\u0648\u0642\u062a\u0645\u0627', u'\u0623\u064a\u0646\u0645\u0627', u'\u062d\u0633\u0628\u0645\u0627', u'\u062d\u064a\u062b\u0645\u0627', u'\u0641\u064a\u0645\u0627', u'\u0639\u0645\u0627', u'\u0646\u0641\u0633', u'\u0644\u064a\u0633', u'\u0644\u064a\u0633\u062a', u'\u0644\u064a\u0633\u0627', u'\u0644\u064a\u0633\u0648\u0627', u'\u0644\u0633\u0646', u'\u0644\u0633\u062a', u'\u0647\u0644', u'\u0645\u0627\u0630\u0627', u'\u0645\u062a\u0649', u'\u0623\u064a\u0646', u'\u0623\u0646\u0649', u'\u0643\u064a\u0641', u'\u0643\u0645', u'\u0623\u0646\u0627', u'\u0623\u0646\u062a\u0645', u'\u0623\u0646\u062a\u0645\u0627', u'\u0623\u0646\u062a\u0645', u'\u0623\u0646\u062a\u0646', u'\u0647\u0648', u'\u0647\u064a', u'\u0647\u0645\u0627', u'\u0647\u0645', u'\u0647\u0646', u'\u0646\u062d\u0646', u'\u0623\u064a', u'\u0623\u064a', u'\u0623\u064a\u0629', u'\u0623\u064a\u0636\u0627', u'\u0643\u0630\u0644\u0643', u'\u0643\u0627\u0646', u'\u0643\u0627\u0646\u062a', u'\u0643\u0627\u0646\u0627', u'\u0643\u0627\u0646\u0648\u0627', u'\u0643\u0646', u'\u0643\u0646\u062a', u'\u0631\u063a\u0645', u'\u0630\u0627\u062a', u'\u0630\u0648', u'\u0630\u064a', u'\u0630\u0627', u'\u0630\u0648\u064a', u'\u0630\u0648\u0627\u062a', u'\u0625\u0644\u0627', u'\u0623\u0645', u'\u0639\u062f\u0645', u'\u0642\u0627\u0645', u'\u0642\u0627\u0645\u062a', u'\u0642\u0627\u0645\u0627', u'\u0642\u0627\u0645\u0648\u0627', u'\u0642\u0645\u0646', u'\u0642\u0645\u062a', u'\u064a\u0642\u0648\u0645', u'\u062a\u0642\u0648\u0645', u'\u0623\u0642\u0648\u0645', u'\u062a\u0642\u0645', u'\u062a\u0642\u0648\u0645\u0648\u0646', u'\u062a\u0642\u0645\u0646', u'\u062a\u0645', u'\u062a\u0645\u062a', u'\u064a\u062a\u0645', u'\u062a\u062a\u0645', u'\u0639\u062f\u0629', u'\u0628\u0636\u0639\u0629', u'\u0628\u0636\u0639', u'\u0639\u0627\u0645', u'\u0623\u0643\u062b\u0631', u'\u0623\u0642\u0644', u'\u0642\u0637', u'\u0628\u0634\u0643\u0644', u'\u0645\u062b\u0644', u'\u0645\u0639\u0638\u0645', u'\u0623\u063a\u0644\u0628', u'\u0628\u0627\u0642\u064a', u'\u0644\u0648', u'\u0644\u0648\u0644\u0627', u'\u0644\u0648\u0644\u0645', u'\u0644\u0643\u0646', u'\u0625\u0646\u064a', u'\u0625\u0646\u0646\u064a', u'\u0623\u0646\u0646\u064a', u'\u0625\u0646\u0647', u'\u0623\u0646\u0647', u'\u0625\u0646\u0647\u0627', u'\u0623\u0646\u0647\u0627', u'\u0625\u0646\u0647\u0645\u0627', u'\u0623\u0646\u0647\u0645\u0627', u'\u0625\u0646\u0647\u0645', u'\u0623\u0646\u0647\u0645', u'\u0625\u0646\u0647\u0646', u'\u0623\u0646\u0647\u0646', u'\u0644\u0643\u0646\u064a', u'\u0644\u0643\u0646\u0646\u064a', u'\u0644\u0643\u0646\u0643', u'\u0644\u0643\u0646\u0643\u0645\u0627', u'\u0644\u0643\u0646\u0643\u0645', u'\u0644\u0643\u0646\u0643\u0646', u'\u0623\u0648', u'\u0628\u0644', u'\u062d\u062a\u0649', u'\u0644\u064a\u062a', u'\u0644\u0639\u0644', u'\u0644\u0639\u0644\u064a', u'\u0644\u0639\u0644\u0643', u'\u0644\u0639\u0644\u0647', u'\u0644\u0639\u0644\u0647\u0627', u'\u0644\u0639\u0644\u0643\u0645\u0627', u'\u0644\u0639\u0644\u0647\u0645', u'\u0644\u0639\u0644\u0647\u0646', u'\u0644\u064a\u062a\u0646\u064a', u'\u0644\u064a\u062a\u0643', u'\u0644\u064a\u062a\u0646\u0627', u'\u0644\u064a\u062a\u0647\u0645', u'\u0644\u064a\u062a\u0647\u0646', u'\u062d\u0633\u0628', u'\u0633\u0648\u0649', u'\u062b\u0645', u'\u0644\u0642\u062f', u'\u0628\u0644\u0649', u'\u0646\u0639\u0645', u'\u0623\u062c\u0644', u'\u062d\u064a\u062b', u'\u0644\u0626\u0646', u'\u0625\u0646\u0645\u0627', u'\u0644\u0645\u0627', u'\u0643\u0644\u0627', u'\u0645\u062b\u0644', u'\u0641\u0648\u0642', u'\u062a\u062d\u062a', u'\u062f\u0627\u062e\u0644', u'\u062e\u0627\u0631\u062c', u'\u062d\u064a\u0646', u'\u0623\u0641\u0644\u0627', u'\u0623\u0639\u0644\u0649', u'\u0623\u0633\u0641\u0644', u'\u0623\u0639\u0644\u0627\u0647', u'\u0623\u062f\u0646\u0627\u0647', u'\u0636\u0645\u0646', u'\u0643\u064a', u'\u0628\u062e\u0644\u0627\u0641', u'\u0628\u0625\u0645\u0643\u0627\u0646', u'\u0642\u062f\u0631', u'\u0623\u0645\u0631', u'\u0623\u0645\u0631\u0627', u'\u0623\u0645\u0648\u0631', u'\u0643\u0645\u0627', u'\u0625\u0630\u0646', u'\u0648', u'\u0633\u064a\u0645\u0627', u'\u0628\u064a\u0646\u0645\u0627', u'\u064a\u0646\u0627\u064a\u0631', u'\u0641\u0628\u0631\u0627\u064a\u0631', u'\u0645\u0627\u0631\u0633', u'\u0625\u0628\u0631\u064a\u0644', u'\u0645\u0627\u064a\u0648', u'\u064a\u0648\u0646\u064a\u0647', u'\u064a\u0648\u0644\u064a\u0647', u'\u0623\u063a\u0633\u0637\u0633', u'\u0633\u0628\u062a\u0645\u0628\u0631', u'\u0623\u0643\u062a\u0648\u0628\u0631', u'\u0646\u0648\u0641\u0645\u0628\u0631', u'\u062f\u064a\u0633\u0645\u0628\u0631', u'\u0643\u0627\u0646\u0648\u0646', u'\u0634\u0628\u0627\u0637', u'\u0628\u062d\u064a\u062b', u'\u0628\u063a\u064a\u0629', u'\u0648\u062c\u0647', u'\u0643\u0627\u0641', u'\u0641\u0642\u0637', u'\u0641\u062d\u0633\u0628', u'\u0628\u064a\u062f', u'\u0628\u0639\u0636', u'\u0628\u0636\u0639\u0629', u'\u0628\u0636\u0639', u'\u0623\u0644\u0641', u'\u0628\u0627\u0621', u'\u0628\u0645\u0648\u062c\u0628']
#stopwords_ar=ar_stopwords=arabic_stopwords=[u'\u0627\u0644\u0644\u0647', u'\u0644\u0644\u0647', u'\u0639\u0628\u0631', u'\u0644\u062f\u0649', u'\u0639\u0646\u062f', u'\u0628\u064a\u0646', u'\u0639\u0646', u'\u0645\u0639', u'\u0641\u064a', u'\u0639\u0644\u0649', u'\u0645\u0646', u'\u0625\u0644\u0649', u'\u0628\u0634\u0623\u0646', u'\u0647\u0630\u0627', u'\u0647\u0630\u0647', u'\u0647\u0627\u0630\u0627\u0646', u'\u0647\u0630\u0627\u0646', u'\u0647\u0627\u062a\u0627\u0646', u'\u0647\u0627\u0630\u064a\u0646', u'\u0647\u0627\u062a\u064a\u0646', u'\u0647\u0624\u0644\u0627\u0621', u'\u0623\u0648\u0644\u0626\u0643', u'\u0630\u0644\u0643', u'\u062a\u0644\u0643', u'\u062a\u0644\u0643\u0645\u0627', u'\u062a\u0644\u0643\u0645\u0627', u'\u0642\u062f', u'\u0644\u0645', u'\u0644\u0627', u'\u0644\u0646', u'\u0633\u0648\u0641', u'\u0625\u0630\u0627', u'\u0625\u0630\u0627', u'\u0625\u0630', u'\u0623\u062b\u0646\u0627\u0621', u'\u062e\u0644\u0627\u0644', u'\u0645\u0646\u0630', u'\u0628\u0639\u062f', u'\u0642\u0628\u0644', u'\u0627\u0644\u0630\u064a', u'\u0627\u0644\u062a\u064a', u'\u0627\u0644\u0630\u064a\u0646', u'\u0627\u0644\u0644\u0627\u062a\u064a', u'\u0627\u0644\u0644\u0627\u0626\u064a', u'\u0627\u0644\u0644\u0630\u0627\u0646', u'\u0627\u0644\u0644\u062a\u0627\u0646', u'\u0627\u0644\u0644\u0630\u064a\u0646', u'\u0627\u0644\u0644\u062a\u064a\u0646', u'\u0646\u062d\u0648', u'\u0625\u0646', u'\u0625\u0646', u'\u0623\u0646', u'\u0625\u0646', u'\u062b\u0644\u0627\u062b', u'\u0623\u0631\u0628\u0639', u'\u062e\u0645\u0633', u'\u0633\u062a', u'\u0633\u0628\u0639', u'\u062b\u0645\u0627\u0646', u'\u062b\u0645\u0627\u0646\u064a', u'\u062a\u0633\u0639', u'\u0639\u0634\u0631', u'\u062b\u0644\u0627\u062b\u0629', u'\u0623\u0631\u0628\u0639\u0629', u'\u062e\u0645\u0633\u0629', u'\u0633\u062a\u0629', u'\u0633\u0628\u0639\u0629', u'\u062b\u0645\u0627\u0646\u064a\u0629', u'\u062a\u0633\u0639\u0629', u'\u0639\u0634\u0631\u0629', u'\u062b\u0645\u0629', u'\u0647\u0646\u0627\u0643', u'\u0647\u0646\u0627', u'\u0647\u0646\u0627\u0644\u0643', u'\u0644\u0630\u0644\u0643', u'\u062f\u0648\u0646', u'\u0643\u0644', u'\u062c\u0645\u064a\u0639', u'\u0643\u0627\u0641\u0629', u'\u0648\u0641\u0642', u'\u062d\u0633\u0628', u'\u0645\u0627', u'\u0645\u0627', u'\u0645\u0645\u0627', u'\u0643\u064a\u0641\u0645\u0627', u'\u0648\u0642\u062a\u0645\u0627', u'\u0623\u064a\u0646\u0645\u0627', u'\u062d\u0633\u0628\u0645\u0627', u'\u062d\u064a\u062b\u0645\u0627', u'\u0641\u064a\u0645\u0627', u'\u0639\u0645\u0627', u'\u0646\u0641\u0633', u'\u0644\u064a\u0633', u'\u0644\u064a\u0633\u062a', u'\u0644\u064a\u0633\u0627', u'\u0644\u064a\u0633\u0648\u0627', u'\u0644\u0633\u0646', u'\u0644\u0633\u062a', u'\u0647\u0644', u'\u0645\u0627\u0630\u0627', u'\u0645\u062a\u0649', u'\u0623\u064a\u0646', u'\u0623\u0646\u0649', u'\u0643\u064a\u0641', u'\u0643\u0645', u'\u0623\u0646\u0627', u'\u0623\u0646\u062a\u0645', u'\u0623\u0646\u062a\u0645\u0627', u'\u0623\u0646\u062a\u0645', u'\u0623\u0646\u062a\u0646', u'\u0647\u0648', u'\u0647\u064a', u'\u0647\u0645\u0627', u'\u0647\u0645', u'\u0647\u0646', u'\u0646\u062d\u0646', u'\u0623\u064a', u'\u0623\u064a', u'\u0623\u064a\u0629', u'\u0623\u064a\u0636\u0627', u'\u0643\u0630\u0644\u0643', u'\u0643\u0627\u0646', u'\u0643\u0627\u0646\u062a', u'\u0643\u0627\u0646\u0627', u'\u0643\u0627\u0646\u0648\u0627', u'\u0643\u0646', u'\u0643\u0646\u062a', u'\u0631\u063a\u0645', u'\u0630\u0627\u062a', u'\u0630\u0648', u'\u0630\u064a', u'\u0630\u0627', u'\u0630\u0648\u064a', u'\u0630\u0648\u0627\u062a', u'\u0625\u0644\u0627', u'\u0623\u0645', u'\u0639\u062f\u0645', u'\u0642\u0627\u0645', u'\u0642\u0627\u0645\u062a', u'\u0642\u0627\u0645\u0627', u'\u0642\u0627\u0645\u0648\u0627', u'\u0642\u0645\u0646', u'\u0642\u0645\u062a', u'\u064a\u0642\u0648\u0645', u'\u062a\u0642\u0648\u0645', u'\u0623\u0642\u0648\u0645', u'\u062a\u0642\u0645', u'\u062a\u0642\u0648\u0645\u0648\u0646', u'\u062a\u0642\u0645\u0646', u'\u062a\u0645', u'\u062a\u0645\u062a', u'\u064a\u062a\u0645', u'\u062a\u062a\u0645', u'\u0639\u062f\u0629', u'\u0628\u0636\u0639\u0629', u'\u0628\u0636\u0639', u'\u0639\u0627\u0645', u'\u0623\u0643\u062b\u0631', u'\u0623\u0642\u0644', u'\u0642\u0637', u'\u0628\u0634\u0643\u0644', u'\u0645\u062b\u0644', u'\u0645\u0639\u0638\u0645', u'\u0623\u063a\u0644\u0628', u'\u0628\u0627\u0642\u064a', u'\u0644\u0648', u'\u0644\u0648\u0644\u0627', u'\u0644\u0648\u0644\u0645', u'\u0644\u0643\u0646', u'\u0625\u0646\u064a', u'\u0625\u0646\u0646\u064a', u'\u0623\u0646\u0646\u064a', u'\u0625\u0646\u0647', u'\u0623\u0646\u0647', u'\u0625\u0646\u0647\u0627', u'\u0623\u0646\u0647\u0627', u'\u0625\u0646\u0647\u0645\u0627', u'\u0623\u0646\u0647\u0645\u0627', u'\u0625\u0646\u0647\u0645', u'\u0623\u0646\u0647\u0645', u'\u0625\u0646\u0647\u0646', u'\u0623\u0646\u0647\u0646', u'\u0644\u0643\u0646\u064a', u'\u0644\u0643\u0646\u0646\u064a', u'\u0644\u0643\u0646\u0643', u'\u0644\u0643\u0646\u0643\u0645\u0627', u'\u0644\u0643\u0646\u0643\u0645', u'\u0644\u0643\u0646\u0643\u0646', u'\u0623\u0648', u'\u0628\u0644', u'\u062d\u062a\u0649', u'\u0644\u064a\u062a', u'\u0644\u0639\u0644', u'\u0644\u0639\u0644\u064a', u'\u0644\u0639\u0644\u0643', u'\u0644\u0639\u0644\u0647', u'\u0644\u0639\u0644\u0647\u0627', u'\u0644\u0639\u0644\u0643\u0645\u0627', u'\u0644\u0639\u0644\u0647\u0645', u'\u0644\u0639\u0644\u0647\u0646', u'\u0644\u064a\u062a\u0646\u064a', u'\u0644\u064a\u062a\u0643', u'\u0644\u064a\u062a\u0646\u0627', u'\u0644\u064a\u062a\u0647\u0645', u'\u0644\u064a\u062a\u0647\u0646', u'\u062d\u0633\u0628', u'\u0633\u0648\u0649', u'\u062b\u0645', u'\u0644\u0642\u062f', u'\u0628\u0644\u0649', u'\u0646\u0639\u0645', u'\u0623\u062c\u0644', u'\u062d\u064a\u062b', u'\u0644\u0626\u0646', u'\u0625\u0646\u0645\u0627', u'\u0644\u0645\u0627', u'\u0643\u0644\u0627', u'\u0645\u062b\u0644', u'\u0641\u0648\u0642', u'\u062a\u062d\u062a', u'\u062f\u0627\u062e\u0644', u'\u062e\u0627\u0631\u062c', u'\u062d\u064a\u0646', u'\u0623\u0641\u0644\u0627', u'\u0623\u0639\u0644\u0649', u'\u0623\u0633\u0641\u0644', u'\u0623\u0639\u0644\u0627\u0647', u'\u0623\u062f\u0646\u0627\u0647', u'\u0636\u0645\u0646', u'\u0643\u064a', u'\u0628\u062e\u0644\u0627\u0641', u'\u0628\u0625\u0645\u0643\u0627\u0646', u'\u0642\u062f\u0631', u'\u0623\u0645\u0631', u'\u0623\u0645\u0631\u0627', u'\u0623\u0645\u0648\u0631', u'\u0643\u0645\u0627', u'\u0625\u0630\u0646', u'\u0648', u'\u0633\u064a\u0645\u0627', u'\u0628\u064a\u0646\u0645\u0627', u'\u064a\u0646\u0627\u064a\u0631', u'\u0641\u0628\u0631\u0627\u064a\u0631', u'\u0645\u0627\u0631\u0633', u'\u0625\u0628\u0631\u064a\u0644', u'\u0645\u0627\u064a\u0648', u'\u064a\u0648\u0646\u064a\u0647', u'\u064a\u0648\u0644\u064a\u0647', u'\u0623\u063a\u0633\u0637\u0633', u'\u0633\u0628\u062a\u0645\u0628\u0631', u'\u0623\u0643\u062a\u0648\u0628\u0631', u'\u0646\u0648\u0641\u0645\u0628\u0631', u'\u062f\u064a\u0633\u0645\u0628\u0631', u'\u0643\u0627\u0646\u0648\u0646', u'\u0634\u0628\u0627\u0637', u'\u0628\u062d\u064a\u062b', u'\u0628\u063a\u064a\u0629', u'\u0648\u062c\u0647', u'\u0643\u0627\u0641', u'\u0641\u0642\u0637', u'\u0641\u062d\u0633\u0628', u'\u0628\u064a\u062f', u'\u0628\u0639\u0636', u'\u0628\u0636\u0639\u0629', u'\u0628\u0636\u0639', u'\u0623\u0644\u0641', u'\u0628\u0627\u0621']
#stopwords_ar=ar_stopwords=arabic_stopwords=[u'\u0627\u0644\u0644\u0647', u'\u0644\u0644\u0647', u'\u0639\u0628\u0631', u'\u0644\u062f\u0649', u'\u0639\u0646\u062f', u'\u0628\u064a\u0646', u'\u0639\u0646', u'\u0645\u0639', u'\u0641\u064a', u'\u0639\u0644\u0649', u'\u0645\u0646', u'\u0625\u0644\u0649', u'\u0628\u0634\u0623\u0646', u'\u0647\u0630\u0627', u'\u0647\u0630\u0647', u'\u0647\u0627\u0630\u0627\u0646', u'\u0647\u0630\u0627\u0646', u'\u0647\u0627\u062a\u0627\u0646', u'\u0647\u0627\u0630\u064a\u0646', u'\u0647\u0627\u062a\u064a\u0646', u'\u0647\u0624\u0644\u0627\u0621', u'\u0623\u0648\u0644\u0626\u0643', u'\u0630\u0644\u0643', u'\u062a\u0644\u0643', u'\u062a\u0644\u0643\u0645\u0627', u'\u062a\u0644\u0643\u0645\u0627', u'\u0642\u062f', u'\u0644\u0645', u'\u0644\u0627', u'\u0644\u0646', u'\u0633\u0648\u0641', u'\u0625\u0630\u0627', u'\u0625\u0630\u0627', u'\u0625\u0630', u'\u0623\u062b\u0646\u0627\u0621', u'\u062e\u0644\u0627\u0644', u'\u0645\u0646\u0630', u'\u0628\u0639\u062f', u'\u0642\u0628\u0644', u'\u0627\u0644\u0630\u064a', u'\u0627\u0644\u062a\u064a', u'\u0627\u0644\u0630\u064a\u0646', u'\u0627\u0644\u0644\u0627\u062a\u064a', u'\u0627\u0644\u0644\u0627\u0626\u064a', u'\u0627\u0644\u0644\u0630\u0627\u0646', u'\u0627\u0644\u0644\u062a\u0627\u0646', u'\u0627\u0644\u0644\u0630\u064a\u0646', u'\u0627\u0644\u0644\u062a\u064a\u0646', u'\u0646\u062d\u0648', u'\u0625\u0646', u'\u0625\u0646', u'\u0623\u0646', u'\u0625\u0646', u'\u062b\u0644\u0627\u062b', u'\u0623\u0631\u0628\u0639', u'\u062e\u0645\u0633', u'\u0633\u062a', u'\u0633\u0628\u0639', u'\u062b\u0645\u0627\u0646', u'\u062b\u0645\u0627\u0646\u064a', u'\u062a\u0633\u0639', u'\u0639\u0634\u0631', u'\u062b\u0644\u0627\u062b\u0629', u'\u0623\u0631\u0628\u0639\u0629', u'\u062e\u0645\u0633\u0629', u'\u0633\u062a\u0629', u'\u0633\u0628\u0639\u0629', u'\u062b\u0645\u0627\u0646\u064a\u0629', u'\u062a\u0633\u0639\u0629', u'\u0639\u0634\u0631\u0629', u'\u062b\u0645\u0629', u'\u0647\u0646\u0627\u0643', u'\u0647\u0646\u0627', u'\u0647\u0646\u0627\u0644\u0643', u'\u0644\u0630\u0644\u0643', u'\u062f\u0648\u0646', u'\u0643\u0644', u'\u062c\u0645\u064a\u0639', u'\u0643\u0627\u0641\u0629', u'\u0648\u0641\u0642', u'\u062d\u0633\u0628', u'\u0645\u0627', u'\u0645\u0627', u'\u0645\u0645\u0627', u'\u0643\u064a\u0641\u0645\u0627', u'\u0648\u0642\u062a\u0645\u0627', u'\u0623\u064a\u0646\u0645\u0627', u'\u062d\u0633\u0628\u0645\u0627', u'\u062d\u064a\u062b\u0645\u0627', u'\u0641\u064a\u0645\u0627', u'\u0639\u0645\u0627', u'\u0646\u0641\u0633', u'\u0644\u064a\u0633', u'\u0644\u064a\u0633\u062a', u'\u0644\u064a\u0633\u0627', u'\u0644\u064a\u0633\u0648\u0627', u'\u0644\u0633\u0646', u'\u0644\u0633\u062a', u'\u0647\u0644', u'\u0645\u0627\u0630\u0627', u'\u0645\u062a\u0649', u'\u0623\u064a\u0646', u'\u0623\u0646\u0649', u'\u0643\u064a\u0641', u'\u0643\u0645', u'\u0623\u0646\u0627', u'\u0623\u0646\u062a\u0645', u'\u0623\u0646\u062a\u0645\u0627', u'\u0623\u0646\u062a\u0645', u'\u0623\u0646\u062a\u0646', u'\u0647\u0648', u'\u0647\u064a', u'\u0647\u0645\u0627', u'\u0647\u0645', u'\u0647\u0646', u'\u0646\u062d\u0646', u'\u0623\u064a', u'\u0623\u064a', u'\u0623\u064a\u0629', u'\u0623\u064a\u0636\u0627', u'\u0643\u0630\u0644\u0643', u'\u0643\u0627\u0646', u'\u0643\u0627\u0646\u062a', u'\u0643\u0627\u0646\u0627', u'\u0643\u0627\u0646\u0648\u0627', u'\u0643\u0646', u'\u0643\u0646\u062a', u'\u0631\u063a\u0645', u'\u0630\u0627\u062a', u'\u0630\u0648', u'\u0630\u064a', u'\u0630\u0627', u'\u0630\u0648\u064a', u'\u0630\u0648\u0627\u062a', u'\u0625\u0644\u0627', u'\u0623\u0645', u'\u0639\u062f\u0645', u'\u0642\u0627\u0645', u'\u0642\u0627\u0645\u062a', u'\u0642\u0627\u0645\u0627', u'\u0642\u0627\u0645\u0648\u0627', u'\u0642\u0645\u0646', u'\u0642\u0645\u062a', u'\u064a\u0642\u0648\u0645', u'\u062a\u0642\u0648\u0645', u'\u0623\u0642\u0648\u0645', u'\u062a\u0642\u0645', u'\u062a\u0642\u0648\u0645\u0648\u0646', u'\u062a\u0642\u0645\u0646', u'\u062a\u0645', u'\u062a\u0645\u062a', u'\u064a\u062a\u0645', u'\u062a\u062a\u0645', u'\u0639\u062f\u0629', u'\u0628\u0636\u0639\u0629', u'\u0628\u0636\u0639', u'\u0639\u0627\u0645', u'\u0623\u0643\u062b\u0631', u'\u0623\u0642\u0644', u'\u0642\u0637', u'\u0628\u0634\u0643\u0644', u'\u0645\u062b\u0644', u'\u0645\u0639\u0638\u0645', u'\u0623\u063a\u0644\u0628', u'\u0628\u0627\u0642\u064a', u'\u0644\u0648', u'\u0644\u0648\u0644\u0627', u'\u0644\u0648\u0644\u0645', u'\u0644\u0643\u0646', u'\u0625\u0646\u064a', u'\u0625\u0646\u0646\u064a', u'\u0623\u0646\u0646\u064a', u'\u0625\u0646\u0647', u'\u0623\u0646\u0647', u'\u0625\u0646\u0647\u0627', u'\u0623\u0646\u0647\u0627', u'\u0625\u0646\u0647\u0645\u0627', u'\u0623\u0646\u0647\u0645\u0627', u'\u0625\u0646\u0647\u0645', u'\u0623\u0646\u0647\u0645', u'\u0625\u0646\u0647\u0646', u'\u0623\u0646\u0647\u0646', u'\u0644\u0643\u0646\u064a', u'\u0644\u0643\u0646\u0646\u064a', u'\u0644\u0643\u0646\u0643', u'\u0644\u0643\u0646\u0643\u0645\u0627', u'\u0644\u0643\u0646\u0643\u0645', u'\u0644\u0643\u0646\u0643\u0646', u'\u0623\u0648', u'\u0628\u0644', u'\u062d\u062a\u0649', u'\u0644\u064a\u062a', u'\u0644\u0639\u0644', u'\u0644\u0639\u0644\u064a', u'\u0644\u0639\u0644\u0643', u'\u0644\u0639\u0644\u0647', u'\u0644\u0639\u0644\u0647\u0627', u'\u0644\u0639\u0644\u0643\u0645\u0627', u'\u0644\u0639\u0644\u0647\u0645', u'\u0644\u0639\u0644\u0647\u0646', u'\u0644\u064a\u062a\u0646\u064a', u'\u0644\u064a\u062a\u0643', u'\u0644\u064a\u062a\u0646\u0627', u'\u0644\u064a\u062a\u0647\u0645', u'\u0644\u064a\u062a\u0647\u0646', u'\u062d\u0633\u0628', u'\u0633\u0648\u0649', u'\u062b\u0645', u'\u0644\u0642\u062f', u'\u0628\u0644\u0649', u'\u0646\u0639\u0645', u'\u0623\u062c\u0644', u'\u062d\u064a\u062b', u'\u0644\u0626\u0646', u'\u0625\u0646\u0645\u0627', u'\u0644\u0645\u0627', u'\u0643\u0644\u0627', u'\u0645\u062b\u0644', u'\u0641\u0648\u0642', u'\u062a\u062d\u062a', u'\u062f\u0627\u062e\u0644', u'\u062e\u0627\u0631\u062c', u'\u062d\u064a\u0646', u'\u0623\u0641\u0644\u0627', u'\u0623\u0639\u0644\u0649', u'\u0623\u0633\u0641\u0644', u'\u0623\u0639\u0644\u0627\u0647', u'\u0623\u062f\u0646\u0627\u0647', u'\u0636\u0645\u0646', u'\u0643\u064a', u'\u0628\u062e\u0644\u0627\u0641', u'\u0628\u0625\u0645\u0643\u0627\u0646', u'\u0642\u062f\u0631', u'\u0623\u0645\u0631', u'\u0623\u0645\u0631\u0627', u'\u0623\u0645\u0648\u0631', u'\u0643\u0645\u0627', u'\u0625\u0630\u0646', u'\u0648', u'\u0633\u064a\u0645\u0627']
#print arabic_stopwords
#for ar_stp in arabic_stopwords:
#	print ar_stp, [ar_stp]
#print " ".join(arabic_stopwords) 

#suf_list=[u'\u0647', u'\u0647\u0627', u'\u0647\u0645', u'\u0647\u0645\u0627', u'\u064a', u'\u0643', u'\u0643\u0645\u0627', u'\u0643\u0645', u'\u0643\u0646', u'\u0646\u064a']
#we exclude ya2, because it adds many unneeded splits, we'll find a way to add it later
#suf_list=[u'\u0647', u'\u0647\u0627', u'\u0647\u0645', u'\u0647\u0645\u0627', u'\u0643', u'\u0643\u0645\u0627', u'\u0643\u0645', u'\u0643\u0646', u'\u0646\u064a']

#suf_list.append(noon+alef)
#print suf_list
suf_list=[u'\u0647', u'\u0647\u0627', u'\u0647\u0645', u'\u0647\u0645\u0627', u'\u0643', u'\u0643\u0645\u0627', u'\u0643\u0645', u'\u0643\u0646', u'\u0646\u064a', u'\u0646\u0627']
#print suf_list
#suf_list=[u'\u0647', u'\u0647\u0627', u'\u0647\u0645', u'\u0647\u0645\u0627', u'\u064a', u'\u0643', u'\u0643\u0645\u0627', u'\u0643\u0646', u'\u0646\u064a']
#for sl in suf_list:
#	print sl, [sl]
#print suf_list
pre_list1=[(v0+v1+v2,(v0,v1,v2)) for v0 in prefixes_zero for v1 in prefixes_one for v2 in prefixes_two if v0 or v1 or v2]
pre_list2=[(v0+v1+v2,(v0,v1,v2)) for v0 in prefixes_zero for v1 in prefixes_one_add for v2 in [""]]
pre_list=pre_list1+pre_list2
pre_dict=dict(iter(pre_list))



#for pre in pre_list:
#	print pre[0], pre[1]

def get_pre_ar(word):
	if ord(word[0])<1500: return [] #if non-Arabic characters
	if len(word)<2: return [] #smallest words acceptable are words with 2 letters such as bihi or lahu
	out=[""]
	for pd in pre_dict: 
		if word.startswith(pd): out.append(pd)
	return out

def get_suf_ar(word):
	if ord(word[0])<1500: return []
	if len(word)<2: return [] #words such as bihi or lahu (2 letters)
	out=[""]
	for suf in suf_list:
		if word.endswith(suf): out.append(suf)
	return out

def get_raw_candidates(word):
	cur_pres=get_pre_ar(word)
	cur_sufs=get_suf_ar(word)
	if cur_pres==[] or cur_sufs==[]: return [("",word,"")]
	all_candidates=[]
	#print ">>>>>>>>>>>>>", word
	for pre0 in cur_pres:
		for suf0 in cur_sufs:
			#print ">>>>", pre0, suf0
			cur_root=word[len(pre0):len(word)-len(suf0)]
			#print "cur_root", cur_root
			all_candidates.append((pre0, cur_root, suf0))
	return all_candidates


def get_candidates_ar(word):
	cur_raw_candidates=get_raw_candidates(word)
	if len(cur_raw_candidates)==1: return cur_raw_candidates
	final_candidates=[]
	for cur_item in cur_raw_candidates:
		cr_pre,cr_root,cr_suf=cur_item
		
		if len(cr_root)<1: continue #eliminate roots with zero chars
		if cr_pre and cr_pre[-1]==seen and not cr_root[0] in modare3_initials: continue #eliminate words with s- prefix and no present tense initials
		if cr_pre and cr_pre[-1]==seen and cr_root[-1]==ta2_marboota: continue #eliminate words with s- prefix and ta2 marboota at the end of the root (clearly a noun)
		if cr_pre and cr_pre[-1]==seen and cr_root.endswith(alef_ta2): continue #eliminate words with s- prefix and alef ta2 at the end of the root (clearly a noun)
		if cr_pre and cr_pre.endswith(alef_lam) and cr_suf!="": continue #eliminate words with al which has suffixes
		
		
		if cr_root in arabic_stopwords: return [cur_item] #once we find a stop word, we include it
		if cr_root.startswith(alef_lam) and len(cr_root)>2 and cr_root[2]!=ta2: continue #exclude roots that begin with al- except if they have ta2 after, such as iltizamat
		#print [cr_root]

			
		final_candidates.append(cur_item)
	if not final_candidates: final_candidates=cur_raw_candidates

	return final_candidates



def get_freq_dict(fpath):
	if not fpath: return {}
	cur_freq_dict={}
	freq_fopen=open(fpath)
	for ff in freq_fopen:
		split=ff[:-1].split("\t")
		if len(split)!=2: continue
		word,count=uc(split[0]),int(split[1])
		cur_freq_dict[word]=count
	freq_fopen.close()
	return cur_freq_dict



if __name__=="__main__":
	print("Hello!")
	word="السعادة"
	word="وللجنة"
	word="أكان"
	word="أوكان"
	word="للسلام"
	word="ومساعدتهم"
	candidates=get_candidates_ar(word)
	for w in candidates:
		print(w)

	# batch_size=20000
	# src_lan="en"
	# trg_lang="ar"
	# root_dir="/Users/hmghaly/Documents"
	# freq_dict=get_freq_dict("freq.txt")

	# #counter_dict={}
	# #freq_fname="freq.txt"
	
	# #freq_shelve=shelve.open("ar_token_freq.shelve")
	# #root_dir=r"c:\test"
	# #proj_dir=os.path.join(root_dir,"walign0")
	# #if not os.path.exists(proj_dir): os.makedirs(proj_dir)

	# #src_idx_fpath=os.path.join(proj_dir,"src-idx.txt")
	# #trg_idx_fpath=os.path.join(proj_dir,"trg-idx.txt")
	# #src_sents_fpath=os.path.join(proj_dir,"src-sents.txt")
	# #trg_sents_fpath=os.path.join(proj_dir,"trg-sents.txt")

	# #pickle_path=os.path.join(root_dir,"walign.pickle")
	# fname="corpus_sample.txt"
	# fpath="../un_corpus/corpus_sample.txt"
	# print("loading indexes")
	
	# #if not pickle_load:
	# fopen=open(fpath)
	# #src_fwd_index=[]
	# #trg_fwd_index=[]
	# #raw_src_sents=[] #tokenized src and trg sentences
	# #raw_trg_sents=[]
	# test_words=[]
	# for i,f in enumerate(fopen):
	# 	#if i%5000==0: print(i)
	# 	#if i>batch_size: break
		
	# 	line=f.strip("\n\r")
	# 	split=line.split("\t")
	# 	if len(split)!=2: continue
	# 	src,trg=split
	# 	src_uc,trg_uc=uc(src),uc(trg)
	# 	print(src_uc)
	# 	print(" ".join(tok_ar(trg_uc,freq_dict)))
	# 	print("-------")


	# 	continue
	# 	trg_clean=clean_ar(trg_uc)
	# 	trg_toks=tok_uc(trg_clean)
	# 	for tt in trg_toks:
	# 		if not is_arabic(tt): continue
			
	# 		word_split=morph_word(tt,freq_dict)
	# 		print(tt, " ".join(word_split))
	# 		continue

	# 		test_words.append(tt)
	# 		#if tt[0]!=seen: continue			
	# 		cand_found=get_candidates_ar(tt)
	# 		for can in cand_found:
	# 			cur_pre,cur_root,cur_suf=can
	# 			root_expansion=expand_root(cur_root)
	# 			cur_wt=0
	# 			for rex in root_expansion: cur_wt+=freq_dict.get(rex,0)
	# 			#print cur_root
	# 			#print ">>>>>", " ".join(root_expansion)
	# 			print(cur_pre,cur_root,cur_suf, freq_dict.get(cur_root,0), cur_wt)
	# 			#print ">>>>", can[0],can[1],can[2]
	# 			#counter_dict[cur_root]=counter_dict.get(cur_root,0)+1
				

	# 		print("------")

	# fopen.close()
	# counter_dict_keys=sorted(counter_dict.keys(),key=lambda x:-counter_dict[x])
	# #we keep this till we get more
	# fopen=open(freq_fname,"w")
	# for a in counter_dict_keys:
	# 	#print a, counter_dict[a]
	# 	line="%s\t%s\n"%(utf(a),counter_dict[a])
	# 	fopen.write(line)
	# fopen.close()

	# #	freq_shelve[utf(a)]=counter_dict[a]

	# for tw in test_words[:2500]:
	# 	cur_candidates=get_candidates_ar(tw)
	# 	for p0,r0,s0 in cur_candidates:
	# 		print(tw, p0,r0,s0, counter_dict.get(r0,0))
	# 	print("------")

	# #freq_shelve.close()
