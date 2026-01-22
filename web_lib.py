#a librry for all the utilities we need for scraping data from the web
import requests, re, sys, time, json, os
import string
import shutil
from urllib.parse import urljoin, urlsplit
from urllib.parse import unquote
import urllib.parse

#import urllib.parse

sys.path.append("code_utils")

cur_lib_path=os.path.split(__file__)[0]
sys.path.append(cur_lib_path)


import general
#from bs4 import BeautifulSoup
#from lxml.html import parse

#This library is for accessing web pages, reading and processing their content
#and also for templating web pages by DOM manipulation


#17 April 2025
def download_file(url, file_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        print(f"Image downloaded successfully and saved as {file_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")



def download_file_OLD(file_url):
  with requests.Session() as sess0:
    download = sess0.get(file_url)
    decoded_content0 = download.content.decode('utf-8')
  return decoded_content0

#23 June 2024
def get_attrs(tag0): #get attributes within an html/xml tags
  tag0=tag0.replace("'",'"')
  found_attrs0=re.findall(r'(\S+)="(.+?)"[\W\s$]',tag0) #'''(\S+)=["'](.+?)["']'''
  final_dict={}
  for a,b in found_attrs0:
    b=re.sub(r'"(\S)',r"'\1",b)
    final_dict[a]=b
  return final_dict#dict(iter(found_attrs0))


# def get_attrs(tag0): #get attributes within an html/xml tags
#   tag0=tag0.replace("'",'"')
#   found_attrs0=re.findall('(\S+)="(.+?)"\b',tag0) #'''(\S+)=["'](.+?)["']'''
#   return dict(iter(found_attrs0))


# def get_attrs(tag0): #get attributes within an html/xml tags
#   found_attrs0=re.findall('(\S+)=(\S+)',tag0) #'''(\S+)=["'](.+?)["']'''
#   final_attrs=[]
#   for at_key0,at_val0 in found_attrs0:
#     at_val0=at_val0.strip("'").strip('"')
#     final_attrs.append((at_key0,at_val0))
#   return dict(iter(final_attrs))


# def get_attrs(tag0): #get attributes within an html/xml tags
#   found_attrs0=re.findall('(\S+)="(.+?)"',tag0) #'''(\S+)=["'](.+?)["']'''
#   found_attrs1=re.findall("(\S+)='(.+?)'",tag0) #"(\S+)='(.+?)'"
#   found_attrs= found_attrs0+found_attrs1#re.findall('''(\S+)=["'](.+?)["']''',tag0)
#   #found_attrs=re.findall('''(\S+)=["'](.*?)["']''',tag0)
#   return dict(iter(found_attrs))

class element:
  def __init__(self) -> None:
      self.name=""
      self.id=""
      self.assigned_id=""
      self.className=""
      self.class_list=[]
      self.tag_name=""
      self.attrs={}
      self.parent=None #must have only one parent
      self.children=[] #only direct children - not recursive
      self.tag_type=None #comment/stand-alone/text-node
      self.open_tag=""
      self.close_tag=""
      self.text="" #if it is a text node
      self.open_tag_i0=None
      self.open_tag_i1=None
      self.close_tag_i0=None
      self.close_tag_i1=None
      self.inner_html=""
      self.outer_html=""
      self.href=""
      self.src=""

class DOM:
  def __init__(self,content,params={}) -> None:
    self.content=content
    self.tag_dict={} #linking assigned IDs with element objects
    self.id_dict={} #mapping actual IDs with assigned IDs
    self.actual_ids=[] #a list of IDs actually used, can help us spot duplicate IDs
    self.class_id_dict={} #map each class name to the assigned ids of elements with that class
    self.text_items=[]
    self.text=""
    self.simple_tag_text_items=[] #non-nested items with a text
    self.text_items_tags=[]
    self.tag_id_list=[] #list of assigned IDs
    self.all_links=[]
    self.all_images=[]
    self.xpath_list=[] #list of open tags with their attrs, and the corresponding tag ID
    self.mismatch_debug_items=[]
    self.description=""
    self.title=""
    self.keywords=""
    self.lang=""
    self.meta_lang=""
    apply_unescape=params.get("apply_unescape",False)
    copy_with_tag_ids=params.get("copy_with_tag_ids",False)

    if apply_unescape: self.content=general.unescape(self.content) 
    #tags=list(re.finditer('<([^<>]*?)>', self.content)) #'<[^<>]*?>|\<\!\-\-.+?\-\-\>'
    tags=list(re.finditer(r'<[^<>]*?>|\<\!\-\-.+?\-\-\>', self.content))
    open_tags=[""]
    open_tags_attr_xpath_list=[]
    tag_counter_dict={}
    start_i=0
    last_open_tag_str=""
    self.content_copy_with_ids=""
    for ti_, t in enumerate(tags):
      tag_str,tag_start,tag_end=t.group(0), t.start(), t.end()
      tag_str_lower=tag_str.lower()
      tag_name=re.findall(r'</?(.+?)[\s>]',tag_str_lower)[0]
      tag_type=""


      if tag_str.startswith('</'): tag_type="closing"
      elif tag_str.startswith('<!'): tag_type="comment"
      elif tag_str_lower.endswith('/>') or tag_name in ["input","link","meta","img","br","hr"]: tag_type="s" #standalone
      else: tag_type="opening"

      if len(open_tags)>0 and open_tags[-1].split("_")[0]=="script": #avoid identifying < > chars in javascript as tags
      	if not (tag_name=="script" and tag_type== "closing"): continue

      inter_text=self.content[start_i:tag_start] #intervening text since last tag
      last_open_tag=open_tags[-1]
      if len(inter_text)>0:
        if not last_open_tag.lower().split("_")[0] in ["script","style","noscript","xml"]: 
          inter_text_stripped=inter_text.strip('\r\n\t ').replace("&times;","")
          if inter_text_stripped!="": 
            inter_text+=" "
            self.text_items.append(inter_text)
            self.text_items_tags.append((last_open_tag_str,inter_text))
            if tag_type=="closing" and len(open_tags)>0 and tag_name==open_tags[-1].split("_")[0]: self.simple_tag_text_items.append((last_open_tag_str,inter_text_stripped))

        text_node_count=tag_counter_dict.get("text_node",0)
        text_node_id="text_node_%s"%text_node_count
        tag_counter_dict["text_node"]=text_node_count+1
        text_el=element()
        text_el.text=inter_text
        text_el.tag_type="text_node"
        text_el.parent=self.tag_dict.get(open_tags[-1])
        self.tag_dict[text_node_id]=text_el

        if text_el.parent!=None: self.tag_dict[open_tags[-1]].children+=[text_node_id]
      start_i=tag_end

      if not tag_type in ["comment","s"]: last_open_tag_str=tag_str

      if tag_name.startswith("h") or tag_name in ["p","div","br","li"]: 
        self.text_items.append("<br>")
        self.text_items_tags.append((last_open_tag_str,"<br>"))

      tag_count=tag_counter_dict.get(tag_name,0)
      assigned_tag_id="%s_%s"%(tag_name,tag_count)
      tag_counter_dict[tag_name]=tag_count+1
      cur_el=element()
      cur_el.assigned_id=assigned_tag_id

      tag_copy=str(tag_str) #add IDs if needed
      if tag_type=="opening" and not ' id=' in tag_copy:
        first_part=tag_copy.split(" ")[0]
        tag_copy=tag_copy.replace(first_part,first_part+f' id="{assigned_tag_id}" ')
      self.content_copy_with_ids+=tag_copy


      if tag_type=="closing" and len(open_tags)>0: #if it is a closing tag,
        if tag_name==open_tags[-1].split("_")[0]: #we check if the tag name matches the last open tag name
          cur_open_tag_id=open_tags[-1]
          el_to_close=self.tag_dict[open_tags[-1]] #and then identify the element corresponding to the last open tag
          tmp_open_i0,tmp_open_i1=el_to_close.open_tag_i0,el_to_close.open_tag_i1 #retrieve the start and end indexes/locations from the open tag
          tmp_inner_html=self.content[tmp_open_i1:tag_start] #then get inner html
          tmp_outer_html=self.content[tmp_open_i0:tag_end] #then outer html
          el_to_close.inner_html=tmp_inner_html #and assign these to the retrieved element object
          el_to_close.outer_html=tmp_outer_html
          if tag_name=="title": self.title=tmp_inner_html
          if tag_name=="a": self.all_links.append(el_to_close)

          self.content_copy_with_ids+=tmp_inner_html

          self.tag_dict[open_tags[-1]]=el_to_close
          
            
          open_tags=open_tags[:-1]
          if open_tags_attr_xpath_list: open_tags_attr_xpath_list=open_tags_attr_xpath_list[:-1]
          self.xpath_list.append((open_tags_attr_xpath_list,cur_open_tag_id))
        else: 
          debug_line_items0=("open_tags",open_tags, "tag_name",tag_name,"tag_str",tag_str,self.content[tag_end-200:tag_end])
          self.mismatch_debug_items.append(debug_line_items0)
          #print("open_tags",open_tags, "tag_name",tag_name,"tag_str",tag_str,self.content[tag_end-200:tag_end])



      else: #if it is an openning or stand alone tags
        self.tag_id_list.append(assigned_tag_id)
        cur_el=element()
        cur_el.open_tag=tag_str 
        cur_el.open_tag_i0,cur_el.open_tag_i1=tag_start,tag_end
        cur_el.tag_name=tag_name
        
        
        cur_el.assigned_id=assigned_tag_id
        cur_el.tag_type=tag_type
        cur_el.attrs=get_attrs(tag_str)
        cur_id=cur_el.attrs.get("id")
        cur_class_str=cur_el.attrs.get("class","")
        cur_class_list=[v for v in cur_class_str.split(" ") if v]

        if tag_name=="meta" and cur_el.attrs.get("name","").lower()=="description":self.description=cur_el.attrs.get("content","")
        if tag_name=="meta" and cur_el.attrs.get("name","").lower()=="keywords":self.keywords=cur_el.attrs.get("content","")
        if tag_name=="meta" and cur_el.attrs.get("http-equiv","")=="content-language":self.meta_lang=cur_el.attrs.get("content","")
        if tag_name=="html": self.lang=cur_el.attrs.get("lang","")
        if cur_el.attrs.get("href")!=None: cur_el.href=cur_el.attrs.get("href") #self.all_links.append(cur_el.attrs.get("href"))
        if cur_el.attrs.get("src")!=None: cur_el.src=cur_el.attrs.get("src")
        if tag_name=="img": self.all_images.append(cur_el)

        if cur_id!=None:
          cur_el.id=cur_id
          self.actual_ids.append(cur_id)
          self.id_dict[cur_id]=assigned_tag_id
        if tag_name in ["script","style"]: cur_el.tag_type=tag_name
        cur_el.parent=self.tag_dict.get(open_tags[-1])
        #print("cur_el.parent",cur_el.parent,"assigned_tag_id",assigned_tag_id)
        if cur_el.parent!=None: self.tag_dict[open_tags[-1]].children+=[assigned_tag_id]
        #else: print("Parent not found:", open_tags[-1], "tag info", assigned_tag_id,tag_type,tag_str_lower,"open_tags",open_tags)


        if tag_type=="opening": 
          cur_el.close_tag='</%s>'%tag_name #for regular tags with open-close
          open_tags.append(assigned_tag_id)
          open_tags_attr_xpath_list.append((tag_name,cur_el.attrs))
        self.tag_dict[assigned_tag_id]=cur_el
        for cls0 in cur_class_list:
          self.class_id_dict[cls0]=self.class_id_dict.get(cls0,[])+[assigned_tag_id]
    self.text_items="".join(self.text_items).split("<br>")
    self.text_items=[v for v in self.text_items if v]
    self.text="\n".join(self.text_items)

    #self.page_info_dict

  def get_html(self,assigned_tag_id0,html_content0=''):
    cur_el=self.tag_dict.get(assigned_tag_id0)
    if cur_el==None: return html_content0
    html_content0+=cur_el.open_tag
    html_content0+=cur_el.text
    children=cur_el.children
    for ch0 in children:
      html_content0=self.get_html(ch0,html_content0)
      #ch_obj=self.tag_dict.get(ch0)
      #html_content0+=ch_obj.
    html_content0+=cur_el.close_tag
    return html_content0
  def get_el_by_tag_name(self,tag_name):
    temp_items=[]
    for a,b in self.tag_dict.items():
      if a.startswith(tag_name+"_"):
        tag_num=a.split("_")[-1]
        tag_num_int=int(tag_num)
        temp_items.append((tag_num_int,b.outer_html))
    #items0=list(self.tag_dict.items())
    temp_items.sort()
    cur_items=[v[1] for v in temp_items]
    #cur_items=[b.outer_html for a,b in items0 if a.startswith(tag_name+"_")]
    return cur_items

  def get_el_by_id(self,actual_id):
    cur_assigned_id=self.id_dict.get(actual_id)
    if cur_assigned_id==None: return None
    return self.tag_dict[cur_assigned_id]
  def get_el_by_class(self,class_name0):
    cur_ids=self.class_id_dict.get(class_name0,[])
    el_list=[]
    for id0 in cur_ids: el_list.append(self.tag_dict[id0])
    return el_list
  def apply_content_by_id(self,id0,el_content0,new_attrs_dict0={}):
    if el_content0!=None: el_content0=el_content0.strip()
    repl_list=[]
    cur_el=self.get_el_by_id(id0)
    if cur_el==None: return repl_list
    new_open_tag=cur_el.open_tag
    if new_attrs_dict0!={}:
      cur_attrs=cur_el.attrs
      for a0,b0 in new_attrs_dict0.items():
        cur_attrs[a0]=b0
      new_open_tag=create_open_tag(cur_el.tag_name,cur_attrs)
    #cur_outer_html=cur_el.outer_html

    cur_outer_html=cur_el.open_tag+cur_el.inner_html+cur_el.close_tag #to fix img src replacement problem - 8 Oct 2024

    if el_content0: new_outer_html=new_open_tag+el_content0+cur_el.close_tag
    elif el_content0==None: new_outer_html=new_open_tag+cur_el.inner_html+cur_el.close_tag
    else: new_outer_html=""
    # print("cur_outer_html",cur_outer_html)
    # print("new_outer_html",new_outer_html)
    
    #to fix layers of nested elements, if new content is None, we replace only the tag - 8 Oct 2024
    if el_content0!=None: repl_list.append((cur_outer_html,new_outer_html))
    else: repl_list.append((cur_el.open_tag,new_open_tag))
    
    return repl_list
  def apply_content_by_class(self,class0,el_content0,new_attrs_dict0={},except_ids=[]):
    if el_content0!=None: el_content0=el_content0.strip()
    repl_list=[]
    cur_el_list=self.get_el_by_class(class0)
    for cur_el in cur_el_list:
      new_open_tag=cur_el.open_tag
      cur_attrs=cur_el.attrs
      if cur_attrs.get("id","") in except_ids: continue
      if new_attrs_dict0!={}:
        
        for a0,b0 in new_attrs_dict0.items():
          cur_attrs[a0]=b0
        new_open_tag=create_open_tag(cur_el.tag_name,cur_attrs)      
      cur_outer_html=cur_el.outer_html
      if el_content0: new_outer_html=new_open_tag+el_content0+cur_el.close_tag
      elif el_content0==None: new_outer_html=new_open_tag+cur_el.inner_html+cur_el.close_tag
      else: new_outer_html=""
      repl_list.append((cur_outer_html,new_outer_html))
    return repl_list
  def get_repl_pairs(self,cur_repl_dict0,except_ids=[],id_suffix=None):
    repl_pairs=[]
    for key0,val0 in cur_repl_dict0.items():
      if val0==None: new_content0,new_attrs0=val0,{} # 8 October 2024 - allow None value as an input to repl dict
      elif type(val0) is str: new_content0,new_attrs0=val0,{} # 8 Oct 2024
      else: new_content0,new_attrs0=val0 #replacement dict has the values as tuples of new content and new attrs
      
      #if new_content0==None and new_attrs0=={}: continue
      if key0.startswith("#"): #we follow jquery selectors, # indicates selection by ID, while . indicates selection by class name
        temp_id0=key0[1:]
        if temp_id0 in except_ids: continue
        if id_suffix!=None: new_attrs0["id"]="%s_%s"%(temp_id0,id_suffix) #if we want to make unique ids by adding a suffix to it
        repl_pairs.extend(self.apply_content_by_id(key0[1:],new_content0,new_attrs0))
      elif key0.startswith("."):
        repl_pairs.extend(self.apply_content_by_class(key0[1:],new_content0,new_attrs0,except_ids=except_ids))
      elif key0=="title":
        found_title=re.findall('(?i)<title.+?/title>',self.content)
        new_title="<title>"+new_content0+"</title>" 
        if len(found_title)>0: repl_pairs.append((found_title[0],new_title))
      elif key0=="description":
        found_description=re.findall('(?i)<meta name="description".+?>',self.content)
        new_description='<meta name="description" content="%s">'%new_content0
        if len(found_description)>0: repl_pairs.append((found_description[0],new_description))

      #   old_title=re.findall('(?i)<title.+?/title>')
    return repl_pairs
  def replace(self,repl_dict0,except_ids=[],id_suffix=None):
    new_content=str(self.content)
    cur_repl_pairs=self.get_repl_pairs(repl_dict0,except_ids=except_ids,id_suffix=id_suffix)
    for a,b in cur_repl_pairs:
      # print(a,b)
      # print("---")
      new_content=new_content.replace(a,b)
    return new_content
  # def apply_class_except_id(self,class0,id0,el_content0):
  #   new_content=str(self.content)
  #   cur_repl_pairs=self.apply_content_by_class(class0,el_content0,{},except_id=id0)
  #   for a,b in cur_repl_pairs:
  #     new_content=new_content.replace(a,b)
  #   return new_content



  
#End class  
def create_open_tag(tag_name0,tag_attrs0={},self_closing=False):
  attr_items=[]
  for a,b in tag_attrs0.items():
    attr_items.append('%s="%s"'%(a,b))
  attr_str=" ".join(attr_items)
  if self_closing: final_open_tag='<%s %s/>'%(tag_name0,attr_str)
  else: final_open_tag='<%s %s>'%(tag_name0,attr_str)
  return final_open_tag

def read_page(url, timeout0=5): #return requests obj
  session = requests.Session()
  session.max_redirects = 3
  op=session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=timeout0, allow_redirects=True)
  #op.encoding = "utf-8" #op.apparent_encoding
  op.encoding = op.apparent_encoding
  return op
