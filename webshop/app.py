from flask import Flask, jsonify, request, render_template, redirect, session, url_for, flash
from flask_cors import CORS
from datetime import date
from decimal import Decimal
import MySQLdb
import bcrypt


app = Flask(__name__)
CORS(app)  


app.secret_key = 'neki_skriveni_kljuc_koji_je_jedinstven'


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Babobilka156',
    'database': 'webshop'
}

db = MySQLdb.connect(**db_config)
cursor = db.cursor()

try:
    cursor.execute("SELECT id, lozinka FROM korisnici")
    korisnici = cursor.fetchall()

    for korisnik in korisnici:
        korisnik_id = korisnik[0]
        plain_lozinka = korisnik[1]


        if plain_lozinka.startswith("$2b$"):
            continue

       
        hashed_lozinka = bcrypt.hashpw(plain_lozinka.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        
        cursor.execute(
            "UPDATE korisnici SET lozinka = %s WHERE id = %s",
            (hashed_lozinka, korisnik_id)
        )

    
    db.commit()
    print("Sve lozinke su uspješno hashirane.")

except Exception as e:
    print(f"Greška: {e}")
    db.rollback()

finally:
    cursor.close()
    db.close()

@app.route('/home')
@app.route('/')
def home():
    page = int(request.args.get('page', 1))  
    per_page = 5  

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    cursor.execute("""
        SELECT p.id, p.naziv, p.opis, p.cijena, k.naziv AS kategorija_naziv
        FROM proizvodi p
        JOIN kategorije_proizvoda k ON p.kategorija_id = k.id
    """)
    proizvodi = cursor.fetchall()

    kategorije = {}
    for proizvod in proizvodi:
        kategorija = proizvod[4]
        if kategorija not in kategorije:
            kategorije[kategorija] = []
        kategorije[kategorija].append(proizvod)

    
    cursor.execute("SELECT COUNT(*) FROM proizvodi")
    total_proizvodi = cursor.fetchone()[0]
    total_pages = (total_proizvodi + per_page - 1) // per_page
    offset = (page - 1) * per_page

    cursor.execute("""
        SELECT p.id, p.naziv, p.opis, p.cijena, k.naziv AS kategorija_naziv
        FROM proizvodi p
        JOIN kategorije_proizvoda k ON p.kategorija_id = k.id
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    paginirani_proizvodi = cursor.fetchall()

    
    pagination = []
    if total_pages <= 7:  
        pagination = list(range(1, total_pages + 1))
    else:
        if page > 1:
            pagination.append(1)  
        if page > 3:
            pagination.append('...')  
        pagination += [p for p in range(max(page - 2, 2), min(page + 3, total_pages))]
        if page < total_pages - 2:
            pagination.append('...')  
        if page < total_pages:
            pagination.append(total_pages)  

    cursor.close()
    db.close()

    return render_template(
        'index.html',
        kategorije=kategorije,
        proizvodi=paginirani_proizvodi,
        page=page,
        total_pages=total_pages,
        pagination=pagination
    )



@app.route('/kategorija/<kategorija_naziv>')
def prikazi_kategoriju(kategorija_naziv):
    page = int(request.args.get('page', 1))  
    per_page = 5  
    offset = (page - 1) * per_page

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    cursor.execute("""
        SELECT p.id, p.naziv, p.opis, p.cijena
        FROM proizvodi p
        JOIN kategorije_proizvoda k ON p.kategorija_id = k.id
        WHERE k.naziv = %s
        LIMIT %s OFFSET %s
    """, (kategorija_naziv, per_page, offset))
    proizvodi = cursor.fetchall()

    
    cursor.execute("""
        SELECT COUNT(*)
        FROM proizvodi p
        JOIN kategorije_proizvoda k ON p.kategorija_id = k.id
        WHERE k.naziv = %s
    """, (kategorija_naziv,))
    total_proizvodi = cursor.fetchone()[0]
    total_pages = (total_proizvodi + per_page - 1) // per_page

    cursor.close()
    db.close()

   
    pagination = []
    if total_pages <= 7:
        pagination = list(range(1, total_pages + 1))
    else:
        if page > 1:
            pagination.append(1)
        if page > 3:
            pagination.append('...')
        pagination += list(range(max(2, page - 2), min(total_pages, page + 3)))
        if page < total_pages - 2:
            pagination.append('...')
        if page < total_pages:
            pagination.append(total_pages)

    return render_template(
        'kategorija.html',
        proizvodi=proizvodi,
        kategorija=kategorija_naziv,
        page=page,
        total_pages=total_pages,
        pagination=pagination
    )


@app.route('/logout')
def logout():
    session.pop('user_id', None)  
    return redirect(url_for('prijava'))

@app.route('/prijava', methods=['GET', 'POST'])
def prijava():
    if request.method == 'GET':
        return render_template('prijava.html')

    data = request.form
    email = data['email']
    lozinka = data['lozinka']

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT id, lozinka FROM korisnici WHERE email = %s", (email,))
    korisnik = cursor.fetchone()
    db.close()

    if korisnik and bcrypt.checkpw(lozinka.encode('utf-8'), korisnik[1].encode('utf-8')):
        session['user_id'] = korisnik[0]
        return redirect(url_for('home'))
    return jsonify({'message': 'Neispravan email ili lozinka!'}), 401

@app.route('/kosarica', methods=['GET'])
def prikazi_kosaricu():
    korisnik_id = session.get('user_id', 1)  
    
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
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
    korisnik_id = session.get('user_id', 1)  
    
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    cursor.execute("SELECT * FROM kosarica WHERE korisnik_id = %s AND proizvod_id = %s", (korisnik_id, proizvod_id))
    stavka = cursor.fetchone()

    if stavka:
        
        cursor.execute("UPDATE kosarica SET kolicina = kolicina + 1 WHERE korisnik_id = %s AND proizvod_id = %s",
                       (korisnik_id, proizvod_id))
    else:
        
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
    korisnik_id = session.get('user_id', 1)  

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
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
    korisnik_id = session.get('user_id', 1)  

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    cursor.execute("DELETE FROM kosarica WHERE korisnik_id = %s AND proizvod_id = %s", (korisnik_id, proizvod_id))
    db.commit()

    cursor.close()
    db.close()

    return jsonify({'success': True, 'message': 'Stavka je uspješno izbrisana.'}), 200

@app.route('/proizvod/<int:proizvod_id>', methods=['GET'])
def proizvod_detail(proizvod_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        
        cursor.execute("""
            SELECT id, naziv, opis, cijena, kategorija_id, kolicina_na_skladistu, slika, specifikacije, datum_kreiranja
            FROM proizvodi WHERE id = %s
        """, (proizvod_id,))
        proizvod = cursor.fetchone()

        
        cursor.execute("""
            SELECT r.ocjena, r.komentar, r.datum_recenzije, k.ime AS korisnik
            FROM recenzije_proizvoda r
            JOIN korisnici k ON r.korisnik_id = k.id
            WHERE r.proizvod_id = %s
        """, (proizvod_id,))
        recenzije = cursor.fetchall()

        
        recenzije = [
            {'ocjena': r[0], 'komentar': r[1], 'datum': r[2], 'korisnik': r[3]}
            for r in recenzije
        ]
    except MySQLdb.MySQLError as e:
        print(f"Greška prilikom dohvaćanja podataka: {e}")
        proizvod = None
        recenzije = []
    finally:
        db.close()

    if proizvod:
        return render_template('proizvod_detail.html', proizvod=proizvod, recenzije=recenzije)
    else:
        return jsonify({"message": "Proizvod nije pronađen."}), 404
    
    
@app.route('/registracija', methods=['GET', 'POST'])
def registracija():
    if request.method == 'GET':
        return render_template('registracija.html')

    elif request.method == 'POST':
        db = None
        try:
            
            data = request.get_json()
            print(f"Primljeni podaci iz JSON-a: {data}")

            
            if not all(key in data for key in ['ime', 'prezime', 'email', 'lozinka', 'adresa', 'grad', 'telefon']):
                return jsonify({'message': 'Nedostaju neki obavezni podaci!'}), 400

        
            ime = data['ime']
            prezime = data['prezime']
            email = data['email']
            lozinka = bcrypt.hashpw(data['lozinka'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            adresa = data['adresa']
            grad = data['grad']
            telefon = data['telefon']

            db = MySQLdb.connect(**db_config)
            cursor = db.cursor()

         
            cursor.callproc('dodaj_korisnika', (ime, prezime, email, lozinka, adresa, grad, telefon))
            db.commit()

            print("Registracija uspešna!")
            return jsonify({'message': 'Registracija uspešna!'}), 200

        except MySQLdb.MySQLError as e:
            error_message = str(e)
            print(f"Greška pri registraciji: {error_message}")  

            if "Korisnik sa ovim email-om već postoji!" in error_message:
                return jsonify({'message': 'Korisnik sa ovim email-om već postoji!'}), 409

            return jsonify({'message': 'Došlo je do greške pri registraciji.'}), 500

        finally:
            if db:
                db.close()

@app.route('/narudzba', methods=['GET', 'POST'])
def narudzba():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))  
    
    korisnik_id = session['user_id']
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT p.id, p.naziv, p.cijena, k.kolicina
                FROM kosarica k
                JOIN proizvodi p ON k.proizvod_id = p.id
                WHERE k.korisnik_id = %s
            """, (korisnik_id,))
            proizvodi = cursor.fetchall()
            if not proizvodi:
                flash('Vaša košarica je prazna.', 'error')
                return redirect(url_for('home'))

            cursor.execute("SELECT * FROM nacini_isporuke")
            nacini_isporuke = cursor.fetchall()
            ukupna_cijena = sum(Decimal(proizvod[2]) * proizvod[3] for proizvod in proizvodi)

            return render_template(
                'narudzba.html',
                proizvodi=proizvodi,
                nacini_isporuke=nacini_isporuke,
                ukupna_cijena=ukupna_cijena
            )

        elif request.method == 'POST':
            cursor.execute("""
                SELECT p.id, p.naziv, p.cijena, k.kolicina
                FROM kosarica k
                JOIN proizvodi p ON k.proizvod_id = p.id
                WHERE k.korisnik_id = %s
            """, (korisnik_id,))
            proizvodi = cursor.fetchall()
            if not proizvodi:
                flash('Vaša košarica je prazna.', 'error')
                return redirect(url_for('home'))

            nacin_isporuke_id = request.form['nacin_isporuke']
            nacin_placanja = request.form['nacin_placanja']  
            kupon_kod = request.form.get('kupon', '').strip()

            cursor.execute("SELECT cijena FROM nacini_isporuke WHERE id = %s", (nacin_isporuke_id,))
            cijena_dostave = Decimal(cursor.fetchone()[0])

            ukupna_cijena = sum(Decimal(proizvod[2]) * proizvod[3] for proizvod in proizvodi)
            ukupni_iznos = ukupna_cijena + cijena_dostave

            kupon_id = None
            if kupon_kod:
                cursor.execute("""
                    SELECT id, postotak_popusta
                    FROM kuponi
                    WHERE kod = %s AND datum_pocetka <= CURDATE() AND datum_zavrsetka >= CURDATE()
                """, (kupon_kod,))
                kupon = cursor.fetchone()
                if kupon:
                    kupon_id = kupon[0]
                    ukupni_iznos -= ukupni_iznos * Decimal(kupon[1]) / 100

            cursor.execute("""
                INSERT INTO narudzbe (korisnik_id, datum_narudzbe, status_narudzbe, ukupna_cijena, nacin_isporuke_id, kupon_id)
                VALUES (%s, CURDATE(), 'u obradi', %s, %s, %s)
            """, (korisnik_id, ukupni_iznos, nacin_isporuke_id, kupon_id))
            db.commit()

            cursor.execute("SELECT LAST_INSERT_ID()")
            narudzba_id = cursor.fetchone()[0]

            for proizvod in proizvodi:
                proizvod_id, _, cijena, kolicina = proizvod
                cursor.execute("""
                    INSERT INTO stavke_narudzbe (narudzba_id, proizvod_id, kolicina)
                    VALUES (%s, %s, %s)
                """, (narudzba_id, proizvod_id, kolicina))

            cursor.execute("""
                INSERT INTO placanja (narudzba_id, iznos, nacin_placanja, datum_placanja)
                VALUES (%s, %s, %s, CURDATE())
            """, (narudzba_id, ukupni_iznos, nacin_placanja))  

            cursor.execute("""
                INSERT INTO racuni (korisnik_id, narudzba_id, iznos, datum_izdavanja)
                VALUES (%s, %s, %s, CURDATE())
            """, (korisnik_id, narudzba_id, ukupni_iznos))

            cursor.execute("DELETE FROM kosarica WHERE korisnik_id = %s", (korisnik_id,))
            db.commit()

            flash('Narudžba uspješno kreirana!', 'success')

    except MySQLdb.MySQLError as e:
        print(f"MySQL greška: {e}")
        flash('Dogodila se greška prilikom kreiranja narudžbe.', 'error')
        db.rollback()

    finally:
        db.close()

    return redirect(url_for('home'))



@app.route('/wishlist', methods=['GET'])
def wishlist():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    korisnik_id = session['user_id']
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        
        cursor.execute("SELECT DISTINCT grupa FROM wishlist WHERE korisnik_id = %s", (korisnik_id,))
        dostupne_grupe = [row[0] for row in cursor.fetchall()]

        
        grupa_filter = request.args.get('grupa', '').strip()
        min_cijena = request.args.get('min_cijena', type=float)
        max_cijena = request.args.get('max_cijena', type=float)

        query = """
            SELECT w.grupa, p.id, p.naziv, p.cijena
            FROM wishlist w
            JOIN proizvodi p ON w.proizvod_id = p.id
            WHERE w.korisnik_id = %s
        """
        params = [korisnik_id]

        if grupa_filter:
            query += " AND w.grupa = %s"
            params.append(grupa_filter)
        if min_cijena is not None:
            query += " AND p.cijena >= %s"
            params.append(min_cijena)
        if max_cijena is not None:
            query += " AND p.cijena <= %s"
            params.append(max_cijena)

        cursor.execute(query, tuple(params))
        proizvodi = cursor.fetchall()

       
        proizvodi_u_wishlistu = {}
        for grupa, proizvod_id, naziv, cijena in proizvodi:
            if grupa not in proizvodi_u_wishlistu:
                proizvodi_u_wishlistu[grupa] = []
            proizvodi_u_wishlistu[grupa].append((proizvod_id, naziv, cijena))

         
        cursor.execute("SELECT * FROM popularni_proizvodi LIMIT 3")
        popularni_proizvodi = cursor.fetchall()

    finally:
        db.close()

    return render_template('wishlist.html', 
                           proizvodi_u_wishlistu=proizvodi_u_wishlistu, 
                           dostupne_grupe=dostupne_grupe,
                           popularni_proizvodi=popularni_proizvodi)




@app.route('/api/wishlist', methods=['POST'])
def api_wishlist():
    korisnik_id = session.get('user_id')
    if not korisnik_id:
        return jsonify({'message': 'Morate biti prijavljeni!'}), 401

    data = request.get_json()
    proizvod_id = data.get('proizvod_id')
    grupa = data.get('grupa', 'Bez grupe')  

    if not proizvod_id:
        return jsonify({'message': 'Proizvod nije definiran!'}), 400

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        
        cursor.execute("""
            INSERT INTO wishlist (korisnik_id, proizvod_id, grupa)
            VALUES (%s, %s, %s)
        """, (korisnik_id, proizvod_id, grupa))
        db.commit()
    except MySQLdb.IntegrityError as e:
        
        if "Duplicate entry" in str(e) or "45002" in str(e):
            return jsonify({'message': 'Proizvod je već u wishlisti!'}), 409
        else:
            return jsonify({'message': f'Greška pri dodavanju u wishlist: {str(e)}'}), 500
    finally:
        db.close()

    return jsonify({'message': f'Proizvod je uspešno dodan u wishlist pod grupu "{grupa}"!'})


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

        cursor.execute("""CALL ukloni_proizvod_iz_wishliste(%s, %s)""", (korisnik_id, proizvod_id))
        db.commit()
    except MySQLdb.Error as e:
        db.rollback()
        return jsonify({'message': f'Greška pri uklanjanju iz wishlist: {str(e)}'}), 500
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
    grupa = data.get('grupa', 'Bez grupe')  

    if not proizvod_id:
        return jsonify({'message': 'Proizvod nije definiran!'}), 400

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        
        cursor.execute("""
            CALL dodaj_u_wishlist(%s, %s, %s)
        """, (korisnik_id, proizvod_id, grupa))
        db.commit()
    except MySQLdb.Error as e:
        db.rollback()
        return jsonify({'message': f'Greška pri dodavanju u wishlist: {str(e)}'}), 500
    finally:
        db.close()

    return jsonify({'message': f'Proizvod je uspješno dodan u wishlist pod grupu "{grupa}"!'})



@app.route('/podrska', methods=['GET', 'POST'])
def kreiraj_upit():
    message = ""  
    if request.method == 'POST':
        
        korisnik_id = session.get('user_id')
        if not korisnik_id:
            message = "Morate biti prijavljeni!"  
            return render_template('podrska.html', message=message)

        
        tema = request.form.get('tema')
        poruka = request.form.get('poruka')

        if not tema or not poruka:
            message = "Tema i poruka su obavezna!"  
            return render_template('podrska.html', message=message)

        
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO podrska_za_korisnike (korisnik_id, tema, poruka, status, datum_upita) "
                "VALUES (%s, %s, %s, 'otvoreno', CURDATE())",
                (korisnik_id, tema, poruka)
            )
            db.commit()
            message = "Upit je uspješno poslan!"  
        finally:
            db.close()

        return render_template('podrska.html', message=message)  

    # Ako je GET metoda, samo prikazujemo formu
    return render_template('podrska.html', message=message)  



