import re
#return children_dict, terminal_dict, flat_dict, all_terminals,vertical_dict

def strip_num(txt): #to strip trailing numbers and underscores
    return txt.strip("0123456789_")


class ptb:
    def __init__(self,ptb_tree_str):
        all_labels=[]
        ptb_tree_str=ptb_tree_str.replace("\n"," ") #we remove line breaks 
        open_labels=re.finditer("(\(\S+)",ptb_tree_str) #get the open tags with non-space items
        open_labels2=re.finditer("(\(\s+)",ptb_tree_str) #get open brackets followed by space
        for op in open_labels: #for each of the open and closed labels found, we use finditer to get its exact start and end points within the tring
            all_labels.append((op.group(), op.start(),op.end())) 
        for op in open_labels2:
            all_labels.append((op.group(), op.start(),op.end())) 

        closed_labels=re.finditer("\)",ptb_tree_str) #get closing brackets
        for cl in closed_labels:
            all_labels.append((cl.group(), cl.start(),cl.end()))

        all_labels.sort(key=lambda x:x[1]) #we sort both the opening and closing tags/brackets by their start index in the tree string (which tags come first)

        open_tags=[] #this is to control the opening and closing of tags, signaled by brackets
        self.all_tag_ids=[]
        self.children_dict={} #showing which nodes dominates which
        tag_count_dict={} #to count the occurance of each tag type, and use it to give each node a unique ID
        self.tag_info_dict={} #to keep track of the start and end indexes within the tree string
        full_span_dict={} #to show the entire string covered by a certain node
        self.terminal_dict={} #to show if this is a terminal node or not
        #phrase_dict={} #NOT needed - to show the phrase tring covered by this node
        self.flat_dict={} #to show the terminal tokens with their token indexes
        self.vertical_dict={} #to show the open tags corresponding to each node, up to the root of the tree
        self.all_terminals=[] #to collect all the terminal tokens
        terminal_counter=0
        for al in all_labels:
            tag_str,tag_start,tag_end=al
            #print al
            prev_tag="" #initialize the previous tag
            if open_tags: prev_tag=open_tags[-1] #if we already have open tags, then our previous tag is the last of these
            if al[0][0]=="(": #if it is an open tag
                tag_name=tag_str[1:] 
                tag_count=tag_count_dict.get(tag_name,0)
                tag_id="%s_%s"%(tag_name,tag_count) #creating a unique node ID from the tag name and tag count
                self.all_tag_ids.append(tag_id)
                tag_count_dict[tag_name]=tag_count+1
                open_tags.append(tag_id) #add the current open tag to the list of open tags
                self.children_dict[prev_tag]=self.children_dict.get(prev_tag,[])+[tag_id] #add the current node to the children dict
                self.tag_info_dict[tag_id]=(tag_start,tag_end) #keep track of the start and end indexes of the current tag/node
            else: #if it is a closing tag/bracket
                prev_start,prev_end=prev_tag_info=self.tag_info_dict[prev_tag] #we identify the start and end indexes of the last open tag
                cur_span=ptb_tree_str[prev_end:tag_start] #then we identify the current span
                full_span_dict[prev_tag]=(prev_start,tag_end) #maybe not needed, just showing the full string span under the currently open node (prev_tag)
                open_tags=open_tags[:-1] #IMPORTANT - this is how we remove the last open tag from the list of open tags once we encounter a closing tag
                #test_span=re.sub("\)+",")",cur_span) #maybe not needed
                #span_items=re.findall("(\S+)\)",test_span) #maybe not needed
                #phrase_dict[prev_tag]=" ".join(span_items) #maybe not needed
                if "(" in cur_span or ")" in cur_span: continue #the following code will be excuted only if it is a terminal node
                cur_terminal=(cur_span.strip(),terminal_counter) #we need to keep both the terminal token and its index
                self.all_terminals.append(cur_terminal) #and add it to the list of terminal tokens
                for opt in open_tags: self.flat_dict[opt]=self.flat_dict.get(opt,[])+[cur_terminal] #and add it to all of the open tags (nodes dominating it)
                self.flat_dict[prev_tag]=self.flat_dict.get(prev_tag,[])+[cur_terminal] #not to forget the previous open tag which we just removed from the list of open tags
                self.vertical_dict[cur_terminal]=open_tags+[prev_tag] #and here for each terminal token with its index, we show all the nodes all the way up to the root of the tree
                self.terminal_dict[prev_tag]=cur_terminal #and here it tells us if the current open tag is a terminal node or not
                #phrase_dict[prev_tag]=cur_span.strip() #maybe not needed
                terminal_counter+=1 #to keep track of the token indexes
                self.children_dict[prev_tag]=self.children_dict.get(prev_tag,[])+[cur_terminal] #to include the terminal token in the children of terminal nodes
    def get_phrases(self):
        self.phrase_list=[]
        for fd in self.flat_dict:
            tag_name=fd.split("_")[0]
            cur_words_indexes=self.flat_dict[fd]
            cur_words=[v[0] for v in cur_words_indexes]
            cur_words_str=" ".join(cur_words)
            first,last=cur_words_indexes[0][1],cur_words_indexes[-1][1]
            self.phrase_list.append((tag_name,cur_words_str,first,last,len(self.all_terminals)))
        self.phrase_list=list(set(self.phrase_list))
        return self.phrase_list  
    def get_non_terminals(self,ignore_tags=["s1","top","root",""]):
        self.non_terminal_phrase_list=[]
        for fd in self.flat_dict:
            if self.terminal_dict.get(fd)!=None: continue
            tag_name=fd.split("_")[0]
            if tag_name.lower() in ignore_tags: continue
            cur_words_indexes=self.flat_dict[fd]
            cur_words=[v[0] for v in cur_words_indexes]
            cur_words_str=" ".join(cur_words)
            first,last=cur_words_indexes[0][1],cur_words_indexes[-1][1]
            self.non_terminal_phrase_list.append((tag_name,cur_words_str,first,last,len(self.all_terminals)))
        self.non_terminal_phrase_list=list(set(self.non_terminal_phrase_list))
        return self.non_terminal_phrase_list