#   status_code=op.status_code
#   html_content=op.text
def get_page_content(url0):
  try:
    page_obj=read_page(url0)
    content0=page_obj.text
    content0=general.unescape(content0)  
  except: content0=""
  #content0=unescape(content0)  
  return content0

#14 Dec 23
def get_page_dom_text(url0):
  html_content0=get_page_content(url0)
  try: dom0=DOM(html_content0)
  except: return ""
  return dom0.text

      
# class web_page_OLD:
#   def __init__(self,url):
#     self.url=url
#     try: self.tld=urlsplit(url).netloc #not sure if it is TLD 
#     except: self.tld=""
#     self.all_text_items=[self.url,"_br_"] #add the page url and a line break at the beginning of the text items

#     self.html_content=""
#     self.title=""
#     self.text=""
#     self.status_code=None
#     self.segs=[]
#     self.clean_text=""
#     self.all_links,self.internal_links,self.externl_links=[],[],[]
#     self.meta_content=[]
#     try:
#       op=requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
#       self.status_code=op.status_code
#       self.html_content=op.text
#       self.html_content=self.html_content.replace("</p>","_br_</p>") #to put a line break at the end of paragraph elements
#       self.html_content=self.html_content.replace("<p>","_br_<p>")
#       self.html_content=self.html_content.replace("</li>","</li>_br_")
      
