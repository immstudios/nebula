import subprocess


import numpy as np
import matplotlib.pyplot as plt 


class VideoAnalyzer():
    def __init__(self):
        self.frame_no = -1
        self.result = {
            "ave_lumas" :[],
            "ave_rs" :[], 
            "ave_gs" :[],
            "ave_bs" :[]
            }

    def push(self, frame):
        r = frame
        ave_luma = np.sum(r)/(len(r))
        reds   = r[0:len(r):3]
        greens = r[1:len(r):3]
        blues  = r[2:len(r):3]
        ave_r = np.sum(reds)  /(len(r)/3)
        ave_g = np.sum(greens)/(len(r)/3)
        ave_b = np.sum(blues) /(len(r)/3)
        
        self.result["ave_lumas"].append(ave_luma)
#        vari_r = np.var(reds)
#        vari_g = np.var(greens)
#        vari_b = np.var(blues)
#        vari_all = np.average(np.array([vari_r,vari_g,vari_b]))

        #print ("{:.02f}\t{:.02f}\t{:.02f}\t{:.02f}".format(ave_r, ave_g, ave_b, ave_luma))

    def finalize(self):
        #luma_fft = np.fft.fft(self.result["ave_lumas"])
        #r_fft  = np.fft.rfft(self.result["ave_rs"])
#        for a, f in zip(self.result["ave_lumas"], luma_fft):
#            print ("{:.02f}\t{:.02f}".format(a, int(f)))

        plt.plot(self.result["ave_lumas"])
        plt.show()



#def anl(fname="testcols.mov"):
#def anl(fname='C:\\martas\\Media\\Movies\\Prometheus.2012.1080p.BrRip.x264.YIFY.mp4'):
def anl(fname="crypto.mov"):
#def anl(fname="helveticapower.png"):

    FFMPEG_BINARY = "ffmpeg.exe"
    PROC_W = 192#0
    PROC_H = 108#0


    proc = subprocess.Popen([
        FFMPEG_BINARY,
        "-i", fname,
        "-s", "{}x{}".format(PROC_W, PROC_H),
        "-pix_fmt", "rgb24",
        "-f", "rawvideo",
        "-"
        ], 
        stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE
        )

    analyzer = VideoAnalyzer()
    fpos = -1
    while proc.poll() == None:
        fpos+=1
        frame = proc.stdout.read(PROC_W*PROC_H*3)
#        if fpos%100 != 0:
#            continue
        print ("Reading frame", fpos)
            
        if not frame:
            break
        frame = np.fromstring(frame, dtype=np.uint8)       
        analyzer.push(frame)
        #frame.shape = (PROC_W,PROC_H,3)
        #print (frame)

    analyzer.finalize()



anl()   