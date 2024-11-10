DROP DATABASE IF EXISTS webs;
CREATE DATABASE webs;
USE webs;

-- 1. Korisnici (Users)
CREATE TABLE Korisnici (
    korisnik_id INT PRIMARY KEY AUTO_INCREMENT,
    ime VARCHAR(50) NOT NULL,
    prezime VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    lozinka VARCHAR(255) NOT NULL,  -- Ensure passwords are hashed before storing
    datum_registracije DATETIME DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'aktivan',
    deleted_at DATETIME,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

INSERT INTO Korisnici (ime, prezime, email, lozinka, datum_registracije, status)
VALUES
('Marko', 'Markić', 'marko@example.com', 'hashed_password_123', '2024-01-01 00:00:00', 'aktivan'),
('Ivana', 'Horvat', 'ivana@example.com', 'hashed_password_123', '2024-02-12 00:00:00', 'aktivan');

-- 2. KorisnickeGrupe (User Roles)
CREATE TABLE KorisnickeGrupe (
    grupa_id INT PRIMARY KEY AUTO_INCREMENT,
    naziv VARCHAR(50) NOT NULL,
    opis TEXT
);

INSERT INTO KorisnickeGrupe (naziv, opis)
VALUES
('Administrator', 'Korisnik s najvišim privilegijama, ima pristup svim funkcijama sustava.'),
('Kupac', 'Korisnik koji obavlja kupovinu na webshopu i upravlja svojim narudžbama.');

-- Junction Table for User Groups
CREATE TABLE KorisniciGrupe (
    korisnik_id INT,
    grupa_id INT,
    PRIMARY KEY (korisnik_id, grupa_id),
    FOREIGN KEY (korisnik_id) REFERENCES Korisnici(korisnik_id) ON DELETE CASCADE,
    FOREIGN KEY (grupa_id) REFERENCES KorisnickeGrupe(grupa_id) ON DELETE CASCADE
);

INSERT INTO KorisniciGrupe (korisnik_id, grupa_id)
VALUES
(1, 1),
(2, 2);

-- 3. Proizvodaci (Manufacturers)
CREATE TABLE Proizvodaci (
    proizvodjac_id INT PRIMARY KEY AUTO_INCREMENT,
    naziv VARCHAR(100) NOT NULL,
    drzava VARCHAR(50),
    opis TEXT
);

INSERT INTO Proizvodaci (naziv, drzava, opis)
VALUES
('Proizvođač 1', 'Hrvatska', 'Opis proizvođača 1'),
('Proizvođač 2', 'SAD', 'Opis proizvođača 2');

-- 4. Proizvodi (Products)
CREATE TABLE Proizvodi (
    proizvod_id INT PRIMARY KEY AUTO_INCREMENT,
    naziv VARCHAR(100) NOT NULL,
    opis TEXT,
    cijena DECIMAL(10, 2) NOT NULL,
    kolicina_na_skladistu INT NOT NULL,
    datum_dodavanja DATETIME DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'dostupan',
    proizvodjac_id INT NOT NULL,
    deleted_at DATETIME,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (proizvodjac_id) REFERENCES Proizvodaci(proizvodjac_id) ON DELETE CASCADE
);

INSERT INTO Proizvodi (naziv, opis, cijena, kolicina_na_skladistu, datum_dodavanja, status, proizvodjac_id)
VALUES
('Proizvod 1', 'Opis proizvoda 1', 100.00, 10, '2024-01-01 00:00:00', 'dostupan', 1),
('Proizvod 2', 'Opis proizvoda 2', 150.00, 5, '2024-01-02 00:00:00', 'dostupan', 2);

-- 5. Kategorije (Categories)
CREATE TABLE Kategorije (
    kategorija_id INT PRIMARY KEY AUTO_INCREMENT,
    naziv VARCHAR(50) NOT NULL,
    opis TEXT
);

INSERT INTO Kategorije (naziv, opis)
VALUES
('Kategorija 1', 'Opis kategorije 1'),
('Kategorija 2', 'Opis kategorije 2');

-- Junction Table for Product Categories
CREATE TABLE ProizvodKategorije (
    proizvod_id INT,
    kategorija_id INT,
    PRIMARY KEY (proizvod_id, kategorija_id),
    FOREIGN KEY (proizvod_id) REFERENCES Proizvodi(proizvod_id) ON DELETE CASCADE,
    FOREIGN KEY (kategorija_id) REFERENCES Kategorije(kategorija_id) ON DELETE CASCADE
);

INSERT INTO ProizvodKategorije (proizvod_id, kategorija_id)
VALUES
(1, 1),
(2, 2);

-- 6. Adrese (Addresses)
CREATE TABLE Adrese (
    adresa_id INT PRIMARY KEY AUTO_INCREMENT,
    korisnik_id INT NOT NULL,
    ulica VARCHAR(100) NOT NULL,
    grad VARCHAR(50) NOT NULL,
    drzava VARCHAR(50) NOT NULL,
    postanski_broj VARCHAR(10) NOT NULL,
    tip_adrese ENUM('Dostava', 'Fakturiranje') NOT NULL,
    FOREIGN KEY (korisnik_id) REFERENCES Korisnici(korisnik_id) ON DELETE CASCADE
);

INSERT INTO Adrese (korisnik_id, ulica, grad, drzava, postanski_broj, tip_adrese)
VALUES
(1, 'Ilica 1', 'Zagreb', 'Hrvatska', '10000', 'Dostava'),
(1, 'Ilica 2', 'Zagreb', 'Hrvatska', '10000', 'Fakturiranje'),
(2, 'Vukovarska 2', 'Split', 'Hrvatska', '21000', 'Dostava'),
(2, 'Vukovarska 3', 'Split', 'Hrvatska', '21000', 'Fakturiranje');

-- 7. StatusTypes (Status Types Table)
CREATE TABLE StatusTypes (
    status_id INT PRIMARY KEY AUTO_INCREMENT,
    naziv VARCHAR(50) NOT NULL
);

INSERT INTO StatusTypes (naziv) VALUES ('Na čekanju'), ('Obrađena'), ('Isporučena'), ('Otkažena');

-- 8. Narudzbe (Orders)
CREATE TABLE Narudzbe (
    narudzba_id INT PRIMARY KEY AUTO_INCREMENT,
    korisnik_id INT NOT NULL,
    datum_narudzbe DATETIME DEFAULT NOW(),
    ukupna_cijena DECIMAL(10, 2) NOT NULL,
    status_id INT NOT NULL,
    billing_address_id INT,
    shipping_address_id INT,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (korisnik_id) REFERENCES Korisnici(korisnik_id) ON DELETE CASCADE,
    FOREIGN KEY (status_id) REFERENCES StatusTypes(status_id) ON DELETE RESTRICT,
    FOREIGN KEY (billing_address_id) REFERENCES Adrese(adresa_id) ON DELETE SET NULL,
    FOREIGN KEY (shipping_address_id) REFERENCES Adrese(adresa_id) ON DELETE SET NULL
);

INSERT INTO Narudzbe (korisnik_id, datum_narudzbe, ukupna_cijena, status_id, billing_address_id, shipping_address_id)
VALUES
(1, '2024-01-01 00:00:00', 1000.00, 1, 2, 1),
(2, '2024-01-02 00:00:00', 1500.00, 2, 4, 3);

-- 9. StavkeNarudzbe (Order Items)
CREATE TABLE StavkeNarudzbe (
    stavka_id INT PRIMARY KEY AUTO_INCREMENT,
    narudzba_id INT NOT NULL,
    proizvod_id INT NOT NULL,
    kolicina INT NOT NULL,
    cijena DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) AS (kolicina * cijena) STORED,
    FOREIGN KEY (narudzba_id) REFERENCES Narudzbe(narudzba_id) ON DELETE CASCADE,
    FOREIGN KEY (proizvod_id) REFERENCES Proizvodi(proizvod_id) ON DELETE CASCADE
);

