import random
import unittest

import belote
from belote import Bot, cartes_jouables, gagnant_pli, jouer_donne, points, resultat


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
