import random

COULEURS = ["Coeur", "Carreau", "Trefle", "Pique"]
VALEURS = ["7", "8", "9", "10", "Valet", "Dame", "Roi", "As"]

POINTS_ATOUT = {"7": 0, "8": 0, "9": 14, "10": 10, "Valet": 20, "Dame": 3, "Roi": 4, "As": 11}
POINTS_HORS_ATOUT = {"7": 0, "8": 0, "9": 0, "10": 10, "Valet": 2, "Dame": 3, "Roi": 4, "As": 11}


def creer_jeu():
    return [(valeur, couleur) for couleur in COULEURS for valeur in VALEURS]


def distribuer(jeu, joueurs=4, cartes=8):
    jeu = jeu[:]
    random.shuffle(jeu)
    return [jeu[i * cartes:(i + 1) * cartes] for i in range(joueurs)]


def points(carte, atout):
    valeur, couleur = carte
    table = POINTS_ATOUT if couleur == atout else POINTS_HORS_ATOUT
    return table[valeur]


if __name__ == "__main__":
    atout = random.choice(COULEURS)
    print(f"Atout : {atout}\n")
    for i, main in enumerate(distribuer(creer_jeu()), start=1):
        total = sum(points(c, atout) for c in main)
        cartes = ", ".join(f"{v} de {c}" for v, c in main)
        print(f"Joueur {i} ({total} pts) : {cartes}")
