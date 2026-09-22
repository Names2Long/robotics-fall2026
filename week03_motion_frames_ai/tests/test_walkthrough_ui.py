"""Exercise walkthrough gates without ROS or student submission writes."""
import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit is not installed")
class WalkthroughUI(unittest.TestCase):
    def test_complete_and_revisit_walkthroughs(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_string('''
import streamlit as st
from lab.session import initialize
from pages.concepts import render
initialize(st)
render(st)
''', default_timeout=20).run()

        def click(label):
            button = next(b for b in app.button if b.label == label)
            self.assertFalse(button.disabled, label)
            button.click().run()
            self.assertFalse(app.exception)

        self.assertFalse(app.exception)
        for index, keys in enumerate((('forward','turn','arc','stop'),
                                      ('equal','left_turn','right_turn','opposite'),
                                      (), ('ideal_measure','changed_measure'), ())):
            self.assertEqual(app.session_state['walkthrough.index'], index)
            for key in keys:
                app.button(key=key).click().run()
                self.assertFalse(app.exception)
            if index == 0:
                previous = app.session_state['walkthrough.animation']['token']
                app.button(key='stop').click().run()
                self.assertNotEqual(previous, app.session_state['walkthrough.animation']['token'])
            if index == 2:
                app.slider[0].set_value(-.8).run()
                click('Use reference snapshot for this walkthrough')
            if index == 4:
                click('Inspect the proposed code')
                click('Run the decision and boundary tests')
            click('Mark reviewed')
            if index < 4:
                click('Next walkthrough')
        self.assertEqual(len(app.session_state['responses']['walkthrough.completed']), 5)
        app.selectbox[0].select(0).run()
        self.assertEqual(app.session_state['walkthrough.index'], 0)
        self.assertTrue(next(b for b in app.button if b.label == 'Previous walkthrough').disabled)
        app.selectbox[0].select(2).run()
        click('Previous walkthrough')
        self.assertEqual(app.session_state['walkthrough.index'], 1)
        app.selectbox[0].select(4).run()
        click('Continue to environment preflight')
        self.assertEqual(app.session_state['stage'], 'preflight')
