# UX Flow Map and ASCII Wireframes

This document shows the user journey, message flows, and screen-by-screen content for the Telegram bot that collects name, age, and address.

---

## Flow map

```
                       +-------------------+
User starts chat  --->  |  /start received  |
                       +----------+--------+
                                  |
                                  v
                        +-----------------------+
                        | Consent + intro text  |
                        | Ask: full name        |
                        +-----------+-----------+
                                    |
                         valid name | invalid name
                                    | (empty/long)
                                    v
                        +-----------------------+
                        |  Reprompt name        |
                        |  (validation hint)    |
                        +-----------+-----------+
                                    |
                                    v
                        +-----------------------+
                        | Ask: age (13–120)     |
                        +-----------+-----------+
                                    |
                         valid age  | invalid age
                                    |
                                    v
                        +-----------------------+
                        |  Reprompt age         |
                        |  (validation hint)    |
                        +-----------+-----------+
                                    |
                                    v
                        +-----------------------+
                        | Ask: address (≤255)   |
                        +-----------+-----------+
                                    |
                       valid address| invalid address
                                    |
                                    v
                        +-----------------------+
                        |  Reprompt address     |
                        |  (validation hint)    |
                        +-----------+-----------+
                                    |
                                    v
                        +-----------------------+
                        |   SAVE to MySQL       |
                        |  (upsert by user id)  |
                        +-----------+-----------+
                                    |
                                    v
                        +-----------------------+
                        |  Success confirmation |
                        |  End conversation     |
                        +-----------------------+

Out-of-band commands (available anytime):

  /cancel --> Abort conversation --> Acknowledge --> End
  /delete --> Delete record for telegram_user_id --> Confirmation --> End
```

---

## Screen-by-screen content (ASCII wireframes)

Legend: [User] indicates user input; [Bot] indicates bot message.

### 1) /start → consent + ask name

```
[User]
/start

[Bot]
+------------------------------------------------------------+
| Hi! I can store your name, age, and address in my database |
| to help with future interactions. By continuing, you agree |
| that I will store these details until you delete them.     |
|                                                            |
| You can reply /cancel anytime to stop.                     |
|                                                            |
| Let's get started. What's your full name?                  |
+------------------------------------------------------------+
```

Validation notes:

-   Accept any non-empty name up to 100 characters.

### 2) Name invalid → reprompt

```
[User]
"   "   (or >100 chars)

[Bot]
+------------------------------------------------------------+
| I couldn't read that name. Please enter your full name      |
| (1–100 characters, letters/numbers/spaces allowed).         |
+------------------------------------------------------------+
```

### 3) Name valid → ask age

```
[User]
Ada Lovelace

[Bot]
+------------------------------------------------------------+
| Great, thanks Ada Lovelace.                                 |
| How old are you? (Please enter a number between 13 and 120) |
+------------------------------------------------------------+
```

### 4) Age invalid → reprompt

```
[User]
abc

[Bot]
+------------------------------------------------------------+
| That doesn't look like a valid age. Please enter a number   |
| between 13 and 120 (e.g., 27).                              |
+------------------------------------------------------------+
```

Or out-of-range:

```
[User]
8

[Bot]
+------------------------------------------------------------+
| Thanks! For this bot, the allowed age is between 13 and 120.|
| Please enter a number in that range.                        |
+------------------------------------------------------------+
```

### 5) Age valid → ask address

```
[User]
27

[Bot]
+------------------------------------------------------------+
| Got it. What's your address?                                |
| (Max 255 characters; you can include apartment/unit, etc.)  |
+------------------------------------------------------------+
```

### 6) Address invalid → reprompt

```
[User]
""  (empty)  or  >255 chars

[Bot]
+------------------------------------------------------------+
| Please enter a non-empty address up to 255 characters.      |
| For example: 123 Main St, Springfield, IL 62704             |
+------------------------------------------------------------+
```

### 7) Address valid → save & confirm

```
[User]
221B Baker Street, London NW1 6XE

[Bot]
+------------------------------------------------------------+
| All set! I've saved your details.                           |
|                                                             |
| Name: Ada Lovelace                                          |
| Age: 27                                                     |
| Address: 221B Baker Street, London NW1 6XE                  |
|                                                             |
| You can update these later by sending /start again,         |
| or erase them anytime with /delete.                         |
+------------------------------------------------------------+
```

### 8) /cancel at any step

```
[User]
/cancel

[Bot]
+------------------------------------------------------------+
| No problem — I’ve cancelled the current process.            |
| Send /start whenever you want to try again.                 |
+------------------------------------------------------------+
```

### 9) /delete (erase data)

```
[User]
/delete

[Bot]
+------------------------------------------------------------+
| Your stored details have been deleted.                      |
| You can provide them again anytime with /start.             |
+------------------------------------------------------------+
```

---

## Content rules & messaging notes

-   Avoid PII in logs; the bot messages may echo user inputs for confirmation, but logs should mask or omit.
-   Keep prompts concise; include a short hint on format and limits.
-   Restrict to private chats; if a group message arrives, politely instruct to DM the bot.
-   Timeouts: if the user pauses too long, send a gentle reminder or end the conversation with instructions to /start again.
