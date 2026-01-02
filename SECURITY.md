# Security Notice

## ⚠️ API Keys Exposed in Git History

If you've committed `config.py` with hardcoded API keys to a public repository, you need to take immediate action:

### Immediate Actions Required

1. **Rotate Your API Keys** (CRITICAL):
   - **VAPI API Key**: 
     - Go to [VAPI Dashboard](https://dashboard.vapi.ai)
     - Generate a new API key
     - Revoke/delete the old key
   - **OpenAI API Key**:
     - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
     - Revoke the exposed key
     - Create a new API key

2. **Remove config.py from Git History**:
   ```bash
   # Run the cleanup script
   ./scripts/remove_config_from_history.sh
   
   # Then force push (WARNING: This rewrites history)
   git push --force --all
   git push --force --tags
   ```

3. **Verify config.py is Ignored**:
   ```bash
   git check-ignore config.py
   # Should output: config.py
   ```

### Best Practices Going Forward

1. **Always use environment variables** - Never hardcode API keys
2. **Use .env files** for local development (and add .env to .gitignore)
3. **Use secrets management** in production (Replit Secrets, GitHub Secrets, etc.)
4. **Regularly rotate API keys** as a security practice

### Current Configuration

- `config.py` is in `.gitignore` and will not be committed
- The app uses `os.getenv()` to read from environment variables
- Default values are empty strings (no fallback keys)

