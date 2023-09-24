import random
import dill as pickle
from collections import OrderedDict
import numpy as np
import os,json, copy, sys, time, random

import gensim
from gensim.models import Word2Vec

sys.path.append("code_utils")
import cat_utils
import general



try:
  import torch
  from torch import nn
  import torch.optim as optim
  torch.manual_seed(1)
  device = torch.device('cpu')
except:
  pass
  # class nn_cls:
  #   def __init__(self):
  #     pass
  #   def Module(self,n1,n2):
  #     return n1,n2
  # nn=nn_cls()

random.seed(1)

try: #to avoid environments without torch installation
  class RNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size,num_layers, matching_in_out=False, apply_sigmoid=False, apply_softmax=False, init_val=None, batch_size=1):
      super(RNN, self).__init__()
      self.input_size = input_size
      self.hidden_size = hidden_size
      self.output_size = output_size
      self.num_layers = num_layers
      self.batch_size = batch_size
      self.apply_softmax=apply_softmax
      self.apply_sigmoid=apply_sigmoid
      self.init_val=init_val
      self.matching_in_out = matching_in_out #length of input vector matches the length of output vector 
      self.lstm = nn.LSTM(input_size, hidden_size,num_layers)
      self.hidden2out = nn.Linear(hidden_size, output_size)
      if self.apply_softmax: self.softmax =nn.Softmax(dim=2)
      if self.apply_sigmoid: self.sigmoid =nn.Sigmoid() 
      
      #self.sigmoid = torch.sigmoid(dim=1)
      self.hidden = self.init_hidden()
    def forward(self, feature_list):
      self.hidden = self.init_hidden() ### check
      feature_list=torch.tensor(feature_list)
      feature_list=feature_list.to(device) #### <<<<<<<<<<<<<<<<< 
      if self.matching_in_out:
        lstm_out, _ = self.lstm( feature_list.view(len( feature_list), 1, -1))
        output_scores = self.hidden2out(lstm_out.view(len( feature_list), -1))
        if self.apply_sigmoid: output_scores=self.sigmoid(output_scores).to(device)
        elif self.apply_softmax: output_scores=self.softmax(output_scores).to(device)
        #output_scores = torch.sigmoid(output_space) #we'll need to check if we need this sigmoid
        return output_scores #output_scores
      else:
        outs=[]
        for i in range(len(feature_list)):
          cur_ft_tensor=feature_list[i]#.view([1,1,self.input_size])
          cur_ft_tensor=cur_ft_tensor.view([1,1,self.input_size])
          lstm_out, self.hidden = self.lstm(cur_ft_tensor, self.hidden)
          outs=self.hidden2out(lstm_out)
          if self.apply_sigmoid: outs = self.sigmoid(outs).to(device) #self.sigmoid =nn.Sigmoid()
          elif self.apply_softmax: outs = self.softmax(outs).to(device)
          
        return outs
    def init_hidden(self):
      #return torch.rand(self.num_layers, self.batch_size, self.hidden_size)
      if self.init_val!=None:
        h1=torch.ones(self.num_layers, self.batch_size, self.hidden_size)*self.init_val
        h2=torch.ones(self.num_layers, self.batch_size, self.hidden_size)*self.init_val
      else:
        h1=torch.rand(self.num_layers, self.batch_size, self.hidden_size)
        h2=torch.rand(self.num_layers, self.batch_size, self.hidden_size)
      return (h1.to(device),h2.to(device))
except:
  pass

def to_tensor(list1):
  return torch.tensor(list1,dtype=torch.float32)


import dill as pickle
import types

def dill_pickle(obj0,fpath0):
  pickle_fopen=open(fpath0,"wb")
  pickle.settings['recurse'] = True
  pickle.dump(obj0,pickle_fopen)
  pickle_fopen.close()

def dill_unpickle(fpath0):
  pickle_fopen0=open(fpath0,"rb")
  tmp_dict=pickle.load(pickle_fopen0)
  pickle_fopen0.close()
  return tmp_dict

def log_something(text0,fpath0):
  fopen0=open(fpath0,"a")
  fopen0.write(text0+"\n")
  fopen0.close()

def split_train_test(all_data0,train_ratio=0.8):
  train_size=int(len(all_data0)*train_ratio)
  train_set0,tes_set0=all_data0[:train_size],all_data0[train_size:]
  return train_set0,tes_set0  

def out2labels(rnn_flat_out,label_list): #a flat rnn output to split into slices, and get the label weights for each slice
  final_list=[]
  n_slices=int(len(rnn_flat_out)/len(label_list))
  for i0 in range(n_slices):
    i1=i0+1
    cur_slice=rnn_flat_out[i0*len(label_list):i1*len(label_list)]
    tmp_list=[]
    for lb0,cs0 in zip(label_list,cur_slice): tmp_list.append((lb0,cs0))
    tmp_list.sort(key=lambda x:-x[-1])
    final_list.append(tmp_list)
  return final_list


def binary_list2one_hot(list1,possible_labels1):
  one_hot_list=[1. if v in list1 else 0. for v in possible_labels1]
  return one_hot_list  

def eval_function(flat_rnn_out0,standard_labels0,cur_labels0):
  list_offsets=[]
  rnn_labels_list=[]
  for i0,rnn_val0 in enumerate(flat_rnn_out0):
    rnn_corr_label=standard_labels0[i0]
    rnn_labels_list.append((rnn_corr_label,rnn_val0))
  rnn_labels_list.sort(key=lambda x:-x[-1])
  for i0,rnn_val_label0 in enumerate(rnn_labels_list):
    rnn_corr_label,rnn_val0=rnn_val_label0
    cur_offset=max(0,i0-len(cur_labels0)+1)
    if rnn_corr_label in cur_labels0: list_offsets.append(cur_offset)
    if len(list_offsets)==len(cur_labels0): break
  return sum(list_offsets)/len(list_offsets)

def copy_func(f, name=None): #to copy the function definition to store the correct feature extraction function in the checkpoint
  return types.FunctionType(f.__code__, f.__globals__, name or f.__name__,
        f.__defaults__, f.__closure__)
  

def load_model_dill(model_fpath0):
  checkpoint = dill_unpickle(model_fpath0)
  rnn0 = RNN(checkpoint["n_input"], checkpoint["n_hidden"] , checkpoint["n_output"] , checkpoint["n_layers"] , matching_in_out=checkpoint["n_layers"]).to(device)
  rnn0.load_state_dict(checkpoint['model_state_dict'])
  rnn0.eval()
  return rnn0

def load_model(model_fpath0):
  checkpoint = torch.load(model_fpath0)
  rnn0 = RNN(checkpoint["n_input"], checkpoint["n_hidden"] , checkpoint["n_output"] , checkpoint["n_layers"] , matching_in_out=checkpoint["n_layers"]).to(device)
  rnn0.load_state_dict(checkpoint['model_state_dict'])
  rnn0.eval()
  return rnn0
def get_chk_labels(model_fpath0):
  checkpoint = torch.load(model_fpath0)
  return checkpoint["output_labels"]

