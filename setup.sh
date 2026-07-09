#!/bin/bash
#
# BeeWeave setup — configures skill discovery for all supported AI agents.
#
# Usage:
#   bash setup.sh
#   bash setup.sh --agents all
#   bash setup.sh --agents claude,codex,gemini
#   bash setup.sh --global-extra beeweave-capture,beeweave-context-pack
#
# What it does:
#   1. Creates .env from .env.example (if not present)
#   2. Writes ~/.beeweave/config so skills work from any project
#   3. Installs skills for the selected agents:
#      Project-local (full skill set):
#        - .claude/skills/        (Claude Code)
#        - .cursor/skills/        (Cursor)
#        - .windsurf/skills/      (Windsurf)
#        - .agents/skills/        (AGENTS.md-aware agents, OpenClaw, generic)
#        - .kiro/skills/          (Kiro IDE/CLI)
#      Global (portable skills only: beeweave-update, beeweave-query, beeweave-ingest):
#        - ~/.claude/skills/      (Claude Code)
#        - ~/.gemini/skills/      (Gemini CLI)
#        - ~/.codex/skills/       (Codex)
#        - ~/.hermes/skills/      (Hermes)
#        - ~/.openclaw/skills/    (OpenClaw)
#        - ~/.copilot/skills/     (GitHub Copilot CLI)
#        - ~/.trae/skills/        (Trae)
#        - ~/.trae-cn/skills/     (Trae CN)
#        - ~/.kiro/skills/        (Kiro CLI)
#        - ~/.agents/skills/      (OpenCode, Aider, Factory Droid, generic)
#   4. Bootstraps AGENTS.md aliases (CLAUDE.md, GEMINI.md, HERMES.md)
#   5. Prints a summary of what's ready
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/.skills"
WIKI_SKILLS_DIR="$SKILLS_DIR/wiki"
WORKBENCH_SKILLS_DIR="$SKILLS_DIR/workbench"
CORE_PORTABLE_SKILLS=(beeweave-update beeweave-query beeweave-ingest)
RECOMMENDED_GLOBAL_EXTRA_SKILLS=(beeweave-capture beeweave-context-pack beeweave-digest beeweave-status beeweave-memory-bridge)
PORTABLE_SKILLS=("${CORE_PORTABLE_SKILLS[@]}")
ALL_AGENTS=(claude cursor windsurf generic pi kiro gemini antigravity codex hermes openclaw copilot trae trae-cn)

usage() {
  cat <<'EOF'
Usage:
  bash setup.sh
  bash setup.sh --agents all
  bash setup.sh --agents claude,codex,gemini
  bash setup.sh --global-extra beeweave-capture,beeweave-context-pack

Options:
  --agents LIST        Comma-separated agents to install for, or "all".
                       Known agents: claude,cursor,windsurf,generic,pi,kiro,
                                     gemini,antigravity,codex,hermes,openclaw,
                                     copilot,trae,trae-cn
  --global-extra LIST  Optional extra global skills. Supported:
                       beeweave-capture,beeweave-context-pack,beeweave-digest,beeweave-status,
                       beeweave-memory-bridge
  -h, --help           Show this help.

Install policy:
  Project-local skills are full installs.
  Global skills default to: beeweave-update, beeweave-query, beeweave-ingest.
  --global-extra appends explicitly selected advanced global skills.
EOF
}

normalize_agents() {
  local raw="$1"
  raw="${raw// /}"
  if [ "$raw" = "none" ]; then
    SELECTED_AGENTS=()
    return
  fi
  if [ -z "$raw" ] || [ "$raw" = "all" ]; then
    SELECTED_AGENTS=("${ALL_AGENTS[@]}")
    return
  fi

  IFS=',' read -r -a SELECTED_AGENTS <<< "$raw"
  local agent known
  for agent in "${SELECTED_AGENTS[@]}"; do
    known=false
    for known_agent in "${ALL_AGENTS[@]}"; do
      if [ "$agent" = "$known_agent" ]; then
        known=true
        break
      fi
    done
    if [ "$known" = false ]; then
      echo "setup.sh: unknown agent '$agent'" >&2
      echo "Run 'bash setup.sh --help' for supported agents." >&2
      exit 1
    fi
  done
}

is_recommended_global_extra() {
  local skill="$1"
  local candidate
  for candidate in "${RECOMMENDED_GLOBAL_EXTRA_SKILLS[@]}"; do
    [ "$skill" = "$candidate" ] && return 0
  done
  return 1
}

