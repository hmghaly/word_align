import time, json, shelve, os, re, sys, itertools
from itertools import groupby
from math import log
import random
import numpy as np

# try: import torch
# except: pass


#from general import * 
sys.path.append("code_utils")
import general
import arabic_lib


#30 Jan 2025
#match a list of pairs of src/trg items - apply to a pair of tokenized sentences
#if we need to match only src items, keep trg_inv_dict={}, and vice versa
def qa_match_2way(src_toks,trg_toks,src_inv_dict,trg_inv_dict,qa_type="matching"):
  all_match_items=[]
  src_found_pairs=[]
  trg_found_pairs=[]
  for et0 in list(set(src_toks)):
    if src_inv_dict=={}: break
    cur_forms0=[et0]
    if ord(et0[0])>1500: cur_forms0=general.get_multi_pre_candidates(et0) #to match Arabic words with different prefix forms
    for form0 in cur_forms0: #print(form0)
      check0=src_inv_dict.get(form0,[])
      for ch0 in check0: src_found_pairs.append(ch0)

  for at0 in list(set(trg_toks)):
    if trg_inv_dict=={}: break
    cur_forms0=[at0]
    if ord(at0[0])>1500: cur_forms0=general.get_multi_pre_candidates(at0)
    for form0 in cur_forms0: #print(form0)
      check0=trg_inv_dict.get(form0,[])
      for ch0 in check0: trg_found_pairs.append(ch0)
        
  src_found_pairs.sort()
  src_grouped_pairs0=[(key,[v[1] for v in list(group)]) for key,group in groupby(src_found_pairs,lambda x:x[0])]

  for src_phrase0,trg_phrase_list0 in src_grouped_pairs0:
    src_locs0=general.is_in(src_phrase0,src_toks)
    if not src_locs0: continue
    trg_locs=[]
    for trg_phrase0 in trg_phrase_list0:
      temp_loc0=general.is_in(trg_phrase0,trg_toks)
      trg_locs.extend(temp_loc0)
    cur_match_item={"src_locs":src_locs0,"trg_locs":trg_locs,"src_phrase": src_phrase0,"trg_phrase":[], "expected":trg_phrase_list0, "qa_type":qa_type}
    all_match_items.append(cur_match_item) #when matching src items, we keep trg_phrase []

  trg_found_pairs.sort()
  trg_grouped_pairs0=[(key,[v[1] for v in list(group)]) for key,group in groupby(trg_found_pairs,lambda x:x[0])]

  for trg_phrase0,src_phrase_list0 in trg_grouped_pairs0:
    trg_locs0=general.is_in(trg_phrase0,trg_toks)
    if not trg_locs0: continue
    src_locs=[]
    for src_phrase0 in src_phrase_list0:
      temp_loc0=general.is_in(src_phrase0,src_toks)
      src_locs.extend(temp_loc0)
    cur_match_item={"src_locs":src_locs,"trg_locs":trg_locs0,"src_phrase": [],"trg_phrase":trg_phrase0, "expected":src_phrase_list0, "qa_type":qa_type}
    all_match_items.append(cur_match_item) #when matching trg items, we keep src_phrase []
  used_loc_pairs=[]
  new_match_items=[]
  for am in all_match_items:
    locs_pair=(am["src_locs"],am["trg_locs"])
    if locs_pair in used_loc_pairs: continue
    used_loc_pairs.append(locs_pair)
    new_match_items.append(am)
  return new_match_items


