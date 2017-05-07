#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import requests, re, getpass, configparser, json, argparse, sys, datetime
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
    debug("Preparing to log in", 3)
    try:
        cp=configparser.RawConfigParser()
        cp.read('login.ini')
        login={'login[username]':cp.get('zarovizsga', 'user'),'login[password]':cp.get('zarovizsga','pass'),'login[loggedin]':'BELÉP'}
        debug("Login info read from file", 2)
    except:
        debug("Failed to read login.ini", 2)
        login={'login[username]':input('E-mail cím? '),'login[password]':getpass.getpass('Jelszó? '),'login[loggedin]':'BELÉP'}
    debug("Login array: "+str(login), 3)
    try:
        debug("Attempting login", 2)
        r=requests.post('http://aok.zarovizsga.hu/login_box/',data=login)
        r.encoding="UTF-8"
        soup=BeautifulSoup(r.text,"lxml")
        errordiv=soup.find("div",class_="error")
        assert errordiv is None
    except AssertionError as e:
        raise LoginException(errordiv.string.strip())
    debug("Logged in successfully")
    debug("Login PHPSESSID: "+r.cookies.get('PHPSESSID'), 3)
    return r.cookies

def crawlfejezet(cookiejar, fcsop, fejezet=None):
    global jar
    kerdesgy=[]
    debug('Entering category "'+fcsop['title']+(('", subcategory "'+fejezet['title']+'"') if fejezet else '"'), 1)
    params={"fcsop[fcsop]":fcsop['fcsop'], "fcsop[fejezet]":fejezet['fej'] if fejezet else None, "feladatcsoport_kerdes_lista[kerdes_pager][pg]": 1}
    gotqs=20
    while gotqs>0:
        debug('Loading page '+str(params["feladatcsoport_kerdes_lista[kerdes_pager][pg]"]), 2)
        r=requests.get(baseurl, params=params, cookies=cookiejar)
        debug("Retrieved "+r.url, 3)
        r.encoding="utf-8"
        soup=BeautifulSoup(r.text, "lxml")
        kerdess=soup.find_all('div', class_='kerdes_reszletes_belso')
        gotqs=len(kerdess)
        for kerdes in kerdess:
            pvf=kerdes.find('div', class_='probavizsga_feladat')
            if(pvf):
                ktype=pvf.table['title']
            if(pvf is None):
                debug("\tFound pairing question", 4)
                kerdesgy.append(pairing(kerdes))
            elif(ktype==u"I. Egyszerü feleletválasztás GY."):
                debug("\tFound simple question", 4)
                kerdesgy.append(simplechoice(kerdes))
            elif(ktype==u"II. Többszörös feleletválasztás GY"):
                debug("\tFound multiple choice question", 4)
                kerdesgy.append(multiplechoice(kerdes))
            elif(ktype==u"IV. Relációanalizis GY"):
                debug("\tFound relanal question", 4)
                kerdesgy.append(relanal(kerdes))
            else:
                raise Exception("Ismeretlen kérdéstípus!")
            try:
                if(kerdesgy[-2]['sorszam']==kerdesgy[-1]['sorszam']):
                    del kerdesgy[-1]
                    debug("Discarding duplicate question "+kerdesgy[-1]['sorszam'])
                if(kerdesgy[-2]['magyarazat']==kerdesgy[-1]['magyarazat']):
                    kerdesgy[-2]['magyarazat']="Magyarázat: ld. következő kérdés"
                    debug("Discarding duplicate explanation for question "+kerdesgy[-1]['sorszam'])
            except IndexError:
                pass
            except KeyError:
                pass
        debug(str(gotqs)+' questions gathered on this page.', 2)
        params["feladatcsoport_kerdes_lista[kerdes_pager][pg]"]+=1
    debug(str(len(kerdesgy))+' questions gathered in this '+('sub' if fejezet else '')+'category.', 1)
    debug('Exiting category "'+fcsop['title']+(('", subcategory "'+fejezet['title']+'"') if fejezet else ""), 2)
    r=requests.get(baseurl, params={"fcsop[vissza]":'true'}, cookies=cookiejar)
    return kerdesgy

def getfcsops(cookiejar):
    r=requests.get(baseurl, cookies=cookiejar)
    r.encoding="utf-8"
    soup=BeautifulSoup(r.text,"lxml")
    return [{'title': div.a.string.strip(), 'fcsop':fcsop_re.search(div.a['href']).group(1)} for div in soup.find_all("div", class_="feladatcsoportok") if fcsop_re.search(div.a['href'])]

