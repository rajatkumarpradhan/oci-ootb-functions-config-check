# oci-ootb-functions-config-check

**Category: built-in OCI services project (OOTB).** The custom portfolio project in this
pair is `oci-network-firewall-policy-check`.

## Which built-in OCI services this wires

- **OCI Functions** (`oci_functions_application` + `oci_functions_function`): the built-in
  serverless functions service. Per the OCI docs, a function's `config` is passed to it as
  **environment variables** (plaintext key-value, 4 KB cap), the sync **timeout defaults to
  30 seconds** (max 300), and **memory defaults to 128 MB** (Java functions are recommended
  at 256 MB or more). Each default is quiet until it hurts.

## Custom code vs native config

- **Native config**: `terraform/` declares one application and one function the careful
  way: explicit `timeout_in_seconds`, explicit `memory_in_mbs`, no secrets in `config`.
  Field names follow the oracle/oci provider docs. **Template only - NOT plan/apply
  validated** (no live tenancy).
- **Custom code**: `fn_check/` audits an offline JSON export of applications and functions
  against four gaps the defaults hide.

## The rules

| Rule | Severity | Fires when |
| ---- | -------- | ---------- |
| FNC001 | HIGH | A function's recorded `config` has a **secret-looking key** (`PASSWORD`, `SECRET`, `TOKEN`, `API_KEY`) with a value - config travels as plaintext env vars; secrets belong in OCI Vault. Review flag on naming. |
| FNC002 | MEDIUM | A **prod-labeled** function has no timeout recorded - it silently runs with the 30-second default. |
| FNC003 | MEDIUM | A **prod-labeled** function has no memory recorded - it silently runs with the 128 MB default (Java functions are recommended 256 MB+). |
| FNC004 | LOW | An application records **zero functions** - empty scaffolding as far as the export records. |

Exit code: `2` on any HIGH, `1` on MEDIUM/LOW only, `0` when clean.

## Run it

```bash
python -m fn_check.cli samples/functions_messy.json   # exits 2, all 4 rules fire
python -m fn_check.cli samples/functions_clean.json   # exits 0
python -m unittest discover -s tests -v               # 18 tests, stdlib only
```

## Honest limits

- **Offline audit**: the JSON export is synthetic; nothing calls the OCI API.
- FNC001 is a naming heuristic review flag, not proof of an exposed secret.
- Default values (30 s timeout, 128 MB memory, plaintext config) are from the OCI
  Functions docs as of Nov 2026; verify current defaults before acting.
- "prod" labeling is read from the export; an unlabeled production function is invisible
  to FNC002/FNC003.
- The Terraform template is illustrative and has **not** been plan/apply validated.
- No live tenancy was touched.

## Project status

Built as a daily OOTB project. 18 unit tests, green locally and in CI. Free tier only; no
live cloud calls, no spend.