@app.route('/preporuceni_proizvodi', methods=['GET', 'POST'])
def preporuceni_proizvodi():
    message = ""  
    proizvodi = []  

    if request.method == 'POST':
        
        korisnik_id = session.get('user_id')
        if not korisnik_id:
            message = "Morate biti prijavljeni!"  
            return render_template('preporuceni_proizvodi.html', message=message, proizvodi=proizvodi)

        
        proizvod_id = request.form.get('proizvod_id')
        razlog_preporuke = request.form.get('razlog_preporuke')

        if not proizvod_id or not razlog_preporuke:
            message = "Proizvod i razlog preporuke su obavezni!"  
            return render_template('preporuceni_proizvodi.html', message=message, proizvodi=proizvodi)

        
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO preporuceni_proizvodi (korisnik_id, proizvod_id, razlog_preporuke) "
                "VALUES (%s, %s, %s)",
                (korisnik_id, proizvod_id, razlog_preporuke)
            )
            db.commit()
            message = "Proizvod je uspješno preporučen!"  
        finally:
            db.close()

        return render_template('preporuceni_proizvodi.html', message=message, proizvodi=proizvodi)  

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT id, naziv FROM proizvodi")  
    proizvodi = cursor.fetchall()  
    db.close()

    return render_template('preporuceni_proizvodi.html', message=message, proizvodi=proizvodi)