#       self.html_content=re.sub('(</h\d>)',r'_br_\1',self.html_content) #to add line break at headings
#       self.html_content=re.sub('(<h\d\b.*?>)',r'_br_\1',self.html_content)
#       self.html_content=re.sub('(<p\b.*?>)',r'_br_\1',self.html_content) #and at paragraphs
#       self.html_content=re.sub('(<li\b.*?>)',r'_br_\1',self.html_content) #and at lists
#       self.html_content=self.html_content.replace("<br>","_br_")
#       soup=BeautifulSoup(self.html_content)
#       if soup==None: return
#     except:
#       return

#     if soup.title: self.title=soup.title.string #Find the title
#     self.all_text_items.append(self.title)
#     self.all_text_items.append("_br_")


#     for script in soup(["script", "style"]):
#         script.decompose()
#     self.strips = list(soup.stripped_strings)
    
#     self.all_text_items.extend(self.strips) #add text strips from page HTML
#     self.all_text_items.append("_br_")

#     meta_content_found=re.findall('content="(.+?)"', self.html_content)
#     self.meta_content=[]
#     for mc in meta_content_found:
#       if "=" in mc: continue
#       self.meta_content.append(mc)
#       self.all_text_items.append(mc)
#       self.all_text_items.append("_br_")

#     #self.all_text_items=[self.url,"_br_"]+self.all_text_items
#     #self.all_text_items.append("_br_")

