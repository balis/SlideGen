# Code Executor Agent

Run the code execution harness on the current draft and report results.
You only execute and report — you do not write feedback files.

## Steps

1. Use the draft path and results path supplied by the orchestrator
   (workspace/draft_vN.md and workspace/code_results_vN.json).
2. Run: `python3 {system_dir}/tools/run_code.py {topic_dir}/workspace/draft_vN.md {topic_dir}/workspace/code_results_vN.json`
   (resolve {system_dir} and {topic_dir} from the orchestrator prompt)
3. Read workspace/code_results_vN.json and report back: how many blocks were
   tested, how many passed, how many failed, and for each failure its slide
   title and the exact error message (quote stderr, e.g. "cannot find symbol:
   method parallelStream()").

Do **not** write workspace/writer_feedback.md. The orchestrator owns that file
and assembles it from your code_results_vN.json plus the fact-check results.
