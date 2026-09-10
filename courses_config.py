"""
====================================================================
 ALL EDITABLE CONTENT LIVES IN THIS FILE.
 You should never need to touch bot.py to rename things, change
 prices, add a new course, or edit payment numbers.
====================================================================
"""

# ---------------------------------------------------------------
# 1. BOT IDENTITY
# ---------------------------------------------------------------
BOT_TITLE = "CourseBari 🔥"          # Shown conceptually in your messages
WELCOME_TEXT = (
    "👋 Welcome to *{title}*!\n\n"
    "Browse our courses below and tap a category to get started."
)

# ---------------------------------------------------------------
# 2. PAYMENT NUMBERS (shown to the buyer before they pay)
# ---------------------------------------------------------------
PAYMENT_METHODS_TEXT = (
    "💳 *Payment Methods*\n\n"
    "bKash (Send Money): `01951032061` ✅\n"
    "Nagad (Send Money): `01951032061` ✅\n\n"
    "After paying, tap *Payment Done* below, then send a screenshot "
    "of the transaction. Your access will be approved after we verify it."
)

# ---------------------------------------------------------------
# 3. CATEGORY / COURSE TREE
# ---------------------------------------------------------------
# Structure:
#   CATALOG["categories"] = list of top-level menu buttons
#   Each category has "courses" = list of course dicts
#
# To add/rename a course: just edit the dicts below.
# `id` must stay unique and have no spaces (used internally for callbacks).

CATALOG = {
    "categories": [
        
 {
            "id": "hsc26admission",
            "title": "🔥 HSC 2026 All Admission Course 🔥",
            "courses": [
                {
                    "id": "ACSUniversityCourse ",
                    "button_title": "📙 ACS (University) Course",
                    "price": "৳100",
                    "detail_text": (
                        "*ACS VERSITY + GST 2026*\n\n"
                        "✅ ক্লাস \n"
                        "✅ ক্লাস এর লেকচার শীট \n"
                        "✅ Archive Classes\n"
                        "✅ ক্লাস সাজানো থাকবে টপিক অনুযায়ী \n"
                        "✅ Practice Sheet\n\n"
                        "*Price: ৳100*"
                    ),
                    "delivery_text": (
                        "🎉 *Access approved!*\n\n"
                        "Here is your course link:\n"
                        "https://t.me/+TJp83JVlE7Q2OGNl\n\n"
                        "Join with the link above. Welcome aboard!"
                    ),
                },

                 {
                    "id": "PHUniversityCourse ",
                    "button_title": "📙 CAMPUS 6.0 — HSC 2025/26",
                    "price": "৳100",
                    "detail_text": (
                        "*CAMPUS 6.0 — HSC 2025/26*\n\n"
                        "✅ ক্লাস \n"
                        "✅ ক্লাস এর লেকচার শীট \n"
                        "✅ Archive Classes\n"
                        "✅ ক্লাস সাজানো থাকবে টপিক অনুযায়ী \n"
                        "✅ Practice Sheet\n\n"
                        "*Price: ৳100*"
                    ),
                    "delivery_text": (
                        "🎉 *Access approved!*\n\n"
                        "Here is your course link:\n"
                        "https://t.me/+TJp83JVlE7Q2OGNl\n\n"
                        "Join with the link above. Welcome aboard!"
                    ),
                },

              {
                    "id": "udvashUniversityCourse ",
                    "button_title": "📙 UDVASH VARSITY KA 2026",
                    "price": "৳0",
                    "detail_text": (
                        "*UDVASH VARSITY KA 2026*\n\n"
                        "📸 পেমেন্টের সময় যেকোনো একটি স্ক্রিনশট দিয়ে দিবেন \n"
                        "✅ ক্লাস \n"
                        "✅ ক্লাস এর লেকচার শীট \n"
                        "✅ Archive Classes\n"
                        "✅ ক্লাস সাজানো থাকবে টপিক অনুযায়ী \n"
                        "✅ Practice Sheet\n\n"
                        "*Price: ৳0*"
                    ),
                    "delivery_text": (
                        "🎉 *Access approved!*\n\n"
                        "Here is your course link:\n"
                        "https://t.me/coursebarifree\n\n"
                        "Join with the link above. Welcome aboard!"
                    ),
                },
             
            ],
        },
     
    ],
    # Extra static buttons on the main menu (support, channel, etc.)
    "extra_links": [
        {"title": "🆘 Support", "url": "https://t.me/jisan_roy"},
        {"title": "📢 Our Channel", "url": "https://t.me/CourseBari"},
    ],
}

# ---------------------------------------------------------------
# 4. ADMIN SETTINGS
# ---------------------------------------------------------------
# Telegram numeric user ID(s) allowed to Approve/Reject payments.
# Get your own numeric ID by messaging @userinfobot on Telegram.
ADMIN_IDS = [
    6752888962,  # <-- replace with your real Telegram numeric ID
]
