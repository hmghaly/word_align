import re, json
from collections import defaultdict
#spaCy part
import os, re, shelve, sys
import spacy
from spacy.tokenizer import Tokenizer
from itertools import groupby
sys.path.append("code_utils")
import general


nlp = spacy.load("en_core_web_sm")
#http://spyysalo.github.io/conllu.js/
#https://github.com/explosion/spaCy/issues/533 #spacy to output conll format
nlp.tokenizer = Tokenizer(nlp.vocab, token_match=re.compile(r'\S+').match)
def tok_sent_join(sent_text): #tokenize with our function, and then join with whitespace for spacy tokenization
    tokenized_sent=general.tok(sent_text)
    return " ".join(tokenized_sent)

def get_conll(sent_input): #Use spaCy to get CoNLL format outpus of an input sentence
    new_sent_input=tok_sent_join(sent_input) #
    doc = nlp(new_sent_input)
    conll_2d=[]
    for token in doc:   
        token_i = token.i+1
        if token.i==token.head.i: head_i=0
        else: head_i = token.head.i+1
        items=[token_i,token.text, token.lemma_, token.tag_, token.pos_, "_", head_i, token.dep_,"_","_"]
        conll_2d.append(items)
    return conll_2d


#https://github.com/hmghaly/word_align/edit/master/parsing_lib.py

def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

def walk_dict(d,depth=0):
    for k,v in sorted(d.items(),key=lambda x: x[0]):
        if isinstance(v, dict):
            print ("  ")*depth + ("%s" % k)
            walk_dict(v,depth+1)
        else:
            print ("  ")*depth + "%s %s" % (k, v)         


def add2trie(cur_trie,items,val,terminal_item=""):
    new_trie=cur_trie
    for it in items:
        new_trie = new_trie.setdefault(it, {})
    new_trie[terminal_item]=val
    return cur_trie

#TO BE UPDATED WITH MORE RULES
rules=[
       "IN NP > PP",
       "NP PP > NP",
       "NP CONJ NP > NP",
       "VP CONJ VP > VP",
       "PP CONJ PP > PP",
       "DT NN > NP",
       "PRP$ NN > NP",
       "JJ NN > NN",
       "JJ JJ > JJ",
       "NN NN > NN",
       "AUX V > V",
       "NP S/NP > NP",
       "RB JJ > JJ"
]
uni_rules=[("PRON","NP"),
           ("NN","NP"),
           ("JJ","ADJ"),
           ("be","V")
           ]
cur_trie=defaultdict(lambda: defaultdict(dict))
for rl in rules:
  items_str,val=rl.split(">")
  items_str,val=items_str.strip(),val.strip()
  items=[v for v in items_str.split(" ") if v]
  items_reveresed=reversed(items)
  #print(items,val)
  cur_trie=add2trie(cur_trie,items_reveresed,val)