def load_model_labels(model_fpath0): #load the model + expected output labels
  checkpoint = torch.load(model_fpath0)
  rnn0 = RNN(checkpoint["n_input"], checkpoint["n_hidden"] , checkpoint["n_output"] , checkpoint["n_layers"] , matching_in_out=checkpoint["n_layers"]).to(device)
  rnn0.load_state_dict(checkpoint['model_state_dict'])
  rnn0.eval()
  labels=checkpoint["output_labels"]
  return rnn0,labels

def chk2pickle(chk_pt_fpath0,new_pickle_path0,skip_function=False,skip_optimizer=True, skip_eval=True,skip_label=True): #convert torch checkpoint to pickle, and convert tensors to numpy arrays - to work independently from torch
  pickle_dict0={}
  try: checkpoint_dict = torch.load(chk_pt_fpath0)
  except: checkpoint_dict = dill_unpickle(chk_pt_fpath0)
  for a,b in checkpoint_dict.items():
    #print(a,type(b))
    if skip_optimizer and a.lower()=="optimizer_state_dict": continue
    if skip_eval and a.lower()=="eval_function": continue
    if skip_label and a.lower()=="label_extraction_function": continue
    if skip_function and "function" in a.lower(): continue
    if "state_dict" in a.lower():
      new_od0=OrderedDict()
      for a1,b1 in b.items():
        #print(a1,type(b1))
        new_od0[a1]=np.array(b1)
      pickle_dict0[a]=new_od0
    else:
      pickle_dict0[a]=b
  pickle_fopen = open(new_pickle_path0, 'wb')
  pickle.dump(pickle_dict0,pickle_fopen)
  pickle_fopen.close()


def state_dict2np(state_dict0):
  new_od0=OrderedDict()
  for a1,b1 in state_dict0.items():
    new_od0[a1]=np.array(b1)
  return new_od0


def get_rnn_result_dict(rnn_out0,standard_labels0):
  flat_rnn_out0=rnn_out0.ravel()
  res_dict0={}
  for i0,rnn_val0 in enumerate(flat_rnn_out0):
    corr_label=standard_labels0[i0]
    res_dict0[corr_label]=rnn_val0.item()
  return res_dict0

def get_phoneme_wt(res_dict0,cur_word_phones0=[]):
  #res_dict1=get_result_dict(rnn_out0,standard_labels0)
  word_wts=[]
  for cwp in cur_word_phones0: word_wts.append((cwp,round(res_dict0.get(cwp,0),4)))
  return word_wts

def identify_wav(fpath0,rnn_obj0,params0,standard_labels0,word_list0=[],ph_pair0=[]):
  times1,ft1=extract_audio_features(fpath0,params0)
  feature_tensor=torch.tensor(ft1,dtype=torch.float32)
  rnn_out=rnn_obj0(feature_tensor)
  res_dict=get_result_dict(rnn_out,standard_labels0)
  ipa_pair1=[arpabet2ipa(v) for v in ph_pair0]
  pair_wt_list=[]
  for ip0 in ipa_pair1: pair_wt_list.append((ip0,round(res_dict.get(ip0,0),4)))
  word_eval_list=[]
  for word1 in word_list0:
    word_ipa1=word2ipa(word1)
    out1=get_phoneme_wt(res_dict,word_ipa1)
    avg_out1=sum([v[1] for v in out1])/len(out1)
    word_eval_list.append((word1,out1, round(avg_out1,4)))
  word_eval_list.sort(key=lambda x:-x[-1])
  out_dict={}
  out_dict["words"]=word_eval_list
  out_dict["pairs"]=pair_wt_list
  return out_dict  


def check_pred_pair(ipa_pair0,preds0,correct0=None): #we want to check the predictions from rnn output for the weight of a pair of ipa phonemes
  res_dict0={}
  if len(preds0)==1: res_dict0=preds0[0]
  pair_wt_list0=[]
  for ip0 in ipa_pair0: pair_wt_list0.append((ip0,round(res_dict0.get(ip0,0),4)))  
  max_wt0=max([v[1] for v in pair_wt_list0])
  if correct0!=None:
    new_pair_wt_list0=[]
    for ph0,ph_wt0 in pair_wt_list0:
      is_correct=False
      if ph_wt0==max_wt0 and ph0==correct0: is_correct=True
      new_pair_wt_list0.append((ph0,ph_wt0,is_correct))
    pair_wt_list0=new_pair_wt_list0
    
    
  #pair_wt_list0.sort(key=lambda x:-x[-1])
  return pair_wt_list0

def check_pred_words(ipa_words0,preds0): #check the prediction weights for several words based on their ipa phonemes
  res_dict0={}
  if len(preds0)==1: res_dict0=preds0[0]  
  final_list=[]
  for ipa_wd0 in ipa_words0:
    cur_ph_wts0=[]
    cur_ph_dict0={}
    for ph0 in ipa_wd0: 
      ph_wt0=round(res_dict0.get(ph0,0),4)
      cur_ph_wts0.append((ph0,ph_wt0)) #cur_ph_dict0[ph0]=res_dict0.get(ph0,0)
    final_list.append(cur_ph_wts0)
  return final_list

#================ numpy RNN implementation
import numpy as np

def sigmoid(x): 
    return 1. / (1 + np.exp(-x))
def softmax(x):
    e_x = np.exp(x - np.max(x)) # max(x) subtracted for numerical stability
    return e_x / np.sum(e_x)

def get_model_n_params(nn_model_obj):
  return sum(p.numel() for p in nn_model_obj.model.parameters() if p.requires_grad)

def get_params(state_dict0): #get network parameters from state dict/understand network architecture from state dict
  params={}
  all_layers=[]
  for a,b in state_dict0.items():
    cur_shape=b.shape
    a0=a.split(".")[-1]
    if a0=="weight_ih_l0": 
      params["n_hidden"],params["n_input"]=int(cur_shape[0]/4),cur_shape[1]
    last_a=a0.split("_")[-1]
    if last_a.startswith("l") and not last_a in all_layers: all_layers.append(last_a)
    if a0== "weight": params["fc_weight"]=b
    if a0== "bias": 
      params["fc_bias"]=b
      params["n_output"]=cur_shape[0]
  params["n_layers"]=len(all_layers)
  return params

