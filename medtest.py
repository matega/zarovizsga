#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json, os.path

ktip=[]

def dumpfejezet(tid, fid, name):
    try:
        with open(os.path.join('medtest', 'csp_'+str(tid), 'fejezet_'+str(fid)+'.json'), 'r') as f:
            kerdesek=json.load(f)
        global ktip
        global khandlers
        for kerdes in kerdesek:
             khandlers[kerdes['feladatTipusId']](kerdes)
    except IOError as e:
        print "I/O error({0}): {1} while trying to access {2}".format(e.errno, e.strerror, os.path.join('medtest', 'csp_'+str(tid), 'fejezet_'+str(fid)+'.json'))
        print "Failed to gather "+ name
        
def egyszeruhandler(kerdes):
#    print kerdes
    pass

def tobbszoroshandler(kerdes):
#    print kerdes
    pass

def furahandler(kerdes):
    print kerdes['sorszam']
    
def relhandler(kerdes):
#    print kerdes
    pass

khandlers={1: egyszeruhandler, 2: tobbszoroshandler, 3: furahandler, 4: relhandler}

with open(os.path.join('medtest', 'gyujtemeny.json'), 'r') as gy:
    gyujtemeny=json.load(gy)
for fcs in gyujtemeny['result']['feladatCsoport']:
    tid=fcs['id']
    if len(fcs['fejezet'])>0:
        for fej in fcs['fejezet']:
            dumpfejezet(tid, fej['id'], fcs['nev']+": "+fej['nev'])
    else:
        dumpfejezet(tid, 0, fcs['nev'])