append_portable_skill() {
  local skill="$1"
  local existing
  for existing in "${PORTABLE_SKILLS[@]}"; do
    [ "$existing" = "$skill" ] && return
  done
  PORTABLE_SKILLS+=("$skill")
}

normalize_global_extra() {
  local raw="$1"
  raw="${raw// /}"
  [ -z "$raw" ] && return
  case "$raw" in
    none|no|skip) return ;;
    all) raw="$(IFS=','; echo "${RECOMMENDED_GLOBAL_EXTRA_SKILLS[*]}")" ;;
  esac

  local selected skill
  IFS=',' read -r -a selected <<< "$raw"
  for skill in "${selected[@]}"; do
    [ -n "$skill" ] || continue
    if ! is_recommended_global_extra "$skill"; then
      echo "setup.sh: unsupported global extra skill '$skill'" >&2
      echo "Supported extras: ${RECOMMENDED_GLOBAL_EXTRA_SKILLS[*]}" >&2
      exit 1
    fi
    if [ ! -d "$WIKI_SKILLS_DIR/$skill" ]; then
      echo "setup.sh: global extra skill not found: $skill" >&2
      exit 1
    fi
    append_portable_skill "$skill"
  done
}

describe_global_extra() {
  case "$1" in
    beeweave-capture) echo "save current-session findings to inbox/wiki" ;;
    beeweave-context-pack) echo "package vault context for another task" ;;
    beeweave-digest) echo "generate recent knowledge digests" ;;
    beeweave-status) echo "show ingest status and vault health" ;;
    beeweave-memory-bridge) echo "compare knowledge by source agent" ;;
    *) echo "" ;;
  esac
}

describe_local_wiki_skill() {
  case "$1" in
    beeweave-agent) echo "agent runtime guide for BeeWeave projects" ;;
    beeweave-claude-ingest) echo "import Claude conversation history" ;;
    beeweave-codex-ingest) echo "import Codex conversation history" ;;
    beeweave-copilot-ingest) echo "import GitHub Copilot conversation history" ;;
    beeweave-core) echo "core vault structure and operating rules" ;;
    beeweave-cross-linker) echo "add wiki links between related notes" ;;
    beeweave-daily-update) echo "create daily knowledge updates" ;;
    beeweave-dashboard) echo "summarize vault status as a dashboard" ;;
    beeweave-dedup) echo "detect and reconcile duplicate knowledge" ;;
    beeweave-export) echo "export vault content for reuse" ;;
    beeweave-graph-colorize) echo "maintain graph color groups" ;;
    beeweave-hermes-ingest) echo "import Hermes conversation history" ;;
    beeweave-history-ingest) echo "unified agent-history import workflow" ;;
    beeweave-impl-validator) echo "validate implementation against specs" ;;
    beeweave-import) echo "import existing documents into the vault" ;;
    beeweave-lint) echo "check vault structure and note hygiene" ;;
    beeweave-openclaw-ingest) echo "import OpenClaw conversation history" ;;
    beeweave-pi-ingest) echo "import Pi conversation history" ;;
    beeweave-rebuild) echo "rebuild vault indexes and derived files" ;;
    beeweave-research) echo "run research capture and synthesis workflows" ;;
    beeweave-setup) echo "set up or repair a BeeWeave workspace" ;;
    beeweave-skill-creator) echo "create, improve, and evaluate skills" ;;
    beeweave-stage-commit) echo "prepare and commit vault changes" ;;
    beeweave-switch) echo "switch active vault or workbench context" ;;
    beeweave-synthesize) echo "synthesize notes into durable knowledge" ;;
    beeweave-tag-taxonomy) echo "maintain tag taxonomy and naming" ;;
    beeweave-vault-skill-factory) echo "turn vault practices into skills" ;;
    *) echo "" ;;
  esac
}

is_core_or_recommended_global_skill() {
  local skill="$1"
  local candidate
  for candidate in "${CORE_PORTABLE_SKILLS[@]}" "${RECOMMENDED_GLOBAL_EXTRA_SKILLS[@]}"; do
    [ "$skill" = "$candidate" ] && return 0
  done
  return 1
}

