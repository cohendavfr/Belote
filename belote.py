"""Belote contrat à 4 joueurs : vous (0) et Partenaire (2) contre Ouest (1) et Est (3)."""
import argparse
import random

COULEURS = ["Coeur", "Carreau", "Trefle", "Pique"]
SYMBOLES = {"Coeur": "♥", "Carreau": "♦", "Trefle": "♣", "Pique": "♠"}
VALEURS = ["7", "8", "9", "10", "Valet", "Dame", "Roi", "As"]

POINTS_ATOUT = {"7": 0, "8": 0, "9": 14, "10": 10, "Valet": 20, "Dame": 3, "Roi": 4, "As": 11}
POINTS_HORS_ATOUT = {"7": 0, "8": 0, "9": 0, "10": 10, "Valet": 2, "Dame": 3, "Roi": 4, "As": 11}

# Du plus faible au plus fort
ORDRE_ATOUT = ["7", "8", "Dame", "Roi", "10", "As", "9", "Valet"]
ORDRE_PLAIN = ["7", "8", "9", "Valet", "Dame", "Roi", "10", "As"]

NOMS = ["Vous", "Ouest", "Partenaire", "Est"]
EQUIPES = ["Vous + Partenaire", "Ouest + Est"]
BONUS_DIX_DE_DER = 10
BONUS_BELOTE = 20
BONUS_CAPOT = 90
TOTAL_CARTES = 162


def creer_jeu():
    return [(valeur, couleur) for couleur in COULEURS for valeur in VALEURS]


def nom_carte(carte):
    return f"{carte[0]}{SYMBOLES[carte[1]]}"


def points(carte, atout):
    valeur, couleur = carte
    return (POINTS_ATOUT if couleur == atout else POINTS_HORS_ATOUT)[valeur]


def force(carte, atout, demandee):
    """Force d'une carte dans un pli : atout > couleur demandée > rien."""
    valeur, couleur = carte
    if couleur == atout:
        return 100 + ORDRE_ATOUT.index(valeur)
    if couleur == demandee:
        return ORDRE_PLAIN.index(valeur)
    return -1


def gagnant_pli(pli, atout):
    """pli : liste de (joueur, carte) dans l'ordre de jeu. Renvoie le joueur gagnant."""
    demandee = pli[0][1][1]
    return max(pli, key=lambda jc: force(jc[1], atout, demandee))[0]


def cartes_jouables(main, pli, atout):
    """Règles : fournir, sinon couper (sauf si le partenaire est maître), monter à l'atout."""
    if not pli:
        return list(main)
    demandee = pli[0][1][1]
    meilleure = max(force(c, atout, demandee) for _, c in pli)

    meme_couleur = [c for c in main if c[1] == demandee]
    if meme_couleur:
        if demandee == atout:
            plus_fortes = [c for c in meme_couleur if force(c, atout, demandee) > meilleure]
            return plus_fortes or meme_couleur
        return meme_couleur

    joueur = (pli[0][0] + len(pli)) % 4
    if gagnant_pli(pli, atout) == (joueur + 2) % 4:
        return list(main)

    atouts = [c for c in main if c[1] == atout]
    if atouts:
        plus_forts = [c for c in atouts if force(c, atout, demandee) > meilleure]
        return plus_forts or atouts
    return list(main)


def trier_main(main, atout=None):
    def cle(c):
        ordre = ORDRE_ATOUT if c[1] == atout else ORDRE_PLAIN
        return (c[1] == atout, COULEURS.index(c[1]), ordre.index(c[0]))
    return sorted(main, key=cle)


def afficher_main(main, atout=None):
    return "  ".join(nom_carte(c) for c in trier_main(main, atout))


# --- Joueurs -----------------------------------------------------------------

