from __future__ import annotations
import math, random
from simulation.filters import apply_filter,fuse,error_metrics
from simulation.sensors import SensorConfig,measure

DT=.05
DATA_VERSION=2
METHODS=('Raw/hold last','Moving average','Median','Exponential')
SAFETY_DISTANCE={'Warehouse':.75,'Assistive':.95}
BASELINES={context:{'threshold':distance,'margin':.10 if context=='Warehouse' else .20,'weight_a':.35,'filter_method':'Median','window':3,'confirmations':1,'missing_policy':'Stop'} for context,distance in SAFETY_DISTANCE.items()}

def dynamic_truth(count=400):
    return [2.8 if i*DT<6 else 1.15 if i*DT<10 else 1.15+.22*(i*DT-10) if i*DT<15 else 2.25+.08*(i*DT-15) for i in range(count)]

def fusion_dataset(seed):
    truth=dynamic_truth();ra=random.Random(seed);rb=random.Random(seed+991)
    ac=SensorConfig(noise_std=.18,resolution=.01,dropout_rate=.025,outlier_rate=.07,outlier_scale=1.2)
    bc=SensorConfig(noise_std=.07,bias=.06,resolution=.02,dropout_rate=.03,outlier_rate=.01,update_stride=4)
    return {'time':[i*DT for i in range(len(truth))],'truth':truth,
            'sensor_a':[measure(v,ac,ra,i) for i,v in enumerate(truth)],'sensor_b':[measure(v,bc,rb,i) for i,v in enumerate(truth)]}

def pipeline_settings(method,window,alpha,weight_a):
    if method not in METHODS: raise ValueError('Unknown filter')
    if not isinstance(window,int) or not 1<=window<=15: raise ValueError('Window must be an integer in [1, 15]')
    if not math.isfinite(weight_a) or not 0<=weight_a<=1: raise ValueError('Weight must be in [0, 1]')
    if method=='Exponential' and (not math.isfinite(alpha) or not .05<=alpha<=1): raise ValueError('Alpha must be in [0.05, 1]')
    return {'method':method,'window':window if method in ('Moving average','Median') else 1,'alpha':alpha if method=='Exponential' else .35,'weight_a':weight_a}

def run_pipeline(dataset,method,window,alpha,weight_a):
    settings=pipeline_settings(method,window,alpha,weight_a)
    a=apply_filter(dataset['sensor_a'],method,settings['window'],settings['alpha']);b=apply_filter(dataset['sensor_b'],'Exponential',5,.35)
    estimate=fuse(a,b,weight_a)
    return {'estimate':estimate,'filtered_a':a,'filtered_b':b,'metrics':error_metrics(dataset['truth'],estimate,DT,120),'settings':settings,'data_version':DATA_VERSION}

DECISION_SCENARIOS={
    'clearly_safe':[2.5]*80,'stationary_danger':[.55]*80,
    'near_threshold':[.92+.05*((i%10)-5)/5 for i in range(80)],
    'fast_approach':[max(.35,2.8-.04*i) for i in range(80)],
    'receding':[.55+.025*i for i in range(80)],'conflicting_sensors':[1.]*80,
    'dropout_burst':[1.4 if i<35 else .65 for i in range(80)]}

def _decision_measurements(name,truth,seed):
    ra=random.Random(seed);rb=random.Random(seed+7)
    ac=SensorConfig(noise_std=.12,resolution=.01,dropout_rate=.03,outlier_rate=.05,outlier_scale=.9)
    bc=SensorConfig(noise_std=.06,bias=.04,resolution=.02,dropout_rate=.04,update_stride=3)
    a=[];b=[]
    for i,v in enumerate(truth):
        av=measure(v,ac,ra,i);bv=measure(v,bc,rb,i)
        if name=='conflicting_sensors': av=v-.32 if i>15 else av;bv=v+.28 if i>15 and i%3==0 else bv
        if name=='dropout_burst' and 30<=i<=50: av=bv=None
        a.append(av);b.append(bv)
    return a,b

def validate_policy(settings):
    numeric={'threshold':(.55,1.25),'margin':(0,.45),'weight_a':(0,1)}
    for key,(low,high) in numeric.items():
        value=float(settings[key])
        if not math.isfinite(value) or not low<=value<=high: raise ValueError('Invalid '+key)
    if settings['filter_method'] not in METHODS or settings['missing_policy'] not in ('Stop','Insufficient evidence','Move'): raise ValueError('Invalid policy option')
    if not isinstance(settings['window'],int) or not 1<=settings['window']<=11: raise ValueError('Invalid policy window')
    if not isinstance(settings['confirmations'],int) or not 1<=settings['confirmations']<=4: raise ValueError('Invalid confirmation count')

