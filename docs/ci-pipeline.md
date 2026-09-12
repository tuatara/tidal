# CI/CD pipeline

Deferred work. Recorded 2026-09-12, not yet implemented.

---

## Current state

### Repo

- `github.com/tuatara/tidal`, public, so Actions minutes are unmetered.
- No `.github/` directory on `main`.
- `deploy.sh` builds the bundle with `uv export --no-dev | uv pip install --target deploy`, then zips `lambda_function.py tidal_functions.py cache.py .env` on top.
- A previous attempt lives only on `feature/actions-hack` (Oct 2024): `matrix.yml` and `simpler.yml`. Both were copied from a work project (multi-account matrix, `GithubActionsRole`, `web`/`worker`/`lp` environments) and are irrelevant here. The branch should be deleted rather than resurrected.
- Dependabot is enabled through the repo UI with no committed config, so it targets the `pip` ecosystem and does not understand `uv.lock`. Four stale PRs remain from 2024: `#1` idna 3.4 to 3.7, `#2` requests 2.31.0 to 2.32.0, `#3` urllib3 2.1.0 to 2.2.2, `#4` certifi 2023.7.22 to 2024.7.4.

### Deployed

Account `036700217332`, region `ap-southeast-2`.

| Property | Value |
|---|---|
| Function | `Tidal` |
| Package | Zip, 21,749,164 bytes |
| Runtime | `python3.13` |
| Architecture | `x86_64` |
| Memory / timeout | 160 MB (128 MB until 2026-09-12 03:49 UTC) / 30 s |
| Handler | `lambda_function.lambda_handler` |
| Layers / VPC | none / none |
| Trigger | Function URL, `AuthType: NONE`, created 2023-11-17, never modified |
| Env vars | present, encrypted with customer-managed KMS key `f691836b-0e93-4173-b7a5-0eff8e13b5ad` |
| Role | `Tidal-role-k3fvnos4`, path `/service-role/`, inline policy `s3-cache-bucket` |
| Tags | none |
| Log group | `/aws/lambda/Tidal` |
| Cache bucket | `tidal-cache-036700217332-ap-southeast-2-an`, no bucket policy |

The S3 cache is live: 141 `astro/` and 141 `tides/` objects, written in bursts, with invocations landing in the same second as the writes.

### Findings

1. **The bundle ships macOS C extensions to Linux.** `deploy/` contains `charset_normalizer/md__mypyc.cpython-313-darwin.so` and `md.cpython-313-darwin.so`. `charset_normalizer` is a `requests` dependency, so it is on the hot path for every NIWA and Visual Crossing call. Building on a Linux runner removes this class of bug by construction.
2. **The deployed artifact is stale.** The live zip hashes to `b00fd9dc80acde4f8427657d5dcf3eae8862aa704470153254ac9c0fd9840111`, byte-identical to the local `lambda-bundle.zip`, which is the May bundle containing `requests` 2.32.5. The urllib3 2.6.3 advisories are live in production.
3. **Secrets are in the deployment artifact.** `deploy.sh` zips `.env`, which holds `NIWA_API_KEY` and `VISUAL_CROSSING_API_KEY`, alongside the code. The function also has CMK-encrypted env vars, and `load_dotenv()` does not override existing variables, so the bundled `.env` is redundant. Anyone with `lambda:GetFunction` can download the code and read the keys in plaintext.
4. **`cache.py` reads `CACHE_BUCKET` at import time, before `load_dotenv()` runs.** In `lambda_function.py` the order is `from tidal_functions import ...`, which imports `cache`, and only then `load_dotenv()`. It works today only because `CACHE_BUCKET` is a real Lambda env var. Anything set only in `.env` would be invisible to `cache.py`.
5. **The Function URL is public and unauthenticated**, with `lat`, `long` and `days` overridable by query string, calling two metered APIs at 12 to 16 seconds per invocation, many times an hour.