#     self.text=" ".join([v for v in self.all_text_items if v])
#     #self.text=self.text.replace("_br_","\n")
#     self.clean_text=re.sub("[\r\n\r\s]+"," ",self.text).strip() #clean breaks and tabs
#     self.clean_text=self.clean_text.replace("_br_","\n")
#     self.segs=[v.strip() for v in self.clean_text.split("\n") if v.strip()]
#     self.clean_text="\n".join(self.segs)
#     self.links_text=[] #links with their text
#     links_found=[]
#     for link in soup.findAll('a'):
#       link_str=link.string
#       if link_str: link_str=link_str.strip()
#       cur_href=link.get('href')
#       if cur_href!=None: 
#         links_found.append(cur_href)
#         if link_str: self.links_text.append((cur_href,link_str))
#     links_found=list(set(links_found))
#     self.all_links=[]
#     self.internal_links=[]
#     self.external_links=[]
#     for li in links_found:
#       if li.endswith(".js"): continue
#       if li.endswith(".css"): continue
#       if li.endswith(".png"): continue
#       if li.endswith(".pdf"): continue
#       if li.startswith("http"): cur_link=li
#       else: 
#         cur_link=urljoin(self.url,li)
#       self.all_links.append(cur_link)
#       if self.tld in cur_link: self.internal_links.append(cur_link)
#       else: self.external_links.append(cur_link)

def html_file2sents(html_fpath):
  fopen=open(html_fpath)
  content0=fopen.read()
  fopen.close()
  return html2sents(content0)