#29 Jan 2025
def qa_list_inv(qa_2d_list,include_self=False): #invert a list of src/trg items to match them for QA 
  src_fwd,trg_fwd=[],[]  
  trg_list=[]
  for src_item_raw0,trg_item_raw0 in qa_2d_list:
    for src_item0 in src_item_raw0.strip().split("|"):
      src_item_toks0=general.tok(src_item0)
      trg_split0=trg_item_raw0.strip().split("|")
      if include_self: trg_split0.append(src_item0)
      for trg_item0 in trg_split0:
        trg_item_toks0=general.tok(trg_item0)
        if not trg_item_toks0 in trg_list:trg_list.append(trg_item_toks0)
        first_src0=src_item_toks0[0]
        first_trg0=trg_item_toks0[0]
        src_fwd.append((first_src0,src_item_toks0,trg_item_toks0))
        trg_fwd.append((first_trg0,trg_item_toks0,src_item_toks0))
  src_fwd.sort()
  src_grouped0=[(key,[v[1:] for v in list(group)]) for key,group in groupby(src_fwd,lambda x:x[0])]
  src_inv_dict=dict(iter(src_grouped0))

  trg_fwd.sort()
  trg_grouped0=[(key,[v[1:] for v in list(group)]) for key,group in groupby(trg_fwd,lambda x:x[0])]
  trg_inv_dict=dict(iter(trg_grouped0))
  return src_inv_dict,trg_inv_dict


#2 Feb 2025
#takes a list of paramaeter dicts, and applies each set of params to get matching items on src/trg pairs
def qa_get_matching_list_from_params(matching_params_list,src_toks,trg_toks):
  all_matches0=[]
  for param0 in matching_params_list:
    src_inv_dict0=param0.get("src_inv_dict",{})
    trg_inv_dict0=param0.get("trg_inv_dict",{})
    qa_type0=param0.get("qa_type","matching")
    qa_out0=qa_match_2way(src_toks,trg_toks,src_inv_dict0,trg_inv_dict0,qa_type=qa_type0)
    all_matches0.extend(qa_out0)
  return all_matches0


#generate qa string for src/trg with spans & classes based on matching items
def qa_matches2tags(all_matches,src_tokens,trg_tokens,prefix="sent0"):
  src_span_tag_open_dict,src_span_tag_close_dict={},{}
  trg_span_tag_open_dict,trg_span_tag_close_dict={},{}
  close_tag="</span>"
  
  all_matches.sort(key=lambda x:-len(x["src_phrase"])-len(x["trg_phrase"])) #need better sorting
  #match_item_counter=0
  for match_item_counter,a0 in enumerate(all_matches):
    match_item_name=f"{prefix}_item{match_item_counter}"
    expected_str=" | ".join([general.de_tok2str(v) for v in a0["expected"]]) 
    qa_type0=a0.get("qa_type","matching")
    src_locs0,trg_locs0=a0["src_locs"],a0["trg_locs"]
    match_type_class="qa_"+qa_type0
    cur_tag_classes=[match_type_class,match_item_name]

    if qa_type0=="matching":
      if len(trg_locs0)==len(src_locs0): cur_tag_classes.append("matched")
      else: cur_tag_classes.append("mismatch")
    cur_tag_classes_str=" ".join(cur_tag_classes)
    #match_item_counter+=1

    open_tag=f'<span title="{expected_str}" class="{cur_tag_classes_str}">'

    for sl_i0,sl_i1 in src_locs0: 
      src_span_tag_open_dict[sl_i0]=src_span_tag_open_dict.get(sl_i0,[])+[open_tag]
      src_span_tag_close_dict[sl_i1]=src_span_tag_close_dict.get(sl_i1,[])+[close_tag]
    for tl_i0,tl_i1 in trg_locs0: 
      trg_span_tag_open_dict[tl_i0]=trg_span_tag_open_dict.get(tl_i0,[])+[open_tag]
      trg_span_tag_close_dict[tl_i1]=trg_span_tag_close_dict.get(tl_i1,[])+[close_tag]
  qa_src_str=qa_detok_apply_tags(src_tokens,src_span_tag_open_dict,src_span_tag_close_dict)
  qa_trg_str=qa_detok_apply_tags(trg_tokens,trg_span_tag_open_dict,trg_span_tag_close_dict)
  return qa_src_str,qa_trg_str


