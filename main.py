#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NEXUS ULTIMATE UNIVERSAL OSINT ENGINE                     ║
║                           Version 5.0 - BLACK EDITION                        ║
║                                                                              ║
║  The Most Advanced Open-Source Intelligence & Security Audit Framework       ║
║  Combining: Async Recon, Smart Fuzzing, Secret Hunting, Tech Analysis        ║
║           Domain Intelligence, Username Enumeration, Data Mapping            ║
║                                                                              ║
║  MODES:                                                                      ║
║  🛡️ DEFENSIVE  : Passive OSINT, Header Analysis, Tech Detection              ║
║  🔥 AGGRESSIVE : Directory Fuzzing, Subdomain Bruteforce, Secret Scanning    ║
║  💀 FULL AUDIT : All-in-one comprehensive security assessment                ║
║                                                                              ║
║  ⚠️  LEGAL WARNING: ONLY FOR AUTHORIZED SELF-AUDIT AND BUG BOUNTY PROGRAMS  ║
║      Usage without permission violates UU ITE, CFAA, Computer Misuse Act     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import aiohttp
import argparse
import json
import re
import sys
import hashlib
import time
import socket
import ssl
from datetime import datetime
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass, asdict, field
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

VERSION = "5.0.0-ULTIMATE-UNIVERSAL"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 NexusAudit/5.0"
MAX_CONCURRENT_REQUESTS = 100
TIMEOUT_SECONDS = 15
RATE_LIMIT_DELAY = 0.1  # seconds between requests

# Colors for terminal output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"

# ============================================================================
# LEGAL & ETHICAL MODULE
# ============================================================================

def show_legal_disclaimer():
    """Display comprehensive legal disclaimer."""
    print(f"""
{Colors.RED}{Colors.BOLD}{'='*80}{Colors.RESET}
{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}                    PERINGATAN HUKUM KERAS / STRICT LEGAL WARNING                    {Colors.RESET}
{Colors.RED}{Colors.BOLD}{'='*80}{Colors.RESET}

{Colors.YELLOW}⚠️  ALAT INI HANYA UNTUK:{Colors.RESET}
   1. Audit keamanan diri sendiri (Self-Audit / Only Me Mode)
   2. Pengujian penetrasi dengan izin tertulis resmi
   3. Program Bug Bounty yang sah sesuai scope

{Colors.RED}❌ TINDAKAN ILEGAL:{Colors.RESET}
   Menggunakan alat ini untuk mengakses, memindai, atau menyerang sistem
   milik pihak lain TANPA IZIN EKSPLESIT adalah tindak pidana.

{Colors.CYAN}📜 DASAR HUKUM (INDONESIA):{Colors.RESET}
   • UU ITE No. 11 Tahun 2008 (Pasal 30, 31, 32): Akses Ilegal, Penyadapan
   • KUHP Pasal 480: Penggunaan alat untuk kejahatan komputer
   • Permenkominfo No. 20 Tahun 2016: Keamanan Sistem Elektronik

{Colors.CYAN}📜 DASAR HUKUM (INTERNASIONAL):{Colors.RESET}
   • Computer Fraud and Abuse Act (CFAA) - USA
   • Computer Misuse Act 1990 - UK
   • GDPR Article 32 - Europe (Data Protection)
   • Cybercrime Prevention Act - Various Countries

{Colors.GREEN}✅ DENGAN MELANJUTKAN, ANDA MENYETUJUI:{Colors.RESET}
   "Saya adalah pemilik sah dari target yang akan diaudit, ATAU saya memiliki
   izin tertulis yang sah untuk melakukan pengujian keamanan pada target ini.
   Saya memahami risiko hukum dan bertanggung jawab penuh atas penggunaan alat ini."

{Colors.RED}Pengembang tool ini TIDAK BERTANGGUNG JAWAB atas penyalahgunaan alat ini.{Colors.RESET}
{Colors.RED}{Colors.BOLD}{'='*80}{Colors.RESET}
""")

