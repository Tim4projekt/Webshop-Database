Webshop Informatičke Opreme
Ovaj projekt implementira backend i frontend rješenje za webshop specijaliziran za prodaju informatičke opreme. Sustav omogućava registraciju i prijavu korisnika, upravljanje proizvodima, kategorijama, popustima, narudžbama, načinima isporuke i korisničkom podrškom.

Sadržaj
Opis projekta
Instalacija
Struktura projekta
Ključne funkcionalnosti
Tehnologije
Pokretanje aplikacije
Autori
Opis projekta
Sustav podržava sljedeće značajke:

Pregled i kategorizaciju proizvoda.
Upravljanje korisnicima (registracija, prijava i ažuriranje).
Implementaciju košarice i procesa narudžbe.
Uporabu popusta i kupona za optimizaciju cijena.
Praćenje narudžbi i upravljanje isporukom.
Administrativni panel za upravljanje svim segmentima webshopa.
Projekt je realiziran u sklopu kolegija Baze podataka II na Fakultetu informatike u Puli.

Instalacija
1. Preduvjeti
Python 3.8+
MySQL Server
Virtualno okruženje za Python
2. Postavljanje okruženja
Klonirajte repozitorij:

bash
Copy
Edit
git clone <url_repozitorija>
cd webshop
Instalirajte potrebne pakete:

bash
Copy
Edit
pip install -r requirements.txt
Konfigurirajte MySQL bazu podataka:

Kreirajte bazu podataka prema specifikacijama u app.py.
Importirajte tablice koristeći MySQL Workbench ili CLI.
Pokrenite aplikaciju:

bash
Copy
Edit
python app.py
Struktura projekta
app.py: Glavna aplikacija koja upravlja rutama i poslovnom logikom sustava.
HTML datoteke: Predlošci za različite funkcionalnosti (prikaz korisničkog i administrativnog sučelja).
requirements.txt: Lista svih Python paketa potrebnih za pokretanje aplikacije.
Važni direktoriji
/templates: Sadrži HTML predloške za korisnički i administrativni panel.
/static: Sadrži CSS stilove i ostale statičke resurse.
/data: Datoteke vezane za bazu podataka i početne podatke.
Ključne funkcionalnosti
Korisnički sustav

Registracija i prijava.
Upravljanje podacima korisnika.
Proizvodi i kategorije

Pregled proizvoda prema kategorijama.
Administracija proizvoda, kategorija i recenzija.
Narudžbe i košarica

Dodavanje proizvoda u košaricu.
Prikaz i potvrda narudžbi.
Popusti i kuponi

Kreiranje i upravljanje promocijama.
Administrativni panel

Upravljanje svim entitetima iz korisničkog sučelja.
Tehnologije
Frontend: HTML5, CSS3
Backend: Flask
Baza podataka: MySQL
Autentikacija: Bcrypt
Pokretanje aplikacije
Pokrenite aplikaciju lokalno:

bash
Copy
Edit
flask run
Posjetite localhost u web pregledniku.

Autori
Loren Bažon
Morena Martan
Bruno Rebić
Fran Barba
Josip Milković
Leo Hrvojić
Mentori:

doc. dr. sc. Goran Oreški
mag. inf. Romeo Šajina
Pula, 2024.
