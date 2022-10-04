import numpy as np

def sigmoid(x): 
    return 1. / (1 + np.exp(-x))
def softmax(x):
    e_x = np.exp(x - np.max(x)) # max(x) subtracted for numerical stability
    return e_x / np.sum(e_x)

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


def numpy_lstm(data_input,state_dict0, matching_in_out=False):
  #we can get the number of layers and number of hidden from the state dict
  cur_params=get_params(state_dict0)
  n_hidden=cur_params["n_hidden"]
  new_stat_dict={}
  for a,b in state_dict0.items(): #just to handle whether th state dict has torch tensors or numpy arrays
    try: new_stat_dict[a]=b.numpy() #if torch tensors, convert to numpy
    except: new_stat_dict[a]=b #otherwise, keep it
  state_dict0=new_stat_dict
  for layer_i in range(cur_params["n_layers"]):
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
      if matching_in_out: out_list.append(h)
      #cur_output=model_output(h, fc_Weight, fc_Bias)
      #all_output.append(cur_output)
    if matching_in_out:  data_input=np.array(out_list)
    else: data_input=np.array(h)
    #data_input=np.array(out_list)
    #print(data_input)
  return  data_input
def fully_connected(lstm_out,state_dict0,apply_sigmoid=False):
  cur_params=get_params(state_dict0)
  fc_wt,fc_bias=cur_params["fc_weight"],cur_params["fc_bias"]
  try: fc_wt,fc_bias=fc_wt.numpy(),fc_bias.numpy()
  except: pass
  all_output=[]
  for lstm_item in lstm_out:
    cur_output=np.dot(fc_wt, lstm_item) + fc_bias
    all_output.append(cur_output)
  res=np.array(all_output)
  if apply_sigmoid: res=sigmoid(res)
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


if __name__=="__main__":
  data = np.array(
            [[1,1],
              [2,2],
              [3,3]])


  input_size  = 2 # size of one 'event', or sample, in our batch of data
  n_hidden = hidden_dim  = 16 # 3 cells in the LSTM layer
  output_size = 6 # desired model output
  num_layers=2
  lstm_output=numpy_lstm(data,state)
  fc_output=fully_connected(lstm_output,state)
  fc_output_sigmoid=sigmoid(fc_output) 
  fc_output_softmax=softmax(fc_output) 
  print("numpy LSTM output:", fc_output)

