# GitHub Settings Parity Report — HSB Boden

Date: 2026-07-04

Source: `cherinojoel-lang/hsb-boden`  
Target: `HSBHexagon/hsb-boden`

## Result

This run copied safe repository settings from source to target and inventoried manual-only settings.

## Copied / enforced

- Repository metadata and merge settings
- Default branch
- Actions permissions where available
- Workflow permissions where available
- Vulnerability alerts
- Dependabot automated security fixes
- Main branch protection core fields if source has protection
- Environment names and basic environment settings
- Labels
- Milestones

## Not copied automatically

These cannot be safely copied without secret values or external app UI access:

- Actions secret values
- Environment secret values
- Webhook secrets
- Deploy-key private keys
- External GitHub App authorizations such as Jules / Google / Vercel / Cloudflare
- Owner-level app installations
- OAuth app grants
- Billing/account-level settings

## Source repo metadata

```json
{
  "full_name": "cherinojoel-lang/hsb-boden",
  "private": false,
  "visibility": "public",
  "default_branch": "main",
  "allow_auto_merge": true,
  "allow_merge_commit": true,
  "allow_squash_merge": true,
  "allow_rebase_merge": true,
  "allow_update_branch": false,
  "delete_branch_on_merge": false,
  "has_issues": true,
  "has_projects": true,
  "has_wiki": true,
  "has_discussions": false
}
```

## Target repo metadata after run

```json
{
  "full_name": "HSBHexagon/hsb-boden",
  "private": false,
  "visibility": "public",
  "default_branch": "main",
  "allow_auto_merge": true,
  "allow_merge_commit": true,
  "allow_squash_merge": true,
  "allow_rebase_merge": true,
  "allow_update_branch": false,
  "delete_branch_on_merge": false,
  "has_issues": true,
  "has_projects": true,
  "has_wiki": true,
  "has_discussions": false
}
```

## Source rulesets

```json
[
  {
    "id": 17620728,
    "name": "Protect Main",
    "target": "branch",
    "source_type": "Repository",
    "source": "cherinojoel-lang/hsb-boden",
    "enforcement": "active",
    "node_id": "RRS_lACqUmVwb3NpdG9yec5LIV6ozgEM3vg",
    "_links": {
      "self": {
        "href": "https://api.github.com/repos/cherinojoel-lang/hsb-boden/rulesets/17620728"
      },
      "html": {
        "href": "https://github.com/cherinojoel-lang/hsb-boden/rules/17620728"
      }
    },
    "created_at": "2026-06-12T21:41:54.538+02:00",
    "updated_at": "2026-06-13T00:33:44.350+02:00"
  }
]
```

## Target rulesets

```json
[]
```

## Source environments

```json
[
  "production"
]
```

## Target environments

```json
[
  "production"
]
```

## Source secret names

```
CLOUDFLARE_ACCOUNT_ID	2026-06-12T21:01:19Z
CLOUDFLARE_API_TOKEN	2026-06-12T21:02:47Z
```

## Target secret names

```
CLOUDFLARE_ACCOUNT_ID	2026-07-02T15:45:14Z
CLOUDFLARE_API_TOKEN	2026-07-02T15:45:15Z
```

## Source variable names

```

```

## Target variable names

```

```

## Source webhooks

```json
[]
```

## Target webhooks

```json
[]
```

## Source deploy keys

```json
[]
```

## Target deploy keys

```json
[]
```

## Required manual verification

1. GitHub UI: Installed GitHub Apps for HSBHexagon.
2. Jules / Google integration: verify HSBHexagon/hsb-boden visible.
3. Cloudflare Git integration: verify connected to HSBHexagon/hsb-boden if used.
4. Vercel: only verify if intentionally used.
5. Secrets: compare names only; values must be re-entered manually if missing.
6. Production environment approval: verify in GitHub UI if reviewer rules exist.

## Local canonical path

```
/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
```

