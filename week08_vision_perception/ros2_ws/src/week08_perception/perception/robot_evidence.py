"""Portable recorded camera attempts, including interrupted and unsuccessful runs."""
import base64
import csv
import io
import math
import cv2
import numpy as np
from perception.vision_control import VisionSettings, VERSION


def validate_report(report, kind):
    if not isinstance(report,dict) or report.get('schema') != VERSION or report.get('kind') != kind:
        raise ValueError('Record a current live-camera attempt for this mission')
    config = VisionSettings(**report['config'])
    if report.get('program'):
        from dataclasses import asdict
        from perception.line_program import load_program
        executed_config,_ = load_program(report['program'])
        if kind != 'line_following' or asdict(executed_config) != report['config']:
            raise ValueError('Recorded program and settings do not match')
    if config.kind != kind: raise ValueError('Settings do not match the mission')
    if report.get('world') not in (('pillars',) if kind == 'pillar_search' else ('practice','track')):
        raise ValueError('Wrong world for this mission')
    if report.get('outcome') not in ('complete','interrupted','timeout'):
        raise ValueError('Stop the controller with Ctrl+C before importing this attempt')
    rows = report.get('rows',[])
    if not rows or not any(r.get('frame',0)>0 for r in rows): raise ValueError('No live camera frames were recorded')
    for row in rows:
        if not all(isinstance(row.get(k),(int,float)) and math.isfinite(row[k]) for k in ('elapsed','linear','angular')):
            raise ValueError('Invalid recorded command or time')
        if abs(row['linear']) > .180001 or abs(row['angular']) > .600001: raise ValueError('A recorded command exceeds the lab limits')
    for name, text in report.get('images',{}).items():
        if name not in ('original','mask','annotated'): raise ValueError('Unexpected evidence image')
        data = base64.b64decode(text,validate=True)
        if cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_UNCHANGED) is None: raise ValueError('Unreadable evidence image')
    if not report.get('images'): raise ValueError('No diagnostic camera images saved')
    errors = [abs(r['error']) for r in rows if r.get('valid') and isinstance(r.get('error'),(float,int)) and math.isfinite(r['error'])]
    losses = sum(r.get('state') == 'LINE_LOST' and (i == 0 or rows[i-1].get('state') != 'LINE_LOST') for i,r in enumerate(rows))
    return {'outcome':report['outcome'], 'world':report['world'], 'recorded_steps':len(rows),
            'elapsed_sim_seconds':round(max(r['elapsed'] for r in rows),2),
            'mean_absolute_image_error_when_visible':sum(errors)/len(errors) if errors else None,
            'line_loss_events':losses, 'visited_colors':report.get('visited',[]),
            'camera_wait_steps':sum(r.get('state') == 'WAIT_CAMERA' for r in rows)}


def artifacts(report):
    validate_report(report,report['kind'])
    buffer = io.StringIO()
    columns = ('elapsed','frame','capture_stamp','state','target','valid','error','fraction','red_fraction','linear','angular','odom_x','odom_y')
    writer = csv.DictWriter(buffer,fieldnames=columns,extrasaction='ignore')
    writer.writeheader()
    writer.writerows(report['rows'])
    yield 'camera_timeline.csv',buffer.getvalue().encode()
    for name,text in report['images'].items(): yield 'images/'+name+'.png',base64.b64decode(text,validate=True)
    if report.get('program'): yield 'controller.py',report['program'].encode('utf-8')


def validate_bundle(evidence, kind):
    if not isinstance(evidence,dict) or evidence.get('kind') != kind:
        raise ValueError('Import recorded robot attempts on the mission page')
    reports = evidence.get('reports',[])
    if not reports: raise ValueError('Import at least one recorded attempt')
    summaries = [validate_report(report,kind) for report in reports]
    if kind == 'line_following' and not {'practice','track'}.issubset({r['world'] for r in reports}):
        raise ValueError('Import an attempt from both practice and track worlds')
    if kind == 'line_following' and any(r.get('program') for r in reports):
        import ast
        programs = {ast.dump(ast.parse(r['program']),include_attributes=False) for r in reports if r['world']=='track' and r.get('program')}
        if len(programs)<2: raise ValueError('Keep two track attempts with different Python settings or steering expressions')
    if kind == 'pillar_search' and not any(set(r['config']['colors'].split(',')) == {'red','green','turquoise','blue'} for r in reports):
        raise ValueError('Include an attempt requesting all four pillar colors')
    return summaries
