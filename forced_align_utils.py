#forced alignment

def get_shortest(dict_list0,seq0): #simple djkstra-like function to get the shortest path in lists of dictionaries of items/phonemes
  padded_seq=[""]+seq0+[""]
  transition_dict={}
  start_pt=(-1,"")
  end_pt=(len(dict_list0),"")
  prev_pts=[start_pt]
  for index0,cur_dict in enumerate(dict_list0):
    tmp_transition={}
    cur_pts=[]
    for a,b in cur_dict.items():
      cur_key=(index0,a)
      tmp_transition[cur_key]=b
      cur_pts.append(cur_key)
    for pv0 in prev_pts:
      transition_dict[pv0]=tmp_transition
    prev_pts=cur_pts
  tmp_transition={}
  tmp_transition[end_pt]=1
  for pv0 in prev_pts:
    transition_dict[pv0]=tmp_transition
  prev_dict={}
  wt_dict={}
  seq_dict={}
  key_list=sorted(list(transition_dict.keys()))
  for prev0 in key_list:
    cur_dict=transition_dict[prev0]
    prev_path_wt=wt_dict.get(prev0,0)
    prev_i,prev_ph=prev0
    prev_seq=seq_dict.get(prev0,[prev_ph])
    for cur0,wt0 in cur_dict.items():
      cur_i,cur_ph=cur0
      tmp_seq=prev_seq
      if cur_ph==prev_seq[-1]: pass
      else: tmp_seq=prev_seq+[cur_ph]
      combined_wt=prev_path_wt+wt0
      found_wt=wt_dict.get(cur0,0)
      if combined_wt>found_wt and tmp_seq==padded_seq[:len(tmp_seq)]:
        prev_dict[cur0]=prev0
        wt_dict[cur0]=combined_wt
        seq_dict[cur0]=tmp_seq
  cur_out=prev_dict.get(end_pt)
  final_list=[]
  while cur_out!=None:
    final_list.append(cur_out)
    tmp_wt=wt_dict.get(cur_out,0)
    cur_out=prev_dict.get(cur_out)
  path0=reversed(final_list[:-1])
  return path0 #output will be the path with the highest combined weight

class falign: #forced alignment class
  def __init__(self,model_fpath) -> None:
    self.model_pred_obj=model_pred(model_fpath)
    self.ipa_ft_dict=self.model_pred_obj.ipa_ft_dict
  def predict_phones(self,wav_fpath0,cur_seq0=[],max_single_frame=1,feature_extraction_fn=extract_audio_features):
    self.ft_pred_out=self.model_pred_obj.predict(wav_fpath0,feature_extraction_fn) #get initial feature predictions
    self.half_step=self.ft_pred_out[1][0]/2
    times=[v[0] for v in self.ft_pred_out]
    sample_rate, sig = wavfile.read(wav_fpath0)
    if len(sig.shape)>1: sig= sig.sum(axis=1)
    file_duration=len(sig)/sample_rate	
    cur_phone_list=list(set(cur_seq0)) #identify a set of current phones to be aligned
    tmp_ph_ft_list=[]
    for ph0 in cur_phone_list:
      corr_fts=self.ipa_ft_dict.get(ph0,[])
      for cf0 in corr_fts: tmp_ph_ft_list.append((cf0,ph0))
    tmp_ph_ft_list.sort()
    grouped_ft_ph=[(key,[v[1] for v in list(group)]) for key,group in groupby(tmp_ph_ft_list,lambda x:x[0])]
    ft_ph_dict=dict(iter(grouped_ft_ph))
    ft_val_list_dict={}
    for i0,t_p in enumerate(self.ft_pred_out):
      time0, cur_ft_preds=t_p
      for a, b in cur_ft_preds: #cur_ft_preds_dict.items():
        corr_ph=ft_ph_dict.get(a,[])
        if not corr_ph: continue
        ft_val_list_dict[a]=ft_val_list_dict.get(a,[])+[b]

    ft_range_mean_dict={}
    for a,b in ft_val_list_dict.items():
      cur_min=min(b)
      cur_max=max(b)
      cur_mean=sum(b)/len(b)
      ft_range_mean_dict[a]=(cur_min,cur_max,cur_mean)
      #print(a, len(b),(cur_min,cur_max,cur_mean))
    ph_list_to_align=[]
    for i0,t_p in enumerate(self.ft_pred_out):
      time0, cur_ft_preds=t_p
      tmp_ph_ft_wt_list=[]
      for ft0, wt0 in cur_ft_preds: #cur_ft_preds_dict.items():
        corr_ph=ft_ph_dict.get(ft0,[])
        if not corr_ph: continue
        min0,max0,mean0=ft_range_mean_dict.get(ft0)
        adj_wt=(wt0-min0)/(max0-min0)
        #print(ft0, round(wt0,4), "adj_wt",round(adj_wt,4), corr_ph)
        for ph0 in corr_ph:
          tmp_ph_ft_wt_list.append((ph0,ft0,adj_wt))
        #print(ft0, round(wt0,4), "adj_wt",round(adj_wt,4) , corr_ph, min0,max0,mean0)
      tmp_ph_ft_wt_list.sort(key=lambda x:(x[0],-x[-1]))
      grouped=[(key,[v[-1] for v in list(group)]) for key,group in groupby(tmp_ph_ft_wt_list,lambda x:x[0])]
      final_tmp_ph_list=[]
      tmp_ph_wt_dict={}
      for key0,grp0 in grouped:
        max_val=round(max(grp0),4)
        mean_val=round(sum(grp0)/len(grp0),4) 
        final_tmp_ph_list.append((key0,max_val,mean_val))
        #tmp_ph_wt_dict[key0]=mean_val
        tmp_ph_wt_dict[key0]=max_val
        #tmp_ph_wt_dict[key0]=max_val+mean_val

      ph_list_to_align.append(tmp_ph_wt_dict)

    shortest_path0=get_shortest(ph_list_to_align,cur_seq0)
    final_out=[]
    for sh0,ti0 in zip(shortest_path0,times):
      start0,end0=max(0,ti0-self.half_step),min(ti0+self.half_step,file_duration)
      final_out.append((sh0[1],start0,end0))
    grouped_final_out=[(key,[v[1:] for v in list(group)]) for key,group in groupby(final_out,lambda x:x[0])]
    phn_list=[]
    n_single_frames=0
    for key0,grp0 in grouped_final_out:
      final_start0,final_end0=grp0[0][0],grp0[-1][1]
      #frame0,frame1=round(final_start0*sample_rate),round(final_end0*sample_rate)
      frame0,frame1=round(final_start0*16000),round(final_end0*16000)
      phn_list.append((frame0,frame1,key0)) 
      print(key0,len(grp0), round(final_start0,4),round(final_end0,4),frame0,frame1)
      if not key0 in ["-","sil"] and len(grp0)<2:n_single_frames+=1
    #print("n_single_frames",n_single_frames)
    #print("self.half_step",self.half_step, "file_duration",file_duration,"sample_rate",sample_rate)
    if n_single_frames>max_single_frame: phn_list=[]
    return phn_list