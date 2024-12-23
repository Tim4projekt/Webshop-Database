from flask import Flask, jsonify, request, render_template, redirect, session, url_for, request
from flask_cors import CORS
from datetime import date
from decimal import Decimal
import MySQLdb

app = Flask(__name__)
CORS(app)  # Omogućava CORS

# Postavljanje tajnog ključa (SECRET_KEY) za Flask aplikaciju
app.secret_key = 'neki_skriveni_kljuc_koji_je_jedinstven'

# Konfiguracija baze podataka
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'webshop'
}

@app.route('/')
def home():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id, p.naziv, p.opis, p.cijena, k.naziv AS kategorija_naziv
        FROM proizvodi p
        JOIN kategorije_proizvoda k ON p.kategorija_id = k.id
    """)
    proizvodi = cursor.fetchall()
    cursor.close()
    db.close()

    kategorije = {}
    for proizvod in proizvodi:
        kategorija = proizvod[4]
        if kategorija not in kategorije:
            kategorije[kategorija] = []
        kategorije[kategorija].append(proizvod)

    return render_template('index.html', kategorije=kategorije)

@app.route('/kategorija/<kategorija_naziv>')
def prikazi_kategoriju(kategorija_naziv):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id, p.naziv, p.opis, p.cijena
        FROM proizvodi p
        JOIN kategorije_proizvoda k ON p.kategorija_id = k.id
        WHERE k.naziv = %s
    """, (kategorija_naziv,))
    proizvodi = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('kategorija.html', proizvodi=proizvodi, kategorija=kategorija_naziv)

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Briše user_id iz sesije
    return redirect(url_for('prijava'))

@app.route('/prijava', methods=['GET', 'POST'])
def prijava():
    if request.method == 'GET':
        return render_template('prijava.html')  # Ako koristiš HTML stranicu
    elif request.method == 'POST':
        data = request.form
        email = data['email']
        lozinka = data['lozinka']
        
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM korisnici WHERE email = %s", (email,))
        korisnik = cursor.fetchone()

        if korisnik and korisnik[4] == lozinka:  # Provjeri lozinku
            session['user_id'] = korisnik[0]  # Spremi korisnikovo ID u sesiju
            return redirect(url_for('home'))  # Preusmjeri na početnu stranicu ili drugu stranicu
        else:
            return jsonify({"message": "Neispravan email ili lozinka"}), 400

@app.route('/kosarica', methods=['GET'])
def prikazi_kosaricu():
    korisnik_id = session.get('user_id', 1)  # Ako korisnik nije prijavljen, postavite korisnik_id na 1
    
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    # Dohvatite stavke iz košarice
    cursor.execute("""
        SELECT p.id, p.naziv, p.cijena, k.kolicina 
        FROM proizvodi p 
        JOIN kosarica k ON p.id = k.proizvod_id 
        WHERE k.korisnik_id = %s
    """, (korisnik_id,))
    stavke = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('kosarica.html', stavke=stavke)

@app.route('/api/kosarica', methods=['POST'])
def dodaj_u_kosaricu():
    data = request.json
    proizvod_id = data['proizvodId']
    korisnik_id = session.get('user_id', 1)  # Ako korisnik nije prijavljen, koristi korisnik_id = 1
    
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    # Provjerite da li proizvod već postoji u košarici
    cursor.execute("SELECT * FROM kosarica WHERE korisnik_id = %s AND proizvod_id = %s", (korisnik_id, proizvod_id))
    stavka = cursor.fetchone()

    if stavka:
        # Ako stavka već postoji, povećajte količinu
        cursor.execute("UPDATE kosarica SET kolicina = kolicina + 1 WHERE korisnik_id = %s AND proizvod_id = %s",
                       (korisnik_id, proizvod_id))
    else:
        # Ako stavka ne postoji, dodajte novu
        cursor.execute("INSERT INTO kosarica (korisnik_id, proizvod_id, kolicina) VALUES (%s, %s, %s)",
                       (korisnik_id, proizvod_id, 1))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"message": "Proizvod je dodan u košaricu!"}), 201