class np_lstm:
  def __init__(self,state_dict0, matching_in_out0=False,apply_sigmoid=False,apply_softmax=False) -> None:
    self.cur_params=get_params(state_dict0)
    self.matching_in_out=matching_in_out0
    self.apply_sigmoid=apply_sigmoid
    self.apply_softmax=apply_softmax
    self.n_hidden=self.cur_params["n_hidden"]
    self.n_layers=self.cur_params["n_layers"]
    self.fc_wt,self.fc_bias=self.cur_params["fc_weight"],self.cur_params["fc_bias"] #fully connected
    new_stat_dict={}
    for a,b in state_dict0.items(): #just to handle whether th state dict has torch tensors or numpy arrays
      try: new_stat_dict[a]=b.numpy() #if torch tensors, convert to numpy
      except: new_stat_dict[a]=b #otherwise, keep it
    self.state_dict0=new_stat_dict

  def forward(self,data_input):
    n_hidden=self.n_hidden
    n_layers=self.n_layers
    state_dict0=self.state_dict0
    for layer_i in range(n_layers):
      layer="l%s"%layer_i
      #Event (x) Weights and Biases for all gates
      Weights_xi = state_dict0['lstm.weight_ih_'+layer][0:n_hidden]  # shape  [h, x]
      Weights_xf = state_dict0['lstm.weight_ih_'+layer][n_hidden:2*n_hidden]  # shape  [h, x]
      Weights_xl = state_dict0['lstm.weight_ih_'+layer][2*n_hidden:3*n_hidden]  # shape  [h, x]
      Weights_xo = state_dict0['lstm.weight_ih_'+layer][3*n_hidden:4*n_hidden] # shape  [h, x]

      Bias_xi = state_dict0['lstm.bias_ih_'+layer][0:n_hidden]  #shape is [h, 1]
      Bias_xf = state_dict0['lstm.bias_ih_'+layer][n_hidden:2*n_hidden]  #shape is [h, 1]
      Bias_xl = state_dict0['lstm.bias_ih_'+layer][2*n_hidden:3*n_hidden]  #shape is [h, 1]
      Bias_xo = state_dict0['lstm.bias_ih_'+layer][3*n_hidden:4*n_hidden] #shape is [h, 1]

      #Hidden state (h) Weights and Biases for all gates
      Weights_hi = state_dict0['lstm.weight_hh_'+layer][0:n_hidden]  #shape is [h, h]
      Weights_hf = state_dict0['lstm.weight_hh_'+layer][n_hidden:2*n_hidden]  #shape is [h, h]
      Weights_hl = state_dict0['lstm.weight_hh_'+layer][2*n_hidden:3*n_hidden]  #shape is [h, h]
      Weights_ho = state_dict0['lstm.weight_hh_'+layer][3*n_hidden:4*n_hidden] #shape is [h, h]

      Bias_hi = state_dict0['lstm.bias_hh_'+layer][0:n_hidden]  #shape is [h, 1]
      Bias_hf = state_dict0['lstm.bias_hh_'+layer][n_hidden:2*n_hidden]  #shape is [h, 1]
      Bias_hl = state_dict0['lstm.bias_hh_'+layer][2*n_hidden:3*n_hidden]  #shape is [h, 1]
      Bias_ho = state_dict0['lstm.bias_hh_'+layer][3*n_hidden:4*n_hidden] #shape is [h, 1]

      #Initialize cell and hidden states with zeroes
      h = np.zeros(n_hidden)
      c = np.zeros(n_hidden)

      #Loop through data, updating the hidden and cell states after each pass
      out_list=[]
      all_output=[]
      for eventx in data_input:
        f = forget_gate(eventx, h, Weights_hf, Bias_hf, Weights_xf, Bias_xf, c)
        i =  input_gate(eventx, h, Weights_hi, Bias_hi, Weights_xi, Bias_xi, 
                      Weights_hl, Bias_hl, Weights_xl, Bias_xl)
        c = cell_state(f,i)
        h = output_gate(eventx, h, Weights_ho, Bias_ho, Weights_xo, Bias_xo, c)
        out_list.append(h)
      data_input=np.array(out_list)
    if self.matching_in_out:lstm_out=data_input
    else: lstm_out=np.array(h)
    if self.matching_in_out:
      all_output=[]
      for lstm_item in lstm_out:
        cur_output=np.dot(self.fc_wt, lstm_item) + self.fc_bias
        all_output.append(cur_output)
      res=np.array(all_output)
    else:
      cur_output=np.dot(self.fc_wt, lstm_out) + self.fc_bias
      res=np.array(cur_output)
    if self.apply_sigmoid: res=sigmoid(res)
    if self.apply_softmax: res=softmax(res)
    return res 


def forget_gate(x, h, Weights_hf, Bias_hf, Weights_xf, Bias_xf, prev_cell_state):
    forget_hidden  = np.dot(Weights_hf, h) + Bias_hf
    forget_eventx  = np.dot(Weights_xf, x) + Bias_xf
    return np.multiply( sigmoid(forget_hidden + forget_eventx), prev_cell_state )

def input_gate(x, h, Weights_hi, Bias_hi, Weights_xi, Bias_xi, Weights_hl, Bias_hl, Weights_xl, Bias_xl):
    ignore_hidden  = np.dot(Weights_hi, h) + Bias_hi
    ignore_eventx  = np.dot(Weights_xi, x) + Bias_xi
    learn_hidden   = np.dot(Weights_hl, h) + Bias_hl
    learn_eventx   = np.dot(Weights_xl, x) + Bias_xl
    return np.multiply( sigmoid(ignore_eventx + ignore_hidden), np.tanh(learn_eventx + learn_hidden) )


def cell_state(forget_gate_output, input_gate_output):
    return forget_gate_output + input_gate_output

  
def output_gate(x, h, Weights_ho, Bias_ho, Weights_xo, Bias_xo, cell_state):
    out_hidden = np.dot(Weights_ho, h) + Bias_ho
    out_eventx = np.dot(Weights_xo, x) + Bias_xo
    return np.multiply( sigmoid(out_eventx + out_hidden), np.tanh(cell_state) )