def confirm_authorization():
    """Require explicit user confirmation."""
    print(f"\n{Colors.YELLOW}[?] KONFIRMASI OTORISASI WAJIB{Colors.RESET}")
    print("Apakah Anda memiliki izin sah atau merupakan pemilik dari target ini?")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        response = input(f"{Colors.BOLD}Ketik 'YA, SAYA PEMILIK/AUTORIZED' untuk melanjutkan: {Colors.RESET}").strip().upper()
        
        if response in ["YA, SAYA PEMILIK/AUTORIZED", "YA", "YES", "I OWN IT"]:
            print(f"\n{Colors.GREEN}✅ Otorisasi Diterima. Memulai Nexus Engine v{VERSION}...{Colors.RESET}")
            return True
        
        if attempt < max_attempts - 1:
            print(f"{Colors.RED}❌ Input tidak valid. Percobaan {attempt + 1}/{max_attempts}{Colors.RESET}")
    
    print(f"\n{Colors.BG_RED}{Colors.WHITE}❌ AKSES DITOLAK. Konfirmasi otorisasi gagal.{Colors.RESET}")
    print("Alat ini tidak dapat dijalankan tanpa persetujuan legal.")
    return False

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ScanResult:
    url: str
    status_code: int
    content_length: int
    content_hash: str
    tech_stack: List[str] = field(default_factory=list)
    secrets_found: List[Dict[str, str]] = field(default_factory=list)
    headers_issues: List[str] = field(default_factory=list)
    is_hidden: bool = False
    risk_level: str = "LOW"
    response_time: float = 0.0
    directory_listing: bool = False

@dataclass
class DomainInfo:
    domain: str
    registrar: str = ""
    creation_date: str = ""
    expiration_date: str = ""
    name_servers: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    org: str = ""
    country: str = ""

@dataclass
class UsernameResult:
    platform: str
    username: str
    url: str
    exists: bool
    status_code: int = 0

# ============================================================================
# SECRET SCANNER MODULE
# ============================================================================

class SecretScanner:
    """Advanced heuristic scanner for sensitive data patterns."""
    
    PATTERNS = {
        "AWS Access Key": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "AWS Secret Key": r"(?i)aws.*[=\s'\"]([0-9a-zA-Z\/+]{40})['\"]",
        "Private Key (RSA/SSH)": r"-----BEGIN (RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY-----",
        "GitHub Token": r"ghp_[a-zA-Z0-9]{36}",
        "GitHub OAuth": r"gho_[a-zA-Z0-9]{36}",
        "GitLab Token": r"glpat-[a-zA-Z0-9\-]{20}",
        "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
        "Google OAuth": r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
        "Slack Token": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*",
        "Slack Webhook": r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}",
        "Generic API Key": r"(?i)(api[_-]?key|apikey|secret[_-]?key)['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]",
        "JWT Token": r"eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9._-]+\.[A-Za-z0-9-_]+",
        "Password in URL": r"(?i)(password|passwd|pwd|pass)=([^&\s'\"]+)",
        "Database Connection": r"(?i)(mysql|postgres|postgresql|mongodb|redis|amqp)://[^\s'\"]+",
        "Stripe Key": r"sk_live_[0-9a-zA-Z]{24}",
        "Twilio Key": r"SK[0-9a-fA-F]{32}",
        "Mailgun Key": r"key-[0-9a-zA-Z]{32}",
        "Heroku API Key": r"(?i)heroku.*[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}",
        "SSH Password": r"(?i)ssh.*password.*[:=]\s*['\"]?[^\s'\"]+",
        "Admin Panel": r"(?i)(admin|administrator|dashboard|wp-admin|phpmyadmin)",
        "Backup File": r"(?i)(backup|bak|old|orig|save|copy)\.(sql|zip|tar|gz|rar|7z)",
        "Config File": r"(?i)(config|conf|settings|environment|env)\.(php|json|yaml|yml|ini)",
        "Log File": r"(?i)(access|error|debug|log)\.(txt|log|out)",
    }

    @staticmethod
    def scan(content: str, url: str = "") -> List[Dict[str, str]]:
        findings = []
        for name, pattern in SecretScanner.PATTERNS.items():
            try:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    # Handle tuple matches from groups
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[-1]
                    
                    # Sanitize output
                    safe_match = match[:15] + "***REDACTED***" if len(str(match)) > 15 else match
                    
                    severity = "CRITICAL"
                    if any(x in name for x in ["Admin", "Backup", "Config", "Log"]):
                        severity = "HIGH"
                    elif any(x in name for x in ["Password", "Key", "Private", "Token"]):
                        severity = "CRITICAL"
                    else:
                        severity = "MEDIUM"
                    
                    findings.append({
                        "type": name,
                        "match_preview": str(safe_match),
                        "url": url,
                        "severity": severity
                    })
            except re.error:
                continue
        return findings

