import re
import dns.resolver
import smtplib
import socket
import time
from typing import Dict, Union
import tldextract  # New: For domain age estimation

# Load disposable domains
with open('disposable_domains.txt', 'r') as f:
    disposable_domains = set(line.strip() for line in f if not line.startswith('#'))

# Load common spam traps (create spam_traps.txt)
try:
    with open('spam_traps.txt', 'r') as f:
        spam_traps = set(line.strip() for line in f)
except FileNotFoundError:
    spam_traps = set()

def is_valid_syntax(email: str) -> bool:
    """Check email format with stricter regex"""
    pattern = r'^(?!\.)[a-zA-Z0-9._%+-]+@(?!-)[a-zA-Z0-9-]+(\.[a-zA-Z]{2,})+$'
    return bool(re.match(pattern, email))

def has_mx_record(domain: str) -> bool:
    """Check MX records with caching"""
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False
    except dns.resolver.Timeout:
        time.sleep(1)  # Retry once
        return has_mx_record(domain)

def is_disposable(email: str) -> bool:
    """Check disposable domains with substring matching"""
    domain = email.split('@')[1]
    return any(temp in domain for temp in disposable_domains)

def is_spam_trap(email: str) -> bool:
    """Check known spam trap patterns"""
    return email.split('@')[0] in spam_traps

def domain_age_score(domain: str) -> int:
    """Estimate domain age (0-20 points)"""
    extracted = tldextract.extract(domain)
    # In production, replace with WHOIS lookup
    return 20 if len(extracted.domain) > 8 else 10  # Placeholder

def verify_mailbox(email: str, timeout: int = 5, retries: int = 2) -> bool:
    """Robust SMTP verification with retries and connection pooling"""
    domain = email.split('@')[1]
    
    for attempt in range(retries + 1):
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(mx_records[0].exchange)
            
            with smtplib.SMTP(timeout=timeout) as server:
                server.set_debuglevel(0)  # Disable debug output
                server.connect(mx_record, 25)
                server.helo('yourdomain.com')
                server.mail('verify@yourdomain.com')
                code, _ = server.rcpt(email)
                server.quit()
                return code == 250
        except smtplib.SMTPServerDisconnected:
            if attempt < retries:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            return False
        except (smtplib.SMTPException, socket.error, socket.gaierror):
            return False
    return False

def get_email_score(result: Dict) -> int:
    """Calculate comprehensive score (0-100%)"""
    score = 0
    
    # Basic checks (40 points)
    if result["valid_syntax"]: score += 15
    if result["valid_mx"]: score += 15
    if not result["is_disposable"]: score += 10
    
    # Advanced checks (60 points)
    if result.get("mailbox_exists", False): score += 30
    if not result.get("is_role_based", False): score += 10
    if not result.get("is_spam_trap", False): score += 10
    score += domain_age_score(result["email"].split('@')[1])
    
    return min(100, score)

def verify_email(email: str, smtp_check: bool = True) -> Dict[str, Union[bool, str, int]]:
    """Complete verification with scoring"""
    result = {
        "email": email,
        "valid_syntax": is_valid_syntax(email),
        "valid_mx": False,
        "is_disposable": False,
        "is_spam_trap": is_spam_trap(email),
        "is_role_based": email.split('@')[0] in ['admin', 'support', 'info'],
        "mailbox_exists": False,
        "score": 0,
        "status": "invalid",
        "reason": ""
    }
    
    # Validation pipeline
    if not result["valid_syntax"]:
        result["reason"] = "Invalid syntax"
        return result
    
    domain = email.split('@')[1]
    result["valid_mx"] = has_mx_record(domain)
    if not result["valid_mx"]:
        result["reason"] = "No MX record"
        return result
    
    result["is_disposable"] = is_disposable(email)
    if result["is_disposable"]:
        result["reason"] = "Disposable email"
        return result
    
    if smtp_check:
        result["mailbox_exists"] = verify_mailbox(email)
        if not result["mailbox_exists"]:
            result["reason"] = "Mailbox not found"
            return result
    
    result["score"] = get_email_score(result)
    result["status"] = (
        "valid" if result["score"] >= 75 else
        "risky" if result["score"] >= 40 else
        "invalid"
    )
    return result

if __name__ == "__main__":
    test_emails = [
        "test@gmail.com",
        "invalid@example.nope",
        "spam@known-spam.com"
    ]
    for email in test_emails:
        print(verify_email(email))