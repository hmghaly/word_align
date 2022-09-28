


ipa_symbols=['ʔ', 'b', 'h', 't', 'θ', 'dʒ', 'ħ', 'x', 'd', 'ð', 'r', 'z', 's', 'ʃ', 'sˤ', 'dˤ', 'tˤ', 'ðˤ', 'ʕ', 'ɣ', 'f', 'q', 'k', 'l', 'm', 'n', 'h', 'w', 'aː', 'j', 'an', 'un', 'in', 'a', 'u', 'i', '', '', 'ɑ', 'ʔ', 'aː', 'aː', 'ʔ', 'ʌ', 'ʌ', 'ʌ', 'g', 'sil', 'u', 'uː', 'i', 'iː', 'ʔ', 'ʔ', 'dʒ']
franco_dict={'a': 'a', 'b': 'b', 'h': 'h', 't': 't', 'th': 'θ', 'g': 'g', 'j': 'dʒ', '7': 'ħ', 'kh': 'x', 'd': 'd', 'dh': 'ð', 'r': 'r', 'z': 'z', 's': 's', 'sh': 'ʃ', 'S': 'sˤ', 'D': 'dˤ', 'T': 'tˤ', 'DH': 'ðˤ', '3': 'ʕ', 'gh': 'ɣ', 'f': 'f', 'q': 'q', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'w': 'w', 'aa': 'a', 'y': 'j', 'ee': 'i', 'oo': 'u', 'oa': 'ɔ', 'ai': 'æ', 'ei': 'æ', '2': 'ʔ', 'an': 'an', 'un': 'un', 'in': 'in', 'u': 'u', 'o': 'u', 'i': 'i', 'e': 'i', "AA'": 'ʔ', 'AH': 'ʌ', 'Ah': 'ʌ', 'G': 'g', 'sil': 'sil', 'U': 'u', 'I': 'i', '<': 'ʔ', '^': 'ʔ', 'J': 'dʒ'}
arpabet_dict={'aa': 'ɑ', 'ae': 'æ', 'ah': 'ʌ', 'ao': 'ɔ', 'aw': 'aʊ', 'ax': 'ə', 'axr': 'ɚ', 'ay': 'aɪ', 'eh': 'ɛ', 'er': 'ɝ', 'ey': 'eɪ', 'ih': 'ɪ', 'ix': 'ɨ', 'iy': 'i', 'ow': 'oʊ', 'oy': 'ɔɪ', 'uh': 'ʊ', 'uw': 'u', 'ux': 'ʉ', 'b': 'b', 'ch': 'tʃ', 'd': 'd', 'dh': 'ð', 'dx': 'ɾ', 'el': 'l̩', 'em': 'm̩', 'en': 'n̩', 'f': 'f', 'g': 'ɡ', 'hh': 'h', 'h': 'h', 'jh': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'nx': 'ɾ̃', 'ng': 'ŋ', 'p': 'p', 'q': 'ʔ', 'r': 'ɹ', 's': 's', 'sh': 'ʃ', 't': 't', 'th': 'θ', 'v': 'v', 'w': 'w', 'wh': 'ʍ', 'y': 'j', 'z': 'z', 'zh': 'ʒ', 'h#': 'sil'}
buckwalter_dict={'A': 'ʔ', 'b': 'b', 'p': 'h', 't': 't', 'v': 'θ', 'j': 'dʒ', 'H': 'ħ', 'x': 'x', 'd': 'd', '*': 'ð', 'r': 'r', 'z': 'z', 's': 's', '$': 'ʃ', 'S': 'sˤ', 'D': 'dˤ', 'T': 'tˤ', 'Z': 'ðˤ', 'E': 'ʕ', 'g': 'ɣ', 'f': 'f', 'q': 'q', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'h': 'h', 'w': 'w', 'Y': 'aː', 'y': 'j', 'F': 'an', 'N': 'un', 'K': 'in', 'a': 'a', 'u': 'u', 'i': 'i', 'AA': 'aː', "A'": 'ʔ', 'aa': 'aː', "AA'": 'ʔ', 'AH': 'ʌ', 'ah': 'ʌ', 'Ah': 'ʌ', 'G': 'g', 'sil': 'sil', 'U': 'u', 'uu': 'uː', 'I': 'i', 'ii': 'iː', '<': 'ʔ', '^': 'ʔ', 'J': 'dʒ'}
ipa_ft_dict={'i': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:close'], 'y': ['ft:vowel', 'ft:front', 'ft:rounded', 'ft:close'], 'ɨ': ['ft:vowel', 'ft:central', 'ft:unrounded', 'ft:close'], 'ʉ': ['ft:vowel', 'ft:central', 'ft:rounded', 'ft:close'], 'ɯ': ['ft:vowel', 'ft:back', 'ft:unrounded', 'ft:close'], 'u': ['ft:vowel', 'ft:back', 'ft:rounded', 'ft:close'], 'ɪ': ['ft:vowel', 'ft:near-front', 'ft:unrounded', 'ft:near-close'], 'ʏ': ['ft:vowel', 'ft:near-front', 'ft:rounded', 'ft:near-close'], 'ʊ': ['ft:vowel', 'ft:near-back', 'ft:rounded', 'ft:near-close'], 'e': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:close-mid'], 'ø': ['ft:vowel', 'ft:front', 'ft:rounded', 'ft:close-mid'], 'ɘ': ['ft:vowel', 'ft:central', 'ft:unrounded', 'ft:close-mid'], 'ɵ': ['ft:vowel', 'ft:central', 'ft:rounded', 'ft:close-mid'], 'ɤ': ['ft:vowel', 'ft:back', 'ft:unrounded', 'ft:close-mid'], 'o': ['ft:vowel', 'ft:back', 'ft:rounded', 'ft:close-mid'], 'ɛ': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:open-mid'], 'œ': ['ft:vowel', 'ft:front', 'ft:rounded', 'ft:open-mid'], 'ɜ': ['ft:vowel', 'ft:central', 'ft:unrounded', 'ft:open-mid'], 'ɞ': ['ft:vowel', 'ft:central', 'ft:rounded', 'ft:open-mid'], 'ʌ': ['ft:vowel', 'ft:back', 'ft:unrounded', 'ft:open-mid'], 'ɔ': ['ft:vowel', 'ft:back', 'ft:rounded', 'ft:open-mid'], 'æ': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:near-open'], 'ɐ': ['ft:vowel', 'ft:central', 'ft:unrounded', 'ft:near-open'], 'a': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:open'], 'ɶ': ['ft:vowel', 'ft:front', 'ft:rounded', 'ft:open'], 'ɑ': ['ft:vowel', 'ft:back', 'ft:unrounded', 'ft:open'], 'ɒ': ['ft:vowel', 'ft:back', 'ft:rounded'], 'm': ['ft:voiced', 'ft:nasal', 'ft:bilabial'], 'ɱ': ['ft:voiced', 'ft:nasal', 'ft:labio-dental'], 'n': ['ft:voiced', 'ft:nasal', 'ft:alveolar'], 'ɳ': ['ft:voiced', 'ft:nasal', 'ft:retroflex'], 'ŋ': ['ft:voiced', 'ft:nasal', 'ft:velar'], 'ɴ': ['ft:voiced', 'ft:nasal', 'ft:uvular'], 'p': ['ft:voiceless', 'ft:plosive', 'ft:bilabial'], 'b': ['ft:voiced', 'ft:plosive', 'ft:bilabial'], 't': ['ft:voiceless', 'ft:plosive', 'ft:alveolar'], 'd': ['ft:voiced', 'ft:plosive', 'ft:alveolar'], 'ʈ': ['ft:voiceless', 'ft:plosive', 'ft:retroflex'], 'ɖ': ['ft:voiced', 'ft:plosive', 'ft:retroflex'], 'c': ['ft:voiceless', 'ft:plosive', 'ft:palatal'], 'ɟ': ['ft:voiced', 'ft:plosive', 'ft:palatal'], 'k': ['ft:voiceless', 'ft:plosive', 'ft:velar'], 'ɡ': ['ft:voiced', 'ft:plosive', 'ft:velar'], 'g': ['ft:voiced', 'ft:plosive', 'ft:velar'], 'q': ['ft:voiceless', 'ft:plosive', 'ft:uvular'], 'ɢ': ['ft:voiced', 'ft:plosive', 'ft:uvular'], 'ʡ': ['ft:voiceless', 'ft:plosive', 'ft:pharyngeal'], 'ʔ': ['ft:voiceless', 'ft:plosive', 'ft:glottal'], 'p͡f': ['ft:voiceless', 'ft:affricate', 'ft:labio-dental'], 'b͡v': ['ft:voiced', 'ft:affricate', 'ft:dental'], 't̪͡s': ['ft:voiceless', 'ft:affricate', 'ft:dental'], 't͡s': ['ft:voiceless', 'ft:affricate', 'ft:alveolar'], 'd͡z': ['ft:voiced', 'ft:affricate', 'ft:alveolar'], 't͡ʃ': ['ft:voiceless', 'ft:affricate', 'ft:post-alveolar'], 'd͡ʒ': ['ft:voiced', 'ft:affricate', 'ft:post-alveolar'], 'ʈ͡ʂ': ['ft:voiceless', 'ft:affricate', 'ft:retroflex'], 'ɖ͡ʐ': ['ft:voiced', 'ft:affricate', 'ft:retroflex'], 't͡ɕ': ['ft:voiceless', 'ft:affricate', 'ft:palatal'], 'd͡ʑ': ['ft:voiced', 'ft:affricate', 'ft:palatal'], 'k͡x': ['ft:voiceless', 'ft:affricate', 'ft:velar'], 'ɸ': ['ft:voiceless', 'ft:fricative', 'ft:bilabial'], 'β': ['ft:voiced', 'ft:fricative', 'ft:bilabial'], 'f': ['ft:voiceless', 'ft:fricative', 'ft:labio-dental'], 'v': ['ft:voiced', 'ft:fricative', 'ft:labio-dental'], 'θ': ['ft:voiceless', 'ft:fricative', 'ft:dental'], 'ð': ['ft:voiced', 'ft:fricative', 'ft:dental'], 's': ['ft:voiceless', 'ft:fricative', 'ft:alveolar'], 'z': ['ft:voiced', 'ft:fricative', 'ft:alveolar'], 'ʃ': ['ft:voiceless', 'ft:fricative', 'ft:post-alveolar'], 'ʒ': ['ft:voiced', 'ft:fricative', 'ft:post-alveolar'], 'ʂ': ['ft:voiceless', 'ft:fricative', 'ft:retroflex'], 'ʐ': ['ft:voiced', 'ft:fricative', 'ft:palatal'], 'ç': ['ft:voiceless', 'ft:fricative', 'ft:palatal'], 'x': ['ft:voiceless', 'ft:fricative', 'ft:velar'], 'ɣ': ['ft:voiced', 'ft:fricative', 'ft:velar'], 'χ': ['ft:voiceless', 'ft:fricative', 'ft:uvular'], 'ʁ': ['ft:voiced', 'ft:fricative', 'ft:uvular'], 'ħ': ['ft:voiceless', 'ft:fricative', 'ft:pharyngeal'], 'h': ['ft:voiceless', 'ft:fricative', 'ft:glottal'], 'ɦ': ['ft:voiced', 'ft:fricative', 'ft:glottal'], 'w': ['ft:voiced', 'ft:approximant', 'ft:bilabial'], 'ʋ': ['ft:voiced', 'ft:approximant', 'ft:labio-dental'], 'ɹ': ['ft:voiced', 'ft:approximant', 'ft:alveolar'], 'ɻ': ['ft:voiced', 'ft:approximant', 'ft:retroflex'], 'j': ['ft:voiced', 'ft:approximant', 'ft:palatal'], 'ɰ': ['ft:voiced', 'ft:approximant', 'ft:velar'], 'ⱱ': ['ft:voiced', 'ft:flap', 'ft:labio-dental'], 'ɾ': ['ft:voiced', 'ft:flap', 'ft:alveolar'], 'ɽ': ['ft:voiced', 'ft:flap', 'ft:retroflex'], 'ʙ': ['ft:voiced', 'ft:trill', 'ft:bilabial'], 'r': ['ft:voiced', 'ft:trill', 'ft:alveolar'], 'ʀ': ['ft:voiced', 'ft:trill', 'ft:uvular'], 'l': ['ft:voiced', 'ft:lateral-approximant', 'ft:alveolar'], 'ɫ': ['ft:voiced', 'ft:lateral-approximant', 'ft:alveolar'], 'ɭ': ['ft:voiced', 'ft:lateral-approximant', 'ft:retroflex'], 'ʎ': ['ft:voiced', 'ft:lateral-approximant', 'ft:palatal'], 'ʟ': ['ft:voiced', 'ft:lateral-approximant', 'ft:velar'], 'ə': ['ft:schwa'], 'ɚ': ['ft:schwa'], 'ɝ': ['ft:schwa'], 'ɹ̩': ['ft:voiced', 'ft:approximant', 'ft:alveolar'], 'sil': ['ft:silence'], '-': ['ft:other'], 'sˤ': ['ft:voiceless', 'ft:fricative', 'ft:alveolar', 'ft:emphatic'], 'dˤ': ['ft:voiced', 'ft:plosive', 'ft:alveolar', 'ft:emphatic'], 'tˤ': ['ft:voiceless', 'ft:plosive', 'ft:alveolar', 'ft:emphatic'], 'ðˤ': ['ft:voiced', 'ft:fricative', 'ft:dental', 'ft:emphatic'], 'aʊ': ['ft:vowel', 'ft:front', 'ft:near-back', 'ft:rounded', 'ft:unrounded', 'ft:open', 'ft:near-close', 'ft:diphthong'], 'aɪ': ['ft:vowel', 'ft:front', 'ft:near-front', 'ft:unrounded', 'ft:near-close', 'ft:diphthong'], 'eɪ': ['ft:vowel', 'ft:front', 'ft:near-front', 'ft:unrounded', 'ft:close-mid', 'ft:near-close', 'ft:diphthong'], 'oʊ': ['ft:vowel', 'ft:back', 'ft:near-back', 'ft:rounded', 'ft:close-mid', 'ft:near-close', 'ft:diphthong'], 'ɔɪ': ['ft:vowel', 'ft:near-front', 'ft:back', 'ft:rounded', 'ft:unrounded', 'ft:open-mid', 'ft:near-close', 'ft:diphthong'], 'tʃ': ['ft:voiceless', 'ft:affricate', 'ft:post-alveolar', 'ft:combined'], 'l̩': ['ft:voiced', 'ft:lateral-approximant', 'ft:alveolar', 'ft:syllabic'], 'm̩': ['ft:voiced', 'ft:nasal', 'ft:bilabial', 'ft:syllabic'], 'n̩': ['ft:voiced', 'ft:nasal', 'ft:alveolar', 'ft:syllabic'], 'dʒ': ['ft:voiced', 'ft:affricate', 'ft:post-alveolar', 'ft:combined'], 'ɾ̃': ['ft:voiced', 'ft:nasal', 'ft:flap'], 'ʍ': ['ft:voiceless', 'ft:fricative', 'ft:bilabial', 'ft:velar'], 'aː': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:open', 'ft:long'], 'uː': ['ft:vowel', 'ft:back', 'ft:rounded', 'ft:close', 'ft:long'], 'iː': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:close', 'ft:long'], 'ɑ̃': ['ft:vowel', 'ft:nasal', 'ft:front', 'ft:unrounded', 'ft:open'], 'ɛ̃': ['ft:vowel', 'ft:nasal', 'ft:front', 'ft:unrounded', 'ft:open-mid'], 'ɔ̃': ['ft:vowel', 'ft:nasal', 'ft:back', 'ft:rounded', 'ft:open-mid'], 'ʕ': ['ft:voiced', 'ft:fricative', 'ft:pharyngeal'], 'an': ['ft:voiced', 'ft:vowel', 'ft:nasal', 'ft:front', 'ft:unrounded', 'ft:alveolar', 'ft:open', 'ft:combined'], 'un': ['ft:voiced', 'ft:vowel', 'ft:back', 'ft:rounded', 'ft:alveolar', 'ft:combined'], 'in': ['ft:voiced', 'ft:vowel', 'ft:front', 'ft:unrounded', 'ft:alveolar', 'ft:combined']}

