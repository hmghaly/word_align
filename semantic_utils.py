import numpy as np
from collections import defaultdict, Counter
from itertools import groupby
import random
import math, re, string
# from torch import nn
#from code_utils.general import *
#from code_utils.pandas_utils import *
#from code_utils import general
import re,json
from itertools import groupby
from collections import Counter
from random import shuffle, seed



# loss_fn = nn.CrossEntropyLoss()
# loss_fn = nn.BCELoss()
# loss_fn =nn.BCEWithLogitsLoss()
# loss_fn = nn.MSELoss()

def get_mse_loss(y_true, y_pred):
    # Calculate the difference between predictions and actual values
    differences = y_pred - y_true
    # Square the differences
    squared_differences = differences ** 2
    # Calculate the mean of the squared differences
    mse_loss_out = np.mean(squared_differences)
    return mse_loss_out


def tok_basic(txt,add_sent_tags=False): 
  txt=re.sub(r"(?u)(\W)",r" \1 ", txt)
  out=re.split(r"\s+",txt)
  tokens=[v for v in out if v]
  if add_sent_tags: tokens=["<s>"]+tokens+["</s>"]
  return tokens

def get_pair_offsets(tokens, max_offset=4): #get pairs of tokens from a sentence, with their +ve & -ve offsets
  all_pair_offset_list=[]
  for tk_i0,tk0 in enumerate(tokens):
    next_toks=tokens[tk_i0+1:tk_i0+max_offset]
    for inc0,next0 in enumerate(next_toks):
      offet0=inc0+1
      all_pair_offset_list.append((tk0,next0,offet0))
      all_pair_offset_list.append((next0,tk0,-offet0))  
  return all_pair_offset_list  

def create_one_hot_vec(hot_i,vec_size,expand_dims=False):
  zeros=[0.]*vec_size
  zeros[hot_i]=1.
  array0=np.array(zeros)
  if expand_dims: array0=np.expand_dims(array0,0)
  return array0


# Sigmoid and softmax
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

#multiply 4 matrices P(w1) x P(t1|w1) x P(t2|t1) x P(w2|t2)
#get gradients to apply to each input matrix by comparing to target output
#get also the loss, and put all these outputs in an output_dict 

def multiply4_get_grad(A,B,C,D,target_output):
  # Using the @ operator (preferred for readability)
  result_at = A @ B @ C @ D
  loss = np.mean((result_at - target_output)**2)

  # Calculate gradient of loss with respect to the final output
  d_output = 2 * (result_at - target_output) / (result_at.size)

  # Backpropagate through D
  dD = (A @ B @ C).T @ d_output

  # Backpropagate through C
  dC = (A @ B).T @ (d_output @ D.T)

  # Backpropagate through B
  dB = A.T @ (d_output @ D.T @ C.T)

  # Backpropagate through A
  dA = d_output @ D.T @ C.T @ B.T
  output_dict={"result":result_at,"grads":[dA,dB,dC,dD],"loss":loss}
  return output_dict




random.seed(0)
np.random.seed()


