#!/usr/bin/python

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import random
from string import punctuation

torch.manual_seed(1)
random.seed(1)

#device = torch.device('cuda')
device = torch.device('cpu')

#For NLP and parsing
import spacy
nlp = spacy.load("en_core_web_sm")
nlp.tokenizer=nlp.tokenizer.tokens_from_list
#print(dir(nlp.tokenizer))
def get_conll(sent_input):
  #nlp = spacy.load("en_core_web_sm")
  #if type(sent_input) is list: nlp.tokenizer=nlp.tokenizer.tokens_from_list
  doc = nlp(sent_input)
  conll_2d=[]
  for token in doc:	
    token_i = token.i+1
    if token.i==token.head.i: head_i=0
    else: head_i = token.head.i+1
    items=[token_i,token.text, token.lemma_, token.tag_, token.pos_, "_", head_i, token.dep_,"_","_"]
    conll_2d.append(items)
  return conll_2d

def get_pos_tags(sent_input):
  doc = nlp(sent_input)
  tmp_pos_tags=[]
  for token in doc: tmp_pos_tags.append(token.tag_)
  return tmp_pos_tags

#Specify the standard RNN network
class RNN(nn.Module):
  def __init__(self, input_size, hidden_size, output_size,num_layers, matching_in_out=False, batch_size=1):
    super(RNN, self).__init__()
    self.input_size = input_size
    self.output_size = output_size
    
    self.hidden_size = hidden_size
    self.num_layers = num_layers
    self.batch_size = batch_size
    self.matching_in_out = matching_in_out #length of input vector matches the length of output vector 
    
    self.lstm = nn.LSTM(input_size, hidden_size,num_layers)
    self.hidden2out = nn.Linear(hidden_size, output_size)
    self.hidden = self.init_hidden()
  def forward(self, feature_list):
    feature_list.to(device) #### <<<<<<<<<<<<<<<<< 
    if self.matching_in_out:
      # test=feature_list.view(len( feature_list), 1, -1)
      # print(test.shape)
      lstm_out, _ = self.lstm( feature_list.view(len( feature_list), 1, -1))
      output_space = self.hidden2out(lstm_out.view(len( feature_list), -1))
      output_scores = torch.sigmoid(output_space) #we'll need to check if we need this sigmoid
      return output_scores #output_scores
    else:
      for i in range(len(feature_list)):
        cur_ft_tensor=feature_list[i]#.view([1,1,self.input_size])
        cur_ft_tensor=cur_ft_tensor.view([1,1,self.input_size])
        lstm_out, self.hidden = self.lstm(cur_ft_tensor, self.hidden)
        outs=self.hidden2out(lstm_out)
      return outs
  def init_hidden(self):
    #return torch.rand(self.num_layers, self.batch_size, self.hidden_size)
    return (torch.rand(self.num_layers, self.batch_size, self.hidden_size).to(device),
            torch.rand(self.num_layers, self.batch_size, self.hidden_size).to(device))

#Now the functions needed to condition the output/labels
def one_hot(item0,list0): #e.g. item "I" in list ["B","I","O"] gives [0,1,0]
  new_list=[0.]*len(list0)
  if item0 in list0: new_list[list0.index(item0)]=1.
  return new_list

def label2tensor(output_labels0,label_scheme0): #converting a list of 1-D or 2-D labels into a vector, according to the label scheme
  output_vector=[]
  for output_element in output_labels0:
    element_vector=[]
    if type(output_element) is list or type(output_element) is tuple: #label_scheme=[["B","I","O"],["+","-"],["A","B","C","D"]]
      for se_i,sub_element in enumerate(output_element):
        sub_scheme=label_scheme0[se_i]
        one_hot_sub_element=one_hot(sub_element,sub_scheme)
        element_vector.extend(one_hot_sub_element)
        # print("sub_element",sub_element,sub_scheme,one_hot_sub_element)
    else: #label_scheme=["B","I","O"]
      element_vector=one_hot(output_element,label_scheme0)
      # print(output_element,element_vector)
    output_vector.append(element_vector)
    #print(element_vector)
  return torch.tensor(output_vector)

def tensor2label(tensor0,label_scheme0): #we will need to account for 2-d labels
  item_labels=[]
  for tns0 in tensor0:
    tmp_dict={}
    for s_i,sub_tns0 in enumerate(tns0):
      cur_label=label_scheme0[s_i]
      cur_val=sub_tns0.item()
      tmp_dict[cur_label]=cur_val
    item_labels.append(tmp_dict)    
  return item_labels