#apply spans at open/close dict to tokenized items, generate detokenized text based on tokens, spaces and tags
def qa_detok_apply_tags(cur_tokens,cur_open_tag_dict,cur_close_tag_dict):
  out_detok_with_space=general.de_tok_space(cur_tokens)

  full_qa_str=""
  for i0,a in enumerate(out_detok_with_space): 
    word0,space0=a
    cur_open_tags=cur_open_tag_dict.get(i0,[])
    cur_close_tags=cur_close_tag_dict.get(i0,[])
    cur_chunk="".join(cur_open_tags)+word0+"".join(cur_close_tags)+space0
    full_qa_str+=cur_chunk
  return full_qa_str

#=================== QA functions ==============
#15 Jan 23
def gen_ul_style(color0="black"):
  underline_style='text-decoration: underline;-webkit-text-decoration-color: %s;text-decoration-color: %s;'%(color0,color0)
  return underline_style

def is_symbol(str0): #is a UN symbol, e.g. A/75/251
  outcome=False
  if str0[0].isupper() and str0[-1].isdigit() and str0.count("/")>0: outcome=True
  return outcome

def qa_match_exact(src_sent_toks,trg_sent_toks): #match numbers, UN-symbols and other items that have to be exact in src/trg
  uq_src0=list(set(src_sent_toks))
  uq_trg0=list(set(trg_sent_toks))
  match_score=1.0
  src_digits=[v for v in uq_src0 if v.isdigit()]
  src_symbols=[v for v in uq_src0 if is_symbol(v)] #we can also add websites, twitter handles, hashtags ... etc
  all_qa_matches=[]
  for dig0 in src_digits:
    match_type="exact-number"
    if len(dig0)<2: criticality="low" #if a single digit number, which is often translated as a word
    else: criticality="high"
    cur_src_spans=general.is_in([dig0],src_sent_toks)
    cur_trg_spans=general.is_in([dig0],trg_sent_toks)
    all_qa_matches.append((dig0,dig0,cur_src_spans,cur_trg_spans,match_type,match_score,criticality))
  for sym0 in src_symbols:
    match_type="exact-UN-symbol"
    criticality="high"
    cur_src_spans=general.is_in([sym0],src_sent_toks)
    cur_trg_spans=general.is_in([sym0],trg_sent_toks)
    all_qa_matches.append((sym0,sym0,cur_src_spans,cur_trg_spans,match_type,match_score,criticality))
  return all_qa_matches

def qa_match_normative(src_sent_toks,trg_sent_toks,normative_list):
  match_score=1.0
  all_norm_matches=[]
  for norm_src0,norm_trg0,norm_type0 in normative_list: #tokenized norm src/trg items, and type
    cur_type="normative-"+norm_type0
    criticality="high"
    src_spans=general.is_in(norm_src0,src_sent_toks)
    trg_spans=general.is_in(norm_trg0,trg_sent_toks) #we'll need to think of cases where there can be multiple trg options
    if src_spans==[] and trg_spans==[]: continue
    all_norm_matches.append((" ".join(norm_src0)," ".join(norm_trg0),src_spans, trg_spans, cur_type,match_score, criticality)) 
  return all_norm_matches

def qa_match_all(src_sent_toks,trg_sent_toks,normative_list):
  all_matches=[]
  all_matches.extend(qa_match_exact(src_sent_toks,trg_sent_toks))
  all_matches.extend(qa_match_normative(src_sent_toks,trg_sent_toks,normative_list))
  all_matches.sort(key=lambda x:len(x[0].split()))
  return all_matches

