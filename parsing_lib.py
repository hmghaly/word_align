import re, json
from collections import defaultdict

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

def get_id(input_tag,counter_dict): #this is a bad function, it takes the global variable tag_count_dict
    tmp_tag_count=counter_dict.get(input_tag,0) #how many times this tag was used before in the parse
    tmp_tag_id="%s_%s"%(input_tag,tmp_tag_count) #create tag ID
    counter_dict[input_tag]=tmp_tag_count+1 #update the tag counter
    return tmp_tag_id, counter_dict
    

def check_back(input_trie,input_seq,input_label,input_start_index,depth=0):
    sub_trie=input_trie.get(input_label,{})
    keys=sub_trie.keys()
    #print(">>>>>>>>>>> input sequence", input_seq, "depth", depth,"input_label", input_label,"input_start_index",input_start_index)
    seq_tags=[v[0] for v in input_seq]
    seq_start_indexes=[v[1] for v in input_seq]
    seq_end_indexes=[v[2] for v in input_seq]
    seq_wt=sum([v[3] for v in input_seq])
    new_seq_start=seq_start_indexes[0]
    new_seq_end=seq_end_indexes[-1]
    for k in keys:
        if k=="":
            candidates=sub_trie[k]
            for can in candidates:
                can_tag,can_wt=can
                new_wt=can_wt+seq_wt
                new_id=get_id(can_tag)
                found_wt=wt_dict[new_seq_start][new_seq_end][can_tag]
                if new_wt<=found_wt: continue #we'll need to adjust to keep track of all the generated labels
                #if depth>0: continue
                #if depth>0 and new_seq_start==new_seq_end: continue
                children_dict[new_id]=seq_tags
                tag_span_wt_dict[new_id]=(new_seq_start,new_seq_end,new_wt) #specify the properties of the current tag: span & weight
                label_end_dict[can_tag][new_seq_end].append(new_seq_start)
                cur_item=(new_id,new_seq_start,new_seq_end,new_wt)
                span_tag_dict[new_seq_start][new_seq_end][can_tag].append(cur_item)
                wt_dict[new_seq_start][new_seq_end][can_tag]=new_wt
                #check_back(input_trie,[cur_item],can_tag,new_seq_start,depth+1)

            
        else:
            found_prev_indexes=label_end_dict.get(k,{})
            if found_prev_indexes: 
                for end_index in found_prev_indexes:
                    if end_index>=input_start_index: continue
                    starting_indexes=found_prev_indexes[end_index]
                    for s0 in starting_indexes:
                        cur_ids=span_tag_dict[s0][end_index][k]
                        #print("found previous tags",input_label, input_seq, k,s0, end_index,cur_ids)
                        check_back(sub_trie[k],cur_ids+input_seq,k,s0,depth+1)
                        
                #print('--------')

                    
            
        
    #print("----")

def merge(input_seq):
    pass


def back(input_label,input_trie,input_end_dict,input_index,seq=[],new_phrases=[],depth=0):
    sub_trie=input_trie.get(input_label,{})
    prev_labels=sub_trie.keys()
    if depth==0: prev_labels=[v for v in prev_labels if v!=""]
    #else: print prev_labels
    for pl in prev_labels:
        if pl=="":
            final_labels=sub_trie[pl]
            for fl in final_labels:
                #print "depth", depth, "input_index", input_index,  "converging", fl, "sequence", seq
                new_phrases.append((fl,seq))
        else:            
            prev_indexes=input_end_dict.get(pl)
            if prev_indexes==None: continue
            
            for i0,i1 in prev_indexes:
                if i1>=input_index: continue
                #print "depth", depth, "input_label: ", input_label, "input_index", input_index, "prev_label: " , pl, "prev_indexes: ", i0,i1
                cur_ids=input_end_dict[pl][(i0,i1)]
                cur_ids.sort(key=lambda x:-x[1])
                top_phrase=cur_ids[0]
                #print "found >>>", cur_ids
                new_phrases=back(pl,sub_trie,input_end_dict,i0,[(top_phrase[0],top_phrase[1],i0,i1)]+seq,new_phrases,depth+1)
    return new_phrases
        