@app.route('/pracenje_isporuka', methods=['GET', 'POST'])
def pracenje_isporuka():
    korisnik_id = session.get('user_id')
    if not korisnik_id:
        flash('Morate biti prijavljeni!', 'error')
        return redirect(url_for('login'))  


    is_admin = session.get('is_admin', False)

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if is_admin:
        
        query = """
        SELECT n.id, n.datum_narudzbe, pi.status_isporuke, pi.datum_isporuke, n.korisnik_id
        FROM narudzbe n
        LEFT JOIN pracenje_isporuka pi ON n.id = pi.narudzba_id
        """
    else:
       
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



@app.route('/povrat', methods=['GET', 'POST'])
def povrat_proizvoda():
    if request.method == 'GET':
        
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            
            korisnik_id = session.get('user_id')
            if not korisnik_id:
                flash("Morate biti prijavljeni za pristup povratu proizvoda!", "error")
                return redirect(url_for('prijava'))

            
            cursor.execute("""
                SELECT sn.id, p.naziv, sn.kolicina
                FROM stavke_narudzbe sn
                JOIN narudzbe n ON sn.narudzba_id = n.id
                JOIN proizvodi p ON sn.proizvod_id = p.id
                WHERE n.korisnik_id = %s
            """, (korisnik_id,))
            stavke = cursor.fetchall()
        finally:
            db.close()

        
        return render_template('povrati_proizvoda.html', stavke=stavke)

    elif request.method == 'POST':
        
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