#27 August 2025
class shadow:
    def __init__(self,sent_list,tag_list,params={}):
        self.sent_list=sent_list
        self.tag_list=tag_list
        self.params={}
        self.add_sent_tags=self.params.get("add_sent_tags",True)
        self.max_offset=self.params.get("max_offset",4)

        self.extended_tags=["<s>","</s>"] #maybe will also include numbers and punctuation - special characters, hashtags, whatever
        if self.add_sent_tags: 
            self.tag_list+=self.extended_tags
            self.tag_list=sorted(list(set(self.tag_list)))
        self.token_counter={}
        for sent0 in self.sent_list:
            cur_tokens=tok_basic(sent0,add_sent_tags=self.add_sent_tags)
            cur_tokens_with_tags=[]
            for tk0 in cur_tokens: 
                self.token_counter[tk0]=self.token_counter.get(tk0,0)+1

        self.vocab=sorted(list(self.token_counter.keys())) 
        
        self.token2idx = {w: i for i, w in enumerate(self.vocab)}
        self.idx2token = {i: w for w, i in self.token2idx.items()}

        self.tag2idx = {w: i for i, w in enumerate(self.tag_list)}
        self.idx2tag = {i: w for w, i in self.tag2idx.items()}

        self.n_vocab=len(self.vocab)
        self.n_tags=len(self.tag_list)

        #initialize transition dict
        self.transition_dict={}
        for offset0 in range(1,self.max_offset):
          self.transition_dict[offset0]=np.random.random(size=(self.n_tags, self.n_tags))
          self.transition_dict[-offset0]=np.random.random(size=(self.n_tags, self.n_tags))
        #initialize word-tag probability dict
        self.p_w_t=np.random.random(size=(self.n_vocab, self.n_tags)) #probability of tag given word
        self.p_t_w=np.random.random(size=(self.n_tags, self.n_vocab)) #probability of tag given word

        #include the immutable matrix with ones and zeros for sent boundary tags, punc, and numbers
        self.fixed_p_w_t=np.full((self.n_vocab, self.n_tags),0.5) #(46, 9)
        self.fixed_p_t_w=np.full((self.n_tags, self.n_vocab),0.5) #(9, 46)
        all_ones=[]
        for token_i,token in enumerate(self.vocab):
          tag=None
          if token in ["<s>","</s>"]: tag=token
          elif token.isdigit(): tag="NUM"
          elif token in string.punctuation: tag="PUNC" 
          tag_i=self.tag2idx.get(tag)
          #print(token_i,token,tag,tag_i)
          if tag_i==None or tag==None: continue
          #print("applying vals","token_i",token_i,"tag_i",tag_i)
          self.fixed_p_w_t[token_i]=0
          self.fixed_p_w_t[:,tag_i]=0
          self.fixed_p_t_w[tag_i]=0
          self.fixed_p_t_w[:,token_i]=0
          all_ones.append((token_i,tag_i))
        for a,b in all_ones:
          self.fixed_p_w_t[a][b]=1.
          self.fixed_p_t_w[b][a]=1.
        #apply fixed vals to p_w_t and p_t_w
        self.apply_fixed_tags()
    def pair_offset_predict(self,pair_offset):
      pass #for a pair of words with their offset, predict the second word given the first, and given the corresponding transition matrix for this offset
      #create one-hot vectors for both words
      #get the transition matrix corresponding to this offset
      #get the p_w_t, p_t_w at this point
      #multiply matrices and get prediction outcome
      #calculate loss between prediction and one-hot vector of second word
      #apply loss/back probagation 
      #updates weights of the current offset transition matrix, and p_w_t, p_t_w

    def apply_fixed_tags(self): #tags such as <s>, PUNC .. etc, whose weights should not be updated with backpropagation
      self.p_w_t[:] = np.where(self.fixed_p_w_t == 1, 1, self.p_w_t[:])
      self.p_w_t[:] = np.where(self.fixed_p_w_t == 0, 0, self.p_w_t[:])
      self.p_t_w[:] = np.where(self.fixed_p_t_w == 1, 1, self.p_t_w[:])
      self.p_t_w[:] = np.where(self.fixed_p_t_w == 0, 0, self.p_t_w[:])

# class shadow:
#     def __init__(self,sent_list,tag_list,params={}):
#         self.sent_list=sent_list
#         self.tag_list=tag_list
#         self.params={}
#         self.add_sent_tags=self.params.get("add_sent_tags",True)
#         self.max_offset=self.params.get("max_offset",4)

#         self.extended_tags=["<s>","</s>"] #maybe will also include numbers and punctuation - special characters, hashtags, whatever
#         if self.add_sent_tags: 
#             self.tag_list+=self.extended_tags
#             self.tag_list=sorted(list(set(self.tag_list)))
#         self.available_tags=[v for v in self.tag_list if not v in self.extended_tags]
#         self.tokenized_sent_list=[]
#         self.tagged_tokens_list=[]
#         self.token_counter={}
#         self.ngram_list=[]
#         for sent0 in self.sent_list:
#             cur_tokens=tok_basic(sent0,add_sent_tags=self.add_sent_tags)
#             #print(cur_tokens)
#             cur_tokens_with_tags=[]
#             for tk0 in cur_tokens: 
#                 self.token_counter[tk0]=self.token_counter.get(tk0,0)+1
#                 assigned_tag=self.assign_tag(tk0)
#                 cur_tokens_with_tags.append((tk0,assigned_tag))
#                 self.tagged_tokens_list.append((tk0,assigned_tag))
#             for tk_i0,cur_tk0 in enumerate(cur_tokens[:-1]):
#                 next_tk0=cur_tokens[tk_i0+1]
#                 self.ngram_list.append((cur_tk0,next_tk0))

