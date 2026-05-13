# jctl Roadmap

**Current Version**: v0.1.0-beta.1
**Last Updated**: 2025-01-20

## Version Overview

| Version | Status | Target | Focus |
|---------|--------|--------|-------|
| v0.1.0-beta.1 | ✅ Complete | 2025-01-20 | Beta release with core features |
| v0.2.0 | 📋 Planned | Q1 2025 | Restore removed commands, improve UX |
| v0.3.0 | 📋 Planned | Q2 2025 | Advanced features, PyPI package |
| v1.0.0 | 🎯 Goal | Q2-Q3 2025 | Production-ready, full feature set |

---

## v0.1.0-beta.1 (Current - Released 2025-01-20)

**Status**: ✅ Complete

### Delivered Features

**Authentication**:
- ✅ Jenkins API token authentication
- ✅ OS-native keystore integration
- ✅ Secure credential storage
- ✅ `token`, `status`, `logout` commands

**Job Management** (2 commands):
- ✅ Trigger jobs with parameters
- ✅ View/stream logs

**Pipeline Management** (5 commands):
- ✅ List pipelines
- ✅ Run pipelines with parameters
- ✅ Describe pipeline with stages
- ✅ View/stream pipeline logs
- ✅ Cancel running pipelines

**Configuration** (6 commands):
- ✅ Interactive setup
- ✅ Multiple profiles support
- ✅ Profile management
- ✅ Config get/set/list/show

**Infrastructure**:
- ✅ Async operations with httpx
- ✅ Retry logic with exponential backoff
- ✅ Shell completion with caching
- ✅ Distinct exit codes
- ✅ Comprehensive documentation
- ✅ Test suite (50%+ coverage)
- ✅ Code quality: 94/100

**Total**: 18 working commands

---

## v0.2.0 (Planned - Q1 2025)

**Target Date**: February-March 2025
**Focus**: Restore removed commands, improve user experience

### Restored Commands (10 total)

#### Job Commands (4 commands)

**1. `jctl job status <name> [build-number]`**
- Get current status of a job/build
- Show: Status, duration, started time, result
- Exit codes based on job status
- **Implementation**: 2-3 hours
- **Priority**: High
- **Complexity**: Low

**2. `jctl job stop <name> <build-number>`**
- Gracefully stop a running job
- Wait for cleanup to complete
- Option: `--force` for immediate kill
- **Implementation**: 1-2 hours
- **Priority**: High
- **Complexity**: Low (API exists)

**3. `jctl job history <name>`**
- Show recent build history for a job
- Display: Build numbers, status, duration, started time
- Options: `--limit`, `--filter-status`
- **Implementation**: 3-4 hours
- **Priority**: Medium
- **Complexity**: Medium (pagination)

**4. `jctl job params <name>`**
- List parameters for a job
- Show: Name, type, default value, description
- Useful before triggering parametrized jobs
- **Implementation**: 2-3 hours
- **Priority**: Medium
- **Complexity**: Low

#### Pipeline Commands (6 commands)

**5. `jctl pipeline search <query>`**
- Search pipelines by name or folder
- Fuzzy matching support
- Filter by: Name, folder, last build status
- **Implementation**: 4-5 hours
- **Priority**: Medium
- **Complexity**: Medium

**6. `jctl pipeline pause <name> <build-number>`**
- Pause pipeline at next input step
- Show pending inputs
- Allow selection of which input to abort
- **Implementation**: 3-4 hours
- **Priority**: Low
- **Complexity**: Medium (requires workflow API)

**7. `jctl pipeline resume <name> <build-number>`**
- Resume paused pipeline
- Submit input parameters
- Handle multiple input prompts
- **Implementation**: 3-4 hours
- **Priority**: Low
- **Complexity**: Medium

**8. `jctl pipeline replay <name> <build-number>`**
- Replay previous pipeline run
- Option to override parameters
- Preserve original configuration
- **Implementation**: 4-5 hours
- **Priority**: High
- **Complexity**: High (replay API)

**9. `jctl pipeline restart <name> <build-number>`**
- Restart pipeline from beginning
- Copy parameters from original run
- Option: `--from-stage` to restart from specific stage
- **Implementation**: 3-4 hours
- **Priority**: Medium
- **Complexity**: Medium