def split_tika_fn(txt): #split tika footnotes for alignment
  txt=re.sub(r'(\.\[footnoteRef.+?\])',r'\1\n',txt)
  txt=re.sub(r'(\s+\[\d+\:)',r'\n\1',txt)
  tmp_items=[v.strip("\xa0' ") for v in txt.split("\n") if v]
  # final_items=[]
  # for v in tmp_items:
  #   if v=="]" and len(final_items)>0: final_items[-1]=final_items[-1]+stripped_v
  #   else: final_items.append(v)
  #tmp_items=[v.strip("\xa0' ") for v in txt.split("\n") if v]
  return tmp_items

def html2sents(html_content,apply_tika=True):
  all_sents=[]
  dom_obj0=DOM(html_content)
  dom_text_items=dom_obj0.text_items
  for a in dom_text_items:
    para0=general.unescape(a)
    para_items=para0.split("\t")
    #all_sents.extend(para_items)
    for p0 in para_items:
      if apply_tika:
        tika_segs=split_tika_fn(p0)
        for ts in tika_segs:
          cur_sents=general.ssplit(ts)
          all_sents.extend(cur_sents)
      else:
        cur_sents=general.ssplit(p0)
        all_sents.extend(cur_sents)
  final_sents=[]
  for a in all_sents:
    if a.strip() in "}]" and len(final_sents)>0:  final_sents[-1]=final_sents[-1]+a
    else: final_sents.append(a)

  return final_sents


def html_with_tags2sents(html_content,apply_tika=True):
  dom_obj=DOM(html_content)
  text_items_tags=dom_obj.text_items_tags
  final_text=""
  for tag0,txt0 in text_items_tags:
    cur_tag_str,cur_txt_str=tag0,general.unescape(txt0)
    if tag0.startswith("</"):cur_tag_str="" 
    else: cur_tag_str= tag0+"\n"
    if txt0=="<br>": cur_txt_str="\n"
    final_text+=cur_tag_str+cur_txt_str
  items=[v for v in final_text.split("\n") if v]
  final_items=[]
  for it_i,it0 in enumerate(items):
    next_it=""
    if it_i+1<len(items):next_it=items[it_i+1]
    if it0.startswith("<") and it0.endswith(">"): 
      if next_it.endswith(">") and next_it.startswith("<"): continue
      else: final_items.append(it0)
    else: 
      if apply_tika:
        tika_segs=split_tika_fn(it0)
        for ts in tika_segs:
          cur_sents=general.ssplit(ts)
          final_items.extend(cur_sents)
      else:
        final_items.extend(general.ssplit(it0))
    #print('----')
  final_sents=[]
  for a in final_items:
    if a.strip() in "}]." and len(final_sents)>0:  final_sents[-1]=final_sents[-1]+a
    else: final_sents.append(a)
  return final_sents

# page_obj=web_page(url)
# #print(page_obj.title)
# #print(page_obj.meta_content)
# links=page_obj.all_links
# text=page_obj.clean_text

def get_bare_url(full_url): #the the top level domain of the url, stripping http, https, www, slash and colons
  bare_url=full_url.replace("http://","").replace("https://","")
  if bare_url.startswith("www."): bare_url=bare_url.replace("www.","")
  if bare_url.startswith("www1."): bare_url=bare_url.replace("www1.","")
  if bare_url.startswith("www2."): bare_url=bare_url.replace("www2.","")  
  bare_url=bare_url.strip("/")
  bare_url=bare_url.split("/")[0]
  bare_url=bare_url.split(":")[0]
  return bare_url

tlds_list=["co","ac","edu","com","org","gov","govt","net","info","sci"]
exclude_prefix=["mail"]
def get_url_id(full_url): #domain with suffix/tld
  bare_url=get_bare_url(full_url)
  bare_url_split=bare_url.split(".")
  if bare_url_split[0] in exclude_prefix: bare_url_split=bare_url_split[1:]
  if len(bare_url_split[-1])==2 and bare_url_split[-2] in tlds_list: output=".".join(bare_url_split[-3:])
  elif len(bare_url_split[-1])==2 and len(bare_url_split[-2])<=3: output=".".join(bare_url_split[-3:])
  else: output=".".join(bare_url_split[-2:])	
  return output

def reverse_url(full_url): #make site.abc.gov.au > au.gov.abc.site to sort by the last part of the url
  # bare_url=full_url.replace("http://","").replace("https://","")
  # if bare_url.startswith("www."): bare_url=bare_url.replace("www.","")
  # if bare_url.startswith("www1."): bare_url=bare_url.replace("www1.","")
  # if bare_url.startswith("www2."): bare_url=bare_url.replace("www2.","")  
  bare_url=get_bare_url(full_url)
  url_split=bare_url.split("/")
  first_part=url_split[0]
  second_part="/".join(url_split[1:])
  first_part=".".join(reversed(first_part.split(".")))
  if second_part: r_url=first_part+"/"+second_part #return first_part+"/"+second_part
  else: r_url=first_part #return first_part
  return r_url.strip("/")

def join_url(root0,rel0): #e.g. root: http://www.adsdf.dad, rel: image1.jpg
  # root0=root0.strip("/")
  # root_split0=root0.split("/")[:-1]
  # root0="/".join()
  # full0=root0.strip("/")+"/"+rel0.strip("/")
  full0=urllib.parse.urljoin(root0,rel0.strip("/"))
  return full0


#20 January 2026
def get_main_url(url): #get the main part of the url (tld/domain/http)
  http_split=url.split("//")
  if len(http_split)<2: return url #if no http is included 
  http_part,without_http=http_split[:2]
  main_part=without_http.split("/")[0]
  final_main_url="//".join([http_part,main_part])
  return final_main_url


#21 June 2024
#curl-based function for reading urls, with subprocess timeout
#while capturing response information after the page content
from subprocess import STDOUT, check_output