#============= Prediction class
class model_pred:
  def __init__(self,model_fpath0) -> None:
    self.checkpoint = dill_unpickle(model_fpath0)
    self.n_input=self.checkpoint["n_input"]
    self.n_hidden=self.checkpoint["n_hidden"]
    self.n_output=self.checkpoint["n_output"]
    self.n_layers=self.checkpoint["n_layers"]
    self.matching_in_out=self.checkpoint.get("matching_in_out",False)
    self.apply_sigmoid=self.checkpoint.get("apply_sigmoid",False)
    self.apply_softmax=self.checkpoint.get("apply_softmax",False)

    self.feature_extraction_fn=self.checkpoint.get("feature_extraction_function")
    self.feature_extraction_params=self.checkpoint.get("feature_extraction_parameters")
    self.standard_labels=self.checkpoint.get('output_labels')
    if self.standard_labels==None: self.standard_labels=self.checkpoint.get('standard-labels')#params["standard-labels"]
    self.model_state_dict=self.checkpoint['model_state_dict']
    self.use_torch=False
    self.np_lstm_obj=None

    try:
      self.rnn = RNN(self.n_input, self.n_hidden , self.n_output , self.n_layers , matching_in_out=self.matching_in_out,apply_sigmoid=self.apply_sigmoid,apply_softmax=self.apply_softmax).to(device)
      self.rnn.load_state_dict(self.model_state_dict)
      self.rnn.eval()
      self.use_torch=True
    except Exception as ex:
      self.np_lstm_obj=np_lstm(self.model_state_dict, self.matching_in_out,self.apply_sigmoid,self.apply_softmax)
  def inspect(self):
    for k,v in self.checkpoint.items():
      if "dict" in k: continue
      if "function" in k: continue
      print(k,v)

  def predict(self,item_fpath,cur_feature_extraction_fn=None,cur_feature_extraction_params=None,time_seq=True,cur_use_torch=True): #time sequence - whether the feature extraction function yields times corresponding to features
    #if self.feature_extraction_fn==None: self.feature_extraction_fn=feature_extraction_fn
    if cur_feature_extraction_fn!=None: self.feature_extraction_fn=cur_feature_extraction_fn
    if cur_feature_extraction_params!=None: self.feature_extraction_params=cur_feature_extraction_params
    if cur_use_torch==False:  self.use_torch=False
    else: self.use_torch=True
    if time_seq: times,ft_vector=self.feature_extraction_fn(item_fpath,self.feature_extraction_params)
    else:  ft_vector=self.feature_extraction_fn(item_fpath,self.feature_extraction_params)
    if self.use_torch:
      ft_tensor=torch.tensor(ft_vector,dtype=torch.float32)
      rnn_out= self.rnn(ft_tensor)
      rnn_out_flat=rnn_out.ravel()
      rnn_out_flat=[v.item() for v in rnn_out_flat]
    else:
      if self.np_lstm_obj==None:
        self.np_lstm_obj=np_lstm(self.model_state_dict, self.matching_in_out,self.apply_sigmoid,self.apply_softmax)
      rnn_out=self.np_lstm_obj.forward(ft_vector)
      rnn_out_flat=rnn_out.ravel()
    preds0=out2labels(rnn_out_flat,self.standard_labels) 
    all_pred_dicts=[]
    for pr0 in preds0:
    	cur_dict0=dict(iter(pr0))
    	all_pred_dicts.append(cur_dict0)
    return all_pred_dicts  

#=========================================== New pipeline and loading =========================
def seq_nn(n_input,n_hidden,n_out,n_layers):
  model0 = nn.Sequential(
      nn.Linear(n_input, n_hidden),
      nn.ReLU(),
      nn.Linear(n_hidden, int(n_hidden/2)),
      nn.ReLU(),
      nn.Linear(int(n_hidden/2), n_out),
      nn.Sigmoid()
  )
  return model0


def analyze_binary_output(actual_list,pred_list,analysis_list): #compare items of predicted and actual lists, to analyze recall and precision .. etc
  for i0,cur_actual0 in enumerate(actual_list):
    cur_pred=pred_list[i0]
    cur_pred_rounded=round(cur_pred)
    is_correct=cur_pred_rounded==cur_actual0
    cur_item_dict=analysis_list[i0]
    temp_item_val_dict=cur_item_dict.get(cur_actual0,{})
    temp_item_val_dict[is_correct]=temp_item_val_dict.get(is_correct,0)+1
    cur_item_dict[cur_actual0]=temp_item_val_dict
    analysis_list[i0]=cur_item_dict
  return analysis_list

def get_accuracy_analysis(analyis_list0): #analyze the output of analyze_binary_output, for accuracy: [{0: {True: 9546, False: 9}, 1: {False: 106, True: 339}}]
  analyis_list0.sort()
  new_list=[]
  for temp_dict0 in analyis_list0:
    cur_items=list(temp_dict0.items())
    new_items_dict={}
    for a,b_dict in cur_items:
      cur_accuracy=b_dict.get(True,0)/sum(b_dict.values())
      b_dict["accuracy"]=round(cur_accuracy,2)
      new_items_dict[a]=b_dict
    new_list.append(new_items_dict)
  return new_list



# def training_pipeline(nn_class,data_fpath,params,feature_ex_params,loss_criterion):
#   n_input0=params["n_input"]#=n_input #np.array(cur_vec).shape[-1] #cur_wv_model.vector_size #np.array(first_item[1]).shape[-1]
#   n_output0=params["n_output"] #1 #np.array(cur_vec).shape[-1] #np.array(first_item[2]).shape[-1]
#   n_hidden0=params["n_hidden"]
#   n_layers0=params.get("n_layers",1)
#   LR=params.get("LR",0.0001)
#   n_epochs0=params.get("n_epochs",100)
#   batch_size0=params.get("batch_size",1000)
#   exp_name0=params.get("exp_name","exp")
#   matching_in_out0=params.get("matching_in_out",False)
#   is_rnn0=params.get("is_rnn",False)

#   train_ratio0=params.get("train_ratio",0.8)
#   ft_lb_extraction_fn=params.get("ft_lb_extraction_fn")
#   #ft_lb_extraction_params=params.get("ft_lb_extraction_params",{})
#   data_ratio=params.get("data_ratio") #the ration of the data we should use from data file
#   #data_gen=read_file_from_to(data_fpath,to_ratio=0.0001)

#   optimizer_name=params.get("optimizer","sgd") #
#   model_dir=params.get("model_dir","models")
#   main_params_items=[exp_name0,data_ratio,n_input0,n_output0,n_hidden0,n_layers0,LR,batch_size0]
#   main_params_items_str="-".join([str(v) for v in main_params_items])
#   model_name=params.get("model_name","model-%s.model"%main_params_items_str)
#   if not os.path.exists(model_dir): os.makedirs(model_dir)
#   model_fpath=os.path.join(model_dir,model_name)
#   print(model_fpath)

#   log_fpath=os.path.join(model_fpath+".txt")
#   log_something(model_fpath,log_fpath)

#   feature_ex_params_copy=copy.deepcopy(feature_ex_params) #remove the model object from parameters to easily log
#   feature_ex_params_copy.pop('wv_model', None)
#   log_something(str(feature_ex_params_copy),log_fpath)




#   model = nn_class(n_input0, n_hidden0, n_output0,n_layers0).to(device)  # 2 represents two neurons in one hidden layer
#   if optimizer_name=="sgd": optimizer = torch.optim.SGD(model.parameters(), lr=LR)#.to(device)
#   elif optimizer_name=="adam": optimizer = torch.optim.Adam(model.parameters(), lr=LR)#.to(device)
#   else: optimizer = torch.optim.Adam(model.parameters(), lr=LR)#.to(device)

#   print(model)
#   log_something(str(model),log_fpath)


#   #model_fname="output/one_layer_vec3_FULL.model"
#   training_progress_list=[]
#   best_dev_loss=1
#   last_epoch=None
#   last_batch_i=None

#   train_counter,dev_counter=0,0
#   train_loss_total,dev_loss_total=0,0

#   model_data_dict={}

#   model_data_dict["params"]=params
#   model_data_dict["feature_params"]=feature_ex_params_copy
#   model_data_dict["network_def"]=nn_class #check
#   model_data_dict["ft_lb_extraction_fn"]=ft_lb_extraction_fn

  



