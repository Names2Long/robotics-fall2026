import math
import unittest

from simulation.filters import median_filter, moving_average, fuse, error_metrics
from simulation.scenarios import fusion_dataset, run_pipeline, evaluate_rule, BASELINES, SAFETY_DISTANCE, verify_policy_result
from simulation.sensors import SensorConfig, sample_metrics, static_samples


class SimulationTests(unittest.TestCase):
    def test_worked_filter_and_fusion_outputs(self):
        values=[2.,2.1,8.,2.2,2.3]
        self.assertAlmostEqual(moving_average(values,3)[-1],12.5/3)
        self.assertEqual(median_filter(values,3)[-1],2.3)
        self.assertAlmostEqual(fuse([1.8],[2.4],.25)[0],2.25)

    def test_mad_uses_middle_pair_for_even_samples(self):
        import statistics
        for seed in (161,197):
            from simulation.sensors import profile_for_seed
            _,config=profile_for_seed(seed);samples=static_samples(2.,240,config,seed);values=[x for x in samples if x is not None]
            center=statistics.median(values);mad=statistics.median(abs(x-center) for x in values)
            expected=sum(abs(x-center)>max(.3,3*1.4826*mad) for x in values)
            self.assertEqual(sample_metrics(samples,2.)['outlier_count'],expected)

    def test_missing_and_empty_metrics_are_insufficient_not_crashes(self):
        for truth,estimate in (([],[]),([2.]*4,[None]*4)):
            result=error_metrics(truth,estimate,step_index=0)
            self.assertEqual(result['availability'],0);self.assertTrue(math.isinf(result['rmse']));self.assertTrue(math.isinf(result['response_delay']))

    def test_delay_requires_three_consecutive_samples(self):
        result=error_metrics([2.]*6,[1.,2.,1.,2.,2.,2.],dt=.05,step_index=0)
        self.assertAlmostEqual(result['response_delay'],.25)

    def test_invalid_filter_and_weight_settings_rejected(self):
        for operation in (lambda:moving_average([1.],0),lambda:fuse([1.],[2.],1.1),lambda:run_pipeline(fusion_dataset(2),'Median',3,.35,float('nan'))):
            with self.assertRaises(ValueError): operation()

    def test_policy_benchmarks_fixed_and_all_scenarios_recorded(self):
        for context in BASELINES:
            for threshold in (.55,1.25):
                result=evaluate_rule({**BASELINES[context],'threshold':threshold},context,2026)
                self.assertEqual(result['safety_distance'],SAFETY_DISTANCE[context]);self.assertEqual(len(result['traces']),7)
                self.assertTrue(all(len(rows)==80 for rows in result['traces'].values()));self.assertTrue(verify_policy_result(result)[0])
    def test_sensor_runs_are_repeatable(self):
        config = SensorConfig(noise_std=.1, dropout_rate=.1, outlier_rate=.1)
        self.assertEqual(static_samples(2.0, 40, config, 17), static_samples(2.0, 40, config, 17))

    def test_statistics_use_valid_samples(self):
        metrics = sample_metrics([1.0, None, 2.0, 3.0], 2.0)
        self.assertEqual(metrics["valid_count"], 3)
        self.assertEqual(metrics["dropout_count"], 1)
        self.assertAlmostEqual(metrics["mean"], 2.0)
        self.assertAlmostEqual(metrics["variance"], 1.0)

    def test_filters_handle_missing_values(self):
        self.assertEqual(moving_average([1.0, None, 3.0], 2), [1.0, 1.0, 2.0])
        self.assertEqual(median_filter([1.0, 9.0, 2.0], 3)[-1], 2.0)

    def test_pipeline_returns_finite_metrics(self):
        result = run_pipeline(fusion_dataset(42), "Median", 3, .35, .5)
        self.assertTrue(all(math.isfinite(value) for value in result["metrics"].values()))
        self.assertEqual(len(result["estimate"]), len(result["filtered_a"]))


if __name__ == "__main__": unittest.main()