# ============================================================================
# TECHNOLOGY ANALYZER MODULE
# ============================================================================

class TechAnalyzer:
    """Advanced technology fingerprinting engine."""
    
    SIGNATURES = {
        "WordPress": {
            "files": ["/wp-admin/", "/wp-content/", "/wp-includes/", "/xmlrpc.php"],
            "headers": ["X-Powered-By", "Link"],
            "content": ["wp-", "wordpress", "WordPress"],
            "cookies": ["wordpress_", "wp-settings"]
        },
        "Joomla": {
            "files": ["/administrator/", "/joomla.xml", "/media/jui/"],
            "headers": [],
            "content": ["joomla", "Joomla!"],
            "cookies": ["__joomla"]
        },
        "Drupal": {
            "files": ["/misc/drupal.js", "/sites/default/", "/core/"],
            "headers": ["X-Generator"],
            "content": ["drupal", "Drupal"],
            "cookies": ["SESS", "SSESS"]
        },
        "Nginx": {
            "headers": ["Server"],
            "content": [],
            "patterns": ["nginx"]
        },
        "Apache": {
            "headers": ["Server"],
            "content": [],
            "patterns": ["Apache"]
        },
        "IIS": {
            "headers": ["Server"],
            "content": [],
            "patterns": ["IIS", "ASP.NET", "Microsoft-IIS"]
        },
        "PHP": {
            "headers": ["X-Powered-By", "Set-Cookie"],
            "content": [],
            "patterns": ["PHP", "php"]
        },
        "Python/Django": {
            "headers": ["Server", "X-Frame-Options"],
            "content": ["django", "Django", "csrftoken"],
            "cookies": ["csrftoken", "sessionid"]
        },
        "Ruby/Rails": {
            "headers": ["X-Runtime", "X-Powered-By"],
            "content": ["rails", "Ruby"],
            "cookies": ["_session_id"]
        },
        "React": {
            "content": ["react", "React", "_reactRoot", "react-dom"],
            "files": []
        },
        "Angular": {
            "content": ["ng-", "angular", "Angular"],
            "files": []
        },
        "Vue.js": {
            "content": ["vue", "Vue", "vue-devtools"],
            "files": []
        },
        "jQuery": {
            "content": ["jquery", "jQuery"],
            "files": []
        },
        "Bootstrap": {
            "content": ["bootstrap", "Bootstrap"],
            "files": []
        },
        "Cloudflare": {
            "headers": ["CF-RAY", "CF-Cache-Status"],
            "content": ["cloudflare"],
            "patterns": ["Cloudflare"]
        },
        "AWS": {
            "headers": ["X-Amz-Cf-Id"],
            "content": ["amazonaws", "cloudfront"],
            "patterns": ["Amazon", "AWS"]
        }
    }

    @staticmethod
    def analyze(headers: Dict[str, str], content: str, cookies: Dict[str, str] = None) -> List[str]:
        techs = []
        content_lower = content.lower()
        
        # Check Headers
        for header, value in headers.items():
            h_combined = f"{header}: {value}".lower()
            for tech, sigs in TechAnalyzer.SIGNATURES.items():
                if tech in techs:
                    continue
                for pattern in sigs.get("patterns", []):
                    if pattern.lower() in h_combined:
                        techs.append(tech)
                        break
                for header_pattern in sigs.get("headers", []):
                    if header_pattern.lower() in header.lower():
                        techs.append(tech)
                        break
        
        # Check Content
        for tech, sigs in TechAnalyzer.SIGNATURES.items():
            if tech in techs:
                continue
            for pattern in sigs.get("content", []):
                if pattern.lower() in content_lower:
                    techs.append(tech)
                    break
        
        # Check Cookies
        if cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()]).lower()
            for tech, sigs in TechAnalyzer.SIGNATURES.items():
                if tech in techs:
                    continue
                for cookie_pattern in sigs.get("cookies", []):
                    if cookie_pattern.lower() in cookie_str:
                        techs.append(tech)
                        break
        
        return list(set(techs))  # Remove duplicates