@app.route('/popust', methods=['GET'])
def pregled_popusta():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT p.id, pr.naziv, p.postotak_popusta, p.datum_pocetka, p.datum_zavrsetka
            FROM popusti p
            JOIN proizvodi pr ON p.proizvod_id = pr.id
        """)
        popusti = cursor.fetchall()
    finally:
        db.close()

    return render_template('popusti.html', popusti=popusti)


@app.route('/recenzije', methods=['GET', 'POST'])
def recenzije():
    proizvodi = []
    
    if request.method == 'POST':
        korisnik_id = session.get('user_id')
        if not korisnik_id:
            flash("Morate biti prijavljeni za ostavljanje recenzije.", "error")
            return redirect(url_for('prijava'))

        proizvod_id = request.form.get('proizvod_id')
        ocjena = request.form.get('ocjena')
        komentar = request.form.get('komentar')

        if not proizvod_id or not ocjena or not komentar:
            flash("Proizvod, ocjena i komentar su obavezni!", "error")
            return redirect(url_for('recenzije'))

        try:
            ocjena = int(ocjena)
            if ocjena < 1 or ocjena > 5:
                flash("Ocjena mora biti između 1 i 5!", "error")
                return redirect(url_for('recenzije'))
        except ValueError:
            flash("Ocjena mora biti broj!", "error")
            return redirect(url_for('recenzije'))

        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO recenzije_proizvoda (proizvod_id, korisnik_id, ocjena, komentar, datum_recenzije)
                VALUES (%s, %s, %s, %s, CURDATE())
            """, (proizvod_id, korisnik_id, ocjena, komentar))
            db.commit()
            flash("Recenzija je uspješno poslana!", "success")
        except MySQLdb.MySQLError as e:
            if e.args[0] == 1644:  
                flash(f"Greška: {e.args[1]}", "error")
            else:
                flash("Dogodila se greška pri dodavanju recenzije.", "error")
            db.rollback()
        finally:
            db.close()

        return redirect(url_for('recenzije'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id, naziv FROM proizvodi")
        proizvodi = cursor.fetchall()
    except MySQLdb.MySQLError:
        flash("Dogodila se greška prilikom dohvaćanja proizvoda.", "error")
    finally:
        db.close()
 
    return render_template('recenzije.html', proizvodi=proizvodi)


@app.route('/dodaj_recenziju/<int:proizvod_id>', methods=['POST'])
def dodaj_recenziju(proizvod_id):
    korisnik_id = session.get('user_id')
    if not korisnik_id:
        flash("Morate biti prijavljeni za ostavljanje recenzije.", "error")
        return redirect(url_for('prijava'))

    ocjena = request.form.get('ocjena')
    komentar = request.form.get('komentar')

    if not ocjena or not komentar:
        flash("Ocjena i komentar su obavezni!", "error")
        return redirect(request.referrer)

    try:
        ocjena = int(ocjena)
        if ocjena < 1 or ocjena > 5:
            flash("Ocjena mora biti između 1 i 5!", "error")
            return redirect(request.referrer)
    except ValueError:
        flash("Ocjena mora biti broj!", "error")
        return redirect(request.referrer)

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO recenzije_proizvoda (proizvod_id, korisnik_id, ocjena, komentar, datum_recenzije)
            VALUES (%s, %s, %s, %s, CURDATE())
        """, (proizvod_id, korisnik_id, ocjena, komentar))
        db.commit()
        flash("Recenzija je uspješno dodana!", "success")
    except MySQLdb.MySQLError as e:
        if e.args[0] == 1644:  
            flash(f"Greška: {e.args[1]}", "error")
        else:
            flash("Dogodila se greška pri dodavanju recenzije.", "error")
        db.rollback()
    finally:
        db.close()

    return redirect(request.referrer)



@app.route('/lista_preporuka', methods=['GET'])
def lista_preporuka():
    korisnik_id = session.get('user_id')  
    if not korisnik_id:
        return redirect(url_for('prijava'))  

    page = int(request.args.get('page', 1))  
    per_page = 10  

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    cursor.execute("""
        CALL prikazi_preporuke(%s, %s, %s)
    """, (korisnik_id, page, per_page))
    proizvodi = cursor.fetchall()  

   
    cursor.execute("""
        CALL prikazi_preporuke(%s, 1, 9999)
    """, (korisnik_id,))
    total_proizvodi = len(cursor.fetchall())  
    total_pages = (total_proizvodi + per_page - 1) // per_page  

    cursor.close()
    db.close()

    
    return render_template('lista_preporuka.html', proizvodi=proizvodi, page=page, total_pages=total_pages)


@app.route('/profil', methods=['GET'])
def profil():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    korisnik_id = session['user_id']
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        
        cursor.execute("""
            SELECT 
                korisnik_id, 
                ime, 
                prezime, 
                email, 
                adresa, 
                grad, 
                telefon, 
                formatiraj_datum(datum_registracije) AS datum_registracije,
                tip_korisnika 
            FROM profil_korisnika 
            WHERE korisnik_id = %s
        """, (korisnik_id,))
        korisnik = cursor.fetchone()

        cursor.execute("SELECT * FROM narudzbe_korisnika WHERE korisnik_id = %s", (korisnik_id,))
        narudzbe = cursor.fetchall()

    finally:
        db.close()

    return render_template('profil.html', korisnik=korisnik, narudzbe=narudzbe)



@app.route('/profil/azuriraj', methods=['POST'])
def azuriraj_profil():
    if 'user_id' not in session:
        return jsonify({'message': 'Morate biti prijavljeni!'}), 401

    data = request.get_json()
    korisnik_id = session['user_id']

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        cursor.callproc('azuriraj_korisnika', (
            korisnik_id,
            data['ime'],
            data['prezime'],
            data['email'],
            data['adresa'],
            data['grad'],
            data['telefon']
        ))
        db.commit()
    finally:
        db.close()

    return jsonify({'message': 'Profil uspešno ažuriran!'})


@app.route('/profil/obrisi', methods=['POST'])
def obrisi_profil():
    if 'user_id' not in session:
        return jsonify({'message': 'Morate biti prijavljeni!'}), 401

    korisnik_id = session['user_id']  

    db = None
    try:
       
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()

        
        cursor.callproc('obrisi_korisnika', (korisnik_id,))
        db.commit()

        
        session.pop('user_id', None)
        return jsonify({'message': 'Račun uspješno obrisan!'}), 200

    except MySQLdb.MySQLError as e:
        
        if e.args[0] == 1644:  
            return jsonify({'message': e.args[1]}), 400
        else:
            print(f"Neočekivana greška u MySQL-u: {e}")  
            return jsonify({'message': 'Došlo je do greške pri brisanju računa.'}), 500

    except Exception as e:
        print(f"Neočekivana greška: {e}")  
        return jsonify({'message': 'Neočekivana greška na serveru.'}), 500

    finally:
        
        if db:
            db.close()


@app.route('/preporuke')
def preporuke():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        
        cursor.execute("SELECT ime, prezime, proizvod_naziv, razlog_preporuke FROM preporuke_drugih")
        preporuke = cursor.fetchall()

    finally:
        db.close()

    return render_template('preporuke.html', preporuke=preporuke)


@app.route('/admin_panel', methods=['GET'])
def admin_panel():
    
    if 'user_id' not in session:
        return redirect(url_for('prijava'))  

   
    korisnik_id = session['user_id']
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT tip_korisnika FROM korisnici WHERE id = %s
        """, (korisnik_id,))
        tip_korisnika = cursor.fetchone()

       
        if not tip_korisnika or tip_korisnika[0] != 'admin':
            flash('Nemate prava pristupa administrativnom panelu.', 'error')
            return redirect(url_for('home'))  

    finally:
        db.close()

  
    return render_template('admin_panel.html')


@app.route('/upravljanje_korisnicima', methods=['GET', 'POST'])
def upravljanje_korisnicima():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))  

    korisnik_id = session['user_id']
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    ime_filter = request.args.get('ime', '')
    prezime_filter = request.args.get('prezime', '')
    tip_korisnika_filter = request.args.get('tip_korisnika', '')

    
    query = "SELECT id, ime, prezime, email, tip_korisnika FROM korisnici WHERE id != %s"
    params = [korisnik_id]  

    if ime_filter:
        query += " AND ime LIKE %s"
        params.append(f'%{ime_filter}%')  

    if prezime_filter:
        query += " AND prezime LIKE %s"
        params.append(f'%{prezime_filter}%')  

    if tip_korisnika_filter:
        query += " AND tip_korisnika = %s"
        params.append(tip_korisnika_filter)  

    
    cursor.execute(query, tuple(params))
    korisnici = cursor.fetchall()
    db.close()

    return render_template('upravljanje_korisnicima.html', korisnici=korisnici)



@app.route('/upravljanje_proizvodima', methods=['GET'])
def upravljanje_proizvodima():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    cursor.execute("SELECT id, naziv, opis, cijena, kolicina_na_skladistu FROM proizvodi")
    proizvodi = cursor.fetchall()
    db.close()

    return render_template('upravljanje_proizvodima.html', proizvodi=proizvodi)

@app.route('/upravljanje_narudzbama', methods=['GET'])
def upravljanje_narudzbama():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

   
    cursor.execute("""
        SELECT n.id, k.ime, k.prezime, n.datum_narudzbe, n.status_narudzbe, 
               SUM(s.kolicina * p.cijena) AS ukupna_cijena
        FROM narudzbe n
        JOIN korisnici k ON n.korisnik_id = k.id
        JOIN stavke_narudzbe s ON n.id = s.narudzba_id
        JOIN proizvodi p ON s.proizvod_id = p.id
        GROUP BY n.id, k.id
    """)
    narudzbe = cursor.fetchall()
    db.close()

    return render_template('upravljanje_narudzbama.html', narudzbe=narudzbe)



@app.route('/statistike', methods=['GET'])
def statistike():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))  

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    cursor.execute("SELECT COUNT(*) FROM korisnici")
    broj_korisnika = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM proizvodi")
    broj_proizvoda = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(ukupna_cijena) FROM narudzbe")
    ukupna_zarada = cursor.fetchone()[0]

    
    cursor.execute("""
        SELECT p.id AS proizvod_id, p.naziv AS proizvod_naziv, COUNT(w.proizvod_id) AS broj_dodavanja
        FROM proizvodi p
        LEFT JOIN wishlist w ON p.id = w.proizvod_id
        GROUP BY p.id, p.naziv
        ORDER BY broj_dodavanja DESC
        LIMIT 5
    """)
    top_proizvodi = cursor.fetchall()

    
    cursor.execute("""
        SELECT k.id AS korisnik_id, k.ime, k.prezime, COUNT(n.id) AS broj_narudzbi
        FROM korisnici k
        JOIN narudzbe n ON k.id = n.korisnik_id
        GROUP BY k.id, k.ime, k.prezime
        ORDER BY broj_narudzbi DESC
        LIMIT 5
    """)
    top_korisnici_narudzbe = cursor.fetchall()

    
    cursor.execute("""
        SELECT k.id AS korisnik_id, k.ime, k.prezime, SUM(n.ukupna_cijena) AS ukupna_zarada
        FROM korisnici k
        JOIN narudzbe n ON k.id = n.korisnik_id
        GROUP BY k.id, k.ime, k.prezime
        ORDER BY ukupna_zarada DESC
    """)
    ukupna_zarada_korisnici = cursor.fetchall()

    db.close()

    return render_template(
        'statistike.html', 
        broj_korisnika=broj_korisnika, 
        broj_proizvoda=broj_proizvoda, 
        ukupna_zarada=ukupna_zarada, 
        top_proizvodi=top_proizvodi, 
        top_korisnici_narudzbe=top_korisnici_narudzbe, 
        ukupna_zarada_korisnici=ukupna_zarada_korisnici
    )



