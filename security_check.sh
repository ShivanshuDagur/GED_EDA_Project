#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# General Pre-Run Security Checker (static triage)
# -----------------------------------------------------------------------------
# What this script does
# - Runs a quick static security triage on a repository BEFORE you install or run it.
# - Looks for risky code patterns, suspicious network/exfiltration indicators,
#   potential secret leakage, unsafe web patterns, and dependency risk signals.
# - Produces a timestamped plaintext report and returns a risk-based exit code.
#
# How it works
# 1) Pattern scan across source files:
#    - Uses `rg` (ripgrep) when available, otherwise falls back to `grep`.
#    - Searches with curated regexes for common dangerous primitives.
# 2) Optional security tools (if installed):
#    - `pip-audit` for vulnerable Python packages.
#    - `bandit` for Python static analysis.
#    - `semgrep` for multi-language static analysis.
#    - `gitleaks` for secret detection.
# 3) Aggregates findings into HIGH / MEDIUM / LOW / INFO counters.
#
# How to run
# - Scan current repository:
#     ./security_check.sh .
# - Scan another repository:
#     ./security_check.sh /path/to/repo
# - Use a custom report directory:
#     ./security_check.sh /path/to/repo /path/to/report_dir
#
# How to read the report
# - Report file path is printed at the end and stored under:
#     <target>/.security_reports/security_scan_YYYYMMDD_HHMMSS.txt
# - Each section contains either:
#     [OK]      -> no matches for that check
#     [HIGH]    -> high-priority manual review needed
#     [MEDIUM]  -> meaningful risk signal to investigate
#     [LOW]     -> informational hygiene/smell
#     [INFO]    -> context/tool availability
# - Only first 40 matching lines are shown per check for readability.
#
# Exit codes (useful for CI/pre-commit gating)
# - 0 = LOW overall risk (no HIGH/MEDIUM findings)
# - 1 = MEDIUM overall risk (at least one MEDIUM, no HIGH)
# - 2 = HIGH overall risk (at least one HIGH)
#
# Important limitations
# - Static triage is not proof of safety; false positives and false negatives exist.
# - Always manually inspect flagged lines before deciding to trust/run a project.
# -----------------------------------------------------------------------------

set -u

TARGET_DIR="${1:-.}"
REPORT_ROOT="${2:-}"

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "[ERROR] Target directory not found: $TARGET_DIR"
  exit 1
fi

TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
if [[ -z "$REPORT_ROOT" ]]; then
  REPORT_ROOT="$TARGET_DIR/.security_reports"
fi
mkdir -p "$REPORT_ROOT"

TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
REPORT_FILE="$REPORT_ROOT/security_scan_${TIMESTAMP}.txt"

HIGH_COUNT=0
MEDIUM_COUNT=0
LOW_COUNT=0
INFO_COUNT=0

EXCLUDE_GLOBS=(
  --glob '!.git/**'
  --glob '!.security_reports/**'
  --glob '!node_modules/**'
  --glob '!venv/**'
  --glob '!.venv/**'
  --glob '!dist/**'
  --glob '!build/**'
  --glob '!target/**'
  --glob '!__pycache__/**'
  --glob '!.mypy_cache/**'
  --glob '!.pytest_cache/**'
  --glob '!.next/**'
  --glob '!coverage/**'
  --glob '!security_check.sh'
)

log() {
  echo "$*"
}

section() {
  echo
  echo "============================================================"
  echo "$*"
  echo "============================================================"
}

bump() {
  local sev="$1"
  case "$sev" in
    HIGH) HIGH_COUNT=$((HIGH_COUNT + 1)) ;;
    MEDIUM) MEDIUM_COUNT=$((MEDIUM_COUNT + 1)) ;;
    LOW) LOW_COUNT=$((LOW_COUNT + 1)) ;;
    INFO) INFO_COUNT=$((INFO_COUNT + 1)) ;;
  esac
}

