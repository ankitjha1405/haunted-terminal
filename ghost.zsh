# haunted-terminal: source this from ~/.zshrc
# Needs a local llama-server running Gemma (see README).

GHOST_BIN=${GHOST_BIN:-${0:A:h}/ghost}
alias ghost="$GHOST_BIN"  # so `ghost hush` works in any haunted shell

# Private settings such as ELEVENLABS_API_KEY live in a git-ignored .env next to this file.
if [[ -f ${GHOST_BIN:h}/.env ]]; then
  set -a
  source ${GHOST_BIN:h}/.env
  set +a
fi

# After each command, the ghost may comment on it.
_ghost_preexec() { _ghost_last=$1 }
_ghost_precmd() {
  local code=$?
  [[ -n $_ghost_last ]] || return
  "$GHOST_BIN" speak $code "$_ghost_last"
  _ghost_last=
}

# Before a risky command runs, the ghost asks you to confirm.
_ghost_accept_line() {
  local warning
  if warning=$("$GHOST_BIN" check "$BUFFER"); then
    zle .accept-line
    return
  fi
  zle -M "👻 $warning Proceed? [y/N]"
  local key
  read -k key
  if [[ $key == [yY] ]]; then
    zle .accept-line
  else
    zle -M "👻 Wise. The machine rests."
  fi
}

# When a terminal opens: the ghost rises, and the music starts (one player for all tabs).
if [[ -o interactive && -t 1 ]]; then
  [[ $GHOST_MUSIC == 0 ]] || ( "$GHOST_BIN" music $$ &>/dev/null & )
  [[ $GHOST_INTRO == 0 ]] || "$GHOST_BIN" intro
fi

autoload -Uz add-zsh-hook
add-zsh-hook preexec _ghost_preexec
add-zsh-hook precmd _ghost_precmd
zle -N accept-line _ghost_accept_line
