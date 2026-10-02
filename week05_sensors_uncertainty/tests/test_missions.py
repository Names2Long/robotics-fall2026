import copy,unittest
from fixtures import valid_state
from lab.completion import current_check
from missions import mission_2,mission_3
from simulation.scenarios import verify_policy_result

class MissionTests(unittest.TestCase):
    def test_complete_work_passes(self):
        st=valid_state()
        for mission in ('mission_1','mission_2','mission_3'): self.assertTrue(current_check(st,mission)[0].passed,mission)

    def test_empty_work_does_not_pass(self):
        self.assertFalse(mission_2.evaluate([],-1,{}).passed);self.assertFalse(mission_3.evaluate({},{}).passed)

    def test_controlled_experiments_and_calculations_required(self):
        st=valid_state();state=st.session_state
        for key in mission_2.CALCULATIONS:
            responses={**state['responses'],'mission_2.'+key:'wrong'}
            self.assertFalse(mission_2.evaluate(state['mission_2_attempts'],state['responses']['mission_2.selected'],responses).passed)
        for omitted in (0,1,2,4,5):
            attempts=[r for i,r in enumerate(state['mission_2_attempts']) if i!=omitted]
            self.assertFalse(mission_2.evaluate(attempts,0,state['responses']).passed)
        duplicate=[state['mission_2_attempts'][0]]*6
        self.assertFalse(mission_2.evaluate(duplicate,0,state['responses']).passed)

    def test_forged_metrics_and_pass_flags_rejected(self):
        st=valid_state();st.session_state['mission_2_attempts'][0]['metrics']['rmse']=0
        self.assertFalse(current_check(st,'mission_2')[0].passed)
        result=copy.deepcopy(valid_state().session_state['mission_3_results']['Warehouse'])
        result['traces'].pop('dropout_burst');result['passed']=True
        self.assertFalse(verify_policy_result(result)[0])
        self.assertFalse(mission_3.evaluate({'Warehouse':{'passed':True},'Assistive':{'passed':True}},{}).passed)

    def test_policy_revision_prediction_and_current_settings_required(self):
        st=valid_state();st.session_state['mission_3_controls']['Warehouse']['missing_policy']='Move'
        self.assertFalse(current_check(st,'mission_3')[0].passed)
        st=valid_state();st.session_state['mission_3_attempts']['Warehouse']=st.session_state['mission_3_attempts']['Warehouse'][:1]
        self.assertFalse(current_check(st,'mission_3')[0].passed)
        st=valid_state();st.session_state['mission_3_attempts']['Assistive'][0]['prediction']=''
        self.assertFalse(current_check(st,'mission_3')[0].passed)

if __name__=='__main__': unittest.main()
