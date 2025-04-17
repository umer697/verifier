import re
import dns.resolver  # For MX record checks

def verify_email(email):
    # 1. Check if email syntax is valid
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return False, "Invalid syntax"
    
    # 2. Check if domain is disposable (e.g., mailinator.com)
    domain = email.split('@')[1]
    with open("disposable_domains.txt", "r") as f:
        if domain in f.read():
            return False, "Disposable domain"
    
    # 3. Check if domain has valid MX records (can receive emails)
    try:
        if not dns.resolver.resolve(domain, "MX"):
            return False, "No MX record"
        return True, "Valid"
    except:
        return False, "DNS lookup failed"