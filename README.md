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
