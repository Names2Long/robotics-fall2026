"""One investigation with three connected parts and stable evidence storage keys."""
from lab.autosave import save
from pages import mission_1, mission_2

PARTS = ('A. Classical detector', 'B. Learned representations', 'C. Compare and choose')


def part_a_answered(st):
    return all(str(st.session_state['responses'].get('mission_1.'+key,'')).strip() for key in ('diagnosis','limitations'))


def render(st):
    st.header('Detector investigation: find the mug on a desk')
    st.write('An assistive robot has been asked to locate the mug without confusing it with the laptop, keyboard or trackpad. Your job is to evaluate visual evidence for that location. You are not controlling a robot arm or measuring a safe grasp pose.')
    st.write('Complete three connected parts. First configure a color-based detector. Next inspect models trained before this lab. Finally compare both cup detectors on identical images and recommend one for this task. Mug is included in the models\' broader cup category.')
    index = min(2, max(0, int(st.session_state['settings'].get('investigation_part', 0))))
    part = index if part_a_answered(st) else 0
    st.session_state['settings']['investigation_part'] = part
    st.caption(PARTS[part])
    if part == 0:
        mission_1.render(st)
    else:
        mission_2.render(st, comparison=part == 2)
    a, b = st.columns(2)
    if part and a.button('Back to '+PARTS[part-1], key='investigation.back'):
        _move(st, part-1)
    if part == 0 and not part_a_answered(st):
        b.caption('Respond to both Part A questions before continuing.')
    if part < 2 and b.button('Continue to '+PARTS[part+1], key='investigation.next', type='primary', disabled=not part_a_answered(st)):
        _move(st, part+1)


def _move(st, part):
    if part > 0 and not part_a_answered(st):
        st.warning('Respond to both Part A questions before continuing.')
        return
    st.session_state['settings']['investigation_part'] = part
    st.session_state.pop('investigation.part', None)
    st.session_state['scroll_to_top'] = True
    save(st)
    st.rerun()