def curl(url,curl_path="curl",timeout=10, params={}):
  allow_insecure=params.get("allow_insecure",False) 
  #cmd='%s -A -k "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0" --max-time 60 -s --max-redirs 10 -w "\n%%{json}" %s -L'%(curl_path,url)
  # if allow_insecure: cmd='%s --compressed -k -L -A "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0" --max-time 60 -s --max-redirs 10 -w "\n%%{json}" "%s" -L'%(curl_path,url)
  # else: cmd='%s --compressed -L -A "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0" --max-time 60 -s --max-redirs 10 -w "\n%%{json}" "%s" -L'%(curl_path,url)

  if allow_insecure: cmd='%s --compressed -k -L -A "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0" --max-time %s -s --max-redirs 10 -w "\n%%{json}" "%s" -L'%(curl_path,timeout,url)
  else: cmd='%s --compressed -L -A "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0" --max-time %s -s --max-redirs 10 -w "\n%%{json}" "%s" -L'%(curl_path,timeout,url)


  try: 
    output = check_output(cmd, shell=True, stderr=STDOUT, timeout=timeout)
    output=output.decode("utf-8", errors='ignore')
    output_split=output.split("\n")
    final_json0=output_split[-1]
    content="\n".join(output_split[:-1])
    meta_redirects=re.findall('<meta[^>]*?url=(.*?)["\']',content , re.IGNORECASE)
    final_url=url
    #handle meta refresh redirects
    try:
      json_dict=json.loads(final_json0)
      final_url_check=json_dict.get("url_effective","")
      if final_url_check!="": final_url=final_url_check
    except: pass
    if len(meta_redirects)>0: 
      meta_new_url=urljoin(final_url,meta_redirects[0])
      return curl(meta_new_url,curl_path=curl_path,timeout=timeout)


  except Exception as ex:
    print(ex) 
    return "", "{}"
  return content, final_json0

def get_page_info(url, read_method="curl",curl_path="curl",timeout=30,params={}):
  page_info_dict={}
  page_info_dict["url"]=url

  if read_method=="curl":
    params_timeout=params.get("timeout")
    if params_timeout!=None: timeout=params_timeout

    page_content,response_json=curl(url,curl_path=curl_path,timeout=timeout,params=params)
    page_content=general.unescape(page_content)
    #response_dict=json.loads(response_json)
    try: response_dict=json.loads(response_json)
    except: response_dict={}
    final_url=response_dict.get("url_effective",url)
    status_code=response_dict.get("response_code")
    page_info_dict["response_json"]=response_json
  else:
    try: page_obj=read_page(url)
    except: return page_info_dict
    page_content=general.unescape(page_obj.text)
    final_url=page_obj.url
    status_code=page_obj.status_code

  page_info_dict["status_code"]=status_code
  final_url=final_url.strip("/")

  page_content=remove_html_noise(page_content)



  #page_content=get_page_content(url)
  page_content=page_content.replace("\r","\n").replace("\t","\n")
  #page_content=page_content.replace("\r\n","|")#.replace("\r","|")
  t0=time.time()
  try: page_dom_obj=DOM(page_content)
  except: return page_info_dict
  t1=time.time()
  dom_elapsed=round(t1-t0)
  #print("dom_elapsed",dom_elapsed)

  t0=time.time()
  lang0=""

  title0=page_dom_obj.title.strip()
  #description0=page_dom_obj.description.strip()
  description0=get_desc(page_content)

  keywords0=page_dom_obj.keywords.strip()
  lang0=page_dom_obj.lang
  meta_lang0=page_dom_obj.meta_lang

  phone_numbers=[]
  logos=[]
  text_items=[]
  links=[]
  emails=[]
  addresses=[]
  social_links=[]
  external_links=[]

  #processing links
  raw_links=page_dom_obj.all_links
  for link0 in raw_links:
    anchor0=general.remove_tags(link0.inner_html)
    href0=link0.href.strip("/")
    if href0.startswith("#"): continue
    if href0.lower().startswith("javascript"): continue
    if href0=="": continue
    if href0.startswith("tel:"):
      phone_numbers.append(href0.replace("tel:",""))
      continue
    if href0.startswith("mailto:"):
      emails.append(href0.replace("mailto:",""))
      continue

    if href0.split(".")[-1].lower() in ["pdf","png","jpg","jpeg"]: continue
    if href0.split(".")[-1].isdigit(): continue
    if not href0.lower().startswith("http"): href0=join_url(final_url,href0) #url0.strip("/")+"/"+href0.strip("/")
    anchor0=re.sub(r"\s+"," ",anchor0).strip()
    is_social_link=False
    if "facebook" in href0 or "twitter" in href0 or "linkedin" in href0 or "youtube" in href0 or "x.com" in href0: 
      social_links.append(href0.lower())
      is_social_link=True
    #print(href0,anchor0)
    links.append((href0,anchor0))
    if not href0.startswith(final_url) and not is_social_link: external_links.append(href0)


    #full_link_url=final_url


  links=list(set(links)) 
  social_links=list(set(social_links))

  #processing images/get logos
  raw_images=page_dom_obj.all_images
  for img0 in raw_images:
    if "logo" in img0.attrs.get("alt","").lower() or "logo" in img0.src.lower(): 
      src0=img0.src
      if src0.startswith("//"):src0="http://"+src0
      elif not src0.startswith("http"): src0=join_url(final_url,src0)
      logos.append(src0)
      #print(src0)

  #processing text items
  raw_items0=page_dom_obj.text_items
  #final_items=[]
  for it0 in raw_items0:
    it0=general.remove_tags(it0)
    text_items.extend(it0.split("\n"))
  text_items=[v.strip() for v in text_items if v.strip()]

  # html_attrs={}
  # html_tag=page_dom_obj.tag_dict.get("html_0")
  # if html_tag!=None: html_attrs=html_tag.attrs
  # lang0=html_attrs.get("lang","")


  #processing addresses
  for key0,val0 in page_dom_obj.tag_dict.items():
    class0=val0.attrs.get("class","")
    if key0.startswith("address_"): addresses.append(general.remove_tags(val0.inner_html," "))
    if "address" in class0.lower(): addresses.append(general.remove_tags(val0.inner_html," "))

  #processing emails
  cur_emails=re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', page_content)
  for email0 in cur_emails:
    if email0.split(".")[-1].lower() in ["pdf","png","jpg","jpeg"]: continue
    if email0.split(".")[-1].isdigit(): continue
    emails.append(email0.strip("."))
  emails=list(set([v.lower() for v in emails]))
  t1=time.time()
  elapsed=round(t1-t0,2)

  #print("elapsed",elapsed)
  if lang0=="" and meta_lang0!="": lang0=meta_lang0
  
  page_info_dict["final_url"]=final_url
  page_info_dict["lang"]=lang0
  #page_info_dict["meta_lang"]=meta_lang0
  page_info_dict["title"]=title0
  page_info_dict["description"]=description0
  page_info_dict["keywords"]=keywords0
  page_info_dict["phone_numbers"]=phone_numbers
  page_info_dict["links"]=links
  page_info_dict["social_links"]=social_links
  page_info_dict["emails"]=emails
  page_info_dict["addresses"]=addresses
  page_info_dict["logos"]=logos
  #page_info_dict["text_items"]=text_items
  page_info_dict["text"]=page_dom_obj.text
  page_info_dict["external_links"]=external_links
  page_info_dict["page_content"]=page_content
  
  
  
  return page_info_dict  

