"""Mapa de emojis para substituição de shortcodes Markdown."""

from typing import Dict


# Dicionário abrangente de emojis (Extended Syntax - Emoji Shortcodes)
EMOJI_MAP: Dict[str, str] = {
    ":smile:": "😄", ":grin:": "😁", ":joy:": "😂", ":rofl:": "🤣",
    ":smiley:": "😃", ":laughing:": "😆", ":sweat_smile:": "😅",
    ":wink:": "😉", ":blush:": "😊", ":innocent:": "😇",
    ":heart_eyes:": "😍", ":kissing_heart:": "😘", ":relaxed:": "☺️",
    ":yum:": "😋", ":stuck_out_tongue:": "😛", ":sunglasses:": "😎",
    ":thinking:": "🤔", ":neutral_face:": "😐", ":expressionless:": "😑",
    ":unamused:": "😒", ":rolling_eyes:": "🙄", ":grimacing:": "😬",
    ":relieved:": "😌", ":pensive:": "😔", ":sleepy:": "😪",
    ":sleeping:": "😴", ":mask:": "😷", ":confused:": "😕",
    ":worried:": "😟", ":slightly_frowning_face:": "🙁", ":frowning_face:": "☹️",
    ":open_mouth:": "😮", ":hushed:": "😯", ":astonished:": "😲",
    ":flushed:": "😳", ":frowning:": "😦", ":anguished:": "😧",
    ":fearful:": "😨", ":cold_sweat:": "😰", ":disappointed_relieved:": "😥",
    ":cry:": "😢", ":sob:": "😭", ":scream:": "😱",
    ":angry:": "😠", ":rage:": "😡", ":skull:": "💀",
    ":poop:": "💩", ":clown_face:": "🤡", ":ghost:": "👻",
    ":alien:": "👽", ":robot:": "🤖", ":sparkles:": "✨",
    ":star:": "⭐", ":star2:": "🌟", ":dizzy:": "💫",
    ":boom:": "💥", ":collision:": "💥", ":fire:": "🔥",
    ":heart:": "❤️", ":orange_heart:": "🧡", ":yellow_heart:": "💛",
    ":green_heart:": "💚", ":blue_heart:": "💙", ":purple_heart:": "💜",
    ":broken_heart:": "💔", ":two_hearts:": "💕", ":revolving_hearts:": "💞",
    ":thumbsup:": "👍", ":+1:": "👍", ":thumbsdown:": "👎", ":-1:": "👎",
    ":clap:": "👏", ":wave:": "👋", ":raised_hands:": "🙌",
    ":pray:": "🙏", ":handshake:": "🤝", ":muscle:": "💪",
    ":point_up:": "☝️", ":point_down:": "👇", ":point_left:": "👈",
    ":point_right:": "👉", ":fist:": "✊", ":punch:": "👊",
    ":v:": "✌️", ":ok_hand:": "👌", ":eyes:": "👀",
    ":tada:": "🎉", ":confetti_ball:": "🎊", ":balloon:": "🎈",
    ":rocket:": "🚀", ":helicopter:": "🚁", ":car:": "🚗",
    ":bulb:": "💡", ":memo:": "📝", ":book:": "📖", ":books:": "📚",
    ":bookmark:": "🔖", ":link:": "🔗", ":paperclip:": "📎",
    ":warning:": "⚠️", ":check:": "✅", ":white_check_mark:": "✅",
    ":x:": "❌", ":negative_squared_cross_mark:": "❎",
    ":question:": "❓", ":grey_question:": "❔", ":exclamation:": "❗",
    ":grey_exclamation:": "❕", ":pin:": "📌", ":round_pushpin:": "📍",
    ":gear:": "⚙️", ":wrench:": "🔧", ":hammer:": "🔨",
    ":lock:": "🔒", ":unlock:": "🔓", ":key:": "🔑",
    ":bell:": "🔔", ":no_bell:": "🔕", ":tag:": "🏷️",
    ":folder:": "📁", ":file:": "📄", ":calendar:": "📅",
    ":clock:": "⏰", ":100:": "💯", ":art:": "🎨",
    ":coffee:": "☕", ":tea:": "🍵", ":pizza:": "🍕",
    ":beer:": "🍺", ":wine_glass:": "🍷", ":cake:": "🎂",
    ":apple:": "🍎", ":zap:": "⚡", ":sunny:": "☀️",
    ":cloud:": "☁️", ":umbrella:": "☔", ":snowflake:": "❄️",
}


def replace_emojis(text: str) -> str:
    """Substitui todos os shortcodes :emoji: pelo caractere Unicode correspondente.

    :param text: Texto contendo shortcodes de emoji
    :return: Texto com shortcodes substituídos por caracteres emoji
    """
    for shorthand, emoji_char in EMOJI_MAP.items():
        if shorthand in text:
            text = text.replace(shorthand, emoji_char)
    return text