scan_rg() {
  local severity="$1"
  local label="$2"
  local regex="$3"

  local output
  if command -v rg >/dev/null 2>&1; then
    output=$(rg -n -S --hidden "${EXCLUDE_GLOBS[@]}" -e "$regex" "$TARGET_DIR" 2>/dev/null || true)
  else
    output=$(grep -RInE \
      --exclude-dir=.git \
      --exclude-dir=.security_reports \
      --exclude-dir=node_modules \
      --exclude-dir=.venv \
      --exclude-dir=venv \
      --exclude-dir=build \
      --exclude-dir=dist \
      --exclude-dir=target \
      --exclude-dir=__pycache__ \
      --exclude-dir=.pytest_cache \
      --exclude-dir=.mypy_cache \
      --exclude=security_check.sh \
      "$regex" "$TARGET_DIR" 2>/dev/null || true)
  fi

  if [[ -n "$output" ]]; then
    log "[$severity] $label"
    echo "$output" | head -n 40
    local lines
    lines=$(echo "$output" | wc -l | tr -d ' ')
    if [[ "$lines" -gt 40 ]]; then
      log "  ... truncated ($lines matches total)"
    fi
    bump "$severity"
  else
    log "[OK] $label"
  fi
}

scan_file_exists() {
  local severity="$1"
  local label="$2"
  local file="$3"
  if [[ -f "$TARGET_DIR/$file" ]]; then
    log "[$severity] $label -> $file"
    bump "$severity"
  else
    log "[OK] $label"
  fi
}

run_optional_tool() {
  local tool_name="$1"
  shift
  local severity_on_findings="$1"
  shift

  if ! command -v "$tool_name" >/dev/null 2>&1; then
    log "[INFO] Optional tool not installed: $tool_name"
    bump "INFO"
    return
  fi

  log "[INFO] Running optional tool: $tool_name"
  if "$@"; then
    log "[OK] $tool_name completed"
  else
    log "[$severity_on_findings] $tool_name reported issues or exited non-zero"
    bump "$severity_on_findings"
  fi
}

# Mirror all output to both terminal and report file.
exec > >(tee -a "$REPORT_FILE") 2>&1

section "General Security Check"
log "Target: $TARGET_DIR"
log "Report: $REPORT_FILE"
log "Time: $(date)"

section "1) Quick Repository Indicators"
scan_file_exists "LOW" "Contains shell profile/autoload file" ".bashrc"
scan_file_exists "LOW" "Contains shell profile/autoload file" ".zshrc"
scan_file_exists "LOW" "Contains shell profile/autoload file" ".profile"
scan_file_exists "LOW" "Contains local env file" ".env"

if command -v rg >/dev/null 2>&1; then
  scan_rg "MEDIUM" "Suspicious install hooks in package.json" '"(preinstall|install|postinstall|prepare)"\s*:'
  scan_rg "LOW" "Binary/compiled artifacts committed" '\\.(exe|dll|dylib|so|class|jar|ps1|bat)$'
else
  scan_rg "MEDIUM" "Suspicious install hooks in package.json" '"(preinstall|install|postinstall|prepare)"[[:space:]]*:'
  scan_rg "LOW" "Binary/compiled artifacts committed" '\\.(exe|dll|dylib|so|class|jar|ps1|bat)$'
fi

section "2) High-Risk Code Patterns"
scan_rg "HIGH" "Dynamic code execution" 'eval\s*\(|exec\s*\(|compile\s*\(|__import__\s*\('
scan_rg "HIGH" "Shell execution with potential injection risk" 'os\.system\s*\(|subprocess\.(Popen|run|call)\s*\(|child_process\.(exec|execSync)\s*\(|Runtime\.getRuntime\(\)\.exec\s*\('
scan_rg "HIGH" "Potential command injection (shell=True or string shell)" 'shell\s*=\s*True|bash\s+-c|sh\s+-c|powershell\s+-'
scan_rg "HIGH" "Potential unsafe deserialization" 'pickle\.loads\s*\(|yaml\.load\s*\(|marshal\.loads\s*\('
scan_rg "HIGH" "Direct file deletion operations" 'shutil\.rmtree\s*\(|os\.remove\s*\(|os\.unlink\s*\(|rm\s+-rf\s+'

section "3) Network and Data Exfiltration Signals"
scan_rg "MEDIUM" "Network clients and outbound requests" 'requests\.(get|post|put|delete)\s*\(|urllib\.|httpx\.|socket\.|ftplib\.|paramiko\.'
scan_rg "HIGH" "Suspicious exfil channels or webhooks" 'webhook|discord\.com/api/webhooks|api\.telegram\.org|pastebin|transfer\.sh|ngrok'
scan_rg "MEDIUM" "Encoded/obfuscated payload patterns" 'base64\.b64decode\s*\(|frombase64string\s*\(|atob\s*\('

