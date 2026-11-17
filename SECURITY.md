# Security

Sparefold never asks for an API key, a session cookie, or a password. Workers shell out to the `claude` or `codex` binary already on the operator's machine. If that binary is missing, the run stops.

Do not put credentials in a result file, a prompt, or a commit. Checkers must be local and deterministic. A checker that phones a network is a bug.

`swarm audit --base <ref>` exists because a result JSON can lie about its checker. Trust the ref you already have, then re-run.

Claims are local files. They are not an authentication system.
