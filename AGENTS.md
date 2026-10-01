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

## Lenient local entry editing

Olive works with local user files, including unfinished drafts. Entry editing,
loading, and saving must remain lenient: do not require referenced YACPDB entries
or person entities to exist, perform online existence checks, or enforce a
`Lastname, Givennames` name format. Allow incomplete attribution, including
versionists without a `version-of` reference, and local text beyond the wiki's
length limits. Preserve these fields through editing and file interchange.

Use the shared YACPDB schema as guidance for field meanings and normal types.
Basic controls such as numeric ID inputs are appropriate, but wiki submission
requirements must not become mandatory validation for local drafts. Explicit
YACPDB validation may report the wiki's stricter requirements.

UI guidance should describe the intended schema-conforming usage without
encouraging deviations. Keep placeholders and tooltips concise; do not advertise
leniency with wording such as "optional" or "any name format". Apply this policy
in every supported language. Tolerating a deviation does not mean recommending it.
