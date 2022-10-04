import torch
from torch import nn
import torch.optim as optim
import random
import dill as pickle
from collections import OrderedDict
import numpy as np

torch.manual_seed(1)
random.seed(1)

device = torch.device('cpu')


class RNN(nn.Module):
  def __init__(self, input_size, hidden_size, output_size,num_layers, matching_in_out=False, init_val=None, apply_sigmoid=False, apply_softmax=False, batch_size=1):
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

def to_tensor(list1):
  return torch.tensor(list1,dtype=torch.float32)

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



class model_pred:
  def __init__(self,model_fpath0) -> None:
    # try: self.checkpoint = torch.load(model_fpath0)
    # except: self.checkpoint = dill_unpickle(model_fpath0)
    self.checkpoint = dill_unpickle(model_fpath0)
    self.rnn = RNN(self.checkpoint["n_input"], self.checkpoint["n_hidden"] , self.checkpoint["n_output"] , self.checkpoint["n_layers"] , matching_in_out=self.checkpoint["n_layers"]).to(device)
    self.rnn.load_state_dict(self.checkpoint['model_state_dict'])
    self.rnn.eval()
    self.feature_extraction_fn=self.checkpoint.get("feature_extraction_function")

    self.feature_extraction_params=self.checkpoint["feature_extraction_parameters"]

    self.standard_labels=self.checkpoint['label_extraction_parameters']['ipa_ft_list']
    self.ipa_ft_dict=self.checkpoint["label_extraction_parameters"]["ipa_ft_dict"]
    self.ipa_list=self.checkpoint["label_extraction_parameters"]["ipa_symbol_list"]    
  def predict(self,item_fpath,feature_extraction_fn=None):
    if self.feature_extraction_fn==None: self.feature_extraction_fn=feature_extraction_fn
    times,ft_vector=self.feature_extraction_fn(item_fpath,self.feature_extraction_params)
    ft_tensor=torch.tensor(ft_vector,dtype=torch.float32)
    rnn_out= self.rnn(ft_tensor)
    preds0=out2labels(rnn_out.ravel(),self.standard_labels)
    times_preds_list=[]
    for pr0,ti0 in zip(preds0,times):
      pr0=[(v[0],v[1].item()) for v in pr0]
      times_preds_list.append((ti0,pr0)) 
    return times_preds_list  

class np_model_pred:
  def __init__(self,model_fpath0) -> None:
    # try: self.checkpoint = torch.load(model_fpath0)
    # except: self.checkpoint = dill_unpickle(model_fpath0)
    self.checkpoint = dill_unpickle(model_fpath0)
    # self.rnn = RNN(self.checkpoint["n_input"], self.checkpoint["n_hidden"] , self.checkpoint["n_output"] , self.checkpoint["n_layers"] , matching_in_out=self.checkpoint["n_layers"]).to(device)
    # self.rnn.load_state_dict(self.checkpoint['model_state_dict'])
    # self.rnn.eval()
    self.state_dict=self.checkpoint['model_state_dict']
    self.feature_extraction_fn=self.checkpoint["feature_extraction_function"]
    self.feature_extraction_params=self.checkpoint["feature_extraction_parameters"]

    self.standard_labels=self.checkpoint['label_extraction_parameters']['ipa_ft_list']
    self.ipa_ft_dict=self.checkpoint["label_extraction_parameters"]["ipa_ft_dict"]
    self.ipa_list=self.checkpoint["label_extraction_parameters"]["ipa_symbol_list"]    
  def predict(self,item_fpath):
    times,ft_vector=self.feature_extraction_fn(item_fpath,self.feature_extraction_params)
    #ft_tensor=torch.tensor(ft_vector,dtype=torch.float32)
    lstm_output=numpy_lstm(ft_vector,self.state_dict)
    rnn_out=fully_connected(lstm_output,self.state_dict)  
    #rnn_out= self.rnn(ft_tensor)
    preds0=out2labels(rnn_out.ravel(),self.standard_labels)
    times_preds_list=[]
    for pr0,ti0 in zip(preds0,times):
      pr0=[(v[0],v[1].item()) for v in pr0]
      times_preds_list.append((ti0,pr0)) 
    return times_preds_list  


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

def chk2pickle(chk_pt_fpath0,new_pickle_path0,skip_optimizer=True, skip_eval=True,skip_label=True): #convert torch checkpoint to pickle, and convert tensors to numpy arrays - to work independently from torch
  pickle_dict0={}
  try: checkpoint_dict = torch.load(chk_pt_fpath0)
  except: checkpoint_dict = dill_unpickle(chk_pt_fpath0)
  for a,b in checkpoint_dict.items():
    #print(a,type(b))
    if skip_optimizer and a.lower()=="optimizer_state_dict": continue
    if skip_eval and a.lower()=="eval_function": continue
    if skip_label and a.lower()=="label_extraction_function": continue
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

# Applying RNN to audio files
# epoch_i=4
# exp_name="en-pronunciation-test-expanded-128-L2"

# torch.manual_seed(1)
# random.seed(1)

# model_dir="models"
# exp_dir_path=os.path.join(model_dir,exp_name)
# tmp_path=os.path.join(exp_dir_path,"model-%s.model"%epoch_i)
# try: checkpoint = torch.load(tmp_path)
# except: checkpoint = dill_unpickle(tmp_path)
# rnn = RNN(checkpoint["n_input"],checkpoint["n_hidden"] ,checkpoint["n_output"] ,checkpoint["n_layers"] ,checkpoint["matching_in_out"]).to(device)
# rnn.load_state_dict(checkpoint['model_state_dict'])
# params=checkpoint['feature_extraction_parameters']
# standard_labels=checkpoint['output_labels']
# rnn.eval()

# cur_files=get_dir_files(segmented_dir,extension="wav")
# word_list=["the","about","pronunciation","create","cat","dog","spirit","this","than","see","she","or","didn't","if","hear"]
# #arpabet_pair=["s","th"]
# arpabet_pair=["z","dh"]


# for cur_wav_fpath in cur_files[:20]:
#   print("cur_wav_fpath",cur_wav_fpath)
#   out_dic1=identify_wav(cur_wav_fpath,rnn,params,standard_labels,word_list,arpabet_pair)
#   for a,b in out_dic1.items():
#     print(a)
#     for b0 in b: print(b0[0],b0[-1])
#   print("=====")  