def getfejezets(fcsop, cookiejar):
    r=requests.get(baseurl, params={"fcsop[fcsop]":fcsop['fcsop']}, cookies=cookiejar)
    r.encoding="utf-8"
    soup=BeautifulSoup(r.text,"lxml")
    fejezets=[{'title': div.a.string.strip(), 'fej':fejezetek_re.search(div.a['href']).group(1)} for div in soup.find_all("div", class_="feladatcsoportok") if fejezetek_re.search(div.a['href'])]
    if(fejezets):
        debug('Found '+str(len(fejezets))+' subcategories in category "'+fcsop['title']+u'"')
        return fejezets
    else:
        print(u'No subcategories found in category "'+fcsop['title']+u'"')
        return [None]
    r=requests.get(baseurl, params={"fcsop[vissza]":'true'}, cookies=cookiejar)


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

def simplechoicets(k):
    return r'\multicolumn{3}{|p{\columnwidth - 2\tabcolsep - 2\arrayrulewidth}|}{'+latex(k['leiras'])+"}\\\\\n"+'\\\\\n'.join([latex(v[0])+r"&\multicolumn{2}{p{\columnwidth - 1.5em - 4\tabcolsep - 2\arrayrulewidth}|}{"+latex(v[1])+r'}' for v in k['valaszok']])+"\\\\\n\\hline\n\\multicolumn{3}{|p{\\columnwidth - 2\\tabcolsep - 2\\arrayrulewidth}|}{Megoldás: "+latex(" ".join(k['megoldas']))+"}\\\\\n"+(("\\multicolumn{3}{|p{\\columnwidth - 2\\tabcolsep - 2\\arrayrulewidth}|}{ "+latex(k['magyarazat'])+"}\\\\\n") if 'magyarazat' in k else "")+"\\hline\n"

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
    
def multiplechoicets(k):
    return r'\multicolumn{3}{|p{\columnwidth - 2\tabcolsep - 2\arrayrulewidth}|}{'+latex(k['leiras'])+"}\\\\\n"+'\\\\\n'.join([latex(v[0])+r"&\multicolumn{2}{p{\columnwidth - 1.5em - 4\tabcolsep - 2\arrayrulewidth}|}{"+latex(v[1])+r'}' for v in k['elemi_valaszok']])+'\\\\\n\\hline\n'+'\\\\\n'.join([latex(v[0])+r"&\multicolumn{2}{p{\columnwidth - 1.5em - 4\tabcolsep - 2\arrayrulewidth}|}{"+latex(v[1])+r'}' for v in k['valaszok']])+"\\\\\n\\hline\n\\multicolumn{3}{|p{\\columnwidth - 2\\tabcolsep - 2\\arrayrulewidth}|}{Megoldás: "+latex(" ".join(k['megoldas']))+"}\\\\\n"+(("\\multicolumn{3}{|p{\\columnwidth - 2\\tabcolsep - 2\\arrayrulewidth}|}{ "+latex(k['magyarazat'])+"}\\\\\n") if 'magyarazat' in k else "")+"\\hline\n"

def relanal(div):
    try:
        kerdes={'type':3,
                'sorszam':str(div.span.label.get_text(strip=True)),
                'leiras':div.find('div',class_='probavizsga_kerdes_leiras').get_text(strip=True),
                "valaszok":[[td.get_text(strip=True).replace('\xa0',' ').strip() for td in tr.contents[1:]] for tr in div.select("div.probavizsga_feladat table tr")],
                'megoldas':[td.get_text(strip=True).replace('\xa0',' ').strip() for td in div.select("div.megoldas_magyarazat table tr:nth-of-type(2) > td")],
                }
        if len(div.select('div.megoldas_magyarazat table tr:nth-of-type(4) > td'))>0: kerdes['magyarazat']=div.select('div.megoldas_magyarazat table tr:nth-of-type(4) > td')[0].get_text(strip=True).strip()
        return kerdes
    except Exception as e:
        print(div)
        raise e

def relanalts(k):
    return r'\multicolumn{3}{|p{\columnwidth - 2\tabcolsep - 2\arrayrulewidth}|}{'+latex(k['leiras'])+"}\\\\\n"+'\\\\\n'.join([latex(v[0])+r"&\multicolumn{2}{p{\columnwidth - 1.5em - 4\tabcolsep - 2\arrayrulewidth}|}{"+latex(v[1])+r'}' for v in k['valaszok']])+"\\\\\n\\hline\n\\multicolumn{3}{|p{\\columnwidth - 2\\tabcolsep - 2\\arrayrulewidth}|}{Megoldás: "+latex(" ".join(k['megoldas']))+"}\\\\\n"+(("\\multicolumn{3}{|p{\\columnwidth - 2\\tabcolsep - 2\\arrayrulewidth}|}{ "+latex(k['magyarazat'])+"}\\\\\n") if 'magyarazat' in k else "")+"\\hline\n"

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
        kerdes['sorszam']=kerdes['kerdesek'][0]['sorszam']+'-'+re.search(r'(\d+)$', kerdes['kerdesek'][-1]['sorszam']).group(1)
        for k in kerdes['kerdesek']: k['sorszam']=re.search(r'(\d+)$',k['sorszam']).group(1)
        return kerdes
    except Exception as e:
        print(div)
        raise e

