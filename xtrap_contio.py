#!/usr/bin/python
import os
import sys 
import time
import csv
import glob

# RDY=0
# REG=1 #ch31
# CE1=2 #ch30
# CE2=3 #ch29
# OE=4 #ch28
# WE=5 #ch27
# WAIT=6 #ch26
# STSCHG=7
# INPACK=8
# IOSIS16=9
# IOWR=10
# IORD=11

RDY=0
MINT=1
CE1=2
CE2=3
OE=4
WE=5

ctr = {
    "31":"REG",
    "30":"CE1",
    "29":"CE2",
    "28":"OE",
    "27":"WE",
    "26":"RDY",
}

# (IO MAP ONLY)
#attribute access specifications (hit pg 13)
#task file register access (hit pg 14) 
STANDBY="11x"
BYTE_ACCESS_EVEN="100" #even byte
BYTE_ACCESS_ODD="101" #invalid d0 to d7??
WORD_ACCESS="00x" 
ODD_ACCESS="01x"
ACC_CHECK_BITS = 3

cis_address=[i for i in range(0x000,0x200)]
radr = {
    "CIS":cis_address,
    "COR":[0x200],
    "CSR":[0x202],
    "PRR":[0x204],
    "SCR":[0x206]
}

rnam = {
    "000":["TFD","TFD"],
    "001":["TFE","TFF"],
    "002":["TFSC","TFSC"],
    "003":["TFSN","TFSN"],
    "004":["TFCL","TFCL"],
    "005":["TFCH","TFCH"],
    "006":["TFDH","TFDH"],
    "007":["TFS","TFC"]
}

ata = {
    0x20:"READ_SECTOR",
    0x30:"WRITE_SECTOR",
}

tfs = {
    0x80:["BSY"],
    0x40:["DRDY"],
    0x20:["DWF"],
    0x10:["DSC"],
    0x08:["DRQ"],
    0x04:["CORR"],
    0x02:["INTRQ"],
    0x01:["ERR"],
}

path = os.path.dirname(os.path.realpath(__file__))

def grab_file(tail):
    i = 0
    name = []
    for file in os.listdir(path):
        if file.endswith(tail):
            name.append(file)
            print(str(i) + ":" + file)
            i+=1
    if i == 0:
        print("no {0} exists".format(tail))
        sys.exit()
    if i > 1:
        i = int(input("Select {0} file(0-{1}):".format(tail,i-1)))
    return name[i-1]

fp = path + "/" + grab_file("DATA.CSV")
data=[]
with open(fp, 'r') as f:
    for l in f:
        data.append(l)    
print("copy of {0} complete".format(fp))
data=data[:-1]

fp = path + "/" + grab_file("ADD.CSV")
addr=[]
with open(fp, 'r') as f:
    for l in f:
        addr.append(l)    
print("copy of {0} complete".format(fp))
addr=addr[:-1]

fp = path + "/" + grab_file("CTRL.CSV")
ctrl=[]
with open(fp, 'r') as f:
    for l in f:
        ctrl.append(l)    
print("copy of {0} complete".format(fp))
ctrl=ctrl[1:]

# fp = path + "/" + grab_file("G4.CSV")
# g4=[]
# with open(fp, 'r') as f:
#     for l in f:
#         g4.append(l)
# print("copy of {0} complete".format(fp))

# fp = path + "/" + grab_file("G10.CSV")
# g10=[]
# with open(fp, 'r') as f:
#     for l in f:
#         g10.append(l)
# print("copy of {0} complete".format(fp))

# if len(g4) != len(g10):
#     print("data length mismatch g4:{0} g10:{1}".format(len(g4),len(g10)))
#     sys.exit()

# ctrl=[]
# for i,l in enumerate(g4):
#     ctrl.append(g4[i].rstrip('\r\n')+g10[i].rstrip('\r\n'))
# ctrl=ctrl[:-1]

#OPTIONAL DEBUG
fp = path + "/DBG.CSV"
if os.path.isfile(fp) == False:
    print("{0} not found".format(fp))
    dbg_included = False
else:
    dbg_included = True
    dbg=[]
    with open(fp, 'r') as f:
        for l in f:
            dbg.append(l)    
    print("copy of {0} complete".format(fp))
    dbg=dbg[:-1]

if not (len(addr) == len(data) == len(ctrl)):
    print("data length mismatch a:{0} d:{1} c:{2}".format(len(addr),len(data),len(ctrl)))
    sys.exit()

def check_rw(c,nc):
    if int(c[OE]) == 0 and int(nc[OE]) == 1:
        return "ATT_READ"
    elif int(c[WE]) == 0 and int(nc[WE]) == 1:
        return "ATT_WRITE"
    # elif int(c[WE]) == 1 and int(c[OE]) == 1:
    #     if int(c[IORD]) == 0 and int(nc[IORD]) == 1:
    #         return "IO_READ"
    #     elif int(c[IOWR]) == 0 and int(nc[IOWR]) == 1:
    #         return "IO_WRITE"
    #     else:
    #         return None
    else:
        return None

# def check_reg(a,c):
#     if c[REG] == "0":
#         try:
#             v = rnam[a]
#         except:
#             return None
#         if c[IORD] == "0" and c[IOWR] == "1":
#             return v[0]
#         elif c[IORD] == "1" and c[IOWR] == "0":
#             return v[1] 
#         else:
#             return None
#     else:
#         return None

def check_data(d):
    for k,v in dta.items():
        try:
            if d in v:
                return k
        except:
            return None