@app.route('/api/kosarica/uredi', methods=['POST'])
def uredi_kosaricu():
    data = request.form
    proizvod_id = data['proizvodId']
    nova_kolicina = data['kolicina']
    korisnik_id = session.get('user_id', 1)  # Ako korisnik nije prijavljen, koristi korisnik_id = 1

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    # Ažurirajte količinu u košarici
    cursor.execute("UPDATE kosarica SET kolicina = %s WHERE korisnik_id = %s AND proizvod_id = %s",
                   (nova_kolicina, korisnik_id, proizvod_id))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"message": "Količina uspješno ažurirana!"}), 200

@app.route('/api/kosarica/izbrisi', methods=['POST'])
def izbrisi_stavku():
    data = request.json
    proizvod_id = data.get('proizvodId')
    korisnik_id = session.get('user_id', 1)  # Ako korisnik nije prijavljen, koristi korisnik_id = 1

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    # Uklonite stavku iz košarice
    cursor.execute("DELETE FROM kosarica WHERE korisnik_id = %s AND proizvod_id = %s", (korisnik_id, proizvod_id))
    db.commit()

    cursor.close()
    db.close()

    return jsonify({'success': True, 'message': 'Stavka je uspješno izbrisana.'}), 200

@app.route('/proizvod/<int:proizvod_id>', methods=['GET'])
def proizvod_detail(proizvod_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM proizvodi WHERE id = %s", (proizvod_id,))
    proizvod = cursor.fetchone()
    cursor.close()
    db.close()
    
    if proizvod:
        return render_template('proizvod_detail.html', proizvod=proizvod)
    else:
        return jsonify({"message": "Proizvod nije pronađen."}), 404
    
    
@app.route('/registracija', methods=['GET', 'POST'])
def registracija():
    if request.method == 'GET':
        return render_template('registracija.html')  # Prikaz forme za registraciju
    elif request.method == 'POST':
        data = request.json
        ime = data['ime']
        prezime = data['prezime']
        email = data['email']
        lozinka = data['lozinka']
        adresa = data.get('adresa')  # Opcionalno
        grad = data.get('grad')  # Opcionalno
        telefon = data.get('telefon')  # Opcionalno

        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()

        # Provjera postoji li već korisnik s istim emailom
        cursor.execute("SELECT * FROM korisnici WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            db.close()
            return jsonify({"message": "Email već postoji!"}), 400

        # Dodavanje korisnika s dodatnim podacima
        cursor.execute(
            """
            INSERT INTO korisnici 
            (ime, prezime, email, lozinka, adresa, grad, telefon, tip_korisnika, datum_registracije) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'kupac', CURDATE())
            """,
            (ime, prezime, email, lozinka, adresa, grad, telefon)
            
        )
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({"message": "Registracija uspješna! Vratite se natrag na proizvode."}), 201



@app.route('/narudzba', methods=['GET', 'POST'])
def narudzba():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))  # Preusmjerenje na prijavu ako nije prijavljen
    
    korisnik_id = session['user_id']
    
    # Preuzimanje podataka iz tablice kosarica za određenog korisnika
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    
    # Prvo uzimamo proizvode u košarici korisnika
    cursor.execute("SELECT p.id, p.naziv, p.cijena, k.kolicina FROM kosarica k JOIN proizvodi p ON k.proizvod_id = p.id WHERE k.korisnik_id = %s", (korisnik_id,))
    proizvodi = cursor.fetchall()
    
    # Ako forma za kreiranje narudžbe nije poslana, prikazujemo proizvode i načine isporuke
    if request.method == 'GET':
        cursor.execute("SELECT * FROM nacini_isporuke")
        nacini_isporuke = cursor.fetchall()
        
        # Pretvaranje tuple-a u rječnik
        nacini_isporuke = [
            {'id': nacin[0], 'naziv': nacin[1], 'opis': nacin[2], 'cijena': float(nacin[3]), 'trajanje': nacin[4]}
            for nacin in nacini_isporuke
        ]
        
        # Izračunavanje ukupne cijene košarice
        ukupna_cijena = sum(Decimal(proizvod[2]) * proizvod[3] for proizvod in proizvodi)  # Pretvaranje cijene u Decimal
        
        db.close()
        
        return render_template('narudzba.html', proizvodi=proizvodi, nacini_isporuke=nacini_isporuke, ukupna_cijena=ukupna_cijena)
    
    # Ako je forma za narudžbu poslana
    if request.method == 'POST':
        # Uzimamo podatke iz forme
        nacin_isporuke_id = request.form['nacin_isporuke']  # ID odabranog načina isporuke
        ukupna_cijena = Decimal(request.form['ukupna_cijena'])  # Pretvorba ukupne cijene u Decimal
        kupon_kod = request.form.get('kupon', '').strip()  # Uneseni kupon
        
        # Dohvati cijenu dostave iz načina isporuke
        cursor.execute("SELECT cijena FROM nacini_isporuke WHERE id = %s", (nacin_isporuke_id,))
        cijena_dostave = Decimal(cursor.fetchone()[0])  # Pretvaramo cijenu dostave u Decimal
        
        # Izračunaj ukupni iznos (košarica + dostava)
        ukupni_iznos = ukupna_cijena + cijena_dostave
        
        # Provjeravamo je li kupon unesen i postoji li u bazi
        if kupon_kod:
            cursor.execute("""
                SELECT * FROM kuponi WHERE kod = %s AND datum_pocetka <= %s AND datum_zavrsetka >= %s
            """, (kupon_kod, date.today(), date.today()))
            kupon = cursor.fetchone()
            
            if kupon:
                # Ako je kupon valjan, primjenjujemo popust
                popust = Decimal(kupon[2])  # postotak popusta
                popust_iznos = (popust / 100) * ukupni_iznos
                ukupni_iznos -= popust_iznos  # Smanjujemo ukupni iznos za popust
                kupon_id = kupon[0]  # ID kupona za spremanje u narudžbu
            else:
                kupon_id = None  # Ako kupon nije valjan
        else:
            kupon_id = None  # Ako kupon nije unesen
        
        # Kreiramo novu narudžbu
        cursor.execute(""" 
            INSERT INTO narudzbe (korisnik_id, datum_narudzbe, status_narudzbe, ukupna_cijena, nacin_isporuke_id, kupon_id) 
            VALUES (%s, %s, 'u obradi', %s, %s, %s)
        """, (korisnik_id, date.today(), ukupni_iznos, nacin_isporuke_id, kupon_id))
        
        # Dobijamo ID nove narudžbe
        cursor.execute("SELECT LAST_INSERT_ID()")
        narudzba_id = cursor.fetchone()[0]
        
        # Prebacujemo stavke iz košarice u stavke_narudzbe
        for proizvod in proizvodi:
            proizvod_id = proizvod[0]  # id proizvoda
            kolicina = proizvod[3]     # količina proizvoda
            
            cursor.execute("""
                INSERT INTO stavke_narudzbe (narudzba_id, proizvod_id, kolicina) 
                VALUES (%s, %s, %s)
            """, (narudzba_id, proizvod_id, kolicina))
        
        # Unos u tablicu placanja
        cursor.execute("""
            INSERT INTO placanja (narudzba_id, iznos, datum_placanja)
            VALUES (%s, %s, %s)
        """, (narudzba_id, ukupni_iznos, date.today()))
        
        # Unos u tablicu racuni
        cursor.execute("""
            INSERT INTO racuni (korisnik_id, narudzba_id, iznos, datum_izdavanja)
            VALUES (%s, %s, %s, %s)
        """, (korisnik_id, narudzba_id, ukupni_iznos, date.today()))
        
        # Brisanje svih stavki iz košarice nakon što je narudžba kreirana
        cursor.execute("DELETE FROM kosarica WHERE korisnik_id = %s", (korisnik_id,))
        
        # Potvrda i preusmjeravanje
        db.commit()
        db.close()
        
        return redirect(url_for('home'))  # Preusmjeravamo na početnu stranicu nakon uspješne narudžbe


