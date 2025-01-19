# Webshop Informatičke Opreme

Ovaj projekt implementira backend i frontend rješenje za webshop specijaliziran za prodaju informatičke opreme. Sustav omogućava registraciju i prijavu korisnika, upravljanje proizvodima, kategorijama, popustima, narudžbama, načinima isporuke i korisničkom podrškom.

## Sadržaj
- [Opis projekta](#opis-projekta)
- [Instalacija](#instalacija)
- [Struktura projekta](#struktura-projekta)
- [Ključne funkcionalnosti](#ključne-funkcionalnosti)
- [Tehnologije](#tehnologije)
- [Pokretanje aplikacije](#pokretanje-aplikacije)
- [Autori](#autori)

## Opis projekta

Sustav podržava sljedeće značajke:
- Pregled i kategorizaciju proizvoda.
- Upravljanje korisnicima (registracija, prijava i ažuriranje).
- Implementaciju košarice i procesa narudžbe.
- Uporabu popusta i kupona za optimizaciju cijena.
- Praćenje narudžbi i upravljanje isporukom.
- Administrativni panel za upravljanje svim segmentima webshopa.

Projekt je realiziran u sklopu kolegija **Baze podataka II** na Fakultetu informatike u Puli.

## Instalacija

### 1. Preduvjeti
- Python 3.8+
- MySQL Server
- Virtualno okruženje za Python

### 2. Postavljanje okruženja

1. Klonirajte repozitorij:
   ```bash
   git clone <url_repozitorija>
   cd webshop
   ```

2. Instalirajte potrebne pakete:
   ```bash
   pip install -r requirements.txt
   ```

3. Konfigurirajte MySQL bazu podataka:
   - Kreirajte bazu podataka prema specifikacijama u `app.py`.
   - Importirajte tablice koristeći MySQL Workbench ili CLI.

4. Pokrenite aplikaciju:
   ```bash
   python app.py
   ```

## Struktura projekta

- **`app.py`**: Glavna aplikacija koja upravlja rutama i poslovnom logikom sustava.
- **HTML datoteke**: Predlošci za različite funkcionalnosti (prikaz korisničkog i administrativnog sučelja).
- **`requirements.txt`**: Lista svih Python paketa potrebnih za pokretanje aplikacije.

### Važni direktoriji
- `/templates`: Sadrži HTML predloške za korisnički i administrativni panel.
- `/static`: Sadrži CSS stilove i ostale statičke resurse.
- `/data`: Datoteke vezane za bazu podataka i početne podatke.

## Ključne funkcionalnosti

1. **Korisnički sustav**
   - Registracija i prijava.
   - Upravljanje podacima korisnika.

2. **Proizvodi i kategorije**
   - Pregled proizvoda prema kategorijama.
   - Administracija proizvoda, kategorija i recenzija.

3. **Narudžbe i košarica**
   - Dodavanje proizvoda u košaricu.
   - Prikaz i potvrda narudžbi.

4. **Popusti i kuponi**
   - Kreiranje i upravljanje promocijama.

5. **Administrativni panel**
   - Upravljanje svim entitetima iz korisničkog sučelja.

## Tehnologije

- **Frontend**: HTML5, CSS3
- **Backend**: Flask
- **Baza podataka**: MySQL
- **Autentikacija**: Bcrypt

## Pokretanje aplikacije

1. Pokrenite aplikaciju lokalno:
   ```bash
   flask run
   ```

2. Posjetite [localhost](http://127.0.0.1:5000) u web pregledniku.

## Autori
- **Loren Bažon**
- **Morena Martan**
- **Bruno Rebić**
- **Fran Barba**
- **Josip Milković**
- **Leo Hrvojić**

### Mentori:
- **doc. dr. sc. Goran Oreški**
- **mag. inf. Romeo Šajina**

_Pula, 2024._
