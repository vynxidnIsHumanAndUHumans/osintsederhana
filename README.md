# 🚀 NEXUS ULTIMATE UNIVERSAL OSINT ENGINE v5.0

**The Most Advanced Open-Source Intelligence & Security Audit Framework**

![Version](https://img.shields.io/badge/version-5.0.0--ULTIMATE--UNIVERSAL-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT--with--Ethical--Clause-orange)

---

## ⚠️ LEGAL DISCLAIMER

**THIS TOOL IS FOR AUTHORIZED SECURITY TESTING ONLY**

NEXUS ULTIMATE is designed exclusively for:
1. **Self-Audit** - Testing your own systems and digital footprint
2. **Authorized Penetration Testing** - With written permission from asset owners
3. **Bug Bounty Programs** - Within defined scope and rules of engagement

### Legal Consequences
Using this tool without authorization violates:
- **Indonesia**: UU ITE No. 11/2008 (Pasal 30-32), KUHP Pasal 480
- **USA**: Computer Fraud and Abuse Act (CFAA)
- **UK**: Computer Misuse Act 1990
- **EU**: GDPR Article 32, Cybercrime Directive

**Developers are NOT liable for misuse of this tool.**

---

## ✨ FEATURES

### 🔥 Core Capabilities

| Module | Description | Mode |
|--------|-------------|------|
| **Async Engine** | High-performance aiohttp-based scanning (100 concurrent requests) | All |
| **Smart Filtering** | Baseline 404 detection to eliminate false positives | All |
| **Secret Scanner** | 25+ patterns for AWS keys, tokens, passwords, configs | Active/Full |
| **Tech Fingerprinting** | Detect 15+ technologies (CMS, frameworks, servers) | All |
| **Directory Fuzzing** | 60+ sensitive paths (admin, backup, config, .env, .git) | Active/Full |
| **Subdomain Bruteforce** | 40+ common subdomains discovery | Active/Full |
| **Web Crawler** | Intelligent link extraction and recursive scanning | Full |
| **Username Enumeration** | 20+ platforms (GitHub, Instagram, Twitter, etc.) | Optional |
| **Security Headers Audit** | HSTS, CSP, X-Frame, X-Content-Type detection | All |
| **JSON Reporting** | Comprehensive forensics-ready reports | All |

### 🎯 Scan Modes

#### 🛡️ PASSIVE MODE
- Basic URL analysis
- Technology detection
- Security headers audit
- Secret scanning (if accessible)
- **No aggressive requests**

#### 🔥 ACTIVE MODE
- Everything in Passive +
- Directory/file fuzzing (60+ paths)
- Subdomain bruteforce (40+ subs)
- Hidden resource detection
- **Moderate aggression**

#### 💀 FULL MODE
- Everything in Active +
- Intelligent web crawling (up to 500 URLs)
- Deep link extraction
- Recursive analysis
- **Maximum coverage**

---

## 📦 INSTALLATION

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Install
```bash
cd /workspace
pip install aiohttp
python3 main.py --help
```

---

## 🚀 USAGE

```bash
# Passive scan
python3 main.py https://your-domain.com --mode passive

# Active scan with fuzzing
python3 main.py https://your-domain.com --mode active

# Full audit with crawler
python3 main.py https://your-domain.com --mode full

# Username enumeration
python3 main.py https://your-domain.com --username your_username --mode full
```

---

## 🔬 TECHNICAL SPECS

- **25+ Secret Patterns**: AWS, GitHub, Google, JWT, DB strings
- **15+ Tech Signatures**: WordPress, Django, React, Nginx, Cloudflare
- **20+ Platforms**: GitHub, IG, Twitter, TikTok, LinkedIn, etc.
- **60+ Sensitive Paths**: .env, .git, admin, backup, config
- **40+ Subdomains**: Common discovery wordlist

---

## ⚖️ LICENSE

MIT License with Ethical Clause - For authorized security testing only.

---

*Built with ❤️ for ethical hackers and security professionals*