def attcmp(c,m):
    mch = list(m)
    cnt = ACC_CHECK_BITS
    for i,ch in enumerate(c):
        if mch[i] == 'x' or ch == mch[i]:
            cnt-=1
    return True if cnt == 0 else False

def check_acc(c,d):
    a0 = int(d,16) & 0x0001
    b = [c[CE2],c[CE1],str(a0)]
    if attcmp(b,STANDBY):
        return "STANDBY" 
    if attcmp(b,BYTE_ACCESS_EVEN):
        return "BYTE_ACCESS_EVEN"
    if attcmp(b,BYTE_ACCESS_ODD):
        return "BYTE_ACCESS_ODD"
    if attcmp(b,WORD_ACCESS):
        return "WORD_ACCESS"
    if attcmp(b,ODD_ACCESS):
        return "ODD_ACCESS"
    return None

def check_mode(d):
    b = int(d,16) &0x1F
    if b == 0:
        return "MEMORY"
    if b == 1:
        return "CONT_IO"
    if b == 2:
        return "PRIM_IO"
    if b == 3:
        return "SECOND_IO"

def check_map(a,d):
    r = int(a,16) & 0xF
    o = (int(d,16) & 0xFF00) >> 8
    e = int(d,16) & 0xFF
    if r == 2:
        return [e,o,None,None,None,]
    elif r == 4:
        return [None,None,e,o,None]
    elif r == 6:
        return [None,None,None,None,e]
    else:
        return [None,None,None,None,None]

def check_cmd(d):
    d = (int(d,16) & 0xFF00) >> 8

def check_ata(acc,d):
    if acc == "BYTE_ACCESS_ODD":
        a = int(d,16)&0xFF
    elif acc == "ODD_ACCESS":
        a = (int(d,16)&0xFF00)>>8
    else:
        return None
    try:
        return ata[a]
    except:
        return "Unkown cmd {0}".format(hex(a))

def reg_addr(n):
    for k,v in rnam.items():
        if n in v:
            return k  

def debit(byt):
    b = []
    for k,v in tfs.items():
        if (byt&k):
            b.append(v)
    return b

if len(sys.argv) >= 2:
    fp = path + "/Form_{0}.csv".format(sys.argv[1])
else:
    fp = path + "/Form_{0}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

if (sys.version_info > (3, 0)):
    # Python 3
    csvf = open(fp, 'w', newline='')
else:
    # Python 2
    csvf = open(fp, 'wb')

writer = csv.writer(csvf)

print("begin writing of {0}".format(fp))
t0 = time.time()

# setup toolbar
toolbar_width = 100
sys.stdout.write("[%s]" % (" " * toolbar_width))
sys.stdout.flush()
sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['

cnt=0
tlb_cnt=0
size=len(data)

#file headers
line = ["TYPE_RW","ACCESS","ADDR","DATA"]
line += ["ready","mint","ce1","ce2","oe","we"]
line += ["ATA_CMD"]
line += ["C","N","CL","CH","DH"]
line += ["Line Redundancy"]

if dbg_included:
    line += ["IOWR","IORD","","","","trig","mMINTsel","MDATA","MTFDABORT","pTFVsel","mTFSsel","mMDBC","MPECC","mMWLsel","MWRITE","MWTFC","BSY"]
    dbg=dbg[1:]

writer.writerow(line)

last_line = [0]
redundancy_cnt = 0
for row in range(0,size):
    cnhld = [None,None,None,None,None]
    cmd = None
    ftr, err = None,None
    bits = None
    ata = None

    #extract data for line
    a = addr[row].rstrip('\r\n')
    d = data[row].rstrip('\r\n')
    c = ctrl[row].rstrip('\r\n').split(",")

    if dbg_included:
        dg = dbg[row].split(",")

    #to detect rising edge of WE and OE
    if row != size-1: 
        nc = ctrl[row+1].split(",")
    else:
        print(row)


    rw = check_rw(c,nc)
    acc = check_acc(c,d)
    #reg = check_reg(a,c)

    #check map,ftr,and err
    if acc == "WORD_ACCESS":
        cnhld = check_map(a,d)

    #check ata command
    # if rw == "IO_WRITE":
    #     ata = check_ata(acc,d)

    #check TFS bits
    # if acc == "TFR_ODD_ACCESS" and reg == "TFS" and rw == "READ":
    #     bits = debit((int(d,16)&0xFF00)>>8)

    #build array to fill row
    line = [rw] #READ or WRITE
    line += [acc] #access
    #line += [reg]
    line += [a,d]
    line += c #drop \r\n
    #line += [ata]
    line += cnhld
    # line += [cmd]
    # line += [ftr,err]
    # line += [bits]

    #space and dbg
    if dbg_included:
        line += dg[0:2]
        line += ["",""]
        line += dg[2:-1]

    #write row to csv
    #check for redundant lines
    if line == last_line:
        redundancy_cnt+=1
    else:
        if redundancy_cnt != 0:
            writer.writerow(["..."])
            line += ["chg occured, {0} redundant lines before".format(redundancy_cnt)]
        redundancy_cnt = 0
        writer.writerow(line)
        last_line = line

    #task bar completion
    cnt+=1
    if cnt >= (size / toolbar_width) * tlb_cnt:
        tlb_cnt+=1
        sys.stdout.write("-")
        sys.stdout.flush()

d = time.time() - t0

sys.stdout.write("]\n") # this ends the progress bar
print("duration: {0:2f} s.".format(d))
csvf.close()