#if need to update

def franco2phones(tmp_text):
  combined_letters=["sh","gh","dh","kh","th", "DH"]
  tmp_text=re.sub("\-q$","-?",tmp_text)
  tmp_text=tmp_text.replace(" "," + ")
  tmp_text=tmp_text.replace("-"," + ")
  tmp_text=re.sub("([aeiou]+)",r" \1 ",tmp_text)
  for a0 in combined_letters:
    tmp_text=tmp_text.replace(a0, " %s "%a0)
  tmp_list_phones=re.split("\s+",tmp_text.strip())
  list_phones=[]
  for tp0 in tmp_list_phones:
    if len(tp0)==1: 
      if tp0 in "DST": list_phones.append(tp0)
      elif tp0.lower()=="p": list_phones.append("b")
      elif tp0.lower()=="c": list_phones.append("k")
      else: list_phones.append(tp0.lower())
    elif tp0[0] in "aeiou": list_phones.append(tp0)
    elif tp0 in combined_letters: list_phones.append(tp0)
    else: 
      for chr0 in tp0:
        if chr0 in "DST": list_phones.append(chr0)
        elif chr0.lower()=="p": list_phones.append("b")
        elif chr0.lower()=="c": list_phones.append("k")
        else: list_phones.append(chr0.lower())
      #list_phones.extend(tp0)
  return list_phones

