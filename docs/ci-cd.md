# CI/CD for this project

This is a learning guide, not a copy-paste pipeline. The goal is to understand the practice using **AI Doc QA**, then write the workflows yourself. Assistance means review and diagnosis of *your* files and logs — not a finished YAML recipe.

The repo is on GitHub: [Darsh-Bothra/AI-Doc-QnA](https://github.com/Darsh-Bothra/AI-Doc-QnA). GitHub Actions is the right first tool because it is already attached to the git host.

For product sequencing (tests, evals, deploy), see [roadmap.md](roadmap.md) Phase 0. For how the system is built, see [tech-architecture.md](tech-architecture.md). For local install and smoke tests, see the [README](../README.md).

Workflows in this repo live under [`.github/workflows/`](../.github/workflows/). Read them as *your* implementation of the stages below, not as canonical YAML to clone into the next project.

---

## 1. What CI/CD actually is

People mash the letters together. They are three different ideas.

**Continuous Integration (CI)**  
You merge often. After each push (or pull request), a **clean machine** that is not your laptop:

1. Checks out the code
2. Installs dependencies from lockfiles
3. Runs lint, typecheck, tests, maybe a build

If that fails, the change is not "done." The point is **fast feedback** and a shared definition of "works." Martin Fowler’s article is still the best explanation of *why*, not just *how*: [Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html).

**Continuous Delivery**  
Every green build on `main` is **releasable**. Deploying to production is a **deliberate** step (button, tag, or merge to a release branch). You *could* ship, but a human still decides. Fowler: [Continuous Delivery](https://martinfowler.com/bliki/ContinuousDelivery.html).

**Continuous Deployment**  
Every green build **goes to production automatically**. That is a later, optional choice. Do not start there.

Atlassian’s comparison: [CI vs CD vs Continuous Deployment](https://www.atlassian.com/continuous-delivery/principles/continuous-integration-vs-delivery-vs-deployment).

A **pipeline** is the sequence of those automated steps. GitHub Actions is one *implementation*. Jenkins, GitLab CI, CircleCI are others.

**Start with CI only.** Make every push prove the backend and frontend still work. Deploy comes after that loop is boring.

---

## 2. Mental model (learn this before YAML)

A GitHub Actions **workflow** is a YAML file in `.github/workflows/`. Read this until you can explain each word without looking: [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions).

| Word | Meaning |
|------|---------|
| **Event** (`on`) | What starts the run: `push`, `pull_request`, schedule, or a button |
| **Runner** (`runs-on`) | A rented VM, usually `ubuntu-latest`. Empty. Not your laptop. |
| **Job** | One VM’s work. Jobs run **in parallel** unless you say `needs:` |
| **Step** | A command (`run:`) or a reusable Action (`uses:`) |
| **Action** | Someone else’s packaged step, e.g. checkout, setup-python |
| **Service container** | Extra Docker containers next to the job (Postgres, Qdrant) |
| **Secret** | Encrypted env vars. Never committed. |

The runner does **not** have your `.env`, your Docker volumes, or your local Python. If CI only works because something is already on your machine, it is not CI.

YAML primer: [Learn YAML in Y Minutes](https://learnxinyminutes.com/docs/yaml/).

---

## 3. Snapshot of this project (why CI is not "just a YAML file")

What exists:

- FastAPI backend, Python 3.11, **uv** + `uv.lock`
- Next.js frontend with `lint` and `build` (check [`frontend/package.json`](../frontend/package.json) for a `test` script)
- Postgres 17 + Qdrant via [`docker-compose.yaml`](../docker-compose.yaml)
- Alembic migrations
- OpenAI for embeddings and ask
- GitHub remote on `main`

What CI cannot do until the repo supports it:

- A workflow that runs `uv run pytest` will fail until pytest is a **declared** project dependency and there are tests. That failure is **correct**.
- Real OpenAI calls in CI are slow, flaky, and cost money. Integration tests that hit the LLM should use a **fake client**. Keep a paid API key out of the workflow until you have a reason.

The first question is: can a stranger’s machine install and verify this project? The pipeline file is not the first file you write. The first file is a test that fails for a reason you understand, then passes on your machine, then you ask a second machine to run the same command.

---

## 4. Working agreement

- You write the workflow from the official docs.
- When it breaks, paste the workflow file, the **failed step’s log** (not a screenshot of the check), and what you expected vs what happened.
- Review should name the *concept* that was missed (event filter, working directory, lockfile vs `uv sync`, services vs localhost, secrets, `needs`, permissions). You fix it.
- Do not skip to deploy while CI is still the learning target.

---

## 5. Learning path

### Stage 0 — Read, then run GitHub’s own tutorial

Do these **in order**. Do not skim and then invent YAML.

1. [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions)
2. [Quickstart](https://docs.github.com/en/actions/get-started/quickstart) — their example workflow on a throwaway branch or tiny test repo is fine as a sandbox.
3. [Creating an example workflow](https://docs.github.com/en/actions/tutorials/create-an-example-workflow)
4. Optional: [GitHub Skills: Hello GitHub Actions](https://github.com/skills/hello-github-actions)

**Checkpoint:** Open the **Actions** tab, click a run, expand a step, and explain checkout vs `run`.

**Common miss:** putting the file in `github/workflows` (missing the leading `.`) or committing it only locally and wondering why GitHub did nothing.

### Stage 1 — Make "verify" a local command

CI is “run the same commands a teammate would.” If you cannot name those commands, you are not ready for YAML.

**Backend — decide and document three commands**, then add the missing tooling:

1. **Lint** — [Ruff](https://docs.astral.sh/ruff/)
2. **Tests** — [pytest](https://docs.pytest.org/), [pytest-asyncio](https://pytest-asyncio.readthedocs.io/), FastAPI [testing with httpx](https://fastapi.tiangolo.com/tutorial/testing/)
3. **Install in CI** — [Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/). Use `uv sync --frozen` / `--locked` so CI **fails** if `pyproject.toml` and `uv.lock` disagree.

Roadmap minimum test set (implement **one** first, not full RAG) — see [roadmap.md §4](roadmap.md#4-phase-0--correctness-and-foundations-1-week):

- register → login → authenticated request
- cross-tenant isolation (404, not 403 or 200)
- chunker unit tests
- ingest happy path, and a failure path that asserts `failed` + `error_message`

**Frontend — scripts already in [`frontend/package.json`](../frontend/package.json):**

- `npm ci` (lockfile-strict; not `npm install`)
- `npm run lint`
- `npm run build`

Official: [Building and testing Node.js](https://docs.github.com/en/actions/how-tos/use-cases-and-examples/building-and-testing/building-and-testing-nodejs), [npm ci](https://docs.npmjs.com/cli/v10/commands/npm-ci).

**Checkpoint:** On a **fresh** clone (or after deleting `.venv` and `frontend/node_modules`), those commands pass on your laptop.

**Common miss:** adding pytest to the workflow but not to declared project dependencies, so it works on the laptop because it was installed once by hand.

### Stage 2 — First real workflow: CI, not deploy

Read, then write the file from:

- [Building and testing Python](https://docs.github.com/en/actions/how-tos/use-cases-and-examples/building-and-testing/building-and-testing-python)
- [Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)
- [Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

**Design choices to make and defend:**

1. **Triggers.** Typical: `pull_request` + `push` to `main`. Should a push to a random feature branch also run? Cost vs feedback. See [Events that trigger workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows).
2. **Two jobs vs one.** Backend (`uv`, ruff, pytest) and frontend (`npm ci`, lint, build) are independent. Parallel jobs isolate failures. `working-directory: frontend` exists for a reason.
3. **Path filters later**, not first. Then: [paths / paths-ignore](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onpushpull_requestpull_request_targetpathspaths-ignore).
4. **Permissions.** Default to `contents: read`. [Secure use](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions).
5. **Pinning.** Prefer a versioned Action or a commit SHA. “Latest” is less reproducible. Action used here: [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv).

**Checkpoint:** Open a PR that **breaks** a test or lint on purpose. CI must go red. Then fix it. If you never saw a red X, you have not tested the pipeline.

**Common misses:**

- `working-directory` missing → npm runs at repo root and cannot find `package.json`
- `uv sync` without `--frozen`/`--locked` → CI silently resolves a different graph than `uv.lock`
- Caching cargo-culted from a blog until installs flake — add cache **after** a green run; Astral documents `enable-cache` on [setup-uv](https://docs.astral.sh/uv/guides/integration/github/)
- Secrets in YAML or in the repo. JWT for tests can be a dummy in workflow `env:`. Mock OpenAI. [Using secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions).

### Stage 3 — Tests that need Postgres / Qdrant

Unit tests (chunker, JWT, password hashing) need **no** Docker. Run those first.

When API tests talk to the DB, pick **one**:

| Approach | Read |
|----------|------|
| **Service containers** — GitHub starts Postgres (and you can add Qdrant) next to the job | [PostgreSQL service containers](https://docs.github.com/en/actions/use-cases-and-examples/using-containerized-services/creating-postgresql-service-containers), [About service containers](https://docs.github.com/en/actions/use-cases-and-examples/using-containerized-services/about-service-containers) |
| **testcontainers** — tests start Docker themselves | [testcontainers-python](https://testcontainers-python.readthedocs.io/) |

Service containers are easier to *see* in YAML. Testcontainers keep “how to get a DB” inside Python so local and CI share one path. Mixing both on day one is not useful.

Also: run **migrations in CI** (`uv run alembic upgrade head`) against that empty database. `POSTGRES_URL` must point at the service, not at `localhost:5433` from `docker-compose.yaml`. Port mapping is a frequent source of “it works locally.”

Do **not** call OpenAI from CI for the ingest happy path. Fake the embedding client; assert status `completed` on success and `failed` + `error_message` on a forced failure.

**Checkpoint:** A test that uses Postgres fails if the service is not healthy. Read the health-check `options` in GitHub’s Postgres tutorial until you know why they exist.

### Stage 4 — Make CI gate merges

A green badge nobody looks at is decoration.

GitHub: **Settings → Branches → Branch protection** (or rulesets) for `main`:

- Require a pull request
- Require the CI job(s) to pass

Docs: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

**Checkpoint:** You cannot click Merge on a red PR.

### Stage 5 — Continuous Delivery (only after CI is boring)

CD is a **second** workflow or a job with `needs: [backend, frontend]` and a condition such as `github.ref == 'refs/heads/main'`.

Sensible split for this app:

- **Frontend:** Vercel (or similar) can deploy on git push without much YAML. That is still CD. [Vercel Git integration](https://vercel.com/docs/git).
- **Backend:** needs an image or a host, Postgres, Qdrant, and secrets. Do **not** bake `OPENAI_API_KEY` into an image. [Roadmap Phase 2](roadmap.md#6-phase-2--serve-it-at-scale-and-instrument-it-3-weeks) (Dockerfile, health probes, Fly/Railway) is the sequence. Starting points: [Publishing Docker images](https://docs.github.com/en/actions/use-cases-and-examples/publishing-packages/publishing-docker-images), [Using secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions).

Do **not** auto-deploy the API to production on every commit until tests cover auth and **cross-tenant isolation**, and secrets live in GitHub Environments: [Using environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment).

Continuous **Deployment** of RAG + paid APIs is a product decision, not a learning milestone.

---

## 6. Target shape of a mature pipeline

Build toward this in slices. Do not treat it as a file to copy.

```text
PR opened / push
        │
        ├─ job: backend
        │     checkout → setup uv + Python 3.11
        │     uv sync --frozen (with test/lint extras)
        │     ruff / format check
        │     (optional) mypy
        │     pytest   [+ Postgres/Qdrant when tests need them]
        │
        └─ job: frontend
              checkout → setup-node + cache on package-lock
              npm ci
              lint
              next build

main green + you chose CD
        │
        ├─ frontend → Vercel (often automatic)
        └─ api     → image / host  (later; needs: backend)
```

Later ([roadmap Phase 1](roadmap.md#5-phase-1--make-retrieval-good-and-prove-it-3-weeks)): a job or step that runs the **eval harness** and fails on retrieval-metric regressions. That is CI earning its keep for a RAG project.

---

## 7. Resources

### Concepts

- [Martin Fowler — Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html)
- [Martin Fowler — Continuous Delivery](https://martinfowler.com/bliki/ContinuousDelivery.html)
- [Atlassian — CI vs Delivery vs Deployment](https://www.atlassian.com/continuous-delivery/principles/continuous-integration-vs-delivery-vs-deployment)
- Book: Jez Humble & Dave Farley, [*Continuous Delivery*](https://martinfowler.com/books/continuousDelivery.html)

### GitHub Actions (source of truth)

- [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions)
- [Quickstart](https://docs.github.com/en/actions/get-started/quickstart)
- [Creating an example workflow](https://docs.github.com/en/actions/tutorials/create-an-example-workflow)
- [Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Events that trigger workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)
- [Python CI](https://docs.github.com/en/actions/how-tos/use-cases-and-examples/building-and-testing/building-and-testing-python)
- [Node CI](https://docs.github.com/en/actions/how-tos/use-cases-and-examples/building-and-testing/building-and-testing-nodejs)
- [About service containers](https://docs.github.com/en/actions/use-cases-and-examples/using-containerized-services/about-service-containers)
- [Postgres service containers](https://docs.github.com/en/actions/use-cases-and-examples/using-containerized-services/creating-postgresql-service-containers)
- [Security hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [Using environments for deployment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Publishing Docker images](https://docs.github.com/en/actions/use-cases-and-examples/publishing-packages/publishing-docker-images)
- [GitHub Skills: Hello GitHub Actions](https://github.com/skills/hello-github-actions)

### This stack

- [uv + GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)
- [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Ruff](https://docs.astral.sh/ruff/)
- [testcontainers-python](https://testcontainers-python.readthedocs.io/)
- [npm ci](https://docs.npmjs.com/cli/v10/commands/npm-ci)
- [Next.js — CI Build Caching](https://nextjs.org/docs/app/guides/ci-build-caching)
- [Vercel Git integration](https://vercel.com/docs/git)
- [Learn YAML in Y Minutes](https://learnxinyminutes.com/docs/yaml/)

### In this repo

- [README](../README.md) — install, env vars, smoke tests
- [Technical architecture](tech-architecture.md)
- [Roadmap](roadmap.md) — Phase 0 tests/CI, Phase 1 evals in CI, Phase 2 deploy
- [`.github/workflows/`](../.github/workflows/) — workflows you write while learning

Skip random “complete YAML in 12 steps” posts until the official pages are familiar. Copy-paste pipelines teach a file, not the system.

---

## 8. First homework

1. Read Fowler’s [CI article](https://martinfowler.com/articles/continuousIntegration.html) and GitHub’s [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions).
2. Add **one** backend test and the pytest extra so `uv run pytest` is a real command.
3. Make `frontend` lint + build clean on a fresh `npm ci`.
4. Write a **minimal** workflow: triggered on PR, running those commands. No deploy. No five-version matrix.
5. Push a PR, watch [Actions](https://github.com/Darsh-Bothra/AI-Doc-QnA/actions), then push a commit that **fails** on purpose.
