#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXUS ULTIMATE AUDIT ENGINE (v3.0)
----------------------------------
Professional Asynchronous Security Auditor & Reconnaissance Tool.

FITUR UTAMA:
1. Async I/O Engine (aiohttp) untuk kecepatan tinggi.
2. Smart False-Positive Filtering (Baseline 404 + Content Hashing).
3. Intelligent Crawler & Parameter Discovery.
4. Advanced Secret Pattern Matching (Regex Heuristics).
5. Security Header & Technology Fingerprinting.
6. Comprehensive JSON Reporting.

PERINGATAN HUKUM (LEGAL DISCLAIMER):
Alat ini hanya ditujukan untuk tujuan edukasi, audit keamanan internal (self-audit),
dan pengujian penetrasi yang sah dengan izin tertulis dari pemilik aset.
Penggunaan alat ini untuk menyerang sistem tanpa izin adalah tindakan ilegal
yang melanggar undang-undang siber (UU ITE Pasal 30-32, CFAA, Computer Misuse Act, dll).
Pengguna bertanggung jawab penuh atas segala konsekuensi hukum dari penggunaan alat ini.

PENGGUNAAN:
python3 nexus_ultimate_audit.py <target_url> --mode [passive|active|full]
"""

import asyncio
import aiohttp
import argparse
import json
import re
import sys
import hashlib
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass, asdict
import ssl

# Konfigurasi Global
VERSION = "3.0.0-ULTIMATE"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 NexusAuditBot"
MAX_CONCURRENT_REQUESTS = 50
TIMEOUT_SECONDS = 10

# --- LEGAL & ETHICAL MODULE ---

def show_legal_disclaimer():
    print(r"""
    ================================================================================
       NEXUS ULTIMATE AUDIT ENGINE v3.0 - PROFESSIONAL SECURITY TOOL
    ================================================================================
    
    ⚠️  PERINGATAN HUKUM KERAS (STRICT LEGAL WARNING) ⚠️
    
    Alat ini dirancang KHUSUS untuk:
    1. Audit keamanan diri sendiri (Self-Audit / Only Me).
    2. Pengujian penetrasi dengan izin tertulis resmi (Authorized Penetration Testing).
    3. Program Bug Bounty yang sah sesuai scope yang ditentukan.
    
    TINDAKAN ILEGAL:
    Menggunakan alat ini untuk mengakses, memindai, atau menyerang sistem komputer
    milik pihak lain TANPA IZIN EKSPLESIT adalah tindak pidana.
    
    Dasar Hukum (Indonesia):
    - UU ITE No. 11 Tahun 2008 (Pasal 30, 31, 32): Akses Ilegal, Penyadapan, Manipulasi Data.
    - KUHP Pasal 480: Penggunaan alat untuk kejahatan komputer.
    
    Dasar Hukum (Internasional):
    - Computer Fraud and Abuse Act (CFAA) - USA
    - Computer Misuse Act 1990 - UK
    
    PENGGUNA MENYETUJUI BAHWA:
    "Saya adalah pemilik sah dari target yang akan diaudit, ATAU saya memiliki 
    izin tertulis yang sah untuk melakukan pengujian keamanan pada target ini."
    
    Pengembang tool ini TIDAK BERTANGGUNG JAWAB atas penyalahgunaan alat ini.
    ================================================================================
    """)

def confirm_authorization():
    print("\n[?] KONFIRMASI OTORISASI WAJIB")
    print("Apakah Anda memiliki izin sah atau merupakan pemilik dari target ini?")
    response = input("Ketik 'YA, SAYA PEMILIK/AUTORIZED' untuk melanjutkan: ").strip().upper()
    
    if response not in ["YA, SAYA PEMILIK/AUTORIZED", "YA"]:
        # Cek variasi input yang mungkin
        if "YA" not in response:
            print("\n❌ AKSES DITOLAK. Konfirmasi otorisasi gagal.")
            print("Alat ini tidak dapat dijalankan tanpa persetujuan legal.")
            sys.exit(1)
    
    print("\n✅ Otorisasi Diterima. Memulai Nexus Engine...")

# --- DATA MODELS ---

@dataclass
class ScanResult:
    url: str
    status_code: int
    content_length: int
    content_hash: str
    tech_stack: List[str]
    secrets_found: List[Dict[str, str]]
    headers_issues: List[str]
    is_hidden: bool  # Detected via diffing
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL

@dataclass
class CrawlNode:
    url: str
    method: str
    parameters: List[str]
    links_to: List[str]

# --- CORE ENGINE CLASSES ---

class SecretScanner:
    """Heuristic scanner for sensitive data patterns."""
    
    PATTERNS = {
        "AWS Access Key": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "AWS Secret Key": r"[A-Za-z0-9/+=]{40}",
        "Private Key": r"-----BEGIN (RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY-----",
        "GitHub Token": r"ghp_[a-zA-Z0-9]{36}",
        "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
        "Slack Token": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*",
        "Generic API Key": r"(?i)(api[_-]?key|apikey|secret[_-]?key)['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]",
        "JWT Token": r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+",
        "Password in URL": r"(?i)password=|passwd=|pwd=",
        "Database Connection": r"(?i)(mysql|postgres|mongodb|redis)://[^\s]+"
    }

    @staticmethod
    def scan(content: str) -> List[Dict[str, str]]:
        findings = []
        for name, pattern in SecretScanner.PATTERNS.items():
            matches = re.findall(pattern, content)
            for match in matches:
                # Sanitize output to avoid leaking full secrets in logs
                safe_match = match[:10] + "..." if len(match) > 10 else match
                findings.append({
                    "type": name,
                    "match_preview": safe_match,
                    "severity": "CRITICAL" if "Key" in name or "Private" in name else "HIGH"
                })
        return findings

class TechAnalyzer:
    """Fingerprint technologies based on headers and content."""
    
    SIGNATURES = {
        "WordPress": ["/wp-content/", "wp-includes", "WordPress"],
        "Joomla": ["/media/jui/", "Joomla!"],
        "Drupal": ["/sites/default/files/", "Drupal"],
        "Nginx": ["nginx"],
        "Apache": ["Apache"],
        "IIS": ["IIS", "ASP.NET"],
        "PHP": ["X-Powered-By: PHP", ".php"],
        "Python/Django": ["csrftoken", "Django"],
        "Ruby/Rails": ["X-Runtime", "Ruby"],
        "React": ["react", "_reactRoot"],
        "Angular": ["ng-version", "angular"],
        "jQuery": ["jquery"]
    }

    @staticmethod
    def analyze(headers: Dict[str, str], content: str) -> List[str]:
        techs = []
        content_lower = content.lower()
        
        # Check Headers
        for header, value in headers.items():
            h_lower = f"{header}: {value}".lower()
            for tech, signs in TechAnalyzer.SIGNATURES.items():
                if any(sign.lower() in h_lower for sign in signs):
                    if tech not in techs: techs.append(tech)

        # Check Content
        for tech, signs in TechAnalyzer.SIGNATURES.items():
            if any(sign.lower() in content_lower for sign in signs):
                if tech not in techs: techs.append(tech)
                
        return techs

class NexusEngine:
    """Main Asynchronous Scanning Engine."""

    def __init__(self, target_url: str, mode: str = "passive"):
        self.target_url = target_url.rstrip('/')
        self.mode = mode
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[ScanResult] = []
        self.crawled_urls: Set[str] = set()
        self.to_crawl: List[str] = [self.target_url]
        self.baseline_404_hash: Optional[str] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        # Wordlist for directory fuzzing (Common paths)
        self.common_paths = [
            "/admin", "/login", "/dashboard", "/api", "/v1", "/v2", 
            "/backup", "/db", "/sql", "/.env", "/config.php", "/wp-admin",
            "/phpinfo.php", "/test", "/dev", "/staging", "/git", "/.git/config",
            "/robots.txt", "/sitemap.xml", "/.htaccess", "/web.config"
        ]

    async def start(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=MAX_CONCURRENT_REQUESTS)
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers={"User-Agent": USER_AGENT}
        ) as self.session:
            
            print(f"\n🚀 Memulai Scan Target: {self.target_url}")
            print(f"🛡️ Mode: {self.mode.upper()}")
            
            # 1. Baseline Check (404 Detection)
            await self.get_baseline_404()
            
            # 2. Initial Scan
            await self.scan_url(self.target_url)
            
            # 3. Active Mode Tasks
            if self.mode in ["active", "full"]:
                print("\n🔥 Mode Aktif: Memulai Directory Fuzzing & Deep Crawl...")
                tasks = [self.fuzz_directory(path) for path in self.common_paths]
                await asyncio.gather(*tasks)
                
                print("\n🕸️ Memulai Intelligent Crawler...")
                await self.run_crawler()
            
            # 4. Generate Report
            self.generate_report()

    async def get_baseline_404(self):
        """Mendapatkan hash respon halaman 404 untuk filtering false positive."""
        random_path = f"/{hashlib.md5(str(time.time()).encode()).hexdigest()}"
        url = f"{self.target_url}{random_path}"
        try:
            async with self.session.get(url) as resp:
                if resp.status == 404:
                    content = await resp.text()
                    self.baseline_404_hash = hashlib.md5(content.encode()).hexdigest()
                    print(f"✅ Baseline 404 Terdeteksi (Hash: {self.baseline_404_hash[:8]}...)")
                else:
                    print(f"⚠️ Server tidak mengembalikan 404 untuk path acak (Status: {resp.status}). Filtering mungkin kurang akurat.")
        except Exception:
            print("⚠️ Gagal mendapatkan baseline 404.")

    async def scan_url(self, url: str) -> Optional[ScanResult]:
        async with self.semaphore:
            try:
                async with self.session.get(url, allow_redirects=True) as resp:
                    content = await resp.text()
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Smart Filtering: Cek apakah ini false positive (halaman custom 404)
                    is_false_positive = False
                    if resp.status == 200 and self.baseline_404_hash:
                        if content_hash == self.baseline_404_hash:
                            is_false_positive = True
                    
                    if is_false_positive:
                        return None

                    # Analisis
                    techs = TechAnalyzer.analyze(dict(resp.headers), content)
                    secrets = SecretScanner.scan(content)
                    
                    # Cek Header Keamanan
                    headers_issues = []
                    required_headers = ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options"]
                    for h in required_headers:
                        if h not in resp.headers:
                            headers_issues.append(f"Missing: {h}")
                    
                    risk = "LOW"
                    if secrets: risk = "CRITICAL"
                    elif headers_issues and len(headers_issues) > 2: risk = "MEDIUM"
                    
                    result = ScanResult(
                        url=url,
                        status_code=resp.status,
                        content_length=len(content),
                        content_hash=content_hash,
                        tech_stack=techs,
                        secrets_found=secrets,
                        headers_issues=headers_issues,
                        is_hidden=False, # Akan diupdate jika hasil fuzzing
                        risk_level=risk
                    )
                    
                    self.results.append(result)
                    
                    # Output Real-time
                    status_color = "\033[92m" if resp.status == 200 else "\033[93m"
                    reset = "\033[0m"
                    secret_alert = " 🔴 SECRETS FOUND!" if secrets else ""
                    print(f"[{status_color}{resp.status}{reset}] {url} {secret_alert}")
                    
                    # Extract links for crawling
                    if resp.status == 200:
                        await self.extract_links(content, url)
                        
                    return result

            except asyncio.TimeoutError:
                print(f"⏱️ Timeout: {url}")
            except Exception as e:
                # Ignore connection errors for cleaner output
                pass
        return None

    async def fuzz_directory(self, path: str):
        url = f"{self.target_url}{path}"
        res = await self.scan_url(url)
        if res and res.status_code == 200:
            # Tandai sebagai hidden resource jika bukan link umum
            res.is_hidden = True
            res.risk_level = "HIGH" if "admin" in path or "backup" in path else "MEDIUM"

    async def extract_links(self, content: str, base_url: str):
        # Regex sederhana untuk href
        links = re.findall(r'href=[\'"]?([^\'" >]+)', content)
        for link in links:
            full_url = urljoin(base_url, link)
            # Filter hanya domain yang sama
            if urlparse(full_url).netloc == urlparse(self.target_url).netloc:
                if full_url not in self.crawled_urls and full_url not in self.to_crawl:
                    # Batasi depth atau jumlah antrian jika perlu
                    if len(self.to_crawl) < 200: 
                        self.to_crawl.append(full_url)

    async def run_crawler(self):
        tasks = []
        while self.to_crawl:
            batch = self.to_crawl[:20] # Batch kecil
            self.to_crawl = self.to_crawl[20:]
            
            for url in batch:
                if url not in self.crawled_urls:
                    self.crawled_urls.add(url)
                    tasks.append(self.scan_url(url))
            
            if tasks:
                await asyncio.gather(*tasks)
                tasks = []
                # Yield control event loop
                await asyncio.sleep(0.1)

    def generate_report(self):
        filename = f"nexus_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "target": self.target_url,
            "scan_time": datetime.now().isoformat(),
            "mode": self.mode,
            "summary": {
                "total_pages_scanned": len(self.results),
                "critical_findings": len([r for r in self.results if r.risk_level == "CRITICAL"]),
                "high_risk": len([r for r in self.results if r.risk_level == "HIGH"]),
                "secrets_leaked": sum(len(r.secrets_found) for r in self.results),
                "technologies_detected": list(set(t for r in self.results for t in r.tech_stack))
            },
            "findings": [asdict(r) for r in self.results if r.secrets_found or r.headers_issues or r.is_hidden]
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=4)
        
        print("\n" + "="*50)
        print(f"✅ SCAN SELESAI. Laporan tersimpan di: {filename}")
        print(f"📊 Ringkasan:")
        print(f"   - Total Halaman: {report_data['summary']['total_pages_scanned']}")
        print(f"   - Temuan Kritis: {report_data['summary']['critical_findings']}")
        print(f"   - Secrets Bocor: {report_data['summary']['secrets_leaked']}")
        print("="*50)

# --- MAIN EXECUTION ---

def main():
    parser = argparse.ArgumentParser(description="Nexus Ultimate Audit Engine")
    parser.add_argument("target", help="Target URL (e.g., https://example.com)")
    parser.add_argument("--mode", choices=["passive", "active", "full"], default="passive",
                        help="Scan mode: passive (safe), active (fuzzing), full (all)")
    
    args = parser.parse_args()
    
    # Validasi URL
    if not args.target.startswith("http"):
        print("❌ Error: URL harus dimulai dengan http:// atau https://")
        sys.exit(1)
    
    show_legal_disclaimer()
    confirm_authorization()
    
    try:
        engine = NexusEngine(args.target, args.mode)
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        print("\n⚠️ Scan dihentikan oleh pengguna.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Terjadi kesalahan: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
