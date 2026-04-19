#!/usr/bin/env python3
"""
OSINT DATA MAPPING & RECONSTRUCTION TOOL
- Real-time HTML parsing for data extraction
- Node-based information mapping
- Vulnerability correlation
- Interactive graph visualization (text-based)
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import socket
import dns.resolver
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import whois
import argparse
from datetime import datetime

class OSINTMapper:
    def __init__(self, target):
        self.target = target
        self.data_nodes = defaultdict(list)
        self.vulnerabilities = []
        self.connections = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def extract_html_data(self, url):
        """Extract all data from HTML content"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract emails
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text))
            self.data_nodes['emails'].extend(list(emails))
            
            # Extract phone numbers
            phones = set(re.findall(r'\+?[\d\s\-\(\)]{10,}', response.text))
            self.data_nodes['phones'].extend(list(phones))
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                links.append(full_url)
            self.data_nodes['links'].extend(links)
            
            # Extract meta info
            meta_tags = {}
            for meta in soup.find_all('meta'):
                if meta.get('name') or meta.get('property'):
                    name = meta.get('name') or meta.get('property')
                    content = meta.get('content')
                    if content:
                        meta_tags[name] = content
            self.data_nodes['meta_info'].append(meta_tags)
            
            # Extract scripts and external resources
            scripts = [script.get('src') for script in soup.find_all('script', src=True)]
            self.data_nodes['external_scripts'].extend(scripts)
            
            # Extract forms
            forms = []
            for form in soup.find_all('form'):
                form_data = {
                    'action': form.get('action'),
                    'method': form.get('method', 'GET'),
                    'inputs': []
                }
                for input_tag in form.find_all(['input', 'textarea', 'select']):
                    input_data = {
                        'type': input_tag.get('type', 'text'),
                        'name': input_tag.get('name'),
                        'value': input_tag.get('value')
                    }
                    form_data['inputs'].append(input_data)
                forms.append(form_data)
            self.data_nodes['forms'].extend(forms)
            
            # Extract comments (potential info leaks)
            comments = soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--'))
            self.data_nodes['comments'].extend([str(c) for c in comments])
            
            return True
        except Exception as e:
            print(f"Error extracting HTML: {e}")
            return False
    
    def get_domain_info(self):
        """Get comprehensive domain information"""
        domain = urlparse(self.target).netloc or self.target
        if not '.' in domain:
            domain = f"{domain}.com"
            
        try:
            # WHOIS
            w = whois.whois(domain)
            self.data_nodes['whois'] = {
                'registrar': w.registrar,
                'creation_date': str(w.creation_date),
                'expiration_date': str(w.expiration_date),
                'name_servers': w.name_servers,
                'emails': w.emails if isinstance(w.emails, list) else [w.emails]
            }
            
            # DNS Records
            dns_records = {}
            for record_type in ['A', 'MX', 'TXT', 'NS', 'SOA']:
                try:
                    answers = dns.resolver.resolve(domain, record_type)
                    dns_records[record_type] = [str(rdata) for rdata in answers]
                except:
                    dns_records[record_type] = []
            self.data_nodes['dns_records'] = dns_records
            
            # IP Geolocation
            if dns_records['A']:
                ip = dns_records['A'][0]
                try:
                    geo_response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
                    geo_data = geo_response.json()
                    self.data_nodes['geo_location'] = geo_data
                except:
                    pass
                    
        except Exception as e:
            print(f"Error getting domain info: {e}")
    
    def check_vulnerabilities(self):
        """Check for common vulnerabilities"""
        # Check security headers
        try:
            response = self.session.get(self.target, timeout=10)
            headers = response.headers
            
            missing_headers = []
            critical_headers = [
                'Strict-Transport-Security',
                'Content-Security-Policy',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'X-XSS-Protection'
            ]
            
            for header in critical_headers:
                if header not in headers:
                    missing_headers.append(header)
                    self.vulnerabilities.append({
                        'type': 'Missing Security Header',
                        'severity': 'Medium',
                        'detail': f'Missing {header} header'
                    })
            
            # Check for exposed sensitive files
            sensitive_paths = [
                '/robots.txt', '/sitemap.xml', '/.git/config', 
                '/.env', '/wp-config.php', '/config.php'
            ]
            
            for path in sensitive_paths:
                try:
                    test_url = urljoin(self.target, path)
                    test_response = self.session.get(test_url, timeout=5)
                    if test_response.status_code == 200:
                        self.vulnerabilities.append({
                            'type': 'Exposed File',
                            'severity': 'High' if path in ['/.env', '/.git/config'] else 'Low',
                            'detail': f'{path} is accessible'
                        })
                        self.data_nodes['exposed_files'].append(path)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error checking vulnerabilities: {e}")
    
    def build_relationship_map(self):
        """Build relationships between data nodes"""
        # Email to domain relationships
        for email in self.data_nodes.get('emails', []):
            domain = email.split('@')[-1]
            self.connections.append({
                'source': email,
                'target': domain,
                'type': 'email_owner'
            })
        
        # Link relationships
        for link in self.data_nodes.get('links', [])[:20]:  # Limit to 20
            parsed = urlparse(link)
            if parsed.netloc:
                self.connections.append({
                    'source': self.target,
                    'target': parsed.netloc,
                    'type': 'external_link'
                })
        
        # IP to location relationships
        if 'geo_location' in self.data_nodes:
            geo = self.data_nodes['geo_location']
            if 'country' in geo and 'city' in geo:
                self.connections.append({
                    'source': geo.get('ip', 'Unknown'),
                    'target': f"{geo.get('city', '')}, {geo.get('country', '')}",
                    'type': 'geolocation'
                })
    
    def generate_report(self):
        """Generate comprehensive report"""
        report = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'data_nodes': dict(self.data_nodes),
            'vulnerabilities': self.vulnerabilities,
            'relationships': self.connections,
            'summary': {
                'total_emails': len(self.data_nodes.get('emails', [])),
                'total_links': len(self.data_nodes.get('links', [])),
                'total_vulnerabilities': len(self.vulnerabilities),
                'critical_issues': len([v for v in self.vulnerabilities if v.get('severity') == 'High'])
            }
        }
        return report
    
    def print_node_map(self):
        """Print text-based node map"""
        print("\n" + "="*60)
        print("🗺️  DATA NODE MAP")
        print("="*60)
        
        for node_type, data in self.data_nodes.items():
            if data:
                print(f"\n📌 {node_type.upper()} ({len(data)} items):")
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"   ├─ {key}: {value}")
                else:
                    for i, item in enumerate(data[:10]):  # Show first 10
                        print(f"   ├─ {item}")
                    if len(data) > 10:
                        print(f"   └─ ... and {len(data) - 10} more")
        
        if self.vulnerabilities:
            print("\n" + "!"*60)
            print("⚠️  VULNERABILITIES FOUND")
            print("!"*60)
            for vuln in self.vulnerabilities:
                severity_icon = "🔴" if vuln['severity'] == 'High' else "🟡"
                print(f"{severity_icon} [{vuln['severity']}] {vuln['type']}: {vuln['detail']}")
        
        if self.connections:
            print("\n" + "="*60)
            print("🔗 RELATIONSHIP GRAPH")
            print("="*60)
            for conn in self.connections[:15]:  # Show first 15
                print(f"{conn['source']} --[{conn['type']}]--> {conn['target']}")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║     OSINT DATA MAPPING & RECONSTRUCTION TOOL          ║
    ║     Advanced HTML Parsing + Node Relationship Map     ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Legal disclaimer
    print("""
    ⚠️  LEGAL DISCLAIMER:
    This tool is for EDUCATIONAL purposes and authorized security testing ONLY.
    Only use on domains/usernames you own or have explicit permission to test.
    Unauthorized scanning may violate laws (CFAA, Computer Misuse Act, etc.).
    By continuing, you confirm you have authorization to test the target.
    """)
    
    confirm = input("Do you have authorization to test this target? (yes/no): ").lower()
    if confirm != 'yes':
        print("❌ Access denied. You must have authorization.")
        return
    
    target = input("\nEnter target (URL or domain): ").strip()
    if not target.startswith('http'):
        target = 'https://' + target
    
    print(f"\n🎯 Starting reconnaissance on: {target}")
    print("This may take a few minutes...\n")
    
    mapper = OSINTMapper(target)
    
    # Step 1: Extract HTML data
    print("📥 Extracting HTML data...")
    mapper.extract_html_data(target)
    
    # Step 2: Get domain intelligence
    print("🔍 Gathering domain intelligence...")
    mapper.get_domain_info()
    
    # Step 3: Check vulnerabilities
    print("🛡️  Checking for vulnerabilities...")
    mapper.check_vulnerabilities()
    
    # Step 4: Build relationship map
    print("🔗 Building relationship map...")
    mapper.build_relationship_map()
    
    # Step 5: Generate and display report
    print("📊 Generating report...\n")
    mapper.print_node_map()
    
    # Save report
    report = mapper.generate_report()
    filename = f"osint_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Full report saved to: {filename}")
    print("\n✅ Reconnaissance complete!")

if __name__ == "__main__":
    main()
