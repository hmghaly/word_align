import re


ipa_symbols=['i', 'y', 'ɨ', 'ʉ', 'ɯ', 'u', 'ɪ', 'ʏ', 'ʊ', 'e', 'ø', 'ɘ', 'ɵ', 'ɤ', 'o', 'ɛ', 'œ', 'ɜ', 'ɞ', 'ʌ', 'ɔ', 'æ', 'ɐ', 'a', 'ɶ', 'ɑ', 'ɒ', 'm', 'ɱ', 'n', 'ɳ', 'ŋ', 'ɴ', 'p', 'b', 't', 'd', 'ʈ', 'ɖ', 'c', 'ɟ', 'k', 'ɡ', 'g', 'q', 'ɢ', 'ʡ', 'ʔ', 'p͡f', 'b͡v', 't̪͡s', 't͡s', 'd͡z', 't͡ʃ', 'd͡ʒ', 'ʈ͡ʂ', 'ɖ͡ʐ', 't͡ɕ', 'd͡ʑ', 'k͡x', 'ɸ', 'β', 'f', 'v', 'θ', 'ð', 's', 'z', 'ʃ', 'ʒ', 'ʂ', 'ʐ', 'ç', 'x', 'ɣ', 'χ', 'ʁ', 'ħ', 'h', 'ɦ', 'w', 'ʋ', 'ɹ', 'ɻ', 'j', 'ɰ', 'ⱱ', 'ɾ', 'ɽ', 'ʙ', 'r', 'ʀ', 'l', 'ɫ', 'ɭ', 'ʎ', 'ʟ', 'ə', 'ɚ', 'ɝ', 'ɹ̩', 'sil', '-', 'sˤ', 'dˤ', 'tˤ', 'ðˤ', 'aʊ', 'aɪ', 'eɪ', 'oʊ', 'ɔɪ', 'tʃ', 'l̩', 'm̩', 'n̩', 'dʒ', 'ɾ̃', 'ʍ', 'aː', 'uː', 'iː', 'ɑ̃', 'ɛ̃', 'ɔ̃', 'ʕ', 'an', 'un', 'in']
 #['ʔ', 'b', 'h', 't', 'θ', 'dʒ', 'ħ', 'x', 'd', 'ð', 'r', 'z', 's', 'ʃ', 'sˤ', 'dˤ', 'tˤ', 'ðˤ', 'ʕ', 'ɣ', 'f', 'q', 'k', 'l', 'm', 'n', 'h', 'w', 'aː', 'j', 'an', 'un', 'in', 'a', 'u', 'i', '', '', 'ɑ', 'ʔ', 'aː', 'aː', 'ʔ', 'ʌ', 'ʌ', 'ʌ', 'g', 'sil', 'u', 'uː', 'i', 'iː', 'ʔ', 'ʔ', 'dʒ']
