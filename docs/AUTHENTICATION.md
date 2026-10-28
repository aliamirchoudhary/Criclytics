# Project authentication and credential rotation

Never paste keys in chat, command arguments, tickets or screenshots. Save new
provider values only in local `.env` and the existing host's secret settings.
No paid plan, credit card, new cloud resource or repository write is required.

## RapidAPI

1. Sign into https://rapidapi.com/developer/dashboard using the existing account.
2. Select the Criclytics application, then Authorization.
3. Choose Add authorization and give the replacement a project-specific name.
4. Replace RAPIDAPI_KEY in the local `.env` and the existing backend Space secret.
5. Once the replacement is in place, remove the exposed old authorization.
6. Review usage without running bulk requests or enabling paid subscriptions.

[Official rotation steps](https://docs.rapidapi.com/v2/docs/keys-and-key-rotation).

## CricAPI / CricketData

1. Sign into the existing CricketData/CricAPI account and open its dashboard.
2. If key reset/regeneration is offered, use it and replace CRICAPI_KEY locally
   and in the backend Space's secrets.
3. If no reset control exists, contact provider support requesting revocation
   and replacement of the exposed key on the existing free account. Do not open
   a paid account or assume making a new account revokes the old key.
4. Record the completion time and service name, never the key value.

The provider documents its dashboard but a self-service rotation control could
not be verified. [Provider dashboard guide](https://cricketdata.org/how-to-get-started-with-cricket-data/).

## Upstash Redis

1. Sign into https://console.upstash.com/ and select the existing database.
2. Use its password-reset control. Preserve the database and stored data.
3. Copy the new TLS (`rediss://`) connection URL into REDIS_URL locally and in
   the backend Space's secret settings. Do not remove TLS.
4. Update any other applications sharing the database before expecting their
   connections to work. Resetting a password invalidates the old connection.
5. Keep the free plan; do not enable billing or create a replacement resource.

[Official reset-password operation](https://upstash.com/docs/devops/developer-api/redis/reset_password).

## Hugging Face inspection access

1. Open https://huggingface.co/settings/tokens while signed into the project owner.
2. Create a token named for local Criclytics inspection. Read-only access is
   enough for the current work; use fine-grained access restricted to the existing
   Space if the UI offers it. Do not enable inference billing or broad writes.
3. In a separate PowerShell terminal at the checkout root, use the project-local
   CLI installed during this session:

```powershell
$env:HF_HOME = "$PWD/.auth/huggingface"
./build/tools/Scripts/hf.exe auth login
```

4. Paste the token only into the CLI's hidden interactive prompt. Decline adding
   it to Git credentials. Keep `.auth/` ignored and out of Docker/public assets.
5. Leave the token in that local auth directory; report only that login is done.

[HF authentication](https://huggingface.co/docs/huggingface_hub/package_reference/authentication)
and [scopes](https://huggingface.co/docs/hub/security-tokens).
Uploading Space files creates remote repository commits: that remains forbidden
without explicit approval, even though service authentication is available.

## Existing backend secrets

At https://huggingface.co/spaces/aliamirchoudhary/criclytics-backend/settings,
replace provider keys under Secrets, not public Variables. Keep credentials out
of repository files. Updating configuration can restart the Space; preserve its
data and resource tier. Do not publish a new code revision through the HF API
without separate Git/repository approval.

## Cloudflare

Only if CLI login is needed, run `npx wrangler@4.152.0 login` yourself and approve
the browser flow for the existing account. Do not share a global API key. Worker
build configuration instructions remain in CLOUDFLARE_DEPLOYMENT.md. Current CLI
authentication has not been verified; local development does not depend on it.

## Status reporting

Tell the agent only which rotations/logins are complete. T001 remains pending
until revocation and production containment are actually verified. A successful
HEAD response on a private path can be a fallback page; status 200 alone does
not prove secret disclosure. Current HEAD-only checks are in
`docs/audit/containment-2026-10-28.json`; no secret bodies were retrieved.