@app.route('/upravljanje_popustima', methods=['GET', 'POST'])
def upravljanje_popustima():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

   
    cursor.execute("""
        SELECT p.id, pr.naziv, p.postotak_popusta, p.datum_pocetka, p.datum_zavrsetka
        FROM popusti p
        JOIN proizvodi pr ON p.proizvod_id = pr.id
    """)
    popusti = cursor.fetchall()
    db.close()

    return render_template('upravljanje_popustima.html', popusti=popusti)


@app.route('/dodaj_popust', methods=['GET', 'POST'])
def dodaj_popust():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    if request.method == 'POST':
        proizvod_id = request.form['proizvod_id']
        postotak_popusta = request.form['postotak_popusta']
        datum_pocetka = request.form['datum_pocetka']
        datum_zavrsetka = request.form['datum_zavrsetka']

        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO popusti (proizvod_id, postotak_popusta, datum_pocetka, datum_zavrsetka)
                VALUES (%s, %s, %s, %s)
            """, (proizvod_id, postotak_popusta, datum_pocetka, datum_zavrsetka))
            db.commit()
            flash('Popust uspješno dodan!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
            db.rollback()
        finally:
            db.close()

        return redirect(url_for('upravljanje_popustima'))

    
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT id, naziv FROM proizvodi")
    proizvodi = cursor.fetchall()
    db.close()

    return render_template('dodaj_popust.html', proizvodi=proizvodi)



@app.route('/obrisi_popust/<int:popust_id>', methods=['POST'])
def obrisi_popust(popust_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Morate biti prijavljeni!'}), 403

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM popusti WHERE id = %s", (popust_id,))
        db.commit()
        return jsonify({'message': 'Popust uspješno obrisan!'}), 200
    except MySQLdb.MySQLError as e:
        db.rollback()
        return jsonify({'message': f'Greška: {e.args[1]}'}), 500
    finally:
        db.close()



@app.route('/azuriraj_popust/<int:popust_id>', methods=['GET', 'POST'])
def azuriraj_popust(popust_id):
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'POST':
        proizvod_id = request.form['proizvod_id']
        postotak_popusta = request.form['postotak_popusta']
        datum_pocetka = request.form['datum_pocetka']
        datum_zavrsetka = request.form['datum_zavrsetka']

        try:
            cursor.execute("""
                UPDATE popusti
                SET proizvod_id = %s, postotak_popusta = %s, datum_pocetka = %s, datum_zavrsetka = %s
                WHERE id = %s
            """, (proizvod_id, postotak_popusta, datum_pocetka, datum_zavrsetka, popust_id))
            db.commit()
            flash('Popust uspješno ažuriran!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
            db.rollback()
        finally:
            db.close()

        return redirect(url_for('upravljanje_popustima'))

    
    cursor.execute("SELECT id, naziv FROM proizvodi")
    proizvodi = cursor.fetchall()

    cursor.execute("SELECT * FROM popusti WHERE id = %s", (popust_id,))
    popust = cursor.fetchone()

    db.close()

    return render_template('azuriraj_popust.html', popust=popust, proizvodi=proizvodi)



@app.route('/dodaj_korisnika', methods=['GET', 'POST'])
def dodaj_korisnika():
    if request.method == 'GET':
        return render_template('dodaj_korisnika.html')

    if request.method == 'POST':
        data = request.form
        try:
            db = MySQLdb.connect(**db_config)
            cursor = db.cursor()

            
            cursor.callproc('dodaj_korisnika', (
                data['ime'], 
                data['prezime'], 
                data['email'], 
                bcrypt.hashpw(data['lozinka'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), 
                data['adresa'], 
                data['grad'], 
                data['telefon']
            ))

            db.commit()

            
            flash('Korisnik uspješno dodan kao kupac!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
        finally:
            db.close()

        return redirect(url_for('upravljanje_korisnicima'))


@app.route('/azuriraj_korisnika/<int:korisnik_id>', methods=['GET', 'POST'])
def azuriraj_korisnika(korisnik_id):
    print(f"Primljen zahtjev za korisnika ID: {korisnik_id}")  

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT id, ime, prezime, email, adresa, grad, telefon, tip_korisnika FROM korisnici WHERE id = %s", (korisnik_id,))
        korisnik = cursor.fetchone()
        db.close()
        return render_template('azuriraj_korisnika.html', korisnik=korisnik)

    if request.method == 'POST':
        data = request.form

        try:
            
            cursor.callproc('azuriraj_korisnika', (
                korisnik_id,  
                data['ime'],
                data['prezime'],
                data['email'],
                data['adresa'],
                data['grad'],
                data['telefon']
            ))
            db.commit()
            print("Korisnik uspješno ažuriran")  

            cursor.callproc('azuriraj_tip_korisnika', (korisnik_id, data['tip_korisnika']))
            db.commit()
            
        except MySQLdb.MySQLError as e:
            print(f"Greška: {e}")  
        finally:
            db.close()

        return redirect(url_for('upravljanje_korisnicima'))


@app.route('/obrisi_korisnika/<int:korisnik_id>', methods=['POST'])
def obrisi_korisnika(korisnik_id):
    try:
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        cursor.callproc('obrisi_korisnika', (korisnik_id,))
        db.commit()
        return jsonify({'message': 'Korisnik uspješno obrisan!', 'status': 'success'})
    except MySQLdb.MySQLError as e:
        return jsonify({'message': f'Greška: {e.args[1]}', 'status': 'error'})
    finally:
        db.close()

@app.route('/promijeni_status/<int:narudzba_id>', methods=['POST'])
def promijeni_status(narudzba_id):
    data = request.get_json()
    novi_status = data.get('status')

    if novi_status not in ['u obradi', 'poslano', 'dostavljeno']:
        return jsonify({'error': 'Nevažeći status!'}), 400

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        cursor.execute("UPDATE narudzbe SET status_narudzbe = %s WHERE id = %s", (novi_status, narudzba_id))
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Greška prilikom ažuriranja statusa!'}), 500
    finally:
        cursor.close()
        db.close()

    return jsonify({'message': 'Status uspješno promijenjen!'})


@app.route('/dodaj_proizvod', methods=['GET', 'POST'])
def dodaj_proizvod():
    if request.method == 'GET':
        
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        cursor.execute("SELECT id, naziv FROM kategorije_proizvoda")
        kategorije = cursor.fetchall()
        db.close()
        return render_template('dodaj_proizvod.html', kategorije=kategorije)

    if request.method == 'POST':
        data = request.form
        try:
            db = MySQLdb.connect(**db_config)
            cursor = db.cursor()
            cursor.callproc('DodajProizvod', (
                data['naziv'],
                data['opis'],
                data['cijena'],
                data['kategorija_id'],
                data['kolicina'],
                data['slika'],
                data['specifikacije']
            ))
            db.commit()
            flash('Proizvod uspješno dodan!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
        finally:
            db.close()

        return redirect(url_for('upravljanje_proizvodima'))

@app.route('/azuriraj_proizvod/<int:proizvod_id>', methods=['GET', 'POST'])
def azuriraj_proizvod(proizvod_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'GET':
        
        cursor.execute("SELECT * FROM proizvodi WHERE id = %s", (proizvod_id,))
        proizvod = cursor.fetchone()

        cursor.execute("SELECT id, naziv FROM kategorije_proizvoda")
        kategorije = cursor.fetchall()
        db.close()

        return render_template('azuriraj_proizvod.html', proizvod=proizvod, kategorije=kategorije)

    if request.method == 'POST':
        data = request.form
        try:
            cursor.callproc('azuriraj_proizvod', (
                proizvod_id,
                data['naziv'],
                data['opis'],
                data['cijena'],
                data['kategorija_id'],
                data['kolicina_na_skladistu'],
                data['slika'],
                data['specifikacije']
            ))
            db.commit()
            flash('Proizvod uspješno ažuriran!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
        finally:
            db.close()

        return redirect(url_for('upravljanje_proizvodima'))


@app.route('/obrisi_proizvod/<int:proizvod_id>', methods=['POST'])
def obrisi_proizvod(proizvod_id):
    try:
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        cursor.callproc('ObrisiProizvod', (proizvod_id,))
        db.commit()
        flash('Proizvod uspješno obrisan!', 'success')
    except MySQLdb.MySQLError as e:
        flash(f'Greška: {e.args[1]}', 'error')
    finally:
        db.close()

    return redirect(url_for('upravljanje_proizvodima'))


@app.route('/dodaj_kategoriju', methods=['GET', 'POST'])
def dodaj_kategoriju():
    if request.method == 'GET':
        return render_template('dodaj_kategoriju.html')

    if request.method == 'POST':
        data = request.form
        try:
            db = MySQLdb.connect(**db_config)
            cursor = db.cursor()
            cursor.callproc('dodaj_kategoriju_proizvoda', (data['naziv'], data['opis']))
            db.commit()
            flash('Kategorija uspješno dodana!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
        finally:
            db.close()

        return redirect(url_for('upravljanje_kategorijama'))


@app.route('/azuriraj_kategoriju/<int:kategorija_id>', methods=['GET', 'POST'])
def azuriraj_kategoriju(kategorija_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'GET':
        
        cursor.execute("SELECT id, naziv, opis FROM kategorije_proizvoda WHERE id = %s", (kategorija_id,))
        kategorija = cursor.fetchone()
        db.close()
        return render_template('azuriraj_kategoriju.html', kategorija=kategorija)

    if request.method == 'POST':
        data = request.form
        try:
            cursor.callproc('azuriraj_kategoriju_proizvoda', (
                kategorija_id,
                data['naziv'],
                data['opis']
            ))
            db.commit()
            flash('Kategorija uspješno ažurirana!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
        finally:
            db.close()

        return redirect(url_for('upravljanje_kategorijama'))


@app.route('/obrisi_kategoriju/<int:kategorija_id>', methods=['POST'])
def obrisi_kategoriju(kategorija_id):
    try:
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        cursor.callproc('obrisi_kategoriju_proizvoda', (kategorija_id,))
        db.commit()
        flash('Kategorija uspješno obrisana!', 'success')
    except MySQLdb.MySQLError as e:
        flash(f'Greška: {e.args[1]}', 'error')
    finally:
        db.close()

    return redirect(url_for('upravljanje_kategorijama'))


@app.route('/upravljanje_kategorijama', methods=['GET'])
def upravljanje_kategorijama():
    try:
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        cursor.execute("SELECT id, naziv, opis FROM kategorije_proizvoda")
        kategorije = cursor.fetchall()  
    except MySQLdb.MySQLError as e:
        kategorije = []
        print(f"Greška prilikom dohvaćanja kategorija: {e}")  
    finally:
        db.close()

    return render_template('upravljanje_kategorijama.html', kategorije=kategorije)


@app.route('/azuriraj_recenziju/<int:recenzija_id>', methods=['GET', 'POST'])
def azuriraj_recenziju(recenzija_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'GET':
        
        cursor.execute("SELECT id, ocjena, komentar FROM recenzije_proizvoda WHERE id = %s", (recenzija_id,))
        recenzija = cursor.fetchone()
        db.close()
        if recenzija:
            return render_template('azuriraj_recenziju.html', recenzija=recenzija)
        else:
            flash('Recenzija nije pronađena!', 'error')
            return redirect(url_for('upravljanje_recenzijama'))

    if request.method == 'POST':
        data = request.form
        try:
            cursor.callproc('azuriraj_recenziju_proizvoda', (
                recenzija_id,
                int(data['ocjena']),
                data['komentar']
            ))
            db.commit()
            flash('Recenzija uspješno ažurirana!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
        finally:
            db.close()

        return redirect(url_for('upravljanje_recenzijama'))


@app.route('/obrisi_recenziju/<int:recenzija_id>', methods=['POST'])
def obrisi_recenziju(recenzija_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    try:
        cursor.callproc('obrisi_recenziju_proizvoda', (recenzija_id,))
        db.commit()
        flash('Recenzija uspješno obrisana!', 'success')
    except MySQLdb.MySQLError as e:
        flash(f'Greška: {e.args[1]}', 'error')
    finally:
        db.close()

    return redirect(url_for('upravljanje_recenzijama'))


@app.route('/upravljanje_recenzijama', methods=['GET'])
def upravljanje_recenzijama():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        
        cursor.execute("""
            SELECT r.id, p.naziv AS proizvod, k.ime AS korisnik, r.ocjena, r.komentar, r.datum_recenzije
            FROM recenzije_proizvoda r
            JOIN proizvodi p ON r.proizvod_id = p.id
            JOIN korisnici k ON r.korisnik_id = k.id
        """)
        recenzije = cursor.fetchall()
    except MySQLdb.MySQLError as e:
        recenzije = []
        print(f"Greška prilikom dohvaćanja recenzija: {e}")
    finally:
        db.close()

    return render_template('upravljanje_recenzijama.html', recenzije=recenzije)

@app.route('/pregled_placanja')
def pregled_placanja():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT p.id, n.id AS narudzba_id, p.iznos, p.nacin_placanja, p.datum_placanja
            FROM placanja p
            JOIN narudzbe n ON p.narudzba_id = n.id
        """)
        placanja = cursor.fetchall()
    finally:
        db.close()

    return render_template('pregled_placanja.html', placanja=placanja)


