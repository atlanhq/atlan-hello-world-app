---
id: RP02
applies-to: [app, tests, contract]
---
# Running the app needs only Python, uv and the README's two commands

Principle: The app talks to no external system and needs no credential, env var, service or
install step beyond `uv sync` and `python -m app.run_dev`. The integration tier stays hermetic on
the SDK fixture kit, with no source and no seeded secret.
Why: Earlier changes removed every external prerequisite and env knob so a newcomer's first run
cannot fail on setup. Adding one back breaks the first run for every developer who clones the repo.
Ask:
- Does the diff make local start-up, the dev server or the integration tier depend on a new required env var, credential field, running service or install step?
- Does it turn on a credential config or a secret store, or add a source fixture, for a feature that does not need it?
Don't flag: optional settings with working defaults; changes the SDK makes to its own local runtime;
a credential added together with the secret store (`K030` covers the store being off). Conformance
reports credential env vars read directly (`S002`) and hard-coded credentials (`S001`).
Severity: High when a clean clone can no longer start, or the integration tier needs an external
service. Medium for a new optional prerequisite that the README does not explain.
