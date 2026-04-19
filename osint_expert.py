#!/usr/bin/env python3
"""
AI-Powered OSINT Framework (Expert Level)
Fokus: Fitur Kerja Nyata, Over-Powered by AI Logic, Self-Audit First.
Tanpa gimmick. Murni fungsionalitas teknis.
"""

import os
import sys
import json
import re
import socket
import whois
import dns.resolver
from urllib.parse import urlparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import argparse

# Konfigurasi Warna Terminal
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

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}======================================================
   AI-POWERED OSINT FRAMEWORK [EXPERT MODE]
   Status: ACTIVE | Mode: WORK & OVER-POWERED
======================================================{Colors.RESET}
"""
    print(banner)

def legal_disclaimer():
    """Peringatan hukum dan etika yang ketat."""
    print(f"{Colors.RED}{Colors.BOLD}[PERINGATAN KERAS]{Colors.RESET}")
    print("Alat ini dirancang untuk AUDIT DIRI SENDIRI (Self-OSINT) dan RISET KEAMANAN sah.")
    print("Penggunaan untuk doxing, pelecehan, atau aktivitas ilegal adalah tanggung jawab pengguna.")
    print("Penulis tidak bertanggung jawab atas penyalahgunaan alat ini.")
    print(f"{Colors.YELLOW}Referensi: UU ITE (Indonesia), GDPR (Eropa), CFAA (USA).{Colors.RESET}")
    print("-" * 60)

def confirm_action(message):
    """Konfirmasi aksi kritis."""
    while True:
        choice = input(f"{Colors.YELLOW}[?] {message} (yes/no): {Colors.RESET}").lower()
        if choice in ['yes', 'y']:
            return True
        elif choice in ['no', 'n']:
            return False
        print("Input tidak valid. Ketik 'yes' atau 'no'.")

# --- MODULE 1: DOMAIN & NETWORK INTELLIGENCE ---

def get_whois_info(domain):
    """Mengambil data WHOIS mendetail."""
    print(f"\n{Colors.BLUE}[*] Mengambil data WHOIS untuk: {domain}{Colors.RESET}")
    try:
        w = whois.whois(domain)
        data = {
            "Registrar": w.registrar,
            "Creation Date": w.creation_date,
            "Expiration Date": w.expiration_date,
            "Name Servers": w.name_servers,
            "Status": w.status,
            "Emails": w.emails,
            "Org": w.org
        }
        print(json.dumps(data, indent=2, default=str))
        return data
    except Exception as e:
        print(f"{Colors.RED}[!] Error WHOIS: {e}{Colors.RESET}")
        return None

def get_dns_records(domain):
    """Analisis rekam jejak DNS (A, MX, TXT, NS)."""
    print(f"\n{Colors.BLUE}[*] Analisis DNS Records: {domain}{Colors.RESET}")
    records = ["A", "MX", "TXT", "NS", "SOA"]
    results = {}
    
    for record_type in records:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            results[record_type] = [str(rdata) for rdata in answers]
            print(f"{Colors.GREEN}[+] {record_type}: {results[record_type]}{Colors.RESET}")
        except dns.resolver.NoAnswer:
            print(f"{Colors.YELLOW}[-] Tidak ada record {record_type}{Colors.RESET}")
        except dns.resolver.NXDOMAIN:
            print(f"{Colors.RED}[!] Domain tidak ditemukan.{Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.RED}[!] Error pada {record_type}: {e}{Colors.RESET}")
    return results

def check_subdomains(domain):
    """Bruteforce subdomain sederhana namun efektif."""
    print(f"\n{Colors.BLUE}[*] Memindai Subdomain Umum...{Colors.RESET}")
    common_subs = ["www", "mail", "ftp", "admin", "dev", "test", "api", "stage", "prod"]
    found = []
    
    for sub in common_subs:
        fqdn = f"{sub}.{domain}"
        try:
            socket.gethostbyname(fqdn)
            print(f"{Colors.GREEN}[+] DITEMUKAN: {fqdn}{Colors.RESET}")
            found.append(fqdn)
        except socket.gaierror:
            pass
    return found

# --- MODULE 2: WEB RECONNAISSANCE ---

def analyze_web_headers(url):
    """Analisis keamanan header HTTP."""
    if not url.startswith("http"):
        url = "https://" + url
    
    print(f"\n{Colors.BLUE}[*] Menganalisis Header Keamanan: {url}{Colors.RESET}")
    try:
        response = requests.get(url, timeout=10)
        headers = response.headers
        
        security_headers = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection"
        ]
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Server: {headers.get('Server', 'Hidden')}")
        print(f"Tech Stack (X-Powered-By): {headers.get('X-Powered-By', 'Hidden')}")
        
        print("\n--- Audit Keamanan Header ---")
        for header in security_headers:
            if header in headers:
                print(f"{Colors.GREEN}[OK] {header}: {headers[header]}{Colors.RESET}")
            else:
                print(f"{Colors.RED}[MISSING] {header}{Colors.RESET}")
                
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}[!] Gagal mengakses target: {e}{Colors.RESET}")

def extract_emails_from_url(url):
    """Scraping email dari halaman web target."""
    if not url.startswith("http"):
        url = "https://" + url
        
    print(f"\n{Colors.BLUE}[*] Scraping Email dari: {url}{Colors.RESET}")
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Regex pola email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = set(re.findall(email_pattern, response.text))
        
        if emails:
            print(f"{Colors.GREEN}[+] Ditemukan {len(emails)} email:{Colors.RESET}")
            for email in emails:
                print(f"   - {email}")
        else:
            print(f"{Colors.YELLOW}[-] Tidak ada email ditemukan.{Colors.RESET}")
            
    except Exception as e:
        print(f"{Colors.RED}[!] Error scraping: {e}{Colors.RESET}")

# --- MODULE 3: USERNAME ENUMERATION (AI LOGIC SIMULATION) ---

def check_username_platform(username, platform, url_template):
    """Cek keberadaan username di platform tertentu."""
    try:
        url = url_template.format(username)
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            # Logika sederhana: jika halaman tidak mengembalikan 404, anggap ada
            # (Bisa diperbaiki dengan parsing konten spesifik per platform)
            print(f"{Colors.GREEN}[+] FOUND: {platform} -> {url}{Colors.RESET}")
            return True
        else:
            return False
    except Exception as e:
        # Tangkap error format URL atau network error
        return False

def username_osint(username):
    """Enumerasi username lintas platform."""
    print(f"\n{Colors.BLUE}[*] Mencari Username '{username}' di Platform Global...{Colors.RESET}")
    
    platforms = {
        "GitHub": "https://github.com/{}",
        "Instagram": "https://instagram.com/{}",
        "Twitter/X": "https://twitter.com/{}",
        "Facebook": "https://facebook.com/{}",
        "TikTok": "https://tiktok.com/@{}",
        "Pinterest": "https://pinterest.com/{}",
        "Reddit": "https://reddit.com/user/{}",
        "Docker Hub": "https://hub.docker.com/u/{}",
        "Medium": "https://medium.com/@{}"
    }
    
    found_accounts = []
    
    for platform, url_template in platforms.items():
        if check_username_platform(username, platform, url_template):
            found_accounts.append(platform)
            
    if not found_accounts:
        print(f"{Colors.YELLOW}[-] Tidak ditemukan akun publik signifikan.{Colors.RESET}")
    else:
        print(f"\n{Colors.GREEN}[SUMMARY] Ditemukan di: {', '.join(found_accounts)}{Colors.RESET}")
    
    return found_accounts

# --- MAIN EXECUTION ---

def main():
    legal_disclaimer()
    
    # Mode ONLY ME Confirmation
    print(f"\n{Colors.MAGENTA}MODE: SELF-AUDIT (ONLY ME){Colors.RESET}")
    if not confirm_action("Apakah Anda yakin ini adalah data DIRI SENDIRI untuk tujuan audit keamanan?"):
        print("Operasi dibatalkan. Keamanan adalah prioritas.")
        sys.exit(0)

    print_banner()
    
    print(f"{Colors.WHITE}Pilih Modul Eksekusi:{Colors.RESET}")
    print("1. Domain Intelligence (WHOIS, DNS, Subdomain)")
    print("2. Web Reconnaissance (Headers, Email Scraping)")
    print("3. Username Enumeration (Cross-Platform)")
    print("4. Full Scan (Semua di atas)")
    print("0. Keluar")
    
    choice = input("\n[>] Pilih opsi (0-4): ")
    
    target = input("[>] Masukkan Target (Domain/URL/Username): ").strip()
    
    if not target:
        print("Target tidak boleh kosong.")
        sys.exit(1)

    if choice == '1':
        # Domain Intel
        if not (target.startswith("http") or "." in target):
             print("Format target harus domain (contoh: google.com)")
        else:
            clean_domain = target.replace("https://", "").replace("http://", "").split("/")[0]
            get_whois_info(clean_domain)
            get_dns_records(clean_domain)
            check_subdomains(clean_domain)
            
    elif choice == '2':
        # Web Recon
        if not target.startswith("http"):
            target = "https://" + target
        analyze_web_headers(target)
        extract_emails_from_url(target)
        
    elif choice == '3':
        # Username
        username_osint(target)
        
    elif choice == '4':
        # Full Scan Logic
        print(f"\n{Colors.RED}[*] MEMULAI FULL SCAN TERHADAP: {target}{Colors.RESET}")
        
        # Cek apakah input domain atau username
        is_domain = "." in target and not target.startswith("http")
        
        if is_domain:
            get_whois_info(target)
            get_dns_records(target)
            check_subdomains(target)
            # Asumsi website ada
            analyze_web_headers(target)
            extract_emails_from_url(target)
        else:
            username_osint(target)
            
    elif choice == '0':
        sys.exit(0)
        
    else:
        print("Opsi tidak valid.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Interupsi diterima. Program berhenti.{Colors.RESET}")
        sys.exit(0)