@app.route('/wishlist', methods=['GET'])
def wishlist():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    korisnik_id = session['user_id']
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        # Dohvati proizvode iz wishlist-a
        cursor.execute("""
            SELECT p.id, p.naziv, p.cijena, p.opis 
            FROM wishlist w 
            JOIN proizvodi p ON w.proizvod_id = p.id 
            WHERE w.korisnik_id = %s
        """, (korisnik_id,))

        proizvodi = cursor.fetchall()
        print("Proizvodi u wishlist-u:", proizvodi)  # Za provjeru u konzoli
    finally:
        db.close()

    if not proizvodi:
        return render_template('wishlist.html', proizvodi_u_wishlistu=None)

    return render_template('wishlist.html', proizvodi_u_wishlistu=proizvodi)


@app.route('/api/wishlist', methods=['POST'])
def api_wishlist():  # naziv endpointa je "api_wishlist"
    korisnik_id = session.get('user_id')
    if not korisnik_id:
        return jsonify({'message': 'Morate biti prijavljeni!'}), 401

    data = request.get_json()
    proizvod_id = data.get('proizvod_id')

    if not proizvod_id:
        return jsonify({'message': 'Proizvod nije definiran!'}), 400

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO wishlist (korisnik_id, proizvod_id) VALUES (%s, %s)",
            (korisnik_id, proizvod_id),
        )
        db.commit()
    except MySQLdb.IntegrityError:
        return jsonify({'message': 'Proizvod je već u wishlisti!'}), 409
    finally:
        db.close()

    return jsonify({'message': 'Proizvod uspješno dodan u wishlist!'})


