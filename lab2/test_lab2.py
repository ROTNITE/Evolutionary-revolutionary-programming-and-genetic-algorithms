import unittest
import numpy as np
from main import (Config,create_problem,feasible,violation,repair,greedy,raw_value,
                  run_ga,run_random,mutate,crossover)

class TestLab2(unittest.TestCase):
    def setUp(self):self.p=create_problem()
    def test_deterministic_problem(self):
        p2=create_problem()
        self.assertTrue(np.array_equal(self.p.value,p2.value))
        self.assertEqual(self.p.conflicts,p2.conflicts)
        self.assertEqual(self.p.n,40)
    def test_valid_mandatory_instance(self):
        self.assertEqual(len(self.p.mandatory),3)
        self.assertTrue(feasible(repair(np.zeros(40,dtype=bool),self.p),self.p))
    def test_repair_all_ones(self):
        self.assertTrue(feasible(repair(np.ones(40,dtype=bool),self.p),self.p))
    def test_repair_idempotent(self):
        x=repair(np.random.default_rng(4).random(40)<.5,self.p)
        self.assertTrue(np.array_equal(x,repair(x,self.p)))
    def test_repair_never_exceeds_capacity(self):
        rng=np.random.default_rng(2)
        for _ in range(250):
            self.assertEqual(violation(repair(rng.random(40)<.5,self.p),self.p),(0,0,0))
    def test_greedy_feasible(self):self.assertTrue(feasible(greedy(self.p),self.p))
    def test_budget_repair(self):
        cfg=Config(population=20,generations=15,elite=2)
        r=run_ga(self.p,7,'repair','bitflip',cfg)
        self.assertEqual(r['evaluations'],cfg.budget)
        self.assertEqual(r['feasible_rate'],1.)
    def test_budget_penalty(self):
        cfg=Config(population=20,generations=15,elite=2)
        r=run_ga(self.p,7,'penalty','bitflip',cfg)
        self.assertEqual(r['evaluations'],cfg.budget)
        if r['best'] is not None:
            z=np.zeros(40,dtype=bool);z[r['solution']]=True
            self.assertTrue(feasible(z,self.p))
    def test_budget_random(self):
        cfg=Config(population=20,generations=15,elite=2)
        r=run_random(self.p,7,cfg)
        self.assertEqual(r['evaluations'],cfg.budget)
    def test_reproducibility(self):
        cfg=Config(population=20,generations=15,elite=2)
        for constraint in ['repair','penalty']:
            a=run_ga(self.p,31,constraint,'bitflip',cfg)
            b=run_ga(self.p,31,constraint,'bitflip',cfg)
            self.assertEqual(a['best'],b['best'])
            self.assertEqual(a['solution'],b['solution'])
            self.assertEqual(a['trajectory'],b['trajectory'])
    def test_binary_operators(self):
        rng=np.random.default_rng(55)
        a=np.ones(40,dtype=bool);b=np.zeros(40,dtype=bool)
        x,y=crossover(a,b,rng,1.)
        self.assertTrue(np.array_equal(x,~y))
        y=mutate(a,rng,'bitflip',1.)
        self.assertTrue(np.array_equal(y,b))
    def test_conflicts_detected(self):
        x=np.ones(40,dtype=bool)
        self.assertGreater(violation(x,self.p)[1],0)

if __name__=='__main__':unittest.main()
