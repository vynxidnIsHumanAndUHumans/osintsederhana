#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXUS RECON - PRO OSINT UNIVERSAL
The Ultimate Data Reconstruction & Vulnerability Mapping Engine

Author: AI Expert System
Version: 1.0.0 (Universal Pro)
License: MIT (For Educational & Ethical Self-Audit Only)

DESCRIPTION:
A comprehensive OSINT framework designed for deep digital footprint reconstruction.
It correlates disparate data points (Domains, IPs, Emails, Tech Stacks) into a 
unified intelligence graph. Features advanced logic for vulnerability detection,
asset discovery, and automated reporting optimized for professional analysis.

WARNING:
Use ONLY on assets you own or have explicit written permission to test.
Unauthorized scanning is illegal under laws such as CFAA (USA), Computer Misuse Act (UK),
and UU ITE (Indonesia). The developer assumes no liability for misuse.
"""

import sys
import socket
import json
import re
import time
import argparse
from urllib.parse import urlparse, urljoin
from datetime import datetime
from collections import defaultdict

# Check for external libraries
try:
    import requests
    from requests.exceptions import RequestException, Timeout, ConnectionError
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

# --- CONFIGURATION & CONSTANTS ---
VERSION = "1.0.0-UNIVERSAL-PRO"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 NexusRecon/{}".format(VERSION)
TIMEOUT = 10

# Wordlists for Subdomain & File Discovery (Optimized for Speed & Coverage)
SUBDOMAIN_WORDLIST = [
    "www", "mail", "ftp", "blog", "shop", "store", "api", "dev", "staging", 
    "prod", "test", "admin", "portal", "support", "help", "docs", "status",
    "cdn", "static", "assets", "media", "img", "images", "video", "app",
    "mobile", "m", "beta", "alpha", "v1", "v2", "secure", "login", "auth",
    "sso", "cloud", "aws", "azure", "gcp", "db", "database", "sql", "backup"
]

SENSITIVE_FILES = [
    ".env", ".git/config", ".htaccess", "robots.txt", "sitemap.xml",
    "wp-config.php", "config.php", "database.yml", "settings.py",
    "package.json", "composer.json", "Dockerfile", "docker-compose.yml",
    ".aws/credentials", ".ssh/id_rsa", "backup.zip", "dump.sql", "web.config"
]

PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}",
    "ip": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "aws_key": r"(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}",
    "private_key": r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
    "jwt": r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+"
}

COLORS = {
    "RESET": "\033[0m",
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "WHITE": "\033[97m",
    "BOLD": "\033[1m"
}

class NexusRecon:
    def __init__(self, target, mode="full"):
        self.target = target
        self.mode = mode
        self.results = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "domain_info": {},
            "dns_records": {},
            "subdomains": [],
            "web_tech": {},
            "vulnerabilities": [],
            "extracted_data": {
                "emails": set(),
                "phones": set(),
                "ips": set(),
                "keys": set(),
                "links": set()
            },
            "geo_location": {},
            "relationship_graph": []
        }
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        
        if not HAS_REQUESTS:
            print(f"{COLORS['RED']}[!] Critical Error: 'requests' library not found. Run: pip install requests{COLORS['RESET']}")
            sys.exit(1)

    def log(self, level, message):
        level_colors = {
            "INFO": COLORS["CYAN"],
            "SUCCESS": COLORS["GREEN"],
            "WARNING": COLORS["YELLOW"],
            "ERROR": COLORS["RED"],
            "CRITICAL": COLORS["MAGENTA"]
        }
        color = level_colors.get(level, COLORS["WHITE"])
        print(f"{color}[{level}] {message}{COLORS['RESET']}")

    def resolve_domain(self, domain):
        """Resolve domain to IP with error handling."""
        try:
            ip = socket.gethostbyname(domain)
            self.results["domain_info"]["resolved_ip"] = ip
            self.results["extracted_data"]["ips"].add(ip)
            self.log("SUCCESS", f"Resolved {domain} -> {ip}")
            return ip
        except socket.gaierror:
            self.log("ERROR", f"Failed to resolve {domain}")
            return None

    def get_whois_data(self, domain):
        """Simulate/Fetch WHOIS data via API or socket if possible."""
        # Note: Real WHOIS parsing requires 'python-whois' lib. 
        # We will use a public API approach for universal compatibility without extra deps if possible,
        # or fallback to basic socket whois on port 43.
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TIMEOUT)
            s.connect(("whois.iana.org", 43))
            s.send((domain + "\r\n").encode())
            response = s.recv(4096).decode()
            s.close()
            
            # Basic parsing for referral
            referral = re.search(r"refer:\s*(\S+)", response)
            if referral:
                server = referral.group(1)
                # Try referral (simplified for this script)
                self.results["domain_info"]["raw_whois"] = response[:500] + "..." # Truncate for display
                self.log("SUCCESS", "WHOIS data retrieved (Referral detected)")
            else:
                self.results["domain_info"]["raw_whois"] = response[:500]
                self.log("SUCCESS", "WHOIS data retrieved")
                
        except Exception as e:
            self.log("WARNING", f"WHOIS lookup failed: {str(e)}")

    def scan_dns(self, domain):
        """Comprehensive DNS Record Scanning."""
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]
        self.log("INFO", f"Scanning DNS records for {domain}...")
        
        for rtype in record_types:
            try:
                if HAS_DNS:
                    answers = dns.resolver.resolve(domain, rtype)
                    records = [str(rdata) for rdata in answers]
                else:
                    # Fallback using socket for A records only if dnspython missing
                    if rtype == "A":
                        try:
                            ip = socket.gethostbyname(domain)
                            records = [ip]
                        except:
                            records = []
                    else:
                        records = ["[Requires dnspython lib]"]
                
                if records:
                    self.results["dns_records"][rtype] = records
                    self.log("SUCCESS", f"{rtype}: {', '.join(records[:3])}{'...' if len(records)>3 else ''}")
            except Exception as e:
                pass # Silent fail for missing records

    def subdomain_enumeration(self, domain):
        """Intelligent Subdomain Bruteforce."""
        self.log("INFO", f"Starting subdomain enumeration for {domain}...")
        found_count = 0
        
        for sub in SUBDOMAIN_WORDLIST:
            candidate = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(candidate)
                self.results["subdomains"].append({"subdomain": candidate, "ip": ip})
                self.results["extracted_data"]["ips"].add(ip)
                self.log("SUCCESS", f"Found: {candidate} ({ip})")
                found_count += 1
                # Add to relationship graph
                self.results["relationship_graph"].append({
                    "source": domain,
                    "target": candidate,
                    "type": "subdomain"
                })
            except socket.gaierror:
                continue
        
        self.log("INFO", f"Enumeration complete. Found {found_count} active subdomains.")

    def web_recon(self, url):
        """Deep Web Reconnaissance: Tech Stack, Headers, Content."""
        if not url.startswith("http"):
            url = "https://" + url
            
        self.log("INFO", f"Initiating Web Recon on {url}...")
        
        try:
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            final_url = response.url
            self.results["web_tech"]["final_url"] = final_url
            self.results["web_tech"]["status_code"] = response.status_code
            
            # 1. Security Headers Analysis
            headers = response.headers
            security_headers = ["Strict-Transport-Security", "Content-Security-Policy", 
                                "X-Frame-Options", "X-Content-Type-Options", 
                                "X-XSS-Protection", "Referrer-Policy"]
            
            missing_headers = []
            for h in security_headers:
                if h not in headers:
                    missing_headers.append(h)
                    self.results["vulnerabilities"].append({
                        "type": "Missing Security Header",
                        "severity": "Medium",
                        "detail": f"Header '{h}' is missing.",
                        "remediation": f"Configure server to include {h}."
                    })
            
            if missing_headers:
                self.log("WARNING", f"Missing Security Headers: {', '.join(missing_headers)}")
            else:
                self.log("SUCCESS", "All major security headers present.")

            # 2. Tech Stack Detection (Simple Fingerprinting)
            tech_stack = []
            server = headers.get("Server", "")
            powered_by = headers.get("X-Powered-By", "")
            
            if server:
                tech_stack.append(f"Server: {server}")
                if "nginx" in server.lower():
                    self.results["web_tech"]["web_server"] = "Nginx"
                elif "apache" in server.lower():
                    self.results["web_tech"]["web_server"] = "Apache"
                    
            if powered_by:
                tech_stack.append(f"Tech: {powered_by}")
                if "php" in powered_by.lower():
                    self.results["web_tech"]["language"] = "PHP"
                elif "asp.net" in powered_by.lower():
                    self.results["web_tech"]["language"] = "ASP.NET"

            # Check cookies for tech hints
            if "JSESSIONID" in str(response.cookies): tech_stack.append("Java/JSP")
            if "csrftoken" in str(response.cookies): tech_stack.append("Django/Python")
            if "wp-login" in response.text: tech_stack.append("WordPress")

            self.results["web_tech"]["detected_stack"] = tech_stack
            self.log("SUCCESS", f"Tech Stack: {', '.join(tech_stack) if tech_stack else 'Unknown'}")

            # 3. Content Extraction (Regex Magic)
            content = response.text
            
            # Emails
            emails = re.findall(PATTERNS["email"], content)
            for e in emails:
                if not e.endswith(".png"): # Filter image fake matches
                    self.results["extracted_data"]["emails"].add(e)
            
            # Phones
            phones = re.findall(PATTERNS["phone"], content)
            for p in phones:
                self.results["extracted_data"]["phones"].add(p)

            # Secrets (Keys, Tokens)
            aws_keys = re.findall(PATTERNS["aws_key"], content)
            if aws_keys:
                self.results["vulnerabilities"].append({
                    "type": "Potential AWS Key Leak",
                    "severity": "CRITICAL",
                    "detail": "AWS Access Key ID pattern found in source code.",
                    "remediation": "Rotate keys immediately and remove from code."
                })
                self.log("CRITICAL", "POTENTIAL AWS KEY LEAK DETECTED!")

            jwt_tokens = re.findall(PATTERNS["jwt"], content)
            if jwt_tokens:
                self.results["extracted_data"]["keys"].update(jwt_tokens)
                self.log("WARNING", "JWT Tokens found in HTML source.")

            # Links Analysis
            links = re.findall(r'href=[\'"]?([^\'" >]+)', content)
            external_links = set()
            internal_links = set()
            
            base_domain = urlparse(final_url).netloc
            
            for link in links:
                full_link = urljoin(final_url, link)
                if base_domain in full_link:
                    internal_links.add(full_link)
                else:
                    if full_link.startswith("http"):
                        external_links.add(full_link)
            
            self.results["extracted_data"]["links"].update(list(external_links)[:20]) # Limit for report
            
            self.log("SUCCESS", f"Extracted: {len(self.results['extracted_data']['emails'])} Emails, {len(external_links)} External Links")

        except ConnectionError:
            self.log("ERROR", "Connection failed. Target unreachable.")
        except Timeout:
            self.log("ERROR", "Request timed out.")
        except Exception as e:
            self.log("ERROR", f"Web recon failed: {str(e)}")

    def check_sensitive_files(self, base_url):
        """Check for exposed sensitive files."""
        self.log("INFO", "Scanning for exposed sensitive files...")
        
        for file in SENSITIVE_FILES:
            url = base_url.rstrip("/") + "/" + file.lstrip("/")
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200 and len(resp.content) > 50:
                    # Heuristic: if it looks like code or config
                    if "password" in resp.text.lower() or "secret" in resp.text.lower() or file.endswith(('.env', '.git', '.sql')):
                        self.results["vulnerabilities"].append({
                            "type": "Sensitive File Exposure",
                            "severity": "High",
                            "detail": f"File {file} is publicly accessible and contains potential secrets.",
                            "url": url
                        })
                        self.log("CRITICAL", f"VULNERABILITY: {file} exposed at {url}")
                    else:
                        self.log("WARNING", f"File {file} exists (Status 200).")
            except:
                pass

    def geo_ip_lookup(self, ip):
        """Basic GeoIP via API (ip-api.com - Free for non-commercial)."""
        if not ip:
            return
        
        self.log("INFO", f"Looking up GeoIP for {ip}...")
        try:
            resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=TIMEOUT)
            data = resp.json()
            
            if data.get("status") == "success":
                self.results["geo_location"] = {
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon")
                }
                self.log("SUCCESS", f"Location: {data.get('city')}, {data.get('country')} (ISP: {data.get('isp')})")
                
                # Add to graph
                self.results["relationship_graph"].append({
                    "source": self.target,
                    "target": f"{data.get('city')}, {data.get('country')}",
                    "type": "geo_location"
                })
            else:
                self.log("WARNING", "GeoIP lookup failed.")
        except Exception as e:
            self.log("ERROR", f"GeoIP error: {str(e)}")

    def generate_report(self):
        """Generate JSON and Visual Text Report."""
        filename = f"nexus_recon_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert sets to lists for JSON serialization
        serializable_results = json.loads(json.dumps(self.results, default=lambda o: list(o) if isinstance(o, set) else str(o)))
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=4)
        
        self.log("SUCCESS", f"Detailed JSON report saved to: {filename}")
        
        # Print Visual Summary
        print("\n" + "="*60)
        print(f"{COLORS['BOLD']}{COLORS['CYAN']} NEXUS RECON - FINAL INTELLIGENCE REPORT{COLORS['RESET']}")
        print("="*60)
        
        print(f"\n{COLORS['BOLD']}Target:{COLORS['RESET']} {self.target}")
        print(f"{COLORS['BOLD']}Timestamp:{COLORS['RESET']} {self.results['timestamp']}")
        
        if self.results["geo_location"]:
            print(f"\n{COLORS['BOLD']}🌍 Geolocation:{COLORS['RESET']}")
            loc = self.results["geo_location"]
            print(f"   📍 {loc.get('city', 'N/A')}, {loc.get('country', 'N/A')}")
            print(f"   🏢 ISP: {loc.get('isp', 'N/A')}")
        
        if self.results["extracted_data"]["emails"]:
            print(f"\n{COLORS['BOLD']}📧 Extracted Emails:{COLORS['RESET']}")
            for email in list(self.results["extracted_data"]["emails"])[:10]:
                print(f"   - {email}")
                
        if self.results["vulnerabilities"]:
            print(f"\n{COLORS['BOLD']}{COLORS['RED']}⚠️ Vulnerabilities Detected:{COLORS['RESET']}")
            for vuln in self.results["vulnerabilities"]:
                print(f"   [{vuln['severity']}] {vuln['type']}: {vuln['detail']}")
        
        print(f"\n{COLORS['BOLD']}🕸️ Relationship Nodes:{COLORS['RESET']}")
        print(f"   - Subdomains Found: {len(self.results['subdomains'])}")
        print(f"   - External Links Mapped: {len(self.results['extracted_data']['links'])}")
        print(f"   - Total Data Points Correlated: {len(self.results['relationship_graph'])}")
        
        print("\n" + "="*60)
        print(f"{COLORS['GREEN']}✅ Scan Complete. Data ready for reconstruction.{COLORS['RESET']}")
        print("="*60 + "\n")

    def run(self):
        """Main Execution Logic."""
        self.log("INFO", f"Initializing NexusRecon v{VERSION} for target: {self.target}")
        
        # Determine if input is URL or Domain
        parsed = urlparse(self.target)
        if parsed.scheme:
            domain = parsed.netloc
            url = self.target
        else:
            domain = self.target
            url = f"http://{self.target}"
            
        # Strip port if present for domain logic
        if ":" in domain:
            domain = domain.split(":")[0]

        # 1. Network Layer
        ip = self.resolve_domain(domain)
        if ip:
            self.get_whois_data(domain)
            self.scan_dns(domain)
            self.geo_ip_lookup(ip)
        
        # 2. Asset Discovery
        self.subdomain_enumeration(domain)
        
        # 3. Application Layer
        self.web_recon(url)
        self.check_sensitive_files(url)
        
        # 4. Reporting
        self.generate_report()

def main():
    print(r"""
    _   _                     ____                  _             
   | \ | |_   _ _ __  _ __   / ___|_ __ _____      _| |_ ___  _ __ 
   |  \| | | | | '_ \| '_ \ | |   | '__/ _ \ \ /\ / / __/ _ \| '__|
   | |\  | |_| | |_) | |_) || |___| | | (_) \ V  V /| || (_) | |   
   |_| \_|\__, | .__/| .__/  \____|_|  \___/ \_/\_/  \__\___/|_|   
          |___/|_|   |_|       UNIVERSAL PRO EDITION              
    """)
    
    parser = argparse.ArgumentParser(description="NexusRecon: Advanced OSINT & Reconstruction Tool")
    parser.add_argument("target", help="Target Domain or URL (e.g., example.com or https://example.com)")
    parser.add_argument("--mode", choices=["full", "passive", "active"], default="full", help="Scan mode")
    args = parser.parse_args()

    # Legal Disclaimer
    print(f"{COLORS['RED']}{COLORS['BOLD']}⚠️ LEGAL DISCLAIMER ⚠️{COLORS['RESET']}")
    print("This tool is for EDUCATIONAL purposes and AUTHORIZED security auditing ONLY.")
    print("Unauthorized scanning of networks or systems is ILLEGAL.")
    print("By proceeding, you confirm that you OWN the target or have EXPLICIT WRITTEN PERMISSION.")
    
    confirm = input(f"\n{COLORS['YELLOW']}Do you accept these terms and confirm authorization? (yes/no): {COLORS['RESET']}")
    
    if confirm.lower() != "yes":
        print("Operation cancelled. Stay ethical.")
        sys.exit(0)

    try:
        scanner = NexusRecon(args.target, args.mode)
        scanner.run()
    except KeyboardInterrupt:
        print(f"\n{COLORS['YELLOW']}Scan interrupted by user.{COLORS['RESET']}")
        sys.exit(0)
    except Exception as e:
        print(f"{COLORS['RED']}Fatal Error: {str(e)}{COLORS['RESET']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
