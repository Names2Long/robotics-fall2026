import importlib,sys,tempfile
from lab.autosave import submission_root

def checks():
    result=[('Python 3.12 or newer',sys.version_info>=(3,12),sys.version.split()[0])]
    for name in ('streamlit','numpy','pandas','matplotlib'):
        try:
            module=importlib.import_module(name);result.append((name,True,getattr(module,'__version__','available')))
        except ImportError as error: result.append((name,False,str(error)))
    try:
        root=submission_root();root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryFile(dir=root) as handle: handle.write(b'Lab 5 storage check');handle.flush()
        result.append(('Writable submission storage',True,str(root)))
    except (OSError,ValueError) as error: result.append(('Writable submission storage',False,str(error)))
    return result

def preflight():
    rows=checks()
    for name,passed,detail in rows: print(('PASS' if passed else 'FAIL')+' '+name+': '+detail)
    return all(passed for _,passed,_ in rows)