def franco2seq(franco_word0,franco_dict0): #main function to convert a word to IPA sequence, with silence before & after, and with shaddah indicator
  final_list=["sil"]
  tmp_phones=franco2phones(franco_word0)
  for ti0,tp in enumerate(tmp_phones):
    if ti0>0 and tmp_phones[ti0-1]==tp: final_list.append("-")
    ipa_equiv=franco_dict.get(tp,"-")
    #if ipa_equiv=="" and final_list[-1]=="-": continue
    final_list.append(ipa_equiv)
  final_list.append("sil")
  final_list=[key for key,group in groupby(final_list)]
  return final_list

def buck2ipa(buckwalter_symbol0):
  if buckwalter_symbol0.lower() in ["sil","dist"]: return buckwalter_symbol0.lower()
  out=buckwalter_dict.get(buckwalter_symbol0)
  if out!=None: return out
  out=buckwalter_dict.get(buckwalter_symbol0[:2])
  if out!=None: return out
  return buckwalter_dict.get(buckwalter_symbol0[0],"-")


def arpabet2ipa(arpabet_symbol0):
  if arpabet_symbol0.lower() in ["sil","dist"]: return arpabet_symbol0.lower()
  return arpabet_dict.get(arpabet_symbol0.lower().strip("0123456789"),"-")


