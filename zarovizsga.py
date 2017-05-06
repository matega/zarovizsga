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
    global jar
    kerdesgy=[]
    params={"fcsop[fcsop]":fcsop['fcsop'], "fcsop[fejezet]":fejezet['fej'] if fejezet else None, "feladatcsoport_kerdes_lista[kerdes_pager][pg]": 1}
    gotqs=20
    while gotqs>0:
        r=requests.get(baseurl, params=params, cookies=cookiejar)
        r.encoding="utf-8"
        soup=BeautifulSoup(r.text, "lxml")
        kerdess=soup.find_all('div', class_='kerdes_reszletes_belso')
        gotqs=len(kerdess)
        for kerdes in kerdess:
            pvf=kerdes.find('div', class_='probavizsga_feladat')
            if(pvf):
                ktype=pvf.table['title']
            else:
                kerdesgy.append(pairing(kerdes))
                continue
            if(ktype==u"I. Egyszerü feleletválasztás GY."):
                kerdesgy.append(simplechoice(kerdes))
            elif(ktype==u"II. Többszörös feleletválasztás GY"):
                kerdesgy.append(multiplechoice(kerdes))
            elif(ktype==u"IV. Relációanalizis GY"):
                kerdesgy.append(relanal(kerdes))
            else:
                print("Ismeretlen feladattípus: "+ktype)
                exit()
        params["feladatcsoport_kerdes_lista[kerdes_pager][pg]"]+=1
    r=requests.get(baseurl, params={"fcsop[vissza]":'true'}, cookies=cookiejar)
    return kerdesgy

def getfcsops(cookiejar):
    r=requests.get(baseurl, cookies=cookiejar)
    r.encoding="utf-8"
    soup=BeautifulSoup(r.text,"lxml")
    return [{'title': div.a.string.strip(), 'fcsop':fcsop_re.search(div.a['href']).group(1)} for div in soup.find_all("div", class_="feladatcsoportok") if fcsop_re.search(div.a['href'])][0:2]

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


def simplechoice(div):
    try:
        kerdes={'type':1,
                'sorszam':str(div.span.label.get_text(strip=True)),
                'leiras':str(div.find('div',class_='probavizsga_kerdes_leiras').get_text(strip=True)),
                'valaszok':[[td.get_text(strip=True).replace('\xa0',' ').strip() for td in tr.contents[1:]] for tr in div.select("div.probavizsga_feladat table tr")],
                'megoldas':[td.get_text(strip=True).replace('\xa0',' ').strip() for td in div.select("div.megoldas_magyarazat table tr:nth-of-type(2) > td")],
                }
        if len(div.select('div.megoldas_magyarazat table tr:nth-of-type(4) > td'))>0: kerdes['magyarazat']=div.select('div.megoldas_magyarazat table tr:nth-of-type(4) > td')[0].get_text(strip=True).strip()
        return kerdes
    except Exception as e:
        print(div)
        raise e

def multiplechoice(div):
    try:
        kerdes={'type':2,
                'sorszam':str(div.span.label.get_text(strip=True)),
                'leiras':str(div.find('div',class_='probavizsga_kerdes_leiras').get_text(strip=True)),
                "valaszok":[[td.get_text(strip=True).replace('\xa0',' ').strip() for td in tr.contents[1:]] for tr in div.select("div.probavizsga_feladat table tr")],
                'megoldas':[td.get_text(strip=True).replace('\xa0',' ').strip() for td in div.select("div.megoldas_magyarazat table tr:nth-of-type(2) > td")],
                'elemi_valaszok':[ev.get_text(strip=True).replace('\xa0', ' ').split(None, 1) for ev in div.select("div.elemi_valaszok")]
                }
        if len(div.select('div.megoldas_magyarazat table tr:nth-of-type(4) > td'))>0: kerdes['magyarazat']=div.select('div.megoldas_magyarazat table tr:nth-of-type(4) > td')[0].get_text(strip=True).strip()
        return kerdes
    except Exception as e:
        print(div)
        raise e

def relanal(div):
    try:
        kerdes={'type':3,
                'sorszam':str(div.span.label.get_text(strip=True)),
                'leiras':div.find('div',class_='probavizsga_kerdes_leiras').get_text(strip=True).split(", mert ", 1),
                "valaszok":[[td.get_text(strip=True).replace('\xa0',' ').strip() for td in tr.contents[1:]] for tr in div.select("div.probavizsga_feladat table tr")],
                'megoldas':[td.get_text(strip=True).replace('\xa0',' ').strip() for td in div.select("div.megoldas_magyarazat table tr:nth-of-type(2) > td")],
                }
        if len(div.select('div.megoldas_magyarazat table tr:nth-of-type(4) > td'))>0: kerdes['magyarazat']=div.select('div.megoldas_magyarazat table tr:nth-of-type(4) > td')[0].get_text(strip=True).strip()
        return kerdes
    except Exception as e:
        print(div)
        raise e

def pairing(div):
    try:
        kerdes={'type':4,
                'leiras':div.find('div',class_='asszociacios_leiras').get_text(strip=True),
                'kerdesek':[{
                    'sorszam':tr.select('span.kerdes_csorszam_2')[0].get_text(strip=True),
                    'leiras':tr.select('span.kerdes_leiras')[0].get_text(strip=True),
                    'megoldas':tr.select('span.kerdes_csorszam_2')[1].get_text(strip=True)
                    } for tr in div.select('div.asszociacios_feladat table:nth-of-type(1) tr')],
                'valaszok':[[td.get_text(strip=True).replace('\xa0',' ').strip() for td in [tr.contents[0],tr.contents[2]]] for tr in div.select('div.asszociacios_feladat table:nth-of-type(2) tr')]
                }
        return kerdes
    except Exception as e:
        print(div)
        raise e

def main():
    try:
        cookiejar=login()
    except LoginException as e:
        print("Nem sikerült bejelentkezni. A weboldal üzenete: "+str(e))
        exit()
    tasks=getfejezets(getfcsops(cookiejar),cookiejar)
    kerdesek=[{'focim':task['fcsop']['title'], 'alcim':task['fejezet']['title'] if task['fejezet'] else None, 'kerdesek':crawlfejezet(cookiejar, task['fcsop'], task['fejezet'])} for task in tasks]
    print(kerdesek)

if __name__ == "__main__":
    main()
