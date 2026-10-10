import random
import unittest

import belote
from belote import (Bot, cartes_jouables, gagnant_pli, jouer_donne, points, points_annonces,
                    resultat, trouver_annonces)


class TestRegles(unittest.TestCase):
    def test_total_points_jeu(self):
        for atout in belote.COULEURS:
            self.assertEqual(sum(points(c, atout) for c in belote.creer_jeu()), 152)

    def test_gagnant_atout_coupe(self):
        pli = [(0, ("As", "Coeur")), (1, ("7", "Pique")), (2, ("10", "Coeur")), (3, ("Roi", "Trefle"))]
        self.assertEqual(gagnant_pli(pli, "Pique"), 1)
        self.assertEqual(gagnant_pli(pli, "Carreau"), 0)

    def test_valet_atout_plus_fort_que_9(self):
        pli = [(0, ("9", "Coeur")), (1, ("Valet", "Coeur")), (2, ("As", "Coeur")), (3, ("10", "Coeur"))]
        self.assertEqual(gagnant_pli(pli, "Coeur"), 1)

    def test_obligation_de_fournir(self):
        main = [("7", "Coeur"), ("As", "Pique"), ("8", "Trefle")]
        pli = [(0, ("Roi", "Coeur"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("7", "Coeur")])

    def test_obligation_de_couper(self):
        main = [("As", "Pique"), ("8", "Trefle")]
        pli = [(0, ("Roi", "Coeur"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("As", "Pique")])

    def test_pas_de_coupe_si_partenaire_maitre(self):
        main = [("As", "Pique"), ("8", "Trefle")]
        pli = [(1, ("7", "Coeur")), (2, ("As", "Coeur")), (3, ("8", "Coeur"))]
        self.assertEqual(len(cartes_jouables(main, pli, "Pique")), 2)

    def test_obligation_de_surcouper(self):
        main = [("9", "Pique"), ("7", "Pique"), ("8", "Trefle")]
        pli = [(0, ("Roi", "Coeur")), (1, ("Dame", "Pique"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("9", "Pique")])

    def test_sous_couper_si_impossible_de_monter(self):
        main = [("7", "Pique"), ("8", "Trefle")]
        pli = [(0, ("Roi", "Coeur")), (1, ("Valet", "Pique"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("7", "Pique")])

    def test_monter_a_latout(self):
        main = [("7", "Pique"), ("Valet", "Pique"), ("8", "Trefle")]
        pli = [(0, ("9", "Pique"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("Valet", "Pique")])


class TestScore(unittest.TestCase):
    def test_contrat_rempli(self):
        r = resultat(0, [100, 62], [5, 3], None)
        self.assertTrue(r["rempli"])
        self.assertEqual(r["marque"], [100, 62])

    def test_chute(self):
        r = resultat(0, [70, 92], [4, 4], None)
        self.assertFalse(r["rempli"])
        self.assertEqual(r["marque"], [0, 162])

    def test_belote_et_capot(self):
        r = resultat(0, [162, 0], [8, 0], 0)
        self.assertEqual(r["marque"], [162 + 20 + 90, 0])

    def test_belote_conservee_en_cas_de_chute(self):
        r = resultat(0, [60, 102], [3, 5], 0)
        self.assertEqual(r["marque"], [20, 162])


class TestAnnonces(unittest.TestCase):
    def noms(self, main, atout="Pique"):
        return sorted(a["nom"] for a in trouver_annonces(main, atout))

    def test_tierce(self):
        main = [("7", "Coeur"), ("8", "Coeur"), ("9", "Coeur"), ("As", "Pique")]
        self.assertEqual(self.noms(main), ["Tierce à 9♥"])

    def test_cinquante_et_cent(self):
        quatre = [(v, "Trefle") for v in ("Valet", "Dame", "Roi", "As")]
        cinq = [(v, "Trefle") for v in ("9", "10", "Valet", "Dame", "Roi")]
        self.assertEqual(self.noms(quatre), ["Cinquante à As♣"])
        self.assertEqual(self.noms(cinq), ["Cent à Roi♣"])

    def test_carre_de_valets(self):
        main = [("Valet", c) for c in belote.COULEURS] + [("7", "Coeur")]
        a = trouver_annonces(main, "Pique")
        self.assertEqual([x["points"] for x in a], [200])

    def test_pas_dannonce(self):
        main = [("7", "Coeur"), ("9", "Coeur"), ("10", "Pique"), ("As", "Trefle")]
        self.assertEqual(trouver_annonces(main, "Pique"), [])

    def test_seule_la_meilleure_equipe_marque(self):
        tierce_a = [("7", "Coeur"), ("8", "Coeur"), ("9", "Coeur")]
        cinquante_b = [(v, "Trefle") for v in ("Valet", "Dame", "Roi", "As")]
        mains = [tierce_a, cinquante_b, [("7", "Pique")], [("8", "Pique")]]
        _, totaux = points_annonces(mains, "Pique")
        self.assertEqual(totaux, [0, 50])

    def test_atout_departage_deux_tierces(self):
        t1 = [("7", "Coeur"), ("8", "Coeur"), ("9", "Coeur")]
        t2 = [("7", "Pique"), ("8", "Pique"), ("9", "Pique")]
        _, totaux = points_annonces([t1, t2, [], []], "Pique")
        self.assertEqual(totaux, [0, 20])

    def test_annonces_dans_le_score(self):
        r = resultat(0, [100, 62], [5, 3], None, annonces=(50, 0))
        self.assertEqual(r["marque"], [150, 62])

    def test_chute_donne_les_annonces_a_la_defense(self):
        r = resultat(0, [60, 102], [3, 5], None, annonces=(20, 0))
        self.assertEqual(r["marque"], [0, 162 + 20])


class TestSimulation(unittest.TestCase):
    def test_donnes_automatiques(self):
        random.seed(42)
        joueurs = [Bot() for _ in range(4)]
        jouees = 0
        for i in range(300):
            res = jouer_donne(joueurs, i % 4, parler=lambda *_: None)
            if res is None:
                continue
            jouees += 1
            self.assertEqual(sum(res["cartes"]), belote.TOTAL_CARTES)
            self.assertEqual(sum(res["plis"]), 8)
        self.assertGreater(jouees, 100)


if __name__ == "__main__":
    unittest.main()
