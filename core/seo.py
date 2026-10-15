from django.conf import settings
from django.http import HttpResponse


def robots_txt(request):
    site_url = getattr(settings, "PUBLIC_SITE_URL", "https://ramnarayanyadav.codebykuldeep.site").rstrip("/")
    content = "\n".join([
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        f"Sitemap: {site_url}/sitemap.xml",
        "",
    ])
    return HttpResponse(content, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    site_url = getattr(settings, "PUBLIC_SITE_URL", "https://ramnarayanyadav.codebykuldeep.site").rstrip("/")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{site_url}/</loc>'
        '<changefreq>monthly</changefreq><priority>1.0</priority></url>'
        '</urlset>'
    )
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