#   if os.path.exists(model_fpath):
#     temp_line=f"found model: {model_fpath}"
#     print(temp_line)
#     #print("found model:",model_fpath)
#     log_something(temp_line,log_fpath)
#     model_data_dict=torch.load(model_fpath)
#     training_progress_list=model_data_dict.get("training_progress_list",[])
#     best_dev_loss=model_data_dict.get("best_dev_loss",1)
#     temp_line=f"best_dev_loss: {best_dev_loss}"
#     print(temp_line)
#     log_something(temp_line,log_fpath)

#     last_epoch=model_data_dict.get("last_epoch")
#     last_batch_i=model_data_dict.get("last_batch_i")
#     latest_state_dict=model_data_dict.get("latest_state_dict",{})
#     top_state_dict=model_data_dict.get("state_dict",{})
    
#     if latest_state_dict=={}: 
#       cur_state_dict=top_state_dict
#       print("loaded top model")
#     else: 
#       cur_state_dict=latest_state_dict
#       print("loaded latest model")
#     #cur_state_dict=model_data_dict.get("state_dict",{})
#     model.load_state_dict(cur_state_dict)
#     model.train()




#   for epoch in range(n_epochs0):
#     epoch_train_counter,epoch_dev_counter=0,0
#     epoch_train_loss_total,epoch_dev_loss_total=0,0
#     train_analysis_list=[{}]*n_output0
    
#     model.zero_grad()

#     if last_epoch!=None and epoch<=last_epoch: 
#       print(f"epoch already used {epoch}- last_epoch: {last_epoch}")
#       continue

#     epoch_train_counter=model_data_dict.get("epoch_train_counter",0)
#     epoch_dev_counter=model_data_dict.get("epoch_dev_counter",0)
#     epoch_train_loss_total=model_data_dict.get("epoch_train_loss_total",0)
#     epoch_dev_loss_total=model_data_dict.get("epoch_dev_loss_total",0)

#     if data_ratio!=None: data_iterator=general.read_file_from_to(data_fpath,to_ratio=data_ratio)
#     else: data_iterator=general.read_file_from_to(data_fpath)
#     batch_iterator=general.get_iter_chunks(data_iterator, chunk_size=batch_size0,min_i=last_batch_i)
#     for batch_i, cur_batch in enumerate(batch_iterator):
#       last_batch_i=model_data_dict.get("last_batch_i")
#       if last_batch_i!=None and batch_i<=last_batch_i:
#         #print(f"batch already used {batch_i}- last_batch_i: {last_batch_i}")
#         continue
#       #print("batch_i",batch_i, "cur_batch",len(cur_batch))
#       t0=time.time()
#       cur_batch_items=[]
#       for item_str in cur_batch:
#         cur_raw_ft_dict=json.loads(item_str)
#         if cur_raw_ft_dict["src"]==cur_raw_ft_dict["trg"]: continue
#         if cur_raw_ft_dict["src"]=='<s> </s>': continue
#         if cur_raw_ft_dict["trg"]=='<s> </s>': continue
#         try: cur_ft,cur_lb=ft_lb_extraction_fn(cur_raw_ft_dict,params=feature_ex_params)
#         except: continue
#         # if cur_lb==0: cur_lb=0.5
#         # elif cur_lb==-1: cur_lb=0
#         cur_batch_items.append((cur_raw_ft_dict,cur_ft,cur_lb))
#       train_size=int(len(cur_batch_items)*train_ratio0)
#       train_data=cur_batch_items[:train_size]
#       dev_data=cur_batch_items[train_size:]
#       t1=time.time()
#       elapsed=t1-t0
#       temp_line=f"feature extraction: elapsed: {round(elapsed,2)} - train_data: {len(train_data)} - dev data: {len(dev_data)}"

#       batch_train_counter,batch_dev_counter=0,0
#       batch_train_loss_total,batch_dev_loss_total=0,0
#       #print("train_data",len(train_data),"dev_data",len(dev_data))
#       dev_analysis_list=[{}]*n_output0

#       for train_i,train_item in enumerate(train_data):
#         raw0,ft_vec0,lb0=train_item
#         input_tensor=to_tensor(ft_vec0).to(device)
#         output_tensor=to_tensor([lb0]).to(device)
#         yhat = model(input_tensor).to(device)
#         loss = loss_criterion(yhat, output_tensor)
#         #print("loss",loss,"yhat",yhat,"output_tensor",output_tensor)
#         #loss = loss_criterion(yhat, lb0)
#         loss.backward()
#         optimizer.step()
#         optimizer.zero_grad()
#         batch_train_counter+=1
#         batch_train_loss_total+=loss.item()
#       positive_counter,negative_counter,acr_counter=0,0,0
#       for dev_i,dev_item in enumerate(dev_data):
#         raw0,ft_vec0,lb0=dev_item
#         input_tensor=to_tensor(ft_vec0).to(device)
#         output_tensor=to_tensor([lb0]).to(device)
#         yhat = model(input_tensor).to(device)
#         #negative0,positive0,acr0=[],[],[]


#         #loss = loss_criterion(yhat, lb0)
#         loss = loss_criterion(yhat, output_tensor)
#         batch_dev_counter+=1
#         batch_dev_loss_total+=loss.item()

#         dev_analysis_list=analyze_binary_output([lb0],yhat.tolist(),dev_analysis_list)

#       epoch_train_counter+=batch_train_counter
#       epoch_dev_counter+=batch_dev_counter
#       epoch_train_loss_total+=batch_train_loss_total
#       epoch_dev_loss_total+=batch_dev_loss_total

#       # model_data_dict["train_counter"]=model_data_dict.get("train_counter",0)+batch_train_counter
#       # model_data_dict["dev_counter"]=model_data_dict.get("dev_counter",0)+batch_dev_counter
#       # model_data_dict["train_loss_total"]=model_data_dict.get("train_loss_total",0)+batch_train_loss_total
#       # model_data_dict["dev_loss_total"]=model_data_dict.get("dev_loss_total",0)+batch_dev_loss_total

#       batch_train_avg=batch_train_loss_total/batch_train_counter
#       batch_dev_avg=batch_dev_loss_total/batch_dev_counter
#       t2=time.time()
#       batch_elapsed=t2-t0
#       #print("batch_i",batch_i, "cur_batch",len(cur_batch), "batch_train_avg",round(batch_train_avg,4),"batch_dev_avg",round(batch_dev_avg,4))
#       dev_accuracy_analysis_list=get_accuracy_analysis(dev_analysis_list)
#       dev_accuracy_analysis_list_sorted=sorted(list(dev_accuracy_analysis_list[0].items()))
#       temp_line=f"epoch: {epoch} - batch_i: {batch_i} - elapsed: {round(batch_elapsed,2)} - batch_train_avg: {round(batch_train_avg,4)} - batch_dev_avg: {round(batch_dev_avg,4)} - {dev_accuracy_analysis_list_sorted}"
#       print(temp_line)
#       log_something(temp_line,log_fpath)

#       model_data_dict["epoch_train_counter"]=epoch_train_counter
#       model_data_dict["epoch_dev_counter"]=epoch_dev_counter
#       model_data_dict["epoch_train_loss_total"]=epoch_train_loss_total
#       model_data_dict["epoch_dev_loss_total"]=epoch_dev_loss_total      

