# The Grateful Catholic Heart — Heart Audio Runner

This PUBLIC repository contains only a small, open-source recording engine for
**The Grateful Catholic Heart**. The actual website repository remains PRIVATE.

Daily sequence:
1. The existing TGCH devotional is created and saved to its protected archive.
2. Supabase independently verifies and publishes an unchanged original.
3. This GitHub Actions runner reads only that published devotional, verifies its
   exact SHA-256, and synthesizes an audio recording with the free Kokoro **af_heart** voice.
4. The resulting MP3 is uploaded to the TGCH audio service with a short-lived
   signed GitHub OIDC token. There are **no service-role keys or other secrets here**.
5. The TGCH site plays a verified MP3 in Safari; the original text is never changed.

Security: uploads are restricted by issuer, audience, *immutable* GitHub
repository-owner ID, repository ID, branch, and exact workflow reference.
An MP3 is published only once per verified daily SHA-256.

### Trigger a recording manually

GitHub → Actions → **TGCH — Heart daily MP3 from verified original**
→ **Run workflow**. Leave `devotional_date` empty for today's verified original,
or enter e.g. `2026-11-10` to backfill a specific date.

### Schedule

10:35 UTC daily (4:35 AM CST / 5:35 AM CDT). GitHub scheduled jobs can be
delayed. If no verified original exists, the job skips without creating content.

### Important notes

- The Python script transforms markup into *spoken* words only; it never
  updates, reformats, or regenerates the original devotional.
- Uses free Kokoro 82M `af_heart` on a standard public-repository runner.
- Public-repository scheduled workflows may be disabled after 60 days of no
  repository activity; check the Actions tab occasionally.
- The workflow reports failure if audio cannot be generated or authenticated.
