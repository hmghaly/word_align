#a librry for all the utilities we need for scraping data from the web
import requests, re
from urllib.parse import urljoin, urlsplit
#from bs4 import BeautifulSoup
#from lxml.html import parse

#This library is for accessing web pages, reading and processing their content
#and also for templating web pages by DOM manipulation

def get_attrs(tag0):
  found_attrs=re.findall('(\S+)="(.+?)"',tag0)
  return dict(iter(found_attrs))

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
  def __init__(self,content) -> None:
    self.content=content
    self.tag_dict={} #linking assigned IDs with element objects
    self.id_dict={} #mapping actual IDs with assigned IDs
    self.actual_ids=[] #a list of IDs actually used, can help us spot duplicate IDs
    self.class_id_dict={} #map each class name to the assigned ids of elements with that class
    self.text_items=[]
    self.tag_id_list=[] #list of assigned IDs
    self.all_links=[]
    self.all_images=[]
    self.description=""
    self.title=""
    tags=list(re.finditer('<([^<>]*?)>', self.content))
    open_tags=[""]
    tag_counter_dict={}
    start_i=0
    for ti_, t in enumerate(tags):
      tag_str,tag_start,tag_end=t.group(0), t.start(), t.end()
      inter_text=self.content[start_i:tag_start] #intervening text since last tag
      last_open_tag=open_tags[-1]
      if len(inter_text)>0:
        if not last_open_tag.lower().split("_")[0] in ["script","style","noscript"]: 
          inter_text_stripped=inter_text.strip('\r\n\t ').replace("&times;","")
          if inter_text_stripped!="": self.text_items.append(inter_text)
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
      tag_str_lower=tag_str.lower()
      tag_name=re.findall(r'</?(.+?)[\s>]',tag_str_lower)[0]
      if tag_name.startswith("h") or tag_name in ["p","div","br","li"]: self.text_items.append("<br>")
      tag_count=tag_counter_dict.get(tag_name,0)
      assigned_tag_id="%s_%s"%(tag_name,tag_count)
      tag_counter_dict[tag_name]=tag_count+1
      cur_el=element()
      cur_el.assigned_id=assigned_tag_id
      tag_type=""
      if tag_str.startswith('</'): tag_type="closing"
      elif tag_str.startswith('<!'): tag_type="comment"
      elif tag_str_lower.endswith('/>') or tag_name in ["input","link","meta","img","br"]: tag_type="s" #standalone
      else: tag_type="opening"
      if tag_type=="closing" and len(open_tags)>0: #if it is a closing tag,
        if tag_name==open_tags[-1].split("_")[0]: #we check if the tag name matches the last open tag name
          el_to_close=self.tag_dict[open_tags[-1]] #and then identify the element corresponding to the last open tag
          tmp_open_i0,tmp_open_i1=el_to_close.open_tag_i0,el_to_close.open_tag_i1 #retrieve the start and end indexes/locations from the open tag
          tmp_inner_html=self.content[tmp_open_i1:tag_start] #then get inner html
          tmp_outer_html=self.content[tmp_open_i0:tag_end] #then outer html
          el_to_close.inner_html=tmp_inner_html #and assign these to the retrieved element object
          el_to_close.outer_html=tmp_outer_html
          if tag_name=="title": self.title=tmp_inner_html
          if tag_name=="a": self.all_links.append(el_to_close)
          
            
          open_tags=open_tags[:-1]
        else: print("open_tags",open_tags, "tag_name",tag_name)
      else:
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

        if tag_name=="meta" and cur_el.attrs.get("name","")=="description":self.description=cur_el.attrs.get("content","")
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
        self.tag_dict[assigned_tag_id]=cur_el
        for cls0 in cur_class_list:
          self.class_id_dict[cls0]=self.class_id_dict.get(cls0,[])+[assigned_tag_id]
    self.text_items="".join(self.text_items).split("<br>")
    self.text_items=[v for v in self.text_items if v]

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
    repl_list=[]
    cur_el=self.get_el_by_id(id0)
    if cur_el==None: return repl_list
    new_open_tag=cur_el.open_tag
    if new_attrs_dict0!={}:
      cur_attrs=cur_el.attrs
      for a0,b0 in new_attrs_dict0.items():
        cur_attrs[a0]=b0
      new_open_tag=create_open_tag(cur_el.tag_name,cur_attrs)
    cur_outer_html=cur_el.outer_html
    if el_content0: new_outer_html=new_open_tag+el_content0+cur_el.close_tag
    else: new_outer_html=new_open_tag+cur_el.inner_html+cur_el.close_tag
    # print("cur_outer_html",cur_outer_html)
    # print("new_outer_html",new_outer_html)
    repl_list.append((cur_outer_html,new_outer_html))
    return repl_list
  def apply_content_by_class(self,class0,el_content0,new_attrs_dict0={}):
    repl_list=[]
    cur_el_list=self.get_el_by_class(class0)
    for cur_el in cur_el_list:
      new_open_tag=cur_el.open_tag
      if new_attrs_dict0!={}:
        cur_attrs=cur_el.attrs
        for a0,b0 in new_attrs_dict0.items():
          cur_attrs[a0]=b0
        new_open_tag=create_open_tag(cur_el.tag_name,cur_attrs)      
      cur_outer_html=cur_el.outer_html
      if el_content0: new_outer_html=new_open_tag+el_content0+cur_el.close_tag
      else: new_outer_html=new_open_tag+cur_el.inner_html+cur_el.close_tag      
      repl_list.append((cur_outer_html,new_outer_html))
    return repl_list
  def get_repl_pairs(self,cur_repl_dict0):
    repl_pairs=[]
    for key0,val0 in cur_repl_dict0.items():
      new_content0,new_attrs0=val0 #replacement dict has the values as tuples of new content and new attrs
      if key0.startswith("#"): #we follow jquery selectors, # indicates selection by ID, while . indicates selection by class name
        repl_pairs.extend(self.apply_content_by_id(key0[1:],new_content0,new_attrs0))
      elif key0.startswith("."):
        repl_pairs.extend(self.apply_content_by_class(key0[1:],new_content0,new_attrs0))
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
  def replace(self,repl_dict0):
    new_content=str(self.content)
    cur_repl_pairs=self.get_repl_pairs(repl_dict0)
    for a,b in cur_repl_pairs:
      new_content=new_content.replace(a,b)
    return new_content


  
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
  op=requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=timeout0)
  return op
