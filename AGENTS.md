# Contributor instructions

## User interface language

Every user-visible text must use the current display language through `Lang.value(...)`.
This includes menu items, action labels, tooltips, dialog titles and bodies, status
messages, and validation or error messages. Do not hard-code UI prose in Python.

Whenever introducing or changing user-visible text, update `conf/lang.yaml` in the
same change for **all supported languages**. Preserve format placeholders
across translations. Literal filenames, paths, and configuration keys remain
unchanged when embedded in translated text.

Existing controls and visible status messages must refresh when the display
language changes. Translate application error messages at presentation time;
do not expose untranslated exception prose from libraries as UI messages.

Verify translation coverage and exercise language switching for new UI elements.
