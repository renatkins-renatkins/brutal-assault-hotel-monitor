# Brutal Assault 2027 Hotel Monitor

This small script watches Brutal Assault's **Hotels** page, not camps.

It checks two things:

1. Whether a new **BA 2027 Hotel** product appears.
2. Whether any BA 2027 hotel product appears in the site's **Show available only** view.

When something useful changes, it sends a phone push notification through ntfy.

## Files

- `monitor.py` — the Python monitor
- `state.json` — today's starting baseline
- `.github/workflows/check.yml` — runs the monitor automatically on GitHub Actions

## Setup

### 1. Create an ntfy topic

Install the ntfy app on your phone.

Subscribe to a long, hard-to-guess topic name, for example:

`ba-hotels-2027-your-random-words-739184`

Keep this topic private in the sense that you do not post it publicly. ntfy.sh topics are effectively unlisted rather than password-protected by default.

### 2. Create a GitHub repository

Create a new repository on GitHub.

A public repository gets free standard GitHub Actions usage. If you prefer a private repository, GitHub applies the Actions allowance associated with your account plan.

Upload all the files in this folder, preserving the `.github/workflows/check.yml` path.

### 3. Add the ntfy topic as a GitHub secret

In the repository:

Settings → Secrets and variables → Actions → New repository secret

Name:

`NTFY_TOPIC`

Value:

your ntfy topic name only, not the full URL.

### 4. Test it manually

Open:

Actions → Monitor Brutal Assault hotels → Run workflow

For the first test, tick **Send a test phone notification**, then run it.
You should receive a push notification saying the monitor test succeeded.

Open the run and check that all steps are green.

The script should report the number of 2027 hotel listings it found. If nothing is available, it will say there were no alert-worthy changes.

### 5. Test the phone notification

The safest test is temporarily to edit `state.json` and remove one of the entries under `known_hotels`, commit the change, then run the workflow manually.

The monitor should treat that room as a newly discovered listing and send you a push notification.

After the test, let the workflow write the correct state back.

## What it monitors

Full hotels page:

https://brutalassault.cz/en/ac-71/hotels

Available-only hotels page:

https://brutalassault.cz/en/ac-71/hotels?show=ao

It deliberately ignores camps and ignores the stray BA 2026 hotel listing currently visible on the site.

## Notes

GitHub scheduled workflows are not guaranteed to run at the exact second shown in the cron schedule and can occasionally be delayed.

If Brutal Assault later changes the structure of its HTML substantially, the script may need a small selector/parser update. The monitor intentionally searches for links containing `BA 2027 Hotel` rather than relying on fragile CSS class names.


## Staying active

GitHub automatically disables scheduled workflows in a public repository after
60 days with no repository activity. The included `keepalive.yml` workflow makes
one tiny commit on the first day of each month so the hotel monitor does not
silently stop while you are waiting for accommodation releases.