section "4) Secrets and Credential Leakage"
scan_rg "HIGH" "Hardcoded cloud/API keys" 'AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]+'
scan_rg "MEDIUM" "Potential hardcoded secrets" '(api[_-]?key|secret|token|password)\s*[:=]\s*["'"'"'][^"'"'"']{8,}["'"'"']'
scan_rg "LOW" "Dotenv usage (check .env handling)" 'dotenv|OPENAI_API_KEY|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN'

section "5) Unsafe Web Patterns"
scan_rg "MEDIUM" "Possible XSS sinks in frontend templates/js" 'innerHTML\s*=|document\.write\s*\(|onerror\s*=|javascript:'
scan_rg "MEDIUM" "Template rendering of user-controlled HTML" '\|safe\b|Markup\('

section "6) Dependency and Tooling Checks"
if [[ -f "$TARGET_DIR/requirements.txt" ]]; then
  log "[INFO] Found Python requirements.txt"
  bump "INFO"
fi
if [[ -f "$TARGET_DIR/pyproject.toml" ]]; then
  log "[INFO] Found pyproject.toml"
  bump "INFO"
fi
if [[ -f "$TARGET_DIR/package.json" ]]; then
  log "[INFO] Found package.json"
  bump "INFO"
fi

if command -v pip-audit >/dev/null 2>&1; then
  if [[ -f "$TARGET_DIR/requirements.txt" ]]; then
    log "[INFO] Running pip-audit on requirements.txt"
    if (cd "$TARGET_DIR" && pip-audit -r requirements.txt); then
      log "[OK] pip-audit found no known vulnerabilities"
    else
      log "[MEDIUM] pip-audit reported known vulnerabilities"
      bump "MEDIUM"
    fi
  else
    log "[INFO] pip-audit installed, but requirements.txt not found at repo root"
    bump "INFO"
  fi
else
  log "[INFO] Optional tool not installed: pip-audit"
  bump "INFO"
fi

if command -v bandit >/dev/null 2>&1; then
  log "[INFO] Running bandit (Python SAST)"
  if (cd "$TARGET_DIR" && bandit -r . -x .venv,venv,node_modules,build,dist,target,.git); then
    log "[OK] bandit completed with no findings"
  else
    log "[MEDIUM] bandit reported findings"
    bump "MEDIUM"
  fi
else
  log "[INFO] Optional tool not installed: bandit"
  bump "INFO"
fi

if command -v semgrep >/dev/null 2>&1; then
  log "[INFO] Running semgrep quick scan"
  if (cd "$TARGET_DIR" && semgrep --config auto --error --quiet); then
    log "[OK] semgrep quick scan completed"
  else
    log "[MEDIUM] semgrep reported findings"
    bump "MEDIUM"
  fi
else
  log "[INFO] Optional tool not installed: semgrep"
  bump "INFO"
fi

if command -v gitleaks >/dev/null 2>&1; then
  log "[INFO] Running gitleaks working-tree scan"
  if (cd "$TARGET_DIR" && gitleaks detect --source . --no-git --redact); then
    log "[OK] gitleaks found no leaks"
  else
    log "[HIGH] gitleaks reported potential secret leaks"
    bump "HIGH"
  fi
else
  log "[INFO] Optional tool not installed: gitleaks"
  bump "INFO"
fi

section "7) Summary"
log "High findings:   $HIGH_COUNT"
log "Medium findings: $MEDIUM_COUNT"
log "Low findings:    $LOW_COUNT"
log "Info items:      $INFO_COUNT"

# Overall risk decision rule:
# - HIGH takes precedence over MEDIUM/LOW.
# - MEDIUM applies only when there are no HIGH findings.
# - LOW means no HIGH or MEDIUM findings were recorded.

if [[ "$HIGH_COUNT" -gt 0 ]]; then
  echo
  log "Overall risk: HIGH"
  log "Recommendation: Do not execute project code yet. Manually review HIGH findings first."
  EXIT_CODE=2
elif [[ "$MEDIUM_COUNT" -gt 0 ]]; then
  echo
  log "Overall risk: MEDIUM"
  log "Recommendation: Review findings before running install/start commands."
  EXIT_CODE=1
else
  echo
  log "Overall risk: LOW"
  log "Recommendation: No obvious high-risk indicators from static pre-checks."
  EXIT_CODE=0
fi

echo
log "Report saved to: $REPORT_FILE"
log "Done."
exit "$EXIT_CODE"