@app.route('/wishlist/ukloni', methods=['POST'])
def ukloni_iz_wishliste():
    korisnik_id = session.get('user_id')
    if not korisnik_id:
        return jsonify({'message': 'Morate biti prijavljeni!'}), 401

    data = request.get_json()
    proizvod_id = data.get('proizvod_id')

    if not proizvod_id:
        return jsonify({'message': 'Proizvod nije definiran!'}), 400

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        cursor.execute(
            "DELETE FROM wishlist WHERE korisnik_id = %s AND proizvod_id = %s",
            (korisnik_id, proizvod_id),
        )
        db.commit()
    finally:
        db.close()

    return jsonify({'message': 'Proizvod je uspješno uklonjen iz wishliste!'})


@app.route('/wishlist/dodaj', methods=['POST'])
def dodaj_u_wishlist():
    korisnik_id = session.get('user_id')
    if not korisnik_id:
        return jsonify({'message': 'Morate biti prijavljeni!'}), 401

    data = request.get_json()
    proizvod_id = data.get('proizvod_id')

    if not proizvod_id:
        return jsonify({'message': 'Proizvod nije definiran!'}), 400

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        # Provjera postoji li proizvod već u wishlisti
        cursor.execute(
            "SELECT * FROM wishlist WHERE korisnik_id = %s AND proizvod_id = %s",
            (korisnik_id, proizvod_id)
        )
        if cursor.fetchone():
            return jsonify({'message': 'Proizvod je već u wishlisti.'}), 400

        # Dodavanje proizvoda u wishlistu
        cursor.execute(
            "INSERT INTO wishlist (korisnik_id, proizvod_id) VALUES (%s, %s)",
            (korisnik_id, proizvod_id)
        )
        db.commit()
    finally:
        db.close()

    return jsonify({'message': 'Proizvod je uspješno dodan u wishlistu!'})


