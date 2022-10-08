#audio processing - splitting - joining - conversion etc.
#!pip install pydub
from pydub import AudioSegment

def split_audio_by_aligned_words(wav_fpath0,out_fpath0,t1,t2): #time in milliseconds
    t1 = t1 * 1000 #Works in milliseconds
    t2 = t2 * 1000
    newAudio = AudioSegment.from_wav(wav_fpath0)
    newAudio = newAudio[t1:t2]
    newAudio.export(out_fpath0, format="wav") #Exports to a wav file in the current path.