def pairingts(k):
    return r'\multicolumn{3}{|p{\columnwidth - 2\tabcolsep - 2\arrayrulewidth}|}{'+latex(k['leiras'])+"}\\\\\n"+'\\\\\n'.join([latex(l['sorszam'])+'&'+latex(l['leiras'])+'&'+latex(l['megoldas']) for l in k['kerdesek']])+'\\\\\n\\hline\n'+'\\\\\n'.join([latex(v[0])+r"&\multicolumn{2}{p{\columnwidth - 1.5em - 4\tabcolsep - 2\arrayrulewidth}|}{"+latex(v[1])+r'}' for v in k['valaszok']])+"\\\\\n\\hline\n"

typesetters=[lambda x:"", simplechoicets, multiplechoicets, relanalts, pairingts]

def latex(sz):
    replacements = {r'#':r'\#',
               r'$':r'\$',
               r'%':r'\%',
               r'^':r'\^{}',
               r'&':r'\&',
               r'_':r'\_',
               r'{':'\{',
               r'}':'\}',
               r'~':r'$\sim$',
               '\\':r'\textbackslash',
               #'μ':'$\\mu$',
               #'α':'$\\alpha$',
               #'β':'$\\beta$',
               #'γ':'$\\gamma$',
               #'°':'$^{\\circ}$',
               #'→':'$\,\\to\,$',
               #'±':"$\\pm$",
               #'≥':'$\\geq$',
               #'≤':'$\\leq$',
               #'½':'$\\frac{1}{2}$'
               }
    substrs = sorted(replacements.keys(), key=len, reverse=True)
    regexp = re.compile('|'.join(map(re.escape, substrs)))
    return regexp.sub(lambda match: replacements[match.group(0)], sz)

def debug(info, level=1):
    if(args.verbose>=level):
        print((("debug "+str(level)+": ") if args.verbose>1 else "")+str(info), file=sys.stderr)

def main():
    if(args.typeset_only is None):
        try:
            cookiejar=login()
        except LoginException as e:
            print("Nem sikerült bejelentkezni. A weboldal üzenete: "+str(e))
            exit()
        fcsops=getfcsops(cookiejar)
        tasks=[{'fcsop':fcsop, 'fejezets':getfejezets(fcsop, cookiejar)} for fcsop in fcsops]
        kerdesek=[{'fcsop':task['fcsop'], 'fejezets':[{'fejezet':fejezet, 'kerdesek':crawlfejezet(cookiejar, task['fcsop'], fejezet)} for fejezet in task['fejezets']]} for task in tasks]
    else:
        with open(args.typeset_only, 'r') as f:
            debug('Opening file '+args.typeset_only)
            kerdesek=json.load(f)
    if(args.retrieve_only):
        with open(args.retrieve_only, 'w') as f:
            debug('Writing '+args.retrieve_only)
            json.dump(kerdesek, f)
            debug('Exiting without typesetting')
        exit()
    debug('Post-processing')
    debug('Typesetting')
    with open(args.output, 'w') as f:
        f.write(r'''\documentclass[openany]{book}
\usepackage[utf8]{inputenc}
\usepackage[magyar]{babel}
\usepackage{t1enc}
\usepackage{tabularx}
\usepackage{calc}
\usepackage{fontspec}
\usepackage[a4paper,margin=.5in,lmargin=1in]{geometry}
\pagestyle{headings}
\setlength{\parindent}{0pt}
\title{Záróvizsga kérdések}
\setmainfont{FreeSans}
\begin{document}
\maketitle
\tableofcontents
''')
        for fcsop in kerdesek:
            f.write(r'\chapter{'+fcsop['fcsop']['title']+'}\n')
            for fejezet in fcsop['fejezets']:
                if(fejezet['fejezet']):
                    f.write(r'\section{'+fejezet['fejezet']['title']+'}\n')
                for kerdes in fejezet['kerdesek']:
                    f.write('\\begin{tabular}{|p{1.5em}p{\\columnwidth - 3em - 6\\tabcolsep - 2\\arrayrulewidth}p{1.5em}|}\n\\hline\n\\multicolumn{3}{|p{\\columnwidth - 2\\tabcolsep -2\\arrayrulewidth}|}{'+kerdes['sorszam']+'}\\\\\n\\hline\n')
                    f.write(typesetters[kerdes['type']](kerdes))
                    f.write('\\end{tabular}\n\n')
        f.write(r'\end{document}')
    

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='Bőbeszédű mód hibakereséshez', action="count", default=0)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('-r', '--retrieve-only', help='Csak a kérdések letöltése és kiírása .json formátumba', metavar="FILENAME", nargs='?', const='zarovizsgakerdesek.json', default=None)
    group.add_argument('-t', '--typeset-only', help='A letöltött .json formátumból .pdf készítése', metavar="FILENAME", nargs='?', const='zarovizsgakerdesek.json', default=None)
    parser.add_argument('-o', '--output', help='Kimeneti fájl', default='zarovizsga.tex')
    args=parser.parse_args()
    main()