@app.route('/podrska', methods=['GET', 'POST'])
def kreiraj_upit():
    message = ""  # Početno postavljanje poruke na prazan string
    if request.method == 'POST':
        # Provjeravamo je li korisnik prijavljen
        korisnik_id = session.get('user_id')
        if not korisnik_id:
            message = "Morate biti prijavljeni!"  # Greška ako nije prijavljen
            return render_template('podrska.html', message=message)

        # Dohvaćamo podatke iz forme
        tema = request.form.get('tema')
        poruka = request.form.get('poruka')

        if not tema or not poruka:
            message = "Tema i poruka su obavezna!"  # Greška ako nisu uneseni podaci
            return render_template('podrska.html', message=message)

        # Spremanje podataka u bazu
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO podrska_za_korisnike (korisnik_id, tema, poruka, status, datum_upita) "
                "VALUES (%s, %s, %s, 'otvoreno', CURDATE())",
                (korisnik_id, tema, poruka)
            )
            db.commit()
            message = "Upit je uspješno poslan!"  # Uspješan unos
        finally:
            db.close()

        return render_template('podrska.html', message=message)  # Vraćamo poruku korisniku

    # Ako je GET metoda, samo prikazujemo formu
    return render_template('podrska.html', message=message)  # Poruka u slučaju GET metode



@app.route('/preporuceni_proizvodi', methods=['GET', 'POST'])
def preporuceni_proizvodi():
    message = ""  # Početno postavljanje poruke na prazan string
    proizvodi = []  # Lista proizvoda koja će biti prikazana u formi

    if request.method == 'POST':
        # Provjeravamo je li korisnik prijavljen
        korisnik_id = session.get('user_id')
        if not korisnik_id:
            message = "Morate biti prijavljeni!"  # Greška ako nije prijavljen
            return render_template('preporuceni_proizvodi.html', message=message, proizvodi=proizvodi)

        # Dohvaćamo podatke iz forme
        proizvod_id = request.form.get('proizvod_id')
        razlog_preporuke = request.form.get('razlog_preporuke')

        if not proizvod_id or not razlog_preporuke:
            message = "Proizvod i razlog preporuke su obavezni!"  # Greška ako nisu uneseni podaci
            return render_template('preporuceni_proizvodi.html', message=message, proizvodi=proizvodi)

        # Spremanje podataka u bazu
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO preporuceni_proizvodi (korisnik_id, proizvod_id, razlog_preporuke) "
                "VALUES (%s, %s, %s)",
                (korisnik_id, proizvod_id, razlog_preporuke)
            )
            db.commit()
            message = "Proizvod je uspješno preporučen!"  # Uspješan unos
        finally:
            db.close()

        return render_template('preporuceni_proizvodi.html', message=message, proizvodi=proizvodi)  # Vraćamo poruku korisniku

    # Ako je GET metoda, dohvaćamo proizvode za prikazivanje u formi
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT id, naziv FROM proizvodi")  # Dohvaćamo ID i naziv proizvoda
    proizvodi = cursor.fetchall()  # Pohranjujemo proizvode u listu
    db.close()

    return render_template('preporuceni_proizvodi.html', message=message, proizvodi=proizvodi)




@app.route('/pracenje_isporuka', methods=['GET', 'POST'])
def pracenje_isporuka():
    korisnik_id = session.get('user_id')
    if not korisnik_id:
        flash('Morate biti prijavljeni!', 'error')
        return redirect(url_for('login'))  # Preusmjeri na stranicu za prijavu ako nije prijavljen

    # Provjeravamo je li korisnik administrator
    is_admin = session.get('is_admin', False)

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if is_admin:
        # Ako je admin, dohvaća sve narudžbe i njihov status isporuke
        query = """
        SELECT n.id, n.datum_narudzbe, pi.status_isporuke, pi.datum_isporuke, n.korisnik_id
        FROM narudzbe n
        LEFT JOIN pracenje_isporuka pi ON n.id = pi.narudzba_id
        """
    else:
        # Ako nije admin, dohvaća samo narudžbe korisnika
        query = """
        SELECT n.id, n.datum_narudzbe, pi.status_isporuke, pi.datum_isporuke
        FROM narudzbe n
        LEFT JOIN pracenje_isporuka pi ON n.id = pi.narudzba_id
        WHERE n.korisnik_id = %s
        """
    
    cursor.execute(query, (korisnik_id,) if not is_admin else ())
    narudzbe = cursor.fetchall()
    db.close()

    return render_template('pracenje_isporuka.html', narudzbe=narudzbe, is_admin=is_admin)