---

## Step 1: pipeline that only builds and updates code

No endpoint change, no role migration, no KMS re-plumbing. This captures most of the value: a correct Linux build and a dependency audit gate.

### Files to add

- `.github/workflows/ci.yml`, on `pull_request` and push to `main`:
  - `uv sync --locked`
  - `uv run flake8`
  - `uv audit --no-dev` (experimental, prints a warning unless passed `--preview-features audit-command`)
- `.github/workflows/deploy.yml`, on push to `main` and `workflow_dispatch`:
  - build the bundle on `ubuntu-latest`
  - `aws lambda update-function-code --function-name Tidal --region ap-southeast-2 --zip-file fileb://lambda-bundle.zip`

### Build command

Prefer `sam build` once Step 2 lands. Until then, resolve for the target platform explicitly so the build is correct regardless of the runner:

```
uv export --no-dev --no-hashes --python-platform x86_64-manylinux_2_28
```

### Auth

Use GitHub OIDC into a dedicated IAM role, with a trust policy for `token.actions.githubusercontent.com` scoped to `repo:tuatara/tidal:ref:refs/heads/main` and a condition on the audience. Grant only `lambda:UpdateFunctionCode` on the one function ARN, plus `lambda:GetFunction` if needed. No long-lived access keys in repo secrets.

### Constraints

- Never call `update-function-configuration` from the pipeline. A partial payload will clobber the CMK-encrypted environment variables, and they cannot be read back to recover them.
- Remove `.env` from the zip in whatever build script remains, per finding 3.

---

## Step 2: adopt into a SAM stack (optional)

CloudFormation has no adopt-by-name behaviour. Declaring `AWS::Lambda::Function` with `FunctionName: Tidal` makes the deploy attempt a create and fail, so it is import or recreate.

Recreate rather than import, because:

- The role is at `/service-role/` and was console-generated, so it is not manageable as an ordinary CloudFormation resource. The template needs a new role regardless.
- The environment variables are CMK-encrypted and cannot be read back through the API, so they must be re-entered. The template needs `KmsKeyId` on `Environment` or it will silently deploy plaintext variables.
- The function's only irreplaceable asset is its Function URL, and repointing it is a one-time manual re-subscribe on each device.

The template should create the function, a fresh execution role, its own Function URL, and the cache bucket, or reference the existing bucket by parameter. The cache is disposable, so a new bucket costs only a re-fetch.

---

## Step 3: Dependabot

- Add a committed `dependabot.yml` targeting the `uv` ecosystem so it understands `uv.lock`.
- Close PRs `#1` to `#4`; `uv lock --upgrade` supersedes all four.

---

## Open decisions

1. **Runtime: stay on `python3.13` or move to `3.14`?** This blocks Step 1. `pyproject.toml` declares `requires-python = ">=3.14"` and `.python-version` is `3.14`, but the deployed function is `python3.13`. Resolving dependencies for 3.14 and uploading to a 3.13 runtime will produce a confusing failure. Either build against the deployed runtime, or move the function to 3.14 first.
2. **Keep `deploy.sh` or delete it?** If the pipeline owns the build, a second, subtly different local build path invites drift.
3. **Is Step 2 needed at all?** If the goal is only a correct build plus an audit gate, Step 1 is sufficient and the infrastructure can stay undescribed.

---

## Verification

For Step 1, when it is picked up:

- Workflow dry run on a PR: `uv sync --locked`, `flake8` and `uv audit` all run, and the audit gate fails on a deliberately known-bad lock.
- Inspect the built bundle for platform tags. `unzip -l lambda-bundle.zip | grep -E "darwin|manylinux"` must show `manylinux` and never `darwin`.
- Confirm `.env` is absent from the bundle.
- After deploy, confirm the Function URL still serves a valid `.ics` and that env vars remain encrypted.
- Confirm the cache bucket continues receiving writes during an invocation.
