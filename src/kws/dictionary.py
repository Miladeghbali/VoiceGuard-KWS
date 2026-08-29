DEFAULT_KWS_TERMS = {
    # Explicit sexual language
    "anal": 2.5,
    "blowjob": 3.0,
    "breast": 1.8,
    "clitoris": 3.0,
    "cock": 2.5,
    "cum": 2.5,
    "dick": 2.5,
    "dildo": 2.5,
    "ejaculate": 3.0,
    "erection": 2.0,
    "fingering": 3.0,
    "fuck": 2.2,
    "handjob": 3.0,
    "masturbat": 3.0,
    "moan": 1.8,
    "naked": 1.5,
    "nipple": 2.0,
    "nude": 1.5,
    "orgasm": 2.5,
    "penis": 2.5,
    "porn": 2.5,
    "pussy": 2.5,
    "sex": 1.8,
    "semen": 2.5,
    "sexual": 1.8,
    "sperm": 2.5,
    "suck": 1.3,
    "tits": 2.0,
    "vagina": 2.5,
    "vibrator": 2.5,
    "vulva": 2.5,

    # Profanity
    "ass": 0.8,
    "bastard": 0.7,
    "bitch": 0.8,
    "bullshit": 0.7,
    "shit": 0.7,
}


TERM_ALIASES = {
    "f*ck": "fuck",
    "f**k": "fuck",
    "fuk": "fuck",
    "phuck": "fuck",
    "sh1t": "shit",
    "b1tch": "bitch",
    "a55": "ass",
    "d1ck": "dick",
    "p0rn": "porn",
}


PHRASE_WEIGHTS = {
    r"\b(come|cum)\s+on\s+(me|your|her|him)\b": 3.0,

    r"\b(send|show)\s+(me\s+)?(nudes?|a\s+nude)\b": 3.0,

    r"\b(want|wanna)\s+have\s+sex\b": 3.0,

    r"\b(very\s+)?explicit\s+content\b": 2.0,
}