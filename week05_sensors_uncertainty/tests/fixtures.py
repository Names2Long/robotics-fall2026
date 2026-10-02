from types import SimpleNamespace
from lab.session import initialize
from lab.evidence import student_seed
from missions import mission_1,mission_2,mission_3
from simulation.sensors import profile_for_seed,static_samples,sample_metrics
from simulation.scenarios import fusion_dataset,run_pipeline,evaluate_rule,BASELINES

EXPLANATION='My evidence-based explanation compares numerical error, response delay, settings, stakeholders and limitations. '*3
PREDICTION='I predict these settings will change smoothing, accuracy and the delay before a safe decision.'

def valid_state(course_id='audit-student'):
    st=SimpleNamespace(session_state={});initialize(st);state=st.session_state
    state['student']={'name':'Test Student','email':'test@example.test','course_id':course_id};state['identity_locked']=True
    state['reviewed_walkthroughs']=[0,1,2,3];state['visited_stages']=['intro','concepts','mission_1','mission_2','mission_3','final'];state['stage']='final'
    responses=state['responses'];seed=student_seed(course_id,'mission_1');name,config=profile_for_seed(seed)
    metrics=sample_metrics(static_samples(2.,240,config,seed),2.)
    for key,field in [('mean','mean'),('variance','variance'),('bias','bias'),('median','median'),('dropouts','dropout_count'),('outliers','outlier_count')]: responses['mission_1.'+key]=str(metrics[field])
    responses.update({'mission_1.profile':name,'mission_1.prediction':PREDICTION})
    for mission,keys in [('mission_1',mission_1.REFLECTIONS),('mission_2',mission_2.REFLECTIONS),('mission_3',mission_3.REFLECTIONS)]:
        responses.update({mission+'.'+k:EXPLANATION for k in keys})
    responses.update({'mission_2.'+k:str(v) for k,v in mission_2.CALCULATIONS.items()})
    data=fusion_dataset(student_seed(course_id,'mission_2'));attempts=[]
    configs=[('Moving average',w,.25) for w in (3,7,11)]+[('Median',3,w) for w in (.25,.5,.75)]
    for method,window,weight in configs:
        attempts.append({'attempt':len(attempts)+1,'prediction':PREDICTION,**run_pipeline(data,method,window,.35,weight)})
    selected=next((i for i in range(len(attempts)) if mission_2.evaluate(attempts,i,responses).passed),None)
    if selected is None:
        for window in (1,3,5,7):
            for weight in (0.,.1,.2,.3,.4,.5):
                record={'attempt':len(attempts)+1,'prediction':PREDICTION,**run_pipeline(data,'Median',window,.35,weight)}
                if mission_2.evaluate([*attempts,record],len(attempts),responses).passed:
                    selected=len(attempts);attempts.append(record);break
            if selected is not None: break
    assert selected is not None
    state['mission_2_attempts']=attempts;responses['mission_2.selected']=selected
    state['mission_2_controls']=dict(attempts[selected]['settings'])
    for context,baseline in BASELINES.items():
        seed=student_seed(course_id,'mission_3_'+context.lower());first=evaluate_rule(baseline,context,seed);first['prediction']=PREDICTION
        candidates=[{**baseline,'margin':baseline['margin']+.05},{**baseline,'margin':baseline['margin']+.1},*[{**baseline,'weight_a':w} for w in (.25,.15,.45)]]
        last=next(evaluate_rule(s,context,seed) for s in candidates if evaluate_rule(s,context,seed)['passed'])
        last['prediction']=PREDICTION;state['mission_3_attempts'][context]=[first,last];state['mission_3_results'][context]=last;state['mission_3_controls'][context]=dict(last['settings'])
    responses['final.synthesis']='Measurement filtering evidence context uncertainty '*40
    responses['final.course_reflection']='This activity connected my interests in robotics with responsibility for checking uncertain measurements.'
    return st
