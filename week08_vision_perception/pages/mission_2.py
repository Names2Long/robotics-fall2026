from perception.experiments import run, validate
from lab.submissions import store_run


def render(st, comparison=False):
    classical = st.session_state['evidence'].get('mission_1')
    evidence = st.session_state['evidence'].get('mission_2')
    st.subheader('Part C: compare and choose' if comparison else 'Part B: explore learned representations')
    if not comparison:
        st.write('A learned model uses numerical parameters called weights, adjusted using training images before this lab. Frozen means those weights stay fixed. Inference means applying the trained model to a new image. Changing an acceptance threshold does not train the model.')
        st.write('You will inspect three different outputs. Classification gives labels for the whole scene. Detection proposes object labels and rectangles. Segmentation marks pixels belonging to a region. The activities explain each output before asking you to interpret it.')
        st.write('A matching scene means the identical test image, not a similar photograph. Both cup detectors receive the same pixels and are checked against the same target definition. This lets you compare methods without changing the test at the same time.')
        st.markdown('''1. Press **Load prepared model results**. Preflight has already computed the predictions if it passed. Otherwise this first run computes and saves them.
2. Work through the four guided activities. Choose a scene and inspect the output alongside the explanation.
3. Continue to Part C for a focused three-condition comparison. Your settings and outputs remain available there.''')
        if st.button('Load prepared model results', type='primary', key='learned.load'):
            with st.spinner('Loading reusable predictions and saving your experiment'):
                store_run(st, 'mission_2', run('learned'))
            evidence = st.session_state['evidence']['mission_2']
    if not evidence or not evidence.get('representations'):
        st.info('Complete Part B and load its model results before comparing. Your earlier writing remains saved.')
        return
    try:
        validate(evidence, 'learned')
    except (ValueError, KeyError, TypeError) as error:
        st.info(str(error)+'. Load prepared model results in Part B to use the current collection. Earlier results and answers remain recoverable.')
        return
    if comparison:
        from pages.comparison import render as compare
        compare(st, evidence, classical)
    else:
        from pages.learned_lessons import render as lessons
        lessons(st, evidence, classical)