INSERT INTO StavkeNarudzbe (narudzba_id, proizvod_id, kolicina, cijena)
VALUES
(1, 1, 2, 100.00),
(2, 2, 1, 150.00);

-- 10. Recenzije (Reviews)
CREATE TABLE Recenzije (
    recenzija_id INT PRIMARY KEY AUTO_INCREMENT,
    korisnik_id INT NOT NULL,
    proizvod_id INT NOT NULL,
    ocjena INT NOT NULL CHECK (ocjena BETWEEN 1 AND 5),
    komentar TEXT,
    naslov VARCHAR(100),
    datum_recenzije DATETIME DEFAULT NOW(),
    verified_purchase BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (korisnik_id) REFERENCES Korisnici(korisnik_id) ON DELETE CASCADE,
    FOREIGN KEY (proizvod_id) REFERENCES Proizvodi(proizvod_id) ON DELETE CASCADE
);

INSERT INTO Recenzije (korisnik_id, proizvod_id, ocjena, komentar, naslov, datum_recenzije)
VALUES
(1, 1, 5, 'Odličan proizvod!', 'Izvrsno', '2024-01-01 00:00:00'),
(2, 2, 4, 'Dobar proizvod, ali skup.', 'Zadovoljan', '2024-01-02 00:00:00');

-- 11. Popusti (Discounts)
CREATE TABLE Popusti (
    popust_id INT PRIMARY KEY AUTO_INCREMENT,
    proizvod_id INT NOT NULL,
    postotak DECIMAL(5, 2) DEFAULT NULL,
    fiksni_iznos DECIMAL(10, 2) DEFAULT NULL,
    uvjet VARCHAR(255),
    datum_pocetka DATE,
    datum_zavrsetka DATE,
    discount_type ENUM('percentage', 'fixed_amount'),
    FOREIGN KEY (proizvod_id) REFERENCES Proizvodi(proizvod_id) ON DELETE CASCADE,
    CONSTRAINT chk_popust CHECK (
        (postotak IS NOT NULL AND fiksni_iznos IS NULL AND discount_type = 'percentage') OR
        (fiksni_iznos IS NOT NULL AND postotak IS NULL AND discount_type = 'fixed_amount')
    )
);

