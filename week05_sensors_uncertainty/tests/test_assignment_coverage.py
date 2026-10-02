import unittest
from fixtures import valid_state
from lab.completion import current_check

class AssignmentCoverageTests(unittest.TestCase):
    def test_one_hundred_assigned_datasets_have_passing_routes(self):
        for index in range(100):
            with self.subTest(course_id='sweep-'+str(index)):
                state=valid_state('sweep-'+str(index))
                for mission in ('mission_1','mission_2','mission_3'):
                    self.assertTrue(current_check(state,mission)[0].passed)

if __name__=='__main__': unittest.main()
