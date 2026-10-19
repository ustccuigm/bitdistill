import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from steerdistill.analysis import AnalysisRejected, call_analyzer, extract_object


class AnalyzerSchemaTests(unittest.TestCase):
    def test_invalid_content_records_rejections_and_retries_with_feedback(self):
        requests = []
        def respond(request, **kwargs):
            requests.append(json.loads(request.data))
            return io.BytesIO(json.dumps({'choices': [{'message': {'content': '{}'}}]}).encode())
        with patch('steerdistill.analysis.apply_budget', side_effect=lambda url, body, key: body), \
             patch('urllib.request.urlopen', side_effect=respond):
            with self.assertRaises(AnalysisRejected) as error:
                call_analyzer('http://localhost/v1', 'EMPTY', 'model', '{}')
        self.assertEqual(len(error.exception.analysis['rejected_responses']), 5)
        self.assertEqual(requests[0]['response_format']['type'], 'json_schema')
        self.assertIn('failed schema validation', requests[1]['messages'][-1]['content'])

    def test_network_failure_is_not_an_analysis_rejection(self):
        with patch('steerdistill.analysis.apply_budget', side_effect=lambda url, body, key: body), \
             patch('urllib.request.urlopen', side_effect=urllib.error.URLError('offline')), \
             patch('time.sleep'):
            with self.assertRaises(RuntimeError) as error:
                call_analyzer('http://localhost/v1', 'EMPTY', 'model', '{}')
        self.assertNotIsInstance(error.exception, AnalysisRejected)

    def test_non_object_is_rejected_without_type_error(self):
        with self.assertRaisesRegex(ValueError, 'JSON object'):
            extract_object('[{}]')