franco_dict={'a': 'a', 'b': 'b', 'h': 'h', 't': 't', 'th': 'θ', 'g': 'g', 'j': 'dʒ', '7': 'ħ', 'kh': 'x', 'd': 'd', 'dh': 'ð', 'r': 'r', 'z': 'z', 's': 's', 'sh': 'ʃ', 'S': 'sˤ', 'D': 'dˤ', 'T': 'tˤ', 'DH': 'ðˤ', '3': 'ʕ', 'gh': 'ɣ', 'f': 'f', 'q': 'q', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'w': 'w', 'aa': 'a', 'y': 'j', 'ee': 'i', 'oo': 'u', 'oa': 'ɔ', 'ai': 'æ', 'ei': 'æ', '2': 'ʔ', 'an': 'an', 'un': 'un', 'in': 'in', 'u': 'u', 'o': 'u', 'i': 'i', 'e': 'i', "AA'": 'ʔ', 'AH': 'ʌ', 'Ah': 'ʌ', 'G': 'g', 'sil': 'sil', 'U': 'u', 'I': 'i', '<': 'ʔ', '^': 'ʔ', 'J': 'dʒ'}
arpabet_dict={'aa': 'ɑ', 'ae': 'æ', 'ah': 'ʌ', 'ao': 'ɔ', 'aw': 'aʊ', 'ax': 'ə', 'axr': 'ɚ', 'ay': 'aɪ', 'eh': 'ɛ', 'er': 'ɝ', 'ey': 'eɪ', 'ih': 'ɪ', 'ix': 'ɨ', 'iy': 'i', 'ow': 'oʊ', 'oy': 'ɔɪ', 'uh': 'ʊ', 'uw': 'u', 'ux': 'ʉ', 'b': 'b', 'ch': 'tʃ', 'd': 'd', 'dh': 'ð', 'dx': 'ɾ', 'el': 'l̩', 'em': 'm̩', 'en': 'n̩', 'f': 'f', 'g': 'ɡ', 'hh': 'h', 'h': 'h', 'jh': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'nx': 'ɾ̃', 'ng': 'ŋ', 'p': 'p', 'q': 'ʔ', 'r': 'ɹ', 's': 's', 'sh': 'ʃ', 't': 't', 'th': 'θ', 'v': 'v', 'w': 'w', 'wh': 'ʍ', 'y': 'j', 'z': 'z', 'zh': 'ʒ', 'h#': 'sil'}
buckwalter_dict={'A': 'ʔ', 'b': 'b', 'p': 'h', 't': 't', 'v': 'θ', 'j': 'dʒ', 'H': 'ħ', 'x': 'x', 'd': 'd', '*': 'ð', 'r': 'r', 'z': 'z', 's': 's', '$': 'ʃ', 'S': 'sˤ', 'D': 'dˤ', 'T': 'tˤ', 'Z': 'ðˤ', 'E': 'ʕ', 'g': 'ɣ', 'f': 'f', 'q': 'q', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'h': 'h', 'w': 'w', 'Y': 'aː', 'y': 'j', 'F': 'an', 'N': 'un', 'K': 'in', 'a': 'a', 'u': 'u', 'i': 'i', 'AA': 'aː', "A'": 'ʔ', 'aa': 'aː', "AA'": 'ʔ', 'AH': 'ʌ', 'ah': 'ʌ', 'Ah': 'ʌ', 'G': 'g', 'sil': 'sil', 'U': 'u', 'uu': 'uː', 'I': 'i', 'ii': 'iː', '<': 'ʔ', '^': 'ʔ', 'J': 'dʒ'}
ipa_ft_dict={'i': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:close'], 'y': ['ft:vowel', 'ft:front', 'ft:rounded', 'ft:close'], 'ɨ': ['ft:vowel', 'ft:central', 'ft:unrounded', 'ft:close'], 'ʉ': ['ft:vowel', 'ft:central', 'ft:rounded', 'ft:close'], 'ɯ': ['ft:vowel', 'ft:back', 'ft:unrounded', 'ft:close'], 'u': ['ft:vowel', 'ft:back', 'ft:rounded', 'ft:close'], 'ɪ': ['ft:vowel', 'ft:near-front', 'ft:unrounded', 'ft:near-close'], 'ʏ': ['ft:vowel', 'ft:near-front', 'ft:rounded', 'ft:near-close'], 'ʊ': ['ft:vowel', 'ft:near-back', 'ft:rounded', 'ft:near-close'], 'e': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:close-mid'], 'ø': ['ft:vowel', 'ft:front', 'ft:rounded', 'ft:close-mid'], 'ɘ': ['ft:vowel', 'ft:central', 'ft:unrounded', 'ft:close-mid'], 'ɵ': ['ft:vowel', 'ft:central', 'ft:rounded', 'ft:close-mid'], 'ɤ': ['ft:vowel', 'ft:back', 'ft:unrounded', 'ft:close-mid'], 'o': ['ft:vowel', 'ft:back', 'ft:rounded', 'ft:close-mid'], 'ɛ': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:open-mid'], 'œ': ['ft:vowel', 'ft:front', 'ft:rounded', 'ft:open-mid'], 'ɜ': ['ft:vowel', 'ft:central', 'ft:unrounded', 'ft:open-mid'], 'ɞ': ['ft:vowel', 'ft:central', 'ft:rounded', 'ft:open-mid'], 'ʌ': ['ft:vowel', 'ft:back', 'ft:unrounded', 'ft:open-mid'], 'ɔ': ['ft:vowel', 'ft:back', 'ft:rounded', 'ft:open-mid'], 'æ': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:near-open'], 'ɐ': ['ft:vowel', 'ft:central', 'ft:unrounded', 'ft:near-open'], 'a': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:open'], 'ɶ': ['ft:vowel', 'ft:front', 'ft:rounded', 'ft:open'], 'ɑ': ['ft:vowel', 'ft:back', 'ft:unrounded', 'ft:open'], 'ɒ': ['ft:vowel', 'ft:back', 'ft:rounded'], 'm': ['ft:voiced', 'ft:nasal', 'ft:bilabial'], 'ɱ': ['ft:voiced', 'ft:nasal', 'ft:labio-dental'], 'n': ['ft:voiced', 'ft:nasal', 'ft:alveolar'], 'ɳ': ['ft:voiced', 'ft:nasal', 'ft:retroflex'], 'ŋ': ['ft:voiced', 'ft:nasal', 'ft:velar'], 'ɴ': ['ft:voiced', 'ft:nasal', 'ft:uvular'], 'p': ['ft:voiceless', 'ft:plosive', 'ft:bilabial'], 'b': ['ft:voiced', 'ft:plosive', 'ft:bilabial'], 't': ['ft:voiceless', 'ft:plosive', 'ft:alveolar'], 'd': ['ft:voiced', 'ft:plosive', 'ft:alveolar'], 'ʈ': ['ft:voiceless', 'ft:plosive', 'ft:retroflex'], 'ɖ': ['ft:voiced', 'ft:plosive', 'ft:retroflex'], 'c': ['ft:voiceless', 'ft:plosive', 'ft:palatal'], 'ɟ': ['ft:voiced', 'ft:plosive', 'ft:palatal'], 'k': ['ft:voiceless', 'ft:plosive', 'ft:velar'], 'ɡ': ['ft:voiced', 'ft:plosive', 'ft:velar'], 'g': ['ft:voiced', 'ft:plosive', 'ft:velar'], 'q': ['ft:voiceless', 'ft:plosive', 'ft:uvular'], 'ɢ': ['ft:voiced', 'ft:plosive', 'ft:uvular'], 'ʡ': ['ft:voiceless', 'ft:plosive', 'ft:pharyngeal'], 'ʔ': ['ft:voiceless', 'ft:plosive', 'ft:glottal'], 'p͡f': ['ft:voiceless', 'ft:affricate', 'ft:labio-dental'], 'b͡v': ['ft:voiced', 'ft:affricate', 'ft:dental'], 't̪͡s': ['ft:voiceless', 'ft:affricate', 'ft:dental'], 't͡s': ['ft:voiceless', 'ft:affricate', 'ft:alveolar'], 'd͡z': ['ft:voiced', 'ft:affricate', 'ft:alveolar'], 't͡ʃ': ['ft:voiceless', 'ft:affricate', 'ft:post-alveolar'], 'd͡ʒ': ['ft:voiced', 'ft:affricate', 'ft:post-alveolar'], 'ʈ͡ʂ': ['ft:voiceless', 'ft:affricate', 'ft:retroflex'], 'ɖ͡ʐ': ['ft:voiced', 'ft:affricate', 'ft:retroflex'], 't͡ɕ': ['ft:voiceless', 'ft:affricate', 'ft:palatal'], 'd͡ʑ': ['ft:voiced', 'ft:affricate', 'ft:palatal'], 'k͡x': ['ft:voiceless', 'ft:affricate', 'ft:velar'], 'ɸ': ['ft:voiceless', 'ft:fricative', 'ft:bilabial'], 'β': ['ft:voiced', 'ft:fricative', 'ft:bilabial'], 'f': ['ft:voiceless', 'ft:fricative', 'ft:labio-dental'], 'v': ['ft:voiced', 'ft:fricative', 'ft:labio-dental'], 'θ': ['ft:voiceless', 'ft:fricative', 'ft:dental'], 'ð': ['ft:voiced', 'ft:fricative', 'ft:dental'], 's': ['ft:voiceless', 'ft:fricative', 'ft:alveolar'], 'z': ['ft:voiced', 'ft:fricative', 'ft:alveolar'], 'ʃ': ['ft:voiceless', 'ft:fricative', 'ft:post-alveolar'], 'ʒ': ['ft:voiced', 'ft:fricative', 'ft:post-alveolar'], 'ʂ': ['ft:voiceless', 'ft:fricative', 'ft:retroflex'], 'ʐ': ['ft:voiced', 'ft:fricative', 'ft:palatal'], 'ç': ['ft:voiceless', 'ft:fricative', 'ft:palatal'], 'x': ['ft:voiceless', 'ft:fricative', 'ft:velar'], 'ɣ': ['ft:voiced', 'ft:fricative', 'ft:velar'], 'χ': ['ft:voiceless', 'ft:fricative', 'ft:uvular'], 'ʁ': ['ft:voiced', 'ft:fricative', 'ft:uvular'], 'ħ': ['ft:voiceless', 'ft:fricative', 'ft:pharyngeal'], 'h': ['ft:voiceless', 'ft:fricative', 'ft:glottal'], 'ɦ': ['ft:voiced', 'ft:fricative', 'ft:glottal'], 'w': ['ft:voiced', 'ft:approximant', 'ft:bilabial'], 'ʋ': ['ft:voiced', 'ft:approximant', 'ft:labio-dental'], 'ɹ': ['ft:voiced', 'ft:approximant', 'ft:alveolar'], 'ɻ': ['ft:voiced', 'ft:approximant', 'ft:retroflex'], 'j': ['ft:voiced', 'ft:approximant', 'ft:palatal'], 'ɰ': ['ft:voiced', 'ft:approximant', 'ft:velar'], 'ⱱ': ['ft:voiced', 'ft:flap', 'ft:labio-dental'], 'ɾ': ['ft:voiced', 'ft:flap', 'ft:alveolar'], 'ɽ': ['ft:voiced', 'ft:flap', 'ft:retroflex'], 'ʙ': ['ft:voiced', 'ft:trill', 'ft:bilabial'], 'r': ['ft:voiced', 'ft:trill', 'ft:alveolar'], 'ʀ': ['ft:voiced', 'ft:trill', 'ft:uvular'], 'l': ['ft:voiced', 'ft:lateral-approximant', 'ft:alveolar'], 'ɫ': ['ft:voiced', 'ft:lateral-approximant', 'ft:alveolar'], 'ɭ': ['ft:voiced', 'ft:lateral-approximant', 'ft:retroflex'], 'ʎ': ['ft:voiced', 'ft:lateral-approximant', 'ft:palatal'], 'ʟ': ['ft:voiced', 'ft:lateral-approximant', 'ft:velar'], 'ə': ['ft:schwa'], 'ɚ': ['ft:schwa'], 'ɝ': ['ft:schwa'], 'ɹ̩': ['ft:voiced', 'ft:approximant', 'ft:alveolar'], 'sil': ['ft:silence'], '-': ['ft:other'], 'sˤ': ['ft:voiceless', 'ft:fricative', 'ft:alveolar', 'ft:emphatic'], 'dˤ': ['ft:voiced', 'ft:plosive', 'ft:alveolar', 'ft:emphatic'], 'tˤ': ['ft:voiceless', 'ft:plosive', 'ft:alveolar', 'ft:emphatic'], 'ðˤ': ['ft:voiced', 'ft:fricative', 'ft:dental', 'ft:emphatic'], 'aʊ': ['ft:vowel', 'ft:front', 'ft:near-back', 'ft:rounded', 'ft:unrounded', 'ft:open', 'ft:near-close', 'ft:diphthong'], 'aɪ': ['ft:vowel', 'ft:front', 'ft:near-front', 'ft:unrounded', 'ft:near-close', 'ft:diphthong'], 'eɪ': ['ft:vowel', 'ft:front', 'ft:near-front', 'ft:unrounded', 'ft:close-mid', 'ft:near-close', 'ft:diphthong'], 'oʊ': ['ft:vowel', 'ft:back', 'ft:near-back', 'ft:rounded', 'ft:close-mid', 'ft:near-close', 'ft:diphthong'], 'ɔɪ': ['ft:vowel', 'ft:near-front', 'ft:back', 'ft:rounded', 'ft:unrounded', 'ft:open-mid', 'ft:near-close', 'ft:diphthong'], 'tʃ': ['ft:voiceless', 'ft:affricate', 'ft:post-alveolar', 'ft:combined'], 'l̩': ['ft:voiced', 'ft:lateral-approximant', 'ft:alveolar', 'ft:syllabic'], 'm̩': ['ft:voiced', 'ft:nasal', 'ft:bilabial', 'ft:syllabic'], 'n̩': ['ft:voiced', 'ft:nasal', 'ft:alveolar', 'ft:syllabic'], 'dʒ': ['ft:voiced', 'ft:affricate', 'ft:post-alveolar', 'ft:combined'], 'ɾ̃': ['ft:voiced', 'ft:nasal', 'ft:flap'], 'ʍ': ['ft:voiceless', 'ft:fricative', 'ft:bilabial', 'ft:velar'], 'aː': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:open', 'ft:long'], 'uː': ['ft:vowel', 'ft:back', 'ft:rounded', 'ft:close', 'ft:long'], 'iː': ['ft:vowel', 'ft:front', 'ft:unrounded', 'ft:close', 'ft:long'], 'ɑ̃': ['ft:vowel', 'ft:nasal', 'ft:front', 'ft:unrounded', 'ft:open'], 'ɛ̃': ['ft:vowel', 'ft:nasal', 'ft:front', 'ft:unrounded', 'ft:open-mid'], 'ɔ̃': ['ft:vowel', 'ft:nasal', 'ft:back', 'ft:rounded', 'ft:open-mid'], 'ʕ': ['ft:voiced', 'ft:fricative', 'ft:pharyngeal'], 'an': ['ft:voiced', 'ft:vowel', 'ft:nasal', 'ft:front', 'ft:unrounded', 'ft:alveolar', 'ft:open', 'ft:combined'], 'un': ['ft:voiced', 'ft:vowel', 'ft:back', 'ft:rounded', 'ft:alveolar', 'ft:combined'], 'in': ['ft:voiced', 'ft:vowel', 'ft:front', 'ft:unrounded', 'ft:alveolar', 'ft:combined']}