def canonical_policy(settings):
    result=dict(settings)
    if result.get('filter_method') in ('Raw/hold last','Exponential'): result['window']=1
    return result

def evaluate_rule(settings,context,seed):
    settings=canonical_policy(settings)
    validate_policy(settings)
    if context not in SAFETY_DISTANCE: raise ValueError('Unknown context')
    safety=SAFETY_DISTANCE[context];threshold=settings['threshold'];margin=settings['margin']
    traces={};scenario_rows=[];total_unsafe=false_safe=unnecessary_stop=clear_count=dangerous=0;delays=[]
    for offset,(name,truth) in enumerate(DECISION_SCENARIOS.items()):
        a,b=_decision_measurements(name,truth,seed+offset*101)
        af=apply_filter(a,settings['filter_method'],settings['window'],.35);bf=apply_filter(b,'Exponential',5,.35)
        estimate=fuse(af,bf,settings['weight_a']);streak=0;rows=[]
        for i,(actual,est,av,bv) in enumerate(zip(truth,estimate,a,b)):
            if av is None and bv is None:
                decision={'Stop':'STOP','Insufficient evidence':'INSUFFICIENT','Move':'MOVE'}[settings['missing_policy']];reason='Both current readings missing';streak=0
            elif est is None: decision='STOP';reason='No estimate';streak=0
            elif est<=threshold+margin:
                streak+=1;decision='STOP' if streak>=settings['confirmations'] else 'SLOW';reason='At/below stop boundary; confirmation count '+str(streak)
            elif est<=threshold+margin+.35: streak=0;decision='SLOW';reason='Inside caution band'
            else: streak=0;decision='MOVE';reason='Outside caution band'
            unsafe=actual<=safety;clear=actual>=safety+.65
            fs=unsafe and decision=='MOVE';us=clear and decision=='STOP';dc=actual<=.45 and decision in ('MOVE','SLOW')
            total_unsafe+=unsafe;clear_count+=clear;false_safe+=fs;unnecessary_stop+=us;dangerous+=dc
            rows.append({'time_s':i*DT,'truth_m':actual,'sensor_a_m':av,'sensor_b_m':bv,'filtered_a_m':af[i],'filtered_b_m':bf[i],'estimate_m':est,'decision':decision,'reason':reason,'false_safe':bool(fs),'unnecessary_stop':bool(us),'dangerous_command':bool(dc)})
        episode_delays=[]
        for i,v in enumerate(truth):
            if v<=safety and (i==0 or truth[i-1]>safety):
                end=next((j for j in range(i+1,len(truth)) if truth[j]>safety),len(truth))
                stop=next((j for j in range(i,end) if rows[j]['decision'] in ('STOP','INSUFFICIENT')),None)
                episode_delays.append((stop-i)*DT if stop is not None else math.inf)
        delays.extend(episode_delays);traces[name]=rows
        scenario_rows.append({'scenario':name,'false_safe':sum(r['false_safe'] for r in rows),'unnecessary_stop':sum(r['unnecessary_stop'] for r in rows),'dangerous_command_events':sum(r['dangerous_command'] for r in rows),'maximum_detection_delay':max(episode_delays,default=0.),'final_decision':rows[-1]['decision']})
    metrics={'false_safe_rate':false_safe/max(1,total_unsafe),'unnecessary_stop_rate':unnecessary_stop/max(1,clear_count),'maximum_detection_delay':max(delays,default=0.),'dangerous_command_events':dangerous}
    criteria={'false_safe_limit':.05 if context=='Warehouse' else .01,'unnecessary_stop_limit':.35 if context=='Warehouse' else .45,'delay_limit':.55 if context=='Warehouse' else .35}
    passed=metrics['false_safe_rate']<=criteria['false_safe_limit'] and metrics['unnecessary_stop_rate']<=criteria['unnecessary_stop_limit'] and metrics['maximum_detection_delay']<=criteria['delay_limit'] and dangerous==0 and settings['missing_policy']!='Move'
    return {'context':context,'seed':seed,'data_version':DATA_VERSION,'settings':dict(settings),'safety_distance':safety,'metrics':metrics,'criteria':criteria,'scenarios':scenario_rows,'traces':traces,'passed':passed}

def verify_policy_result(result):
    try:
        expected=evaluate_rule(result['settings'],result['context'],result['seed'])
        return all(result.get(key)==expected[key] for key in expected),expected
    except (KeyError,TypeError,ValueError): return False,{}
