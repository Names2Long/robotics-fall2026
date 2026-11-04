import unittest
from planning.core import inflate,reference_path,evaluate_student
from planning.teaching import search_trace,weighted_case,footprint_case,small_cases


class TeachingTests(unittest.TestCase):
    def test_reference_algorithms_and_frames(self):
        grid = [[1]*7,[1,0,0,0,0,0,1],[1]*7]
        for method in ('bfs','dfs','iddfs','astar','dijkstra'):
            result = search_trace(grid,(1,1),(1,5),method)
            self.assertEqual(result['status'],'succeeded')
            self.assertEqual(result['steps'],4)
            self.assertEqual(result['total_cost'],4)
            self.assertEqual(result['frames'][-1]['path'],result['path'])
            self.assertGreater(result['expanded'],0)
            self.assertTrue(any(f['frontier'] for f in result['frames']))

    def test_weighted_cost_is_not_distance(self):
        grid,costs,start,goal = weighted_case(5)
        results = {m:search_trace(grid,start,goal,m,costs) for m in ('bfs','dijkstra','astar')}
        self.assertLess(results['bfs']['steps'],results['dijkstra']['steps'])
        self.assertGreater(results['bfs']['total_cost'],results['dijkstra']['total_cost'])
        self.assertEqual(results['astar']['total_cost'],results['dijkstra']['total_cost'])
        self.assertEqual(results['astar']['total_cost'],10)

    def test_iddfs_failure_and_budget(self):
        case = small_cases()['Disconnected goal']
        bounded = search_trace(case['grid'],case['start'],case['goal'],'iddfs',budget=12)
        self.assertEqual(bounded['status'],'resource_limit')
        self.assertEqual(bounded['expanded'],12)
        grid = [[0,1,0]]
        self.assertEqual(search_trace(grid,(0,0),(0,2),'iddfs')['status'],'no_path')

    def test_cost_control_changes_the_route_at_explained_threshold(self):
        results = []
        for cost in (1,1.2,1.3,2):
            grid,costs,start,goal = weighted_case(cost)
            result = search_trace(grid,start,goal,'astar',costs)
            results.append(result)
            self.assertEqual(result['total_cost'],search_trace(grid,start,goal,'dijkstra',costs)['total_cost'])
        self.assertEqual([r['steps'] for r in results],[8,8,10,10])
        self.assertAlmostEqual(results[1]['total_cost'],9.4)

    def test_radius_closes_passage(self):
        grid,start,goal = footprint_case()
        self.assertTrue(reference_path(inflate(grid,0),start,goal))
        self.assertTrue(reference_path(inflate(grid,.18),start,goal))
        self.assertFalse(reference_path(inflate(grid,.30),start,goal))

    def test_small_cases_and_zero_move_validation(self):
        cases = small_cases()
        self.assertEqual(len(cases),6)
        for name in ('Occupied goal','Disconnected goal'):
            case = cases[name]
            self.assertFalse(reference_path(case['grid'],case['start'],case['goal']))
        result = evaluate_student(lambda ctx:[ctx.start],[[0]],(0,0),(0,0))
        self.assertEqual(result['status'],'succeeded')
        self.assertEqual(result['path_length_m'],0)
        self.assertEqual(result['optimality_ratio'],1)
        self.assertFalse(reference_path([[1]],(0,0),(0,0)))


if __name__=='__main__':
    unittest.main()
