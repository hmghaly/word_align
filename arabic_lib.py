import os, sys, time, shelve, json
from itertools import groupby
#sys.path.append("../utils")

#from general import *

#https://github.com/hmghaly/word_align/edit/master/arabic_lib.py

def tok_uc(txt):
    txt=re.sub(r"(?u)(\W)",r" \1 ",txt)
    return [v for v in re.split("\s+",txt) if v]

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