def get_title(html_content):
  title0=""
  title_found=re.findall('(?i)<title>(.+?)</title>',html_content)
  if title_found: title0=title_found[0]
  return title0

#15 Jan 2024
def get_desc(html_content):
  desc_out=""
  desc_property_list=["description", "og:description"]
  meta_tags=re.findall('(?i)<meta.+?>',html_content)
  for meta0 in meta_tags: 
    meta_attrs=get_attrs(meta0)
    attr_name=meta_attrs.get("name","") #og:description
    attr_property=meta_attrs.get("property","") #og:description
    
    if attr_name.lower() in desc_property_list or attr_property.lower() in desc_property_list: 
      attr_desc_out=meta_attrs.get("content","")
      if attr_desc_out!="": desc_out=attr_desc_out
    #print(meta_attrs)
  return desc_out
# def get_desc(html_content):
#   desc0=""
#   desc_tag_found=re.findall('(?i)<meta name="description" .+>',html_content)
#   if desc_tag_found:
#     desc_tag0=desc_tag_found[0]
#     desc_found=re.findall('(?i)content="(.+?)"',desc_tag0)
#     if desc_found: desc0=desc_found[0]
#   return desc0  

def get_emails(html_content,max_name_len=50):
  all_emails=[]
  found_em_domain=re.finditer(r'\@[\w\-\.]+',str(html_content))
  for a in found_em_domain:
    cur_domain=a.group(0).strip(".")
    cur_domain_split=cur_domain.split(".")
    if len(cur_domain_split)<2: continue
    cur_domain_last=cur_domain_split[-1]
    if cur_domain_last.isdigit(): continue
    if cur_domain_last.lower() in ["pdf","png","jpg","jpeg"]: continue

    x0=a.start()
    prev0=html_content[x0-max_name_len:x0]
    if len(prev0)>0 and prev0[-1] in "\n\t\r "+string.punctuation: continue
    check=re.findall(r"[\w\.]+$",prev0)
    if check:
      cur_email=check[0]+cur_domain
      all_emails.append(cur_email)
  return list(set(all_emails))

# def get_emails(html_content):
#   emails=re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', str(html_content))
#   emails=list(set(emails))
#   valid_emails=[]
#   for em0 in emails:
#     em_dom=em0.split("@")[-1]
#     check=re.findall("[a-zA-Z]",em_dom)
#     if not check: continue
#     if em0.split(".")[-1].lower() in ["pdf","png","jpg","jpeg"]: continue
#     if em0.split(".")[-1].isdigit(): continue
#     valid_emails.append(em0.strip(".-"))
#   return list(set(valid_emails))

def get_page_lang(html_content):
  html_tags=re.findall('(?i)<html.+?>',html_content)
  if len(html_tags)==0: return ""
  html_tag_attrs=get_attrs(html_tags[0])
  lang_attr=html_tag_attrs.get("lang")
  if lang_attr!=None: return lang_attr
  lang_xml_attr=html_tag_attrs.get("xml:lang")
  if lang_xml_attr!=None: return lang_xml_attr #if tag_name=="meta" and cur_el.attrs.get("http-equiv","")=="content-language":self.meta_lang=cur_el.attrs.get("content","")
  return ""




def get_page_summary(url):
  page_info_dict={}
  #page_obj=read_page(url)
  try: page_obj=read_page(url)
  except: return page_info_dict
  page_content=general.unescape(page_obj.text)
  page_content=page_content.replace("\n"," ")
  final_url=page_obj.url
  page_info_dict["url"]=final_url
  page_info_dict["title"]=get_title(page_content)
  page_info_dict["desc"]=get_desc(page_content)
  page_info_dict["emails"]=get_emails(page_content)
  page_info_dict["lang"]=get_page_lang(page_content)
  return page_info_dict