#         self.vocab=sorted(list(self.token_counter.keys())) 
        
#         self.token2idx = {w: i for i, w in enumerate(self.vocab)}
#         self.idx2token = {i: w for w, i in self.token2idx.items()}

#         self.tag2idx = {w: i for i, w in enumerate(self.tag_list)}
#         self.idx2tag = {i: w for w, i in self.tag2idx.items()}

#         self.n_vocab=len(self.vocab)
#         self.n_tags=len(self.tag_list)

#         self.calc_prob()
#         #self.train()
            
#     def assign_tag(self,token,params={}):
#         if token in ["<s>","</s>"]: tag=token
#         elif token.isdigit(): tag="NUM"
#         elif token in string.punctuation: tag="PUNC" 
#         else: tag=random.choice(self.available_tags)
#         return tag
#     def calc_prob(self): #calculate P(word|tag) , P(tag|word), P(tag2|tag1)
#         tag_pairs=[(self.tagged_tokens_list[i0][1],self.tagged_tokens_list[i0+1][1]) for i0 in range(len(self.tagged_tokens_list)-1)] #get the tag pairs from the current assignment
#         only_tags=[v[1] for v in self.tagged_tokens_list]
#         tag_counter=dict(Counter(only_tags))
#         sorted_by_word=sorted(self.tagged_tokens_list,key=lambda x:x[0])
#         sorted_by_tag=sorted(self.tagged_tokens_list,key=lambda x:x[1])
#         tag_pairs_sorted=sorted(tag_pairs,key=lambda x:x[0])
        
#         grouped_by_word=dict(iter( [(key,dict( Counter([v[1] for v in list(group)]) )  ) for key,group in groupby(sorted_by_word,lambda x:x[0])] )) 
#         grouped_by_tag=dict(iter( [(key,dict( Counter([v[0] for v in list(group)]) )  ) for key,group in groupby(sorted_by_tag,lambda x:x[1])] )) 
#         tag_pairs_grouped_by_tag=dict(iter( [(key,dict( Counter([v[1] for v in list(group)]) )  ) for key,group in groupby(tag_pairs_sorted,lambda x:x[0])] )) 

#         self.grouped_by_word=grouped_by_word
#         self.grouped_by_tag=grouped_by_tag
#         self.tag_pairs_grouped_by_tag=tag_pairs_grouped_by_tag
        

#         self.fwd_tag_transition_matrix=np.zeros((self.n_tags,self.n_tags))
#         self.p_tag_given_word_matrix=np.zeros((self.n_vocab,self.n_tags)) #check
#         self.p_word_given_tag_matrix=np.zeros((self.n_tags,self.n_vocab)) #check

#         for word0,word_tag_count0 in grouped_by_word.items():
#             word_i0=self.token2idx.get(word0)
#             word_count0=self.token_counter.get(word0)
#             if word_i0==None or word_count0==None: continue
#             #print(word0,word_i0,word_tag_count0)
#             for tag0,tag_count0 in word_tag_count0.items():
#                 tag_i0=self.tag2idx.get(tag0)
#                 if tag_i0==None: continue
#                 ratio0=tag_count0/word_count0
#                 self.p_tag_given_word_matrix[word_i0][tag_i0]=ratio0

#         for tag0,tag_word_count0 in grouped_by_tag.items():
#             tag_i0=self.tag2idx.get(tag0)
#             tag_count0=tag_counter.get(tag0)
#             if tag_i0==None or tag_count0==None: continue
#             #print(tag0,tag_i0,tag_word_count0)
#             for word0,word_count0 in tag_word_count0.items():
#                 word_i0=self.token2idx.get(word0)
#                 if word_i0==None: continue
#                 ratio0=word_count0/tag_count0
#                 self.p_word_given_tag_matrix[tag_i0][word_i0]=ratio0