#       # epoch_train_counter=model_data_dict.get("epoch_train_counter",0)
#       # epoch_dev_counter=model_data_dict.get("epoch_dev_counter",0)
#       # epoch_train_loss_total=model_data_dict.get("epoch_train_loss_total",0)
#       # epoch_dev_loss_total=model_data_dict.get("epoch_dev_loss_total",0)


#       model_data_dict["last_batch_i"]=batch_i
#       model_data_dict["latest_state_dict"]=model.state_dict()
#       torch.save(model_data_dict, model_fpath)

#     #resetting counters
#     model_data_dict["epoch_train_counter"]=0
#     model_data_dict["epoch_dev_counter"]=0
#     model_data_dict["epoch_train_loss_total"]=0
#     model_data_dict["epoch_dev_loss_total"]=0      



#     model_data_dict["last_batch_i"]=None #resetting last batch to none after the end of the epoch, to avoid restarting in the middle batches at the new epoch
#     #end of batch - save model
#     epoch_train_avg=epoch_train_loss_total/epoch_train_counter
#     epoch_dev_avg=epoch_dev_loss_total/epoch_dev_counter
#     #print(epoch, ">>>>> epoch_train_avg",round(epoch_train_avg,4),"epoch_dev_avg",round(epoch_dev_avg,4))
#     temp_line=f"epoch: {epoch} - epoch_train_avg: {round(epoch_train_avg,4)} - epoch_dev_avg: {round(epoch_dev_avg,4)}"
#     print(temp_line)
#     log_something(temp_line,log_fpath)


#     model_data_dict["last_epoch"]=epoch

#     epoch_dict=model_data_dict.get("epoch_dict",{}) #state dict for each epoch
#     epoch_dict[epoch]=model.state_dict()
#     model_data_dict["epoch_dict"]=epoch_dict

#     epoch_loss_dict=model_data_dict.get("epoch_loss_dict",{}) #loss values for each epoch
#     epoch_loss_dict[epoch]={"train":round(epoch_train_avg,4),"dev":round(epoch_dev_avg,4)}
#     model_data_dict["epoch_loss_dict"]=epoch_loss_dict


#     model_data_dict["n_train"]=epoch_train_counter
#     model_data_dict["n_dev"]=epoch_dev_counter
#     training_progress_list=model_data_dict.get("training_progress_list",[])+[(epoch,round(epoch_train_avg,6),round(epoch_dev_avg,6))]
#     #training_progress_list.append((epoch0,round(avg_train_loss,6),round(avg_dev_loss,6)))
#     model_data_dict["training_progress_list"]=training_progress_list


#     if epoch_dev_avg < best_dev_loss:
#         best_dev_loss = epoch_dev_avg
#         model_data_dict["best_dev_loss"]=best_dev_loss
#         model_data_dict["state_dict"]=model.state_dict()

#         #torch.save(rnn.state_dict(), model_fname)
#         temp_line=f"epoch: {epoch} - best_dev_loss: {round(best_dev_loss,6)} - saved to {model_fpath}"
#         print(temp_line)
#         log_something(temp_line,log_fpath)
#         # print(epoch, "best_dev_loss",best_dev_loss)
#         # print("saved to:",model_fpath)
#     torch.save(model_data_dict, model_fpath)    

def create_iter(iter_params): #use any iter parameters to create a generator
  cur_iter_fn=iter_params.get("function")
  cur_iter_fpath=iter_params.get("fpath")
  cur_from_ratio=iter_params.get("from_ratio")
  cur_to_ratio=iter_params.get("to_ratio")
  cur_yield_loc=iter_params.get("yield_loc",True)
  cur_apply_json=iter_params.get("apply_json",True)
  #read_file_from_to(data_fpath,from_ratio=0.005,to_ratio=0.006,yield_loc=True,apply_json=True)
  cur_gen=cur_iter_fn(cur_iter_fpath,from_ratio=cur_from_ratio,to_ratio=cur_to_ratio,yield_loc=cur_yield_loc,apply_json=cur_apply_json)
  return cur_gen



def training_pipeline_iter(nn_class,train_iter_params,dev_iter_params,params,feature_ex_params,loss_criterion):
  n_input0=params["n_input"]#=n_input #np.array(cur_vec).shape[-1] #cur_wv_model.vector_size #np.array(first_item[1]).shape[-1]
  n_output0=params["n_output"] #1 #np.array(cur_vec).shape[-1] #np.array(first_item[2]).shape[-1]
  n_hidden0=params["n_hidden"]
  n_layers0=params.get("n_layers",1)
  LR=params.get("LR",0.0001)
  n_epochs0=params.get("n_epochs",100)
  batch_size0=params.get("batch_size",1000)
  exp_name0=params.get("exp_name","exp")
  matching_in_out0=params.get("matching_in_out",False)
  is_rnn0=params.get("is_rnn",False)

  train_ratio0=params.get("train_ratio",0.8)
  ft_lb_extraction_fn=params.get("ft_lb_extraction_fn")
  #ft_lb_extraction_params=params.get("ft_lb_extraction_params",{})
  data_ratio=params.get("data_ratio") #the ration of the data we should use from data file
  #data_gen=read_file_from_to(data_fpath,to_ratio=0.0001)

  optimizer_name=params.get("optimizer","sgd") #
  model_dir=params.get("model_dir","models")
  main_params_items=[exp_name0,data_ratio,n_input0,n_output0,n_hidden0,n_layers0,LR,batch_size0]
  main_params_items_str="-".join([str(v) for v in main_params_items])
  model_name=params.get("model_name","model-%s.model"%main_params_items_str)
  if not os.path.exists(model_dir): os.makedirs(model_dir)
  model_fpath=os.path.join(model_dir,model_name)
  print(model_fpath)

  log_fpath=os.path.join(model_fpath+".txt")
  log_something(model_fpath,log_fpath)

  feature_ex_params_copy=copy.deepcopy(feature_ex_params) #remove the model object from parameters to easily log
  feature_ex_params_copy.pop('wv_model', None)
  log_something(str(feature_ex_params_copy),log_fpath)




  model = nn_class(n_input0, n_hidden0, n_output0,n_layers0).to(device)  # 2 represents two neurons in one hidden layer
  if optimizer_name=="sgd": optimizer = torch.optim.SGD(model.parameters(), lr=LR)#.to(device)
  elif optimizer_name=="adam": optimizer = torch.optim.Adam(model.parameters(), lr=LR)#.to(device)
  else: optimizer = torch.optim.Adam(model.parameters(), lr=LR)#.to(device)

  print(model)
  log_something(str(model),log_fpath)


  #model_fname="output/one_layer_vec3_FULL.model"
  training_progress_list=[]
  best_dev_loss=1
  last_epoch=None
  last_batch_i=None

  train_counter,dev_counter=0,0
  train_loss_total,dev_loss_total=0,0

  model_data_dict={}

  model_data_dict["params"]=params
  model_data_dict["feature_params"]=feature_ex_params_copy
  model_data_dict["network_def"]=nn_class #check
  model_data_dict["ft_lb_extraction_fn"]=ft_lb_extraction_fn

  



  if os.path.exists(model_fpath):
    temp_line=f"found model: {model_fpath}"
    print(temp_line)
    #print("found model:",model_fpath)
    log_something(temp_line,log_fpath)
    model_data_dict=torch.load(model_fpath)
    training_progress_list=model_data_dict.get("training_progress_list",[])
    best_dev_loss=model_data_dict.get("best_dev_loss",1)
    temp_line=f"best_dev_loss: {best_dev_loss}"
    print(temp_line)
    log_something(temp_line,log_fpath)

    last_epoch=model_data_dict.get("last_epoch")
    last_batch_i=model_data_dict.get("last_batch_i")
    latest_state_dict=model_data_dict.get("latest_state_dict",{})
    top_state_dict=model_data_dict.get("state_dict",{})
    
    if latest_state_dict=={}: 
      cur_state_dict=top_state_dict
      print("loaded top model")
    else: 
      cur_state_dict=latest_state_dict
      print("loaded latest model")
    #cur_state_dict=model_data_dict.get("state_dict",{})
    model.load_state_dict(cur_state_dict)
    model.train()




  for epoch in range(n_epochs0):
    epoch_train_counter,epoch_dev_counter=0,0
    epoch_train_loss_total,epoch_dev_loss_total=0,0
    train_analysis_list=[{}]*n_output0
    
    model.zero_grad()

    if last_epoch!=None and epoch<=last_epoch: 
      print(f"epoch already used {epoch}- last_epoch: {last_epoch}")
      continue

    epoch_train_counter=model_data_dict.get("epoch_train_counter",0)
    epoch_dev_counter=model_data_dict.get("epoch_dev_counter",0)
    epoch_train_loss_total=model_data_dict.get("epoch_train_loss_total",0)
    epoch_dev_loss_total=model_data_dict.get("epoch_dev_loss_total",0)

    # if data_ratio!=None: data_iterator=general.read_file_from_to(data_fpath,to_ratio=data_ratio)
    # else: data_iterator=general.read_file_from_to(data_fpath)


    #batch_iterator=general.get_iter_chunks(data_iterator, chunk_size=batch_size0,min_i=last_batch_i)

    batch_train_size=int(batch_size0*train_ratio0)
    batch_dev_size=int(batch_size0*(1-train_ratio0))
    #print("batch_train_size",batch_train_size,"batch_dev_size",batch_dev_size)
    #train_iter_params
