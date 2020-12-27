import re, os, shelve, unicodedata, sys
if sys.version[0]=="3": 
    import _pickle as cPickle
    from html.parser import HTMLParser
    htmlp = HTMLParser() #To decode html entities in the tika output
else: 
    import cPickle
    import HTMLParser
    htmlp = HTMLParser.HTMLParser() #To decode html entities in the tika output

#from difflib import SequenceMatcher


from difflib import SequenceMatcher


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

def read(fpath):
	file_open=open(fpath)
	content=file_open.read()
	file_open.close()
	return content

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

# Normalizing Unicode String
def norm_unicode(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

#different tokenization schemes
def tok_uc(txt): #basic tokenization of unicode text - removes all punctuation
    txt=re.sub(r"(?u)(\W)",r" \1 ",txt)
    return [v for v in re.split("\s+",txt) if v]

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

def tok(txt): #this is a tokenization scheme to preserve the punctuation also, but it is sensetive to English clitics, instead of splitting isn't as ['isn',"'","t"], it splits ["is","n't"]
    #txt=txt.replace(u'\x01'," ")
    txt=txt.replace(u'\u2019',"'")
    
    txt=txt.replace("'s ","_s ")
    txt=txt.replace("'re ","_re ")
    txt=txt.replace("can't ","cann_t ")
    txt=txt.replace("cannot ","can not")
    txt=txt.replace("n't ","n_t ")
    txt=re.sub("(?u)(\W)",r" \1 ", txt)
    txt=txt.replace("_s ", " 's ")
    txt=txt.replace("_re "," 're ")
    txt=txt.replace("n_t "," n't ")
    
    out=re.split("\s+",txt)
    return [v for v in out if v]





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


#sentence tokenization

def ssplit(txt):
    dot_words=["Mr","Ms","Dr","Art","art","Chap","chap","No","no","rev","Rev","Add"]
    for dw in dot_words:
        txt=txt.replace(dw+".",dw+"._")
    #txt=re.sub("(?u)([\.\?\!\;\u061b])\s",r"\1\n",txt)
    txt=re.sub("(?u)([\.\?\!\;])\s",r"\1\n",txt)
    txt=txt.replace("\xd8\x9b ","\xd8\x9b\n")
    txt=txt.replace("\xd8\x9f ","\xd8\x9f\n")
    txt=txt.replace("\r","\n")
    txt=txt.replace("\t","\n")
    
    txt=txt.replace("._",".")

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

    #output=re.sub("(\d) (\d)",r"\1\2",output) #to normalize the string of the numbers to their bare value
    #output=output.strip()
    return output

def clean_digit_comma(en_txt): #unicode - to normalize all numbers to their value
    #output=re.sub("(\d),(\d)",r"\1\2",en_txt)
    output=en_txt
    return output

def clean_html(html_str):
    html = re.sub("[\n\r\t]+", " ", html_str)
    html=htmlp.unescape(html.decode("utf-8")) #remove html entities
    html=html.encode("utf-8")
    html=re.sub("(<!--.*?-->)", "", html) #remove HTML comments
    html = re.sub('(?i)<script.*?</script>', '', html) #remove javascript
    html = re.sub('(?i)<style.*?</style>', '', html) #remove css
    notags = re.sub("<.*?>", "  ", html) #remove tags
    return notags


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


#List functions
def list_in_list(small,large): #retieves the spans of indexes where a small list exists in a big list
    first=small[0]
    ranges=[]
    for idx, item in enumerate(large):
        if large[idx:idx+len(small)]==small:
            ranges.append((idx,idx+len(small)-1))
    return ranges


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




#OS functions
def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


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
    fopen=open(output_file,'w')
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
                    line='%s\n'%(file_path)
                    fopen.write(line)
            except:
                pass
    fopen.close()
    return all_files


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