#1 June 2024
def remove_html_noise(html_content): #remove script/style/comments
  text=html_content
  # (REMOVE <SCRIPT> to </script> and variations)
  pattern = r'<[ ]*script.*?\/[ ]*script[ ]*>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

  # (REMOVE HTML <STYLE> to </style> and variations)
  pattern = r'<[ ]*style.*?\/[ ]*style[ ]*>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
  

  # (REMOVE HTML <SVG> to </SVG> and variations)
  pattern = r'<[ ]*svg.*?\/[ ]*svg[ ]*>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

  # (REMOVE HTML <SOURCE> to </SOURCE> and variations)
  pattern = r'<[ ]*source.*?\/[ ]*source[ ]*>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))


  #remove link and variations
  #pattern = re.compile(r'<link\b[^>]*>.*?</link\b[^>]*>|<link\b[^>]*/>', re.DOTALL | re.IGNORECASE)
  # pattern= r'<link\b[^>]*>.*?</link\b[^>]*>|<link\b[^>]*/>'
  # #text = pattern.sub('', text)
  # text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))


  # (REMOVE HTML COMMENTS <!-- to --> and variations)
  pattern = r'<[ ]*!--.*?--[ ]*>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

  # (REMOVE HTML DOCTYPE <!DOCTYPE html to > and variations)
  pattern = r'<[ ]*\![ ]*DOCTYPE.*?>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
  #tags=list(re.findall('<[^<>]*?>|\<\!\-\-.+?\-\-\>', text))
  return text


def get_page_paras(page_url):
  try:text=get_page_content(page_url)
  except: return []
  # (REMOVE <SCRIPT> to </script> and variations)
  pattern = r'<[ ]*script.*?\/[ ]*script[ ]*>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

  # (REMOVE HTML <STYLE> to </style> and variations)
  pattern = r'<[ ]*style.*?\/[ ]*style[ ]*>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

  # (REMOVE HTML <META> to </meta> and variations)
  pattern = r'<[ ]*meta.*?>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

  # (REMOVE HTML COMMENTS <!-- to --> and variations)
  pattern = r'<[ ]*!--.*?--[ ]*>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

  # (REMOVE HTML DOCTYPE <!DOCTYPE html to > and variations)
  pattern = r'<[ ]*\![ ]*DOCTYPE.*?>'  # mach any char zero or more times
  text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
  tags=list(re.findall(r'<[^<>]*?>|\<\!\-\-.+?\-\-\>', text))
  for tag0 in list(set(tags)): text=text.replace(tag0,tag0.lower()) #make sure al tag names are in lower case

  text=text.replace('<br />',"_br_")
  text=text.replace('<br/>',"_br_")
  text=text.replace("</p>","_br_</p>") #to put a line break at the end of paragraph elements
  text=text.replace("<p>","_br_<p>")
  text=text.replace("</title>","</title>_br_")
  text=text.replace("</li>","</li>_br_")
  text=text.replace("</div>","</div>_br_")
  text=text.replace("</label>","</label>_br_")
  text=text.replace("</button>","</button>_br_")
  
  text=re.sub(r'(</h\d>)',r'_br_\1',text) #to add line break at headings
  text=re.sub(r'(<h\d\b.*?>)',r'_br_\1',text)
  text=re.sub('(<p\b.*?>)',r'_br_\1',text) #and at paragraphs
  text=re.sub('(<li\b.*?>)',r'_br_\1',text) #and at lists
  text=text.replace("<br>","_br_")
  text=re.sub('<[^<>]*?>',' ',text)
  text=re.sub('[\n\r\t]+',"_br_",text)
  text=re.sub(r'\s+'," ",text)
  
  paras=[v.strip() for v in text.split("_br_") if v.strip() and not (v[0]=='<' and v[-1]=='>') ]
  return paras


def get_qs_dict(qs_str,lower=False):
  qs_str = unquote(qs_str)
  qs_dict0={}
  for item0 in qs_str.split("&"):
    eq_split=item0.split("=")
    if len(eq_split)!=2: continue
    key,val=eq_split
    if lower: key=key.lower()
    qs_dict0[key]=val
  return qs_dict0

def encode_qs(qs_dict):
  qs_items=[]
  for a,b in qs_dict.items():
    cur_item=f'{a}={b}'
    qs_items.append(cur_item)
  return "&".join(qs_items)



#21 January 2026
#to get a list of valid elements with their IDs and element/tag objects
def get_el_text_obj_list(dom_obj, params={}):
  max_el_text_size=params.get("max_el_text_size",500)
  final_id_text_obj_list=[]
  for tag_id0,tag_obj0 in dom_obj.tag_dict.items():
    if tag_id0.startswith("text_node"): continue
    inner0=tag_obj0.inner_html
    outer0=tag_obj0.outer_html
    open_tag0=tag_obj0.open_tag
    if open_tag0.lower() in ["html","body"]: continue
    inner0=re.sub(r"\s+"," ",inner0)
    #inner_text=general.remove_html(inner0).strip()
    inner_text=general.remove_tags(inner0,repl_with=" ").strip()
    if inner_text=="" or len(inner_text)>max_el_text_size: continue #remove elements with empty text or very big elements (which are probably parent elements) 
    tag_name0=tag_obj0.tag_name
    counted_recursive_tags=inner0.count(f"<{tag_name0} ")
    if counted_recursive_tags>0: continue #exclude recursive elements <span><span> or <div><div>
    cur_i0=tag_obj0.open_tag_i0
    cur_i1=cur_i0+len(tag_obj0.outer_html)
    final_id_text_obj_list.append((tag_id0,inner_text,tag_obj0,(cur_i0,cur_i1)))
  
  final_id_text_obj_list.sort(key=lambda x:x[-1]) #sort all items by their position from the beginning of the page
  temp_final=[]
  last_i=0
  for item0 in final_id_text_obj_list:
    span_i0,span_i1=item_span=item0[-1]
    valid=True
    if span_i0<last_i: continue #do not include overlapping/nested elements
    temp_final.append(item0)
    last_i=span_i1
    #print(valid,item0)
  final_id_text_obj_list=temp_final
  return final_id_text_obj_list

