#extract audio features
#!pip install python_speech_features

from python_speech_features import mfcc #Mel Frequency Cepstral Coefficients
from python_speech_features import logfbank #Log Filterbank Energies ->> just Filterbank: python_speech_features.fbank()
from python_speech_features import ssc #Spectral Subband Centroids

import re, time, os, json
import scipy.io.wavfile as wav
from scipy import signal
from scipy.io import wavfile
import numpy as np

def extract_audio_features(wav_fpath0,parameters0={}):
  #sample_rate, samples = wavfile.read(wav_fpath0)
  nfft0=parameters0.get("nfft",2048)
  use_logfbank=parameters0.get("logfbank",True)
  use_mfcc=parameters0.get("mfcc",False)
  use_ssc=parameters0.get("ssc",False)
  use_spectrogram=parameters0.get("spectrogram",False) or parameters0.get("spec",False)

  sample_rate, sig = wavfile.read(wav_fpath0)
  if len(sig.shape)>1: sig= sig.sum(axis=1)
  file_duration=len(sig)/sample_rate	
  if use_spectrogram: 
    frequencies, times, spectrogram = signal.spectrogram(sig, sample_rate)
    spectrogram=spectrogram.transpose()
    return times, spectrogram
  logfbank_out=[]
  mfcc_out=[]
  ssc_out=[]
  if use_logfbank: logfbank_out=logfbank(sig,sample_rate,nfft=nfft0)
  if use_mfcc: mfcc_out=mfcc(sig,sample_rate,nfft=nfft0)
  if use_ssc: ssc_out=ssc(sig,sample_rate,nfft=nfft0)
  tmp_combined=[]
  for it0 in [logfbank_out,mfcc_out,ssc_out]:
    tmp_list=list(it0)
    if tmp_list==[]: continue
    tmp_combined.append(tmp_list)

  #combined_out=np.concatenate((logfbank_out, mfcc_out,ssc_out), axis=1)
  combined_out=np.concatenate(tmp_combined, axis=1)
  time_step=file_duration/len(combined_out)
  times=[i_*time_step for i_ in range(len(combined_out))]
  return times, combined_out  
