import math
from collections import defaultdict
from lab.models import RequirementResult,make_check
from missions.mission_1 import _close

REFLECTIONS=('comparison','responsiveness','fusion_choice')
LIMITS={'rmse':.18,'max_error':1.85,'response_delay':1.25,'availability':.99}
CALCULATIONS={'manual_average':(8.+2.2+2.3)/3,'manual_median':2.3,'manual_fusion':.25*1.8+.75*2.4}

def experiment_coverage(attempts):
    windows=defaultdict(set);weights=defaultdict(set);pairs=defaultdict(set);distinct=set()
    for item in attempts:
        s=item.get('settings',{})
        try:
            signature=(s['method'],s['window'],s['alpha'],s['weight_a']);distinct.add(signature)
            if s['method']=='Moving average': windows[s['weight_a']].add(s['window'])
            weights[(s['method'],s['window'],s['alpha'])].add(s['weight_a'])
            pairs[(s['window'],s['weight_a'])].add(s['method'])
        except KeyError: continue
    return {'distinct':len(distinct),'windows':max(map(len,windows.values()),default=0),'weights':max(map(len,weights.values()),default=0),
            'matched':any({'Moving average','Median'}.issubset(methods) for methods in pairs.values())}

def evaluate(attempts,selected_index,responses,*,data_valid=True):
    coverage=experiment_coverage(attempts)
    selected=attempts[selected_index] if isinstance(selected_index,int) and 0<=selected_index<len(attempts) else {}
    metrics=selected.get('metrics',{})
    requirements=[
        RequirementResult('data','Reproducible current experiment evidence',data_valid,data_valid,'current data and recomputed metrics'),
        RequirementResult('attempts','Record six distinct configurations',coverage['distinct']>=6,coverage['distinct'],'6 or more'),
        RequirementResult('windows','Compare three moving-average windows at one fixed fusion weight',coverage['windows']>=3,coverage['windows'],'3 different windows'),
        RequirementResult('methods','Compare median and moving average with matching window and fusion weight',coverage['matched'],coverage['matched'],'a matched pair'),
        RequirementResult('weights','Compare three fusion weights with otherwise identical settings',coverage['weights']>=3,coverage['weights'],'3 different weights'),
        RequirementResult('predictions','Preserve a prediction before every recorded configuration',bool(attempts) and all(len(str(a.get('prediction','')).strip())>=20 for a in attempts),sum(len(str(a.get('prediction','')).strip())>=20 for a in attempts),'a prediction of at least 20 characters for each record')]
    for key,expected in CALCULATIONS.items():
        requirements.append(RequirementResult(key,'Calculate '+key.replace('manual_','').replace('_',' '),_close(responses.get('mission_2.'+key),expected,.01),responses.get('mission_2.'+key,''),'within 0.01 m'))
    for key,limit in LIMITS.items():
        value=metrics.get(key)
        valid=isinstance(value,(int,float)) and math.isfinite(value)
        passed=valid and (value>=limit if key=='availability' else value<=limit)
        requirements.append(RequirementResult(key,'Selected '+key.replace('_',' '),passed,value,'≥ 99%' if key=='availability' else f'≤ {limit} '+('s' if key=='response_delay' else 'm')))
    for key in REFLECTIONS:
        text=str(responses.get('mission_2.'+key,'')).strip()
        requirements.append(RequirementResult(key,key.replace('_',' ').title(),len(text)>=100,len(text),'at least 100 characters using your recorded evidence'))
    return make_check('Mission 2 has calculated, predicted, controlled and defensible filtering/fusion evidence.',requirements)
