import hashlib
from lab.autosave import CONTENT_VERSION,read_json,submission_root
from lab.evidence import evidence_id,student_seed
from lab.session import complete_mission
from missions import mission_1,mission_2,mission_3
from simulation.sensors import profile_for_seed,static_samples,sample_metrics
from simulation.scenarios import fusion_dataset,run_pipeline

def current_check(st,mission):
    responses=st.session_state['responses'];course_id=st.session_state['student']['course_id']
    answers={k:v for k,v in responses.items() if k.startswith(mission+'.') and not k.endswith('.prediction_draft')}
    if mission=='mission_1':
        seed=student_seed(course_id,mission);name,config=profile_for_seed(seed)
        metrics=sample_metrics(static_samples(2.,240,config,seed),2.)
        check=mission_1.evaluate(metrics,name,responses);evidence={'seed':seed,'metrics':metrics,'profile':name}
    elif mission=='mission_2':
        attempts=st.session_state['mission_2_attempts'];data=fusion_dataset(student_seed(course_id,mission));valid=True
        for record in attempts:
            try:
                s=record['settings'];actual=run_pipeline(data,s['method'],s['window'],s['alpha'],s['weight_a'])
                valid=valid and all(record.get(k)==actual[k] for k in ('settings','metrics','estimate','data_version'))
            except (KeyError,TypeError,ValueError): valid=False
        selected=responses.get('mission_2.selected',0)
        check=mission_2.evaluate(attempts,selected,responses,data_valid=valid)
        evidence={'selected_attempt':selected+1 if isinstance(selected,int) else None,'attempts':attempts}
    else:
        evidence={'context_results':st.session_state['mission_3_results'],'attempts':st.session_state['mission_3_attempts'],'controls':st.session_state['mission_3_controls']}
        check=mission_3.evaluate(evidence['context_results'],responses,evidence['attempts'],evidence['controls'],course_id)
    signature=evidence_id(CONTENT_VERSION,course_id,evidence,answers)
    return check,signature,evidence

def saved_matches(mission,signature,evidence):
    try:
        root=submission_root()/mission;payload=read_json(root/'submission.json')
        artifacts=payload.get('artifact_hashes',{})
        required={'explanation.md','measurements.csv'}|({'evidence.png'} if mission!='mission_3' else set())
        return payload.get('state_signature')==signature and payload.get('evidence')==evidence and required.issubset(artifacts) and all((root/path).is_file() and hashlib.sha256((root/path).read_bytes()).hexdigest()==digest for path,digest in artifacts.items())
    except (OSError,ValueError,TypeError): return False

def mission_status(st):
    result={}
    for mission in ('mission_1','mission_2','mission_3'):
        check,signature,evidence=current_check(st,mission)
        result[mission]=bool(check.passed and st.session_state['checked_evidence_ids'].get(mission)==signature and saved_matches(mission,signature,evidence))
    return result

def refresh_completion(st):
    status=mission_status(st)
    st.session_state['completed_missions']=[m for m,valid in status.items() if valid]
    return status
