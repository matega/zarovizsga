#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests, re, getpass, ConfigParser

fcsop_re=re.compile(r'<td><div[^>]*class="[^"]*feladatcsoportok[^"]*"[^>]*><a[^>]*href="[^"]*fcsop\[fcsop\]=(\d+)[^"]*"[^>]*>([^<]*)</a>');
hasfejezet_re=re.compile(r'<a href="\.\./\.\./segedanyagok/kerdes_tallozo/\?fcsop\[vissza\]">');
fejezetek_re=re.compile(r'<td><div[^>]*class="[^"]*feladatcsoportok[^"]*"[^>]*><a[^>]*href="[^"]*fcsop\[fcsop\]=(\d+)&fcsop\[fejezet\]=(\d+)[^"]*"[^>]*>([^<]*)</a>');

try:
    cp=ConfigParser.RawConfigParser()
    cp.read('login.ini')
    login={'login[username]':cp.get('zarovizsga', 'user'),'login[password]':cp.get('zarovizsga','pass'),'login[loggedin]':'BELÉP'}
except:
    login={'login[username]':raw_input('E-mail cím? '),'login[password]':getpass.getpass('Jelszó? '),'login[loggedin]':'BELÉP'}
baseurl='http://aok.zarovizsga.hu/segedanyagok/kerdes_tallozo/'
kerdesek=[]

def crawlfejezet(fcsop, fejezet=None):
    global kerdesek
    global jar
    kerdesgy=[]
    params={"fcsop[fcsop]":fcsop['fcsop'], "fcsop[fejezet]":fejezet['fej'] if fejezet else 0, "feladatcsoport_kerdes_lista[kerdes_pager][pg]": 1}
    gotqs=20
    while gotqs==20:
        r=requests.get(baseurl, params=params, cookies=jar)
        r.encoding="UTF-8"
        print(r.text)
        exit()
        #TODO: Kérdések kigyűjtése
        params["feladatcsoport_kerdes_lista[kerdes_pager][pg]"]+=1
        

r=requests.post('http://aok.zarovizsga.hu/login_box/',data=login)
jar=r.cookies
#print(r.text)
#print(r.cookies)
r=requests.get(baseurl, cookies=jar)
r.encoding="utf-8"
fcsops=[{'title': m.group(2), 'fcsop':m.group(1)} for m in fcsop_re.finditer(r.text)]
for fcsop in fcsops:
    print(fcsop['fcsop'])
    r=requests.get(baseurl, params={"fcsop[fcsop]":fcsop['fcsop']}, cookies=jar)
    r.encoding="utf-8"
    if(hasfejezet_re.search(r.text)):
        fejezets=[{'title': m.group(3), 'fej':m.group(2)} for m in fejezetek_re.finditer(r.text)]
        print(str(len(fejezets))+u' fejezetet találtam a '+fcsop['title']+u' kategóriában.')
        for fejezet in fejezets:
            print(fejezet['fej']+u': '+fejezet['title'])
            crawlfejezet(fcsop, fejezet)
    else:
        print(u'Nem találtam fejezeteket a '+fcsop['title']+u' kategóriában.')
        crawlfejezet(fcsop)
    r=requests.get(baseurl, params={"fcsop[vissza]":'true'}, cookies=jar)
#TODO: Kérdések kiírása