def look_back(phrase_span0,all_phrase_spans0,rule_trie0,child_dict0,sequence0=[],depth=0):
  label,i0,i1=phrase_span0
  prev_phrase_spans=[v for v in all_phrase_spans0 if v[-1]+1==i0] #get all previous spans whose span end is right before the current span beginning << we can adjust this to skip
  tmp_rule_trie=rule_trie0.get(label,{})
  tmp_sequence=  sequence0+[phrase_span0]
  tmp_rule_trie=rule_trie0
  for seq in tmp_sequence:
    tmp_rule_trie=tmp_rule_trie.get(seq[0],{})
  for a,b in uni_rules: #apply uni rules first to avoid infinite loops
    if label==a:
      new_phrase_span=(b,i0,i1)
      if new_phrase_span in all_phrase_spans0: continue
      found_children=child_dict0.get(new_phrase_span,[])
      if not new_phrase_span in found_children: child_dict0[new_phrase_span]=found_children+[[phrase_span0]]
      all_phrase_spans0.append(new_phrase_span)
      child_dict0,all_phrase_spans0=look_back(new_phrase_span,all_phrase_spans0,rule_trie0,child_dict0,[],depth+1)
      #Now do recursion on the new phrase span
  for key, val in tmp_rule_trie.items():
    #print("key:",key,"val:",val)
    converged_label=val.get("") #check if there can be a label that the current sequence converges to
    # print(">>> converged_label",converged_label)
    for prev in prev_phrase_spans:
      if not prev[0]==key: continue
      if converged_label!=None:
        new_sequence=tmp_sequence+[prev]
        new_phrase_start=min([v[1] for v in new_sequence])
        new_phrase_end=max([v[2] for v in new_sequence])
        #new_phrase_span=(converged_label,prev[1],phrase_span0[2])
        new_phrase_span=(converged_label,new_phrase_start,new_phrase_end)
        found_children=child_dict0.get(new_phrase_span,[])

        if not new_phrase_span in found_children: child_dict0[new_phrase_span]=found_children+[new_sequence]
        if new_phrase_span in all_phrase_spans0: continue
        all_phrase_spans0.append(new_phrase_span)
        child_dict0,all_phrase_spans0=look_back(new_phrase_span,all_phrase_spans0,rule_trie0,child_dict0,[],depth+1)
        #print("prev >>>>", prev, "current >>>",phrase_span0, " - Converge to:",new_phrase_span)
      else:
        child_dict0,all_phrase_spans0=look_back(prev,all_phrase_spans0,rule_trie0,child_dict0,tmp_sequence,depth+1)
        pass

  return child_dict0, all_phrase_spans0

def get_children_recursive(node0,child_dict0,parent_node=(),all_nodes=[],depth=0):
  tmp_nodes=all_nodes+[(node0,parent_node,depth)]
  for ch0 in child_dict0.get(node0,[[]])[0]:
    tmp_nodes=get_children_recursive(ch0,child_dict0,node0,tmp_nodes,depth+1)
  return tmp_nodes


class parse:
  def __init__(self,sent0,cur_trie0,verb_frame_shelve_path):
    self.cur_trie=cur_trie0
    self.child_dict={}
    conll_out=get_conll(sent0)
    self.all_phrases_spans=[]
    #all_phrase_rules=[]
    tag_word_dict={}
    verb_shelve_open=shelve.open(verb_frame_shelve_path)
    verb_frame_dict={}
    for i_,co in enumerate(conll_out):
      verb_frame_dict[co[2]]=verb_shelve_open.get(co[2],[])  #create a small dictionary for the frames of the word in this sentence
    verb_shelve_open.close()
    for i_,co in enumerate(conll_out):
      word,lemma,tag,pos=co[1],co[2],co[3],co[4]
      if tag.startswith("V"): uni_rules.append((tag,"V")) #expand the UNI rules for any tverb tag to "V" to match the frames in verb frame
      if tag.startswith("JJ") and tag!="JJ": uni_rules.append((tag,"JJ"))
      if tag.startswith("NN") and tag!="NN": uni_rules.append((tag,"NN"))
      
      verb_frames=[]
      if pos in ["VERB","AUX"]: #get the frames of any word if it is a verb 
        frames=verb_frame_dict.get(lemma,[])
        for f in frames: 
          vb_frame=f[0]
          verb_frames.append(vb_frame) #add the verb frames to the trie, with their VP rules, and the slash rules
          vb_frame_items=[v for v in vb_frame.split(" ") if v]
          vb_frame_items=[v.split("-")[0] for v in vb_frame_items]
          vb_frame_items=[v.split(".")[0] for v in vb_frame_items] #just to remove things liks NP.xxx or PP-xxx
          self.cur_trie=add2trie(self.cur_trie,reversed(vb_frame_items),"S")
          np_locs=[i_ for i_, v_ in enumerate(vb_frame_items) if v_=="NP" and i_!=0]
          for np_i in np_locs: #identify NP locations in object/dative positions in frame
            list_copy=list(vb_frame_items)
            list_copy.pop(np_i)
            self.cur_trie=add2trie(self.cur_trie,reversed(list_copy),"S/NP") #create a copy with the slash rule

      for lb in co[1:5]: #we iterate over the word, its stem, its POS and tag
        cur_phrase_span=(lb,i_,i_)
        if cur_phrase_span in self.all_phrases_spans: continue
        self.all_phrases_spans.append(cur_phrase_span) #[(word,i_,i_)]
        tag_word_dict[cur_phrase_span]=(word,i_,i_)
        self.child_dict, self.all_phrases_spans=look_back(cur_phrase_span,self.all_phrases_spans,self.cur_trie,self.child_dict,[]) #now run the recursive look_back function
    self.parse_nodes=[]
    for node,children in self.child_dict.items():
      if node[1]==0 and node[2]==len(conll_out)-1:  #if a node spans the entire sentence
        self.parse_nodes=get_children_recursive(node,self.child_dict,(),[],0)
    self.parse_phrase_list=[]
    max_level=0
    if self.parse_nodes: max_level=max([v[-1] for v in self.parse_nodes])
    self.out_dict={}
    self.out_dict["n_words"]=len(conll_out)
    self.out_dict["n_levels"]=max_level
    for node,parent_node,depth in self.parse_nodes:
      node_str="-".join([str(v) for v in node])
      parent_str="-".join([str(v) for v in parent_node])
      node_i0,node_i1=node[1],node[2]
      cur_depth=max_level-depth
      self.parse_phrase_list.append((node_str,node_i0,node_i1,parent_str,cur_depth))
      corr_word_node=tag_word_dict.get(node)
      if corr_word_node!=None:
        word_node_str= "-".join([str(v) for v in corr_word_node])
        new_depth=cur_depth-1
        self.parse_phrase_list.append((word_node_str,node_i0,node_i1,node_str,new_depth))
    self.out_dict["phrases"]=self.parse_phrase_list
    self.json_out=json.dumps(self.out_dict)