if __name__=="__main__":
    rule_dict={}
    token_dict={}
    #bw_dict={} #backwards dictionary - identifies the last tag in a rule, its previous tags, and the new tag they form
    model_name="bnc_1000"
    rules_fname="%s.rules.txt"%model_name
    tokens_pos_fname="%s.tokens.pos.txt"%model_name
    rules_fopen=open(rules_fname)
    rule_trie = dict()
    for ri,rf in enumerate(rules_fopen):
        split=rf.strip("\n\r").split("\t")
        if len(split)!=2: continue
        key=tuple(json.loads(split[0]))
        val=json.loads(split[1])
        if len(key)==1: val.pop(key[0], None) #to avoid things like NP > NP > NP ... for single label rules
        reversed_key=reversed(key)
        current_dict = rule_trie
        for rk in reversed_key:
            current_dict = current_dict.setdefault(rk, {})
        current_dict[""]=[(k0,val[k0]) for k0 in val]
    rules_fopen.close()
    #walk_dict(rule_trie)

    tokens_pos_fopen=open(tokens_pos_fname) #we create a unigram dictionary for the possible tags for each token
    for ti,tf in enumerate(tokens_pos_fopen):
        split=tf.strip("\n\r").split("\t")
        if len(split)!=2: continue
        token_dict[split[0]]=json.loads(split[1])
    tokens_pos_fopen.close()

    

    #end_dict={} #end_dict[index][tag]=[(tag1,start_index_tag1),(tag1,start_index_tag1) ...]
    tag_count_dict={} #to count the occurances of a certain tag to create tag ID
    tag_span_wt_dict={} #tag_span_wt_dict[tag_id]=(start,end,wt)
    children_dict={} #children_dict[parent_tag]=[child_tag1,child_tag2...]
    #generic_end_dict={} #generic label with its end index, and the corresponding list of beginning indexes, e.g. generic_dict[NP][5]=[5,4]
    #specific_tag_start_end={} #for a generic tag with a specific start and end indexes, what are the corresponding phrase IDs with their weights specific_tag_start_end[NP][0][2]=[(NP_0,5),(NP_15,2)]
    span_tag_dict = nested_dict(3, list) #what are the phrase ids and their corresponding weights, that fall within this span with this tag e.g. span_dict[0][5][NP]=[(NP_1,15),(NP_5,20)]
    label_end_dict = nested_dict(2, list) #for each label, and for each end indexes, what are the corresponding beginning indexes
    wt_dict = nested_dict(3, int) #the maximum weight reached for a given span and label

    #span_tag_dict={} #span_tag_dict[(0,1)]=tag_id
    #span_wt_dict={} #span_wt_dict[(0,1)]=tag_wt
    #wt_check_dict={} #wt_check_dict[(0,1,NP)]=15
    #tag_dict = defaultdict(dict)
    #wt_dict = defaultdict(dict)
    #new_tag_dict = nested_dict(3, str)


    sent=["I","will","go","there","at","the","door"]
    stack=[]
    for index,word in enumerate(sent):
        print(index,word)
        cur_tags=token_dict.get(word.lower(),{}) #we get possible tags for each token
        #local_dict=nested_dict(1, list)
        all_new_labels=[]
        #print(si,s,cur_tags)
        #print("-----")
        for terminal_label in cur_tags:
            #print("terminal_label",terminal_label)
            cur_start_index,cur_end_index=index,index
            cur_wt=cur_tags[terminal_label] #the weight of the current tag
            cur_tag_id,tag_count_dict=get_id(terminal_label,tag_count_dict)
            all_new_labels.append((terminal_label,cur_wt,cur_start_index,cur_end_index,cur_tag_id,"")) #last one is the child tag
            cur_sub_trie=rule_trie.get(terminal_label,{})
            non_terminal_labels=cur_sub_trie.get("",[])
            for nt_label,nt_wt in non_terminal_labels:
                #print "terminal_label",terminal_label, cur_wt, "non_terminal_labels", nt_label, nt_wt
                nt_tag_id,tag_count_dict=get_id(nt_label,tag_count_dict)
                combined_wt=cur_wt+nt_wt
                all_new_labels.append((nt_label,combined_wt,cur_start_index,cur_end_index,nt_tag_id,cur_tag_id))
                children_dict[nt_tag_id]=[cur_tag_id]
                #print nt_tag_id, combined_wt
        all_new_labels.sort(key=lambda x:-x[1])
        used_labels=[]
        for a in all_new_labels:
            a_label=a[0]
            a_wt=a[1]
            a_id=a[-2]
            #print a_label
            if a_label in used_labels: 
                #print "excluding >>>", a
                continue
            used_labels.append(a_label)
            
            final_new_phrases=back(a_label,rule_trie,label_end_dict,index,depth=0)
            label_end_dict[a_label][(index,index)].append((a_id,a_wt))
            for fn in final_new_phrases:
                print fn
            
##            sub_trie=rule_trie.get(a_label,{})
##            label_end_dict[a_label][index].append(index)
##            prev_labels=sub_trie.keys()
##            
##                
##            print ">>>", a, a_label, index#, prev_labels
##            for pl in prev_labels:
##                prev_indexes=label_end_dict.get(pl)
##                if prev_indexes==None: continue
##                
##                print pl, prev_indexes
        print '-------'


##    for le in label_end_dict:
##        print le, label_end_dict[le]
    #walk_dict(label_end_dict)
    #for td in label_end_dict:
    #    print(td, label_end_dict[td])
    #    print('------')

  #for td in generic_end_dict:
  #    print(td, generic_end_dict[td])
  #    print('------')
    #for st in stack:

    #   print(st, tag_span_wt_dict.get(st), parent_dict.get(st))
    #for ed in end_dict:
    #   print(ed, end_dict[ed])
    #   print('---')
    #for sp in span_tag_dict:
    #   print(">>>", sp, span_tag_dict[sp])
    #   print('---')
        



