# TGCH — No-ZIP Cloudflare Pages automated deployments

**Existing production project:** `the-grateful-catholic-heart` (Direct Upload)
**Existing production domain:** https://thegratefulcatholicheart.com
**Private source repo:** `handlinlearning/the-grateful-catholic-heart` (`main`, `site/`)
**Public CI runner:** This repo, `handlinlearning/tgch-heart-audio-runner`

Cloudflare does not convert an existing Direct Upload project to native Git
integration. This public GitHub Actions workflow uses Wrangler against the
**existing** Pages project; the private site repo remains private.

## One-time secrets in THIS public GitHub repository (Settings → Secrets and variables → Actions)

1. `TGCH_SOURCE_READ_TOKEN` — GitHub **fine-grained personal access token**,
   *only* for `handlinlearning/the-grateful-catholic-heart`,
   Repository permissions → **Contents: Read-only**. No other scopes.
2. `CLOUDFLARE_API_TOKEN` — Cloudflare Pages Edit token, restricted to
   your account. Use the token already configured for the private TGCH
   deploy workflow, or create/revoke a replacement securely.
3. `CLOUDFLARE_ACCOUNT_ID` — the account ID used by the working
   private TGCH deploy workflow (an ID, not a password).

Never paste secrets in a chat, README, issue, commit, file, or workflow output.
GitHub masks repository secrets. Only scheduled and owner-dispatched runs
use these credentials. No `pull_request` execution or artifact upload.

## Operation

The workflow `TGCH — automatic Cloudflare Pages (private source)` checks
the private `main` branch about every 15 minutes. If there is no new commit
and a previous run completed, it makes **no deployment**.

For changed source, it:
1. Fetches the private source with read-only credentials.
2. Verifies complete website files, JS and JSON, the preserved
   source devotional reader, formation data, Prayer Bell, and Heart player.
3. Downloads the original approved homepage image, checks its fixed SHA-256.
4. Deploys a **preview** to branch `tgch-ci-preview`.
5. Checks the preview release marker and essential pages.
6. Deploys to **production** of the existing project, with no DNS changes.
7. Checks the production release marker and essential pages.
8. Records only the **source commit SHA** in this public runner.
   No private source code/artifacts are committed or exposed here.

If any check fails, the workflow stops and does not record a successful
deployment. Preview verification is mandatory before production.

**Run the first deployment:** GitHub → Actions → `TGCH — automatic
Cloudflare Pages (private source)` → Run workflow. Leave `force_deploy`
false unless intentionally redeploying the same approved commit.

## Constraints

- Never put the TGCH private GitHub source or API tokens in this public repo.
- The original devotional, Prayer Bell service worker and formation data
  are locked by source fingerprints until explicitly reapproved.
- Existing 3:00 AM devotional and 4:00 AM archival automation are untouched.
- Site updates happen only when private GitHub `main` changes.
- A new direct-upload ZIP deployed manually will **not** change the source
  commit SHA. To make it the automated baseline, commit its reviewed
  changes into the private `site/` first.
