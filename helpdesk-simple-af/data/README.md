# Helpdesk Documents Data

This folder contains the mock helpdesk documentation that gets uploaded to Azure AI Search.

## 📄 Files

- **`helpdesk_docs.json`** - Mock helpdesk articles in JSON format

## 📝 JSON Structure

Each document in `helpdesk_docs.json` must have:

```json
{
  "id": "unique-id",
  "title": "Article Title",
  "content": "Full article content with step-by-step instructions..."
}
```

### Field Descriptions

- **`id`** (required, string) - Unique identifier for the document (e.g., "1", "2", "doc-001")
- **`title`** (required, string) - Document title that appears in search results
- **`content`** (required, string) - Full text content that will be:
  - Searchable via keyword search
  - Converted to embeddings for semantic/vector search
  - Used to generate RAG answers

## ✏️ Adding New Documents

To add a new helpdesk article:

1. Open `helpdesk_docs.json`
2. Add a new object to the array:

```json
[
  {
    "id": "1",
    "title": "Password Reset Guide",
    "content": "..."
  },
  {
    "id": "4",
    "title": "Software Installation Guide",
    "content": "How to Install Company Software\n\nStep 1: Download the installer...\nStep 2: Run as administrator...\n..."
  }
]
```

3. Save the file
4. Re-run the setup script:
   ```bash
   python scripts/setup_search.py
   ```

## 🔄 Updating Existing Documents

1. Edit the `content` or `title` field in `helpdesk_docs.json`
2. Save the file
3. Re-run setup script (it will delete and recreate the index):
   ```bash
   python scripts/setup_search.py
   ```

## ⚠️ Important Notes

- **IDs must be unique** - Duplicate IDs will cause upload errors
- **Newlines** - Use `\n` for line breaks in JSON strings
- **Quotes** - Escape quotes with `\"` inside content
- **Encoding** - File must be UTF-8 encoded
- **Format** - Must be valid JSON (use a validator if unsure)

## 📋 Content Best Practices

For best RAG results:

1. **Be detailed** - Include step-by-step instructions
2. **Use clear headings** - Help users scan the content
3. **Add troubleshooting** - Common issues and solutions
4. **Include context** - Explain why steps are needed
5. **Use examples** - Specific commands, URLs, screenshots references

## 🧪 Testing After Changes

After updating documents, test your changes:

```bash
# 1. Re-run setup
python scripts/setup_search.py

# 2. Start the app
python app.py

# 3. Query the new content
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"message": "your question about the new content"}'
```

## 🗂️ Example Document Templates

### IT Support Article
```json
{
  "id": "new-article-001",
  "title": "How to Reset MFA Device",
  "content": "Multi-Factor Authentication Reset\n\nIf you've lost your MFA device:\n\n1. Contact IT Support at extension 5555\n2. Provide your employee ID\n3. Answer security questions\n4. IT will send a temporary code to your email\n5. Log in with the temporary code\n6. Set up a new MFA device\n\nSecurity Note: This process may take 24 hours for verification."
}
```

### Software Guide
```json
{
  "id": "software-guide-001",
  "title": "Microsoft Teams Setup",
  "content": "Setting Up Microsoft Teams\n\nStep 1: Download Teams\n- Go to https://teams.microsoft.com/downloads\n- Click 'Download for desktop'\n\nStep 2: Install\n- Run the installer\n- Sign in with your company email\n\nStep 3: Configure\n- Allow microphone and camera access\n- Test your audio and video\n- Set your status\n\nCommon Issues:\n- 'Sign-in failed': Check your internet connection\n- 'No audio': Check microphone permissions in settings"
}
```

---

**Remember:** Always re-run `python scripts/setup_search.py` after making changes to this file!