#==================== 
import cmudict
cur_cmu=cmudict.dict()

def word2ipa(word0):
  arpabet_out=cur_cmu.get(word0.lower(),[""])[0]
  if arpabet_out=="": return []
  ipa_out0=[arpabet2ipa(v) for v in arpabet_out]
  return ipa_out0 


#===========================================
# import pandas
# def get_sheet_dict(sheet_obj,key_col0,val_col0): #pandas get conversion dicts
#   tmp_sheet_dict={}
#   for i0,row0 in sheet_obj.iterrows():
#     cur_key,cur_val=row0[key_col0],row0[val_col0]
#     if cur_key=="" or cur_val=="": continue
#     tmp_sheet_dict[cur_key]=cur_val
#   return tmp_sheet_dict

# transcription_xls='https://docs.google.com/spreadsheets/d/e/2PACX-1vSQnJplWovDMZT121xv3HpuFTErhX18wIOdORJa060mFHXlzYa-9xUh-L4iK7OB6ifiP09VrkVDLg2v/pub?output=xlsx'
# cur_sheet_name="buckwalter"
# cur_workbook_obj=pd.read_excel(transcription_xls, None,keep_default_na=False)
# cur_sheet_obj=cur_workbook_obj["buckwalter"]
# #cur_sheet_obj=pd.read_excel(transcription_xls, cur_sheet_name,keep_default_na=False)
# buckwalter_symbols=list(cur_sheet_obj["buckwalter"])
# ipa_symbols=list(cur_sheet_obj["IPA"])


