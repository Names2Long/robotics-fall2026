import unittest
from planning.core import PLANNERS,make_map,inflate,fingerprint,EXPERIMENT_VERSION
from planning.social import CONFIGS
from evaluation.experiments import navigation_checks,social_checks


class CheckTests(unittest.TestCase):
    def test_navigation_requires_two_maps_current_source_and_common_controller(self):
        rows = [dict(experiment_version=EXPERIMENT_VERSION,map=m,planner=p,status='succeeded',map_hash=fingerprint(inflate(make_map(m))),
                     source_sha256='source' if p in PLANNERS[:4] else None,controller_hash='common',trajectory=[{'x':0,'y':0,'t':0}])
                for m in ('open','constrained') for p in PLANNERS]
        self.assertTrue(all(ok for _,ok in navigation_checks(rows,'source')))
        self.assertFalse(all(ok for _,ok in navigation_checks(rows,'changed')))
        rows[0]['controller_hash'] = 'other'
        self.assertFalse(all(ok for _,ok in navigation_checks(rows,'source')))
        rows[0]['controller_hash'] = 'common'
        rows[0]['status'] = 'environment_error'
        self.assertFalse(all(ok for _,ok in navigation_checks(rows,'source')))

    def test_social_requires_distinct_paired_settings_not_perfect_success(self):
        rows = []
        for planner in ('astar','rrt'):
            for condition in CONFIGS:
                rows.append(dict(experiment_version=EXPERIMENT_VERSION,planner=planner,map='open',seed=0,map_hash='map',source_sha256='source',
                    controller_hash='common',condition=condition,field_hash=fingerprint(CONFIGS[condition]),
                    status='succeeded' if condition=='baseline' else 'field_oscillation',
                    trajectory=[{'x':0,'y':0,'t':0}] if condition=='baseline' else []))
        self.assertTrue(all(ok for _,ok in social_checks(rows)))
        rows[-1]['seed'] = 2
        self.assertFalse(all(ok for _,ok in social_checks(rows)))


if __name__=='__main__':
    unittest.main()