# ============================================================================
# USERNAME ENUMERATION MODULE
# ============================================================================

class UsernameEnumerator:
    """Cross-platform username enumeration."""
    
    PLATFORMS = {
        "GitHub": "https://github.com/{}",
        "Instagram": "https://www.instagram.com/{}/",
        "Twitter/X": "https://twitter.com/{}",
        "Facebook": "https://www.facebook.com/{}/",
        "TikTok": "https://www.tiktok.com/@{}",
        "Pinterest": "https://www.pinterest.com/{}/",
        "Reddit": "https://www.reddit.com/user/{}",
        "Docker Hub": "https://hub.docker.com/u/{}/",
        "Medium": "https://medium.com/@{}",
        "GitLab": "https://gitlab.com/{}",
        "Bitbucket": "https://bitbucket.org/{}/",
        "LinkedIn": "https://www.linkedin.com/in/{}/",
        "YouTube": "https://www.youtube.com/@{}",
        "Vimeo": "https://vimeo.com/{}",
        "SoundCloud": "https://soundcloud.com/{}",
        "Telegram": "https://t.me/{}",
        "WhatsApp": "https://wa.me/{}",
        "Discord": "https://discord.com/users/{}",
        "Steam": "https://steamcommunity.com/id/{}",
        "Twitch": "https://www.twitch.tv/{}",
    }

    @staticmethod
    async def check_platform(session: aiohttp.ClientSession, platform: str, username: str, url_template: str) -> UsernameResult:
        url = url_template.format(username)
        try:
            async with session.get(url, timeout=10, allow_redirects=True) as resp:
                exists = resp.status == 200
                return UsernameResult(
                    platform=platform,
                    username=username,
                    url=url,
                    exists=exists,
                    status_code=resp.status
                )
        except Exception:
            return UsernameResult(
                platform=platform,
                username=username,
                url=url,
                exists=False,
                status_code=0
            )

    @staticmethod
    async def enumerate(username: str) -> List[UsernameResult]:
        results = []
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=50)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for platform, url_template in UsernameEnumerator.PLATFORMS.items():
                tasks.append(UsernameEnumerator.check_platform(session, platform, username, url_template))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, UsernameResult)]
        return valid_results

# ============================================================================
# DOMAIN INTELLIGENCE MODULE
# ============================================================================

