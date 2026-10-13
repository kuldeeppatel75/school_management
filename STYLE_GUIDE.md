# SchoolPro template and styling guide

## Structure
- `templates/base.html`: shared HTML shell and Django template blocks.
- `static/css/base.css`: shared global design tokens and safe global defaults.
- `static/css/pages/`: one CSS file per page/template; edit the matching page file for page-specific styling.
- `core/static/core/css/style.css`: existing homepage design stylesheet, retained for compatibility.
- `core/static/core/js/main.js`: existing homepage JavaScript, retained.
- App templates remain in their original Django app folders to preserve `render()` template paths.

## Template inheritance
Most full-page templates now use `{% extends "base.html" %}` and the blocks `title`, `extra_css`, `content`, and `extra_js`. The shared base loads Bootstrap 5 and `static/css/base.css`. Page-specific styles are linked in `extra_css`.

## Where to edit
- Shared fonts/colors/layout defaults: `static/css/base.css`.
- Homepage: `static/css/pages/core_home.css` and existing `core/static/core/css/style.css`.
- Principal portal: `static/css/pages/core_portal.css`.
- Login: `static/css/pages/core_login.css`.
- Fee pages: `static/css/pages/fees_*.css`.
- Attendance pages: `static/css/pages/attendance_*.css`.
- Student and staff pages: `static/css/pages/core_student_*.css`, `core_staff_*.css`.

## Important
Do not move app templates without updating every `render()` call. Do not replace `db.sqlite3` when updating source files. Run `python manage.py check` and test the affected pages after CSS or template edits.

## Validation limitation
This package was structurally inspected and Python source syntax can be checked, but Django is not installed in the build environment, so a live `manage.py check`/browser smoke test could not be run here.
