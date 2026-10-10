# Belote

Belote contrat à 4 joueurs en Python, dans le terminal : vous et Partenaire contre Ouest et Est (3 bots).

## Lancer

```bash
python3 belote.py                  # partie jusqu'à 1000 points, vous contre 3 bots
python3 belote.py --cible 500      # autre score cible
python3 belote.py --auto --seed 1  # 4 bots jouent entre eux (reproductible)
python3 -m unittest -v             # tests
```

## Règles implémentées

- Jeu de 32 cartes, 5 cartes distribuées, carte retournée, puis 3 cartes (2 pour le preneur qui reçoit la retournée)
- Enchères en 2 tours (à la couleur retournée, puis à une autre couleur) ; redistribution si tout le monde passe
- Jeu des plis : fournir, couper (sauf si le partenaire est maître), surcouper / monter à l'atout
- Valeurs atout / hors atout, dix de der (+10), belote-rebelote (+20), capot (+90)
- Contrat : le preneur doit marquer plus que ses adversaires, sinon « chute » (162 points pour la défense)

## À faire

- Annonces (tierce, cinquante, cent, carré)
- Bots plus malins (mémoire des cartes jouées, défense)
- Mode « coinche » / contre
