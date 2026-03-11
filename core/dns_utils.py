import dns.resolver

def check_spf(domain: str) -> dict:
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for r in answers:
            record = r.to_text().strip('"')
            if record.startswith('v=spf1'):
                return {"status": "pass", "record": record}
        return {"status": "fail", "record": None}
    except Exception:
        return {"status": "fail", "record": None}

def check_dmarc(domain: str) -> dict:
    try:
        answers = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
        for r in answers:
            record = r.to_text().strip('"')
            if record.startswith('v=DMARC1'):
                return {"status": "pass", "record": record}
        return {"status": "fail", "record": None}
    except Exception:
        return {"status": "fail", "record": None}

def check_dkim(domain: str, selector: str = "default") -> dict:
    try:
        answers = dns.resolver.resolve(f"{selector}._domainkey.{domain}", 'TXT')
        for r in answers:
            record = r.to_text().strip('"')
            if 'v=DKIM1' in record:
                return {"status": "pass", "record": record}
        return {"status": "fail", "record": None}
    except Exception:
        return {"status": "fail", "record": None}

def verify_domain_token(domain: str, token: str) -> bool:
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for r in answers:
            record = r.to_text().strip('"')
            if token in record:
                return True
        return False
    except Exception:
        return False

def get_dns_health(domain: str) -> dict:
    spf   = check_spf(domain)
    dmarc = check_dmarc(domain)
    dkim  = check_dkim(domain)

    passed = sum(1 for r in [spf, dmarc, dkim] if r["status"] == "pass")
    score  = int((passed / 3) * 100)

    return {
        "domain": domain,
        "score": score,
        "spf": spf,
        "dmarc": dmarc,
        "dkim": dkim,
    }
