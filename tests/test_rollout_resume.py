import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from steerdistill.online import main

class ResumeTest(unittest.TestCase):
    def test_rollout_resume_and_training_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            prompts=base/'prompts.jsonl'
            prompts.write_text(''.join(json.dumps({'task':i})+'\n' for i in range(16)))
            clip=base/'clip.pt'
            clip.write_bytes(b'clip')
            run=base/'online'
            env={'STEER_ONLINE_ROOT':str(run),'BENCHMARK_ENGINE':'tool_env',
                 'PROMPT_MANIFEST':str(prompts),'BENCHMARK':'bfcl_v4','MODEL_FAMILY':'qwen3_8b',
                 'TEACHER_MODEL':'teacher','INITIAL_W4_MASTER':'master','INITIAL_RUNTIME_W4':'runtime',
                 'CLIP_PATH':str(clip),'OPD_EPOCHS':'1','OPD_MAX_STEPS':'1'}
            def completed(*args):
                train=run/'steps/step000001/train'
                train.mkdir(exist_ok=True)
                (train/'training_signal.json').write_text(json.dumps({'global_step':1,'previous_step':0,'status':'passed'}))
            with patch.dict(os.environ,env,clear=True), patch('sys.argv',['steerdistill.online.py','--gpu-ids','0,1']), \
                 patch('steerdistill.online.model_digest',side_effect=str):
                with patch('steerdistill.online.run_command',side_effect=RuntimeError('rollout failed')):
                    with self.assertRaisesRegex(RuntimeError,'rollout failed'): main()
                with self.assertRaisesRegex(ValueError,'Partial step'): main()
                os.environ['OPD_RESUME_ROLLOUT_ONLY']='1'
                train=run/'steps/step000001/train'
                train.mkdir()
                artifact=train/'partial.json'
                artifact.write_text('{}')
                with self.assertRaisesRegex(ValueError,'training artifacts'): main()
                artifact.unlink()
                with patch('steerdistill.online.run_command',side_effect=completed) as execute:
                    main()
                    self.assertEqual(execute.call_count,1)
                    main()
                    self.assertEqual(execute.call_count,1)

if __name__=='__main__': unittest.main()