@app.route('/pregled_stavki_narudzbe')
def pregled_stavki_narudzbe():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        
        cursor.execute("""
            SELECT
                n.id AS narudzba_id,
                k.ime AS korisnik_ime,
                k.prezime AS korisnik_prezime,
                n.datum_narudzbe,
                n.ukupna_cijena,
                p.naziv AS proizvod,
                sn.kolicina,
                (sn.kolicina * p.cijena) AS ukupno_stavka
            FROM narudzbe n
            JOIN korisnici k ON n.korisnik_id = k.id
            JOIN stavke_narudzbe sn ON n.id = sn.narudzba_id
            JOIN proizvodi p ON sn.proizvod_id = p.id
            ORDER BY n.id, p.naziv
        """)
        stavke_narudzbi = cursor.fetchall()
    finally:
        db.close()

    
    narudzbe = {}
    for stavka in stavke_narudzbi:
        narudzba_id = stavka[0]
        if narudzba_id not in narudzbe:
            narudzbe[narudzba_id] = {
                'korisnik': f"{stavka[1]} {stavka[2]}",
                'datum_narudzbe': stavka[3],
                'ukupna_cijena': stavka[4],
                'stavke': []
            }
        narudzbe[narudzba_id]['stavke'].append({
            'proizvod': stavka[5],
            'kolicina': stavka[6],
            'ukupno_stavka': stavka[7]
        })

    return render_template('pregled_stavki_narudzbe.html', narudzbe=narudzbe)

@app.route('/pregled_racuna')
def pregled_racuna():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        
        cursor.execute("""
            SELECT
                r.id AS racun_id,
                k.ime AS korisnik_ime,
                k.prezime AS korisnik_prezime,
                n.datum_narudzbe,
                n.ukupna_cijena,
                r.datum_izdavanja,
                p.naziv AS proizvod,
                sn.kolicina,
                (sn.kolicina * p.cijena) AS ukupno_stavka
            FROM racuni r
            JOIN korisnici k ON r.korisnik_id = k.id
            JOIN narudzbe n ON r.narudzba_id = n.id
            JOIN stavke_narudzbe sn ON n.id = sn.narudzba_id
            JOIN proizvodi p ON sn.proizvod_id = p.id
            ORDER BY r.id, p.naziv
        """)
        racuni_podaci = cursor.fetchall()
    finally:
        db.close()

    
    racuni = {}
    for stavka in racuni_podaci:
        racun_id = stavka[0]
        if racun_id not in racuni:
            racuni[racun_id] = {
                'korisnik': f"{stavka[1]} {stavka[2]}",
                'datum_narudzbe': stavka[3],
                'ukupna_cijena': stavka[4],
                'datum_izdavanja': stavka[5],
                'stavke': []
            }
        racuni[racun_id]['stavke'].append({
            'proizvod': stavka[6],
            'kolicina': stavka[7],
            'ukupno_stavka': stavka[8]
        })

    return render_template('pregled_racuna.html', racuni=racuni)