# # buckwalter_sheet=cur_sheet_obj["buckwalter"]
# # ipa_sheet=cur_sheet_obj["ipa"]
# # franco_sheet=cur_sheet_obj["franco"]

# # arpabet_sheet=cur_sheet_obj["arpabet"]
# # sheet_list=cur_sheet_obj.keys()

# arabic_sheet=cur_workbook_obj["arabic"]
# ar_dict=get_sheet_dict(arabic_sheet,"arabic","IPA")

# arpabet_sheet_obj=cur_workbook_obj["arpabet"]
# #arpabet_sheet_obj=pd.read_excel(transcription_xls, "arpabet",keep_default_na=False)
# arpabet_symbols=list(arpabet_sheet_obj["arpabet"])
# arpabet_symbols=[v.lower() for v in arpabet_symbols]
# arpabet_ipa_symbols=list(arpabet_sheet_obj["IPA"])

# franco_sheet_obj=cur_workbook_obj["franco"]
# #franco_sheet_obj=pd.read_excel(transcription_xls, "franco",keep_default_na=False)
# franco_symbols=list(franco_sheet_obj["franco"])
# franco_ipa_symbols=list(franco_sheet_obj["IPA"])

# cur_conv_list=[(a,b) for a,b in zip(buckwalter_symbols,ipa_symbols) if b]
# buckwalter_dict=conversion_dict=dict(iter(cur_conv_list))

