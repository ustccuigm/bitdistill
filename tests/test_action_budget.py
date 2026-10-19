import io
import json
import os
import unittest
from unittest.mock import patch

from steerdistill.benchmarks.online_rollout import generate


class ActionBudgetTests(unittest.TestCase):
    def request(self, benchmark):
        response = {'choices': [{'message': {'content': '<think>done</think><action>click[x]</action>'},
                                 'finish_reason': 'stop'}], 'usage': {}}
        with patch.dict(os.environ, {'STEER_BENCHMARK': benchmark, 'MAX_TOKENS': '32768',
                                     'ACTION_MAX_TOKENS': '4096'}), \
             patch('steerdistill.benchmarks.online_rollout.apply_budget'), \
             patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(response).encode())) as call:
            text, metadata = generate('http://localhost/v1', 'model', [], 42)
        return json.loads(call.call_args.args[0].data), text, metadata

    def test_action_boundary_preserves_closing_tag_and_reasoning(self):
        for benchmark in ('webshop', 'alfworld'):
            payload, text, metadata = self.request(benchmark)
            self.assertEqual(payload['max_tokens'], 4096)
            self.assertEqual(payload['stop'], ['</action>'])
            self.assertTrue(payload['include_stop_str_in_output'])
            self.assertEqual(text, '<think>done</think><action>click[x]</action>')
            self.assertEqual(metadata['stop'], ['</action>'])

    def test_search_keeps_its_own_protocol(self):
        payload, _, _ = self.request('search_qa')
        self.assertEqual(payload['max_tokens'], 32768)
        self.assertNotIn('stop', payload)
