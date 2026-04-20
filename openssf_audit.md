# OpenSSF Audit Report - AskGem v0.16.4

**Date:** 2026-04-20  
**Version:** 0.16.4  
**Auditor:** AI Assistant  

---

## Executive Summary

This document provides an assessment of AskGem's compliance with OpenSSF (Open Source Security Foundation) Best Practices and free software standards. The project demonstrates solid foundational security measures but has critical gaps that should be addressed to achieve a higher maturity level.

**Overall Rating: 6.5/10 (Adecuado)**

---

## 1. Free Software Standards Compliance

### License

| Criterion | Status |
|-----------|--------|
| OSI Approved License | ✅ YES - GPLv3 |
| License File Present | ✅ LICENSE (full text) |
| License Compatibility | ✅ Strong copyleft |

**Assessment:** AskGem uses GNU General Public License v3, which is an OSI-approved free software license. The full license text is included in the repository.

---

## 2. OpenSSF Best Practices

### 2.1 Security Measures (Implemented)

| Criterion | Status | Notes |
|-----------|--------|-------|
| SECURITY.md | ✅ YES | Clear vulnerability reporting policy |
| Trusted Dependencies | ✅ YES | Dependabot enabled for pip + actions |
| Secret Management | ✅ YES | Uses `keyring` (no plaintext secrets) |
| Human-in-the-Loop | ✅ YES | Manual mode requires user confirmation |
| TrustManager | ✅ YES | Filesystem boundaries enforcement |
| Input Sanitization | ✅ YES | Pydantic schemas + path validation |
| CI/CD Security | ✅ YES | Gitleaks workflow for secrets |

### 2.2 Critical Gaps

| Criterion | Status | Priority |
|-----------|--------|----------|
| SBOM (Software Bill of Materials) | ❌ MISSING | HIGH |
| Dependency Vulnerability Scanning | ⚠️ PARTIAL | HIGH |
| OSSF Scorecard | ❌ MISSING | MEDIUM |
| Signed Releases | ❌ MISSING | HIGH |
| CodeQL Analysis | ❌ MISSING | MEDIUM |
| Fuzzing Tests | ❌ MISSING | LOW |

---

## 3. Detailed Findings

### 3.1 Strengths

1. **Project Isolation (v0.16.4)** - The new `.askgem/` directory architecture provides proper project-level isolation, preventing context leakage.
2. **TrustManager** - Centralized trust model restricts write/execute tools to explicitly authorized directories via `trusted.json`.
3. **Credential Handling** - Integration with system-native credential store (`keyring`) ensures secrets are not stored in plaintext.

### 3.2 Vulnerabilities & Risks

1. **No SBOM** - Without a Software Bill of Materials, it's difficult to track transitive dependencies and respond quickly to CVE disclosures.
2. **Binary Integrity** - The `dist/askgem.exe` binary is not signed, making it vulnerable to tampering.

---

## 4. Implementation Roadmap (Closing the Gaps)

### 4.1 Generate SBOM (Software Bill of Materials)
To comply with NTIA standards, add this step to your `release.yml` or run manually:
```bash
# Install tool
pip install cyclonedx-bom

# Generate SBOM in JSON format
cyclonedx-py -o sbom.json --format json
```

### 4.2 Enable CodeQL Analysis
Create `.github/workflows/codeql.yml`:
```yaml
name: "CodeQL"
on: [push, pull_request]
jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: python
      - uses: github/codeql-action/analyze@v3
```

### 4.3 Add OSSF Scorecard
Create `.github/workflows/scorecard.yml`:
```yaml
name: Scorecard
on: [push, branch_protection_rule]
jobs:
  analysis:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: ossf/scorecard-action@v2.4.0
        with:
          publish_results: true
```

### 4.4 Sign Releases (Binary Integrity)
Implement signing in your release pipeline using `gpg`:
```bash
# Create detached signature
gpg --armor --detach-sign dist/askgem.exe
```

---

## 5. Future Improvements

- Implement COSIGN or Sigstore for binary signing
- Add fuzzing tests with `pytest-fuzz`
- Achieve OSSF Scorecard "A" rating

---

## 6. References

- [OpenSSF Best Practices](https://bestractices.openssf.org/)
- [OSSF Scorecard](https://securityscorecard.dev/)
