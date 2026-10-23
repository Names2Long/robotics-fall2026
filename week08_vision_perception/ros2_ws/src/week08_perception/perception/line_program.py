"""Editable ROS steering code with a deliberately narrow arithmetic interface."""
import ast
from dataclasses import asdict
from perception.vision_control import VisionSettings

STARTER = '''"""Camera line controller used by the ROS node.
Edit one choice at a time, save, stop the old controller, reset the world and run.
The initial steering gain is intentionally weak. Diagnose it, do not assume it
will follow bends. The ROS node keeps the freshness and motion safeguards.
"""
GAIN = 0.08
SPEED = 0.16  # metres per second before slowing for large image errors
ROI_TOP = 0.60  # fraction of image height, measured from the top
ROI_BOTTOM = 0.95
HUE_LOW = 140  # OpenCV hue, 0 to 179
HUE_HIGH = 169
MIN_FRACTION = 0.002  # smallest selected contour area / region area


def angular_velocity(error, gain):
    """Image right is positive error. ROS left turn is positive angular speed."""
    return -gain * error
'''
FIELDS = {'GAIN':'gain','SPEED':'speed','ROI_TOP':'roi_top','ROI_BOTTOM':'roi_bottom',
          'HUE_LOW':'hue_low','HUE_HIGH':'hue_high','MIN_FRACTION':'min_fraction'}


def load_program(source):
    """Validate literal settings and a pure arithmetic steering function.

    Disallow imports, file access, loops and arbitrary calls in this small editor.
    Students can change the actual executed steering expression without replacing
    the ROS camera loop or the independent watchdog.
    """
    if len(source)>12000: raise ValueError('Keep the controller program below 12000 characters')
    try: tree = ast.parse(source)
    except SyntaxError as error: raise ValueError('Python syntax: '+str(error)) from error
    values = {}
    function = None
    for item in tree.body:
        if isinstance(item,ast.Expr) and isinstance(item.value,ast.Constant) and isinstance(item.value.value,str): continue
        if isinstance(item,ast.Assign) and len(item.targets)==1 and isinstance(item.targets[0],ast.Name) and item.targets[0].id in FIELDS:
            name = item.targets[0].id
            if name in values: raise ValueError('Define each setting only once')
            try: value = ast.literal_eval(item.value)
            except (ValueError,TypeError): raise ValueError('Settings must be literal numbers')
            if isinstance(value,bool) or not isinstance(value,(int,float)): raise ValueError('Settings must be numbers')
            values[name] = value
        elif isinstance(item,ast.FunctionDef) and item.name=='angular_velocity' and function is None:
            function = item
        else: raise ValueError('Keep the named numeric settings and angular_velocity(error, gain) function only')
    if set(values)!=set(FIELDS) or function is None: raise ValueError('Keep all seven settings and the steering function')
    args = function.args
    if [a.arg for a in args.args] != ['error','gain'] or args.posonlyargs or args.kwonlyargs or args.vararg or args.kwarg or args.defaults or function.decorator_list or function.returns or any(a.annotation for a in args.args):
        raise ValueError('Use exactly def angular_velocity(error, gain):')
    body = function.body
    if body and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str): body = body[1:]
    if len(body)!=1 or not isinstance(body[0],ast.Return): raise ValueError('The steering function must contain one return expression')
    allowed = (ast.Expression,ast.BinOp,ast.UnaryOp,ast.Name,ast.Load,ast.Constant,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.USub,ast.UAdd)
    expression = ast.Expression(body[0].value)
    for node in ast.walk(expression):
        if not isinstance(node,allowed): raise ValueError('Use arithmetic with error, gain and numeric constants')
        if isinstance(node,ast.Name) and node.id not in ('error','gain'): raise ValueError('Only error and gain are available in the steering expression')
        if isinstance(node,ast.Constant) and (isinstance(node.value,bool) or not isinstance(node.value,(int,float))): raise ValueError('Use numeric constants')
    settings = asdict(VisionSettings(kind='line_following'))
    settings.update({FIELDS[k]:v for k,v in values.items()})
    config = VisionSettings(**settings)
    compiled = compile(expression,'<student ROS steering>','eval')
    def steering(error,gain): return eval(compiled,{'__builtins__':{}},{'error':error,'gain':gain})
    return config,steering
