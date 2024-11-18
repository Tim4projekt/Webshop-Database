document.addEventListener('DOMContentLoaded', () => {
    dohvatiProizvode();
});

// Funkcija za dohvaćanje proizvoda iz API-ja
async function dohvatiProizvode() {
    const response = await fetch('/api/proizvodi');
    const proizvodi = await response.json();
    const listaProizvoda = document.getElementById('lista-proizvoda');

    proizvodi.forEach(proizvod => {
        const div = document.createElement('div');
        div.innerHTML = `
            <h3>${proizvod[1]}</h3>
            <p>Cijena: ${proizvod[3]} HRK</p>
            <button class="dodaj-u-kosaricu" data-id="${proizvod[0]}">Dodaj u košaricu</button>
        `;
        listaProizvoda.appendChild(div);
    });

    // Dodavanje event listener-a za dugmad "Dodaj u košaricu"
    document.querySelectorAll('.dodaj-u-kosaricu').forEach(button => {
        button.addEventListener('click', (event) => {
            const proizvodId = event.target.getAttribute('data-id');
            alert(`Proizvod ID ${proizvodId} dodan u košaricu!`);
            // Ovdje možete dodati logiku za dodavanje u košaricu
        });
    });
}



// Funkcija za dodavanje proizvoda u košaricu
async function dodajUKosaricu(proizvodId, kolicina) {
    const response = await fetch('/api/kosarica', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ proizvodId, kolicina })
    });

    const data = await response.json();
    alert(data.message);
}

// Dodavanje event listener-a za dugmad "Dodaj u košaricu"
document.querySelectorAll('.dodaj-u-kosaricu').forEach(button => {
    button.addEventListener('click', (event) => {
        const proizvodId = event.target.getAttribute('data-id');
        const kolicina = 1; // Možete dodati opciju za odabir količine
        dodajUKosaricu(proizvodId, kolicina);
    });
});


document.getElementById('zavrsi-narudzbu').addEventListener('click', async () => {
    const response = await fetch('/api/narudzba', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    const data = await response.json();
    alert(data.message);
});