# def get_id(input_tag,counter_dict): #this is a bad function, it takes the global variable tag_count_dict
#     tmp_tag_count=counter_dict.get(input_tag,0) #how many times this tag was used before in the parse
#     tmp_tag_id="%s_%s"%(input_tag,tmp_tag_count) #create tag ID
#     counter_dict[input_tag]=tmp_tag_count+1 #update the tag counter
#     return tmp_tag_id, counter_dict
    

# def check_back(input_trie,input_seq,input_label,input_start_index,depth=0):
#     sub_trie=input_trie.get(input_label,{})
#     keys=sub_trie.keys()
#     #print(">>>>>>>>>>> input sequence", input_seq, "depth", depth,"input_label", input_label,"input_start_index",input_start_index)
#     seq_tags=[v[0] for v in input_seq]
#     seq_start_indexes=[v[1] for v in input_seq]
#     seq_end_indexes=[v[2] for v in input_seq]
#     seq_wt=sum([v[3] for v in input_seq])
#     new_seq_start=seq_start_indexes[0]
#     new_seq_end=seq_end_indexes[-1]
#     for k in keys:
#         if k=="":
#             candidates=sub_trie[k]
#             for can in candidates:
#                 can_tag,can_wt=can
#                 new_wt=can_wt+seq_wt
#                 new_id=get_id(can_tag)
#                 found_wt=wt_dict[new_seq_start][new_seq_end][can_tag]
#                 if new_wt<=found_wt: continue #we'll need to adjust to keep track of all the generated labels
#                 #if depth>0: continue
#                 #if depth>0 and new_seq_start==new_seq_end: continue
#                 children_dict[new_id]=seq_tags
#                 tag_span_wt_dict[new_id]=(new_seq_start,new_seq_end,new_wt) #specify the properties of the current tag: span & weight
#                 label_end_dict[can_tag][new_seq_end].append(new_seq_start)
#                 cur_item=(new_id,new_seq_start,new_seq_end,new_wt)
#                 span_tag_dict[new_seq_start][new_seq_end][can_tag].append(cur_item)
#                 wt_dict[new_seq_start][new_seq_end][can_tag]=new_wt
#                 #check_back(input_trie,[cur_item],can_tag,new_seq_start,depth+1)

            
#         else:
#             found_prev_indexes=label_end_dict.get(k,{})
#             if found_prev_indexes: 
#                 for end_index in found_prev_indexes:
#                     if end_index>=input_start_index: continue
#                     starting_indexes=found_prev_indexes[end_index]
#                     for s0 in starting_indexes:
#                         cur_ids=span_tag_dict[s0][end_index][k]
#                         #print("found previous tags",input_label, input_seq, k,s0, end_index,cur_ids)
#                         check_back(sub_trie[k],cur_ids+input_seq,k,s0,depth+1)
                        
