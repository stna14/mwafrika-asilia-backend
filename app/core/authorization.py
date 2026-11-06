"""Server-side role policy. Authentication alone does not grant module access."""

EDITORIAL = {"news", "services", "projects", "pages", "gallery", "media"}
ROLE_MODULES = {
    "content_manager": EDITORIAL | {"wisac", "tickets/events", "tickets/tiers"},
    "editor": EDITORIAL,
    "moderator": {"wisac", "media"},
    "support": {"talent"},
    "finance": {"tickets/orders", "payments"},
}


def role_allows(role: str, path: str, method: str) -> bool:
    if role in {"super_admin", "admin"}:
        return True
    if path.rstrip("/") == "/api/admin/me":
        return role in ROLE_MODULES
    if path.rstrip("/") == "/api/tickets/check-in":
        return role == "support"
    prefix = "/api/admin/"
    if not path.startswith(prefix):
        return False
    module = path[len(prefix):].rstrip("/")
    if role == "finance" and method not in {"GET", "HEAD"}:
        return False
    return any(module == allowed or module.startswith(allowed + "/")
               for allowed in ROLE_MODULES.get(role, set()))