def qa_add_spans_classes(src_sent_toks,trg_sent_toks,qa_match_list):
  src_start_dict,src_end_dict={},{}
  trg_start_dict,trg_end_dict={},{}
  for src0,trg0,src_spans0,trg_spans0,match_type0,match_score0,criticality0 in qa_match_list:
    match_color="black"
    match_message=""
    class_name=""
    match_type_classes0=match_type0
    if match_type0.lower().split("-")[0] in ["normative","exact"]: match_type_classes0="%s %s"%(match_type0.lower().split("-")[0],match_type0)
    # if match_type0.lower().startswith("normative"): match_type_classes0="%s %s"%("normative",match_type0)
    # if match_type0.lower().startswith("exact"): match_type_classes0="%s %s"%("exact",match_type0)
    if len(src_spans0)==0 and len(trg_spans0)==0: continue
    if len(src_spans0)>0:
      if len(trg_spans0)==len(src_spans0): 
        match_color="lightgreen"
        match_message+=" correct match"
        class_name="match"
      elif len(trg_spans0)==0: 
        match_color="red"
        match_message="target not found"
        if criticality0=="low": class_name+=" weak-mismatch mismatch %s"%match_type_classes0
        else: class_name+=" strong-mismatch mismatch %s"%match_type_classes0
      elif len(trg_spans0)!=len(src_spans0): 
        match_color="brown"
        match_message="mismatch count of instances"
        class_name+=" weak-mismatch mismatch %s"%match_type_classes0
    else:
      if len(trg_spans0)>0:
        match_color="orange"
        match_message="found in target but not in src"
        class_name+=" weak-mismatch mismatch %s"%match_type_classes0

    for x0,x1 in src_spans0:
      src_start_dict[x0]=src_start_dict.get(x0,"")+'<span class="%s" style="%s">'%(class_name,gen_ul_style(match_color))
      src_end_dict[x1]=src_end_dict.get(x1,"")+'</span>'
    for y0,y1 in trg_spans0:
      trg_start_dict[y0]=trg_start_dict.get(y0,"")+'<span class="%s" style="%s">'%(class_name,gen_ul_style(match_color))
      trg_end_dict[y1]=src_end_dict.get(y1,"")+'</span>'
  src_open_close_tags,trg_open_close_tags=[],[]
  for i0,tok0 in enumerate(src_sent_toks):
    open0=src_start_dict.get(i0,"")
    close0=src_end_dict.get(i0,"")
    src_open_close_tags.append((open0,close0))
  for i0,tok0 in enumerate(trg_sent_toks):
    open0=trg_start_dict.get(i0,"")
    close0=trg_end_dict.get(i0,"")
    trg_open_close_tags.append((open0,close0))
  return src_open_close_tags,trg_open_close_tags


def random_color():
  rand = lambda: random.randint(100, 255)
  return '#%02X%02X%02X' % (rand(), rand(), rand())

def create_color_classes_css(n_classes=100):
  chars = '0123456789ABCDEF'
  css_str0='<style>\n'
  aligned_transparent_cls='.aligned-transparent {opacity: 0.25};\n'
  
  css_str0+=aligned_transparent_cls
 #  green_underline="""
 #  .green-ul {
 #  text-decoration: underline;
 #  -webkit-text-decoration-color: green; /* safari still uses vendor prefix */
 #  text-decoration-color: green;
    # }
 #  """
 #  red_underline="""
 #  .red-ul {
 #  text-decoration: underline;
 #  -webkit-text-decoration-color: red; /* safari still uses vendor prefix */
 #  text-decoration-color: red;
    # }
 #  """
  fixed_header_css="""
{margin:0;}

.navbar {
  overflow: hidden;
  background-color: lightyellow;
  position: fixed;
  top: 0;
  width: 100%;
}


.main {
  padding: 16px;
  margin-top: 80px;
  height: 1500px; /* Used in this example to enable scrolling */
}

  """
  #css_str0+=green_underline+red_underline+fixed_header_css
  css_str0+=fixed_header_css

  for class_i in range(n_classes):
    class_name="walign-%s"%(class_i)
    cur_color=random_color() #'#'+''.join(random.sample(chars,6))
    cur_css_line='.%s {background: %s;}\n'%(class_name,cur_color)
    css_str0+=cur_css_line
  no_bg_cls='.no-bg { background-color:transparent; }\n'
  css_str0+=no_bg_cls
  css_str0+='.item-highlight {color: red;background-color:#00CED1;font-weight: bold;}'
  css_str0+='.td-highlight {background-color:#F5F5DC;}'
  css_str0+='</style>\n'
  return css_str0