**10. `jctl pipeline validate <Jenkinsfile>`**
- Validate Jenkinsfile syntax
- Check for common errors
- Option: `--file` for local file, `--pipeline` for remote
- **Implementation**: 2-3 hours
- **Priority**: Low
- **Complexity**: Low (API exists)

### User Experience Improvements

**Enhanced Error Messages**:
- More descriptive error messages
- Suggestions for common mistakes
- Better handling of network errors
- **Effort**: 4-6 hours

**Progress Indicators**:
- Spinners for long operations
- Progress bars for large data transfers
- Better async operation feedback
- **Effort**: 3-4 hours

**Interactive Mode Improvements**:
- Better prompts in `jctl config init`
- Autocomplete in interactive mode
- Default value suggestions
- **Effort**: 4-5 hours

### Quality Improvements

**Test Coverage**:
- Increase to 80%+ coverage
- Add integration tests
- Platform-specific tests (Linux, Windows)
- **Effort**: 8-10 hours

**Type Checking**:
- Fix all mypy errors (50 currently)
- Add return type annotations
- Replace `Any` returns with proper types
- **Effort**: 3-4 hours

**Documentation**:
- Update all commands in README
- Add video tutorials
- Create examples repository
- **Effort**: 4-6 hours

### Total Effort Estimate
- **Development**: 40-50 hours
- **Testing**: 10-15 hours
- **Documentation**: 5-10 hours
- **Total**: 55-75 hours (~2-3 weeks)

---

## v0.3.0 (Planned - Q2 2025)

**Target Date**: April-May 2025
**Focus**: Advanced features, package distribution

### New Features

**1. Multi-Jenkins Support**
```bash
# Support multiple Jenkins instances in one profile
jctl --jenkins prod-us pipeline list
jctl --jenkins prod-eu pipeline list

# Or configure multiple Jenkins URLs per profile
jctl config set profiles.prod.jenkins.urls '["https://jenkins1", "https://jenkins2"]'
```
**Effort**: 8-10 hours

**2. Watch Mode**
```bash
# Continuously watch pipeline status
jctl pipeline watch deploy/release-pipeline

# Watch multiple pipelines
jctl pipeline watch --all --filter "deploy-*"
```
**Effort**: 6-8 hours

**3. Batch Operations**
```bash
# Trigger multiple jobs in parallel
jctl job trigger-batch jobs.yaml

# Cancel multiple pipelines
jctl pipeline cancel-batch --filter "deploy-*" --status running
```
**Effort**: 10-12 hours

**4. Output Templates**
```bash
# Custom output templates
jctl pipeline list --template my-template.jinja2

# Save output to file
jctl pipeline list --output-file pipelines.json
```
**Effort**: 4-6 hours

**5. Pipeline Comparison**
```bash
# Compare two pipeline runs
jctl pipeline diff deploy-staging 123 124

# Show what changed between runs
jctl pipeline compare --builds 123,124,125
```
**Effort**: 8-10 hours

### Package Distribution

**PyPI Package**:
- Publish to PyPI under a name that does not collide with the existing
  `jctl` package (a Jamf Pro CRUD tool from another author). Likely
  candidates: `avidala-jctl` or `jenkins-jctl`.
- Automated releases via GitHub Actions
- **Effort**: 4-6 hours

**Homebrew Formula** (macOS):
- Create Homebrew formula
- Submit to Homebrew
- Enable `brew install jctl`
- **Effort**: 6-8 hours

**Debian/RPM Packages** (Linux):
- Create `.deb` package
- Create `.rpm` package
- Host on package repository
- **Effort**: 10-12 hours

### Platform Support

**Windows Improvements**:
- PowerShell completion
- Windows-specific installation docs
- Chocolatey package
- **Effort**: 8-10 hours

**Docker Image**:
```bash
# Run jctl in Docker
docker run -it avidala/jctl pipeline list

# Mount config
docker run -v ~/.jctl:/root/.jctl avidala/jctl pipeline list
```
**Effort**: 4-6 hours

### Total Effort Estimate
- **Development**: 60-80 hours
- **Testing**: 15-20 hours
- **Documentation**: 10-15 hours
- **Total**: 85-115 hours (~3-4 weeks)

---

## v1.0.0 (Goal - Q2-Q3 2025)

