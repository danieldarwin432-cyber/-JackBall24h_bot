import logging
import os
from datetime import date

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import api_football as af

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Football prediction bot.\n\n"
        "/today [league] - list today's fixtures (e.g. /today epl)\n"
        "/predict <fixture_id> - get a prediction for a fixture\n"
        "/leagues - show supported league shortcuts"
    )


async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = [f"{key} -> {league_id}" for key, league_id in af.LEAGUES.items()]
    await update.message.reply_text("Supported league shortcuts:\n" + "\n".join(lines))


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    league_key = context.args[0].lower() if context.args else None
    league_id = af.LEAGUES.get(league_key) if league_key else None

    if league_key and not league_id:
        await update.message.reply_text(f"Unknown league '{league_key}'. Try /leagues for options.")
        return

    today_str = date.today().isoformat()
    try:
        fixtures = af.get_fixtures_by_date(today_str, league=league_id)
    except Exception:
        logger.exception("Fixtures request failed")
        await update.message.reply_text("Couldn't reach the football API. Try again shortly.")
        return

    if not fixtures:
        await update.message.reply_text("No fixtures found for today with that filter.")
        return

    lines = []
    for f in fixtures[:20]:
        fixture = f["fixture"]
        teams = f["teams"]
        lines.append(
            f"#{fixture['id']} {teams['home']['name']} vs {teams['away']['name']} "
            f"- {fixture['date'][11:16]} UTC"
        )

    text = "Today's fixtures:\n" + "\n".join(lines)
    if len(fixtures) > 20:
        text += f"\n...and {len(fixtures) - 20} more. Narrow with a league, e.g. /today epl"
    text += "\n\nUse /predict <fixture_id> to get a prediction."
    await update.message.reply_text(text)


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /predict <fixture_id>\nGet fixture ids from /today")
        return

    try:
        fixture_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Fixture id must be a number. Get one from /today")
        return

    try:
        pred = af.get_prediction(fixture_id)
    except Exception:
        logger.exception("Prediction request failed")
        await update.message.reply_text("Couldn't reach the football API. Try again shortly.")
        return

    if not pred:
        await update.message.reply_text("No prediction available for that fixture id.")
        return

    teams = pred["teams"]
    predictions = pred["predictions"]
    comparison = pred.get("comparison", {})

    home_name = teams["home"]["name"]
    away_name = teams["away"]["name"]
    winner = predictions.get("winner", {}).get("name") or "No clear favorite"
    advice = predictions.get("advice", "No advice available")
    percent = predictions.get("percent", {})

    lines = [
        f"{home_name} vs {away_name}",
        f"Predicted result: {winner}",
        f"Win probability - home: {percent.get('home', 'n/a')}, "
        f"draw: {percent.get('draw', 'n/a')}, away: {percent.get('away', 'n/a')}",
        f"Advice: {advice}",
    ]

    form = comparison.get("form", {})
    if form:
        lines.append(f"Form comparison - home: {form.get('home', 'n/a')}, away: {form.get('away', 'n/a')}")

    await update.message.reply_text("\n".join(lines))


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leagues", leagues))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("predict", predict))

    logger.info("Bot starting (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