print_project_local_skill_summary() {
  echo "  Wiki/project-local skills:"
  local skill desc
  for skill_dir in "$WIKI_SKILLS_DIR"/*; do
    [ -d "$skill_dir" ] || continue
    skill="$(basename "$skill_dir")"
    is_core_or_recommended_global_skill "$skill" && continue
    desc="$(describe_local_wiki_skill "$skill")"
    [ -n "$desc" ] || desc="project-local BeeWeave wiki workflow"
    printf "    %-28s %s\n" "$skill" "$desc"
  done
  echo ""
  echo "  Workbench/project-local skills:"
  echo "    beeweave-article-writer     long-form articles, blog posts, essays, and opinion pieces"
  echo "    beeweave-ppt-writer         HTML PPT decks and presentation projects"
  echo "    beeweave-social-writer      X/Twitter posts, threads, short takes, and social copy"
}

choose_global_extra_interactive() {
  echo "  Global skills"
  echo "    Always installed:"
  local skill idx desc
  for skill in "${CORE_PORTABLE_SKILLS[@]}"; do
    echo "      [x] $skill"
  done
  echo ""
  echo "    Optional advanced global skills:"
  idx=1
  for skill in "${RECOMMENDED_GLOBAL_EXTRA_SKILLS[@]}"; do
    desc="$(describe_global_extra "$skill")"
    printf "     %2d. %-18s %s\n" "$idx" "$skill" "$desc"
    idx=$((idx + 1))
  done
  echo "        all              Install all optional advanced global skills"
  echo "        none             Default: install only the core three"
  echo ""
  print_project_local_skill_summary
  echo ""
  read -p "  Extra global skills [none]: " GLOBAL_EXTRA_ARG || true

  local raw="$GLOBAL_EXTRA_ARG"
  raw="${raw//,/ }"
  local expanded=()
  for token in $raw; do
    if [[ "$token" =~ ^[0-9]+$ ]]; then
      if [ "$token" -lt 1 ] || [ "$token" -gt "${#RECOMMENDED_GLOBAL_EXTRA_SKILLS[@]}" ]; then
        echo "setup.sh: global extra selection out of range: $token" >&2
        exit 1
      fi
      expanded+=("${RECOMMENDED_GLOBAL_EXTRA_SKILLS[$((token - 1))]}")
    else
      expanded+=("$token")
    fi
  done
  if [ ${#expanded[@]} -gt 0 ]; then
    (IFS=','; normalize_global_extra "${expanded[*]}")
  fi
}

AGENTS_ARG=""
GLOBAL_EXTRA_ARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --agents)
      [ $# -ge 2 ] || { echo "setup.sh: --agents requires a value" >&2; exit 1; }
      AGENTS_ARG="$2"
      shift 2
      ;;
    --agents=*)
      AGENTS_ARG="${1#--agents=}"
      shift
      ;;
    --global-extra)
      [ $# -ge 2 ] || { echo "setup.sh: --global-extra requires a value" >&2; exit 1; }
      GLOBAL_EXTRA_ARG="$2"
      shift 2
      ;;
    --global-extra=*)
      GLOBAL_EXTRA_ARG="${1#--global-extra=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "setup.sh: unknown argument '$1'" >&2
      echo "Run 'bash setup.sh --help' for usage." >&2
      exit 1
      ;;
  esac
done

SELECTED_AGENTS=()

expand_path() {
  local path="$1"
  if [ -z "$path" ]; then
    return
  fi
  case "$path" in
    "~") printf '%s\n' "$HOME" ;;
    "~/"*) printf '%s/%s\n' "$HOME" "${path#"~/"}" ;;
    /*) printf '%s\n' "$path" ;;
    *) printf '%s/%s\n' "$SCRIPT_DIR" "$path" ;;
  esac
}

update_env_value() {
  local key="$1"
  local value="$2"
  local escaped
  escaped=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g' -e 's/"/\\"/g')
  if grep -qE "^${key}=" "$SCRIPT_DIR/.env"; then
    sed -i.bak "s|^${key}=.*|${key}=\"${escaped}\"|" "$SCRIPT_DIR/.env"
  else
    printf '%s="%s"\n' "$key" "$value" >> "$SCRIPT_DIR/.env"
  fi
  rm -f "$SCRIPT_DIR/.env.bak"
}

ensure_gitkeep() {
  local dir="$1"
  mkdir -p "$dir"
  if [ ! -e "$dir/.gitkeep" ]; then
    : > "$dir/.gitkeep"
  fi
}

init_vault_layout() {
  local vault_path="$1"
  [ -n "$vault_path" ] || return

  # Fixed vault schema used by wiki skills. Content pages are maintained by
  # beeweave-ingest/beeweave-update; setup only creates the stable skeleton.
  for dir in concepts entities skills references synthesis projects _meta _archives _staging .obsidian; do
    ensure_gitkeep "$vault_path/$dir"
  done
}

init_workbench_layout() {
  local workbench_path="$1"
  [ -n "$workbench_path" ] || return

  # Keep the creation workspace intentionally small:
  # inbox -> articles -> ppt -> library. Runtime directories are generated by setup.
  ensure_gitkeep "$workbench_path/inbox/captures"
  ensure_gitkeep "$workbench_path/inbox/web"
  ensure_gitkeep "$workbench_path/inbox/archived"
  ensure_gitkeep "$workbench_path/inbox/rejected"
  ensure_gitkeep "$workbench_path/articles/drafts"
  ensure_gitkeep "$workbench_path/articles/published"
  ensure_gitkeep "$workbench_path/ppt"
  ensure_gitkeep "$workbench_path/library"
}

# install_skills_from <source_dir> <target_dir> <label> [relative|absolute] [skill-subset...]
# "relative" requires target_dir under $SCRIPT_DIR and emits ../-prefixed
# targets matching the committed symlinks. Extra args restrict the install
# to a named subset of skills (e.g. portable-only into ~/.claude/skills).
install_skills_from() {
  local source_dir="$1"
  local target_dir="$2"
  local label="$3"
  local mode="${4:-absolute}"
  shift 4 || shift $#
  local subset=("$@")  # empty = install all

  [ -d "$source_dir" ] || return

  case "$mode" in
    relative|absolute) ;;
    *) echo "install_skills: bad mode '$mode' (want relative|absolute)" >&2; exit 1 ;;
  esac

  local rel_prefix=""
  if [ "$mode" = "relative" ]; then
    # Strip $SCRIPT_DIR prefix; if it doesn't match, target is outside the
    # repo and "relative" isn't meaningful — bail rather than emit a wrong link.
    local rel="${target_dir#"$SCRIPT_DIR"/}"
    if [ "$rel" = "$target_dir" ]; then
      echo "install_skills: relative mode requires target under \$SCRIPT_DIR ($target_dir)" >&2
      exit 1
    fi
    # One ../ per path component in $rel; e.g. .claude/skills → 2 components → ../../
    local slashes="${rel//[^\/]/}"
    local depth=$(( ${#slashes} + 1 )) i
    for (( i=0; i<depth; i++ )); do rel_prefix="../$rel_prefix"; done
  fi

  mkdir -p "$target_dir"
  for skill in "$source_dir"/*/; do
    local skill_name link_path link_target
    [ -d "$skill" ] || continue
    skill_name="$(basename "$skill")"
    if [ ${#subset[@]} -gt 0 ]; then
      local match=0 want
      for want in "${subset[@]}"; do [ "$want" = "$skill_name" ] && match=1 && break; done
      [ "$match" = 1 ] || continue
    fi
    link_path="$target_dir/$skill_name"
    if [ "$mode" = "relative" ]; then
      local source_rel="${source_dir#"$SCRIPT_DIR"/}"
      if [ "$source_rel" = "$source_dir" ]; then
        echo "install_skills: relative mode requires source under \$SCRIPT_DIR ($source_dir)" >&2
        exit 1
      fi
      link_target="${rel_prefix}${source_rel}/$skill_name"
    else
      link_target="${skill%/}"
    fi
    if [ -L "$link_path" ]; then
      rm "$link_path"
    elif [ -d "$link_path" ]; then
      echo "⚠️   $link_path is a real directory, skipping symlink"
      continue
    elif [ -f "$link_path" ]; then
      # Git on Windows without core.symlinks=true writes committed symlinks
      # as regular files containing the target path. Replace with a real symlink.
      rm "$link_path"
    fi
    ln -s "$link_target" "$link_path"
    # Sanity check: every skill ships a SKILL.md, so a working symlink resolves it.
    [ -e "$link_path/SKILL.md" ] || { echo "install_skills: broken link $link_path → $link_target" >&2; exit 1; }
  done
  echo "✅  Installed skills → $label"
}

install_skills() {
  install_skills_from "$WIKI_SKILLS_DIR" "$@"
}

install_project_skills() {
  local target_dir="$1"
  local label="$2"
  install_skills_from "$WIKI_SKILLS_DIR" "$target_dir" "$label wiki" relative
  install_skills_from "$WORKBENCH_SKILLS_DIR" "$target_dir" "$label workbench" relative
}

install_bootstrap_file() {
  local src="$1"
  local dest="$2"
  [ -f "$src" ] || return
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
}

install_bootstrap_files() {
  install_bootstrap_file "$SCRIPT_DIR/bootstrap/cursor/rules/beeweave.mdc" "$SCRIPT_DIR/.cursor/rules/beeweave.mdc"
  install_bootstrap_file "$SCRIPT_DIR/bootstrap/windsurf/rules/beeweave.md" "$SCRIPT_DIR/.windsurf/rules/beeweave.md"
  install_bootstrap_file "$SCRIPT_DIR/bootstrap/kiro/steering/beeweave.md" "$SCRIPT_DIR/.kiro/steering/beeweave.md"
  install_bootstrap_file "$SCRIPT_DIR/bootstrap/agent/rules/beeweave.md" "$SCRIPT_DIR/.agent/rules/beeweave.md"
  install_bootstrap_file "$SCRIPT_DIR/bootstrap/agent/workflows/beeweave.md" "$SCRIPT_DIR/.agent/workflows/beeweave.md"
  echo "✅  Installed agent bootstrap files"
}

link_agent_context_aliases() {
  local alias
  for alias in CLAUDE.md GEMINI.md HERMES.md; do
    local target="$SCRIPT_DIR/$alias"
    if [ -L "$target" ] || [ -e "$target" ]; then
      rm "$target"
    fi
    ln -s AGENTS.md "$target"
  done

  echo "✅  Linked AGENTS.md aliases (CLAUDE.md, GEMINI.md, HERMES.md)"
}

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║               BeeWeave Agent Setup               ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── Step 0: Global skill selection ────────────────────────────
if [ -z "$GLOBAL_EXTRA_ARG" ]; then
  if [ -t 0 ]; then
    choose_global_extra_interactive
  fi
else
  normalize_global_extra "$GLOBAL_EXTRA_ARG"
fi
echo "✅  Global skills: ${PORTABLE_SKILLS[*]}"
echo ""

# ── Step 0b: Agent selection ─────────────────────────────────
if [ -z "$AGENTS_ARG" ]; then
  echo "  Install skills for which agents?"
  echo "  Known agents: ${ALL_AGENTS[*]}"
  echo ""
  read -p "  Agents [all]: " AGENTS_ARG || true
fi
normalize_agents "${AGENTS_ARG:-all}"
if [ ${#SELECTED_AGENTS[@]} -eq 0 ]; then
  echo "✅  Selected agents: none"
else
  echo "✅  Selected agents: ${SELECTED_AGENTS[*]}"
fi
echo "    Project-local: full skills; global: ${PORTABLE_SKILLS[*]}"
echo ""

# ── Step 1: .env ──────────────────────────────────────────────
if [ ! -f "$SCRIPT_DIR/.env" ]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo "✅  Created .env from .env.example"
  echo "    → Edit .env and set BEEWEAVE_VAULT_PATH before using skills."
else
  echo "✅  .env already exists"
fi

# ── Step 1b: ~/.beeweave/config ─────────────────────────
GLOBAL_CONFIG_DIR="$HOME/.beeweave"
GLOBAL_CONFIG="$GLOBAL_CONFIG_DIR/config"
mkdir -p "$GLOBAL_CONFIG_DIR"

# Read vault path from .env if it's already set
VAULT_PATH=""
if [ -f "$SCRIPT_DIR/.env" ]; then
  # Strip quotes if present, but preserve the path (spaces or not)
  VAULT_PATH=$(grep -E '^BEEWEAVE_VAULT_PATH=' "$SCRIPT_DIR/.env" | cut -d'=' -f2- | sed 's/^"//;s/"$//')
fi

# 如果未配置 vault 路径，则默认使用当前项目下的 ./vault。
# 需要其它目录时，可先在 .env 中设置 BEEWEAVE_VAULT_PATH。
if [ -z "$VAULT_PATH" ] || [ "$VAULT_PATH" = "/path/to/your/vault" ]; then
  VAULT_PATH="${VAULT_PATH:-./vault}"
  if [ -n "$VAULT_PATH" ]; then
    VAULT_PATH="$(expand_path "$VAULT_PATH")"
    init_vault_layout "$VAULT_PATH"
    update_env_value "BEEWEAVE_VAULT_PATH" "$VAULT_PATH"
  fi
else
  VAULT_PATH="$(expand_path "$VAULT_PATH")"
  init_vault_layout "$VAULT_PATH"
  update_env_value "BEEWEAVE_VAULT_PATH" "$VAULT_PATH"
fi

WORKBENCH_PATH=""
if [ -f "$SCRIPT_DIR/.env" ]; then
  WORKBENCH_PATH=$(grep -E '^BEEWEAVE_WORKBENCH_PATH=' "$SCRIPT_DIR/.env" | cut -d'=' -f2- | sed 's/^"//;s/"$//')
fi
if [ -z "$WORKBENCH_PATH" ]; then
  WORKBENCH_PATH="./workbench"
fi
WORKBENCH_PATH="$(expand_path "$WORKBENCH_PATH")"
init_workbench_layout "$WORKBENCH_PATH"
update_env_value "BEEWEAVE_WORKBENCH_PATH" "$WORKBENCH_PATH"

# Write global config with quoted path (preserves spaces)
cat > "$GLOBAL_CONFIG" <<EOF
BEEWEAVE_VAULT_PATH="$VAULT_PATH"
BEEWEAVE_WORKBENCH_PATH="$WORKBENCH_PATH"
BEEWEAVE_REPO="$SCRIPT_DIR"
BEEWEAVE_VERSION="source"
EOF
echo "✅  Global config written to ~/.beeweave/config"

install_bootstrap_files
link_agent_context_aliases

# ── Step 2: Install skills for selected agents ────────────────
install_global_portable() {
  install_skills "$1" "$2 (${PORTABLE_SKILLS[*]})" absolute "${PORTABLE_SKILLS[@]}"
}

install_hermes_portable() {
  install_global_portable "$HOME/.hermes/skills" "~/.hermes/skills/ (Hermes default)"
  # Hermes: active named profile (if $HERMES_HOME points to a non-default location)
  if [ -n "$HERMES_HOME" ] && [ "$HERMES_HOME" != "$HOME/.hermes" ]; then
    install_global_portable "$HERMES_HOME/skills" "$HERMES_HOME/skills/ (Hermes active profile: $(basename "$HERMES_HOME"))"
  fi
  # Hermes: all named profiles under ~/.hermes/profiles/
  if [ -d "$HOME/.hermes/profiles" ]; then
    for _hermes_profile_dir in "$HOME/.hermes/profiles"/*/; do
      [ -d "$_hermes_profile_dir" ] || continue
      _hermes_profile_name="$(basename "$_hermes_profile_dir")"
      # Skip if already handled via $HERMES_HOME above
      if [ -n "$HERMES_HOME" ] && [ "$HERMES_HOME" = "${_hermes_profile_dir%/}" ]; then
        continue
      fi
      install_global_portable "${_hermes_profile_dir}skills" \
        "~/.hermes/profiles/${_hermes_profile_name}/skills/ (Hermes profile: ${_hermes_profile_name})"
    done
  fi
}

install_agent() {
  case "$1" in
    claude)
      install_project_skills "$SCRIPT_DIR/.claude/skills" ".claude/skills/ (Claude Code, full)"
      install_global_portable "$HOME/.claude/skills" "~/.claude/skills/ (Claude Code)"
      ;;
    cursor)
      install_project_skills "$SCRIPT_DIR/.cursor/skills" ".cursor/skills/ (Cursor, full)"
      ;;
    windsurf)
      install_project_skills "$SCRIPT_DIR/.windsurf/skills" ".windsurf/skills/ (Windsurf, full)"
      ;;
    generic)
      install_project_skills "$SCRIPT_DIR/.agents/skills" ".agents/skills/ (AGENTS.md agents, full)"
      install_global_portable "$HOME/.agents/skills" "~/.agents/skills/ (OpenCode, Aider, Droid, generic)"
      ;;
    pi)
      install_project_skills "$SCRIPT_DIR/.pi/skills" ".pi/skills/ (Pi, full)"
      install_global_portable "$HOME/.pi/agent/skills" "~/.pi/agent/skills/ (Pi)"
      ;;
    kiro)
      install_project_skills "$SCRIPT_DIR/.kiro/skills" ".kiro/skills/ (Kiro, full)"
      install_global_portable "$HOME/.kiro/skills" "~/.kiro/skills/ (Kiro CLI)"
      ;;
    gemini)
      install_project_skills "$SCRIPT_DIR/.gemini/skills" ".gemini/skills/ (Gemini CLI, full)"
      install_global_portable "$HOME/.gemini/skills" "~/.gemini/skills/ (Gemini CLI)"
      ;;
    antigravity)
      install_project_skills "$SCRIPT_DIR/.agents/skills" ".agents/skills/ (Antigravity, full)"
      install_global_portable "$HOME/.gemini/antigravity/skills" "~/.gemini/antigravity/skills/ (Antigravity, legacy)"
      ;;
    codex)
      install_project_skills "$SCRIPT_DIR/.codex/skills" ".codex/skills/ (Codex, full)"
      install_global_portable "$HOME/.codex/skills" "~/.codex/skills/ (Codex)"
      ;;
    hermes)
      install_project_skills "$SCRIPT_DIR/.hermes/skills" ".hermes/skills/ (Hermes, full)"
      install_hermes_portable
      ;;
    openclaw)
      install_project_skills "$SCRIPT_DIR/.agents/skills" ".agents/skills/ (OpenClaw project agent, full)"
      install_global_portable "$HOME/.openclaw/skills" "~/.openclaw/skills/ (OpenClaw managed)"
      ;;
    copilot)
      install_project_skills "$SCRIPT_DIR/.copilot/skills" ".copilot/skills/ (GitHub Copilot CLI, full)"
      install_global_portable "$HOME/.copilot/skills" "~/.copilot/skills/ (GitHub Copilot CLI)"
      ;;
    trae)
      install_project_skills "$SCRIPT_DIR/.trae/skills" ".trae/skills/ (Trae, full)"
      install_global_portable "$HOME/.trae/skills" "~/.trae/skills/ (Trae)"
      ;;
    trae-cn)
      install_project_skills "$SCRIPT_DIR/.trae-cn/skills" ".trae-cn/skills/ (Trae CN, full)"
      install_global_portable "$HOME/.trae-cn/skills" "~/.trae-cn/skills/ (Trae CN)"
      ;;
  esac
}

for agent in "${SELECTED_AGENTS[@]}"; do
  install_agent "$agent"
done

# ── Step 4: GitHub sync (optional) ───────────────────────────
SYNC_CONFIGURED=false
VAULT_REMOTE=""

echo ""
read -p "  Set up GitHub sync for your vault? [y/N]: " SETUP_SYNC || true
if [[ "$SETUP_SYNC" =~ ^[Yy]$ ]]; then
  read -p "  GitHub repo URL (e.g. https://github.com/you/my-wiki.git): " VAULT_REMOTE || true
  if [ -n "$VAULT_REMOTE" ] && [ -n "$VAULT_PATH" ] && [ -d "$VAULT_PATH" ]; then
    # Init git repo in vault if needed
    if [ ! -d "$VAULT_PATH/.git" ]; then
      git -C "$VAULT_PATH" init -q
      echo "✅  Initialized git repo in vault"
    fi
    # Create .gitignore if missing
    if [ ! -f "$VAULT_PATH/.gitignore" ]; then
      cat > "$VAULT_PATH/.gitignore" <<'GITIGNORE'
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache
.trash/
GITIGNORE
      echo "✅  Created .gitignore in vault"
    fi
    # Add or update remote
    if git -C "$VAULT_PATH" remote get-url origin &>/dev/null 2>&1; then
      git -C "$VAULT_PATH" remote set-url origin "$VAULT_REMOTE"
    else
      git -C "$VAULT_PATH" remote add origin "$VAULT_REMOTE"
    fi
    echo "✅  Git remote → $VAULT_REMOTE"
    # Persist remote in global config
    echo "VAULT_GITHUB_REMOTE=\"$VAULT_REMOTE\"" >> "$GLOBAL_CONFIG"
    # Write ~/.beeweave/sync.sh
    cat > "$GLOBAL_CONFIG_DIR/sync.sh" <<'SYNC_SCRIPT'
#!/bin/bash
# wiki-sync — commit and push vault changes to GitHub
set -e
# shellcheck source=/dev/null
source "$HOME/.beeweave/config" 2>/dev/null || true
VAULT="${BEEWEAVE_VAULT_PATH:-}"
[ -d "$VAULT" ] || { echo "wiki-sync: vault not found at '$VAULT'" >&2; exit 1; }
cd "$VAULT"
git add -A
if git diff --cached --quiet; then
  echo "wiki-sync: nothing to commit"
  exit 0
fi
git commit -m "sync $(date '+%Y-%m-%d %H:%M')"
git push
echo "wiki-sync: pushed to $(git remote get-url origin)"
SYNC_SCRIPT
    chmod +x "$GLOBAL_CONFIG_DIR/sync.sh"
    echo "✅  Wrote ~/.beeweave/sync.sh"
    SYNC_CONFIGURED=true

    # Offer shell alias
    echo ""
    read -p "  Add 'wiki-sync' alias to your shell? [Y/n]: " ADD_ALIAS || true
    if [[ ! "$ADD_ALIAS" =~ ^[Nn]$ ]]; then
      SHELL_RC=""
      [ -f "$HOME/.zshrc" ]  && SHELL_RC="$HOME/.zshrc"
      [ -z "$SHELL_RC" ] && [ -f "$HOME/.bashrc" ] && SHELL_RC="$HOME/.bashrc"
      if [ -n "$SHELL_RC" ]; then
        if ! grep -q "wiki-sync" "$SHELL_RC"; then
          printf '\n# wiki-sync — push Obsidian vault to GitHub\nalias wiki-sync='"'"'~/.beeweave/sync.sh'"'"'\n' >> "$SHELL_RC"
          echo "✅  Added wiki-sync alias to $SHELL_RC"
          echo "    → Run: source $SHELL_RC  (or open a new terminal)"
        else
          echo "    ℹ️  wiki-sync alias already in $SHELL_RC"
        fi
      fi
    fi

    # Offer hourly cron
    echo ""
    read -p "  Enable hourly auto-sync (cron)? [y/N]: " ADD_CRON || true
    if [[ "$ADD_CRON" =~ ^[Yy]$ ]]; then
      CRON_LINE="0 * * * * $GLOBAL_CONFIG_DIR/sync.sh >> $GLOBAL_CONFIG_DIR/sync.log 2>&1"
      ( crontab -l 2>/dev/null; echo "$CRON_LINE" ) | sort -u | crontab -
      echo "✅  Hourly cron installed  (logs: ~/.beeweave/sync.log)"
    fi
  fi
fi

# ── Step 5: Summary ──────────────────────────────────────────
SKILL_COUNT=$(find "$WIKI_SKILLS_DIR" "$WORKBENCH_SKILLS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')

echo ""
echo "───────────────────────────────────────────────────"
echo " Setup complete!"
echo ""
echo " Skills found:    $SKILL_COUNT"
if [ ${#SELECTED_AGENTS[@]} -eq 0 ]; then
echo " Agents selected: none"
else
echo " Agents selected: ${SELECTED_AGENTS[*]}"
fi
echo " Install policy:  project-local full; global portable (${PORTABLE_SKILLS[*]})"
if $SYNC_CONFIGURED; then
echo " GitHub sync:     wiki-sync  (script: ~/.beeweave/sync.sh)"
fi
echo ""
echo " Bootstrap files:"
echo "   CLAUDE.md                            → Claude Code"
echo "   GEMINI.md                            → Gemini / Antigravity"
echo "   AGENTS.md                            → Codex, OpenClaw, OpenCode, Aider, Droid, Trae, Pi"
echo "   HERMES.md                            → Hermes (symlink → AGENTS.md)"
echo "   .cursor/rules/beeweave.mdc      → Cursor (alwaysApply)"
echo "   .windsurf/rules/beeweave.md     → Windsurf (always-on)"
echo "   .kiro/steering/beeweave.md      → Kiro (inclusion: always)"
echo "   .agent/rules/beeweave.md        → Google Antigravity (alwaysApply)"
echo "   .agent/workflows/beeweave.md    → Google Antigravity (slash commands)"
echo "   .github/copilot-instructions.md      → GitHub Copilot (VS Code Chat)"
echo ""
echo " Next steps:"
echo "   1. Open this project in your agent"
echo "   2. Start using the installed skills directly:"
echo "      /beeweave-ingest workbench/inbox"
echo "      /beeweave-query what do I know about ..."
echo "      /beeweave-update"
echo ""
echo " From any other project:"
echo "   /beeweave-update    → sync project knowledge into your vault"
echo "   /beeweave-query     → ask questions against your compiled vault"
if $SYNC_CONFIGURED; then
echo "   wiki-sync       → push all vault changes to GitHub"
fi
echo "───────────────────────────────────────────────────"
echo ""
