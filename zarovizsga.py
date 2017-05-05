#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import requests, re, getpass, configparser
from bs4 import BeautifulSoup

fcsop_re=re.compile(r'fcsop\[fcsop\]=(\d+)');
fejezetek_re=re.compile(r'fcsop\[fejezet\]=(\d+)');
baseurl='http://aok.zarovizsga.hu/segedanyagok/kerdes_tallozo/'
jar=[]
kerdesek=[]

class LoginException(Exception):
    pass

def login():
    global jar
    try:
        cp=configparser.RawConfigParser()
        cp.read('login.ini')
        login={'login[username]':cp.get('zarovizsga', 'user'),'login[password]':cp.get('zarovizsga','pass'),'login[loggedin]':'BELÉP'}
    except:
        login={'login[username]':input('E-mail cím? '),'login[password]':getpass.getpass('Jelszó? '),'login[loggedin]':'BELÉP'}
    try:
        r=requests.post('http://aok.zarovizsga.hu/login_box/',data=login)
        r.encoding="UTF-8"
        soup=BeautifulSoup(r.text,"lxml")
        errordiv=soup.find("div",class_="error")
        assert errordiv is None
    except AssertionError as e:
        raise LoginException(errordiv.string.strip())
    return r.cookies

def crawlfejezet(cookiejar, fcsop, fejezet=None):
    global kerdesek
    global jar
    kerdesgy=[]
    params={"fcsop[fcsop]":fcsop['fcsop'], "fcsop[fejezet]":fejezet['fej'] if fejezet else None, "feladatcsoport_kerdes_lista[kerdes_pager][pg]": 1}
    gotqs=20
    while gotqs==20:
        r=requests.get(baseurl, params=params, cookies=cookiejar)
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
    r=requests.get(baseurl, params={"fcsop[vissza]":'true'}, cookies=cookiejar)
    return kerdesgy

def getfcsops(cookiejar):
    r=requests.get(baseurl, cookies=cookiejar)
    r.encoding="utf-8"
    soup=BeautifulSoup(r.text,"lxml")
    return [{'title': div.a.string.strip(), 'fcsop':fcsop_re.search(div.a['href']).group(1)} for div in soup.find_all("div", class_="feladatcsoportok") if fcsop_re.search(div.a['href'])]

def getfejezets(fcsops, cookiejar):
    tasks=[]
    for fcsop in fcsops:
        r=requests.get(baseurl, params={"fcsop[fcsop]":fcsop['fcsop']}, cookies=cookiejar)
        r.encoding="utf-8"
        soup=BeautifulSoup(r.text,"lxml")
        fejezets=[{'title': div.a.string.strip(), 'fej':fejezetek_re.search(div.a['href']).group(1)} for div in soup.find_all("div", class_="feladatcsoportok") if fejezetek_re.search(div.a['href'])]
        if(fejezets):
            print(str(len(fejezets))+u' fejezetet találtam a '+fcsop['title']+u' kategóriában.')
            for fejezet in fejezets:
                print(fejezet['fej']+u': '+fejezet['title'])
            tasks.append({'fcsop':fcsop, 'fejezet':fejezet})
        else:
            print(u'Nem találtam fejezeteket a '+fcsop['title']+u' kategóriában.')
            tasks.append({'fcsop':fcsop, 'fejezet': None})
        r=requests.get(baseurl, params={"fcsop[vissza]":'true'}, cookies=cookiejar)
    return tasks

def main():
    try:
        cookiejar=login()
    except LoginException as e:
        print("Nem sikerült bejelentkezni. A weboldal üzenete: "+str(e))
        exit()
    tasks=getfejezets(getfcsops(cookiejar),cookiejar)
    kerdesek=[crawlfejezet(cookiejar, task['fcsop'], task['fejezet']) for task in tasks]

if __name__ == "__main__":
    main()
