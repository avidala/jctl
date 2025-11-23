# How to Set AVIDALA Organization Avatar/Profile Picture

> **Note**: On GitHub, the "organization avatar" and "profile picture" are the **same thing**. This is the icon that appears next to your organization name everywhere on GitHub.

## What This Changes

When you update the org avatar, it will appear:
- ✅ Next to "avidala" organization name
- ✅ On all repositories under the organization
- ✅ In organization listings and search results
- ✅ When you contribute as the organization
- ✅ On the organization's main page

## Quick Steps

### 1. Get the Org Avatar File
The organization avatar is ready in: `assets/org-avatar.svg`

You can view it here: https://github.com/avidala/jctl/blob/develop/assets/org-avatar.svg

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

**IMPORTANT**: You must be logged in as an **owner** of the avidala organization to change the avatar.

#### Detailed Steps:

1. **Go to organization settings**:
   - **Direct link**: https://github.com/organizations/avidala/settings/profile
   - **Or navigate manually**:
     - Go to https://github.com/avidala
     - Click the "Settings" tab (⚙️ icon)
     - Select "Profile" from the left sidebar

2. **Find the Profile Picture Section**:
   - Look for the circular image at the top
   - It currently shows your existing org avatar
   - Below it says "Profile picture"

3. **Upload your new avatar**:
   - Click "Edit" or "Upload a photo" button
   - Select your `org-avatar.png` file (400x400)
   - A crop tool will appear - adjust if needed (usually centered is fine)
   - Click "Set new profile picture" or "Save"

4. **Verify the change**:
   - Refresh the page
   - The new AVIDALA logo should now show
   - Go to https://github.com/avidala to see it on the org page
   - Check https://github.com/avidala/jctl - it should show next to "avidala"

#### What Gets Updated:
- ✅ Organization page (https://github.com/avidala)
- ✅ All repositories under avidala organization
- ✅ Organization listings and search results
- ✅ Member lists and contributor views
- ✅ Everywhere "avidala" appears on GitHub

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