@app.route('/povrat', methods=['POST'])
def povrat_proizvoda():
    data = request.get_json()
    stavka_id = data.get('stavka_id')
    razlog = data.get('razlog')
    datum_povrata = data.get('datum_povrata')

    if not stavka_id or not razlog or not datum_povrata:
        return jsonify({'message': 'Svi podaci moraju biti uneseni!'}), 400

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO povrati_proizvoda (stavka_id, datum_povrata, razlog, status_povrata) "
            "VALUES (%s, %s, %s, 'u obradi')",
            (stavka_id, datum_povrata, razlog)
        )
        db.commit()
    finally:
        db.close()

    return jsonify({'message': 'Povrat proizvoda je uspješno poslan!'})


@app.route('/popust', methods=['POST'])
def dodaj_popust():
    data = request.get_json()
    proizvod_id = data.get('proizvod_id')
    postotak_popusta = data.get('postotak_popusta')
    datum_pocetka = data.get('datum_pocetka')
    datum_zavrsetka = data.get('datum_zavrsetka')

    if not proizvod_id or not postotak_popusta or not datum_pocetka or not datum_zavrsetka:
        return jsonify({'message': 'Svi podaci moraju biti uneseni!'}), 400

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO popusti (proizvod_id, postotak_popusta, datum_pocetka, datum_zavrsetka) "
            "VALUES (%s, %s, %s, %s)",
            (proizvod_id, postotak_popusta, datum_pocetka, datum_zavrsetka)
        )
        db.commit()
    finally:
        db.close()

    return jsonify({'message': 'Popust je uspješno dodan!'})

@app.route('/recenzije', methods=['GET', 'POST'])
def recenzije():
    message = ""  # Početno postavljanje poruke na prazan string
    proizvodi = []  # Lista proizvoda koja će biti prikazana u formi

    if request.method == 'POST':
        # Provjeravamo je li korisnik prijavljen
        korisnik_id = session.get('user_id')
        if not korisnik_id:
            message = "Morate biti prijavljeni!"  # Greška ako nije prijavljen
            return render_template('recenzije.html', message=message, proizvodi=proizvodi)

        # Dohvaćamo podatke iz forme
        proizvod_id = request.form.get('proizvod_id')
        ocjena = request.form.get('ocjena')
        komentar = request.form.get('komentar')

        # Provjera da su svi podaci uneseni
        if not proizvod_id or not ocjena or not komentar:
            message = "Proizvod, ocjena i komentar su obavezni!"  # Greška ako nisu uneseni podaci
            return render_template('recenzije.html', message=message, proizvodi=proizvodi)

        # Provjera da je ocjena u validnom rasponu (1-5)
        if int(ocjena) < 1 or int(ocjena) > 5:
            message = "Ocjena mora biti između 1 i 5!"  # Greška ako ocjena nije u ispravnom rasponu
            return render_template('recenzije.html', message=message, proizvodi=proizvodi)

        # Spremanje podataka u bazu
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO recenzije_proizvoda (proizvod_id, korisnik_id, ocjena, komentar, datum_recenzije) "
                "VALUES (%s, %s, %s, %s, CURDATE())",
                (proizvod_id, korisnik_id, ocjena, komentar)
            )
            db.commit()
            message = "Recenzija je uspješno poslana!"  # Uspješan unos
        finally:
            db.close()

        return render_template('recenzije.html', message=message, proizvodi=proizvodi)  # Vraćamo poruku korisniku

    # Ako je GET metoda, dohvaćamo proizvode za prikazivanje u formi
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT id, naziv FROM proizvodi")  # Dohvaćamo ID i naziv proizvoda
    proizvodi = cursor.fetchall()  # Pohranjujemo proizvode u listu
    db.close()

    return render_template('recenzije.html', message=message, proizvodi=proizvodi)




if __name__ == '__main__':
    app.run(debug=True)
