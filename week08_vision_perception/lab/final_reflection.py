"""The shared course reflection wording, kept identical to Labs 4, 5 and 6."""
PROMPTS = (
    "What did this activity make you think about regarding your own interests in robotics, computing, engineering, or related work?",
    "How did this activity affect your motivation to do similar kinds of work in the future?",
    "What value do you see in connecting technical or computing work with human, ethical, or societal considerations?",
    "What stood out to you about the activity, and why?",
    "Is there anything else you would like to share about your experience with the activity?",
)


def render(st):
    from lab.ui import text_response
    from lab.autosave import save
    st.subheader('Final reflection')
    st.write('Write a short reflection of no more than 300 words. You may respond to any or all of the prompts below.')
    st.markdown('\n'.join(f'{i}. {prompt}' for i,prompt in enumerate(PROMPTS,1)))
    answer = text_response(st,'final.course_reflection','Your reflection',220)
    if st.button('Save reflection and update word count',key='save.final.course_reflection'):
        save(st)
        st.success('Reflection saved and word count updated.')
    st.caption(f'{len(answer.split())}/300 words')