class tree_diff:
    def __init__(self,ptb_gold_tree_str,ptb_guessed_tree_str,ignore_tags=["s1","top","root",""]): #indicate which spurious tags to ignore in our tree difference analysis
        gold_tree_obj=ptb(ptb_gold_tree_str)
        guessed_tree_obj=ptb(ptb_guessed_tree_str)
        self.gold_tree_nt_phrases=[v for v in gold_tree_obj.get_non_terminals() if not v[0].lower() in ignore_tags]
        self.guessed_tree_nt_phrases=[v for v in guessed_tree_obj.get_non_terminals() if not v[0].lower() in ignore_tags]
        self.common_phrases=[v for v in self.guessed_tree_nt_phrases if v in self.gold_tree_nt_phrases]
        self.missed_phrases=[v for v in self.gold_tree_nt_phrases if not v in self.guessed_tree_nt_phrases]
        self.wrong_phrases=[v for v in self.guessed_tree_nt_phrases if not v in self.gold_tree_nt_phrases]
        self.precision=0
        if len(self.guessed_tree_nt_phrases)!=0: self.precision=float(len(self.common_phrases))/len(self.guessed_tree_nt_phrases)
        self.recall=0
        if len(self.gold_tree_nt_phrases)!=0: self.recall=float(len(self.common_phrases))/len(self.gold_tree_nt_phrases)
        self.f1=0
        if self.precision+self.recall!=0: self.f1=float(2)*(self.precision*self.recall)/(self.precision+self.recall)
        #if len(self.common_phrases)==0 or len(self.guessed_tree_nt_phrases)==0 or len(self.gold_tree_nt_phrases)==0: return


        #self.precision=float(len(self.common_phrases))/len(self.guessed_tree_nt_phrases)
        #self.recall=float(len(self.common_phrases))/len(self.gold_tree_nt_phrases)
        #self.f1=2*(self.precision*self.recall)/(self.precision+self.recall)

        