#                 #print('--------')

                    
            
        
#     #print("----")

# def merge(input_seq):
#     pass


# def back(input_label,input_trie,input_end_dict,input_index,seq=[],new_phrases=[],depth=0):
#     sub_trie=input_trie.get(input_label,{})
#     prev_labels=sub_trie.keys()
#     if depth==0: prev_labels=[v for v in prev_labels if v!=""]
#     #else: print prev_labels
#     for pl in prev_labels:
#         if pl=="":
#             final_labels=sub_trie[pl]
#             for fl in final_labels:
#                 #print "depth", depth, "input_index", input_index,  "converging", fl, "sequence", seq
#                 new_phrases.append((fl,seq))
#         else:            
#             prev_indexes=input_end_dict.get(pl)
#             if prev_indexes==None: continue
            
#             for i0,i1 in prev_indexes:
#                 if i1>=input_index: continue
#                 #print "depth", depth, "input_label: ", input_label, "input_index", input_index, "prev_label: " , pl, "prev_indexes: ", i0,i1
#                 cur_ids=input_end_dict[pl][(i0,i1)]
#                 cur_ids.sort(key=lambda x:-x[1])
#                 top_phrase=cur_ids[0]
#                 #print "found >>>", cur_ids
#                 new_phrases=back(pl,sub_trie,input_end_dict,i0,[(top_phrase[0],top_phrase[1],i0,i1)]+seq,new_phrases,depth+1)
#     return new_phrases
        

if __name__=="__main__":
    pass
    print("Hello!")
    sent="the woman I love is pretty"
    shelve_fpath="verbs.shelve"
    parse_obj=parse(sent,cur_trie,shelve_fpath)
    print(parse_obj.json_out)
    # for a in parse_obj.parse_phrase_list:
    #   print(a)

#     rule_dict={}
#     token_dict={}
#     #bw_dict={} #backwards dictionary - identifies the last tag in a rule, its previous tags, and the new tag they form
#     model_name="bnc_1000"
#     rules_fname="%s.rules.txt"%model_name
#     tokens_pos_fname="%s.tokens.pos.txt"%model_name
#     rules_fopen=open(rules_fname)
#     rule_trie = dict()
#     for ri,rf in enumerate(rules_fopen):
#         split=rf.strip("\n\r").split("\t")
#         if len(split)!=2: continue
#         key=tuple(json.loads(split[0]))
#         val=json.loads(split[1])
#         if len(key)==1: val.pop(key[0], None) #to avoid things like NP > NP > NP ... for single label rules
#         reversed_key=reversed(key)
#         current_dict = rule_trie
#         for rk in reversed_key:
#             current_dict = current_dict.setdefault(rk, {})
#         current_dict[""]=[(k0,val[k0]) for k0 in val]
#     rules_fopen.close()
#     #walk_dict(rule_trie)

#     tokens_pos_fopen=open(tokens_pos_fname) #we create a unigram dictionary for the possible tags for each token
#     for ti,tf in enumerate(tokens_pos_fopen):
#         split=tf.strip("\n\r").split("\t")
#         if len(split)!=2: continue
#         token_dict[split[0]]=json.loads(split[1])
#     tokens_pos_fopen.close()

    

#     #end_dict={} #end_dict[index][tag]=[(tag1,start_index_tag1),(tag1,start_index_tag1) ...]
#     tag_count_dict={} #to count the occurances of a certain tag to create tag ID
#     tag_span_wt_dict={} #tag_span_wt_dict[tag_id]=(start,end,wt)
#     children_dict={} #children_dict[parent_tag]=[child_tag1,child_tag2...]
#     #generic_end_dict={} #generic label with its end index, and the corresponding list of beginning indexes, e.g. generic_dict[NP][5]=[5,4]
#     #specific_tag_start_end={} #for a generic tag with a specific start and end indexes, what are the corresponding phrase IDs with their weights specific_tag_start_end[NP][0][2]=[(NP_0,5),(NP_15,2)]
#     span_tag_dict = nested_dict(3, list) #what are the phrase ids and their corresponding weights, that fall within this span with this tag e.g. span_dict[0][5][NP]=[(NP_1,15),(NP_5,20)]
#     label_end_dict = nested_dict(2, list) #for each label, and for each end indexes, what are the corresponding beginning indexes
#     wt_dict = nested_dict(3, int) #the maximum weight reached for a given span and label