#         #Now updating tag transitions
#         for tag0,tag_tag_count0 in tag_pairs_grouped_by_tag.items():
#             tag_i0=self.tag2idx.get(tag0)
#             tag_count0=tag_counter.get(tag0)
#             if tag_i0==None or tag_count0==None: continue
#             #print(tag0,tag_i0,tag_tag_count0)
#             for tag1,tag_count1 in tag_tag_count0.items():
#                 tag_i1=self.tag2idx.get(tag1)
#                 if tag_i1==None: continue
#                 ratio0=tag_count1/tag_count0
#                 self.fwd_tag_transition_matrix[tag_i0][tag_i1]=ratio0


#     def train(self,params={}):
#         all_loss=0
#         for i0 in range(len(self.tagged_tokens_list)-1):
#             item0,item1=self.tagged_tokens_list[i0],self.tagged_tokens_list[i0+1]
#             #print(f"{i0} out of {len(self.tagged_tokens_list)-1}", item0,item1)
#             token0,tag0=item0
#             token1,tag1=item1
#             token0_i,token1_i=self.token2idx.get(token0),self.token2idx.get(token1)
#             token0_oh=create_one_hot_vec(token0_i,self.n_vocab)
#             token1_oh=create_one_hot_vec(token1_i,self.n_vocab)
#             pred01=token0_oh @ self.p_tag_given_word_matrix @ self.fwd_tag_transition_matrix @ self.p_word_given_tag_matrix
#             pred01_with_tokens=[(v,round(float(w),3) ) for v,w in zip(self.vocab,pred01)]
#             pred01_with_tokens.sort(key=lambda x:-x[-1])
#             #print(pred01.shape)
#             #print(pred01_with_tokens[:5])
#             cur_loss=get_mse_loss(token1_oh,pred01)
#             #print(tag0, "cur_loss", cur_loss)
#             #chosen_new_tag=tag0

#             chosen_new_tag=self.assign_tag(token0)
#             if chosen_new_tag!=tag0:
#                 self.update_tag(i0,chosen_new_tag)
#                 self.calc_prob()
#                 temp_pred01=token0_oh @ self.p_tag_given_word_matrix @ self.fwd_tag_transition_matrix @ self.p_word_given_tag_matrix
#                 temp_loss=get_mse_loss(token1_oh,temp_pred01)
            
#                 if temp_loss<cur_loss:
#                     cur_loss=temp_loss
#                     print("New chosen tag", token0, chosen_new_tag, "cur_loss", round(cur_loss,6) , "temp_loss",round(temp_loss,6) )
#                 else:
#                     self.update_tag(i0,tag0) #return to the current tag
#                     self.calc_prob()
                
                
            

#             # if not tag0 in self.extended_tags:
#             #     for temp_tag0 in self.available_tags: #iterate over available tags for current token, to see which yields best loss
#             #         self.update_tag(i0,temp_tag0)
#             #         self.calc_prob()
#             #         temp_pred01=token0_oh @ self.p_tag_given_word_matrix @ self.fwd_tag_transition_matrix @ self.p_word_given_tag_matrix
#             #         temp_loss=get_mse_loss(token1_oh,temp_pred01)
#             #         #print(temp_tag0, temp_loss, "cur_loss",cur_loss)
#             #         if temp_loss<cur_loss:
#             #             cur_loss=temp_loss
#             #             chosen_new_tag=temp_tag0
#             #             #print(">>>>> chosen_new_tag",token0,chosen_new_tag, temp_loss)
#             #         #print("^^")
                        
#             # #print("---")
#             # if chosen_new_tag!=tag0:
#             #     self.update_tag(i0,chosen_new_tag)
#             #     self.calc_prob()
                
                
            

#             all_loss+=cur_loss
#         print("all_loss", round(all_loss,4))
#     def update_tag(self,item_i,new_tag):
#         cur_item=self.tagged_tokens_list[item_i]
#         self.tagged_tokens_list[item_i]=(cur_item[0],new_tag)
#         #print("updated", cur_item,self.tagged_tokens_list[item_i])
#     def update_word_tags(self,word,new_tag):
#         for i, cur_item in enumerate(self.tagged_tokens_list):
#             if cur_item[0].lower()==word.lower(): self.tagged_tokens_list[item_i]=(self.tagged_tokens_list[item_i][0],new_tag)
#         