class tree_diff_phrase_list: #a faster way to compare two trees if you already have the non-terminal phrase list of each
    def __init__(self,gold_tree_nt_phrases,guessed_tree_nt_phrases,ignore_tags=["s1","top","root",""]): #indicate which spurious tags to ignore in our tree difference analysis
        #gold_tree_obj=ptb(ptb_gold_tree_str)
        #guessed_tree_obj=ptb(ptb_guessed_tree_str)
        #self.gold_tree_nt_phrases=[v for v in gold_tree_obj.get_non_terminals() if not v[0].lower() in ignore_tags]
        #self.guessed_tree_nt_phrases=[v for v in guessed_tree_obj.get_non_terminals() if not v[0].lower() in ignore_tags]
        self.common_phrases=[v for v in guessed_tree_nt_phrases if v in gold_tree_nt_phrases]
        self.missed_phrases=[v for v in gold_tree_nt_phrases if not v in guessed_tree_nt_phrases]
        self.wrong_phrases=[v for v in guessed_tree_nt_phrases if not v in gold_tree_nt_phrases]
        self.precision=0
        if len(guessed_tree_nt_phrases)!=0: self.precision=float(len(self.common_phrases))/len(guessed_tree_nt_phrases)
        self.recall=0
        if len(gold_tree_nt_phrases)!=0: self.recall=float(len(self.common_phrases))/len(gold_tree_nt_phrases)
        self.f1=0
        if self.precision+self.recall!=0: self.f1=float(2)*(self.precision*self.recall)/(self.precision+self.recall)
        #if len(self.common_phrases)==0 or len(self.guessed_tree_nt_phrases)==0 or len(self.gold_tree_nt_phrases)==0: return

def extract_rules_tree_str(tree_str,start_end=False,ignore_tags=["s1","top","root",""]):
    ptb_obj=ptb(tree_str)
    return extract_rules(ptb_obj,start_end,ignore_tags)

def extract_rules(ptb_obj,start_end=False,ignore_tags=["s1","top","root",""]):
    #ptb_obj=ptb(tree_str)
    ch_dict,terminal_dict=ptb_obj.children_dict, ptb_obj.terminal_dict
    flat_dict=ptb_obj.flat_dict
    terminals=[v[0] for v in ptb_obj.all_terminals]
    #print (terminals)
    terminal_rules,non_terminal_rules=[],[]
    for ch in ch_dict:
        terminal_check=terminal_dict.get(ch)
        ch_stripped=strip_num(ch)
        if ch_stripped.lower() in ignore_tags: continue
        if terminal_check:
            cur_word=ch_dict[ch][0][0]
            terminal_rules.append((ch_stripped, cur_word))
        else: 
            if start_end: cur_nt_children=[(strip_num(v),ptb_obj.flat_dict[v]) for v in ch_dict[ch]]
            else: cur_nt_children=[strip_num(v) for v in ch_dict[ch]]
            non_terminal_rules.append((ch_stripped, cur_nt_children))
    return terminal_rules, non_terminal_rules

