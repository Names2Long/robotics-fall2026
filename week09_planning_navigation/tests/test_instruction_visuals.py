import io
import math
import unittest
import matplotlib.pyplot as plt
from lab.planning_visuals import context_example,context_handoff_figure,context_example_figure,force_figure
from planning.core import free,reference_path,fingerprint
from planning.experiments import cases
from planning.social import field_forces,CONFIGS,PEOPLE
from planning.teaching import search_trace
from evaluation.experiments import offline_checks


class InstructionTests(unittest.TestCase):
    def test_context_example_matches_real_interface(self):
        ctx,current,adjacent = context_example()
        self.assertEqual(current,(2,2))
        self.assertEqual(adjacent,[(3,2),(2,1),(1,2)])
        self.assertEqual(ctx.expanded,1)
        self.assertEqual(ctx.peak_frontier,5)
        self.assertEqual(ctx.heuristic(current),3)
        self.assertGreater(len(reference_path(ctx.grid,current,ctx.goal))-1,3)

    def test_disconnected_case_exhausts_without_resource_limit(self):
        grid,start,goal = cases()['unreachable']
        self.assertTrue(free(grid,start))
        self.assertTrue(free(grid,goal))
        self.assertFalse(reference_path(grid,start,goal))
        self.assertTrue(all(row[4] for row in grid))
        for method in ('bfs','dfs','iddfs','astar'):
            result = search_trace(grid,start,goal,method,budget=2500)
            self.assertEqual(result['status'],'no_path',msg=method)
            self.assertLess(result['expanded'],2500)

    def test_old_unreachable_map_is_rejected(self):
        rows = [dict(map=name,map_hash=fingerprint(grid)) for name,(grid,_,_) in cases().items()]
        self.assertTrue(dict(offline_checks({'rows':rows}))['Results use the current test maps'])
        rows[-1]['map_hash'] = 'old-map'
        self.assertFalse(dict(offline_checks({'rows':rows}))['Results use the current test maps'])

    def test_force_vectors_use_the_same_math_as_refinement(self):
        pos,waypoint = (-.8,-1.05),(1.2,-1.05)
        vectors = field_forces(pos,waypoint,PEOPLE,CONFIGS['social_1'])
        self.assertEqual(vectors['attraction'],(1.0,0.0))
        self.assertLess(vectors['repulsion'][0],0)
        self.assertGreater(vectors['repulsion'][1],0)
        for i in (0,1):
            self.assertAlmostEqual(vectors['resultant'][i],vectors['attraction'][i]+vectors['repulsion'][i])
        outside = field_forces((-4,0),(1,0),PEOPLE,CONFIGS['social_1'])
        self.assertEqual(outside['repulsion'],(0,0))
        zero_gain = field_forces(pos,waypoint,PEOPLE,CONFIGS['baseline'])
        self.assertEqual(zero_gain['repulsion'],(0,0))

    def test_figures_render(self):
        for fig in (context_handoff_figure(),context_example_figure(),force_figure(CONFIGS)):
            with io.BytesIO() as output:
                fig.savefig(output,format='png',dpi=100)
                self.assertGreater(output.tell(),5000)
            plt.close(fig)


if __name__=='__main__':
    unittest.main()