INSERT INTO Popusti (proizvod_id, postotak, fiksni_iznos, uvjet, datum_pocetka, datum_zavrsetka, discount_type)
VALUES
(1, 10.00, NULL, 'Kupnja iznad 500 kn', '2024-01-01', '2024-01-15', 'percentage'),
(2, NULL, 50.00, 'Kupnja iznad 1000 kn', '2024-02-01', '2024-02-15', 'fixed_amount');

-- 12. Dostave (Deliveries)
CREATE TABLE Dostave (
    dostava_id INT PRIMARY KEY AUTO_INCREMENT,
    narudzba_id INT NOT NULL,
    datum_dostave DATETIME DEFAULT NOW(),
    dostavljac VARCHAR(100),
    trosak_dostave DECIMAL(10, 2),
    status_id INT,
    FOREIGN KEY (narudzba_id) REFERENCES Narudzbe(narudzba_id) ON DELETE CASCADE,
    FOREIGN KEY (status_id) REFERENCES StatusTypes(status_id) ON DELETE RESTRICT
);

INSERT INTO Dostave (narudzba_id, datum_dostave, dostavljac, trosak_dostave, status_id)
VALUES
(1, '2024-01-01 00:00:00', 'DHL', 50.00, 3),
(2, '2024-01-02 00:00:00', 'GLS', 70.00, 3);

-- 13. Favoriti (Favorites)
CREATE TABLE Favoriti (
    favorit_id INT PRIMARY KEY AUTO_INCREMENT,
    korisnik_id INT NOT NULL,
    proizvod_id INT NOT NULL,
    datum_dodavanja DATETIME DEFAULT NOW(),
    FOREIGN KEY (korisnik_id) REFERENCES Korisnici(korisnik_id) ON DELETE CASCADE,
    FOREIGN KEY (proizvod_id) REFERENCES Proizvodi(proizvod_id) ON DELETE CASCADE
);

INSERT INTO Favoriti (korisnik_id, proizvod_id, datum_dodavanja)
VALUES
(1, 1, '2024-01-01 00:00:00'),
(2, 2, '2024-01-02 00:00:00');

-- 14. KorisnickePoruke (User Messages)
CREATE TABLE KorisnickePoruke (
    poruka_id INT PRIMARY KEY AUTO_INCREMENT,
    korisnik_id INT NOT NULL,
    naslov VARCHAR(100),
    sadrzaj TEXT,
    datum_slanja DATETIME DEFAULT NOW(),
    status ENUM('Nepročitano', 'Pročitano') DEFAULT 'Nepročitano',
    FOREIGN KEY (korisnik_id) REFERENCES Korisnici(korisnik_id) ON DELETE CASCADE
);

INSERT INTO KorisnickePoruke (korisnik_id, naslov, sadrzaj, datum_slanja, status)
VALUES
(1, 'Upit o proizvodu', 'Zanima me više o ovom proizvodu.', '2024-01-01 00:00:00', 'Nepročitano'),
(2, 'Pitanje o dostavi', 'Kada mogu očekivati dostavu?', '2024-01-02 00:00:00', 'Pročitano');

-- 15. Povrati (Returns)
CREATE TABLE Povrati (
    povrat_id INT PRIMARY KEY AUTO_INCREMENT,
    narudzba_id INT NOT NULL,
    datum_povrata DATETIME DEFAULT NOW(),
    razlog_povrata TEXT,
    status_id INT DEFAULT 1,
    FOREIGN KEY (narudzba_id) REFERENCES Narudzbe(narudzba_id) ON DELETE CASCADE,
    FOREIGN KEY (status_id) REFERENCES StatusTypes(status_id) ON DELETE RESTRICT
);

INSERT INTO Povrati (narudzba_id, datum_povrata, razlog_povrata, status_id)
VALUES
(1, '2024-01-01 00:00:00', 'Proizvod nije ispunio očekivanja', 4),
(2, '2024-01-02 00:00:00', 'Proizvod oštećen prilikom dostave', 4);

-- 16. Placanja (Payments)
CREATE TABLE Placanja (
    placanje_id INT PRIMARY KEY AUTO_INCREMENT,
    narudzba_id INT NOT NULL,
    iznos DECIMAL(10, 2) NOT NULL,
    nacin_placanja ENUM('Kreditna kartica', 'PayPal', 'Gotovina', 'Bankovni transfer') NOT NULL,
    datum_placanja DATETIME DEFAULT NOW(),
    status_id INT DEFAULT 1,
    FOREIGN KEY (narudzba_id) REFERENCES Narudzbe(narudzba_id) ON DELETE CASCADE,
    FOREIGN KEY (status_id) REFERENCES StatusTypes(status_id) ON DELETE RESTRICT
);

INSERT INTO Placanja (narudzba_id, iznos, nacin_placanja, datum_placanja, status_id)
VALUES
(1, 1000.00, 'Kreditna kartica', '2024-01-01 00:00:00', 2),
(2, 1500.00, 'PayPal', '2024-01-02 00:00:00', 2);