def create_align_html_table(list_aligned_classed0):
  table_str0='<table border="1" style="width:100%;table-layout:fixed;">'
  for item0 in list_aligned_classed0:
    src_cell0,trg_cell0=item0[:2]
    tr0='<tr><td style="max-width:50%%;width:50%%;">%s</td><td dir="rtl" style="max-width:50%%;width:50%%;">%s</td></tr>'%(src_cell0,trg_cell0)
    table_str0+=tr0
  table_str0+='</table>'
  return table_str0


def create_align_html_content(aligned_html_sent_pairs,phrase_analysis_table=""):
    css_content=create_color_classes_css()
    res_html_table=create_align_html_table(aligned_html_sent_pairs)
    

    cur_srcipt="""
    var qa_obj={}
    function go2el(qa_key){
      item_highlight_class="item-highlight"
      td_highlight_class="td-highlight"
      console.log(qa_obj[qa_key])
      cur_items=qa_obj[qa_key]["items"]
      cur_i=qa_obj[qa_key]["i"]
      if (cur_i==null || cur_i==undefined) cur_i=0 
      else cur_i=cur_i+1
      if (cur_i>=len(cur_items)) cur_i=0  
      qa_obj[qa_key]["i"]=cur_i

      cur_item0=cur_items[cur_i]
      parent_td=get_parent_with_tag(cur_item0,"td")
      scroll2el(cur_item0)
      $(".item-highlight").removeClass("item-highlight");
      $(".td-highlight").removeClass("td-highlight");

      if (!cur_item0.classList.contains(item_highlight_class)) cur_item0.classList.add(item_highlight_class)
      if (!parent_td.classList.contains(td_highlight_class)) parent_td.classList.add(td_highlight_class)
    }

    function init(){
      strong_mismatch_items=get_class_el_items(".strong-mismatch")
      weak_mismatch_items=get_class_el_items(".weak-mismatch")
      strong_mismatch_exact_items=filter_items(strong_mismatch_items,"exact")
      weak_mismatch_exact_items=filter_items(weak_mismatch_items,"exact")
      strong_mismatch_normative_items=filter_items(strong_mismatch_items,"normative")
      weak_mismatch_normative_items=filter_items(weak_mismatch_items,"normative")

      qa_obj["strong-mismatch"]={"items":strong_mismatch_items}
      qa_obj["weak-mismatch"]={"items":weak_mismatch_items}
      qa_obj["strong-mismatch-exact"]={"items":strong_mismatch_exact_items} 
      qa_obj["weak-mismatch-exact"]={"items":weak_mismatch_exact_items} 
      qa_obj["strong-mismatch-normative"]={"items":strong_mismatch_normative_items}
      qa_obj["weak-mismatch-normative"]={"items":weak_mismatch_normative_items}
      console.log(qa_obj)

      //filter_items(strong_mismatch_items,"exact")

      $$("exact-strong-mismatch").innerHTML=""+len(strong_mismatch_exact_items)
      $$("exact-weak-mismatch").innerHTML=""+len(weak_mismatch_exact_items)
      $$("normative-strong-mismatch").innerHTML=""+len(strong_mismatch_normative_items)
      $$("normative-weak-mismatch").innerHTML=""+len(weak_mismatch_normative_items)

        // mismatches=$(".mismatch")
        // $("#exact-strong-mismatch").text(""+mismatches.length)
        // console.log(mismatches)
    }


    function toggle_bg(){
        $(".aligned").toggleClass("no-bg");
    }
    function toggle_transparent_aligned(){
        $(".aligned").toggleClass("aligned-transparent");
    }
    function nav_classes(){

    }

    function handle(e){
            if(e.keyCode === 13){
                e.preventDefault(); // Ensure it is only this code that runs
                //alert("Enter was pressed was presses");
                //$(".aligned").toggleClass("aligned-transparent");
                //$(".aligned").toggleClass("no-bg");
            }
        }


    """

    html_main_content="""
    <html>
    <head>
      <title>QA Analysis</title>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
      <script src="https://code.jquery.com/jquery-3.6.1.min.js" integrity="sha256-o88AwQnZB+VDvE9tvIXrMQaPlFFSUTR+nldQm1LuPXQ=" crossorigin="anonymous"></script>
      <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
      <script src="https://hmghaly.github.io/script.js"></script>
    %s  
    
    <script>%s</script>
    </head>
        <body onload="init()" onkeypress="handle(event)">
    
    <div class="navbar" id="dashboard">
      <div class="row w-100 text-center">
          <div class="col"> 
            <h6>Alignment</h6>
            <button onclick="toggle_bg()">Option1</button>
            <button onclick="toggle_transparent_aligned()">Option2</button>
          </div>
          <div class="col">
            <h6>Numbers Mismatch</h6>
             <a href="JavaScript:void(0)" onclick='go2el("strong-mismatch-exact")'>Strong: <span id="exact-strong-mismatch">0</span></a>
             <a href="JavaScript:void(0)" onclick='go2el("weak-mismatch-exact")'>Weak: <span id="exact-weak-mismatch">0</span></a>
            </div>
          <div class="col">
            <h6>Normative Mismatch</h6> 
             <a href="JavaScript:void(0)" onclick='go2el("strong-mismatch-normative")'>Strong: <span id="normative-strong-mismatch">0</span></a>
             <a href="JavaScript:void(0)" onclick='go2el("weak-mismatch-normative")'>Weak: <span id="normative-weak-mismatch">0</span></a>

          </div>
          <div class="col">Terminology Mismatch</div>
          <div class="col">Spelling Mistakes</div>
    </div>
    </div>   

    <div class="main"> 


    %s

    <h2>Phrase Matching Analysis</h2>
    %s
    </div>
    </body>
    </html>
    """%(css_content,cur_srcipt,res_html_table,phrase_analysis_table)
    return html_main_content

