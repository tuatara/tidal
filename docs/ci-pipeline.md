# CI/CD pipeline

## What is in place

| File | Purpose |
|---|---|
| `.github/workflows/ci.yml` | On pull request and push to `main`: `uv sync --locked`, `uv run flake8`, `uv audit --no-dev`, then builds the bundle and asserts it is Linux-native and free of `.env`. |
| `.github/workflows/deploy.yml` | On push to `main` and manual dispatch: audits, assumes the deploy role via OIDC, builds, runs `update-function-code`, then smoke tests the Function URL. |
| `deploy.sh` | The single build path, used locally and by both workflows. |

`deploy.sh` targets `x86_64-manylinux_2_28` for Python 3.14, excludes the dev
dependency group, and no longer bundles `.env`. That fixes the original problem,
where a bundle built on macOS shipped `charset_normalizer/*-darwin.so` into the
Linux runtime.

### Build command

`uv export` has no `--python-platform` flag, contrary to an earlier revision of
this document. The flag belongs on the install step:

```
uv export --no-dev --no-hashes \
  | uv pip install -r - --target deploy \
      --python-version 3.14 \
      --python-platform x86_64-manylinux_2_28
```

The platform must be set explicitly. A macOS build would otherwise resolve darwin
wheels, and a build on `ubuntu-latest` could resolve wheels newer than the glibc
that Amazon Linux 2023 provides.

`uv audit` prints an experimental-command warning. That is expected. The preview
flag that silences it is deliberately not used, to avoid coupling CI to a flag
name that may change.

## One-time AWS setup

These steps need a profile with write access. The credentials used during this
work were read-only and have since expired.

### 1. OIDC identity provider

Check first, then create only if absent:

```
aws iam list-open-id-connect-providers
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com
```

### 2. Deploy role

Create `tidal-github-deploy` with this trust policy. The `sub` condition is what
stops a pull request, or any other branch, from assuming the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::036700217332:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:tuatara/tidal:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Permission policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:UpdateFunctionCode",
      "Resource": "arn:aws:lambda:ap-southeast-2:036700217332:function:Tidal"
    },
    {
      "Effect": "Allow",
      "Action": "lambda:GetFunctionUrlConfig",
      "Resource": "arn:aws:lambda:ap-southeast-2:036700217332:function:Tidal"
    }
  ]
}
```

A possible third statement for `kms:Decrypt` is described below.

### 3. Bump the runtime to Python 3.14

```
aws lambda update-function-configuration \
  --function-name Tidal \
  --region ap-southeast-2 \
  --runtime python3.14
```

Omitting `--environment` leaves the existing variables untouched. Never pass a
partial `--environment` to this call: the variables are encrypted with a
customer-managed key and cannot be read back to recover them.

Do this before the first pipeline deploy. The currently deployed bundle was built
for 3.13, and its only compiled artifact is `charset_normalizer`, which falls back
to a pure-Python implementation when the extension does not match, so there is no
window where the function stops working.

## The `kms:Decrypt` question

The function's environment variables are encrypted with customer-managed KMS key
`f691836b-0e93-4173-b7a5-0eff8e13b5ad`. Lambda requires `kms:Decrypt` for any
caller reading that configuration: `get-function-configuration` fails without it,
which was confirmed against the live function.

It is not confirmed whether `update-function-code` needs it too, because the
credentials available during this work expired before that could be tested. If the
first deploy run fails with a KMS access-denied error, add:

```json
{
  "Effect": "Allow",
  "Action": "kms:Decrypt",
  "Resource": "arn:aws:kms:ap-southeast-2:036700217332:key/f691836b-0e93-4173-b7a5-0eff8e13b5ad"
}
```

That also lets the workflow read the API keys back out through
`get-function-configuration`. The OIDC subject condition bounds who can trigger
that, but it is a real widening of the role.

## Findings worth keeping in view

1. **`cache.py` reads `CACHE_BUCKET` at import time, before `load_dotenv()` runs.** In `lambda_function.py` the order is `from tidal_functions import ...`, which imports `cache`, and only then `load_dotenv()`. It works today only because `CACHE_BUCKET` is a real Lambda environment variable. Anything set only in `.env` would be invisible to `cache.py`.
2. **The Function URL is public and unauthenticated**, with `lat`, `long` and `days` overridable by query string, calling two metered APIs at 12 to 16 seconds per invocation.
3. **`boto3` and `botocore` are provided by the Lambda runtime.** Bundling them accounts for most of the bundle's size.

## Follow-ups, not done

- **Move the API keys into Secrets Manager.** They are CMK-encrypted Lambda environment variables today, which works, but it forces the `kms:Decrypt` conversation above. Referencing them as `{{resolve:secretsmanager:...}}` and resolving with `asm-exec` would remove the keys from the function configuration entirely.
- **Drop `boto3`/`botocore` from the bundle**, since the runtime provides them. Confirm the runtime version is acceptable first.
- **Switch Dependabot to the `uv` ecosystem** with a committed `dependabot.yml`, and close PRs `#1` to `#4`, which `uv lock --upgrade` supersedes.
- **Delete `feature/actions-hack`**, the abandoned October 2024 attempt copied from a work project (multi-account matrix, `GithubActionsRole`, `web`/`worker`/`lp` environments).
- **Consider requiring CI before merge to `main`** through branch protection. The deploy workflow audits the lock before deploying, but a direct push to `main` still deploys.
- **The SAM stack**, the deferred second step, remains undone. If it is picked up, recreate rather than import: the execution role sits at `/service-role/` and is not manageable as an ordinary CloudFormation resource, and the environment variables cannot be read back to populate a template.

## Deployed state for reference

Account `036700217332`, region `ap-southeast-2`, as at 2026-09-12.

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

The S3 cache is live: 141 `astro/` and 141 `tides/` objects, written in bursts,
with invocations landing in the same second as the writes.

The deployed artifact hashes to
`b00fd9dc80acde4f8427657d5dcf3eae8862aa704470153254ac9c0fd9840111`, byte-identical
to the local `lambda-bundle.zip` as it stood before this work: the May bundle
containing `requests` 2.32.5, which is why the urllib3 2.6.3 advisories and the
darwin extension were both live in production.
