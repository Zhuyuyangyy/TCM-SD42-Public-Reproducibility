from collections import defaultdict
from contextlib import contextmanager
from html import escape
from pathlib import Path
from statistics import mean, median, quantiles
from math import exp, log10
import csv
import json
import os
import re
import subprocess
import sys

NAVY="#0b2a6b"
INK="#1e2c46"
MUTED="#3c4d6a"
BORDER="#9ca8c0"
GRID="#dbe0ea"
LIGHT="#edf2f8"
PAPER="#f8fafc"
BLUE="#1f5ea8"
ORANGE="#c65b2f"
GREEN="#4d8d6b"
PLUM="#7145a4"
GOLD="#b46c2a"
RED="#bd412d"
MODEL=[BLUE,ORANGE,GREEN,PLUM]
NAMES=["ZY-BERT","InternLM3-8B","MacBERT","Qwen3-8B"]
SHORT=["ZY","Intern","Mac","Qwen"]
KEYS=["zybert","internlm3","macbert","qwen3"]
PAIRS=[(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
LOCAL_ROOT=Path(__file__).resolve().parent
LOCAL_REPO=LOCAL_ROOT.parent
DEFAULT_REPO=LOCAL_REPO if (LOCAL_REPO/"figures_py"/"source_data").is_dir() else Path("D:/GITHUB/Sivia/submission-repro-review")
BUNDLED_REPO=LOCAL_ROOT/"ReproData"
REPO=Path(os.environ.get("TCM_SD42_REPO", str(BUNDLED_REPO if BUNDLED_REPO.exists() else DEFAULT_REPO)))
DATA=REPO/"figures_py"/"source_data"
RES=REPO/"results"
DEFAULT_OUT=LOCAL_REPO/"figures_py"/"generated_figures" if (LOCAL_REPO/"figures_py"/"source_data").is_dir() else LOCAL_ROOT
OUT=Path(os.environ.get("TCM_SD42_OUT", str(DEFAULT_OUT)))
TMP=Path(__file__).parent

def csvrows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def mix(col,t):
    return "#"+"".join(f"{round(255*(1-t)+int(col[i:i+2],16)*t):02x}" for i in (1,3,5))

def f2(val, sign=False):
    return format(float(val),"+.2f" if sign else ".2f").replace("-","−")

def sci(val):
    a,b=format(float(val),".2e").split("e")
    return a+" × 10"+str(int(b)).translate(str.maketrans("-0123456789","⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))

class SVG:
    def __init__(self,w,h):
        self.w,self.h=w,h
        self.el=[]
        self.box(0,0,w,h,"#ffffff","none")

    def raw(self,x):
        self.el.append(x)

    @contextmanager
    def group(self,name):
        self.raw(f'<g aria-label="{escape(name,quote=True)}">')
        yield
        self.raw("</g>")

    def box(self,x,y,w,h,fill="#ffffff",stroke=BORDER,r=0,sw=1,dash=False):
        d=' stroke-dasharray="5 3"' if dash else ""
        self.raw(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}"{d}/>' )

    def text(self,x,y,label,size=16,weight=400,c=INK,a="start",family=None,rotate=None):
        family=family or ("Noto Sans CJK SC" if re.search("[\u3000-\u9fff]",str(label)) else "Arial")
        t=f' transform="rotate({rotate:g} {x:g} {y:g})"' if rotate else ""
        self.raw(f'<text x="{x:g}" y="{y:g}" text-anchor="{a}" font-family="{family}" font-size="{size:g}" font-weight="{weight}" fill="{c}"{t}>{escape(str(label))}</text>')

    def line(self,x,y,X,Y,c=NAVY,w=1.25,dash=False):
        d=' stroke-dasharray="4 3"' if dash else ""
        self.raw(f'<line x1="{x:g}" y1="{y:g}" x2="{X:g}" y2="{Y:g}" stroke="{c}" stroke-width="{w:g}"{d}/>' )

    def poly(self,xy,c=NAVY,w=1.25,fill="none",closed=False):
        tag="polygon" if closed else "polyline"
        xy=" ".join(f"{x:g},{y:g}" for x,y in xy)
        self.raw(f'<{tag} points="{xy}" stroke="{c}" stroke-width="{w:g}" fill="{fill}"/>')

    def path(self,d,fill="none",c=NAVY,w=1.25):
        self.raw(f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{w:g}"/>')

    def dot(self,x,y,r,fill=BLUE,c="none",w=1):
        self.raw(f'<circle cx="{x:g}" cy="{y:g}" r="{r:g}" fill="{fill}" stroke="{c}" stroke-width="{w:g}"/>' )

    def arrow(self,xy,c=NAVY,w=1.6):
        x,y=xy[-1]; q,z=xy[-2]; norm=((x-q)**2+(y-z)**2)**.5
        vx,vy=(x-q)/norm,(y-z)/norm
        d=min(8,norm*.72)
        X,Y=x-vx*d,y-vy*d
        self.poly([*xy[:-1],(X,Y)],c,w)
        self.poly([(x,y),(X-vy*d*.46,Y+vx*d*.46),(X+vy*d*.46,Y-vx*d*.46)],"none",0,c,True)

    def panel(self,x,y,w,h,letter=None):
        self.box(x,y,w,h,"#ffffff",NAVY,10,2.1)
        if letter:
            self.box(x+10,y+8,46,40,NAVY,"none",8)
            self.text(x+33,y+37,letter,26,700,"#ffffff","middle","Georgia")

    def module(self,x,y,w,h,title,c=NAVY,quiet=False):
        self.box(x,y,w,h,"#ffffff",BORDER,6,1,not quiet)
        if title:
            self.box(x+5,y+5,w-10,31,mix(c,.16),"none",6)
            self.text(x+w/2,y+25,title,16.5,700,c,"middle","Georgia")

    def labelbox(self,x,y,w,h,label,c=BLUE,size=14):
        self.box(x,y,w,h,mix(c,.17),mix(c,.72),4)
        self.text(x+w/2,y+h/2+size*.34,label,size,700,c,"middle")

    def legend(self,x,y,pairs,size=14,step=108):
        for j,(c,t) in enumerate(pairs):
            X=x+j*step
            self.box(X,y-10,10,10,c,"none",1)
            self.text(X+16,y,t,size,400,INK)

    def lines(self,x,y,s,size=15,dy=20,c=INK,a="middle",weight=400):
        for j,t in enumerate(s):
            self.text(x,y+j*dy,t,size,weight,c,a)

    def database(self,cx,y,w=65,h=64,c=BLUE):
        x=cx-w/2; z=cx+w/2
        self.path(f"M{x:g},{y+8:g} V{y+h-10:g} C{x:g},{y+h+5:g} {z:g},{y+h+5:g} {z:g},{y+h-10:g} V{y+8:g} Z",mix(c,.12),c,1.55)
        self.path(f"M{x:g},{y+8:g} C{x:g},{y-4:g} {z:g},{y-4:g} {z:g},{y+8:g} C{z:g},{y+20:g} {x:g},{y+20:g} {x:g},{y+8:g} Z",mix(c,.39),c,1.55)
        for i in (1,2):
            yy=y+8+(h-17)*i/3
            self.path(f"M{x:g},{yy:g} C{x:g},{yy+10:g} {z:g},{yy+10:g} {z:g},{yy:g}","none",c,1.45)
        for i in (1,2):
            self.dot(z-7,y+15+(h-15)*i/3,1.75,c)

    def doc(self,x,y,w,h,c=BLUE):
        d=min(w,h)*.24
        self.path(f"M{x:g},{y:g} H{x+w-d:g} L{x+w:g},{y+d:g} V{y+h:g} H{x:g} Z",mix(c,.08),c,1.4)
        self.poly([(x+w-d,y),(x+w-d,y+d),(x+w,y+d)],c,1.3)
        for i in (1,2,3):
            yy=y+h*(.31+.16*i)
            self.line(x+w*.20,yy,x+w*.80,yy,c,1.15)

    def grid(self,x,y,rows,cols,cell,c=BLUE,flavor="square"):
        for j in range(rows):
            for i in range(cols):
                v=((i*11+j*7)%13)/13
                k=.87 if (i==j or (flavor=="causal" and i==j-1)) else .11+.32*v
                if flavor=="causal" and i>j: k=.04
                self.box(x+i*cell,y+j*cell,cell-1.6,cell-1.6,mix(c,k),"none",.3)

    def charticon(self,x,y,w=42,h=44,c=BLUE):
        for i,f in enumerate((.30,.57,.9)):
            sz=w/4
            self.box(x+sz*i*1.28,y+h-h*f,sz,h*f,mix(c,.37+i*.24),c,.8)
        self.line(x-2,y+h+1,x+w,y+h+1,c,.9)

    def nodeicon(self,x,y,w=78,h=47,c=GREEN):
        levels=[[(x+w*.08,y+h*t) for t in (.20,.50,.80)],
                [(x+w*.53,y+h*t) for t in (.12,.39,.63,.89)],
                [(x+w*.93,y+h*.50)]]
        for src,dest in zip(levels,levels[1:]):
            for X,Y in src:
                for xx,yy in dest:
                    self.line(X,Y,xx,yy,mix(c,.55),.8)
        for j,g in enumerate(levels):
            for X,Y in g:
                self.dot(X,Y,4.4,mix(c,.19+j*.12),c,.9)

    def tree(self,x,y,w=160,h=63,c=BLUE):
        xs=[x+w*f for f in (.19,.50,.81)]
        self.line(xs[0],y+h*.39,xs[2],y+h*.39,c,.9)
        self.line(xs[1],y+h*.12,xs[1],y+h*.56,c,.9)
        self.dot(xs[1],y+h*.12,5,c)
        for X,k in zip(xs,(BLUE,GREEN,ORANGE)):
            self.line(X,y+h*.39,X,y+h*.77,k,1)
            self.dot(X,y+h*.55,4.8,mix(k,.68),k)
            self.line(X-w*.075,y+h*.77,X+w*.075,y+h*.77,k,1)
            for q in (-1,1):
                v=X+q*w*.075
                self.line(v,y+h*.77,v,y+h*.93,k,1)
                self.dot(v,y+h*.93,3.5,mix(k,.28),k)

    def write(self,n):
        target=OUT/"SVG"/f"Figure{n}.svg"
        target.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">\n'+"\n".join(self.el)+"\n</svg>\n",encoding="utf-8")
        return target

def fig1():
    # Reconstructed on the exact 1448 x 1086 reference canvas.
    navy="#000035"; blue="#2a73b9"; green="#608865"; purple="#814d71"; orange="#f2673e"
    soft_blue="#dfedf7"; soft_green="#e4eedf"; soft_purple="#f0e5ef"; soft_orange="#fdf0e6"; cream="#fcf5e8"
    s=SVG(1448,1086)
    # title band
    s.line(24,32,322,32,navy,1.5);s.line(1125,32,1423,32,navy,1.5)
    s.text(724,43,"TCM-SD42 Benchmark Workflow",35,700,navy,"middle","Georgia")
    # A
    s.panel(5,70,1438,633,"A")
    s.box(17,78,61,48,navy,"none",8);s.text(47,112,"A",31,700,"#ffffff","middle","Georgia")
    # corpus
    s.box(101,120,194,237,"#ffffff","#aab4c3",1.5,8)
    s.lines(198,157,["Public","TCM-SD","Corpus"],28,31,navy,"middle",700)
    s.database(198,229,78,72,navy)
    s.labelbox(130,309,143,35,"54,152",blue,26)
    # benchmark construction frame
    s.box(324,120,914,238,"#ffffff",navy,1.6,8,True)
    s.box(337,126,888,39,cream,"none",7);s.text(781,154,"Benchmark Construction",25,700,navy,"middle","Georgia")
    # frozen task
    s.box(342,174,232,172,"#ffffff",navy,7,1.3,True)
    s.text(458,201,"Frozen Task",22,700,navy,"middle","Georgia")
    cells=[blue,blue,"#60a0d0",orange,"#eef0df",green,"#f3ceb9","#d9e3db"]
    for j,c in enumerate(cells):s.box(378+(j%3)*40,219+(j//3)*29,31,22,c,"none",1)
    s.text(541,244,"…",22,700,navy)
    s.labelbox(386,302,150,34,"42 Classes",blue,19)
    # frozen partitions
    s.box(590,174,289,172,"#ffffff",navy,7,1.3,True)
    s.text(735,201,"Frozen Partitions",22,700,navy,"middle","Georgia")
    for j,(lab,val) in enumerate((("Train","4,186"),("Dev","420"),("Source test","4,452"))):
        y=220+j*39;s.box(612,y,142,31,blue,"none",0);s.text(682,y+22,lab,16,700,"#ffffff","middle")
        s.box(754,y,101,31,"#ffffff",navy,1);s.text(804,y+22,val,16,700,navy,"middle")
    # held-out cleaning
    s.box(900,174,330,172,"#ffffff",navy,7,1.3,True)
    s.text(1065,201,"Held-out Cleaning",22,700,navy,"middle","Georgia")
    s.doc(931,236,46,55,navy);s.arrow([(985,264),(1012,264)],navy,2)
    # filter
    s.path("M1022,237 L1076,237 L1056,264 L1056,286 L1043,295 L1043,264 Z",soft_blue,navy,2)
    s.arrow([(1081,264),(1110,264)],navy,2)
    s.labelbox(1115,244,95,40,"4,218",green,20)
    # top arrow down / right
    s.arrow([(1238,236),(1290,236),(1290,389)],navy,2)
    s.arrow([(745,358),(745,389)],navy,2)
    # matched eval
    s.box(40,389,385,298,"#ffffff",navy,8,1.5,True)
    s.box(54,396,357,37,cream,"none",7);s.text(232,422,"Matched Evaluation",23,700,navy,"middle","Georgia")
    s.charticon(105,452,67,50,blue);s.line(199,446,199,499,navy,1.3);s.labelbox(216,449,143,39,"N = 4,218",blue,25)
    s.line(81,516,380,516,navy,1.2)
    for j,t in enumerate(("Accuracy","Macro-F1","Weighted-F1","Balanced Acc.")):
        y=550+j*37;s.box(128,y-10,13,13,blue,"none",1);s.text(173,y,t,20,400,navy)
    # four system
    s.box(472,389,546,298,"#ffffff",navy,8,1.5,True)
    s.box(486,396,518,37,cream,"none",7);s.text(745,422,"Four-System Prediction",23,700,navy,"middle","Georgia")
    s.box(494,452,134,84,soft_blue,navy,8,1.3);s.lines(561,480,["Direct","42-class","index"],20,23,navy,"middle")
    s.box(494,565,134,85,soft_blue,navy,8,1.3);s.lines(561,594,["Frozen","parser","v18"],20,23,navy,"middle")
    # Predictions flow from the model routes back through the frozen parser/index.
    s.arrow([(682,492),(628,492)],navy,1.6);s.arrow([(682,607),(628,607)],navy,1.6)
    s.box(682,440,320,112,"#ffffff",navy,7,1.2,True)
    s.text(842,465,"Discriminative Encoders",18,700,navy,"middle","Georgia")
    s.labelbox(695,474,286,29,"MacBERT",green,20)
    s.labelbox(695,513,286,29,"ZY-BERT",blue,20)
    s.box(682,561,320,112,"#ffffff",navy,7,1.2,True)
    s.text(842,586,"Generative Language Models",18,700,navy,"middle","Georgia")
    s.labelbox(695,595,286,29,"Qwen3-8B",purple,20)
    s.labelbox(695,634,286,29,"InternLM3-8B",orange,20)
    # standardized input
    s.box(1057,389,359,298,"#ffffff",navy,8,1.5,True)
    s.box(1071,396,331,37,cream,"none",7);s.text(1236,422,"Standardized Input",23,700,navy,"middle","Georgia")
    for j,t in enumerate(("Disease","Complaint","Four-diagnostic","Illness summary")):
        y=449+j*34;s.labelbox(1145,y,235,29,t,blue,15)
        if j<3:s.line(1120,y+14,1145,y+14,navy,1.2)
    s.line(1120,463,1120,565,navy,1.2);s.arrow([(1263,589),(1263,581)],navy,1.4)
    s.doc(1236,590,42,42,navy);s.box(1144,652,237,27,"#f3edda","none",6);s.text(1262,671,"input_text",15,700,navy,"middle","Georgia")
    # flow arrows
    s.arrow([(1057,535),(1019,535)],navy,1.7);s.arrow([(472,538),(425,538)],navy,1.7)
    # B
    s.panel(5,724,1438,349,"B")
    s.box(17,732,61,48,navy,"none",8);s.text(47,766,"B",31,700,"#ffffff","middle","Georgia")
    # files
    s.box(42,787,393,253,"#ffffff",navy,8,1.4,True);s.box(54,794,369,37,cream,"none",7);s.text(238,820,"Frozen Prediction Files",23,700,navy,"middle","Georgia")
    s.doc(80,847,45,34,navy);s.text(143,870,"Archived",23,700,navy)
    s.labelbox(84,885,160,35,"MacBERT",green,18);s.labelbox(255,885,160,35,"Qwen3-8B",purple,18)
    s.doc(80,933,45,34,navy);s.text(143,956,"New runs",23,700,navy)
    s.labelbox(84,969,160,35,"ZY-BERT",blue,18);s.labelbox(255,969,160,35,"InternLM3-8B",orange,18)
    # table
    s.box(478,787,555,253,"#ffffff",navy,8,1.4,True);s.box(490,794,531,37,cream,"none",7);s.text(755,820,"Match Predictions by Record ID",23,700,navy,"middle","Georgia")
    headers=["ID","Gold","MacBERT","ZY-BERT","Qwen3-8B","InternLM3-8B"];widths=[64,67,89,89,104,108];x=490
    for k,(h,w) in enumerate(zip(headers,widths)):
        c=[blue,blue,green,blue,purple,orange][k];s.box(x,839,w,36,mix(c,.76),navy,1);s.text(x+w/2,863,h,13,700,navy,"middle");x+=w
    rows=[["0001","17","17","17","17","17"],["0002","03","07","03","03","03"],["0003","28","28","26","28","28"],["…","…","…","…","…","…"]]
    for j,row in enumerate(rows):
        y=875+j*36;x=490
        for k,(v,w) in enumerate(zip(row,widths)):
            s.box(x,y,w,36,"#ffffff",navy,0.7);s.text(x+w/2,y+24,v,15,400,navy,"middle");x+=w
    # paired inference
    s.box(1075,787,365,253,"#ffffff",navy,8,1.4,True);s.box(1087,794,341,37,cream,"none",7);s.text(1257,820,"Paired Inference",23,700,navy,"middle","Georgia")
    s.charticon(1124,862,54,44,blue);s.line(1196,841,1196,922,navy,1.2);s.lines(1306,862,["2,000","paired","bootstrap"],21,25,navy,"middle")
    s.line(1098,946,1417,946,navy,1.2)
    # lower comparison marker stays left of the separator so it cannot cross the label
    s.line(1196,958,1196,1030,navy,1.2)
    s.line(1138,980,1138,1023,navy,1.8);s.line(1106,987,1170,987,navy,1.8);s.dot(1138,987,4,navy,navy,1)
    s.line(1106,987,1098,1002,navy,1.2);s.line(1098,1002,1114,1002,navy,1.2);s.line(1170,987,1162,1002,navy,1.2);s.line(1162,1002,1178,1002,navy,1.2)
    s.text(1306,981,"Six",21,700,navy,"middle");s.text(1306,1007,"paired comparisons",18,400,navy,"middle")
    s.arrow([(435,915),(478,915)],navy,1.7);s.arrow([(1033,915),(1075,915)],navy,1.7)
    return s

def fig2():
    navy="#0a1d55"; blue="#195b9b"; green="#4e8f6b"; orange="#d8782e"; purple="#814d71"; pale_blue="#e5eef9"; pale_green="#e7f0df"; pale_orange="#f8e8d8"; pale_red="#f7e6d9"; cream="#f8f2e7"
    s=SVG(1672,941)
    # A outer plate
    s.panel(8,13,1656,539,"A")
    s.box(18,20,48,48,navy,"none",8);s.text(42,54,"A",31,700,"#ffffff","middle","Georgia")
    # top modules
    s.box(91,41,375,199,"#ffffff",navy,9,1.5,True);s.box(132,25,291,37,"#dce4f2","none",18);s.text(278,51,"TCM-SD records",25,700,navy,"middle","Georgia")
    s.database(166,92,98,86,blue);s.path("M178,147 C199,131 223,138 232,159 C214,157 201,168 188,182 C187,165 184,155 178,147 Z","#dcebf6",blue,1.2);s.text(292,125,"54,152",37,700,navy);s.text(292,165,"records",23,700,navy)
    s.arrow([(468,140),(501,140)],navy,2.2)
    s.box(506,41,374,199,"#ffffff",navy,9,1.5,True);s.box(548,25,291,37,"#dce4f2","none",18);s.text(694,51,"Four examinations",25,700,navy,"middle","Georgia")
    for i,(lab,c) in enumerate((("Inspection",orange),("Inquiry",orange),("Palpation",orange),("Auscultation & Olfaction",orange))):
        x=535+(i%2)*182;y=68+(i//2)*80;s.box(x,y,169,67,pale_orange,"none",10)
        if i==0:
            s.ellipse if False else None
            s.path(f"M{x+53},{y+28} C{x+70},{y-1} {x+113},{y-1} {x+132},{y+28} C{x+113},{y+53} {x+70},{y+53} {x+53},{y+28} Z","none",c,2)
            s.dot(x+93,y+28,10,"#ffffff",c,2);s.dot(x+93,y+28,3,c)
        elif i==1:
            s.path(f"M{x+62},{y+10} H{x+92} C{x+95},{y+10} {x+97},{y+12} {x+97},{y+15} V{y+30} C{x+97},{y+33} {x+95},{y+35} {x+92},{y+35} H{x+73} L{x+64},{y+43} V{y+35} H{x+62} C{x+59},{y+35} {x+57},{y+33} {x+57},{y+30} V{y+15} C{x+57},{y+12} {x+59},{y+10} {x+62},{y+10} Z","#ffffff",c,2)
            for dx in (x+69,x+77,x+85):
                s.dot(dx,y+22.5,2.0,c)
            s.path(f"M{x+99},{y+17} H{x+107} C{x+110},{y+17} {x+112},{y+19} {x+112},{y+22} V{y+35} C{x+112},{y+38} {x+110},{y+40} {x+107},{y+40} H{x+105} V{y+45} L{x+98},{y+40} H{x+83} C{x+80},{y+40} {x+78},{y+38} {x+78},{y+36}","none",c,1.8)
        elif i==2:
            s.path(f"M{x+63},{y+46} C{x+70},{y+21} {x+83},{y+29} {x+87},{y+17} L{x+94},{y+6} L{x+101},{y+20} L{x+112},{y+9} L{x+119},{y+22} L{x+131},{y+27} C{x+119},{y+47} {x+91},{y+55} {x+63},{y+46} Z","none",c,2)
        else:
            s.path(f"M{x+87},{y+10} C{x+111},{y+14} {x+108},{y+28} {x+99},{y+36} L{x+96},{y+56} L{x+80},{y+56} L{x+87},{y+35} C{x+69},{y+29} {x+69},{y+18} {x+87},{y+10} Z","none",c,2)
        s.text(x+84,y+59,lab,12.5,700,navy,"middle")
    s.arrow([(883,140),(918,140)],navy,2.2)
    s.box(945,41,354,199,"#ffffff",navy,9,1.5,True);s.box(968,25,307,37,"#dce4f2","none",18);s.text(1121,51,"Class-support filter",25,700,navy,"middle","Georgia")
    for i,(lab,c,fill) in enumerate((("Train ≥ 100",blue,pale_blue),("Dev ≥ 10",green,pale_green),("Test ≥ 10",orange,pale_orange))):
        y=70+i*44;s.box(974,y,297,39,fill,"none",10)
        s.path(f"M990,{y+10} H1024 L1013,{y+24} V{y+31} L1006,{y+36} V{y+24} Z","none",c,1.8)
        s.text(1125,y+28,lab,20,700,navy,"middle")
    s.arrow([(1302,140),(1334,140)],navy,2.2)
    s.box(1338,41,292,199,"#ffffff",navy,9,1.5,True);s.box(1361,25,246,37,"#dce4f2","none",18);s.text(1484,51,"Eligible forms",25,700,navy,"middle","Georgia")
    s.text(1467,113,"43",48,700,navy,"middle")
    for j,h in enumerate((115,88,72,60,49,41,33,27,21,17)):
        s.box(1380+j*22,217-h,14,h,blue,"none",1)
    s.text(1587,178,"…",26,700,navy)
    # connector
    # The lower panels describe a retrospective reconstruction and audit path.
    s.line(347,273,1495,273,navy,1.5,True);s.line(347,273,347,307,navy,1.5,True);s.arrow([(862,273),(862,306)],navy,1.8);s.line(1495,273,1495,241,navy,1.5,True);s.text(1160,266,"retrospective audit path",12,400,navy,"middle")
    # lower A
    s.box(91,311,550,208,"#ffffff",navy,9,1.5,True);s.box(194,295,347,37,"#dce4f2","none",18);s.text(368,321,"Suffix normalization",25,700,navy,"middle","Georgia")
    s.labelbox(151,366,132,39,"证候后缀",blue,17);s.arrow([(289,385),(323,385)],navy,1.8);s.labelbox(336,366,55,39,"证",orange,18);s.arrow([(399,385),(430,385)],navy,1.8);s.labelbox(443,366,151,39,"后缀规范",orange,17)
    for j,(x,y) in enumerate(((206,436),(319,436),(206,494),(319,494))):
        s.dot(x,y,14,blue if j<2 else "#f5b46e",navy,1.5)
    s.line(206,451,206,480,navy,1);s.line(319,451,319,480,navy,1);s.text(249,443,"…",20,700,navy,"middle");s.text(249,501,"…",20,700,navy,"middle")
    s.lines(428,438,["41 one-to-one", "+ 1 collision (2→1)", "= 42 frozen labels"],16,19,navy,"start",700)
    s.arrow([(707,414),(641,414)],navy,2)
    s.box(704,311,372,208,"#ffffff",navy,9,1.5,True);s.box(757,295,267,37,"#dce4f2","none",18);s.text(890,321,"Frozen labels",25,700,navy,"middle","Georgia")
    s.text(889,386,"42",48,700,navy,"middle")
    for j in range(42):s.dot(782+(j%7)*32,403+(j//7)*17,7,blue,navy,.5)
    s.text(890,503,"…",22,700,navy,"middle")
    # The official 148-class taxonomy is contextual reference evidence, not a direct parent of the frozen labels.
    s.line(1113,414,1078,414,navy,1.2,True)
    s.box(1114,311,465,208,"#ffffff",navy,9,1.5,True);s.box(1170,295,355,37,"#dce4f2","none",18);s.text(1347,321,"Reference taxonomy (context)",22,700,navy,"middle","Georgia")
    s.text(1347,382,"148 classes",39,700,navy,"middle");s.text(1347,510,"reference only",12,400,navy,"middle")
    # taxonomy tree
    s.dot(1347,404,10,blue,navy,1.2);s.line(1347,414,1347,430,navy,1.2);s.line(1265,430,1428,430,navy,1.2)
    for i,(x,c) in enumerate(((1265,blue),(1347,green),(1428,orange))):
        s.dot(x,450,10,c,navy,1.2);s.line(x,460,x,469,navy,1.2);s.line(x-35,469,x+35,469,navy,1)
        for q in (-35,0,35):s.dot(x+q,481,7,pale_blue if c==blue else pale_green if c==green else pale_orange,navy,.9);s.line(x+q,469,x+q,474,navy,1)
    # B
    s.panel(8,567,1656,361,"B");s.box(18,576,48,48,navy,"none",8);s.text(42,610,"B",31,700,"#ffffff","middle","Georgia")
    s.box(72,593,1530,100,"#ffffff",navy,9,1.5,True);s.text(99,631,"Public normalization map",19,700,navy);s.text(99,657,"(548 entries)",19,700,navy)
    x=431
    for count,c,label,pct in ((246,green,"KEEP","44.9%"),(187,blue,"MERGE","34.1%"),(114,orange,"DELETE","20.8%"),(1,purple,"SUB_MERGE","0.2%")):
        w=936*count/548;s.box(x,605,w,56,c,"none")
        if count>1:
            s.text(x+w/2,630,f"{count} ({pct})",16,700,"#ffffff","middle");s.text(x+w/2,652,label,16,700,"#ffffff","middle")
        x+=w
    for p in (0,20,40,60,80,100):
        xx=431+p*9.36;s.line(xx,664,xx,674,navy,1);s.text(xx,686,f"{p}%",12,400,navy,"middle")
    s.box(1363,605,7,56,purple,"none");s.line(1367,611,1420,596,navy,1.2);s.text(1430,632,"1 (0.2%)",17,700,navy);s.text(1430,654,"SUB_MERGE",16,700,navy)
    # bottom B modules
    s.box(39,728,469,181,"#ffffff",navy,9,1.5,True);s.box(133,712,282,37,"#dce4f2","none",18);s.text(274,738,"Frozen labels (42)",23,700,navy,"middle")
    s.box(72,766,56,95,"#dfeaf8",navy,4);s.text(100,823,"标",25,700,navy,"middle","Noto Sans CJK SC")
    for j in range(42):s.dot(204+(j%6)*24,772+(j//6)*20,6,blue,navy,.4)
    s.line(354,774,354,859,navy,1.5);s.text(369,799,"38 KEEP",15,700,navy);s.dot(460,796,7,navy);s.text(369,838,"4 MERGE",15,700,navy);s.dot(460,835,7,"#79a9e0",navy)
    s.arrow([(510,819),(542,819)],navy,2)
    s.box(550,728,630,181,"#ffffff",navy,9,1.5,True);s.box(641,712,448,37,"#dce4f2","none",18);s.text(865,738,"Mapping and conflict resolution",23,700,navy,"middle")
    s.labelbox(565,765,160,44,"2 MERGE → existing",green,14);s.labelbox(565,827,160,44,"2 MERGE → outside",blue,14)
    for j,y in enumerate((768,793,818,843)):
        s.dot(748,y,8,green if j<3 else blue,navy,1)
        for q,yy in enumerate((768,793,818,843)):s.path(f"M756,{y} C830,{y} 873,{yy} 932,{yy}","none",mix(green if j<3 else blue,.55),2)
    for y,c in zip((768,793,818,843),(navy,navy,"#81b0dd","#81b0dd")):s.dot(940,y,8,c,navy,1)
    s.text(1001,793,"2 collisions",17,700,navy);s.text(1001,842,"2 outside",17,700,navy)
    s.arrow([(1180,819),(1210,819)],navy,2)
    s.box(1214,728,419,181,"#ffffff",navy,9,1.5,True);s.box(1267,712,315,37,"#dce4f2","none",18);s.text(1424,738,"Normalized categories",23,700,navy,"middle")
    s.text(1281,820,"40",40,700,navy);s.text(1280,846,"distinct",16,700,navy);s.text(1280,865,"categories",16,700,navy)
    s.dot(1508,770,10,blue,navy,1);s.line(1508,780,1508,800,navy,1.2);s.line(1455,800,1560,800,navy,1.2)
    for x,c in ((1455,blue),(1508,green),(1560,orange)):
        s.dot(x,819,10,c,navy,1);s.line(x,829,x,841,navy,1)
        for q in (-22,0,22):s.dot(x+q,850,7,pale_blue if c==blue else pale_green if c==green else pale_orange,navy,.8)
    return s

def fig3():
    navy="#000035"; blue="#2a73b9"; green="#4e7648"; orange="#c44f2f"; pale="#eef2f8"; cream="#f8f2e7"; gray="#e9e5df"
    s=SVG(1254,1254)
    def frame(y,h): s.box(18,y,1218,h,"#ffffff",navy,8,1.7)
    # top frozen cohort
    frame(39,200)
    s.database(96,72,72,98,navy);s.text(211,132,"54,152",43,700,navy);s.text(217,161,"records",24,400,navy);s.text(153,222,"Raw corpus",23,700,navy)
    s.arrow([(357,133),(398,133)],navy,2)
    for j in range(42):
        x=415+(j%7)*23;y=70+(j//7)*21;c=blue if (j%9 in (0,5)) else "#ffffff"
        s.box(x,y,17,17,c,blue,0,1.2)
    s.text(590,135,"42",43,700,navy);s.text(594,163,"classes",22,400,navy);s.text(466,222,"Frozen task",24,700,navy,"middle")
    s.arrow([(665,133),(707,133)],navy,2)
    for j,(lab,val,c) in enumerate((("Training","4,186",blue),("Development","420",green),("Source test","4,452",blue))):
        y=71+j*47;s.text(715,y+14,lab,19,400,navy);s.box(842,y,277,22,gray,"none",2);s.box(842,y,277*float(val.replace(",",""))/4452,22,c,"none",2);s.text(1198,y+18,val,25,700,navy,"end")
    s.text(943,222,"Frozen splits",23,700,navy,"middle")
    s.arrow([(627,243),(627,273)],navy,2.2)
    # exact screening
    frame(278,203)
    s.line(92,302,92,437,navy,1.5);s.text(137,351,"4,452",43,700,navy);s.text(137,378,"record IDs",22,400,navy)
    for j,w in enumerate((159,136,112,87)):s.line(138,391+j*14,138+w,391+j*14,navy,2)
    s.text(151,463,"Source pool",22,700,navy);s.arrow([(328,368),(368,368)],navy,2)
    for j,label in enumerate(("h(a)","h(b)")):
        y=331+j*67;s.text(388,y+18,label,24,700,navy,"middle","Georgia")
        for k,c in enumerate((navy,blue,blue,"#f4eee0",green,blue,blue,orange,navy,blue,blue,green)):
            s.box(457+k*23,y,19,28,c,"none",1)
    s.text(609,463,"SHA-256 hashes",23,700,navy,"middle")
    s.text(782,373,"=",31,700,navy,"middle");s.box(820,321,119,83,"#eef3e6",green,10,2);s.lines(879,351,["Exact","match"],21,24,navy,"middle")
    s.arrow([(965,368),(1008,368)],navy,2);s.text(1040,391,"6",59,700,orange);s.text(1091,384,"excluded",25,400,navy);s.text(1003,463,"Exact duplicates",22,700,navy,"middle")
    s.arrow([(627,482),(627,514)],navy,2.2)
    # near duplicate
    frame(518,210)
    s.line(92,545,92,679,navy,1.5)
    for j,label in enumerate(("v₁","v₂")):
        y=568+j*64;s.text(145,y+19,label,24,700,navy,"middle","Georgia")
        for k in range(11):s.box(177+k*27,y,22,28,blue if k in (0,5,8) else "#f8fafc",blue,0,1.1)
    s.text(318,705,"TF-IDF vectors",23,700,navy,"middle");s.text(514,603,"…",23,700,navy,"middle");s.arrow([(563,603),(603,603)],navy,2)
    # cosine plot
    s.arrow([(666,657),(886,657)],navy,1.5);s.arrow([(666,657),(666,545)],navy,1.5)
    s.arrow([(666,657),(788,553)],blue,2.6);s.arrow([(666,657),(820,578)],orange,2.6);s.path("M706,657 A40,40 0 0 1 722,632","none",navy,1.2);s.text(727,640,"θ",18,700,navy)
    s.text(783,550,"COSINE ≥ 0.95",21,700,navy);s.text(783,705,"Cosine similarity",19,400,navy,"middle")
    s.arrow([(920,603),(963,603)],navy,2);s.text(1006,604,"228",59,700,orange);s.text(1007,636,"additional",22,400,navy);s.text(1007,663,"exclusions",22,400,navy);s.text(1002,705,"Near duplicates",22,700,navy)
    s.arrow([(627,730),(627,759)],navy,2.2)
    # summary
    frame(763,176)
    s.line(92,789,92,908,navy,1.5);s.text(136,837,"4,452",43,700,navy);s.text(142,866,"source-test records",20,400,navy);s.text(151,913,"Source test",22,700,navy)
    total_screened=4452; retained_count=4218; near_count=228; exact_count=6; bar_w=548
    retained_w=bar_w*retained_count/total_screened; near_w=bar_w*near_count/total_screened; exact_w=bar_w*exact_count/total_screened
    exact_col=blue
    s.box(363,799,retained_w,57,green,"none");s.box(363+retained_w,799,near_w,57,"#ba4e2c","none");s.box(363+retained_w+near_w,799,exact_w,57,exact_col,"none");s.text(363+retained_w/2,837,"4,218 retained",26,700,"#ffffff","middle")
    ex_mid=363+retained_w+near_w+exact_w/2
    s.line(ex_mid,798,ex_mid,784,exact_col,1.4);s.text(ex_mid,780,"6",13,700,exact_col,"middle")
    for x,c,t in ((394,green,"Retained"),(580,"#ba4e2c","Near 228"),(801,exact_col,"Exact 6")):
        s.box(x,870,27,19,c,"none");s.text(x+39,887,t,18,400,navy)
    s.text(635,914,"Exclusion summary",22,700,navy,"middle");s.arrow([(930,827),(972,827)],navy,2);s.text(1007,805,"4,452 − 6 − 228",19,400,navy);s.text(1008,869,"4,218",55,700,green);s.text(1010,903,"Clean held-out",23,700,navy)
    s.arrow([(627,945),(627,974)],navy,2.2)
    # overlap audit
    frame(979,241)
    s.line(87,1008,87,1168,navy,1.5);s.text(136,1030,"Train",21,400,navy);s.text(225,1030,"Dev",21,400,navy)
    audit_targets=(1096,1070,1152,1116,1172)
    for j in range(5):
        yy=1060+j*28;s.dot(140,yy,8,"#ffffff",blue,2);s.dot(249,yy,8,"#ffffff",green,2);s.line(148,yy,241,audit_targets[j],(orange if j in (1,3) else blue),1.6)
    s.text(175,1204,"Overlap audit",21,700,navy,"middle")
    s.text(319,1072,"54 / 420 flagged",23,700,"#9c3827");s.text(329,1106,"18 exact among 54",18,400,navy);s.box(323,1123,215,39,"#e3ead8","none",3);s.text(431,1152,"366 remaining",22,700,"#3d6b39","middle");s.text(427,1204,"Flagged cases",21,700,navy,"middle")
    s.line(590,1005,590,1171,navy,1.5);s.text(864,1011,"ZY-BERT / DEV MACRO-F1",19,700,navy,"middle");s.text(1147,1010,"Δ −0.0314 (−3.9%)",17,700,"#c34f34","end")
    x0,x1,y0,y1=678,1165,1136,1038
    for v in (.74,.76,.78,.80,.82): yy=y0-(v-.74)/.08*(y0-y1);s.line(x0,yy,x1,yy,"#dbe0ea",1);s.text(x0-10,yy+4,f"{v:.2f}",13,400,navy,"end")
    s.line(x0,y0,x0,y1,navy,1.3);s.line(x0,y0,x1,y0,navy,1.3)
    macro_y=lambda value: y0-(value-.74)/.08*(y0-y1)
    p1=(799,macro_y(.8056));p2=(1036,macro_y(.7742));s.poly([p1,p2],navy,1.7);s.dot(*p1,9,blue,navy,1.4);s.dot(*p2,9,orange,navy,1.4);s.text(p1[0],p1[1]-16,"0.8056",20,700,navy,"middle");s.text(p2[0],p2[1]-16,"0.7742",20,700,navy,"middle");s.text(799,1170,"Original",18,400,navy,"middle");s.text(1036,1170,"After removal",18,400,navy,"middle");s.text(918,1204,"Macro-F1 sensitivity",22,700,navy,"middle")
    return s

def fig4():
    navy="#14365e"; blue="#1e4e8c"; green="#497458"; orange="#ec7955"; brown="#bd5838"
    pale_blue="#cde0ef"; pale_green="#e5eee3"; pale_orange="#f2d2c2"; cream="#f5f0e5"; pale_lilac="#c9c5da"
    s=SVG(1450,1086)
    base_text=s.text
    def text4(x,y,label,size=16,weight=400,c=INK,a="start",family="Georgia",rotate=None):
        fam="Noto Sans CJK SC" if re.search("[\u3000-\u9fff]",str(label)) else family
        return base_text(x,y,label,size,weight,c,a,fam,rotate=rotate)
    s.text=text4
    # Layout follows the supplied 1448 x 1086 reference plate at 1:1 scale.
    s.panel(7,30,1436,555,"A")
    s.box(17,30,61,48,navy,"none",8);s.text(47,64,"A",31,700,"#ffffff","middle")
    s.box(27,91,1398,234,"#ffffff",navy,9,1.5,True)
    s.box(27,344,1398,227,"#ffffff",navy,9,1.5,True)

    def model_card(x,y,w,h,name,c,zy=False):
        s.box(x,y,w,h,mix(c,.035),c,9,1.3)
        if not zy:
            bx,by,bw,bh=x+28,y+3,160,118
            s.box(bx,by,bw,bh,"#ffffff",c,8,1.4)
            s.path(f"M{bx+12},{by+17} C{bx+48},{by-5} {bx+114},{by-5} {bx+148},{by+17}","none",c,2.2)
            s.path(f"M{bx+12},{by+101} C{bx+50},{by+121} {bx+113},{by+121} {bx+148},{by+101}","none",c,2.2)
            xs=[bx+20,bx+61,bx+102,bx+143]; ys=[by+32,by+61,by+90]
            for j in range(3):
                for yy in ys:
                    for zz in ys:s.line(xs[j],yy,xs[j+1],zz,mix(c,.48),1.05)
            for j,xx in enumerate(xs):
                for i,yy in enumerate(ys):s.dot(xx,yy,8.3,pale_green if i in (0,2) else mix(c,.72),c,1.35)
            s.box(x+10,y+h-43,w-20,33,c,"none",7);s.text(x+w/2,y+h-20,name,21,700,"#ffffff","middle")
        else:
            cx,cy=x+106,y+64
            for xx,yy,lab in ((x+61,y+33,"望"),(x+153,y+33,"闻"),(x+61,y+96,"问"),(x+153,y+96,"切")):
                s.dot(xx,yy,18,pale_blue,c,1.8);s.text(xx,yy+6,lab,16,700,c,"middle")
            s.dot(cx,cy,23,c,c,1.4);s.text(cx,cy+7,"证",18,700,"#ffffff","middle")
            for xx,yy in ((x+61,y+51),(x+106,y+42),(x+106,y+85),(x+153,y+51)):s.line(cx,cy,xx,yy,mix(c,.7),1.0)
            s.box(x+10,y+h-43,w-20,33,c,"none",7);s.text(x+w/2,y+h-20,name,21,700,"#ffffff","middle")

    model_card(45,128,213,177,"MacBERT",green)
    model_card(45,370,214,177,"ZY-BERT",blue,True)

    def encoder(x,y,w,h,kind,c):
        s.box(x,y,w,h,"#ffffff",navy,9,1.4,True)
        s.box(x+20,y+14,76,36,pale_blue,c,5);s.text(x+58,y+40,"[CLS]",18,700,navy,"middle")
        for j in range(3):s.box(x+22,y+58+j*28,74,21,pale_blue,c if j==0 else "none",4)
        s.text(x+59,y+92,"…",21,700,navy,"middle")
        s.arrow([(x+98,y+88),(x+121,y+88)],navy,1.4)
        if kind=="mac":
            for j,xx in enumerate((x+125,x+255,x+385)):
                s.box(xx,y+28,86,105,pale_blue,navy,7,1.2)
                s.box(xx+10,y+43,66,30,mix(blue,.17),blue,5);s.text(xx+43,y+65,"Attn",16,700,navy,"middle")
                s.box(xx+10,y+82,66,30,cream,navy,5);s.text(xx+43,y+104,"FFN",16,700,navy,"middle")
                if j<2:s.arrow([(xx+86,y+81),(xx+116,y+81)],navy,1.1)
            s.text(x+w/2,y+h+26,"Bidirectional encoder",20,700,navy,"middle")
        else:
            # ZY-BERT is represented as a bidirectional encoder, so its attention map is not causal.
            s.grid(x+124,y+30,7,7,14,blue,"square")
            for j in range(5):
                xx=x+319+j*37;s.box(xx,y+42,26,86,pale_blue,blue,3)
                s.box(xx+5,y+48,16,18,mix(blue,.12),blue,1);s.line(xx+6,y+72,xx+20,y+72,blue,1);s.line(xx+6,y+80,xx+20,y+80,blue,1)
            s.text(x+w/2,y+h+26,"TCM-domain encoder",20,700,navy,"middle")

    encoder(299,103,525,177,"mac",green)
    encoder(300,355,525,175,"zy",blue)

    # MacBERT historical predictions and fixed 42-class index.
    s.arrow([(824,198),(866,198)],navy,1.9)
    s.database(910,145,75,76,green)
    s.dot(952,198,24,green,"#ffffff",1.1);s.line(952,181,952,215,"#ffffff",1.5);s.line(937,189,967,207,"#ffffff",1.5);s.line(937,207,967,189,"#ffffff",1.5)
    s.box(988,123,157,156,"#ffffff",green,8,1.3)
    s.text(1066,153,"Historical",19,700,navy,"middle");s.text(1066,177,"predictions",19,700,navy,"middle")
    s.line(1003,201,1129,201,"#cfd8cf",1);s.line(1003,227,1129,227,"#cfd8cf",1)
    s.text(1003,197,"#0001",15,400,navy);s.text(1123,197,"…",15,700,navy,"end");s.text(1003,223,"#0002",15,400,navy);s.text(1123,223,"…",15,700,navy,"end");s.text(1066,253,"…",19,700,navy,"middle")
    s.arrow([(1146,198),(1185,198)],navy,1.9)
    ix,iy,iw,ih=1197,105,219,191
    s.box(ix,iy,iw,ih,"#ffffff",green,8,1.2);s.box(ix,iy,iw,43,green,"none",8);s.text(ix+iw/2,iy+29,"42-class index",17,700,"#ffffff","middle")
    for j,(num,lab) in enumerate((("1","Class-01"),("2","Class-02"),("3","Class-03"),("…",""),("42","Class-42"))):
        yy=153+j*29;s.box(ix+10,yy,iw-20,23,cream,"none",5)
        if j!=3:
            s.box(ix+14,yy+2,34,19,green,"none",4);s.text(ix+31,yy+16,num,12,700,"#ffffff","middle");s.text(ix+132,yy+16,lab,12.5,700,navy,"middle")
        else:s.text(ix+iw/2,yy+16,"…",16,700,navy,"middle")

    # ZY-BERT fine-tuned head and ranked output.
    s.arrow([(825,443),(866,443)],navy,1.9)
    hx,hy=892,378
    lv=[[(hx,hy),(hx,hy+43),(hx,hy+86)],[(hx+82,hy),(hx+82,hy+43),(hx+82,hy+86)],[(hx+165,hy+43)]]
    for src,dst in zip(lv,lv[1:]):
        for a in src:
            for b in dst:s.line(a[0],a[1],b[0],b[1],navy,1.2)
    for li,items in enumerate(lv):
        for xx,yy in items:s.dot(xx,yy,17,blue if li==0 else pale_green if li==1 else pale_orange,navy,1.4)
    s.text(hx+82,hy+144,"Fine-tuned head",20,700,navy,"middle")
    s.arrow([(1057,443),(1128,443)],navy,1.9)
    ox,oy,ow,oh=1143,360,271,180
    s.box(ox,oy,ow,oh,"#ffffff",blue,8,1.3);s.box(ox,oy,ow,41,pale_blue,"none",8);s.text(ox+ow/2,oy+28,"42-class output",18,700,navy,"middle")
    for j,(lab,val) in enumerate((("Class-07","0.86"),("Class-12","0.06"),("Class-29","0.03"),("…",""),("Class-42","0.01"))):
        yy=415+j*25;s.text(ox+18,yy,lab,14,700,navy);s.text(ox+166,yy,val,14,700,navy,"end")
        s.box(ox+174,yy-12,79,13,mix(blue,.18),blue,2)
        if val:s.box(ox+174,yy-12,79*float(val),13,blue,"none",2)

    # Section B: two separate dashed process rows, matching the source layout.
    s.panel(7,600,1436,473,"B")
    s.box(17,600,61,48,navy,"none",8);s.text(47,634,"B",31,700,"#ffffff","middle")
    s.box(27,649,1398,190,"#ffffff",navy,9,1.5,True)
    s.box(27,858,1398,198,"#ffffff",navy,9,1.5,True)
    def parser_chip(x,y,c,report=False):
        if report:
            s.path(f"M{x},{y+10} L{x+18},{y} H{x+73} V{y+72} H{x} Z", "#ffffff", c, 1.6);s.poly([(x+55,y),(x+55,y+15),(x+73,y+15)],c,1.4)
            s.box(x+11,y+18,18,18,orange,"none",3);s.line(x+15,y+27,x+25,y+27,"#ffffff",2);s.line(x+20,y+22,x+20,y+32,"#ffffff",2)
            s.text(x+45,y+33,"Syndrome label",11.5,700,navy);s.text(x+45,y+58,"Rationale",11.5,700,navy)
        else:
            s.box(x,y,74,70,"#ffffff",c,8,1.5)
            for q in (10,25,40,55):s.line(x-8,y+q,x,y+q,c,1.7);s.line(x+74,y+q,x+82,y+q,c,1.7)
            s.text(x+37,y+36,"Parser",14,700,navy,"middle");s.text(x+37,y+54,"v18",14,700,navy,"middle")
    def decoder_row(y,name,c,kind):
        # input feature grid / activation strip
        s.box(43,y+9,208,175 if kind=="qwen" else 178,"#ffffff",c,7,1.2)
        if kind=="qwen":
            s.grid(80,y+14,7,8,11,c,"causal")
            s.line(80,y+99,214,y+99,c,1.2)
            for xx in (98,144,190):s.dot(xx,y+99,4.5,c,"#ffffff",1)
            s.arrow([(212,y+99),(224,y+99)],c,1.1)
        else:
            for q in range(10):s.box(76+q*13,y+16,10,55,mix(c,.22+.06*q),c,2)
            s.line(76,y+88,203,y+88,c,1.2);s.arrow([(203,y+88),(222,y+88)],c,1.1)
        s.box(53,y+128,188,33,c,"none",7);s.text(147,y+120,"activation schematic",10.5,400,navy,"middle");s.text(147,y+151,name,16,700,"#ffffff","middle")
        s.arrow([(251,y+98),(272,y+98)],navy,1.8)
        # decoder block
        s.box(278,y+4,440,164,"#ffffff",navy,8,1.3,True)
        strip=pale_lilac if kind=="qwen" else pale_orange
        s.box(408,y-7,199,31,strip,"none",16);s.text(507,y+15,"36 layers" if kind=="qwen" else "48 layers",20,700,navy,"middle")
        if kind=="qwen":
            for gx,n in ((305,4),(448,4),(603,3)):
                for j in range(n):s.box(gx+j*34,y+53,21,61,pale_blue,blue,3)
            s.text(432,y+85,"…",21,700,navy,"middle");s.text(586,y+85,"…",21,700,navy,"middle");s.text(498,y+154,"Causal decoder · NF4",15,700,navy,"middle")
        else:
            for j in range(4):s.box(305+j*30,y+53,21,61,pale_blue,blue,3)
            for j in range(6):s.box(445+j*25,y+53,19,61,pale_orange,orange,3)
            for j in range(2):s.box(623+j*30,y+53,21,61,pale_blue,blue,3)
            s.text(429,y+85,"…",21,700,navy,"middle");s.text(607,y+85,"…",21,700,navy,"middle");s.text(498,y+154,"48-layer decoder",15,700,navy,"middle")
        s.arrow([(718,y+98),(745,y+98)],navy,1.8)
        # adapter
        s.box(747,y+8,143,151,"#ffffff",navy,8,1.2,True);s.text(818,y+34,"QLoRA · r16" if kind=="qwen" else "Active LoRA",16,700,navy,"middle")
        ac=blue if kind=="qwen" else orange
        s.poly([(776,y+53),(855,y+53),(844,y+83),(765,y+83)],ac,1.4,mix(ac,.18),True);s.poly([(776,y+94),(855,y+94),(844,y+124),(765,y+124)],ac,1.4,mix(ac,.18),True)
        s.text(810,y+74,"B",15,700,navy,"middle");s.text(810,y+115,"A",15,700,navy,"middle");s.dot(878,y+89,15,"#ffffff",navy,1.6);s.text(878,y+96,"+",20,700,navy,"middle")
        s.arrow([(890,y+98),(919,y+98)],navy,1.8)
        # generated response/report
        s.box(958,y+8,287,145,"#ffffff",navy if kind=="qwen" else orange,8,1.3)
        if kind=="qwen":
            s.box(968,y+14,260,29,pale_lilac,"none",5)
            s.box(975,y+20,26,21,"#ffffff",navy,4);s.line(981,y+27,995,y+27,navy,1.3);s.line(981,y+32,992,y+32,navy,1.3)
            s.text(1112,y+38,"Generated response",17,700,navy,"middle")
            s.line(976,y+70,988,y+70,navy,1.2);s.line(976,y+105,988,y+105,navy,1.2)
            s.box(1000,y+56,230,24,pale_green,"none",4);s.text(1115,y+73,"Syndrome label",12,700,navy,"middle");s.box(1000,y+91,230,24,pale_blue,"none",4);s.text(1115,y+108,"Rationale",12,700,navy,"middle")
        else:
            s.path(f"M{979},{y+8} H{1220} L{1245},{y+33} V{y+153} H{979} Z","#ffffff",orange,1.5);s.poly([(1220,y+8),(1220,y+33),(1245,y+33)],orange,1.2)
            s.box(990,y+19,22,22,orange,"none",3);s.line(995,y+30,1007,y+30,"#ffffff",2);s.line(1001,y+24,1001,y+36,"#ffffff",2)
            s.text(1115,y+39,"Generated report",17,700,navy,"middle")
            for yy in (y+70,y+105):
                s.box(1000,yy-12,22,22,"#ffffff",orange,3);s.line(1004,yy,1011,yy+6,orange,1.6);s.line(1011,yy+6,1018,yy-5,orange,1.6)
            s.box(1034,y+58,191,24,pale_green,"none",4);s.text(1128,y+75,"Syndrome label",12,700,navy,"middle");s.box(1034,y+93,191,24,pale_orange,"none",4);s.text(1128,y+110,"Rationale",12,700,navy,"middle");s.dot(1003,y+133,3,orange)
        s.arrow([(1246,y+98),(1281,y+98)],navy,1.8);parser_chip(1291,y+62,navy,False)
    decoder_row(655,"Qwen3-8B",brown,"qwen")
    decoder_row(861,"InternLM3-8B",orange,"intern")
    return s

def fig5():
    navy="#142a6b"; blue="#1976c5"; orange="#e35b22"; green="#3c7c4f"; purple="#7c54ad"
    pale="#edf1f7"; panel_fill="#f7f8fb"; grid="#ccd5e3"; ink="#101b45"; cream="#f5f0e5"
    s=SVG(1536,1024)
    base_text=s.text
    def text5(x,y,label,size=16,weight=400,c=INK,a="start",family="Georgia",rotate=None):
        label=str(label)
        has_cjk=bool(re.search("[\\u3000-\\u9fff]",label))
        has_special=any(ord(ch)>127 for ch in label)
        fam="Noto Sans CJK SC" if has_cjk else ("Arial" if has_special else family)
        return base_text(x,y,label,size,400 if has_special else weight,c,a,fam,rotate=rotate)
    s.text=text5
    colors={"ZY-BERT":blue,"InternLM3-8B":orange,"MacBERT":green,"Qwen3-8B":purple}
    short={"ZY-BERT":"ZY","InternLM3-8B":"Intern","MacBERT":"Mac","Qwen3-8B":"Qwen"}
    metrics=csvrows(DATA/"fig5_metrics.csv")
    pairs=csvrows(DATA/"fig5_pairs.csv")
    corrected=csvrows(RES.parent/"audits"/"20261110_ba_reverification"/"results"/"pairwise_balanced_accuracy_bootstrap_seed42_corrected.csv")
    corrected_map={
        "ZY-BERT vs InternLM3": corrected[0],
        "ZY-BERT vs MacBERT": corrected[1],
        "ZY-BERT vs Qwen3": corrected[2],
        "InternLM3 vs MacBERT": corrected[3],
        "InternLM3 vs Qwen3": corrected[4],
        "MacBERT vs Qwen3": corrected[5],
    }
    for row in pairs:
        corr=corrected_map[row["pair"]]
        row["ba_diff"]=f"{float(corr['diff_obs_full_precision'])*100:.2f}"
        row["ba_lo"]=f"{float(corr['ci_lower'])*100:.2f}"
        row["ba_hi"]=f"{float(corr['ci_upper'])*100:.2f}"
    def frame(x,y,w,h,letter,title):
        s.box(x,y,w,h,"#ffffff",navy,10,1.8)
        s.box(x+8,y+8,w-16,35,pale,"none",7)
        s.box(x+12,y+8,45,35,navy,"none",8);s.text(x+34,y+35,letter,24,700,"#ffffff","middle")
        s.text(x+70,y+35,title,22,700,navy)
        s.line(x+12,y+48,x+w-12,y+48,navy,1)
    def subhead(x,y,w,title):
        s.box(x,y,w,31,"#e8ebf2","none",7);s.text(x+w/2,y+23,title,17,700,navy,"middle")
    def icon_doc(x,y,w,h,c):
        s.path(f"M{x},{y} H{x+w-13} L{x+w},{y+13} V{y+h} H{x} Z","#ffffff",c,1.6)
        s.poly([(x+w-13,y),(x+w-13,y+13),(x+w,y+13)],c,1.3)
        for q in (0.40,0.57,0.74): s.line(x+w*.22,y+h*q,x+w*.78,y+h*q,c,1.1)
    def paired_row(x,y,row,metric,c=blue,scale=5.4,x_off=218,max_val=20,show_label=True):
        lab=row["pair"].replace("ZY-BERT","ZY").replace("InternLM3","Intern").replace("MacBERT","Mac").replace("Qwen3","Qwen")
        if show_label:s.text(x,y,lab,14,700,ink)
        if metric=="acc":v,lo,hi=float(row["acc_diff"]),float(row["acc_lo"]),float(row["acc_hi"])
        elif metric=="mf1":v,lo,hi=float(row["mf1_diff"]),float(row["mf1_lo"]),float(row["mf1_hi"])
        else:v,lo,hi=float(row["ba_diff"]),float(row["ba_lo"]),float(row["ba_hi"])
        x0=x+x_off
        s.line(x0-2*scale,y-3,x0+max_val*scale,y-3,"#d7dce6",1)
        s.line(x0+lo*scale,y-3,x0+hi*scale,y-3,c,2.1);s.line(x0+lo*scale,y-8,x0+lo*scale,y+2,c,1.1);s.line(x0+hi*scale,y-8,x0+hi*scale,y+2,c,1.1);s.dot(x0+v*scale,y-3,4.2,c)
        return v,lo,hi
    # A
    frame(8,8,1520,265,"A","Overall model performance & model roles")
    subhead(24,61,182,"Model");
    for x,t in ((284,"Accuracy"),(440,"Macro-F1"),(596,"Weighted-F1"),(752,"Balanced acc.")):
        s.box(x-68,61,136,31,"#e8ebf2","none",7);s.text(x,84,t,16,700,navy,"middle")
    for j,row in enumerate(metrics):
        y=116+j*37; name=row["model"]+""; key={"InternLM3":"InternLM3-8B","Qwen3":"Qwen3-8B"}.get(name,name); c=colors[key]
        s.box(24,y-18,804,30,"#fbfcfe",grid,3);s.box(42,y-9,30,12,c,"none",2)
        # small model-specific pictogram
        if j==0:
            s.box(39,y-13,16,9,c,"none",1);s.box(58,y-13,16,9,c,"none",1);s.box(48,y-23,16,9,c,"none",1)
        elif j==1:s.poly([(42,y-12),(57,y-12),(48,y-4),(64,y-4),(52,y+5),(38,y+5),(50,y-4)],c,1.1,c,True)
        elif j==2:s.line(40,y-4,72,y-4,c,2);s.line(48,y-12,48,y+4,c,2);s.line(64,y-12,64,y+4,c,2)
        else:
            for q in range(5):s.dot(43+q*7,y-3,2.2,c)
        s.text(84,y+4,key,15,700,c)
        vals=(float(row["accuracy"]),float(row["macro_f1"]),float(row["weighted_f1"]),float(row["balanced_accuracy"]))
        xs=(284,440,596,752)
        for k,(v,x) in enumerate(zip(vals,xs)):
            s.box(x-64,y-8,66,11,"#f0eee9","none",2);s.box(x-64,y-8,66*v/100,11,c,"none",2)
            s.text(x+60,y+5,f"{v:.2f}",14,700,ink,"end")
    # architecture cards
    subhead(862,61,644,"Model role key")
    cards=[("ZY-BERT","TCM Encoder",blue),("InternLM3-8B","Decoder",orange),("MacBERT","Encoder",green),("Qwen3-8B","Causal Attn",purple)]
    for j,(name,typ,c) in enumerate(cards):
        x=868+j*157; s.box(x,95,147,145,"#ffffff",c,8,1.3);s.box(x+3,98,141,35,mix(c,.08),c,6);s.text(x+73,y_name:=122,name,15,700,c,"middle");s.text(x+73,144,typ,12.5,700,navy,"middle")
        role_icon=["TCM encoder","Generative decoder","Bidirectional encoder","Causal decoder"][j]
        s.box(x+18,158,111,39,mix(c,.08),c,7,1.1)
        if j in (0,3):
            s.grid(x+28,166,4,4,9,c,"square" if j==0 else "causal")
        elif j==1:
            for q in range(3):s.box(x+34,166+q*9,74,6,mix(c,.18),c,2)
        else:
            for q in range(3):s.line(x+37,169+q*9,x+108,169+q*9,mix(c,.45),1);s.dot(x+37,169+q*9,3,pale,c,1);s.dot(x+108,169+q*9,3,pale,c,1)
        s.text(x+73,218,role_icon,10.5,700,c,"middle")
    # B and C
    frame(8,281,784,273,"B","Paired accuracy differences")
    frame(803,281,725,273,"C","Discordant correct counts")
    # B left paired-record illustration
    s.box(26,336,242,174,"#ffffff",blue,7,1.2,True);s.labelbox(102,329,90,29,"ID: r_i",blue,15)
    icon_doc(42,374,75,75,blue);icon_doc(174,374,75,75,orange);s.arrow([(118,411),(171,411)],navy,2)
    s.labelbox(71,464,142,29,"Model 1",blue,13);s.arrow([(214,478),(239,478)],navy,1.5);s.dot(248,478,17,"#ffffff",green,2);s.text(248,485,"OK",18,700,green,"middle")
    s.labelbox(71,503,142,29,"Model 2",orange,13);s.arrow([(214,517),(239,517)],navy,1.5);s.dot(248,517,17,"#ffffff",orange,2);s.text(248,524,"x",18,700,orange,"middle")
    s.text(320,351,"Model pair",14,700,navy);s.text(514,351,"Δ pp",14,700,navy,"end");s.text(778,351,"95% paired CI",14,700,navy,"end")
    s.line(538,365,538,524,"#64748b",1.1,True)
    for j,row in enumerate(pairs):
        y=382+j*25;v,lo,hi=paired_row(320,y,row,"acc",blue,5.2,218,20)
        s.text(514,y,f"{v:+.2f}",14,700,navy,"end");s.text(778,y,f"[{lo:.2f}, {hi:.2f}]",13,700,navy,"end")
    s.line(538-2*5.2,524,538+20*5.2,524,navy,1.1)
    for tv in (0,5,10,15,20):
        tx=538+tv*5.2;s.line(tx,524,tx,529,navy,1);s.text(tx,541,str(tv),10,400,ink,"middle")
    # C 2x2 paired discordance schematic and discordance bars
    s.labelbox(914,337,100,24,"Model B",orange,12)
    s.text(935,379,"B correct",10.5,700,navy,"middle");s.text(993,379,"B error",10.5,700,navy,"middle")
    s.box(816,392,26,96,mix(blue,.17),mix(blue,.72),4);s.text(833,440,"Model A",11.5,700,blue,"middle",rotate=-90)
    s.text(901,416,"A correct",10.5,700,navy,"end");s.text(901,468,"A error",10.5,700,navy,"end")
    for rr in range(2):
        for cc in range(2):
            c=((green,orange),(blue,pale))[rr][cc]; lab=("n11","n10","n01","n00")[rr*2+cc]
            s.box(908+cc*58,390+rr*52,54,46,mix(c,.16),c,1.2);s.text(935+cc*58,419+rr*52,lab,15,700,green if (rr,cc)==(0,0) else navy,"middle")
    s.text(964,512,"Discordant: n10 vs n01",10.5,400,MUTED,"middle")
    s.text(1045,351,"Model pair",14,700,navy);s.text(1223,351,"first only",13,700,blue,"end");s.text(1450,351,"second only",13,700,orange,"end")
    for j,row in enumerate(pairs):
        y=386+j*28;lab=row["pair"].replace("ZY-BERT","ZY").replace("InternLM3","Intern").replace("MacBERT","Mac").replace("Qwen3","Qwen");a,b=int(row["mcn_a"]),int(row["mcn_b"]);s.text(1045,y,lab,13.5,700,ink);s.text(1223,y,str(a),13,700,blue,"end");s.text(1450,y,str(b),13,700,orange,"end")
        s.line(1235,y-4,1420,y-4,"#d4dbe7",1);s.box(1236,y-10,100*a/900,11,blue,"none",1);s.box(1339,y-10,100*b/900,11,orange,"none",1)
    # D and E
    frame(8,570,744,263,"D","Macro-F1 differences")
    frame(760,570,768,263,"E","Balanced-accuracy differences")
    # D confusion matrix illustration
    s.labelbox(111,616,116,29,"Predicted",blue,13);s.text(169,660,"+     -",15,700,navy,"middle");s.labelbox(34,675,31,92,"Actual",blue,12)
    cells=[("TP",green),("FN",orange),("FP",cream),("TN",pale)]
    for k,(lab,c) in enumerate(cells):
        xx=107+(k%2)*66;yy=673+(k//2)*48;s.box(xx,yy,62,44,mix(c,.18),c,4);s.text(xx+31,yy+27,lab,14,700,navy,"middle")
    s.text(252,635,"Model pair",14,700,navy);s.text(444,635,"Δ (Macro-F1)",14,700,navy,"end");s.text(736,635,"95% paired CI",14,700,navy,"end")
    s.line(470,645,470,801,"#64748b",1.1,True)
    for j,row in enumerate(pairs):
        y=660+j*25;v,lo,hi=paired_row(252,y,row,"mf1",blue,6.2,218,16);s.text(444,y,f"{v:+.2f}",14,700,navy,"end");s.text(736,y,f"[{lo:.2f}, {hi:.2f}]",12.5,700,navy,"end")
    s.line(470-2*6.2,801,470+16*6.2,801,navy,1.1)
    for tv in (-2,0,4,8,12,16):
        tx=470+tv*6.2;s.line(tx,801,tx,806,navy,1);s.text(tx,818,str(tv),10,400,ink,"middle")
    # E balance scale icon and table
    # balanced-accuracy icon
    s.line(835,637,835,719,navy,2);s.line(800,719,870,719,navy,2);s.line(835,650,835,719,navy,1.6);s.line(800,650,870,650,navy,1.8);s.dot(835,650,5,orange,navy,1.2)
    s.line(800,650,788,682,navy,1.3);s.line(870,650,882,682,navy,1.3)
    s.poly([(776,682),(804,682),(798,695),(782,695)],navy,1.1,"#f2bd62",True);s.poly([(868,682),(896,682),(890,695),(874,695)],navy,1.1,"#f2bd62",True)
    s.labelbox(788,735,150,35,"42 classes\n(equal weight)",blue,13)
    s.text(998,635,"Model pair",14,700,navy);s.text(1190,635,"Δ (Balanced acc.)",14,700,navy,"end");s.text(1513,635,"95% paired CI",14,700,navy,"end")
    s.box(990,660+3*25-15,528,23,mix(orange,.08),orange,3)
    s.line(1216,645,1216,801,"#64748b",1.1,True)
    for j,row in enumerate(pairs):
        y=660+j*25;v,lo,hi=paired_row(998,y,row,"ba",green,6.2,218,16);col=orange if j==3 else green;s.text(1190,y,f"{v:+.2f}",14,700,col,"end");s.text(1513,y,f"[{lo:.2f}, {hi:.2f}]",12.5,700,navy,"end")
    s.line(1216-2*6.2,801,1216+16*6.2,801,navy,1.1)
    for tv in (-2,0,4,8,12,16):
        tx=1216+tv*6.2;s.line(tx,801,tx,806,navy,1);s.text(tx,818,str(tv),10,400,ink,"middle")
    # F bootstrap strip
    frame(8,850,1520,158,"F","Bootstrap 95% CI (paired)")
    icon_doc(22,916,58,60,blue);s.labelbox(92,919,144,40,"D (n = 4,218)",blue,14)
    s.arrow([(236,939),(268,939)],navy,2)
    s.box(272,916,148,46,mix(blue,.17),mix(blue,.72),4);s.lines(346,935,["Resample","(B = 2,000)"],13,16,blue,"middle",700)
    s.arrow([(420,939),(458,939)],navy,2)
    for j,x in enumerate((472,576,680)): icon_doc(x,914,56,65,blue)
    s.text(548,946,"...",25,700,navy,"middle");s.text(652,946,"...",25,700,navy,"middle")
    s.arrow([(744,939),(789,939)],navy,2);s.box(804,900,232,76,mix(blue,.08),"none",10)
    for j,h in enumerate((9,17,26,35,26,17,9)):s.box(839+j*22,968-h,14,h,blue,"none",1)
    s.text(919,918,"Δ(1), ..., Δ(B)",17,700,navy,"middle")
    s.arrow([(1054,939),(1090,939)],navy,2);s.box(1108,900,205,76,mix(blue,.06),"none",10);s.line(1149,939,1263,939,navy,2);s.line(1149,929,1149,949,navy,1.5);s.line(1263,929,1263,949,navy,1.5);s.dot(1206,939,7,navy)
    s.arrow([(1328,939),(1364,939)],navy,2);s.box(1375,913,129,53,mix(blue,.08),blue,7);s.text(1439,934,"Bootstrap 95% CI",12,700,navy,"middle");s.text(1439,953,"(2.5%, 97.5%)",12,700,navy,"middle")
    return s

def fig6():
    navy="#142a6b"; blue="#1769c2"; orange="#e35b22"; green="#3c7c4f"; pale="#eceef3"; grid="#d5dce8"; ink="#101b45"
    s=SVG(1448,1020)
    base_text=s.text
    def text6(x,y,label,size=16,weight=400,c=INK,a="start",family="Georgia",rotate=None):
        label=str(label)
        has_cjk=bool(re.search("[\\u3000-\\u9fff]",label))
        has_special=any(ord(ch)>127 for ch in label)
        fam="Noto Sans CJK SC" if has_cjk else ("Arial" if has_special else family)
        return base_text(x,y,label,size,400 if has_special else weight,c,a,fam,rotate=rotate)
    s.text=text6
    seed=csvrows(DATA/"fig6_seeds.csv")
    ded_raw=csvrows(RES/"dedup_sensitivity_seed42.csv")
    ded_map={}
    for row in ded_raw:
        subset={"S0_full":"S0","S1_raw_dedup":"S1","S2_norm_dedup":"S2"}[row["subset"]]
        pair_sign={"internlm3-vs-macbert":("InternLM3 vs MacBERT",1),"internlm3-vs-qwen3":("InternLM3 vs Qwen3",1),"internlm3-vs-zybert":("ZY-BERT vs InternLM3",-1),"macbert-vs-qwen3":("MacBERT vs Qwen3",1),"macbert-vs-zybert":("ZY-BERT vs MacBERT",-1),"qwen3-vs-zybert":("ZY-BERT vs Qwen3",-1)}[row["pair"]]
        display,sign=pair_sign; ded_map.setdefault(display,{})[subset]=f"{sign*float(row['delta_acc_pp']):.2f}"
    ded=[{"pair":pair,"S0":ded_map[pair]["S0"],"S1":ded_map[pair]["S1"],"S2":ded_map[pair]["S2"]} for pair in ("ZY-BERT vs InternLM3","ZY-BERT vs MacBERT","ZY-BERT vs Qwen3","InternLM3 vs MacBERT","InternLM3 vs Qwen3","MacBERT vs Qwen3")]
    ordinary=csvrows(DATA/"fig5_pairs.csv"); strat=csvrows(RES/"pairwise_class_sensitive_stratified_bootstrap_seed42.csv")
    fig6_boot=csvrows(DATA/"fig6_bootstrap.csv")
    corrected=csvrows(RES.parent/"audits"/"20261110_ba_reverification"/"results"/"pairwise_balanced_accuracy_bootstrap_seed42_corrected.csv")
    corrected_map={
        "zybert_vs_internlm3": corrected[0],
        "zybert_vs_macbert": corrected[1],
        "zybert_vs_qwen3": corrected[2],
        "internlm3_vs_macbert": corrected[3],
        "internlm3_vs_qwen3": corrected[4],
        "macbert_vs_qwen3": corrected[5],
    }
    for row,key in zip(ordinary, ("zybert_vs_internlm3","zybert_vs_macbert","zybert_vs_qwen3","internlm3_vs_macbert","internlm3_vs_qwen3","macbert_vs_qwen3")):
        corr=corrected_map[key]
        row["ba_diff"]=f"{float(corr['diff_obs_full_precision'])*100:.2f}"
        row["ba_lo"]=f"{float(corr['ci_lower'])*100:.2f}"
        row["ba_hi"]=f"{float(corr['ci_upper'])*100:.2f}"
    for orow,key in zip(ordinary, ("zybert_vs_internlm3","zybert_vs_macbert","zybert_vs_qwen3","internlm3_vs_macbert","internlm3_vs_qwen3","macbert_vs_qwen3")):
        bm=next(r for r in fig6_boot if r["pair"]==orow["pair"] and r["metric"]=="Macro-F1")
        bb=next(r for r in fig6_boot if r["pair"]==orow["pair"] and r["metric"]=="Balanced accuracy")
        sm=next(r for r in strat if r["pair"]==key and r["metric"]=="macro_f1")
        sb=next(r for r in strat if r["pair"]==key and r["metric"]=="balanced_accuracy")
        assert (bm["ord_lo"],bm["ord_hi"])==(orow["mf1_lo"],orow["mf1_hi"])
        assert (bb["ord_lo"],bb["ord_hi"])==(orow["ba_lo"],orow["ba_hi"])
        assert (bm["str_lo"],bm["str_hi"])==(f"{float(sm['ci_lower'])*100:.2f}",f"{float(sm['ci_upper'])*100:.2f}")
        assert (bb["str_lo"],bb["str_hi"])==(f"{float(sb['ci_lower'])*100:.2f}",f"{float(sb['ci_upper'])*100:.2f}")
    def frame(x,y,w,h,letter,title):
        s.box(x,y,w,h,"#ffffff",navy,10,1.8);s.box(x+8,y+8,w-16,46,pale,"none",8);s.box(x+12,y+8,64,46,navy,"none",8);s.text(x+44,y+41,letter,31,700,"#ffffff","middle");s.text(x+87,y+41,title,22,700,navy);s.line(x+14,y+55,x+w-14,y+55,navy,1)
    def subbox(x,y,w,h,title):
        s.box(x,y,w,h,"#ffffff",grid,8,1.2,True);s.box(x+5,y+5,w-10,35,pale,"none",7);s.text(x+w/2,y+29,title,18,700,navy,"middle")
    def lab(row):return row["pair"].replace("ZY-BERT","ZY").replace("InternLM3","Intern").replace("MacBERT","Mac").replace("Qwen3","Qwen")
    frame(4,18,1440,452,"A","Held-out performance and pairwise comparison")
    # A1 accuracy across seeds
    subbox(16,106,389,349,"Accuracy across seeds")
    x0,x1,y0,y1=96,389,391,194
    for v in range(68,80,2):
        yy=y0-(v-68)/(78-68)*(y0-y1);s.line(x0,yy,x1,yy,grid,1);s.text(x0-9,yy+4,str(v),12,400,ink,"end")
    s.line(x0,y0,x1,y0,navy,1.2);s.line(x0,y1,x0,y0,navy,1.2);s.text(44,293,"Accuracy (%)",14,400,navy,"middle",rotate=-90)
    xs=(135,259,350); seeds=("42","2026","7")
    for j,xx in enumerate(xs):s.line(xx,y0,xx,y0+5,navy,1);s.text(xx,y0+28,seeds[j],12,400,ink,"middle")
    for i,model in enumerate(("ZY-BERT","InternLM3")):
        vals=[float(r["accuracy"]) for r in seed if r["model"]==model];c=blue if i==0 else orange;pts=[]
        for j,v in enumerate(vals):
            yy=y0-(v-68)/(78-68)*(y0-y1);pts.append((xs[j],yy));s.dot(xs[j],yy,7,"#ffffff",c,2);s.text(xs[j],yy-16,f"{v:.2f}",14,700,c,"middle")
        # Independent seed outcomes are shown as points. The adjacent mean ± SD panel carries the summary uncertainty.
    s.dot(114,170,5,"#ffffff",blue,1.5);s.text(135,175,"ZY-BERT",13,700,blue)
    s.dot(239,170,5,"#ffffff",orange,1.5);s.text(261,175,"InternLM3-8B",13,700,orange)
    s.text(242,445,"Random seed",14,400,navy,"middle")
    # A2 mean SD
    subbox(417,106,232,349,"Mean ± SD")
    means=csvrows(RES/"three_seed_summary.csv")
    mean_acc={}
    for j,model in enumerate(("ZY-BERT","InternLM3-8B")):
        row=next(r for r in means if r["model"]==model and r["metric"]=="accuracy");c=blue if j==0 else orange;y=166+j*99
        mean_acc[model]=float(row["mean_percent"])
        s.box(430,y,202,77,mix(c,.12),mix(c,.45),7);s.box(434,y+10,9,57,c,"none",3);s.text(456,y+31,"ZY-BERT" if j==0 else "InternLM3-8B",16,700,c);s.text(456,y+60,f"{float(row['mean_percent']):.2f} ± {float(row['sd_percent']):.2f}%",19,700,ink)
    mean_gap=mean_acc["ZY-BERT"]-mean_acc["InternLM3-8B"]
    s.box(430,363,202,64,mix(green,.12),green,7);s.text(449,389,"Mean gap",14,700,navy);s.text(449,416,f"{mean_gap:.2f} pp",22,700,blue)
    # A3 pairwise table
    subbox(660,106,421,349,"Pairwise accuracy Delta (pp)")
    s.text(676,157,"Model pair",15,700,navy);s.box(826,140,77,34,"#dbe8f5","none",6);s.box(911,140,77,34,"#e4ebf5","none",6);s.box(996,140,77,34,"#dbe3f2","none",6)
    for x,t in ((864,"S0"),(949,"S1"),(1034,"S2")):s.text(x,163,t,14,700,navy,"middle")
    for j,row in enumerate(ded):
        y=198+j*39;s.box(674,y-20,394,31,"#f9fafc" if j%2==0 else "#f2f5f9","none",3);s.text(677,y,lab(row),14,700,ink)
        for k,v in enumerate((row["S0"],row["S1"],row["S2"])):s.text(864+k*85,y,f"{float(v):.2f}",14,700,(blue,green,orange)[k],"middle")
    # A4 subset N
    subbox(1092,106,340,349,"Subset N")
    sx0,sx1,sy0,sy1=1190,1408,391,194
    for v in (4190,4200,4210,4220):
        yy=sy0-(v-4190)/(4220-4190)*(sy0-sy1);s.line(sx0,yy,sx1,yy,grid,1);s.text(sx0-9,yy+4,f"{v:,}",12,400,ink,"end")
    s.line(sx0,sy0,sx1,sy0,navy,1.2);s.line(sx0,sy1,sx0,sy0,navy,1.2);s.text(1140,310,"Record count",14,400,navy,"middle")
    pts=[]
    for j,n in enumerate((4218,4206,4195)):
        xx=1206+j*86;yy=sy0-(n-4190)/(4220-4190)*(sy0-sy1);pts.append((xx,yy));s.dot(xx,yy,8,"#ffffff",green,2);s.text(xx,yy-17,f"{n:,}",15,700,green,"middle");s.text(xx,sy0+28,("S0","S1","S2")[j],12,700,navy,"middle")
    s.poly(pts,green,2)
    # B
    frame(4,487,1440,466,"B","Bootstrap inference for model contrasts")
    subbox(16,577,364,363,"Macro-F1 (Δ, pp)");subbox(387,577,364,363,"Balanced accuracy (Δ, pp)");subbox(760,577,294,363,"Mean 95% CI width (pp)");subbox(1068,577,364,363,"Balanced acc.: InternLM3 / MacBERT")
    pairkeys=["zybert_vs_internlm3","zybert_vs_macbert","zybert_vs_qwen3","internlm3_vs_macbert","internlm3_vs_qwen3","macbert_vs_qwen3"]
    # bottom pairwise interval panels
    for px,metric in ((16,"mf1"),(387,"ba")):
        x0=120+px;scale=9.8
        def x_coord(value):
            return x0+(value+2)*scale
        for val in (-2,0,4,8,12,16):
            xx=x_coord(val);s.line(xx,870,xx,876,navy,1);s.text(xx,895,str(val),11,400,ink,"middle")
        s.line(x_coord(-2),870,x_coord(16),870,navy,1.2);s.text(x_coord(7),923,"Δ "+("Macro-F1" if metric=="mf1" else "Balanced acc.")+" (pp)",12,400,navy,"middle")
        for j,(key,orow) in enumerate(zip(pairkeys,ordinary)):
            y=640+j*40
            if metric=="ba" and j==3:s.box(px+8,y-19,348,34,"#fff1e7",orange,4)
            label=lab(orow);s.text(px+16,y,label,13,700,ink)
            if metric=="mf1": ov,olo,ohi=float(orow["mf1_diff"]),float(orow["mf1_lo"]),float(orow["mf1_hi"]);mkey="macro_f1"
            else:ov,olo,ohi=float(orow["ba_diff"]),float(orow["ba_lo"]),float(orow["ba_hi"]);mkey="balanced_accuracy"
            sr=next(r for r in strat if r["pair"]==key and r["metric"]==mkey)
            sv_4dp=float(sr["diff_obs_unrounded_4dp"])*100
            sv_full=float(sr["diff_obs_full_precision"])*100
            assert abs(ov-sv_4dp)<1e-9 and abs(round(sv_full,2)-ov)<1e-9, (key,mkey,ov,sv_4dp,sv_full)
            sv,slo,shi=ov,float(sr["ci_lower"])*100,float(sr["ci_upper"])*100
            for off,c,v,lo,hi in ((-5,blue,ov,olo,ohi),(6,orange,sv,slo,shi)):
                xx=x_coord(v);xl=x_coord(lo);xh=x_coord(hi);s.line(xl,y+off,xh,y+off,c,2);s.line(xl,y+off-5,xl,y+off+5,c,1);s.line(xh,y+off-5,xh,y+off+5,c,1);s.dot(xx,y+off,4,c)
            s.text(px+350,y+4,f"{ov:+.2f}",14,700,orange if metric=="ba" and j==3 else blue,"end")
    # CI width derived directly from the loaded ordinary and stratified tables
    mf1_ord_w=mean(float(r["mf1_hi"])-float(r["mf1_lo"]) for r in ordinary)
    mf1_str_w=mean((float(r["ci_upper"])-float(r["ci_lower"]))*100 for r in strat if r["metric"]=="macro_f1")
    ba_ord_w=mean(float(r["ba_hi"])-float(r["ba_lo"]) for r in ordinary)
    ba_str_w=mean((float(r["ci_upper"])-float(r["ci_lower"]))*100 for r in strat if r["metric"]=="balanced_accuracy")
    s.box(790,613,10,10,blue,"none",1);s.text(811,623,"Ordinary",13,400,ink);s.box(903,613,10,10,orange,"none",1);s.text(924,623,"Stratified",13,400,ink)
    for j,(name,a,b) in enumerate((("Macro-F1",mf1_ord_w,mf1_str_w),("Balanced\nacc.",ba_ord_w,ba_str_w))):
        y=690+j*96;s.lines(790,y-4,name.split("\n"),14,18,ink,"start",400);s.box(861,y-25,a*25,21,blue,"none",2);s.box(861,y+4,b*25,21,orange,"none",2);s.text(1000,y-9,f"{a:.2f}",13,700,navy);s.text(1000,y+20,f"{b:.2f}",13,700,orange)
    s.line(861,861,1018,861,navy,1);s.text(940,883,"CI width (pp)",12,400,ink,"middle")
    # right ordinary versus stratified intervals derived directly from ordinary and strat tables
    im_ord=next(r for r in ordinary if r["pair"]=="InternLM3 vs MacBERT")
    im_str=next(r for r in strat if r["pair"]=="internlm3_vs_macbert" and r["metric"]=="balanced_accuracy")
    im_pt=float(im_ord["ba_diff"])
    for j,(name,c,lo,hi) in enumerate((("Ordinary",blue,float(im_ord["ba_lo"]),float(im_ord["ba_hi"])),("Stratified",orange,float(im_str["ci_lower"])*100,float(im_str["ci_upper"])*100))):
        y=672+j*113;s.text(1086,y,name,14,400,ink);x0=1194;scale=25;s.line(x0-2*scale,y-3,x0+4*scale,y-3,grid,1);s.line(x0,y-17,x0,y+10,navy,1);s.line(x0+lo*scale,y-3,x0+hi*scale,y-3,c,2);s.dot(x0+im_pt*scale,y-3,5,c);s.text(1420,y+4,f"[{lo:+.2f}, {hi:+.2f}]",14,700,c,"end")
    s.box(1085,817,334,90,mix(green,.10),green,7);s.text(1107,846,"Both 95% confidence intervals",13,700,navy);s.text(1107,870,"include zero.",13,400,ink)
    return s

def fig7():
    navy="#142a6b"; blue="#1769c2"; orange="#e35b22"; green="#3c7c4f"; purple="#7c4cad"; pale="#eceef3"; grid="#cdd6e3"; ink="#101b45"; cream="#f5f0e5"
    s=SVG(1448,1086)
    base_text=s.text
    def text7(x,y,label,size=16,weight=400,c=INK,a="start",family="Georgia",rotate=None):
        label=str(label)
        has_cjk=bool(re.search("[\\u3000-\\u9fff]",label))
        has_special=any(ord(ch)>127 for ch in label)
        fam="Noto Sans CJK SC" if has_cjk else ("Arial" if has_special else family)
        return base_text(x,y,label,size,400 if has_special else weight,c,a,fam,rotate=rotate)
    s.text=text7
    classwise=csvrows(DATA/"classwise_metrics.csv"); support=[int(r["support"]) for r in classwise]; total=sum(support); order=sorted(range(len(classwise)),key=lambda j:(-int(classwise[j]["support"]), int(classwise[j]["label_id"])))
    strata_rows=[ [classwise[i] for i in order[:7]], [classwise[i] for i in order[7:28]], [classwise[i] for i in order[28:]] ]
    stratum_means={}
    for label,rows in zip(("Head","Body","Tail"),strata_rows):
        stratum_means[label]={key:mean(float(r[f"f1_{key}"]) for r in rows) for key in ("zybert","internlm3","macbert","qwen3")}
    cols=[blue,orange,green,purple]; names=["ZY-BERT","InternLM3-8B","MacBERT","Qwen3-8B"]
    def frame(x,y,w,h,letter,title):
        s.box(x,y,w,h,"#ffffff",navy,10,1.8);s.box(x+8,y+8,w-16,43,pale,"none",8);s.box(x+12,y+8,64,43,navy,"none",8);s.text(x+44,y+39,letter,30,700,"#ffffff","middle");s.text(x+87,y+39,title,21,700,navy);s.line(x+14,y+53,x+w-14,y+53,navy,1)
    def subbox(x,y,w,h,title):
        s.box(x,y,w,h,"#ffffff",grid,8,1.2,True);s.box(x+5,y+5,w-10,31,pale,"none",7);s.text(x+w/2,y+26,title,17,700,navy,"middle")
    def people_icon(x,y,c):
        s.dot(x+12,y+8,5,c,c,1);s.dot(x+28,y+8,5,c,c,1);s.dot(x+20,y+21,5,c,c,1);s.path(f"M{x+3},{y+31} C{x+3},{y+20} {x+21},{y+20} {x+21},{y+31} Z",c,c,1);s.path(f"M{x+19},{y+31} C{x+19},{y+20} {x+37},{y+20} {x+37},{y+31} Z",c,c,1)
    def database_icon(cx,y,w,h,c):
        s.database(cx,y,w,h,c)
    # A
    frame(4,4,1440,333,"A","")
    # remove unused title slot in frame A and keep only the letter like the reference
    s.box(88,10,1,1,"none","none")
    subbox(15,71,326,249,"Class composition")
    database_icon(62,105,60,66,blue);s.text(63,213,"42",39,700,blue,"middle");s.text(63,238,"classes",16,400,navy,"middle")
    for j,(label,pct,c) in enumerate((("Head (top 7)","16.7%",blue),("Body (next 21)","50.0%",green),("Tail (bottom 14)","33.3%",orange))):
        y=125+j*49;s.box(111,y,218,38,mix(c,.09),mix(c,.35),6);people_icon(120,y+3,c);s.text(149,y+25,label,13.5,700,ink);s.text(312,y+25,pct,15,700,c,"end")
    s.box(15,271,326,48,"#ffffff","none",0);s.box(26,271,315,43,mix(orange,.10),orange,7);s.text(43,295,"Support ratio",15,700,navy);s.text(43,312,"(head vs. tail)",13,700,navy);s.text(322,302,"~ 25.03x",22,700,orange,"end")
    # scale icon
    s.line(197,281,197,309,navy,1.7);s.line(178,309,216,309,navy,1.7);s.line(197,279,183,286,navy,1.3);s.line(197,279,211,286,navy,1.3);s.poly([(177,286),(189,286),(184,300),(173,300)],blue,1.2,"#ffffff",True);s.poly([(205,286),(217,286),(221,300),(210,300)],orange,1.2,"#ffffff",True)
    # ranked support
    subbox(348,71,329,249,"Ranked class support")
    x0,x1,y0,y1=398,654,281,143
    # Support is shown on a true log10 scale. Bar heights and tick positions use the same transform.
    plot_h=y0-y1
    for j,idx in enumerate(order):
        v=support[idx];c=blue if j<7 else green if j<28 else "#8fb1d9";h=plot_h*log10(v)/3;s.box(x0+j*6.0,y0-h,5.2,h,c,"none",.4)
    s.line(x0,y0,x1,y0,navy,1.2)
    for val in (10,100,1000):
        yy=y0-plot_h*log10(val)/3;label="10"+{10:"¹",100:"²",1000:"³"}[val]
        s.line(x0-5,yy,x1,yy,"#dfe4ec",1);s.text(x0-13,yy+4,label,11,400,ink,"end")
    s.text(526,308,"Classes sorted by held-out support",11.5,400,navy,"middle")
    s.box(476,115,186,79,"#ffffff",blue,6,1.2);s.grid(491,125,3,3,11,blue);s.text(540,141,"Head (7, 16.7%)",12,700,navy);s.text(540,163,"Body (21, 50.0%)",12,700,navy);s.text(540,185,"Tail (14, 33.3%)",12,700,navy)
    # cumulative coverage
    subbox(684,71,277,249,"Cumulative coverage")
    x0,x1,y0,y1=737,944,281,145
    for v in (0,.2,.4,.6,.8,1):
        yy=y0-v*(y0-y1);s.line(x0,yy,x1,yy,grid,1);s.text(x0-10,yy+4,f"{v:.1f}",11,400,ink,"end")
    s.line(x0,y0,x1,y0,navy,1.2);s.line(x0,y1,x0,y0,navy,1.2)
    pts=[];cum=0
    for j in range(42):
        cum+=support[order[j]];pts.append((x0+j*(x1-x0)/41,y0-(cum/total)*(y0-y1)))
    poly=[(x0,y0)]+pts+[(x1,y0)];s.poly(poly,"none",0,mix(green,.08),True);s.poly(pts,green,2)
    for idx in (7,28,42):
        xx=pts[idx-1][0];yy=pts[idx-1][1];label=f"{sum(support[order[j]] for j in range(idx))/total:.1%}";s.line(xx,yy,xx,y0,green,1,True);s.dot(xx,yy,5,green);s.text(xx,yy-12,label,13,700,green,"middle")
    for v in (1,7,14,21,28,35,42):
        xx=x0+(v-1)*(x1-x0)/41;s.line(xx,y0,xx,y0+5,navy,1);s.text(xx,y0+16,str(v),11,400,ink,"middle")
    s.text(840,317,"Number of classes (sorted)",11.5,400,navy,"middle")
    # imbalance
    subbox(968,71,228,249,"Class imbalance (support)")
    s.box(1016,113,132,36,cream,orange,12);s.text(1082,137,"≈ 25×",20,700,orange,"middle");s.text(1082,158,"head / tail mean",10.5,400,navy,"middle")
    s.line(1018,166,1146,166,navy,1.2);s.line(1018,166,1018,173,navy,1.2);s.line(1146,166,1146,173,navy,1.2)
    s.database(1008,178,48,55,blue);s.database(1082,178,48,55,green);s.database(1150,190,36,40,orange)
    s.text(1008,250,"Head",12,700,blue,"middle");s.text(1082,250,"Body",12,700,green,"middle");s.text(1150,250,"Tail",12,700,orange,"middle")
    # dataset characteristic
    subbox(1204,71,236,249,"Dataset characteristic")
    for j,(label,pct,c) in enumerate((("Head","7 (16.7%)",blue),("Body","21 (50.0%)",green),("Tail","14 (33.3%)",orange))):
        y=116+j*53;people_icon(1225,y+2,c);s.text(1278,y+25,pct,14,700,ink);s.text(1415,y+25,label,14,700,c,"end")
    s.line(1218,269,1427,269,grid,1)
    bar_x,bar_y,bar_w,bar_h=1219,281,209,18
    parts=((7/42,blue),(21/42,green),(14/42,orange));cursor=bar_x
    for share,c in parts:
        width=bar_w*share;s.box(cursor,bar_y,width,bar_h,c,"none",1);cursor+=width
    # B
    frame(4,355,1440,684,"B","")
    subbox(15,423,407,252,"F1 vs. class support")
    s.box(46,463,366,20,"#f8fafc",blue,5,0.8)
    for lx,c,n in ((58,blue,"ZY-BERT"),(134,orange,"InternLM3-8B"),(236,green,"MacBERT"),(318,purple,"Qwen3-8B")):
        s.dot(lx,473,4.2,c);s.text(lx+8,477,n,10,400,ink)
    x0,x1,y0,y1=92,399,619,493
    for v in (0,.2,.4,.6,.8,1):
        yy=y0-v*(y0-y1);s.line(x0,yy,x1,yy,grid,1);s.text(x0-9,yy+4,f"{v:.1f}",11,400,ink,"end")
    support_axis_min=4.5
    support_axis_max=1050
    for v in (10,100,1000):
        xx=x0+(log10(v)-log10(support_axis_min))/(log10(support_axis_max)-log10(support_axis_min))*(x1-x0);s.line(xx,y0,xx,y0+5,navy,1);s.text(xx,y0+21,"10"+{10:"¹",100:"²",1000:"³"}[v],11,400,ink,"middle")
    s.line(x0,y0,x1,y0,navy,1.2);s.line(x0,y1,x0,y0,navy,1.2)
    for r in classwise:
        sup=int(r["support"]);xx=x0+(log10(sup)-log10(support_axis_min))/(log10(support_axis_max)-log10(support_axis_min))*(x1-x0)
        for j,k in enumerate(("zybert","internlm3","macbert","qwen3")):
            yy=y0-(float(r[f"f1_{k}"])/100)*(y0-y1);s.dot(xx+(j-1.5)*2.5,yy,2.7,cols[j])
    s.text(245,664,"Support (log10)",12,400,navy,"middle");s.text(36,556,"F1 score",12,400,navy,"middle",rotate=-90)
    # representative classes
    subbox(430,423,405,252,"Representative classes")
    s.text(525,472,"Class",12,700,navy);s.text(574,472,"N",12,700,navy)
    for k,t in enumerate(("ZY","Intern","Mac","Qwen")):s.text(625+k*47,472,t,12,700,cols[k],"middle")
    selected=[("C05",860),("C08",552),("C04",531),("C07",89),("C29",77),("C02",13),("C16",13),("C11",6)]
    byid={f"C{int(r['label_id']):02d}":r for r in classwise}
    for j,(cid,n) in enumerate(selected):
        r=byid[cid];y=497+j*21;c=blue if j<3 else green if j<5 else orange;s.box(512,y-13,307,19,"#f7f9fc" if j%2==0 else "#eef3f8","none",2);s.text(525,y,cid,11.5,700,c);s.text(574,y,str(n),11.5,400,ink)
        for k,key in enumerate(("zybert","internlm3","macbert","qwen3")):s.text(625+k*47,y,f"{float(r[f'f1_{key}']):.1f}",11.5,400,cols[k],"middle")
    # violin
    subbox(842,423,270,252,"F1 distribution (by stratum)")
    x0,x1,y0,y1=886,1091,622,469
    for v in (0,.2,.4,.6,.8,1):
        yy=y0-v*(y0-y1);s.line(x0,yy,x1,yy,grid,1);s.text(x0-9,yy+4,f"{v:.1f}",11,400,ink,"end")
    s.line(x0,y0,x0,y1,navy,1.2);s.line(x0,y0,x1,y0,navy,1.2)
    def actual_violin(values,xx,c,label):
        # Histogram-backed silhouette from the observed class/model F1 values.
        bins=20; counts=[0]*bins
        for value in values:
            idx=min(bins-1,max(0,int(float(value)/100*bins))); counts[idx]+=1
        smooth=[]
        for idx,count in enumerate(counts):
            left=counts[idx-1] if idx else count; right=counts[idx+1] if idx<bins-1 else count
            smooth.append((left+2*count+right)/4)
        peak=max(smooth) or 1
        left_pts=[]; right_pts=[]
        for idx,density in enumerate(smooth):
            value=(idx+0.5)*100/bins; yy=y0-value/100*(y0-y1); half=24*density/peak
            left_pts.append((xx-half,yy)); right_pts.append((xx+half,yy))
        s.poly(left_pts+list(reversed(right_pts)),c,1.3,mix(c,.22),True)
        ordered=sorted(float(v) for v in values)
        mid=median(ordered)
        if len(ordered) > 1:
            q1,_,q3=quantiles(ordered,n=4,method="inclusive")
        else:
            q1=q3=ordered[0]
        ym=y0-mid/100*(y0-y1); yq1=y0-q1/100*(y0-y1); yq3=y0-q3/100*(y0-y1)
        s.line(xx,yq1,xx,yq3,"#ffffff",2.2);s.dot(xx,ym,4,"#ffffff",navy,1)
        s.text(xx,648,label,11.5,700,c,"middle");s.text(xx,662,f"n={len(values)}",9.5,400,ink,"middle")
    for j,(c,label,rows) in enumerate(zip((blue,green,orange),("Head","Body","Tail"),strata_rows)):
        vals=[float(r[f"f1_{key}"]) for r in rows for key in ("zybert","internlm3","macbert","qwen3")]
        actual_violin(vals,935+j*68,c,label)
    # mean F1
    subbox(1121,423,319,252,"Mean F1 by stratum")
    x0,x1,y0,y1=1172,1402,626,485
    for v in (0,.2,.4,.6,.8,1):
        yy=y0-v*(y0-y1);s.line(x0,yy,x1,yy,grid,1);s.text(x0-9,yy+4,f"{v:.1f}",11,400,ink,"end")
    s.line(x0,y0,x0,y1,navy,1.2);s.line(x0,y0,x1,y0,navy,1.2)
    meanvals=[tuple(stratum_means[s_name][key] for s_name in ("Head","Body","Tail")) for key in ("zybert","internlm3","macbert","qwen3")]
    stratum_cols=(blue,green,orange)
    for j,vals in enumerate(meanvals):
        pts=[(1190+j*61,y0-v/100*(y0-y1)) for v in vals];s.poly(pts,cols[j],1.7)
        for k,(xx,yy) in enumerate(pts):s.dot(xx,yy,5,stratum_cols[k],cols[j],1.8)
    s.lines(1190,643,["ZY-","BERT"],11,12,blue,"middle",700);s.lines(1251,643,["Intern","LM3-8B"],11,12,orange,"middle",700);s.lines(1312,643,["Mac","BERT"],11,12,green,"middle",700);s.lines(1373,643,["Qwen3","-8B"],11,12,purple,"middle",700)
    # Compact legend sits above the plot and cannot cover the Qwen3-8B points.
    for j,(lab,c) in enumerate(zip(("ZY","Intern","Mac","Qwen"),cols)):
        xx=1179+j*57;s.line(xx-4,468,xx+4,468,c,1.4);s.text(xx+8,472,lab,9.5,400,ink)
    for j,(lab,c) in enumerate(zip(("Head","Body","Tail"),stratum_cols)):
        xx=1179+j*77;s.dot(xx,494,4,c,"#ffffff",1.2);s.text(xx+8,498,lab,9.5,400,ink)
    # bottom left bars derived directly from stratum_means
    subbox(15,703,499,318,"Stratum-wise model contrast")
    for j,(lab,c) in enumerate((("Head",blue),("Body",green),("Tail",orange))):
        vals=[stratum_means[lab][k] for k in ("zybert","internlm3","macbert","qwen3")]
        y=773+j*83;people_icon(36,y-16,c);s.text(72,y,lab,16,700,c)
        for k,v in enumerate(vals):yy=y-25+k*16;s.box(131,yy,v*2.4,11,cols[k],"none",1);s.text(131+v*2.4+7,yy+10,f"{v:.1f}",11,400,ink)
    s.line(130,986,393,986,navy,1);s.text(261,1012,"F1 (%)",13,400,navy,"middle")
    s.box(373,826,131,126,"#ffffff",navy,7,1.0)
    for k,(c,n) in enumerate(zip(cols,names)):
        yy=850+k*23;s.box(386,yy-9,11,11,c,"none",1);s.text(405,yy,n,11,400,ink)
    # gap as a true dumbbell plot using the observed head and tail mean F1 positions
    subbox(530,703,466,318,"Top-to-tail F1 gap")
    s.text(564,750,"● Head (mean F1)   ○ Tail (mean F1)   Δ (pp)",12,700,navy)
    gap_x0,gap_x1=650,931
    def gap_x(value): return gap_x0+(value-20)/(100-20)*(gap_x1-gap_x0)
    for j,(lab,key) in enumerate(zip(("ZY-BERT","InternLM3-8B","MacBERT","Qwen3-8B"),("zybert","internlm3","macbert","qwen3"))):
        head=stratum_means["Head"][key];tail=stratum_means["Tail"][key];gap=head-tail;y=796+j*43;xh=gap_x(head);xt=gap_x(tail)
        s.text(564,y,lab,12,700,ink);s.line(xt,y-4,xh,y-4,navy,1.4);s.dot(xh,y-4,7,cols[j],cols[j],1);s.dot(xt,y-4,7,"#ffffff",cols[j],2);s.text(978,y,f"{gap:.1f}",15,700,cols[j],"end")
    for value in (20,40,60,80,100):
        xx=gap_x(value);s.line(xx,973,xx,979,navy,1);s.text(xx,993,str(value),10.5,400,ink,"middle")
    s.line(gap_x0,975,gap_x1,975,navy,1);s.text(790,1013,"F1 (%)",13,400,navy,"middle")
    # observations
    subbox(1012,703,428,318,"Key observation")
    s.box(1032,754,388,76,mix(green,.10),green,7);s.text(1120,800,"Support ↑  F1 ↑",22,700,navy)
    # small rising bars
    for j,h in enumerate((15,28,42)):s.box(1050+j*17,803-h,11,h,green,"none",1)
    gap_values=[stratum_means["Head"][key]-stratum_means["Tail"][key] for key in ("zybert","internlm3","macbert","qwen3")]
    s.box(1032,855,388,111,mix(green,.10),green,7);s.text(1090,896,"Tail F1 gap",18,700,navy);s.text(1090,930,f"{min(gap_values):.1f}–{max(gap_values):.1f} pp",22,700,orange)
    s.dot(1059,895,16,"#ffffff",blue,4);s.dot(1059,895,7,orange,orange,1)
    return s

def fig8():
    navy="#142a6b"; blue="#1769c2"; orange="#e35b22"; green="#3c7c4f"; purple="#7c4cad"; pale="#eceef3"; grid="#cdd6e3"; ink="#101b45"; cream="#f5f0e5"
    s=SVG(1448,1086)
    base_text=s.text
    def text8(x,y,label,size=16,weight=400,c=INK,a="start",family="Georgia",rotate=None):
        label=str(label)
        has_cjk=bool(re.search("[\\u3000-\\u9fff]",label))
        has_special=any(ord(ch)>127 for ch in label)
        fam="Noto Sans CJK SC" if has_cjk else ("Arial" if has_special else family)
        return base_text(x,y,label,size,400 if has_special else weight,c,a,fam,rotate=rotate)
    s.text=text8
    cols={"ZY-BERT":blue,"InternLM3":orange,"MacBERT":green,"Qwen3":purple}
    errors=csvrows(DATA/"fig8_errors.csv")
    def frame(x,y,w,h,letter,title):
        s.box(x,y,w,h,"#ffffff",navy,10,1.8);s.box(x+8,y+8,w-16,48,pale,"none",8);s.box(x+12,y+8,76,48,navy,"none",8);s.text(x+50,y+42,letter,31,700,"#ffffff","middle");s.text(x+107,y+42,title,22,700,navy);s.line(x+14,y+57,x+w-14,y+57,navy,1)
    def subbox(x,y,w,h,title):
        s.box(x,y,w,h,"#ffffff",grid,8,1.2,True);s.box(x+5,y+5,w-10,36,pale,"none",7);s.text(x+w/2,y+28,title,18,700,navy,"middle")
    def matrix_icon(x,y,c):
        for j in range(6):
            for i in range(6):
                fill=mix(c,.75) if i==j or i==j-1 else mix(c,.06+.12*((i+j)%3));s.box(x+i*11,y+j*11,9,9,fill,"none",.4)
    def doc(x,y,w,h,c):
        s.path(f"M{x},{y} H{x+w-14} L{x+w},{y+14} V{y+h} H{x} Z","#ffffff",c,1.5);s.poly([(x+w-14,y),(x+w-14,y+14),(x+w,y+14)],c,1.1)
        for q in (0.38,0.55,0.72):s.line(x+w*.20,y+h*q,x+w*.80,y+h*q,c,1.1)
    def label_pair(row):
        return row["true_id"]+" → "+row["pred_id"]
    # A
    frame(4,20,1440,646,"A","Confusion-matrix error analysis (seed 42, clean test N = 4,218)")
    # overview
    subbox(14,108,291,543,"Model overview")
    s.text(159,168,"Schematic matrix icons",11.5,400,MUTED,"middle")
    for j,(name,c) in enumerate((("ZY-BERT",blue),("InternLM3-8B",orange),("MacBERT",green),("Qwen3-8B",purple))):
        x=49+(j%2)*134;y=188+(j//2)*104;matrix_icon(x,y,c);s.text(x+28,y+74,name,12.5,700,c,"middle")
    s.database(69,486,60,47,blue);s.lines(149,503,["42 x 42 confusion","matrices"],14,18,navy,"start",700);s.text(149,543,"Clean test N = 4,218",14,400,ink);s.text(159,580,"Full 42×42 heatmaps: Figs. S1–S4",11,400,MUTED,"middle")
    # route map generated directly from the ranked error rows
    subbox(313,108,394,543,"Error-route map")
    s.text(355,168,"True label",15,700,navy);s.text(542,168,"Predicted label",15,700,navy)
    for j,r in enumerate(errors):
        y=187+j*40
        s.labelbox(330,y,128,30,r["true_id"],blue,11.5)
        s.arrow([(463,y+15),(501,y+15)],navy,1.1)
        s.text(482,y+10,str(j+1),10.5,700,navy,"middle")
        s.labelbox(509,y,170,30,r["pred_id"],orange,11.5)
    s.box(327,603,365,33,"#ffffff",navy,10,1.1,True);s.text(510,625,"Pooled off-diagonal extraction",13,700,navy,"middle")
    # model-specific count table
    subbox(715,108,389,543,"Model-specific counts")
    s.text(730,174,"Route (True → Pred)",13,700,navy)
    for k,t in enumerate(("ZY","Int","Mac","Qw")):s.labelbox(954+k*35,153,32,27,t,(blue,orange,green,purple)[k],11)
    for j,r in enumerate(errors):
        y=211+j*38;s.box(728,y-22,361,30,"#f7f9fc" if j%2==0 else "#eef3f8","none",3);s.text(736,y,label_pair(r),13,700,ink)
        for k,key in enumerate(("ZY-BERT","InternLM3","MacBERT","Qwen3")):s.text(970+k*35,y,r[key],12.5,700,(blue,orange,green,purple)[k],"middle")
    for xx,c,t in ((724,blue,"ZY-BERT"),(812,orange,"InternLM3"),(914,green,"MacBERT"),(1008,purple,"Qwen3")):
        s.box(xx,613,12,12,c,"none",1);s.text(xx+17,623,t,10.5,400,ink)
    # pooled counts
    subbox(1112,108,322,543,"Pooled counts")
    pooled=[errors[0],errors[2]]
    for j,r in enumerate(pooled):
        y=194+j*192;c=green if j==0 else blue;tot=sum(int(r[k]) for k in ("ZY-BERT","InternLM3","MacBERT","Qwen3"))
        s.text(1134,y,f"{r['true_id']} →",17,700,navy);s.text(1134,y+27,r["pred_id"],17,700,navy)
        x=1134
        for k,key in enumerate(("ZY-BERT","InternLM3","MacBERT","Qwen3")):
            w=205*int(r[key])/tot;s.box(x,y+51,w,22,(blue,orange,green,purple)[k],"none",1);x+=w
        s.box(1352,y+39,70,45,mix(c,.08),c,7);s.text(1387,y+70,str(tot),24,700,c,"middle")
    for xx,yy,c,t in ((1142,588,blue,"ZY-BERT"),(1274,588,orange,"InternLM3"),(1142,614,green,"MacBERT"),(1274,614,purple,"Qwen3")):
        s.box(xx,yy,13,13,c,"none",1);s.text(xx+19,yy+11,t,11,400,ink)
    # B
    frame(4,680,1440,384,"B","Valid-label extraction & parser audit (N = 4,218)")
    subbox(14,767,334,286,"Direct class index")
    for j,(name,c) in enumerate((("ZY-BERT",blue),("MacBERT",green))):
        y=851+j*102;s.dot(36,y,7,c);s.text(53,y+5,name,15,700,c);s.text(310,y+5,"4,218 / 4,218",14,700,ink,"end");s.box(26,y+25,296,13,mix(c,.15),c,4);s.text(311,y+64,"100.00%",13,700,ink,"end")
    subbox(360,767,365,286,"Generated text + parser")
    for j,(name,c) in enumerate((("InternLM3-8B",orange),("Qwen3-8B",purple))):
        y=842+j*102;s.dot(383,y-8,7,c);s.text(402,y-3,name,13,700,c);s.text(704,y-3,"4,216 / 4,218",13.5,700,ink,"end")
        s.box(402,y+12,302,11,mix(c,.16),c,4)
        doc(402,y+34,32,36,c);s.arrow([(440,y+52),(464,y+52)],navy,1.3);s.labelbox(470,y+38,94,28,"Parser v18",c,11);s.text(704,y+57,"99.95% · 2 empty",12,400,ink,"end")
    subbox(738,767,320,286,"Validity summary")
    for j,(lab,val,c) in enumerate((("Direct index","100.00%",green),("Generated text","99.95%",green),("Empty model outputs","4",orange))):
        y=817+j*64;s.box(759,y,278,49,mix(c,.10),c,7);s.text(777,y+29,lab,14,700,navy);s.text(1015,y+32,val,21,700,c,"end")
    subbox(1070,767,364,286,"Representative routes")
    for j,r in enumerate(pooled):
        y=830+j*94;c=green if j==0 else blue;tot=sum(int(r[k]) for k in ("ZY-BERT","InternLM3","MacBERT","Qwen3"));s.text(1093,y,f"{r['true_id']} →",14,700,c);s.text(1093,y+22,r["pred_id"],14,700,c);s.text(1093,y+48," / ".join(r[k] for k in ("ZY-BERT","InternLM3","MacBERT","Qwen3"))+f" · pooled {tot}",12,400,ink);x=1093
        for k,key in enumerate(("ZY-BERT","InternLM3","MacBERT","Qwen3")):
            w=280*int(r[key])/tot;s.box(x,y+59,w,13,(blue,orange,green,purple)[k],"none",1);x+=w
    s.text(1089,1036,"* Two directions in main text · pooled counts are not unique cases",10.5,400,ink)
    return s

def main():
    (OUT/"SVG").mkdir(parents=True,exist_ok=True)
    funcs=[fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8]
    for i,f in enumerate(funcs,1): f().write(i)
if __name__=="__main__":
    main()


