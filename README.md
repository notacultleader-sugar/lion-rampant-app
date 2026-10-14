# Lion Rampant App

A clickable mobile app prototype for [The Lion Rampant Scottish Pub](https://www.lionrampantpub.com/) in Maple Bay, BC.

Open `index.html` in a browser. The app runs inside a simulated phone that scales to fit any window.

## Screens

- **Home**: live open/closed status from the pub's hours, tonight's special and the week of specials, upcoming events, address and hours.
- **Menu**: the full menu from the pub's website, with search, section filters and favourites.
- **Events**: live bands, Music Bingo and Karaoke, with reminders and shuttle info.
- **Contact & Hours**: today's hours highlighted, kitchen hours, phone and email with copy buttons, Facebook and Instagram, directions, shuttle and house rules.
- **Gift cards**: sign in with Apple, Google or email; buy a card for yourself or a friend; tap a card to show a scan code at the bar, see the balance and history, or add a code.

## Prototype notes

- Sign-in and payments are simulated. No account is created, no money is charged and no email is sent.
- Events come from the pub's website. A GitHub Action (`.github/workflows/sync-events.yml`) runs `scripts/sync_events.py` every 6 hours, reads the events section of lionrampantpub.com and commits any changes to `events.json`. The app loads `events.json` when it opens, so new events appear without touching the app code. Only upcoming events are shown; past ones drop off automatically.
- Menu prices are not shown because the website does not list them; daily special prices are real.
- State (sign-in, cards, favourites, reminders) is saved in the browser's localStorage only.

## Holiday and special hours (for staff)

Staff update special hours in a Google Sheet, never in this repo.

1. The sheet has these columns in row 1: `Date | Open? | Opens | Closes | Note`
   - `Dec 25 | No | | | Merry Christmas!`
   - `Dec 31 | Yes | 11am | 1am | New Year's Eve party`
2. The sheet is published as CSV (File > Share > Publish to web > CSV), and that link is saved in the repo secret `SHEET_CSV_URL`.
3. Every hour, `scripts/sync_special_hours.py` reads the sheet and updates `special-hours.json`. The app shows upcoming special hours on the home screen and Hours page, and uses them for the open/closed badge.

Rows that can't be read are skipped (the run log says which). Past dates drop off automatically.
