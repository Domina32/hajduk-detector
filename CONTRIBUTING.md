# Contributing

This is a solo project. There is no issue tracker, no discussion board and no
review process — the workflow below is what keeps `master` green.

## Workflow

Trunk-based, one branch per milestone:

```bash
git switch -c feat/m3-sheets
# ... work, with PLAN.md checkbox updates riding in the same commit ...
git switch master && git merge --ff-only feat/m3-sheets
```

`master` stays green: CI runs on every push and every pull request, and
`PLAN.md` is the checklist that says what is left to do.

## Before you commit

The `prek` hooks run on `git commit` and check formatting, lint, types and
typos. If a hook rewrites files, stage them again and commit.

Run the full check manually at any time:

```bash
just check
```

## Tests

Every change needs tests for the behaviour it adds or changes:

```bash
just test-backend
```

The suite runs against its own `app_test` database, so it never touches the
development data. CI enforces a coverage floor of 90%.

## Conventions

- Schemas live next to the models in `backend/app/models.py`.
- Routes live in `backend/app/api/routes/`.
- Business logic lives in `backend/app/services/`.
- No `TODO` comments in the code — unfinished work belongs in `PLAN.md`.
- Email templates are React Email components in `packages/react-email/`.
  Edit those, then run `npm run email:export`; the HTML under
  `backend/app/email-templates/` is generated and must not be edited by hand.