#   status_code=op.status_code
#   html_content=op.text
      
class web_page_OLD:
  def __init__(self,url):
    self.url=url
    try: self.tld=urlsplit(url).netloc #not sure if it is TLD 
    except: self.tld=""
    self.all_text_items=[self.url,"_br_"] #add the page url and a line break at the beginning of the text items

    self.html_content=""
    self.title=""
    self.text=""
    self.status_code=None
    self.segs=[]
    self.clean_text=""
    self.all_links,self.internal_links,self.externl_links=[],[],[]
    self.meta_content=[]
    try:
      op=requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
      self.status_code=op.status_code
      self.html_content=op.text
      self.html_content=self.html_content.replace("</p>","_br_</p>") #to put a line break at the end of paragraph elements
      self.html_content=self.html_content.replace("<p>","_br_<p>")
      self.html_content=self.html_content.replace("</li>","</li>_br_")
      
      self.html_content=re.sub('(</h\d>)',r'_br_\1',self.html_content) #to add line break at headings
      self.html_content=re.sub('(<h\d\b.*?>)',r'_br_\1',self.html_content)
      self.html_content=re.sub('(<p\b.*?>)',r'_br_\1',self.html_content) #and at paragraphs
      self.html_content=re.sub('(<li\b.*?>)',r'_br_\1',self.html_content) #and at lists
      self.html_content=self.html_content.replace("<br>","_br_")
      soup=BeautifulSoup(self.html_content)
      if soup==None: return
    except:
      return

    if soup.title: self.title=soup.title.string #Find the title
    self.all_text_items.append(self.title)
    self.all_text_items.append("_br_")


    for script in soup(["script", "style"]):
        script.decompose()
    self.strips = list(soup.stripped_strings)
    
    self.all_text_items.extend(self.strips) #add text strips from page HTML
    self.all_text_items.append("_br_")

    meta_content_found=re.findall('content="(.+?)"', self.html_content)
    self.meta_content=[]
    for mc in meta_content_found:
      if "=" in mc: continue
      self.meta_content.append(mc)
      self.all_text_items.append(mc)
      self.all_text_items.append("_br_")

    #self.all_text_items=[self.url,"_br_"]+self.all_text_items
    #self.all_text_items.append("_br_")

    self.text=" ".join([v for v in self.all_text_items if v])
    #self.text=self.text.replace("_br_","\n")
    self.clean_text=re.sub("[\r\n\r\s]+"," ",self.text).strip() #clean breaks and tabs
    self.clean_text=self.clean_text.replace("_br_","\n")
    self.segs=[v.strip() for v in self.clean_text.split("\n") if v.strip()]
    self.clean_text="\n".join(self.segs)
    self.links_text=[] #links with their text
    links_found=[]
    for link in soup.findAll('a'):
      link_str=link.string
      if link_str: link_str=link_str.strip()
      cur_href=link.get('href')
      if cur_href!=None: 
        links_found.append(cur_href)
        if link_str: self.links_text.append((cur_href,link_str))
    links_found=list(set(links_found))
    self.all_links=[]
    self.internal_links=[]
    self.external_links=[]
    for li in links_found:
      if li.endswith(".js"): continue
      if li.endswith(".css"): continue
      if li.endswith(".png"): continue
      if li.endswith(".pdf"): continue
      if li.startswith("http"): cur_link=li
      else: 
        cur_link=urljoin(self.url,li)
      self.all_links.append(cur_link)
      if self.tld in cur_link: self.internal_links.append(cur_link)
      else: self.external_links.append(cur_link)

# page_obj=web_page(url)
# #print(page_obj.title)
# #print(page_obj.meta_content)
# links=page_obj.all_links
# text=page_obj.clean_text