**Target Date**: June-August 2025
**Focus**: Production-ready, full feature set

### Production Readiness

**Stability**:
- 100% test coverage on critical paths
- Comprehensive integration tests
- Performance benchmarks
- Load testing
- **Effort**: 20-30 hours

**Security**:
- Security audit
- Penetration testing
- OWASP compliance
- Dependency scanning automation
- **Effort**: 15-20 hours

**Monitoring**:
- Usage telemetry (opt-in)
- Error reporting (opt-in)
- Performance metrics
- Crash reporting
- **Effort**: 10-15 hours

### Advanced Features

**Plugin System**:
```python
# Custom plugins
from jctl.plugins import Plugin

class CustomPlugin(Plugin):
    def on_job_trigger(self, job_name, params):
        # Custom logic
        pass

# Load plugins
jctl --plugin my_plugin.py pipeline run my-job
```
**Effort**: 20-25 hours

**Configuration Sync**:
```bash
# Sync config across machines
jctl config sync --push
jctl config sync --pull

# Use remote config
jctl config remote --url https://config.example.com/jctl
```
**Effort**: 15-20 hours

**Notification System**:
```bash
# Get notified on completion
jctl pipeline run my-job --notify-slack
jctl pipeline run my-job --notify-email
jctl pipeline run my-job --notify-webhook https://example.com/webhook
```
**Effort**: 12-15 hours

### Documentation Site

**ReadTheDocs or GitHub Pages**:
- Complete API documentation
- User guide
- Architecture documentation
- Examples and tutorials
- Video tutorials
- **Effort**: 20-30 hours

### Total Effort Estimate
- **Development**: 80-100 hours
- **Testing**: 20-30 hours
- **Documentation**: 20-30 hours
- **Total**: 120-160 hours (~4-6 weeks)

---

## Beyond v1.0.0 (Future Vision)

### Potential Features

**1. Web UI** (v1.1.0)
- Local web interface
- View pipelines in browser
- Interactive job triggering
- Real-time log streaming

**2. Job Builder** (v1.2.0)
- Interactive job creation
- Generate Jenkinsfile from templates
- Visual pipeline builder

**3. Analytics** (v1.3.0)
- Pipeline performance analytics
- Success rate tracking
- Resource usage insights
- Cost optimization suggestions

**4. AI Assistant** (v1.4.0)
- Natural language interface
- Intelligent error diagnosis
- Automated troubleshooting
- Optimization recommendations

**5. Team Collaboration** (v1.5.0)
- Shared configurations
- Team workspaces
- Access control
- Audit logging

---

## Feature Requests

Have a feature request? Open an issue!

**GitHub Issues**: https://github.com/avidala/jctl/issues/new

**Template**:
```markdown
### Feature Description
Clear description of the feature

### Use Case
Why is this feature needed?

### Proposed Solution
How should it work?

### Alternatives Considered
Other approaches

### Priority
Low / Medium / High
```

---

## Contributing

Want to help implement features from the roadmap?

1. **Pick an issue**: Look for issues tagged with `roadmap` and `help wanted`
2. **Comment**: Let us know you're working on it
3. **Submit PR**: Follow the contributing guidelines
4. **Get merged**: We'll review and merge your contribution

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Roadmap Updates

This roadmap is a living document and will be updated based on:
- User feedback
- Community contributions
- Jenkins DevOps priorities
- Industry trends

**Last Reviewed**: 2025-01-20
**Next Review**: 2025-02-01 (monthly)

---

## Success Metrics

### v0.2.0 Goals
- ✅ All 10 commands implemented
- ✅ 80%+ test coverage
- ✅ No critical bugs for 2 weeks
- ✅ 10+ active users

### v0.3.0 Goals
- ✅ PyPI package available
- ✅ 100+ PyPI downloads/month
- ✅ 3+ external contributors
- ✅ 90%+ test coverage

### v1.0.0 Goals
- ✅ 500+ PyPI downloads/month
- ✅ 10+ stars on GitHub
- ✅ 5+ external contributors
- ✅ Production use at H2O
- ✅ Zero security vulnerabilities
- ✅ 95%+ test coverage

---

**Document Version**: 1.0
**Last Updated**: 2025-01-20
**Status**: Active Planning