class Bot:
    def valeur_main(self, main, couleur):
        cartes = [c for c in main if c[1] == couleur]
        total = sum(POINTS_ATOUT[v] for v, _ in cartes)
        if len(cartes) >= 3:
            total += 10
        total += 5 * sum(1 for v, c in main if v == "As" and c != couleur)
        return total

    def prise(self, main, retournee, tour):
        if tour == 1:
            candidats = [retournee[1]]
            main = main + [retournee]
            seuil = 45
        else:
            candidats = [c for c in COULEURS if c != retournee[1]]
            seuil = 42
        meilleur = max(candidats, key=lambda c: self.valeur_main(main, c))
        return meilleur if self.valeur_main(main, meilleur) >= seuil else None

    def choisir_carte(self, main, jouables, pli, atout):
        if len(jouables) == 1:
            return jouables[0]
        demandee = pli[0][1][1] if pli else None
        if not pli:
            atouts = [c for c in jouables if c[1] == atout]
            if ("Valet", atout) in atouts:
                return ("Valet", atout)
            as_ = [c for c in jouables if c[0] == "As" and c[1] != atout]
            if as_:
                return as_[0]
            return min(jouables, key=lambda c: (points(c, atout), force(c, atout, c[1])))
        courant = gagnant_pli(pli, atout)
        joueur = (pli[0][0] + len(pli)) % 4
        if courant == (joueur + 2) % 4:
            return max(jouables, key=lambda c: points(c, atout))
        meilleure = max(force(c, atout, demandee) for _, c in pli)
        gagnantes = [c for c in jouables if force(c, atout, demandee) > meilleure]
        if gagnantes:
            return min(gagnantes, key=lambda c: force(c, atout, demandee))
        return min(jouables, key=lambda c: (points(c, atout), force(c, atout, demandee)))


class Humain:
    def _demander(self, texte):
        return input(texte).strip().lower()

    def prise(self, main, retournee, tour):
        print(f"\nVotre main : {afficher_main(main)}")
        if tour == 1:
            rep = self._demander(f"Carte retournée : {nom_carte(retournee)}. Prendre à {retournee[1]} ? (o/n) ")
            return retournee[1] if rep in ("o", "oui", "y") else None
        choix = [c for c in COULEURS if c != retournee[1]]
        while True:
            rep = self._demander(
                "Choisir un atout : " + ", ".join(f"{i + 1}={SYMBOLES[c]}" for i, c in enumerate(choix)) + " (n = passer) "
            )
            if rep in ("n", "non", ""):
                return None
            if rep.isdigit() and 1 <= int(rep) <= len(choix):
                return choix[int(rep) - 1]

    def choisir_carte(self, main, jouables, pli, atout):
        if pli:
            print("Pli en cours : " + ", ".join(f"{NOMS[j]} {nom_carte(c)}" for j, c in pli))
        main = trier_main(main, atout)
        print("Votre main : " + "  ".join(
            f"[{i + 1}]{nom_carte(c)}" if c in jouables else f" -{nom_carte(c)}" for i, c in enumerate(main)
        ))
        while True:
            rep = self._demander("Votre carte (numéro) : ")
            if rep.isdigit() and 1 <= int(rep) <= len(main) and main[int(rep) - 1] in jouables:
                return main[int(rep) - 1]
            print("Carte non jouable.")


# --- Déroulement d'une donne ---------------------------------------------------

def encheres(joueurs, mains, retournee, donneur, parler):
    for tour in (1, 2):
        for k in range(4):
            p = (donneur + 1 + k) % 4
            choix = joueurs[p].prise(mains[p], retournee, tour)
            if choix is not None:
                parler(f"{NOMS[p]} prend à {SYMBOLES[choix]} {choix}.")
                return p, choix
            parler(f"{NOMS[p]} passe.")
    return None, None