#     train_gen=read_file_from_to(data_fpath,to_ratio=0.005,yield_loc=True,apply_json=True)
# dev_gen=read_file_from_to(data_fpath,from_ratio=0.005,to_ratio=0.006,yield_loc=True,apply_json=True)
    #train_iter=general.read_file_from_to(train_iter_params["fpath"],to_ratio=train_iter_params.get("to_ratio"),to_ratio=train_iter_params.get("to_ratio"))


    batch_train_iterator=general.get_iter_chunks(train_iter, chunk_size=batch_train_size,min_i=last_batch_i)
    batch_dev_iterator=general.get_iter_chunks(dev_iter, chunk_size=batch_dev_size,min_i=last_batch_i)

    for batch_i, cur_batch_train_dev in enumerate(zip(batch_train_iterator,batch_dev_iterator)): 
      cur_batch_train,cur_batch_dev=cur_batch_train_dev
      last_batch_i=model_data_dict.get("last_batch_i")
      if last_batch_i!=None and batch_i<=last_batch_i: continue
      t0=time.time()
      #dev_data=cur_batch_items[train_size:]
      train_data,dev_data=[],[]
      for train_i,train_item in cur_batch_train: #iterators include both the index and item
        cur_raw_ft_dict=train_item #json.loads(train_item_str)
        cur_ft,cur_lb=ft_lb_extraction_fn(cur_raw_ft_dict,params=feature_ex_params)
        # try: cur_ft,cur_lb=ft_lb_extraction_fn(cur_raw_ft_dict,params=feature_ex_params)
        # except: continue
        train_data.append((cur_raw_ft_dict,cur_ft,cur_lb))
      for dev_i,dev_item in cur_batch_dev:
        cur_raw_ft_dict=dev_item #json.loads(dev_item_str)
        try: cur_ft,cur_lb=ft_lb_extraction_fn(cur_raw_ft_dict,params=feature_ex_params)
        except: continue
        dev_data.append((cur_raw_ft_dict,cur_ft,cur_lb))


      t1=time.time()
      elapsed=t1-t0
      temp_line=f"feature extraction: elapsed: {round(elapsed,2)} - train_data: {len(train_data)} - dev data: {len(dev_data)}"
      print(temp_line)

      batch_train_counter,batch_dev_counter=0,0
      batch_train_loss_total,batch_dev_loss_total=0,0
      #print("train_data",len(train_data),"dev_data",len(dev_data))
      dev_analysis_list=[{}]*n_output0

      for train_i,train_item in enumerate(train_data):
        raw0,ft_vec0,lb0=train_item
        input_tensor=to_tensor(ft_vec0).to(device)
        output_tensor=to_tensor([lb0]).to(device)
        yhat = model(input_tensor).to(device)
        loss = loss_criterion(yhat, output_tensor)
        #print("loss",loss,"yhat",yhat,"output_tensor",output_tensor)
        #loss = loss_criterion(yhat, lb0)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        batch_train_counter+=1
        batch_train_loss_total+=loss.item()
      positive_counter,negative_counter,acr_counter=0,0,0
      for dev_i,dev_item in enumerate(dev_data):
        raw0,ft_vec0,lb0=dev_item
        input_tensor=to_tensor(ft_vec0).to(device)
        output_tensor=to_tensor([lb0]).to(device)
        yhat = model(input_tensor).to(device)
        #negative0,positive0,acr0=[],[],[]


        #loss = loss_criterion(yhat, lb0)
        loss = loss_criterion(yhat, output_tensor)
        batch_dev_counter+=1
        batch_dev_loss_total+=loss.item()

        dev_analysis_list=analyze_binary_output([lb0],yhat.tolist(),dev_analysis_list)

      epoch_train_counter+=batch_train_counter
      epoch_dev_counter+=batch_dev_counter
      epoch_train_loss_total+=batch_train_loss_total
      epoch_dev_loss_total+=batch_dev_loss_total

      # model_data_dict["train_counter"]=model_data_dict.get("train_counter",0)+batch_train_counter
      # model_data_dict["dev_counter"]=model_data_dict.get("dev_counter",0)+batch_dev_counter
      # model_data_dict["train_loss_total"]=model_data_dict.get("train_loss_total",0)+batch_train_loss_total
      # model_data_dict["dev_loss_total"]=model_data_dict.get("dev_loss_total",0)+batch_dev_loss_total
      batch_train_avg,batch_dev_avg=-1,-1

      if batch_train_counter>0: batch_train_avg=batch_train_loss_total/batch_train_counter
      if batch_dev_counter>0: batch_dev_avg=batch_dev_loss_total/batch_dev_counter
      t2=time.time()
      batch_elapsed=t2-t0
      #print("batch_i",batch_i, "cur_batch",len(cur_batch), "batch_train_avg",round(batch_train_avg,4),"batch_dev_avg",round(batch_dev_avg,4))
      dev_accuracy_analysis_list=get_accuracy_analysis(dev_analysis_list)
      dev_accuracy_analysis_list_sorted=sorted(list(dev_accuracy_analysis_list[0].items()))
      temp_line=f"epoch: {epoch} - batch_i: {batch_i} - elapsed: {round(batch_elapsed,2)} - batch_train_avg: {round(batch_train_avg,4)} - batch_dev_avg: {round(batch_dev_avg,4)} - {dev_accuracy_analysis_list_sorted}"
      print(temp_line)
      log_something(temp_line,log_fpath)

      model_data_dict["epoch_train_counter"]=epoch_train_counter
      model_data_dict["epoch_dev_counter"]=epoch_dev_counter
      model_data_dict["epoch_train_loss_total"]=epoch_train_loss_total
      model_data_dict["epoch_dev_loss_total"]=epoch_dev_loss_total      

      # epoch_train_counter=model_data_dict.get("epoch_train_counter",0)
      # epoch_dev_counter=model_data_dict.get("epoch_dev_counter",0)
      # epoch_train_loss_total=model_data_dict.get("epoch_train_loss_total",0)
      # epoch_dev_loss_total=model_data_dict.get("epoch_dev_loss_total",0)


      model_data_dict["last_batch_i"]=batch_i
      model_data_dict["latest_state_dict"]=model.state_dict()
      torch.save(model_data_dict, model_fpath)

    #resetting counters
    model_data_dict["epoch_train_counter"]=0
    model_data_dict["epoch_dev_counter"]=0
    model_data_dict["epoch_train_loss_total"]=0
    model_data_dict["epoch_dev_loss_total"]=0      



    model_data_dict["last_batch_i"]=None #resetting last batch to none after the end of the epoch, to avoid restarting in the middle batches at the new epoch
    #end of batch - save model
    epoch_train_avg,epoch_dev_avg=-1,-1
    if epoch_train_counter>0: epoch_train_avg=epoch_train_loss_total/epoch_train_counter
    if epoch_dev_counter>0: epoch_dev_avg=epoch_dev_loss_total/epoch_dev_counter
    #print(epoch, ">>>>> epoch_train_avg",round(epoch_train_avg,4),"epoch_dev_avg",round(epoch_dev_avg,4))
    temp_line=f"epoch: {epoch} - epoch_train_avg: {round(epoch_train_avg,4)} - epoch_dev_avg: {round(epoch_dev_avg,4)}"
    print(temp_line)
    log_something(temp_line,log_fpath)


    model_data_dict["last_epoch"]=epoch

    epoch_dict=model_data_dict.get("epoch_dict",{}) #state dict for each epoch
    epoch_dict[epoch]=model.state_dict()
    model_data_dict["epoch_dict"]=epoch_dict

    epoch_loss_dict=model_data_dict.get("epoch_loss_dict",{}) #loss values for each epoch
    epoch_loss_dict[epoch]={"train":round(epoch_train_avg,4),"dev":round(epoch_dev_avg,4)}
    model_data_dict["epoch_loss_dict"]=epoch_loss_dict


    model_data_dict["n_train"]=epoch_train_counter
    model_data_dict["n_dev"]=epoch_dev_counter
    training_progress_list=model_data_dict.get("training_progress_list",[])+[(epoch,round(epoch_train_avg,6),round(epoch_dev_avg,6))]
    #training_progress_list.append((epoch0,round(avg_train_loss,6),round(avg_dev_loss,6)))
    model_data_dict["training_progress_list"]=training_progress_list


    if epoch_dev_avg < best_dev_loss:
        best_dev_loss = epoch_dev_avg
        model_data_dict["best_dev_loss"]=best_dev_loss
        model_data_dict["state_dict"]=model.state_dict()

        #torch.save(rnn.state_dict(), model_fname)
        temp_line=f"epoch: {epoch} - best_dev_loss: {round(best_dev_loss,6)} - saved to {model_fpath}"
        print(temp_line)
        log_something(temp_line,log_fpath)
        # print(epoch, "best_dev_loss",best_dev_loss)
        # print("saved to:",model_fpath)
    torch.save(model_data_dict, model_fpath)    