if __name__ == "__main__":
    print("treebank")
    ptb_tree_str="""( (S (NP (PRP I)) (VP (VBP 'm) (NP (NP (DT a) (JJ contemporary) (NN artist)) (PP (IN with) (NP (NP (DT a) (NN bit)) (PP (IN of) (NP (DT an) (JJ unexpected) (NN background))))))) (. .)) )"""
    ptb_tree_str="(S (CC and) (NP (PRP I) ) (VP (VBP put) (NP (NP (DT half) ) (PP (IN of) (NP (PRP it) ) ) ) (PP (IN in) (NP (DT the) (NN bank) ) ) ) )"
    new_str=' [S [CC and] [NP [PRP I]] [VP [VB put] [NP [NP [DT half]] [PP [IN of] [NP [PRP it]]] [PP [IN in] [NP [DT the] [NN bank]]]]]]'
    ptb_tree_str=new_str.replace("[","(").replace("]",")")
    tree_obj=ptb(ptb_tree_str)
    phrases=tree_obj.get_phrases()
    phrases.sort(key=lambda x:x[2])
    for ph in phrases:
        if ph[-2]-ph[-3]==0: continue
        #print ph[0],">", ph[1]
    ch_dict=tree_obj.children_dict
    gold_tree="(S (INTJ (UH Uh) )  (ADVP (RB first) )  (INTJ (UH um) )  (NP (PRP I) ) (VP (VBP need) (S (VP (TO to) (VP (VB know)  (INTJ (UH uh) )  (SBARQ (WHADVP (WRB how) ) (SQ (VBP do) (NP (PRP you) ) (VP (VB feel) (EDITED (PP (IN about) )  ) (INTJ (UH uh) )  (PP (IN about) (S (VP (VBG sending)  (INTJ (UH uh) )  (NP (DT an) (JJ elderly)  (INTJ (UH uh) )  (NN family) (NN member) ) (PP (IN to) (NP (DT a) (NN nursing) (NN home) ) ) ) ) ) ) ) ) ) ) ) )  )"
    guessed_tree="(S1 (INTJ (UH Uh) (JJ first) (S (ADVP (RB um)) (NP (PRP I)) (VP (VBP need) (S (VP (TO to) (VP (VB know) (SBARQ (INTJ (UH uh)) (WHADVP (WRB how)) (SQ (VBP do) (NP (PRP you)) (VP (VBP feel) (PP (IN about) (NP (NNP uh))) (PP (IN about) (S (VP (VBG sending) (INTJ (UH uh)))))))) (NP (DT an) (JJ elderly) (NNP uh) (NN family) (NN member)) (PP (TO to) (NP (DT a) (NN nursing) (NN home))))))))))"