def jouer_donne(joueurs, donneur, parler=print):
    """Joue une donne. Renvoie None si personne ne prend, sinon un dict de résultats."""
    jeu = creer_jeu()
    random.shuffle(jeu)
    mains = [jeu[i * 5:(i + 1) * 5] for i in range(4)]
    retournee, reste = jeu[20], jeu[21:]

    parler(f"\n=== Donneur : {NOMS[donneur]} — carte retournée : {nom_carte(retournee)} ===")
    preneur, atout = encheres(joueurs, mains, retournee, donneur, parler)
    if preneur is None:
        parler("Personne ne prend : on redistribue.")
        return None

    mains[preneur].append(retournee)
    i = 0
    for p in range(4):
        n = 2 if p == preneur else 3
        mains[p] += reste[i:i + n]
        i += n

    belote_equipe = None
    for p in range(4):
        if ("Roi", atout) in mains[p] and ("Dame", atout) in mains[p]:
            belote_equipe = p % 2

    parler(f"Atout : {SYMBOLES[atout]} {atout} (pris par {NOMS[preneur]})")

    belote_jouees = 0
    cartes = [0, 0]
    plis = [0, 0]
    meneur = (donneur + 1) % 4
    for numero in range(8):
        pli = []
        for k in range(4):
            p = (meneur + k) % 4
            jouables = cartes_jouables(mains[p], pli, atout)
            carte = joueurs[p].choisir_carte(mains[p], jouables, pli, atout)
            assert carte in jouables
            mains[p].remove(carte)
            pli.append((p, carte))
            if p != 0 or not isinstance(joueurs[0], Humain):
                parler(f"  {NOMS[p]} joue {nom_carte(carte)}")
            if belote_equipe == p % 2 and carte in (("Roi", atout), ("Dame", atout)) \
                    and ("Roi", atout) not in mains[(p + 2) % 4] + mains[(p + 1) % 4] + mains[(p + 3) % 4] \
                    and ("Dame", atout) not in mains[(p + 2) % 4] + mains[(p + 1) % 4] + mains[(p + 3) % 4]:
                belote_jouees += 1
                parler("  ... Belote !" if belote_jouees == 1 else "  ... Rebelote !")
        gagnant = gagnant_pli(pli, atout)
        gain = sum(points(c, atout) for _, c in pli) + (BONUS_DIX_DE_DER if numero == 7 else 0)
        cartes[gagnant % 2] += gain
        plis[gagnant % 2] += 1
        parler(f"Pli {numero + 1} : {NOMS[gagnant]} (+{gain})")
        meneur = gagnant

    return resultat(preneur, cartes, plis, belote_equipe, atout)


def resultat(preneur, cartes, plis, belote_equipe, atout=None):
    totaux = list(cartes)
    if belote_equipe is not None:
        totaux[belote_equipe] += BONUS_BELOTE
    for e in (0, 1):
        if plis[e] == 8:
            totaux[e] += BONUS_CAPOT

    eq = preneur % 2
    contrat_rempli = totaux[eq] > totaux[1 - eq]
    marque = list(totaux)
    if not contrat_rempli:
        marque = [0, 0]
        marque[1 - eq] = TOTAL_CARTES
        if belote_equipe is not None:
            marque[belote_equipe] += BONUS_BELOTE
    return {
        "preneur": preneur, "atout": atout, "cartes": cartes, "plis": plis,
        "belote": belote_equipe, "totaux": totaux, "marque": marque, "rempli": contrat_rempli,
    }


def jouer_partie(joueurs, cible=1000, parler=print):
    scores = [0, 0]
    donneur = random.randrange(4)
    while max(scores) < cible:
        res = jouer_donne(joueurs, donneur, parler)
        donneur = (donneur + 1) % 4
        if res is None:
            continue
        for e in (0, 1):
            scores[e] += res["marque"][e]
        statut = "contrat rempli" if res["rempli"] else "CHUTE du preneur"
        parler(f"→ {statut} ; donne : {res['marque'][0]} - {res['marque'][1]} ; "
               f"total : {EQUIPES[0]} {scores[0]} / {EQUIPES[1]} {scores[1]}")
    if scores[0] == scores[1]:
        return scores
    gagnante = 0 if scores[0] > scores[1] else 1
    parler(f"\nVictoire de l'équipe {EQUIPES[gagnante]} !")
    return scores


def main():
    parser = argparse.ArgumentParser(description="Belote")
    parser.add_argument("--auto", action="store_true", help="4 bots jouent entre eux")
    parser.add_argument("--seed", type=int, help="graine aléatoire")
    parser.add_argument("--cible", type=int, default=1000, help="score à atteindre (défaut 1000)")
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    joueurs = [Bot() if args.auto else Humain(), Bot(), Bot(), Bot()]
    jouer_partie(joueurs, args.cible)


if __name__ == "__main__":
    main()