#6 Jan 2023
def align_words_span_tags(src_tokens,trg_tokens,align_items,sent_class="sent0",only_without_children=True,max_phrase_length=6):
  src_start_dict,src_end_dict={},{}
  trg_start_dict,trg_end_dict={},{}
  for i0,align_item in enumerate(align_items):
    class_name="walign-%s"%(i0)
    el0,wt0,children0=align_item
    src_span0,trg_span0=el0
    x0,x1=src_span0
    y0,y1=trg_span0
    src_phrase0=" ".join(src_tokens[x0:x1+1]) 
    trg_phrase0=" ".join(trg_tokens[y0:y1+1])
    if "<s>" in src_phrase0 or "<s>" in trg_phrase0: continue
    if "</s>" in src_phrase0 or "</s>" in trg_phrase0: continue
    if general.is_punct(src_phrase0) or general.is_punct(trg_phrase0): continue
    valid=False
    if x1-x0<3 or children0==[]: valid=True
    if not valid: continue
    open_class_str='<span class="aligned %s %s">'%(sent_class, class_name)
    src_start_dict[x0]=src_start_dict.get(x0,"")+open_class_str
    trg_start_dict[y0]=trg_start_dict.get(y0,"")+open_class_str
    src_end_dict[x1]=src_end_dict.get(x1,"")+"</span>"
    trg_end_dict[y1]=trg_end_dict.get(y1,"")+"</span>"
  src_tok_tags,trg_tok_tags=[],[]
  for s_i,s_tok in enumerate(src_tokens):
    open0,close0=src_start_dict.get(s_i,""),src_end_dict.get(s_i,"")
    src_tok_tags.append((open0,close0))
    # print("SRC:", open0,s_tok, close0)
  for s_i,s_tok in enumerate(trg_tokens):
    open0,close0=trg_start_dict.get(s_i,""),trg_end_dict.get(s_i,"")
    trg_tok_tags.append((open0,close0))
    # print("TRG:", open0,s_tok, close0)
  return src_tok_tags,trg_tok_tags