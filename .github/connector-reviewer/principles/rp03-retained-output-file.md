---
id: RP03
applies-to: [app, tests]
---
# The workflow's output file outlives the run as its retained store copy

Principle: `HelloWorldOutput.output_file` is the run's only artifact. It stays `RETAINED`, and
anything that reads it after the run (a test, a consumer, the README) reads the store copy at
`storage_path`. The local scratch file is deleted by post-run cleanup.
Why: An SDK upgrade turned on post-run cleanup, and a test that read the local scratch path after
the run broke in the merge queue. A move to a transient tier would leave the returned reference
pointing at nothing.
Ask:
- Does the diff change the tier of the greetings file, or stop returning it as `output_file`?
- Does code or a test read `local_path` after the run completes, rather than `storage_path`?
- Is the test that pins local cleanup removed or skipped without a reason?
Don't flag: `summarize` reading `local_path` inside the same run, which reads the copy the SDK
materialised for it. Conformance reports a declared artifact schema that is missing or disagrees
with the writer (`K016`, `K017`), hand-set durability fields (`P010`) and transfers nested in a
task (`P008`).
Severity: High when the returned reference can point at a deleted file. Medium when only a test
reads the wrong copy.
