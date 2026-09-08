"""
Telegram course-selling bot.

Flow:
  /start -> Main menu (categories)
  tap category -> list of courses
  tap course -> course detail + "Buy / Payment Info" button
  tap "Payment Info" -> shows payment numbers + "Payment Done" button
  tap "Payment Done" -> bot asks buyer to send a screenshot
  buyer sends photo -> forwarded to ADMIN_IDS with Approve/Reject buttons
  admin taps Approve -> buyer automatically receives delivery_text (access link)
  admin taps Reject  -> buyer is notified politely

All editable text/course data lives in courses_config.py — this file
only contains logic and should not need to change for content edits.
"""

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db
from courses_config import (
    ADMIN_IDS,
    BOT_TITLE,
    CATALOG,
    PAYMENT_METHODS_TEXT,
    WELCOME_TEXT,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# Helpers to find a course/category by id
# ---------------------------------------------------------------
def find_category(cat_id: str):
    for cat in CATALOG["categories"]:
        if cat["id"] == cat_id:
            return cat
    return None


def find_course(course_id: str):
    for cat in CATALOG["categories"]:
        for course in cat["courses"]:
            if course["id"] == course_id:
                return course
    return None


# ---------------------------------------------------------------
# Keyboard builders
# ---------------------------------------------------------------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for cat in CATALOG["categories"]:
        rows.append([InlineKeyboardButton(cat["title"], callback_data=f"cat:{cat['id']}")])
    extra_row = []
    for link in CATALOG.get("extra_links", []):
        extra_row.append(InlineKeyboardButton(link["title"], url=link["url"]))
    if extra_row:
        rows.append(extra_row)
    return InlineKeyboardMarkup(rows)


def category_keyboard(cat_id: str) -> InlineKeyboardMarkup:
    cat = find_category(cat_id)
    rows = []
    for course in cat["courses"]:
        label = f"{course['button_title']} — {course['price']}"
        rows.append([InlineKeyboardButton(label, callback_data=f"course:{course['id']}")])
    rows.append([InlineKeyboardButton("⬅ Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def course_detail_keyboard(course_id: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("💳 Buy / Payment Info", callback_data=f"pay:{course_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(rows)


def payment_keyboard(course_id: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("✅ Payment Done", callback_data=f"done:{course_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(rows)


def admin_review_keyboard(request_id: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{request_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{request_id}"),
        ]
    ]
    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = WELCOME_TEXT.format(title=BOT_TITLE)
    await update.message.reply_text(
        text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN
    )


# ---------------------------------------------------------------
# Callback query (button press) handler
# ---------------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text(
            WELCOME_TEXT.format(title=BOT_TITLE),
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data.startswith("cat:"):
        cat_id = data.split(":", 1)[1]
        cat = find_category(cat_id)
        await query.edit_message_text(
            f"*{cat['title']}*\n\nChoose a course:",
            reply_markup=category_keyboard(cat_id),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data.startswith("course:"):
        course_id = data.split(":", 1)[1]
        course = find_course(course_id)
        await query.edit_message_text(
            course["detail_text"],
            reply_markup=course_detail_keyboard(course_id),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data.startswith("pay:"):
        course_id = data.split(":", 1)[1]
        await query.edit_message_text(
            PAYMENT_METHODS_TEXT,
            reply_markup=payment_keyboard(course_id),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data.startswith("done:"):
        course_id = data.split(":", 1)[1]
        user_id = query.from_user.id

        db.set_awaiting_screenshot(user_id, course_id)

        await query.edit_message_text(
            "📸 Please *send a screenshot* of your payment now as a photo message.\n\n"
            "We'll review it and approve your access shortly.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data.startswith("approve:") or data.startswith("reject:"):
        await handle_admin_decision(update, context, data)
        return


# ---------------------------------------------------------------
# Photo handler — buyer sends payment screenshot
# ---------------------------------------------------------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    course_id = db.pop_awaiting_screenshot(user.id)

    if not course_id:
        # User sent a photo without going through the "Payment Done" flow
        await update.message.reply_text(
            "If this is a payment screenshot, please first tap *Buy / Payment Info* "
            "on a course, then *Payment Done*, then send the screenshot.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    course = find_course(course_id)
    request_id = f"{user.id}:{course_id}:{update.message.message_id}"

    db.add_pending_approval(
        request_id=request_id,
        user_id=user.id,
        username=user.username or user.first_name,
        course_id=course_id,
    )

    caption = (
        f"🧾 *New payment claim*\n\n"
        f"User: @{user.username or user.first_name} (ID: `{user.id}`)\n"
        f"Course: {course['button_title']}\n"
        f"Price: {course['price']}\n\n"
        f"Approve or reject below."
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=update.message.photo[-1].file_id,
                caption=caption,
                reply_markup=admin_review_keyboard(request_id),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            logger.exception("Failed to notify admin %s", admin_id)

    await update.message.reply_text(
        "✅ Screenshot received! We'll confirm your access shortly."
    )


# ---------------------------------------------------------------
# Admin approve/reject
# ---------------------------------------------------------------
async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    query = update.callback_query

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("Not authorized.", show_alert=True)
        return

    action, request_id = data.split(":", 1)
    request = db.pop_pending_approval(request_id)

    if not request:
        await query.edit_message_caption(caption="⚠️ This request was already handled.")
        return

    user_id = request["user_id"]
    course = find_course(request["course_id"])

    if action == "approve":
        await context.bot.send_message(
            chat_id=user_id,
            text=course["delivery_text"],
            parse_mode=ParseMode.MARKDOWN,
        )
        await query.edit_message_caption(caption=f"✅ Approved — access sent to user {user_id}.")
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ We couldn't verify your payment. Please contact support "
                "with your transaction details."
            ),
        )
        await query.edit_message_caption(caption=f"❌ Rejected — user {user_id} notified.")


# ---------------------------------------------------------------
# Tiny HTTP server — exists ONLY so Render's free "Web Service" tier
# sees something listening on $PORT and doesn't mark the deploy as
# failed. It does nothing except reply 200 OK. An external uptime
# monitor (e.g. UptimeRobot) pinging this URL every few minutes is
# what keeps the free service from spinning down after inactivity.
# ---------------------------------------------------------------
class _HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running.")

    def log_message(self, format, *args):
        pass  # silence default request logging, keep logs clean


def _start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), _HealthCheckHandler)
    logger.info("Health-check server listening on port %s", port)
    server.serve_forever()


# ---------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------
def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Set the BOT_TOKEN environment variable (get it from @BotFather)."
        )

    db.init_db()

    # Run the tiny health-check server in a background thread so Render's
    # free Web Service tier sees a listening port, while the bot itself
    # runs normally via polling on the main thread.
    threading.Thread(target=_start_health_server, daemon=True).start()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
