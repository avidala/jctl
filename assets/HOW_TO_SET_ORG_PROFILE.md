# How to Set AVIDALA Organization Profile Picture

## Quick Steps

### 1. Download the Org Avatar
The organization avatar is ready in: `assets/org-avatar.svg`

### 2. Convert to PNG (GitHub prefers PNG)

**Option A: Online Converter (Easiest)**
1. Go to: https://cloudconvert.com/svg-to-png
2. Upload `assets/org-avatar.svg`
3. Set size: **400x400** pixels
4. Download as `org-avatar.png`

**Option B: Using ImageMagick (if installed)**
```bash
magick assets/org-avatar.svg -resize 400x400 assets/org-avatar.png
```

### 3. Upload to GitHub Organization

1. **Go to organization settings**:
   - Direct link: https://github.com/organizations/avidala/settings/profile
   - Or: GitHub → Your organizations → avidala → Settings → Profile

2. **Upload profile picture**:
   - Look for "Profile picture" section
   - Click "Upload new picture" or "Edit"
   - Select your `org-avatar.png` file
   - Adjust the crop if needed
   - Click "Set new profile picture"

3. **Result**:
   - The new avatar will appear next to "avidala" organization name
   - Shows in all organization repositories
   - Displays on your profile when you contribute as the org

## Optional: Set Organization Profile Banner

While you're in the settings, you can also set a banner:

1. Stay in: https://github.com/organizations/avidala/settings/profile
2. Scroll to "Social accounts and profile" section
3. Upload `assets/org-banner.png` (convert from org-banner.svg first)
4. Recommended size: **1280x640** pixels

## What the Org Avatar Looks Like

The org-avatar.svg features:
- Square design (400x400) with rounded corners
- Pipeline icon (3 vertical pipes)
- "AV" monogram in bold
- Purple-pink gradient security shield
- Dark theme background
- Blue-cyan gradient accents

Perfect for representing the AVIDALA DevOps Tools organization!

## Troubleshooting

**Image too large?**
- GitHub accepts up to 1MB for profile pictures
- Try compressing the PNG or reducing size to 200x200

**Can't access settings?**
- You need to be an owner of the organization
- Check: https://github.com/orgs/avidala/people
- Make sure you're logged in as the owner

**Want a different design?**
- Edit `assets/org-avatar.svg`
- Regenerate PNG
- Upload new version

---

**Note**: The profile picture change is immediate and affects all repositories under the avidala organization, including this jctl repo!