#     #span_tag_dict={} #span_tag_dict[(0,1)]=tag_id
#     #span_wt_dict={} #span_wt_dict[(0,1)]=tag_wt
#     #wt_check_dict={} #wt_check_dict[(0,1,NP)]=15
#     #tag_dict = defaultdict(dict)
#     #wt_dict = defaultdict(dict)
#     #new_tag_dict = nested_dict(3, str)


#     sent=["I","will","go","there","at","the","door"]
#     stack=[]
#     for index,word in enumerate(sent):
#         print(index,word)
#         cur_tags=token_dict.get(word.lower(),{}) #we get possible tags for each token
#         #local_dict=nested_dict(1, list)
#         all_new_labels=[]
#         #print(si,s,cur_tags)
#         #print("-----")
#         for terminal_label in cur_tags:
#             #print("terminal_label",terminal_label)
#             cur_start_index,cur_end_index=index,index
#             cur_wt=cur_tags[terminal_label] #the weight of the current tag
#             cur_tag_id,tag_count_dict=get_id(terminal_label,tag_count_dict)
#             all_new_labels.append((terminal_label,cur_wt,cur_start_index,cur_end_index,cur_tag_id,"")) #last one is the child tag
#             cur_sub_trie=rule_trie.get(terminal_label,{})
#             non_terminal_labels=cur_sub_trie.get("",[])
#             for nt_label,nt_wt in non_terminal_labels:
#                 #print "terminal_label",terminal_label, cur_wt, "non_terminal_labels", nt_label, nt_wt
#                 nt_tag_id,tag_count_dict=get_id(nt_label,tag_count_dict)
#                 combined_wt=cur_wt+nt_wt
#                 all_new_labels.append((nt_label,combined_wt,cur_start_index,cur_end_index,nt_tag_id,cur_tag_id))
#                 children_dict[nt_tag_id]=[cur_tag_id]
#                 #print nt_tag_id, combined_wt
#         all_new_labels.sort(key=lambda x:-x[1])
#         used_labels=[]
#         for a in all_new_labels:
#             a_label=a[0]
#             a_wt=a[1]
#             a_id=a[-2]
#             #print a_label
#             if a_label in used_labels: 
#                 #print "excluding >>>", a
#                 continue
#             used_labels.append(a_label)
            
#             final_new_phrases=back(a_label,rule_trie,label_end_dict,index,depth=0)
#             label_end_dict[a_label][(index,index)].append((a_id,a_wt))
#             for fn in final_new_phrases:
#                 print fn
            
# ##            sub_trie=rule_trie.get(a_label,{})
# ##            label_end_dict[a_label][index].append(index)
# ##            prev_labels=sub_trie.keys()
# ##            
# ##                
# ##            print ">>>", a, a_label, index#, prev_labels
# ##            for pl in prev_labels:
# ##                prev_indexes=label_end_dict.get(pl)
# ##                if prev_indexes==None: continue
# ##                
# ##                print pl, prev_indexes
#         print '-------'


# ##    for le in label_end_dict:
# ##        print le, label_end_dict[le]
#     #walk_dict(label_end_dict)
#     #for td in label_end_dict:
#     #    print(td, label_end_dict[td])
#     #    print('------')

#   #for td in generic_end_dict:
#   #    print(td, generic_end_dict[td])
#   #    print('------')
#     #for st in stack:

#     #   print(st, tag_span_wt_dict.get(st), parent_dict.get(st))
#     #for ed in end_dict:
#     #   print(ed, end_dict[ed])
#     #   print('---')
#     #for sp in span_tag_dict:
#     #   print(">>>", sp, span_tag_dict[sp])
#     #   print('---')
        



