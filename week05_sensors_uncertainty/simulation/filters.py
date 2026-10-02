from __future__ import annotations
import math
from statistics import median

def _values(values):
    if any(v is not None and not math.isfinite(float(v)) for v in values): raise ValueError('Measurements must be finite or missing (None)')

def hold_last(values):
    _values(values);output=[];last=None
    for v in values:
        if v is not None: last=float(v)
        output.append(last)
    return output

def moving_average(values,window):
    _values(values)
    if not isinstance(window,int) or window<1: raise ValueError('Window must be a positive integer')
    output=[];recent=[]
    for v in values:
        if v is not None: recent.append(float(v));recent=recent[-window:]
        output.append(sum(recent)/len(recent) if recent else None)
    return output

def median_filter(values,window):
    _values(values)
    if not isinstance(window,int) or window<1: raise ValueError('Window must be a positive integer')
    output=[];recent=[]
    for v in values:
        if v is not None: recent.append(float(v));recent=recent[-window:]
        output.append(median(recent) if recent else None)
    return output

def exponential(values,alpha):
    _values(values)
    if not math.isfinite(alpha) or not 0<alpha<=1: raise ValueError('Alpha must be in (0, 1]')
    output=[];state=None
    for v in values:
        if v is not None: state=float(v) if state is None else alpha*float(v)+(1-alpha)*state
        output.append(state)
    return output

def apply_filter(values,method,window=5,alpha=.35):
    if method=='Raw/hold last': return hold_last(values)
    if method=='Moving average': return moving_average(values,window)
    if method=='Median': return median_filter(values,window)
    if method=='Exponential': return exponential(values,alpha)
    raise ValueError('Unknown filter: '+str(method))

def fuse(a,b,weight_a):
    if not math.isfinite(weight_a) or not 0<=weight_a<=1: raise ValueError('Weight must be in [0, 1]')
    if len(a)!=len(b): raise ValueError('Sensor sequences must have equal lengths')
    return [bv if av is None else av if bv is None else weight_a*av+(1-weight_a)*bv for av,bv in zip(a,b)]

def error_metrics(truth,estimate,dt=.05,step_index=120):
    if len(truth)!=len(estimate): raise ValueError('Truth and estimate must have equal lengths')
    _values(estimate)
    if dt<=0: raise ValueError('Time step must be positive')
    pairs=[(t,e) for t,e in zip(truth,estimate) if e is not None]
    errors=[abs(t-e) for t,e in pairs]
    delay=math.inf
    if truth and 0<=step_index<len(truth):
        target=truth[step_index];streak=0
        for i in range(step_index,len(estimate)):
            streak=streak+1 if estimate[i] is not None and abs(estimate[i]-target)<=.15 else 0
            if streak>=3: delay=(i-step_index)*dt;break
    return {'rmse':math.sqrt(sum((t-e)**2 for t,e in pairs)/len(pairs)) if pairs else math.inf,
            'mae':sum(errors)/len(errors) if errors else math.inf,'max_error':max(errors) if errors else math.inf,
            'response_delay':delay,'availability':len(pairs)/len(truth) if truth else 0.}