class DomainIntelligence:
    """Comprehensive domain and network analysis."""
    
    COMMON_SUBDOMAINS = [
        "www", "mail", "ftp", "admin", "dev", "test", "api", "stage", "prod",
        "staging", "development", "beta", "alpha", "demo", "app", "web", "blog",
        "shop", "store", "portal", "dashboard", "panel", "control", "manage",
        "cdn", "static", "assets", "img", "images", "video", "media", "files",
        "docs", "doc", "help", "support", "status", "monitor", "analytics",
        "db", "database", "sql", "mysql", "postgres", "mongo", "redis",
        "git", "svn", "jenkins", "ci", "cd", "build", "deploy",
        "vpn", "remote", "internal", "intranet", "extranet", "secure", "login",
        "auth", "oauth", "sso", "iam", "identity", "account", "accounts",
        "billing", "payment", "pay", "checkout", "cart", "order", "orders",
        "crm", "erp", "hr", "hrm", "finance", "legal", "compliance", "audit"
    ]

    @staticmethod
    def get_dns_records(domain: str) -> Dict[str, List[str]]:
        """Get DNS records using socket (no external dependencies)."""
        records = {}
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]
        
        for rtype in record_types:
            try:
                if rtype == "A":
                    result = socket.gethostbyname_ex(domain)
                    records[rtype] = result[2]
                elif rtype == "AAAA":
                    result = socket.getaddrinfo(domain, None, socket.AF_INET6)
                    records[rtype] = list(set([r[4][0] for r in result]))
                else:
                    # For other types, we'd need dnspython library
                    # Fallback to basic resolution
                    pass
            except socket.gaierror:
                pass
            except Exception:
                pass
        
        return records

    @staticmethod
    async def check_subdomain(session: aiohttp.ClientSession, subdomain: str, base_domain: str) -> Optional[str]:
        """Check if subdomain exists."""
        fqdn = f"{subdomain}.{base_domain}"
        try:
            async with session.get(f"http://{fqdn}", timeout=5, allow_redirects=False) as resp:
                if resp.status < 400:
                    return fqdn
        except Exception:
            pass
        
        # Try HTTPS
        try:
            async with session.get(f"https://{fqdn}", timeout=5, allow_redirects=False, ssl=False) as resp:
                if resp.status < 400:
                    return fqdn
        except Exception:
            pass
        
        return None

    @staticmethod
    async def brute_subdomains(base_domain: str) -> List[str]:
        """Bruteforce common subdomains."""
        found = []
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=50)
        timeout = aiohttp.ClientTimeout(total=5)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for sub in DomainIntelligence.COMMON_SUBDOMAINS[:40]:  # Limit to 40 for speed
                tasks.append(DomainIntelligence.check_subdomain(session, sub, base_domain))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            found = [r for r in results if r is not None]
        
        return found

# ============================================================================
# MAIN NEXUS ENGINE
# ============================================================================