@app.route('/racun/<int:racun_id>')
def prikazi_racun(racun_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    try:
       
        cursor.execute("""
            SELECT 
                r.id AS racun_id,
                r.narudzba_id,
                r.iznos AS ukupna_cijena,
                r.datum_izdavanja,
                k.ime AS korisnik_ime,
                k.prezime AS korisnik_prezime,
                k.email AS korisnik_email,
                k.adresa AS korisnik_adresa,
                k.telefon AS korisnik_telefon,
                p.nacin_placanja,
                IFNULL(pop.postotak_popusta, 0) AS popust,
                IFNULL(kup.kod, 'Nema kupona') AS kupon,
                ni.naziv AS nacin_isporuke,
                ni.trajanje AS trajanje_isporuke
            FROM racuni r
            JOIN korisnici k ON r.korisnik_id = k.id
            JOIN narudzbe n ON r.narudzba_id = n.id
            LEFT JOIN placanja p ON n.id = p.narudzba_id
            LEFT JOIN popusti pop ON n.id = pop.proizvod_id
            LEFT JOIN kuponi kup ON n.kupon_id = kup.id
            LEFT JOIN nacini_isporuke ni ON n.nacin_isporuke_id = ni.id
            WHERE r.id = %s
        """, (racun_id,))
        racun = cursor.fetchone()

        
        cursor.execute("""
            SELECT 
                p.naziv AS proizvod,
                sn.kolicina,
                ROUND(p.cijena * sn.kolicina, 2) AS ukupno_stavka
            FROM stavke_narudzbe sn
            JOIN proizvodi p ON sn.proizvod_id = p.id
            WHERE sn.narudzba_id = %s
        """, (racun['narudzba_id'],))
        stavke = cursor.fetchall()

       
        if not racun:
            flash('Račun nije pronađen!', 'error')
            return redirect(url_for('pregled_racuna'))

        racun['stavke'] = stavke

    except MySQLdb.MySQLError as e:
        flash(f'Greška prilikom dohvaćanja računa: {e}', 'error')
        return redirect(url_for('pregled_racuna'))

    finally:
        cursor.close()
        db.close()

   
    return render_template('racun_detalji.html', racun=racun)


@app.route('/upravljanje_kuponima', methods=['GET'])
def upravljanje_kuponima():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        cursor.execute("SELECT * FROM kuponi")
        kuponi = cursor.fetchall()
    except MySQLdb.MySQLError as e:
        flash(f'Greška prilikom dohvaćanja kupona: {e}', 'error')
        kuponi = []
    finally:
        cursor.close()
        db.close()
    
    return render_template('upravljanje_kuponima.html', kuponi=kuponi)


@app.route('/dodaj_kupon', methods=['GET', 'POST'])
def dodaj_kupon():
    if request.method == 'GET':
        return render_template('dodaj_kupon.html')
    
    elif request.method == 'POST':
        data = request.form
        kod = data['kod']
        postotak_popusta = data['postotak_popusta']
        datum_pocetka = data['datum_pocetka']
        datum_zavrsetka = data['datum_zavrsetka']
        max_iskoristenja = data['max_iskoristenja']
        
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO kuponi (kod, postotak_popusta, datum_pocetka, datum_zavrsetka, max_iskoristenja)
                VALUES (%s, %s, %s, %s, %s)
            """, (kod, postotak_popusta, datum_pocetka, datum_zavrsetka, max_iskoristenja))
            db.commit()
            flash('Kupon uspješno dodan!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška prilikom dodavanja kupona: {e}', 'error')
        finally:
            cursor.close()
            db.close()
        
        return redirect(url_for('upravljanje_kuponima'))


@app.route('/azuriraj_kupon/<int:kupon_id>', methods=['GET', 'POST'])
def azuriraj_kupon(kupon_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM kuponi WHERE id = %s", (kupon_id,))
        kupon = cursor.fetchone()
        if not kupon:
            flash('Kupon nije pronađen!', 'error')
            return redirect(url_for('upravljanje_kuponima'))
        return render_template('azuriraj_kupon.html', kupon=kupon)
    
    elif request.method == 'POST':
        data = request.form
        kod = data['kod']
        postotak_popusta = data['postotak_popusta']
        datum_pocetka = data['datum_pocetka']
        datum_zavrsetka = data['datum_zavrsetka']
        max_iskoristenja = data['max_iskoristenja']
        
        try:
            cursor.execute("""
                UPDATE kuponi
                SET kod = %s, postotak_popusta = %s, datum_pocetka = %s, datum_zavrsetka = %s, max_iskoristenja = %s
                WHERE id = %s
            """, (kod, postotak_popusta, datum_pocetka, datum_zavrsetka, max_iskoristenja, kupon_id))
            db.commit()
            flash('Kupon uspješno ažuriran!', 'success')
        except MySQLdb.MySQLError as e:
            flash(f'Greška prilikom ažuriranja kupona: {e}', 'error')
        finally:
            cursor.close()
            db.close()
        
        return redirect(url_for('upravljanje_kuponima'))

@app.route('/obrisi_kupon/<int:kupon_id>', methods=['DELETE'])
def obrisi_kupon(kupon_id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM kuponi WHERE id = %s", (kupon_id,))
        db.commit()
        return jsonify({'success': True, 'message': 'Kupon uspješno obrisan!'})
    except MySQLdb.MySQLError as e:
        return jsonify({'success': False, 'message': f'Greška prilikom brisanja kupona: {e}'}), 500
    finally:
        cursor.close()
        db.close()


@app.route('/upravljanje_povratima', methods=['GET'])
def upravljanje_povratima():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    cursor.execute("""
        SELECT p.id, s.narudzba_id, p.datum_povrata, p.razlog, p.status_povrata, s.proizvod_id, pr.naziv AS proizvod_naziv
        FROM povrati_proizvoda p
        JOIN stavke_narudzbe s ON p.stavka_id = s.id
        JOIN proizvodi pr ON s.proizvod_id = pr.id
    """)
    povrati = cursor.fetchall()

    db.close()

    return render_template('upravljanje_povratima.html', povrati=povrati)



@app.route('/azuriraj_povrat/<int:id>', methods=['GET', 'POST'])
def azuriraj_povrat(id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'POST':
        status_povrata = request.form['status_povrata']
        cursor.execute("""
            UPDATE povrati_proizvoda
            SET status_povrata = %s
            WHERE id = %s
        """, (status_povrata, id))
        db.commit()
        db.close()
        flash('Povrat ažuriran.', 'success')
        return redirect(url_for('upravljanje_povratima'))

    cursor.execute("""
        SELECT p.id, s.narudzba_id, p.datum_povrata, p.razlog, p.status_povrata, s.proizvod_id, pr.naziv AS proizvod_naziv
        FROM povrati_proizvoda p
        JOIN stavke_narudzbe s ON p.stavka_id = s.id
        JOIN proizvodi pr ON s.proizvod_id = pr.id
        WHERE p.id = %s
    """, (id,))
    povrat = cursor.fetchone()
    db.close()

    return render_template('azuriraj_povrat.html', povrat=povrat)


@app.route('/upravljanje_podrskom', methods=['GET'])
def upravljanje_podrskom():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    cursor.execute("""
        SELECT p.id, k.ime, k.prezime, k.email, p.tema, p.poruka, p.status, p.datum_upita, p.datum_odgovora
        FROM podrska_za_korisnike p
        JOIN korisnici k ON p.korisnik_id = k.id
    """)
    podrska = cursor.fetchall()

    db.close()

    return render_template('upravljanje_podrskom.html', podrska=podrska)


@app.route('/azuriraj_podrsku/<int:id>', methods=['GET', 'POST'])
def azuriraj_podrsku(id):
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'POST':
        status = request.form['status']
        datum_odgovora = date.today() if status == 'riješeno' else None
        cursor.execute("""
            UPDATE podrska_za_korisnike
            SET status = %s, datum_odgovora = %s
            WHERE id = %s
        """, (status, datum_odgovora, id))
        db.commit()
        db.close()
        flash('Status podrške ažuriran.', 'success')
        return redirect(url_for('upravljanje_podrskom'))

    cursor.execute("""
        SELECT p.id, k.ime, k.prezime, k.email, p.tema, p.poruka, p.status, p.datum_upita, p.datum_odgovora
        FROM podrska_za_korisnike p
        JOIN korisnici k ON p.korisnik_id = k.id
        WHERE p.id = %s
    """, (id,))
    podrska = cursor.fetchone()
    db.close()

    return render_template('azuriraj_podrsku.html', podrska=podrska)

@app.route('/upravljanje_isporukama', methods=['GET', 'POST'])
def upravljanje_isporukama():
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'POST':
        
        isporuka_id = request.form['isporuka_id']
        novi_status = request.form['status_isporuke']

        try:
            
            cursor.execute("""
                UPDATE pracenje_isporuka pi
                JOIN narudzbe n ON pi.narudzba_id = n.id
                JOIN nacini_isporuke ni ON n.nacin_isporuke_id = ni.id
                SET pi.status_isporuke = %s,
                    pi.datum_isporuke = CASE
                        WHEN %s = 'poslano' THEN DATE_ADD(CURDATE(), INTERVAL ni.trajanje DAY)
                        ELSE NULL
                    END
                WHERE pi.id = %s
            """, (novi_status, novi_status, isporuka_id))
            db.commit()
            flash('Status isporuke uspješno ažuriran!', 'success')

        except MySQLdb.MySQLError as e:
            flash(f'Greška: {e.args[1]}', 'error')
            db.rollback()

   
    cursor.execute("""
        SELECT pi.id, pi.narudzba_id, n.datum_narudzbe, pi.status_isporuke, pi.datum_isporuke
        FROM pracenje_isporuka pi
        JOIN narudzbe n ON pi.narudzba_id = n.id
    """)
    isporuke = cursor.fetchall()

    db.close()
    return render_template('upravljanje_isporukama.html', isporuke=isporuke)


@app.route('/azuriraj_isporuku/<int:isp_id>', methods=['POST'])
def azuriraj_isporuku(isp_id):
    
    novi_status = request.form['status_isporuke']

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        
        cursor.execute("""
            UPDATE pracenje_isporuka pi
            JOIN narudzbe n ON pi.narudzba_id = n.id
            JOIN nacini_isporuke ni ON n.nacin_isporuke_id = ni.id
            SET pi.status_isporuke = %s,
                pi.datum_isporuke = CASE
                    WHEN %s = 'poslano' THEN DATE_ADD(CURDATE(), INTERVAL ni.trajanje DAY)
                    ELSE NULL
                END
            WHERE pi.id = %s
        """, (novi_status, novi_status, isp_id))
        db.commit()
        flash('Status isporuke uspješno ažuriran!', 'success')
    except MySQLdb.MySQLError as e:
        db.rollback()
        flash(f'Greška: {e.args[1]}', 'error')
    finally:
        db.close()

    return redirect(url_for('upravljanje_isporukama'))


@app.route('/upravljanje_nacinima_isporuke', methods=['GET'])
def upravljanje_nacinima_isporuke():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    
    cursor.execute("SELECT * FROM nacini_isporuke")
    nacini_isporuke = cursor.fetchall()

    db.close()
    return render_template('upravljanje_nacinima_isporuke.html', nacini_isporuke=nacini_isporuke)



@app.route('/dodaj_nacin_isporuke', methods=['GET', 'POST'])
def dodaj_nacin_isporuke():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    if request.method == 'POST':
        naziv = request.form['naziv']
        opis = request.form.get('opis', '')
        cijena = request.form['cijena']
        trajanje = request.form['trajanje']

        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO nacini_isporuke (naziv, opis, cijena, trajanje)
                VALUES (%s, %s, %s, %s)
            """, (naziv, opis, cijena, trajanje))
            db.commit()
            flash('Način isporuke uspješno dodan!', 'success')
        except MySQLdb.MySQLError as e:
            db.rollback()
            flash(f'Greška: {e.args[1]}', 'error')
        finally:
            db.close()
        return redirect(url_for('upravljanje_nacinima_isporuke'))

    return render_template('dodaj_nacin_isporuke.html')


