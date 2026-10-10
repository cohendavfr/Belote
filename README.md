# Belote

Belote en Python, dans le terminal : vous et Partenaire contre Ouest et Est (3 bots). Deux modes : **belote contrat** (par défaut) et **coinche**.

## Lancer

```bash
python3 belote.py                  # belote contrat, jusqu'à 1000 points
python3 belote.py --coinche        # mode coinche
python3 belote.py --cible 500      # autre score cible
python3 belote.py --auto --seed 1  # 4 bots jouent entre eux (reproductible)
python3 -m unittest -v             # tests
```

## Règles communes

- Jeu de 32 cartes, valeurs atout / hors atout, dix de der (+10), belote-rebelote (+20)
- Jeu des plis : fournir, couper (sauf si le partenaire est maître), surcouper / monter à l'atout

## Belote contrat

- 5 cartes distribuées, carte retournée, enchères en 2 tours, puis 3 cartes (2 pour le preneur qui reçoit la retournée)
- Le preneur doit marquer plus que ses adversaires, sinon « chute » (162 points pour la défense)
- Capot : +90

## Coinche

- 8 cartes distribuées, enchères au point : 80 à 160 par 10, puis capot (250) ; fin après 3 passes
- Les adversaires du preneur peuvent **coincher** (x2), le preneur peut **surcoincher** (x4)
- Contrat rempli (belote comprise) : sans coinche, le preneur marque ses points + le contrat, la défense ses points ; avec coinche, le preneur marque (162 + contrat) × multiplicateur
- Contrat chuté : la défense marque (162 + contrat) × multiplicateur
- Capot : le preneur doit gagner les 8 plis

## À faire

- Bots plus malins (mémoire des cartes jouées, défense, enchères de soutien au partenaire)
- Annonces de coinche « générale »
