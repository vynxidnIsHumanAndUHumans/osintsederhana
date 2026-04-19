#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSINT EXPERT SUITE - OVERPOWERED EDITION
Full Digital Footprint Mapping & Intelligence Gathering
Author: AI Assistant
Disclaimer: FOR EDUCATIONAL & SELF-AUDIT PURPOSES ONLY
"""

import os
import sys
import json
import socket
import re
import argparse
from datetime import datetime
from urllib.parse import urlparse, urljoin
from collections import defaultdict

# External libraries with fallbacks
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("[!] WARNING: 'requests' library not found. Install with: pip install requests")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("[!] WARNING: 'beautifulsoup4' not found. Install with: pip install beautifulsoup4")

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False
    print("[!] WARNING: 'dnspython' not found. Install with: pip install dnspython")

# --- CONFIGURATION & CONSTANTS ---
VERSION = "2.0.OVERPOWERED"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
]
SOCIAL_PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Twitter": "https://twitter.com/{}",
    "Facebook": "https://www.facebook.com/{}/",
    "TikTok": "https://www.tiktok.com/@{}",
    "LinkedIn": "https://www.linkedin.com/in/{}/",
    "Reddit": "https://www.reddit.com/user/{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Medium": "https://medium.com/@{}",
    "DockerHub": "https://hub.docker.com/u/{}/",
    "GitLab": "https://gitlab.com/{}"
}
SUBDOMAIN_LIST = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "admin", "login", "blog", 
    "shop", "store", "api", "dev", "staging", "test", "m", "mobile", 
    "cdn", "static", "assets", "media", "img", "images", "video", "docs",
    "support", "help", "forum", "community", "status", "monitor", "db",
    "database", "sql", "mysql", "postgres", "redis", "cache", "vpn", 
    "remote", "cloud", "aws", "azure", "gcp", "server", "ns1", "ns2"
]

# --- UTILITY FUNCTIONS ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           OSINT EXPERT SUITE - OVERPOWERED EDITION        ║
    ║                    Version: {VERSION}                     ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  ⚠️  DISCLAIMER: FOR LEGAL SELF-AUDIT & EDUCATION ONLY   ║
    ║      Unauthorized scanning of third-party targets is      ║
    ║      ILLEGAL and violates privacy laws (UU ITE, GDPR).    ║
    ║      Use this tool ONLY on assets YOU own or have explicit║
    ║      written permission to audit.                         ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def legal_confirmation():
    print("\n[⚖️]  LEGAL & ETHICAL CONFIRMATION REQUIRED")
    print("-" * 50)
    print("By proceeding, you confirm that:")
    print("  1. You are auditing YOUR OWN digital footprint, OR")
    print("  2. You have EXPLICIT WRITTEN PERMISSION from the target owner.")
    print("  3. You understand that misuse can lead to criminal prosecution.")
    print("-" * 50)
    confirm = input("\n❓ DO YOU ACCEPT THESE TERMS? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("\n[!] Access denied. Tool terminated.")
        sys.exit(0)
    print("[✓] Terms accepted. Proceeding in AUDIT MODE.\n")

# --- CORE INTELLIGENCE MODULES ---

class DomainIntelligence:
    def __init__(self, domain):
        self.domain = domain
        self.data = defaultdict(dict)
    
    def get_whois_raw(self):
        """Fetch raw WHOIS data via socket"""
        print(f"[*] Fetching WHOIS data for {self.domain}...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            whois_server = "whois.verisign-grs.com" # Default for .com/.net
            if "." in self.domain:
                tld = self.domain.split(".")[-1]
                if tld == "org": whois_server = "whois.pir.org"
                elif tld == "id": whois_server = "whois.id"
                # Add more TLD specific servers as needed
            
            s.connect((whois_server, 43))
            s.send((self.domain + "\r\n").encode())
            response = ""
            while True:
                d = s.recv(4096)
                if not d: break
                response += d.decode('utf-8', errors='ignore')
            s.close()
            self.data['whois'] = response
            return response
        except Exception as e:
            return f"Error fetching WHOIS: {str(e)}"

    def resolve_dns(self):
        """Resolve DNS records"""
        print(f"[*] Resolving DNS records for {self.domain}...")
        records = {}
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
        
        if HAS_DNS:
            try:
                for rtype in record_types:
                    try:
                        answers = dns.resolver.resolve(self.domain, rtype)
                        records[rtype] = [str(r) for r in answers]
                    except dns.resolver.NXDOMAIN:
                        records[rtype] = ["NXDOMAIN"]
                    except dns.resolver.NoAnswer:
                        records[rtype] = ["No Answer"]
                    except Exception as e:
                        records[rtype] = [f"Error: {str(e)}"]
            except Exception as e:
                records['error'] = str(e)
        else:
            # Fallback using socket for A record only
            try:
                ip = socket.gethostbyname(self.domain)
                records['A'] = [ip]
            except:
                records['A'] = ["Resolution Failed"]
        
        self.data['dns'] = records
        return records

    def subdomain_enumeration(self):
        """Bruteforce common subdomains"""
        print(f"[*] Scanning subdomains for {self.domain}...")
        found_subs = []
        for sub in SUBDOMAIN_LIST:
            fqdn = f"{sub}.{self.domain}"
            try:
                socket.gethostbyname(fqdn)
                found_subs.append(fqdn)
                print(f"    [+] Found: {fqdn}")
            except socket.gaierror:
                pass
        self.data['subdomains'] = found_subs
        return found_subs

    def run_full_scan(self):
        print("\n" + "="*40)
        print(f"🌍 DOMAIN INTELLIGENCE: {self.domain}")
        print("="*40)
        self.get_whois_raw()
        self.resolve_dns()
        self.subdomain_enumeration()
        return self.data

class WebReconnaissance:
    def __init__(self, url):
        if not url.startswith('http'):
            url = 'http://' + url
        self.url = url
        self.data = defaultdict(dict)
    
    def fetch_page(self):
        """Fetch webpage content"""
        print(f"[*] Fetching content from {self.url}...")
        if not HAS_REQUESTS:
            return None, "Requests library missing"
        try:
            headers = {'User-Agent': USER_AGENTS[0]}
            resp = requests.get(self.url, headers=headers, timeout=15, verify=True)
            return resp, None
        except Exception as e:
            return None, str(e)

    def analyze_headers(self, response):
        """Analyze HTTP Security Headers"""
        print("[*] Analyzing HTTP Security Headers...")
        headers = response.headers
        security_headers = {
            'Strict-Transport-Security': 'HSTS Missing',
            'Content-Security-Policy': 'CSP Missing',
            'X-Frame-Options': 'Clickjacking Protection Missing',
            'X-Content-Type-Options': 'MIME Sniffing Protection Missing',
            'Referrer-Policy': 'Referrer Policy Missing',
            'Permissions-Policy': 'Permissions Policy Missing'
        }
        findings = {}
        for header, msg in security_headers.items():
            if header in headers:
                findings[header] = headers[header]
            else:
                findings[header] = f"[!] {msg}"
        
        tech_stack = {}
        if 'Server' in headers: tech_stack['Web Server'] = headers['Server']
        if 'X-Powered-By' in headers: tech_stack['Framework/Lang'] = headers['X-Powered-By']
        if 'Set-Cookie' in headers: tech_stack['Cookies'] = "Present"
        
        self.data['headers'] = findings
        self.data['tech_stack'] = tech_stack
        return findings, tech_stack

    def extract_emails(self, html):
        """Extract emails from HTML"""
        print("[*] Extracting email addresses...")
        if not HAS_BS4 or not html:
            return []
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
        self.data['emails'] = list(emails)
        return list(emails)

    def extract_links(self, html, base_url):
        """Extract all links"""
        print("[*] Mapping internal/external links...")
        if not HAS_BS4 or not html:
            return [], []
        soup = BeautifulSoup(html, 'html.parser')
        internal = set()
        external = set()
        parsed_base = urlparse(base_url)
        
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            if parsed.netloc == parsed_base.netloc:
                internal.add(full_url)
            else:
                external.add(full_url)
        
        self.data['links'] = {'internal': list(internal)[:20], 'external': list(external)[:20]}
        return list(internal), list(external)

    def run_full_scan(self):
        print("\n" + "="*40)
        print(f"🕸️  WEB RECONNAISSANCE: {self.url}")
        print("="*40)
        resp, err = self.fetch_page()
        if err:
            print(f"[!] Error: {err}")
            return self.data
        
        self.analyze_headers(resp)
        emails = self.extract_emails(resp.text)
        int_links, ext_links = self.extract_links(resp.text, self.url)
        
        print(f"    [+] Found {len(emails)} emails")
        print(f"    [+] Found {len(int_links)} internal links (showing top 5)")
        for l in int_links[:5]: print(f"        - {l}")
        
        return self.data

class UsernameEnumeration:
    def __init__(self, username):
        self.username = username
        self.data = {}
    
    def check_platform(self, platform, url_template):
        """Check existence on a specific platform"""
        url = url_template.format(self.username)
        if not HAS_REQUESTS:
            return "N/A (No requests lib)"
        try:
            headers = {'User-Agent': USER_AGENTS[0]}
            resp = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                return f"EXISTS ({url})"
            elif resp.status_code == 404:
                return "Not Found"
            else:
                return f"Status: {resp.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def scan_all_platforms(self):
        print(f"\n👤 USERNAME ENUMERATION: @{self.username}")
        print("="*40)
        results = {}
        for platform, template in SOCIAL_PLATFORMS.items():
            status = self.check_platform(platform, template)
            results[platform] = status
            icon = "[+]" if "EXISTS" in status else "[-]"
            print(f"    {icon} {platform}: {status}")
        
        self.data = results
        return results

class GeoIPMapping:
    @staticmethod
    def get_ip_info(ip):
        """Get GeoIP info via API"""
        print(f"[*] Looking up GeoIP for {ip}...")
        if not HAS_REQUESTS:
            return {"error": "No requests library"}
        try:
            resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            data = resp.json()
            if data.get('status') == 'success':
                return {
                    "Country": data.get('country'),
                    "Region": data.get('regionName'),
                    "City": data.get('city'),
                    "ISP": data.get('isp'),
                    "Org": data.get('org'),
                    "Timezone": data.get('timezone'),
                    "Coordinates": f"{data.get('lat')}, {data.get('lon')}"
                }
            return data
        except Exception as e:
            return {"error": str(e)}

# --- MAIN ORCHESTRATOR ---

def main():
    clear_screen()
    print_banner()
    legal_confirmation()
    
    print("\nSELECT SCAN MODE:")
    print("  [1] 🌍 Domain Intelligence (WHOIS, DNS, Subdomains)")
    print("  [2] 🕸️  Web Reconnaissance (Headers, Tech Stack, Emails)")
    print("  [3] 👤 Username Enumeration (Social Media Check)")
    print("  [4] 🚀 FULL MAPPING (Auto-detect & Run All)")
    print("  [0] Exit")
    
    choice = input("\n>>> Enter choice: ").strip()
    
    if choice == '0':
        print("[*] Exiting. Stay safe and legal!")
        sys.exit(0)
    
    target = input(">>> Enter Target (Domain, URL, or Username): ").strip()
    if not target:
        print("[!] No target provided.")
        sys.exit(1)
    
    report = {
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "version": VERSION,
        "results": {}
    }
    
    if choice == '1':
        # Domain Scan
        scanner = DomainIntelligence(target)
        report['results'] = scanner.run_full_scan()
        
        # If we got IPs, do GeoIP
        if 'dns' in report['results'] and 'A' in report['results']['dns']:
            ips = [ip for ip in report['results']['dns']['A'] if re.match(r"\d+\.\d+\.\d+\.\d+", ip)]
            if ips:
                geo_data = GeoIPMapping.get_ip_info(ips[0])
                report['results']['geoip'] = geo_data
    
    elif choice == '2':
        # Web Scan
        scanner = WebReconnaissance(target)
        report['results'] = scanner.run_full_scan()
        
    elif choice == '3':
        # Username Scan
        scanner = UsernameEnumeration(target)
        report['results'] = scanner.scan_all_platforms()
        
    elif choice == '4':
        # Full Auto Mapping
        print("\n[*] Initiating FULL MAPPING sequence...")
        parsed = urlparse(target if target.startswith('http') else 'http://' + target)
        
        is_domain = re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target)
        is_url = parsed.scheme in ['http', 'https'] and parsed.netloc
        
        if is_domain or (is_url and '.' in parsed.netloc):
            domain = parsed.netloc if is_url else target
            print(f"\n[+] Detected TARGET TYPE: DOMAIN ({domain})")
            
            # 1. Domain Intel
            d_scan = DomainIntelligence(domain)
            d_res = d_scan.run_full_scan()
            report['results']['domain_intel'] = d_res
            
            # 2. Web Recon
            w_scan = WebReconnaissance(domain if is_domain else target)
            w_res = w_scan.run_full_scan()
            report['results']['web_recon'] = w_res
            
            # 3. GeoIP
            if 'dns' in d_res and 'A' in d_res['dns']:
                ips = [ip for ip in d_res['dns']['A'] if re.match(r"\d+\.\d+\.\d+\.\d+", ip)]
                if ips:
                    report['results']['geoip'] = GeoIPMapping.get_ip_info(ips[0])
                    
        else:
            # Assume Username
            print(f"\n[+] Detected TARGET TYPE: USERNAME (@{target})")
            u_scan = UsernameEnumeration(target)
            report['results'] = u_scan.scan_all_platforms()
    
    else:
        print("[!] Invalid choice.")
        sys.exit(1)
    
    # Save Report
    filename = f"osint_report_{target.replace('.', '_').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w') as f:
            json.dump(report, f, indent=4, default=str)
        print(f"\n[💾] Full report saved to: {filename}")
    except Exception as e:
        print(f"[!] Could not save report: {e}")
    
    print("\n[✅] SCAN COMPLETE.")

if __name__ == "__main__":
    # Check dependencies
    if not HAS_REQUESTS:
        print("\n[CRITICAL] 'requests' library is required for full functionality.")
        print("Install with: pip install requests beautifulsoup4 dnspython")
        cont = input("Continue with limited features? (y/n): ")
        if cont.lower() != 'y':
            sys.exit(1)
            
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Exiting.")
        sys.exit(0)