def tensor2label_OLD(tensor0,label_scheme0): #now converting a 2-d tensor into a dictionary for the labels
  item_labels=[]
  for tns0 in tensor0:
    #print(tns0)
    item_counter=0
    
    if type(label_scheme0[0]) is list or type(label_scheme0[0]) is tuple: #label_scheme=[["B","I","O"],["+","-"],["A","B","C","D"]]
      for item0 in label_scheme0:
        cur_dict={}
        for sub_item in item0:
          cur_val=tns0[item_counter].item()
          cur_dict[sub_item]=cur_val
          item_counter+=1
        item_labels.append(cur_dict)
    else: #label_scheme=["B","I","O"]
      tmp_dict={}
      for s_i,sub_tns0 in enumerate(tns0):
        cur_label=label_scheme[s_i]
        cur_val=sub_tns0.item()
        tmp_dict[cur_label]=cur_val
        item_labels.append(tmp_dict)
            
      # cur_dict={}
      # for item0 in label_scheme0:
      #   cur_val=tns0[item_counter].item()
      #   cur_dict[item0]=cur_val
      #   item_counter+=1
      #   item_labels.append(cur_dict)
    return item_labels

#Extract word features
def get_word_features(word0,word_vector_model,add_len_vec=True,add_caps_vec=True,
                      add_punct_vec=True,add_num_vec=True, vector_size=300):
  try: vec=list(wv_model[word0.lower()]) #word vectors from the model
  except: vec=[0.]*vector_size 

  final_vector=vec

  if add_len_vec:
    w_len_vec=[0.]*5  #word length vector, five slots, if length >= 5, last slot=1
    if len(word0)>=5: w_len_vec[4]=1.
    else: w_len_vec[len(word0)-1]=1.
    final_vector+=w_len_vec
  if add_caps_vec:
    caps_vector=[0.,0.] #if the first character and last character are uppercase
    if word0[0].isupper(): caps_vector[0]=1.
    if word0[-1].isupper(): caps_vector[1]=1.
    final_vector+=caps_vector
  if add_punct_vec:
    punct_vector=[0.] #if the word is a punctuation
    if word0 in punctuation: punct_vector=[1.]
    final_vector+=punct_vector
  if add_num_vec:
    num_vector=[0.,0.,0.] #if the first and last character are digits
    if word0[0].isdigit(): num_vector[0]=1.
    if word0[-1].isdigit(): num_vector[1]=1.
    if word0.isdigit(): num_vector[2]=1.
    final_vector+=num_vector
  return final_vector 
pos_letter_list="BCDIHJLMNPRSTVW.,-:"
def get_sent_features(word_list0,word_vector_model,pos_list0=[] ,add_pos_vec=True,add_len_vec=True,add_caps_vec=True,
                      add_punct_vec=True,add_num_vec=True, vector_size=300):
  sent_vector_list=[]
  if add_pos_vec:
    if pos_list0==[]: 
      tmp_conll_list=get_conll(word_list0)
      tmp_pos_list=[v[3] for v in tmp_conll_list]
    else: tmp_pos_list=pos_list0
    
  for wi,word1 in enumerate(word_list0):
    cur_vec=get_word_features(word1,word_vector_model,add_len_vec,add_caps_vec,
                      add_punct_vec,add_num_vec, vector_size)
    
    if add_pos_vec:
      #cur_conll_item=tmp_conll_list[wi]
      #pos_letter=cur_conll_item[3][0]
      cur_pos_item=tmp_pos_list[wi]
      pos_letter=cur_pos_item[0]
      pos_vec=one_hot(pos_letter,pos_letter_list)
      cur_vec+=pos_vec
      #print(word1, cur_conll_item[3], pos_letter, pos_vec)

    sent_vector_list.append(cur_vec)
  return torch.tensor(sent_vector_list) 


if __name__=="__main__":
  sent="I asked them but I do not know what he did in the big palace very easily".decode("utf-8")
  # out=get_conll(sent.split())
  # pos_list=[]
  # for o1 in out:
  #   pos_list.append(o1[3][0])
  #   #print(o1[3])
  # pos_list=sorted(list(set(pos_list)))
  # print("".join(pos_list))
  out_features=get_sent_features(sent.split(),{})

  #print(out)
  # label_scheme=["B","I","O"]
  # output_labels=["O","O","B","I","O","O","B","O"]

  # label_scheme=[["B","I","O"],["+","-"],["A","B","C","D"]]
  # output_labels=[["B","+","A"],
  #               ["I","-","C"],
  #               ["B","+","D"],
  #               ["O","-","C"],
  #               ["O","-","B"]]
  # out_tensor=label2tensor(output_labels,label_scheme)
  # #print(out_tensor.shape)
  # out1=tensor2label(out_tensor,label_scheme)
  # #print(out1)
  # #t=[0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0]
  # label_scheme_simple=["B","I","O"]
  # output_labels_simple=[[0.,1.,0.],[1.,0.,0.],[0.5,0.9,1.]]
  # output_labels_simple_tensor=torch.tensor(output_labels_)
  # out2=tensor2label(output_labels_simple_tensor,label_scheme_simple)
  # #print(out2)               