#     stanford_tree="""
# (ROOT
#   (S
#     (VP (VB Uh)
#       (NP (JJ first) (NN um))
#       (SBAR
#         (S
#           (NP (PRP I))
#           (VP (VBP need)
#             (S
#               (S
#                 (VP (TO to)
#                   (VP (VB know)
#                     (INTJ (UH uh)))))
#               (SBARQ
#                 (WHADVP (WRB how))
#                 (SQ (VBP do)
#                   (NP (PRP you))
#                   (VP (VB feel)
#                     (NP
#                       (QP (RB about) (CD uh)))
#                     (PP (IN about)
#                       (S
#                         (VP (VBG sending)
#                           (NP
#                             (INTJ (UH uh))
#                             (NP (DT an) (JJ elderly) (JJ uh) (NN family) (NN member)))
#                           (PP (TO to)
#                             (NP (DT a) (NN nursing) (NN home))))))))))))))))    """
    gold_tree="(S (ADVP (RB Probably) ) (NP (DT the) (JJS hardest) (NN thing) (EDITED (PP (IN in) )  ) ) (PP (IN in) (NP (PRP$ my) (NN family) ) )  (INTJ (UH uh) )  (NP (PRP$ my) (NN grandmother) )  (NP (PRP she) ) (VP (VBD had) (S (VP (TO to) (VP (VB be) (VP (VBN put) (PP (IN in) (NP (DT a) (NN nursing) (NN home) ) ) ) ) ) ) ) )"
    guessed_tree="(S1 (FRAG (NP (NP (RB Probably) (DT the) (JJS hardest) (NN thing)) (PP (IN in) (PP (IN in) (NP (PRP$ my) (NN family))))) (INTJ (UH uh)) (NP (NP (PRP$ my) (NN grandmother)) (SBAR (S (NP (PRP she)) (VP (VBD had) (S (VP (TO to) (VP (VB be) (VP (VBN put) (PP (IN in) (NP (DT a) (NN nursing) (NN home)))))))))))))"
    gold_tree='(S (CC and)  (INTJ (UH um) )  (NP (PRP she) ) (VP (VBD had) (VP (VBN used) (NP (DT the) (NN walker) ) (EDITED (PP (IN for) )  ) (PP (IN for) (NP (NP (PDT quite) (DT some) (NN time) )  (NP (QP (ADVP (RB probably) ) (RB about) (CD six) (IN to) (CD nine) ) (NNS months) ) ) ) ) )  )'
    guessed_tree='(S1 (S (CC and) (ADVP (RB um)) (NP (PRP she)) (VP (VBD had) (VP (VBN used) (NP (DT the) (NNP walker)) (PP (IN for)) (PP (IN for) (NP (NP (RB quite) (DT some) (NN time)) (ADVP (RB probably)) (NP (QP (RB about) (CD six) (TO to) (CD nine)) (NNS months))))))))'
    gold_tree='(S (ADVP (RB probably) ) (NP (NP (CD one) ) (PP (IN of) (NP (NP (DT the) (JJS biggest) (NNS decisions) ) (PRN (S (NP (PRP I) ) (VP (VBP think) ) ) ) (SBAR (WHNP (WDT that) ) (S (VP (VBD was) (ADJP (RB very) (JJ strengthening) (PP (IN for) (NP (PRP$ our) (NN family) ) ) ) ) ) ) ) ) ) (VP (VBD was) (SBAR (SBAR (IN rather) (IN than) (S (VP (VB have) (S (NP (CD one) (NN child) ) (VP (VBP make) (NP (DT that) (NN decision) ) ) ) ) ) ) (SBAR (IN than) (ADVP (RB just) ) (S (VP (VB delegate) (NP (PRP it) ) ) ) ) ) )  )'
    guessed_tree='(S1 (NP (NP (RB probably) (CD one)) (PP (IN of) (NP (NP (DT the) (JJS biggest) (NNS decisions)) (SBAR (S (NP (PRP I)) (VP (VBP think) (SBAR (S (NP (DT that)) (VP (VBD was) (ADJP (RB very) (JJ strengthening)) (SBAR (IN for) (S (NP (PRP$ our) (NN family)) (VP (VBD was) (PP (RB rather) (IN than) (VP (VB have) (S (NP (CD one) (NN child)) (VP (VB make) (NP (DT that) (NN decision)) (SBAR (IN than) (S (ADVP (RB just)) (VP (VB delegate) (NP (PRP it))))))))))))))))))))))'

    #diff_obj=tree_diff(gold_tree,guessed_tree,[])

    tree1="(S (INTJ (UH Um) )  (ADVP (UH actually) ) (NP (PRP I) ) (VP (VBD wore) (NP (NP (NP (JJ corduroy) (NNS shorts) ) (PP (IN with) (NP (DT a) (JJ white) (NN blouse) ) ) )  (INTJ (UH um) )  (CC and) (NP (JJ flat) (NNS shoes) ) ) )  )"
    tree2="(S (INTJ (UH Um) ) (PRN  (S (NP (PRP you) ) (VP (VBP know) ) )  ) (NP (PRP I) ) (VP (VBP wear) (NP (NNS suits) ) )  )"
    tree3="(S (INTJ (UH Um) ) (PRN  (S (NP (PRP you) ) (VP (VBP know) ) )  ) (NP (EX there) ) (VP (BES 's) (EDITED (NP (JJ real) (DT no) )  ) (NP (DT no) (JJ real) (NN dress) (NN code) ) (SBAR (WHADVP (WRB where) ) (S (NP (PRP I) ) (VP (VBP work)  ) ) ) )  )"
    #tree1="(S (INTJ (UH Um) )  (NP (PRP you) ) (VP (VBP see) (NP (NP (NNS people) ) (VP (VBG wearing) (PRN  (S (NP (PRP you) ) (VP (VBP know) ) )  ) (NP (RB all) (JJ different) (NN attire) ) ) ) )  )"
    tree1="(S (VBP do)(NP (PRP you))(VP (VB know)(NP (NN anyone)(S (WDT that)(UH uh)(VBZ is)(VP (VBZ is)(PP (IN in)(NP (DT a)(NN nursing)(NN home)))(CC or)(S (VBZ has)(RB ever)(VP (VBN been)(PP (IN in)(CD one)))))))))"
    tree2="(SQ (VBP Do) (NP (PRP you) ) (VP (VB know) (NP (NP (NN anyone) ) (SBAR (WHNP (WDT that) )  (INTJ (UH uh) )  (S (EDITED (VP (VBZ is) )  ) (VP (VP (VBZ is) (PP (IN in) (NP (DT a) (NN nursing) (NN home) ) ) ) (CC or) (VP (VBZ has) (ADVP (RB ever) ) (VP (VBN been) (PP (IN in) (NP (CD one) ) ) ) ) ) ) ) ) )  )"
    tree1="(S (NP (NP (NN Somebody) ) (PP (IN in) (NP (NNP South) (NNP Carolina) ) ) ) (VP (VBD told) (NP (PRP me) ) (PP (IN about) (NP (PRP him) ) ) )  )"
    tree_obj=ptb(tree1)
    phrases=tree_obj.get_non_terminals()
    tree_obj2=ptb(tree2)
    phrases2=tree_obj2.get_non_terminals()
    phrases.sort(key=lambda x:x[-3:])
    phrases2.sort(key=lambda x:x[-3:])

    print(tree1.replace("(","[").replace(")","]"))

    for p in phrases:
        print("\t".join([str(v) for v in p]))

    # print "Converted Parse"
    # for p in phrases:
    #     if p in phrases2:
    #         print p, "<<<"
    #     else:
    #         print p, "XXX"

    # print "-------"
    # print "Original Parse"
    # for p2 in phrases2:
    #     if p2 in phrases:
    #         print p2, "<<<<"
    #     else:
    #         print p2, "XXXXXX"

    # cur_terminals=tree_obj.all_terminals
    # print([v[0] for v in cur_terminals])
    # phrases.sort(key=lambda x:x[2])
    # end_dict={}
    # for ntp in phrases:
    #     #print ntp
    #     cur_end=ntp[-2]
    #     end_dict[cur_end]=end_dict.get(cur_end,0)+1
    # ends=sorted(end_dict.keys())
    # #for e0 in ends:
    # #    print e0, cur_terminals[e0], end_dict[e0]
    # cur_tree=tree1
    # print cur_tree
    # t_rules,nt_rules=extract_rules_tree_str(cur_tree,True)
    # print ">>>> terminal rules"
    # for tr0 in t_rules:
    #     print tr0
    # print ">>>> non-terminal rules"
    # for ntr0 in nt_rules:
    #     print ntr0
    # top_tag=tree_obj.all_tag_ids[0]
    # print top_tag, tree_obj.children_dict.get(top_tag)


    #print "precision", diff_obj.precision, "recall", diff_obj.recall, "F1", diff_obj.f1
    #diff_obj=tree_diff(gold_tree,stanford_tree)
    #print "stanford precision", diff_obj.precision, "recall", diff_obj.recall, "F1", diff_obj.f1
    
    #for a in sorted(diff_obj.guessed_tree_nt_phrases,key=lambda x:(x[-2],x[-1])):
    #    print a

    #gold_tree_obj=ptb(gold_tree)
    #gold_phrases=gold_tree_obj.get_phrases()
    #gold_nt_phrases=gold_tree_obj.get_non_terminals()
    #guessed_tree_obj=ptb(guessed_tree)
    #guessed_phrases=guessed_tree_obj.get_phrases()
    #guessed_nt_phrases=guessed_tree_obj.get_non_terminals()
    #correct_counter=0
    #for gnt in gold_nt_phrases:
        #print "Gold non-termnal only", gnt
    #    pass
    #for gsnt in guessed_nt_phrases:
        #print "Guessed non-termnal only", gsnt
    #    if gsnt in gold_nt_phrases:
    #        print "Guessed CORRECT >>>>", gsnt
    #        correct_counter+=1
    #    else:
    #        print "Guessed wrong", gsnt
    #print "CORRECT", correct_counter, "out of gold_nt_phrases", len(gold_nt_phrases), "guessed_nt_phrases", len(guessed_nt_phrases)  


    #for ch in ch_dict:
    #    print( ch, ch_dict[ch], tree_obj.terminal_dict.get(ch))
    #for ph in phrases:
    #    print(ph)

