#compdef jctl

# jctl zsh completion with proper global option handling
# No Jenkins API calls - just static command completion

_jctl() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    # Parse the command line to find command and subcommand
    # Exclude the current word being typed if it's incomplete
    local -a cmd_parts
    local i
    local is_current=0
    for ((i = 2; i <= $#words; i++)); do
        # Check if this is the word being completed
        if [[ $i -eq $CURRENT ]]; then
            is_current=1
            # Don't include the current partial word in cmd_parts
            continue
        fi

        case ${words[i]} in
            --profile|--debug|--output)
                # Skip option and its argument
                ((i++))
                ;;
            -*)
                # Skip flag
                ;;
            *)
                # This is a command or subcommand
                cmd_parts+=("${words[i]}")
                ;;
        esac
    done

    local cmd="${cmd_parts[1]}"
    local subcmd="${cmd_parts[2]}"

    # If no command yet, offer commands
    if [[ -z "$cmd" ]]; then
        _arguments -C \
            '(- *)'{-h,--help}'[Show help message]' \
            '(- *)'{-V,--version}'[Show version]' \
            '--profile[Configuration profile to use]:profile:' \
            '--debug[Enable debug mode]' \
            '--output[Output format]:format:(table json yaml plain)' \
            '1:command:((
                auth\:"Manage authentication with Okta SSO"
                config\:"Manage jctl configuration"
                job\:"Manage Jenkins jobs"
                pipeline\:"Manage Jenkins pipelines"
                completion\:"Install shell completion"
            ))'
        return
    fi

    # If command exists but no subcommand, offer subcommands
    if [[ -n "$cmd" && -z "$subcmd" ]]; then
        case $cmd in
            pipeline)
                local -a pipeline_commands
                pipeline_commands=(
                    'list:List available pipelines'
                    'describe:Show detailed pipeline status'
                    'logs:View or stream pipeline logs'
                    'run:Execute a pipeline with parameters'
                    'cancel:Cancel/abort a running pipeline'
                    'pause:Pause a running pipeline'
                    'resume:Resume a paused pipeline'
                    'replay:Replay a previous pipeline run'
                    'restart:Restart a failed pipeline'
                    'validate:Validate pipeline configuration'
                    'search:Search for pipelines'
                )
                _describe 'pipeline subcommand' pipeline_commands
                return
                ;;
            job)
                local -a job_commands
                job_commands=(
                    'trigger:Trigger a Jenkins job'
                    'status:Get job status'
                    'logs:View or stream job logs'
                    'stop:Stop a running job'
                    'history:Show job execution history'
                    'params:List required parameters'
                )
                _describe 'job subcommand' job_commands
                return
                ;;
            auth)
                local -a auth_commands
                auth_commands=(
                    'login:Login with Okta SSO'
                    'logout:Clear stored credentials'
                    'status:Show authentication status'
                    'token:Configure Jenkins API token'
                    'refresh:Force token refresh'
                )
                _describe 'auth subcommand' auth_commands
                return
                ;;
            config)
                local -a config_commands
                config_commands=(
                    'init:Initialize configuration'
                    'get:Get configuration value'
                    'set:Set configuration value'
                    'list:List all configurations'
                    'show:Show current configuration'
                    'add-profile:Add a new configuration profile'
                )
                _describe 'config subcommand' config_commands
                return
                ;;
            completion)
                local -a completion_shells
                completion_shells=(
                    'bash:Bash shell'
                    'zsh:Zsh shell'
                    'fish:Fish shell'
                )
                _describe 'shell' completion_shells
                return
                ;;
        esac
    fi

    # If both command and subcommand exist, offer subcommand options
    if [[ -n "$cmd" && -n "$subcmd" ]]; then
        case "$cmd $subcmd" in
            "pipeline list")
                _arguments \
                    '--profile[Configuration profile to use]:profile:' \
                    '--debug[Enable debug mode]' \
                    '--filter[Filter pipelines by pattern]:pattern:' \
                    '--folder[Filter by folder]:folder:' \
                    '--status[Filter by status]:status:(SUCCESS FAILED RUNNING ABORTED)' \
                    '--limit[Number of pipelines to show]:limit:' \
                    '--output[Output format]:format:(table json yaml plain)'
                ;;
            "pipeline run")
                _arguments \
                    '--profile[Configuration profile to use]:profile:' \
                    '--debug[Enable debug mode]' \
                    '--param[Pipeline parameters]:param:' \
                    '-p[Pipeline parameters]:param:' \
                    '--wait[Wait for pipeline completion]' \
                    '--notify[Send notification on completion]'
                ;;
            "pipeline logs")
                _arguments \
                    '--profile[Configuration profile to use]:profile:' \
                    '--debug[Enable debug mode]' \
                    '--follow[Stream logs in real-time]' \
                    '-f[Stream logs in real-time]'
                ;;
            "pipeline cancel")
                _arguments \
                    '--profile[Configuration profile to use]:profile:' \
                    '--debug[Enable debug mode]' \
                    '--reason[Reason for cancellation]:reason:'
                ;;
            "job trigger")
                _arguments \
                    '--profile[Configuration profile to use]:profile:' \
                    '--debug[Enable debug mode]' \
                    '--param[Job parameters]:param:' \
                    '-p[Job parameters]:param:' \
                    '--wait[Wait for job completion]' \
                    '--dry-run[Show what would be triggered]'
                ;;
            "job logs")
                _arguments \
                    '--profile[Configuration profile to use]:profile:' \
                    '--debug[Enable debug mode]' \
                    '--follow[Stream logs in real-time]' \
                    '-f[Stream logs in real-time]'
                ;;
            "auth token")
                _arguments \
                    '--profile[Configuration profile to use]:profile:' \
                    '--debug[Enable debug mode]' \
                    '--username[Jenkins username]:username:' \
                    '--token[API token]:token:'
                ;;
            "config add-profile")
                _arguments \
                    '--profile[Configuration profile to use]:profile:' \
                    '--debug[Enable debug mode]' \
                    '--jenkins-url[Jenkins server URL]:url:' \
                    '--okta-domain[Okta domain]:domain:' \
                    '--okta-client-id[OAuth client ID]:client_id:' \
                    '--verify-ssl[Verify SSL certificates]' \
                    '--no-verify-ssl[Skip SSL verification]' \
                    '--set-default[Set as default profile]'
                ;;
        esac
    fi
}

# Register completion for jctl command
compdef _jctl jctl
