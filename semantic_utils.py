import numpy as np
from collections import defaultdict, Counter
from itertools import groupby
import random
import math, re, string, os, json
# from torch import nn
#from code_utils.general import *
#from code_utils.pandas_utils import *
#from code_utils import general
#import re,json
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



#================== Utility functions

#24 September 2025
#a fast way to get a number of lines from a large file, starting at any ratio of the file content
def get_n_lines_from_file(fpath,n_lines=100, start_ratio=0):
  all_lines=[]
  fopen=open(fpath, encoding='utf-8', errors='ignore')
  f_size=os.path.getsize(fpath)
  start_loc=0
  if start_ratio>0: 
    start_loc=start_ratio*f_size
    fopen.seek(start_loc)
    fopen.readline()
  for i0 in range(n_lines):
    line0=fopen.readline()
    if line0=="": continue
    all_lines.append(line0)
  return all_lines