#if need to update

def franco2ipa(franco_text):
  phones=franco2phones(franco_text)
  ipa_phones=[franco_dict.get(v,v) for v in phones]
  return ipa_phones

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
try:
  import cmudict
  cur_cmu=cmudict.dict()
except: pass

def word2ipa(word0):
  word0=word0.replace("’","'")
  arpabet_out=cur_cmu.get(word0.lower(),[""])[0]
  if arpabet_out=="": return []
  ipa_out0=[arpabet2ipa(v) for v in arpabet_out]
  return ipa_out0 


#===========================================
#Converting an Arabic word to franco, split it and analyze it

ar_shape_dict={'أ': ['أ', 'ـأ'], 'ب': ['ب', 'بـ', 'ـبـ', 'ـب'], 'ت': ['ت', 'تـ', 'ـتـ', 'ـت'], 'ث': ['ث', 'ثـ', 'ـثـ', 'ـث'], 'ج': ['ج', 'جـ', 'ـجـ', 'ـج'], 'ح': ['ح', 'حـ', 'ـحـ', 'ـح'], 'خ': ['خ', 'خـ', 'ـخـ', 'ـخ'], 'د': ['د', 'ـد'], 'ذ': ['ذ', 'ـذ'], 'ر': ['ر', 'ـر'], 'ز': ['ز', 'ـز'], 'س': ['س', 'سـ', 'ـسـ', 'ـس'], 'ش': ['ش', 'شـ', 'ـشـ', 'ـش'], 'ص': ['ص', 'صـ', 'ـصـ', 'ـص'], 'ض': ['ض', 'ضـ', 'ـضـ', 'ـض'], 'ط': ['ط', 'طـ', 'ـطـ', 'ـط'], 'ظ': ['ظ', 'ظـ', 'ـظـ', 'ـظ'], 'ع': ['ع', 'عـ', 'ـعـ', 'ـع'], 'غ': ['غ', 'غـ', 'ـغـ', 'ـغ'], 'ف': ['ف', 'فـ', 'ـفـ', 'ـف'], 'ق': ['ق', 'قـ', 'ـقـ', 'ـق'], 'ك': ['ك', 'كـ', 'ـكـ', 'ـك'], 'ل': ['ل', 'لـ', 'ـلـ', 'ـل'], 'م': ['م', 'مـ', 'ـمـ', 'ـم'], 'ن': ['ن', 'نـ', 'ـنـ', 'ـن'], 'هـ': ['ه', 'هـ', 'ـهـ', 'ـه'], 'و': ['و', 'ـو'], 'ي': ['ي', 'يـ', 'ـيـ', 'ـي'], 'ء': ['ء'], 'لا': ['لا', 'ـلا'], 'ئ': ['ئ', 'ئـ', 'ـئـ', 'ـئ'], 'ؤ': ['ؤ', 'ـؤ'], 'ة': ['ة', 'ـة'], 'ى': ['ى', 'ـى'], 'إ': ['إ', 'ـإ'], 'آ': ['آ', 'ـآ'], 'لأ': ['لأ', 'ـلأ'], 'لإ': ['لإ', 'ـلإ'], 'لآ': ['لآ', 'ـلآ']}    
romanization_dict={'أ': ('2', 'a'), 'ا': ('aa', 'a'), 'إ': ('2i', 'i'), 'آ': ('2aa', 'aa'), 'ى': ('aa', ''), 'ب': ('b', ''), 'ت': ('t', ''), 'ث': ('th', ''), 'ج': ('j', ''), 'ح': ('7', ''), 'خ': ('kh', ''), 'د': ('d', ''), 'ذ': ('dh', ''), 'ر': ('r', ''), 'ز': ('z', ''), 'س': ('s', ''), 'ش': ('sh', ''), 'ص': ('S', ''), 'ض': ('D', ''), 'ط': ('T', ''), 'ظ': ('DH', ''), 'ع': ('3', ''), 'غ': ('gh', ''), 'ف': ('f', ''), 'ق': ('q', ''), 'ك': ('k', ''), 'ل': ('l', ''), 'م': ('m', ''), 'ن': ('n', ''), 'ه': ('h', ''), 'و': ('oo', 'w'), 'ي': ('ee', 'y'), 'ة': ('h', ''), 'ئ': ('2', ''), 'ؤ': ('2', ''), 'ء': ('2', ''), 'َ': ('a', ''), 'ِ': ('i', ''), 'ُ': ('u', ''), 'ٌ': ('un', ''), 'ً': ('an', ''), 'ٍ': ('in', ''), 'ّ': ('x', '')}

