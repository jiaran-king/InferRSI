# InferRSI plugin for Codex (Developer Preview)

Use InferRSI from a Codex conversation in your target repository: research a
bottleneck, prepare a comparison, or inspect an existing run. This is the Codex
implementation slice of [RFC #152](https://github.com/InferMatrixLab/InferRSI/issues/152);
DSH/openJiuwen integration and a measured usability comparison remain separate.

## Install from the Release ZIP

The [daily release guide](https://github.com/InferMatrixLab/InferRSI/blob/main/docs/releases.md)
describes the versioned installer named
`inferrsi-codex-plugin-vX.Y.Z.zip` in
[GitHub Releases](https://github.com/InferMatrixLab/InferRSI/releases). Download
it with `SHA256SUMS` and verify the ZIP's SHA-256 before importing it. The ZIP
contains exactly one plugin directory:

```text
inferrsi/
  plugin.json
  skills/inferrsi/SKILL.md
  skills/inferrsi/scripts/inferrsi.py
  runtime/manifest.json
  runtime/inferrsi/
  LICENSE
  README.md
```

The downloaded archive bundles the same-version InferRSI runtime and knowledge;
installation requires no source checkout, package build or separate pip install.
There is no marketplace catalog, registration step or distribution branch.

If your Codex client offers **Plugins → Add → Upload plugin archive**, use it
to import the downloaded `inferrsi-codex-plugin-vX.Y.Z.zip`. If the InferRSI
detail page offers **Install plugin**, select it and follow the prompts. After
installation, enable InferRSI, open your target repository and start a new
conversation.

[Watch or download the installation guide (English narration and subtitles)](https://raw.githubusercontent.com/InferMatrixLab/InferRSI/main/docs/assets/inferrsi-codex-install-en.mp4).
The video uses English UI illustrations based on the supplied screenshots to show
the menu click order; it does not record a completed upload or installation.
Exact labels and availability depend
on the client and workspace permissions. Here, offline package describes the
included runtime and resources; it does not guarantee offline client operation.

Clients without archive import cannot install this package directly. The current
Codex CLI's `plugin add` accepts marketplace selectors, not ZIP paths; do not pass
the archive to that command. Archive ingestion and enablement must be verified
on the target host; release checks validate package contents and local execution.

Requires a local Codex client with plugin support and Python 3.10 or newer.
Git is needed for target-repository inspection and experiment source provenance.
The built plugin contains the same InferRSI core and knowledge bytes as its
source build; basic operations need no pip install, network service or API key
specific to InferRSI. Your normal Codex model connection is still required.

## First task

Open the repository you want to investigate and ask, for example:

> Use InferRSI to research this engine's memory bottleneck. Find relevant
> knowledge and explain what is needed for a controlled comparison.

Or:

> Use InferRSI to inspect the existing run I provide and explain its verdict,
> missing evidence and next action.

The plugin checks its bundle/interpreter, reads relevant knowledge progressively,
and uses the current CLI's help to prepare operations. Its optional onboarding
action invokes the same entry skill. Setup does not start benchmarks.

Use the script resolved from the installed skill for manual diagnosis:

```text
python -X utf8 "<PLUGIN_ROOT>/skills/inferrsi/scripts/inferrsi.py" --plugin-info
python -X utf8 "<PLUGIN_ROOT>/skills/inferrsi/scripts/inferrsi.py" --help
```

Core `knowledge`, packaged `collect/read`, `doctor`, `plan/run` and
`status/report` delegate to the bundled runtime. The optional `skills` commands
and checkout-skill sources need PyYAML in the selected Python interpreter.
Image validators and target engines retain their own optional dependencies.

## MindIE knowledge and an RMSNorm candidate

Use one Codex agent in one session: InferRSI owns task/round identities, budgets,
controlled execution and independent evaluation; that agent reads MindIE
knowledge and edits the candidate. MindIE supplies knowledge in this first phase.
No MindIE optimization loop, model request or remote execution is added.

`campaign import-mindie` is an offline CLI host adapter. It accepts the graded
query/explain contract documented by
[MindIE Codex v0.1.21](https://github.com/mindie-agent/mindie-agent-codex/blob/v0.1.21/plugins/mindie-agent/skills/mindie-agent/references/domain-skills.md):
revision-bound `mindie://<domain>/units/<id>@<integer>` references and full
`units` / `requires` / `unresolved` delivery. It supports direct JSON, MCP
`structuredContent`, or one JSON text block. Unsupported or legacy material
formats are rejected for explicit inspection. Software fixtures exercise this
mapping; they do not qualify a live MindIE session or NPU.

Keep the work directory outside the source checkout. Set `WORK`, `CAMPAIGN_DIR`,
`CAMPAIGN_ID`, `CANDIDATE_ID` and `ROUND` from the actual task, and keep the
installed InferRSI launcher/interpreter consistent. Commands below use
`inferrsi`; the installed plugin's launcher accepts the same arguments.

### Obtain and retain the actual read

First inspect the task and actual environment. Record the InferRSI baseline and
diff, Codex version, installed MindIE plugin/runtime and knowledge-component
versions, and corpus Git commit separately. A unit's integer revision is neither
the corpus commit nor a plugin version. Preserve unknown values as unknown.

From the target Git checkout, authorize the already synced domain once:

```sh
inferrsi mindie enable --domain operators
inferrsi mindie describe
```

The project reader uses the installed `mindie-knowledge 0.13.13` graded
retrieval engine with a read-only connection to the synced local catalog.
`--adapter-config` selects the installed adapter when it lives outside the
default MindIE config location. The grant and read receipts live in the user's
local InferRSI configuration directory. New sessions in this checkout discover
the grant through the InferRSI Skill. Use `inferrsi mindie disable` there to
revoke it. Opening another checkout requires that project's own grant.

To expose the two reads as native MCP tools, add the following entry to the
trusted project's Codex configuration once. Set the command to the installed
InferRSI executable and the cwd to the checkout that has the grant. For a built
plugin, use the compatible Python command and prepend the absolute bundled
launcher path to `args`.

```toml
[mcp_servers.inferrsi_mindie]
command = "<absolute-inferrsi-executable>"
args = ["mindie", "serve"]
cwd = "<absolute-project-checkout>"
enabled_tools = ["knowledge_query", "knowledge_explain"]
```

The Skill checks whether a specific implementation decision needs research
before writing a candidate. Use the available MCP tools or the bundled CLI.
Record the decision and continue with the available evidence when a read is
unavailable or the search has no applicable hit.

Create `query-input.json` using observed facts. For the currently proposed
RMSNorm task package, the timed inputs are contiguous float32 `[1,4096]` and
`[64,4096]`, with nonuniform weights. Verify the selected task before using this
example; add SoC/CANN conditions only after probing them:

```json
{
  "query": "Ascend RMSNorm float32 reduction precision and memory access",
  "conditions": {"dtype": "float32", "input_shape": [[1, 4096], [64, 4096]]},
  "limit": 5,
  "token_budget": 8000
}
```

```sh
inferrsi mindie query --input "$WORK/query-input.json"
```

Inspect exit status, `isError` and the business payload. Copy exact versioned
refs from the successful query into `explain-input.json` (`refs`, observed
`conditions`, `known_refs`, `token_budget`). `known_refs` may list only full
exact-version bodies still visible in this agent's context; after compaction,
read them again. Then:

```sh
inferrsi mindie explain --input "$WORK/explain-input.json"
```

Inspect this response too, and actually read the delivered bodies. Search cards
and excerpts are navigation; errors and `unresolved` are not delivered knowledge.
For example, five search hits and one expanded unit remain five hits and one
expanded unit, plus any prerequisites actually returned in `requires`.

Set `QUERY_READ` and `EXPLAIN_READ` to the respective returned
`receipt_directory` values. Confirm both exits in their `receipt.json` files.
Use an existing matching campaign or initialize a new one, then import the
retained bytes:

```sh
inferrsi campaign init --directory "$CAMPAIGN_DIR" --id "$CAMPAIGN_ID"
inferrsi campaign import-mindie --directory "$CAMPAIGN_DIR" --id read-r1 \
  --query-input "$QUERY_READ/input.json" --query-result "$QUERY_READ/result.json" \
  --explain-input "$EXPLAIN_READ/input.json" --explain-result "$EXPLAIN_READ/result.json" \
  --query-exit-code 0 --explain-exit-code 0
```

The new `mindie/read-r1/` directory contains exact original files, a hash receipt,
`reviewed-context.txt` and `context.json`. The latter is a fragment for the
existing trace template, with `text` deliberately empty. Its sources include
only delivered bodies and prerequisites. Each locator names the retained
response, its SHA-256 and the position of the exact content. Unit refs are
qualified from the request domain and the delivered id/integer revision when
the response omits a redundant `ref` field. Excluded or undelivered requested
material marks the context partial, with its original `unresolved` list retained.

The importer does not mark caller review or read a transcript. A response file
and supplied exit code are caller-provided evidence, not authenticated tool
receipts or proof of model consumption. Failed reads, missing files and empty
deliveries are rejected. Existing read IDs are never overwritten. On an I/O
failure preserve any partial export for inspection and use a fresh ID after
resolving the cause. Ordinary InferRSI operations require no MindIE installation.

### Deliver and independently evaluate one fixed candidate

Freeze the selected task, baseline, scalar oracle, shapes/dtype, tolerances,
measurement boundary and this round's budget **before** modifying a candidate.
Use the task's existing gates; do not substitute default CLI values for accepted
criteria. The RMSNorm package uses scalar double/`math.fsum` correctness,
also checks zero/large/tiny inputs and input/weight preservation, and measures
synchronized eager-call latency with generation, transfers and validation
outside the timer. It does not measure pure kernel time or service throughput.

**Task availability:** the shared `benchmarks` RMSNorm path is proposed in
[Draft #338](https://github.com/InferMatrixLab/InferRSI/pull/338), tracked by
[#337](https://github.com/InferMatrixLab/InferRSI/issues/337). It is not supplied
by this integration. Use only an explicitly selected, reviewed evaluation
revision/environment; retain its revision separately from this host adapter.
Check `"$EVAL_PYTHON" -m inferrsi benchmarks show rmsnorm-npu` before preparing
the commands below. If absent, retain that gap; do not invent a mainline command
or silently merge the Draft. The existing `run` entry can instead consume
explicitly reviewed independent benchmark/validation commands.

The agent edits `"$WORK/generation/implementation.py"` after reading the actual
knowledge. Deliver a separate v1 source snapshot, including all local imports:

```sh
mkdir "$WORK/candidate-v1"
cp "$WORK/generation/implementation.py" "$WORK/candidate-v1/implementation.py"
git -C "$WORK/candidate-v1" init -b codex/rmsnorm-v1
git -C "$WORK/candidate-v1" add -- implementation.py
git -C "$WORK/candidate-v1" commit -s -m "Freeze reviewed RMSNorm candidate v1"
CANDIDATE_REPO="$WORK/candidate-v1"
```

Use the project's Author, Committer and sign-off policy for that local snapshot.
Retain its commit separately from the evaluator revision. `--repo` sets the
trial working directory: for the selected RMSNorm worker, it must contain the
exact frozen `implementation.py`, because Triton JIT source inspection resolves
that filename there. The standalone `check` already uses the candidate's parent;
`compare` uses `--repo`. When using the pinned evaluator source checkout, set
`PYTHONPATH="$EVAL_REPO/src"` for these commands so evaluator imports remain
separate from the candidate execution checkout. Inspect `benchmarks plan` before
execution to confirm those paths and the frozen task/candidate identities.

Retain a manifest of its SHA-256, originating baseline/diff, generation round,
reviewed knowledge receipt and applicable source-review outcome. Review before
using the trusted NPU worker: the formal CPU sandbox does not qualify generated
NPU code. Use the authorized task/allocation and exclusive physical device
reservation, respecting A3 dual-Die ownership. Verify the selected single
`ASCEND_RT_VISIBLE_DEVICES` mapping; this document grants no resources.

Inside that authorized allocation, using the frozen budget and gates:

```sh
"$EVAL_PYTHON" -m inferrsi benchmarks check rmsnorm-npu \
  --candidate "$WORK/candidate-v1/implementation.py" \
  --output-dir "$WORK/check-v1" --timeout-seconds "$ACTION_TIMEOUT"
"$EVAL_PYTHON" -m inferrsi benchmarks compare rmsnorm-npu \
  --candidate "$WORK/candidate-v1/implementation.py" --repo "$CANDIDATE_REPO" \
  --output-dir "$CAMPAIGN_DIR/runs" --repetitions "$PAIRS" \
  --max-minutes "$COMPARISON_MINUTES" --min-improvement-pct "$GAIN_GATE" \
  > "$WORK/compare-v1.json"
COMPARE_EXIT=$?
```

Record check and comparison exit statuses and outputs, including negative
results. Establish allocation/process deadlines and verify cleanup: the #338
whole-utility/action-timeout finding is not resolved by this adapter. Do not run
the full qualification utility to obtain ordinary candidate measurements.
Profiling is optional. Inspect the actual returned `run_dir` to obtain `RUN_ID`;
if no run was created, do not fabricate an association.

### Bind the read, round, delivered source and run

Copy the complete
[per-candidate trace template](https://github.com/InferMatrixLab/InferRSI/blob/main/docs/dashboard.md#per-candidate-narrative-schema-version-1)
and replace its `context` with the exported `context.json`. Fill the actual
`CAMPAIGN_ID`, `CANDIDATE_ID`, `ROUND`, `RUN_ID`, search/attempt narrative and
limitations. Review the full delivered text and original responses before
setting `reviewed_by_caller: true`. If a copy is shortened or sanitized, retain
the authorized original separately and use `partial`/`redacted` with the reason;
do not describe it as the complete original.

```sh
inferrsi campaign assemble-trace --directory "$CAMPAIGN_DIR" \
  --template "$WORK/trace-template.json" \
  --context-file "$CAMPAIGN_DIR/mindie/read-r1/reviewed-context.txt" \
  --output optimization-v1.json
inferrsi campaign record --directory "$CAMPAIGN_DIR" \
  --candidate "$CANDIDATE_ID" --run-id "$RUN_ID" --round "$ROUND" \
  --title "RMSNorm candidate v1" --optimization-trace optimization-v1.json
inferrsi status --output-dir "$CAMPAIGN_DIR/runs" --run-id "$RUN_ID"
inferrsi report --output-dir "$CAMPAIGN_DIR/runs" --run-id "$RUN_ID"
inferrsi dashboard --input "$CAMPAIGN_DIR" --output "$WORK/dashboard.html"
```

Follow `candidates/<candidate_id>/candidate.json` to its hashed optimization
trace, the retained explain response and its source positions. Follow `run_id`
to `runs/<run_id>/run.lock.json`, `repositories.lock.json`, per-command source
checks, validation, results and `evaluation.json`. For the shared task, compare
the worker's `candidate_sha256` and frozen command identity with the retained
source snapshot. The generic runner fingerprints checkouts; it does not copy
source files or authenticate external candidate paths. A candidate ID alone
cannot establish tested bytes. Generate v2 under a new candidate/snapshot and
trace; changing the generation workspace must not change what the v1 commands
load. Preserve v1 and all failed attempts.

Report correctness, measured performance, process state, wall time and available
usage separately. Missing token/call/device accounting stays unknown. A failed
quality gate or absent speedup is retained; incomplete source/device/measurement
evidence is `INCONCLUSIVE`. CPU fixtures, NPU operator verification and service
claims remain distinct. This workflow neither publishes artifacts nor grants
Issue/PR/comment/knowledge-contribution or merge permission.

## Build from the InferRSI source checkout

```text
python tools/build_codex_plugin.py
```

This writes a fresh `dist/codex-plugin/` standalone plugin directory and
`dist/codex-plugin.zip`. The ZIP always has the single enclosing `inferrsi/`
directory shown above; the output directory's name does not add a wrapper.
To rebuild, choose a new `--output <directory>`; the builder refuses to replace
an existing distribution/archive.

For release builds, first build the runtime so SCM generates `_version.py`, then
pass `--release-version <version>` and a versioned output directory. The builder
requires that version to match the generated runtime. It stamps the generated
plugin manifest and pins the bundled README's video link to the release tag.
The tracked source template remains unchanged.
Unbuilt source previews use the runtime's explicit `0+unknown` fallback.

Only the ZIP is attached to Releases. The raw `plugins/inferrsi/` source template
does not contain the bundled runtime and is not an installation package.

The build copies the canonical Python package, its packaged knowledge/resources
and source notices, plus the repository license. It records per-file SHA-256
digests and the runtime version in `runtime/manifest.json`. Generated copies live
only in the distribution; maintain procedures and metadata in their existing
source owners. No new core dependencies or CI lanes are introduced.

## Updates, disable and uninstall

Download and verify the new Release ZIP, then use the client's supported update
or replacement flow for the existing InferRSI plugin. Check the selected bundle with
`--plugin-info` in a new conversation. Do not overwrite an installed cache or
carry forward an old runtime by hand.

For older installations managed through Plugin Creator, file updates overlay
existing files. Compare the old and new runtime manifests and explicitly remove
obsolete runtime files and resources while retaining the same plugin identity
and audience. Files omitted from that update archive remain installed. Verify
how native ZIP replacement behaves on your target client.

Disable InferRSI in the desktop plugin UI when you want to retain its installation
but stop loading it. To uninstall, remove the selected InferRSI plugin in the
client's plugin management UI. Existing marketplace-based previews are a separate
installation: disable/remove them in the client before enabling the ZIP import
so only one InferRSI entry skill is active.

Removal does not delete target repositories or experiment evidence. The plugin
registers no MCP server, hooks, daemon or scheduled task.

## Troubleshooting and limits

| Observation | Next step |
| --- | --- |
| Python cannot be found or is too old | Select/install Python 3.10+ and use its executable consistently |
| Incomplete bundle or version mismatch | Rebuild/reinstall the distribution; do not substitute an unrelated installed runtime |
| Optional skills dependency missing | Use packaged Collect/Read, or install PyYAML in the chosen interpreter |
| No knowledge match | Inspect the query/source selection; no match does not establish lack of an optimization |
| Target backend unavailable | Fix the target environment; knowledge research remains usable |
| Interrupted experiment | Inspect its existing status/evidence before deciding on a new run |

Execution remains local to the prepared target machine. The plugin does not
install accelerator stacks, download weights or dispatch SSH jobs. A `plan`
preview does not freeze validators or authorize execution. Preserve the user's
accepted campaign gates, evidence and authorization; completed processes do not
automatically establish PASS.

The preview's functional checks and actual host observations must be reported
separately from a usability pilot or an inference-performance campaign. Synthetic
CPU comparisons establish command/evidence wiring only.

Plugin installation and packaging follow the
[official OpenAI plugin guide](https://developers.openai.com/plugins/build/plugins).
