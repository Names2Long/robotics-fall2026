import csv,hashlib,io,json,zipfile
from datetime import datetime,timezone
from lab.autosave import submission_root,_atomic,write_json,read_json,save
from lab_config import LAB
from lab.evidence import evidence_id
from simulation.plotting import png_bytes

def save_mission(mission_id,evidence,responses,*,state_signature,rows=None,figure=None):
    root=submission_root()/mission_id;root.mkdir(parents=True,exist_ok=True)
    lines=['# '+mission_id.replace('_',' ').title(),'']
    for k,v in sorted(responses.items()):
        if k.startswith(mission_id+'.'): lines.extend(['## '+k.split('.',1)[1],'',str(v),''])
    _atomic(root/'explanation.md','\n'.join(lines))
    artifacts=['explanation.md']
    if rows:
        output=io.StringIO();writer=csv.DictWriter(output,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        _atomic(root/'measurements.csv',output.getvalue());artifacts.append('measurements.csv')
    if figure is not None:
        (root/'evidence.png').write_bytes(png_bytes(figure));artifacts.append('evidence.png')
    payload={'schema_version':2,'lab_id':LAB.id,'mission_id':mission_id,'saved_at':datetime.now(timezone.utc).isoformat(),
             'state_signature':state_signature,'evidence':evidence,'artifact_hashes':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in artifacts}}
    write_json(root/'submission.json',payload);return root

def export_files():
    root=submission_root()
    # Recovery copies stay local; only current student evidence belongs in the ZIP.
    return sorted(p for p in root.rglob('*') if p.is_file() and p.name not in ('manifest.json','.gitkeep') and p.suffix not in ('.bak','.tmp') and '.unreadable.' not in p.name)

def write_manifest(st):
    from lab.completion import mission_status
    if not all(mission_status(st).values()): raise ValueError('Recheck and save every changed mission before export.')
    if not all(str(v).strip() for v in st.session_state['student'].values()): raise ValueError('Student identity is incomplete')
    if not 150<=len(str(st.session_state['responses'].get('final.synthesis','')).split())<=250 or not 1<=len(str(st.session_state['responses'].get('final.course_reflection','')).split())<=300: raise ValueError('Complete synthesis and reflection before export')
    save(st)
    required=('final_synthesis.md','final_reflection.md','student.json','autosave/responses.json','autosave/responses.md')
    if not all((submission_root()/name).is_file() for name in required): raise ValueError('Required submission files are missing. Prepare the synthesis and reflection again.')
    root=submission_root();files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in export_files()}
    path=root/'manifest.json'
    write_json(path,{'schema_version':2,'lab_id':LAB.id,'generated_at':datetime.now(timezone.utc).isoformat(),'student':dict(st.session_state['student']),
                     'mission_signatures':dict(st.session_state['checked_evidence_ids']),'response_signature':evidence_id(dict(st.session_state['responses'])),'files':files})
    return path

def manifest_current(st):
    try:
        data=read_json(submission_root()/'manifest.json')
        from lab.completion import mission_status
        if not all(mission_status(st).values()) or data.get('student')!=dict(st.session_state['student']): return False
        if data.get('mission_signatures')!=dict(st.session_state['checked_evidence_ids']): return False
        if data.get('response_signature')!=evidence_id(dict(st.session_state['responses'])): return False
        root=submission_root()
        expected={p.relative_to(root).as_posix() for p in export_files()}
        if expected!=set(data['files']): return False
        for name,digest in data['files'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: return False
        return True
    except (OSError,ValueError,KeyError,TypeError): return False

def submission_zip(st):
    # Refresh hashes after the latest autosave; never offer an obsolete archive.
    if not manifest_current(st): raise ValueError('Prepare a fresh submission before downloading.')
    write_manifest(st);root=submission_root();output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in [*export_files(),root/'manifest.json']: archive.write(p,p.relative_to(root).as_posix())
    return output.getvalue()
