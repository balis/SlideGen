# Code Executor Agent

Run the code execution harness on the current draft.

## Steps
1. Determine current draft version N (latest draft_vN.md in workspace/).
2. Run: `python3 {system_dir}/tools/run_code.py {topic_dir}/workspace/draft_vN.md {topic_dir}/workspace/code_results_vN.json`
   (resolve {system_dir} and {topic_dir} from the orchestrator prompt)
3. Read workspace/code_results_vN.json.
4. If failed > 0, write workspace/writer_feedback.md with a section titled
   "## Code Failures" listing each failed block, its slide title, and the error message.
   Be specific: if stderr says "cannot find symbol: method parallelStream()", say exactly that.
5. Report back: how many blocks tested, how many passed, how many failed.