class NexusEngine:
    """Main Asynchronous Scanning Engine combining all modules."""

    def __init__(self, target: str, mode: str = "passive"):
        self.target = target
        self.mode = mode
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[ScanResult] = []
        self.crawled_urls: Set[str] = set()
        self.to_crawl: List[str] = []
        self.baseline_404_hash: Optional[str] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self.domain_info: Optional[DomainInfo] = None
        self.username_results: List[UsernameResult] = []
        self.subdomains_found: List[str] = []
        
        # Sensitive paths for fuzzing
        self.sensitive_paths = [
            "/admin", "/administrator", "/wp-admin", "/dashboard", "/login",
            "/config", "/conf", "/settings", "/backup", "/backups", "/db", "/sql",
            "/.env", "/.git", "/.git/config", "/.svn", "/.htaccess", "/.htpasswd",
            "/phpinfo.php", "/info.php", "/test.php", "/phpinfo", "/info",
            "/api", "/api/v1", "/api/v2", "/graphql", "/swagger", "/docs",
            "/upload", "/uploads", "/temp", "/tmp", "/cache",
            "/log", "/logs", "/error_log", "/access_log",
            "/shell", "/console", "/manager", "/control", "/panel",
            "/private", "/secret", "/hidden", "/internal", "/dev", "/staging",
            "/robots.txt", "/sitemap.xml", "/crossdomain.xml", "/clientaccesspolicy.xml",
            "/web.config", "/.DS_Store", "/Thumbs.db",
            "/backup.sql", "/dump.sql", "/database.sql", "/db.sql",
            "/config.php", "/config.json", "/config.yaml", "/settings.json",
            "/.bash_history", "/.ssh/id_rsa", "/.ssh/authorized_keys",
            "/server-status", "/server-info", "/phpmyadmin", "/pma",
            "/elmah.axd", "/trace.axd", "/route.aspx",
            "/actuator", "/health", "/metrics", "/env", "/beans"
        ]

    async def initialize_session(self):
        """Initialize async HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=MAX_CONCURRENT_REQUESTS)
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

    async def close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()

    def get_content_hash(self, content: str) -> str:
        """Generate MD5 hash of content."""
        return hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()

    async def setup_baseline(self):
        """Create baseline for 404 detection."""
        random_path = f"/nexus_{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"
        url = f"{self.target}{random_path}"
        try:
            async with self.session.get(url, allow_redirects=False) as resp:
                content = await resp.text()
                self.baseline_404_hash = self.get_content_hash(content)
                print(f"{Colors.GREEN}✅{Colors.RESET} Baseline 404 established")
        except Exception:
            print(f"{Colors.YELLOW}⚠️{Colors.RESET} Could not establish 404 baseline")

    async def is_false_positive(self, content: str, status: int) -> bool:
        """Check if response is a false positive (custom 404 page)."""
        if status != 200:
            return False
        if not self.baseline_404_hash:
            return False
        content_hash = self.get_content_hash(content)
        return content_hash == self.baseline_404_hash

    async def scan_url(self, url: str, is_fuzzing: bool = False) -> Optional[ScanResult]:
        """Scan a single URL with full analysis."""
        async with self.semaphore:
            start_time = time.time()
            try:
                async with self.session.get(url, allow_redirects=True, ssl=False) as resp:
                    content = await resp.text()
                    response_time = time.time() - start_time
                    
                    # Check for false positives
                    if await self.is_false_positive(content, resp.status):
                        return None
                    
                    content_hash = self.get_content_hash(content)
                    
                    # Analyze technologies
                    techs = TechAnalyzer.analyze(dict(resp.headers), content, dict(resp.cookies))
                    
                    # Scan for secrets
                    secrets = SecretScanner.scan(content, url)
                    
                    # Check security headers
                    headers_issues = []
                    required_headers = [
                        "Strict-Transport-Security",
                        "Content-Security-Policy",
                        "X-Frame-Options",
                        "X-Content-Type-Options",
                        "Referrer-Policy",
                        "Permissions-Policy"
                    ]
                    for h in required_headers:
                        if h not in resp.headers:
                            headers_issues.append(f"Missing: {h}")
                    
                    # Check for directory listing
                    directory_listing = "Index of /" in content or "Directory listing for" in content
                    
                    # Determine risk level
                    risk = "LOW"
                    if secrets:
                        risk = "CRITICAL"
                    elif directory_listing:
                        risk = "HIGH"
                    elif len(headers_issues) > 3:
                        risk = "MEDIUM"
                    elif is_fuzzing and resp.status == 200:
                        risk = "HIGH" if any(x in url.lower() for x in ["admin", "backup", "config", "db"]) else "MEDIUM"
                    
                    result = ScanResult(
                        url=url,
                        status_code=resp.status,
                        content_length=len(content),
                        content_hash=content_hash,
                        tech_stack=techs,
                        secrets_found=secrets,
                        headers_issues=headers_issues,
                        is_hidden=is_fuzzing,
                        risk_level=risk,
                        response_time=response_time,
                        directory_listing=directory_listing
                    )
                    
                    self.results.append(result)
                    
                    # Real-time output
                    status_color = Colors.GREEN if resp.status == 200 else Colors.YELLOW
                    secret_alert = f" {Colors.BG_RED}SECRETS!{Colors.RESET}" if secrets else ""
                    dir_alert = f" {Colors.RED}DIR LISTING{Colors.RESET}" if directory_listing else ""
                    
                    if is_fuzzing or len(self.results) % 10 == 0:
                        print(f"[{status_color}{resp.status}{Colors.RESET}] {url}{secret_alert}{dir_alert}")
                    
                    # Extract links for crawling
                    if resp.status == 200 and self.mode == "full":
                        await self.extract_links(content, url)
                    
                    return result

            except asyncio.TimeoutError:
                print(f"{Colors.YELLOW}⏱️{Colors.RESET} Timeout: {url}")
            except Exception as e:
                pass
        return None

    async def extract_links(self, content: str, base_url: str):
        """Extract URLs from HTML content."""
        links = re.findall(r'href=[\'"]?([^\'" >]+)', content, re.IGNORECASE)
        for link in links:
            full_url = urljoin(base_url, link)
            parsed = urlparse(full_url)
            
            # Only same domain, http/https, no fragments
            if (parsed.netloc == urlparse(self.target).netloc and 
                parsed.scheme in ["http", "https"] and
                not full_url.endswith(('.pdf', '.jpg', '.png', '.gif', '.css', '.js'))):
                
                if full_url not in self.crawled_urls and full_url not in self.to_crawl:
                    if len(self.to_crawl) < 500:  # Limit queue size
                        self.to_crawl.append(full_url)

    async def run_fuzzing(self):
        """Active directory/file fuzzing."""
        if self.mode not in ["active", "full"]:
            return
        
        print(f"\n{Colors.RED}🔥{Colors.RESET} Starting directory fuzzing ({len(self.sensitive_paths)} paths)...")
        
        tasks = []
        for path in self.sensitive_paths:
            url = f"{self.target}{path}"
            tasks.append(self.scan_url(url, is_fuzzing=True))
        
        await asyncio.gather(*tasks, return_exceptions=True)

    async def run_crawler(self):
        """Intelligent web crawler."""
        if self.mode != "full":
            return
        
        print(f"\n{Colors.CYAN}🕸️{Colors.RESET} Starting intelligent crawler...")
        self.to_crawl.append(self.target)
        
        iteration = 0
        while self.to_crawl and iteration < 25:  # Max 25 iterations
            batch = self.to_crawl[:20]
            self.to_crawl = self.to_crawl[20:]
            
            tasks = []
            for url in batch:
                if url not in self.crawled_urls:
                    self.crawled_urls.add(url)
                    tasks.append(self.scan_url(url))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            iteration += 1
            await asyncio.sleep(RATE_LIMIT_DELAY)

    async def run_subdomain_scan(self, domain: str):
        """Run subdomain bruteforce."""
        if self.mode not in ["active", "full"]:
            return
        
        print(f"\n{Colors.MAGENTA}🔍{Colors.RESET} Scanning subdomains for {domain}...")
        self.subdomains_found = await DomainIntelligence.brute_subdomains(domain)
        
        if self.subdomains_found:
            print(f"{Colors.GREEN}✅{Colors.RESET} Found {len(self.subdomains_found)} subdomains:")
            for sub in self.subdomains_found[:10]:
                print(f"   • {sub}")
            if len(self.subdomains_found) > 10:
                print(f"   ... and {len(self.subdomains_found) - 10} more")

    async def run_username_scan(self, username: str):
        """Run username enumeration."""
        print(f"\n{Colors.BLUE}👤{Colors.RESET} Enumerating username '{username}' across platforms...")
        self.username_results = await UsernameEnumerator.enumerate(username)
        
        found_count = sum(1 for r in self.username_results if r.exists)
        if found_count > 0:
            print(f"{Colors.GREEN}✅{Colors.RESET} Found {found_count} profiles:")
            for r in self.username_results:
                if r.exists:
                    print(f"   • {r.platform}: {r.url}")

    async def run_full_scan(self):
        """Execute complete scan based on mode."""
        parsed = urlparse(self.target)
        
        # Initialize session
        await self.initialize_session()
        
        # Setup baseline
        await self.setup_baseline()
        
        # Initial scan of main URL
        print(f"\n{Colors.CYAN}🚀{Colors.RESET} Scanning target: {self.target}")
        await self.scan_url(self.target)
        
        # Mode-specific operations
        if self.mode in ["active", "full"]:
            # Subdomain scan
            if parsed.netloc:
                domain = parsed.netloc.split(':')[0]
                await self.run_subdomain_scan(domain)
            
            # Directory fuzzing
            await self.run_fuzzing()
        
        if self.mode == "full":
            # Full crawl
            await self.run_crawler()
        
        # Close session
        await self.close_session()
        
        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive JSON report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nexus_ultimate_report_{timestamp}.json"
        
        # Calculate statistics
        critical_findings = len([r for r in self.results if r.risk_level == "CRITICAL"])
        high_risk = len([r for r in self.results if r.risk_level == "HIGH"])
        medium_risk = len([r for r in self.results if r.risk_level == "MEDIUM"])
        total_secrets = sum(len(r.secrets_found) for r in self.results)
        all_techs = list(set(t for r in self.results for t in r.tech_stack))
        hidden_resources = len([r for r in self.results if r.is_hidden and r.status_code == 200])
        
        report_data = {
            "nexus_ultimate_audit": VERSION,
            "target": self.target,
            "scan_mode": self.mode,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_urls_scanned": len(self.results),
                "critical_findings": critical_findings,
                "high_risk_findings": high_risk,
                "medium_risk_findings": medium_risk,
                "total_secrets_found": total_secrets,
                "hidden_resources": hidden_resources,
                "technologies_detected": all_techs,
                "subdomains_found": self.subdomains_found,
                "username_profiles": [asdict(r) for r in self.username_results if r.exists]
            },
            "detailed_findings": [
                asdict(r) for r in self.results 
                if r.secrets_found or r.headers_issues or r.is_hidden or r.directory_listing or r.risk_level in ["CRITICAL", "HIGH"]
            ]
        }
        
        # Save report
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"{Colors.GREEN}✅ SCAN COMPLETED{Colors.RESET}")
        print(f"{'='*70}")
        print(f"📊 Summary:")
        print(f"   • Total URLs Scanned: {len(self.results)}")
        print(f"   • Critical Findings: {Colors.RED}{critical_findings}{Colors.RESET}")
        print(f"   • High Risk: {Colors.YELLOW}{high_risk}{Colors.RESET}")
        print(f"   • Secrets Leaked: {Colors.BG_RED}{total_secrets}{Colors.RESET}")
        print(f"   • Technologies: {', '.join(all_techs[:5])}{'...' if len(all_techs) > 5 else ''}")
        print(f"   • Subdomains: {len(self.subdomains_found)}")
        print(f"\n💾 Report saved to: {Colors.CYAN}{filename}{Colors.RESET}")
        print(f"{'='*70}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description=f"NEXUS ULTIMATE UNIVERSAL OSINT ENGINE v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py https://example.com --mode passive
  python3 main.py https://example.com --mode active
  python3 main.py https://example.com --mode full
  python3 main.py https://example.com --username john_doe --mode full
        """
    )
    parser.add_argument("target", help="Target URL (e.g., https://example.com)")
    parser.add_argument("--mode", choices=["passive", "active", "full"], 
                       default="passive", 
                       help="Scan mode: passive (safe), active (fuzzing), full (all)")
    parser.add_argument("--username", help="Username to enumerate across platforms")
    
    args = parser.parse_args()
    
    # Validate URL
    if not args.target.startswith(("http://", "https://")):
        print(f"{Colors.RED}❌ Error: URL must start with http:// or https://{Colors.RESET}")
        sys.exit(1)
    
    # Show legal disclaimer
    show_legal_disclaimer()
    
    # Confirm authorization
    if not confirm_authorization():
        sys.exit(1)
    
    # Create engine
    engine = NexusEngine(args.target, args.mode)
    
    try:
        # Run main scan
        asyncio.run(engine.run_full_scan())
        
        # Run username scan if specified
        if args.username:
            print(f"\n{Colors.BLUE}👤{Colors.RESET} Running username enumeration...")
            asyncio.run(engine.run_username_scan(args.username))
            engine.generate_report()  # Regenerate with username data
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Scan interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
