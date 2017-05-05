#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import requests, re, getpass, configparser
from bs4 import BeautifulSoup

fcsop_re=re.compile(r'fcsop\[fcsop\]=(\d+)');
fejezetek_re=re.compile(r'fcsop\[fejezet\]=(\d+)');

try:
    cp=configparser.RawConfigParser()
    cp.read('login.ini')
    login={'login[username]':cp.get('zarovizsga', 'user'),'login[password]':cp.get('zarovizsga','pass'),'login[loggedin]':'BELÉP'}
except IOException as e:
    login={'login[username]':input('E-mail cím? '),'login[password]':getpass.getpass('Jelszó? '),'login[loggedin]':'BELÉP'}
baseurl='http://aok.zarovizsga.hu/segedanyagok/kerdes_tallozo/'
kerdesek=[]

def crawlfejezet(fcsop, fejezet=None):
    global kerdesek
    global jar
    kerdesgy=[]
    params={"fcsop[fcsop]":fcsop['fcsop'], "fcsop[fejezet]":fejezet['fej'] if fejezet else None, "feladatcsoport_kerdes_lista[kerdes_pager][pg]": 1}
    gotqs=20
    while gotqs==20:
        r=requests.get(baseurl, params=params, cookies=jar)
        r.encoding="utf-8"
        #TODO: Kérdések kigyűjtése
        soup=BeautifulSoup(r.text, "lxml")
        kerdesek=soup.find_all('div', class_='kerdes_reszletes_belso')
        gotqs=len(kerdesek)
        for kerdes in kerdesek:
            pvf=kerdes.find('div', class_='probavizsga_feladat')
            if(pvf):
                ktype=pvf.table['title']
            else:
                print("III. Párosításos feladat")
                continue
            if(ktype==u"I. Egyszerü feleletválasztás GY."):
                print(kerdes.find('div', class_='probavizsga_kerdes_leiras').get_text())
            elif(ktype==u"II. Többszörös feleletválasztás GY"):
                pass
            elif(ktype==u"IV. Relációanalizis GY"):
                pass
            else:
                print("Ismeretlen feladattípus: "+ktype)
                exit()
        print(gotqs)
        params["feladatcsoport_kerdes_lista[kerdes_pager][pg]"]+=1
        

r=requests.post('http://aok.zarovizsga.hu/login_box/',data=login)
jar=r.cookies
r=requests.get(baseurl, cookies=jar)
r.encoding="utf-8"
soup=BeautifulSoup(r.text,"lxml")
fcsops=[{'title': div.a.string.strip(), 'fcsop':fcsop_re.search(div.a['href']).group(1)} for div in soup.find_all("div", class_="feladatcsoportok") if fcsop_re.search(div.a['href'])]
for fcsop in fcsops:
    print(fcsop['fcsop'])
    r=requests.get(baseurl, params={"fcsop[fcsop]":fcsop['fcsop']}, cookies=jar)
    r.encoding="utf-8"
    soup=BeautifulSoup(r.text,"lxml")
    fejezets=[{'title': div.a.string.strip(), 'fej':fejezetek_re.search(div.a['href']).group(1)} for div in soup.find_all("div", class_="feladatcsoportok") if fejezetek_re.search(div.a['href'])]
    if(fejezets):
        print(str(len(fejezets))+u' fejezetet találtam a '+fcsop['title']+u' kategóriában.')
        for fejezet in fejezets:
            print(fejezet['fej']+u': '+fejezet['title'])
            pass
            crawlfejezet(fcsop, fejezet)
    else:
        print(u'Nem találtam fejezeteket a '+fcsop['title']+u' kategóriában.')
        crawlfejezet(fcsop)
    r=requests.get(baseurl, params={"fcsop[vissza]":'true'}, cookies=jar) #Igen, erre tényleg szükség van, különben összeomlik az oldal.
#TODO: Kérdések kiírása