@app.route('/azuriraj_nacin_isporuke/<int:id>', methods=['GET', 'POST'])
def azuriraj_nacin_isporuke(id):
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'POST':
        naziv = request.form['naziv']
        opis = request.form.get('opis', '')
        cijena = request.form['cijena']
        trajanje = request.form['trajanje']

        try:
            cursor.execute("""
                UPDATE nacini_isporuke
                SET naziv = %s, opis = %s, cijena = %s, trajanje = %s
                WHERE id = %s
            """, (naziv, opis, cijena, trajanje, id))
            db.commit()
            flash('Način isporuke uspješno ažuriran!', 'success')
        except MySQLdb.MySQLError as e:
            db.rollback()
            flash(f'Greška: {e.args[1]}', 'error')
        finally:
            db.close()
        return redirect(url_for('upravljanje_nacinima_isporuke'))

    
    cursor.execute("SELECT * FROM nacini_isporuke WHERE id = %s", (id,))
    nacin_isporuke = cursor.fetchone()
    db.close()

    return render_template('azuriraj_nacin_isporuke.html', nacin_isporuke=nacin_isporuke)

@app.route('/obrisi_nacin_isporuke/<int:id>', methods=['POST'])
def obrisi_nacin_isporuke(id):
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM nacini_isporuke WHERE id = %s", (id,))
        db.commit()
        flash('Način isporuke uspješno obrisan!', 'success')
    except MySQLdb.MySQLError as e:
        db.rollback()
        flash(f'Greška: {e.args[1]}', 'error')
    finally:
        db.close()

    return redirect(url_for('upravljanje_nacinima_isporuke'))


@app.route('/upravljanje_pracenjem', methods=['GET', 'POST'])
def upravljanje_pracenjem():
    if 'user_id' not in session:
        return redirect(url_for('prijava'))

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    if request.method == 'POST':
        pracenje_id = request.form.get('pracenje_id')
        novi_status = request.form.get('status_isporuke')

        try:
            
            cursor.execute("""
                UPDATE pracenje_isporuka
                SET status_isporuke = %s
                WHERE id = %s
            """, (novi_status, pracenje_id))
            db.commit()
            flash('Status isporuke uspješno ažuriran!', 'success')
        except MySQLdb.MySQLError as e:
            db.rollback()
            flash(f'Greška: {e.args[1]}', 'error')

    
    cursor.execute("""
        SELECT pi.id, pi.narudzba_id, n.datum_narudzbe, n.status_narudzbe, 
               pi.status_isporuke, pi.datum_isporuke
        FROM pracenje_isporuka pi
        JOIN narudzbe n ON pi.narudzba_id = n.id
    """)
    pracenje_list = cursor.fetchall()
    db.close()

    return render_template('upravljanje_pracenjem.html', pracenje_list=pracenje_list)


@app.route('/azuriraj_pracenje/<int:pracenje_id>', methods=['POST'])
def azuriraj_pracenje(pracenje_id):
    novi_status = request.form['status_isporuke']

    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    try:
        
        cursor.execute("""
            UPDATE pracenje_isporuka
            SET status_isporuke = %s
            WHERE id = %s
        """, (novi_status, pracenje_id))
        db.commit()
        flash('Status isporuke uspješno ažuriran!', 'success')
    except MySQLdb.MySQLError as e:
        db.rollback()
        flash(f'Greška: {e.args[1]}', 'error')
    finally:
        db.close()

    return redirect(url_for('upravljanje_pracenjem'))




if __name__ == '__main__':
    app.run(debug=True)
