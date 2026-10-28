# haunted-terminal: source this from ~/.zshrc
# Needs a local llama-server running Gemma (see README).

GHOST_BIN=${GHOST_BIN:-${0:A:h}/ghost}

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

autoload -Uz add-zsh-hook
add-zsh-hook preexec _ghost_preexec
add-zsh-hook precmd _ghost_precmd
zle -N accept-line _ghost_accept_line