class load_nn:
  def __init__(self,model_fpath,network_def,extraction_fn=None,extraction_params=None,epoch_i=None) -> None:
    self.model_data_dict={}
    self.model=None
    if not os.path.exists(model_fpath): return 

    self.model_data_dict=torch.load(model_fpath)
    self.cur_params=self.model_data_dict.get("params",{})
    if extraction_params!=None: self.extraction_params=extraction_params
    else: self.extraction_params=self.model_data_dict["feature_params"]
    
    self.training_progress_list=self.model_data_dict.get("training_progress_list",[])
    self.best_dev_loss=self.model_data_dict.get("best_dev_loss",1)
    self.last_epoch=self.model_data_dict.get("last_epoch")
    self.last_batch_i=self.model_data_dict.get("last_batch_i")
    
    self.cur_state_dict=self.model_data_dict.get("state_dict",{}) #top state dict
    self.cur_epoch_dict=self.model_data_dict.get("epoch_dict",{}) #state dict for every epoch
    epoch_state_dict=self.cur_epoch_dict.get(epoch_i)

    if epoch_i!=None and epoch_state_dict!=None: self.cur_state_dict=epoch_state_dict


    if extraction_fn!=None: self.ft_lb_extraction_fn=extraction_fn
    else: self.ft_lb_extraction_fn=self.model_data_dict.get("ft_lb_extraction_fn")
    #model = one_layer_net(cur_params["n_input"], cur_params["n_hidden"], cur_params["n_output"])
    self.n_input=self.cur_params["n_input"]
    self.n_hidden=self.cur_params["n_hidden"]
    self.n_output=self.cur_params["n_output"]
    self.n_layers=self.cur_params.get("n_layers",1)

    self.model = network_def(self.n_input, self.n_hidden, self.n_output, self.n_layers)
    self.model.load_state_dict(self.cur_state_dict)
    self.model.eval()
    cur_wv_path=self.extraction_params.get("wv_fpath","")
    self.wv_model=Word2Vec.load(cur_wv_path)
    self.extraction_params["wv_model"]=self.wv_model
  def update_state_dict(self,new_state_dict):
    self.model.load_state_dict(new_state_dict)
    self.model.eval()
  def pred(self,raw_input_dict):
    input_vector,input_lb=self.ft_lb_extraction_fn(raw_input_dict,self.extraction_params)
    input_tensor=to_tensor(input_vector)
    nn_out=self.model(input_tensor)
    return nn_out.item()