class analyze_ar_word: #analyze a word with diacritics in different ways
  def __init__(self,word0,shape_dict0=ar_shape_dict,romanize_dict0=romanization_dict):
    self.word=word0
    self.shape_dict=shape_dict0
    self.romanize_dict=romanize_dict0
    #first split the word into chunks, based on diacritics
    self.chunks=[]
    new_chunk=""
    self.plain=""
    for w0 in self.word:
      if w0.isalpha() or w0==" ":
        self.plain+=w0
        if  new_chunk!="": self.chunks.append(new_chunk)
        new_chunk=w0 
      else: new_chunk+=w0
    if  new_chunk!="": self.chunks.append(new_chunk)
    #get the shape
    self.word_letter_shapes_plain=[]
    self.word_letter_shapes=[]
    prev_shapes=[]
    
    for i0,ch in enumerate(self.chunks):
      att_before,att_after=False,False #attach before and attach after
      w0=ch[0]
      cur_shape=w0
      possible_shapes=shape_dict0.get(w0,[])

      if i0==0 and len(possible_shapes)>2: att_after=True #cur_shape=w0+"ـ"
      elif i0==len(self.chunks)-1:
        if len(prev_shapes)>2: att_before=True #cur_shape="ـ"+w0
      else:
        if len(prev_shapes)>2: att_before=True # cur_shape="ـ"+w0
        if len(possible_shapes)>2:  att_after=True
          #cur_shape=cur_shape+"ـ"
      prev_shapes=possible_shapes
      cur_shape=w0
      if att_before: cur_shape="ـ"+cur_shape
      if att_after: cur_shape=cur_shape+"ـ"
      self.word_letter_shapes_plain.append(cur_shape)
      #print(cur_shape)
      
      cur_shape=ch
      if att_before: cur_shape="ـ"+cur_shape
      if att_after: cur_shape=cur_shape+"ـ"
      self.word_letter_shapes.append(cur_shape)
  
    #get the sound
    self.romanized_chunks=[]
    prev_romanized=""
    for ch_i,ch in enumerate(self.chunks):
      found=self.romanize_dict.get(ch[0],ch[0])
      first=found[0]
      if ch_i==0 and found[1]!="": first=found[1]
      #first=self.romanize_dict[ch[0]][0]
      
      #cur_romanized_chunk=first
      dia0="".join([self.romanize_dict.get(v,["",""])[0] for v in ch[1:]]) #convert the diacritics part of the chunk
      has_shaddah=False
      if "x" in dia0: has_shaddah=True #in the conversion sheet, shadda is converted to x
      dia0=dia0.replace("x","")
      if dia0 and found[1]!="": first=found[1] 
      if ch_i>0 and "2" in found[0]: first="2" #imra2ah

      if prev_romanized.endswith("a") and ch[0] in "وي" and found[1]!="": first=found[1]
      if has_shaddah and found[1]!="": first=found[1]

      cur_romanized_chunk=first+dia0
      if has_shaddah: cur_romanized_chunk=first+cur_romanized_chunk #shaddah

      if ch_i==0 and cur_romanized_chunk=="aa" and ch[0]!="آ":  cur_romanized_chunk="a" #cheap hacks to fix certain fringe cases
      if cur_romanized_chunk=="ai":  cur_romanized_chunk="i"
      if cur_romanized_chunk=="ii":  cur_romanized_chunk="i"
      if cur_romanized_chunk=="au":  cur_romanized_chunk="u"
      if cur_romanized_chunk=="aan":  cur_romanized_chunk="an"




      self.romanized_chunks.append(cur_romanized_chunk)
      #print(cur_romanized_chunk)
      prev_romanized=cur_romanized_chunk
    self.romanized=""
    for s_i, rom in enumerate(self.romanized_chunks):
      next_chunk=""
      if s_i<len(self.romanized_chunks)-1: next_chunk=self.romanized_chunks[s_i+1]
      if rom.endswith("i") and next_chunk=="ee": rom=rom[:-1] #avoid iee for kasrah before yaa2
      if rom.endswith("u") and next_chunk=="oo": rom=rom[:-1]
      if rom.endswith("a") and next_chunk=="aa": rom=rom[:-1]
      self.romanized+=rom


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