# arpabet_conv_list=[(a,b) for a,b in zip(arpabet_symbols,arpabet_ipa_symbols) if b]
# arpabet_dict=dict(iter(arpabet_conv_list))
# arpabet_dict={'aa': 'ɑ', 'ae': 'æ', 'ah': 'ʌ', 'ao': 'ɔ', 'aw': 'aʊ', 'ax': 'ə', 'axr': 'ɚ', 'ay': 'aɪ', 'eh': 'ɛ', 'er': 'ɝ', 'ey': 'eɪ', 'ih': 'ɪ', 'ix': 'ɨ', 'iy': 'i', 'ow': 'oʊ', 'oy': 'ɔɪ', 'uh': 'ʊ', 'uw': 'u', 'ux': 'ʉ', 'b': 'b', 'ch': 'tʃ', 'd': 'd', 'dh': 'ð', 'dx': 'ɾ', 'el': 'l̩', 'em': 'm̩', 'en': 'n̩', 'f': 'f', 'g': 'ɡ', 'hh': 'h', 'h': 'h', 'jh': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'nx': 'ɾ̃', 'ng': 'ŋ', 'p': 'p', 'q': 'ʔ', 'r': 'ɹ', 's': 's', 'sh': 'ʃ', 't': 't', 'th': 'θ', 'v': 'v', 'w': 'w', 'wh': 'ʍ', 'y': 'j', 'z': 'z', 'zh': 'ʒ', 'h#': 'sil'}



# franco_conv_list=[(a,b) for a,b in zip(franco_symbols,franco_ipa_symbols) if b]
# franco_dict=dict(iter(franco_conv_list))
# franco_dict={'a': 'a', 'b': 'b', 'h': 'h', 't': 't', 'th': 'θ', 'g': 'g', 'j': 'dʒ', '7': 'ħ', 'kh': 'x', 'd': 'd', 'dh': 'ð', 'r': 'r', 'z': 'z', 's': 's', 'sh': 'ʃ', 'S': 'sˤ', 'D': 'dˤ', 'T': 'tˤ', 'DH': 'ðˤ', '3': 'ʕ', 'gh': 'ɣ', 'f': 'f', 'q': 'q', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'w': 'w', 'aa': 'a', 'y': 'j', 'ee': 'i', 'oo': 'u', 'oa': 'ɔ', 'ai': 'æ', 'ei': 'æ', '2': 'ʔ', 'an': 'an', 'un': 'un', 'in': 'in', 'u': 'u', 'o': 'u', 'i': 'i', 'e': 'i', "AA'": 'ʔ', 'AH': 'ʌ', 'Ah': 'ʌ', 'G': 'g', 'sil': 'sil', 'U': 'u', 'I': 'i', '<': 'ʔ', '^': 'ʔ', 'J': 'dʒ'}


# combined_ipa_list=sorted(list(set(ipa_symbols+arpabet_ipa_symbols)))
# combined_ipa_list.append("-")