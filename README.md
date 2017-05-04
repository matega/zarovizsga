# SE-ÁOK záróvizsga kigyűjtő

Work in progress

## Mi ez?

Ez két python program. Az egyik (`medtest.py`) a telefonos alkalmazás letöltött kérdéseit gyűjti ki, a másik (`zarovizsga.py`) az online felületről menti le a kérdéseket.

## Mi van kész?

### medtest.py

* Képes feltérképezni a kategóriákat és a kategóriákon belüli fejezeteket
* Képes importálni a kategóriák kérdéseit
* TODO: Párosításos kérdések összegyűjtése
* TODO: Kimenet PDF-ben (valószínűleg HTML-en keresztül)
* TODO: szebb kód

Használat: Másold az Androidos alkalmazás adatait (`/sdcard/medtest/(hex könyvtárnév)/*`) a python fájl mellé a `medtest` mappába, majd futtasd.

## zarovizsga.py

* Képes beolvasni a `login.ini`-ből a felhasználónevet és jelszót, vagy bekérni őket a parancssorból
* Képes bejelentkezni az oldalra (enélkül nem lehet letölteni a kérdéseket)
* Képes feltérképezni a kategóriákat és a kategóriákon belüli fejezeteket
* Képes feltérképezni a kategóriák kérdéseit
* TODO: Kérdések kigyűjtése az oldalakból
* TODO: Kimenet PDF-ben (valószínűleg HTML-en keresztül)
* TODO: szebb kód

Használat: Futtasd a programot. Jelentkezz be. 
