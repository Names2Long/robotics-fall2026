"""Small local Streamlit component. No external scripts or package downloads."""
import base64
import math
from pathlib import Path
import cv2


def coordinates(value, width, height):
    if not isinstance(value, dict): return None
    x, y = value.get('x'), value.get('y')
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (x, y)):
        return None
    if not (0 <= x < width and 0 <= y < height): return None
    return int(x), int(y)


def picker(st, image):
    import streamlit.components.v1 as components
    component = components.declare_component('lab7_pixel_picker', path=str(Path(__file__).parent/'pixel_component'))
    ok, encoded = cv2.imencode('.png', image)
    if not ok: raise ValueError('Cannot display the source scene')
    value = component(image=base64.b64encode(encoded.tobytes()).decode('ascii'),
                      width=image.shape[1], height=image.shape[0], key='pixel.click', default=None)
    token = value.get('token') if isinstance(value, dict) else None
    point = coordinates(value, image.shape[1], image.shape[0])
    if point and token and token != st.session_state.get('pixel.last_click'):
        st.session_state['lesson.pixel_x'], st.session_state['lesson.pixel_y'] = point
        st.session_state['pixel.last_click'] = token
