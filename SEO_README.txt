SEO update notes — Ramnarayan Yadav School, Khirkia

Changes made:
- Added school-specific page title, description, canonical URL, Open Graph and Twitter metadata.
- Added School JSON-LD structured data using the school name and Khirkia locality supplied for this project.
- Added /robots.txt and /sitemap.xml endpoints. Sitemap currently lists the public homepage only because other app routes are primarily login/portal/operational pages.
- Set non-home pages to noindex/nofollow to avoid exposing private/utility pages in search results.
- Updated homepage heading and school name context to match the target school.
- Fixed responsive CSS that hid the main navigation below 900px and added small-screen wrapping rules.
- No database models, migrations, login behavior, fee/attendance logic, or backend workflows were intentionally changed.

Before deploying:
1. Confirm https://ramnarayanyadav.codebykuldeep.site/ is the final public canonical domain. If not, set PUBLIC_SITE_URL in Render to the correct full https URL.
2. Commit and deploy the changed files.
3. Check /robots.txt and /sitemap.xml in the browser.
4. In Google Search Console, verify domain/property ownership and submit https://ramnarayanyadav.codebykuldeep.site/sitemap.xml.
5. Request indexing of the homepage. Rankings are not guaranteed and may take time.
6. Ensure the site publicly displays accurate school contact/location details if you want richer local search visibility. Do not add unverified address/phone details to structured data.

Security note:
This ZIP intentionally excludes Python __pycache__/bytecode, database files, .env files, and .git history if present.

NEW: PRINCIPAL HERO, STUDENT ACHIEVEMENTS & THEME MODES
------------------------------------------------------
- Principal-only homepage controls: /principal/homepage/
- The principal can update hero title, subtitle, description and upload a hero image.
- The principal can add student photos with captions, publish/hide them, and delete entries.
- A light/dark theme toggle is available across pages. Light mode is the default for first-time visitors; the selected theme is remembered in that browser.
- A new migration was added: core/migrations/0003_homepage_settings_student_highlight.py
- Pillow was added to requirements.txt for image uploads.

DEPLOY CHECKLIST
1. Back up your current database/project before deploying.
2. Commit and push the updated files to GitHub.
3. Ensure Render's Start Command runs migrations, e.g.:
   python manage.py migrate --noinput && python manage.py create_admin && gunicorn config.wsgi:application
4. After deploy, sign in with the Principal account and visit /principal/homepage/.
5. Test hero image upload, adding a student highlight, publishing/hiding it, and both theme modes on mobile and desktop.

IMPORTANT IMAGE STORAGE NOTE
Django stores these uploads under MEDIA_ROOT by default. Render's ordinary ephemeral filesystem may lose uploaded images after redeploy/replacement. For durable production uploads, configure a persistent disk or cloud media storage before relying on uploaded school/student photos. Please obtain parent/guardian consent before publishing identifiable photos of minors.
