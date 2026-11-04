import json
from pathlib import Path
import tempfile
import unittest
from planning.core import inflate,make_map
from planning.experiments import student_search


class WorkerTests(unittest.TestCase):
    def test_quick_same_size_edit_does_not_run_cached_code(self):
        import os
        import py_compile
        from planning.experiments import student_search
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'planners.py'
            source.write_text("def bfs(ctx):\n    raise ValueError('old')\n")
            stamp = source.stat()
            py_compile.compile(str(source),doraise=True)
            source.write_text("def bfs(ctx):\n    raise ValueError('new')\n")
            os.utime(source,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
            row = student_search(source,'bfs',[[0,0]],(0,0),(0,1))
            self.assertIn('new',row['error'])

    def test_error_and_hard_timeout(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'test_source.py'
            source.write_text('def bfs(ctx):\n    raise NotImplementedError("complete this")\n')
            row = student_search(source,'bfs',inflate(make_map('open')))
            self.assertEqual(row['status'],'implementation_error')
            source.write_text('def bfs(ctx):\n    while True:\n        pass\n')
            row = student_search(source,'bfs',inflate(make_map('open')),timeout=.5)
            self.assertEqual(row['status'],'resource_limit')


if __name__=='__main__':
    unittest.main()
