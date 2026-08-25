# Setup (Mac + GitHub Desktop)

## 1. Create and clone the repository

1. On GitHub, click **New repository**.
2. Name it `robinhood-etf-research-agent`.
3. Make it **Private** initially.
4. Do not add a README, `.gitignore`, or license.
5. Click **Create repository**.
6. Open GitHub Desktop and choose **File → Clone repository**.
7. Select `robinhood-etf-research-agent` and click **Clone**.

## 2. Put the project on GitHub

1. Unzip the downloaded project and show hidden files with `Command + Shift + .`.
2. In GitHub Desktop choose **Repository → Show in Finder**.
3. Copy everything *inside* the unzipped project into the cloned repository folder.
4. Return to GitHub Desktop and commit with summary `Initial read-only ETF research agent`.
5. Click **Push origin**.

## 3. Allow the workflow to save paper state

In the GitHub repository:

1. Open **Settings → Actions → General**.
2. Under **Workflow permissions**, choose **Read and write permissions**.
3. Click **Save**.

The workflow also declares only the permissions it needs. It cannot access Robinhood.

## 4. Enable the dashboard

1. Open **Settings → Pages**.
2. Under **Build and deployment**, set Source to **GitHub Actions**.

## 5. Start the evaluation

1. Open **Actions**.
2. Choose **ETF paper research**.
3. Click **Run workflow → Run workflow**.
4. Wait for both jobs to turn green.

The first successful run creates the evaluation start time. The scheduled workflow then runs after the U.S. close on weekdays. GitHub schedules are best-effort, so an occasional delayed run is normal.

The first run downloads up to ten years of daily history for each ETF so all 100 techniques have enough warm-up data. This does not backdate the paper portfolio; hypothetical transactions begin only on the first successful run.

## What to verify

After the first run, open `state/evaluation.json` and confirm:

- `duration_days` is `30`.
- `started_at` is populated.
- `complete` is `false`.

On later runs, `started_at` must remain unchanged and `runs_observed` must rise. The dashboard URL appears in the completed **deploy** job.

## Resetting the paper test

To intentionally begin again, delete generated files inside `state/` but keep `state/.gitkeep`, then replace `docs/index.html` with the checked-in placeholder. Commit and push those changes. Never reset midway merely because performance is poor; that destroys the usefulness of the evaluation.
