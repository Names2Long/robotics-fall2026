from lab.models import RequirementResult,make_check
from lab.evidence import student_seed
from simulation.scenarios import verify_policy_result,BASELINES

REFLECTIONS=('error_costs','context_comparison','limitations')

def evaluate(results,responses,histories=None,current_settings=None,course_id=None):
    histories=histories or {};current_settings=current_settings or {};requirements=[]
    for context in ('Warehouse','Assistive'):
        result=results.get(context,{})
        valid,computed=verify_policy_result(result)
        valid=valid and result.get('context')==context
        if course_id is not None:
            valid=valid and result.get('seed')==student_seed(course_id,'mission_3_'+context.lower())
        records=histories.get(context,[])
        unique={tuple(sorted(r.get('settings',{}).items())) for r in records}
        history_valid=bool(records) and all(r.get('context')==context and verify_policy_result(r)[0] and len(str(r.get('prediction','')).strip())>=20 for r in records)
        history_valid=history_valid and any(r.get('settings')==BASELINES[context] for r in records) and result in records
        if course_id is not None:
            history_valid=history_valid and all(r.get('seed')==student_seed(course_id,'mission_3_'+context.lower()) for r in records)
        fresh=result.get('settings')==current_settings.get(context)
        requirements.extend([
            RequirementResult(context+'.evidence',context+' reproducible seven-scenario evidence',valid,valid,'all seven complete scenario traces, independently verified'),
            RequirementResult(context+'.history',context+' predicted baseline and revised policy',history_valid and len(unique)>=2,len(unique),'at least 2 distinct tested policies with saved predictions'),
            RequirementResult(context+'.fresh',context+' test matches current controls',fresh,fresh,'retest after changing any control'),
            RequirementResult(context+'.pass',context+' quantitative policy criteria',valid and computed.get('passed',False),computed.get('metrics','not tested'),'meet every fixed-context criterion')])
    warehouse=results.get('Warehouse',{}).get('settings',{});assistive=results.get('Assistive',{}).get('settings',{})
    differences=sum(warehouse.get(k)!=assistive.get(k) for k in set(warehouse)|set(assistive)) if warehouse and assistive else 0
    requirements.append(RequirementResult('context_specific','Policies are context-specific',differences>=2,differences,'at least 2 parameter differences, justified using metrics'))
    for key in REFLECTIONS:
        text=str(responses.get('mission_3.'+key,'')).strip()
        requirements.append(RequirementResult(key,key.replace('_',' ').title(),len(text)>=120,len(text),'at least 120 characters citing your evidence'))
    return make_check('Mission 3 demonstrates tested, current, context-sensitive decisions.',requirements)
