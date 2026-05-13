# jctl Branding Assets

This directory contains all branding and logo assets for the jctl project.

## Files

### Logos
- **`logo.svg`** - Full horizontal logo (400x120px)
  - Use in: README, documentation, websites
  - Features: Pipeline icon, full text, security badge

- **`icon.svg`** - Square icon (200x200px)
  - Use in: Favicon, app icons, small spaces
  - Features: Simplified design optimized for small sizes

- **`logo.txt`** - ASCII art logo
  - Use in: Terminal output, CLI help text, console banners
  - Format: Plain text

### GitHub Assets
- **`repo-icon.svg`** - Repository avatar (512x512px)
  - Use as: GitHub repository icon/avatar
  - Square format with rounded corners

- **`social-preview.svg`** - Social media preview (1280x640px)
  - Use in: GitHub social preview, Open Graph images
  - Optimized for social media sharing

### Organization Branding
- **`org-logo.svg`** - Full organization logo (600x600px)
  - Use in: Organization profile, presentations, print materials
  - Features: Animated pipeline, "AV" monogram, security shield
  - Circular design with "AVIDALA" text and "DevOps Tools" subtitle

- **`org-avatar.svg`** - Organization avatar (400x400px)
  - Use as: GitHub organization profile picture
  - Simplified square design with rounded corners
  - Features: Pipeline icon, "AV" monogram, security shield

- **`org-banner.svg`** - Organization banner (1200x300px)
  - Use in: Website headers, email signatures, LinkedIn
  - Features: Full branding with tech stack badges (Jenkins, Python, CLI)
  - Horizontal layout with gradient background

## How to Set GitHub Repository Icon

1. **Convert SVG to PNG** (GitHub prefers PNG):
   ```bash
   # Using ImageMagick or an online converter
   # Convert repo-icon.svg to repo-icon.png at 512x512
   ```

2. **Upload to GitHub**:
   - Go to: https://github.com/avidala/jctl/settings
   - Scroll to "Social preview" section
   - Click "Edit" → "Upload an image"
   - Upload `repo-icon.png` or `social-preview.png`

3. **Result**: The icon will appear:
   - Next to repository name
   - In search results
   - In social media shares
   - On the repository page

## Design Specifications

### Colors
- **Background**: `#1e293b` (slate-800)
- **Background Dark**: `#0f172a` (slate-900)
- **Primary Gradient**: `#3b82f6` → `#06b6d4` (blue-500 → cyan-500)
- **Text**: `#f8fafc` (slate-50)
- **Subtitle**: `#94a3b8` (slate-400)
- **Security Badge**: `#10b981` (emerald-500)

### Fonts
- **Main Text**: Courier New, Monaco (monospace)
- **Subtitle**: Arial, Helvetica (sans-serif)

### Design Elements
- 🔵 **Pipeline Icon**: Three vertical pipes with connections
- 🔒 **Security Badge**: Lock icon emphasizing authentication
- 🎨 **Dark Theme**: Developer-friendly aesthetic
- ⚡ **Gradient**: Blue to cyan for tech/DevOps feel

## Usage Guidelines

1. **Maintain aspect ratios** when scaling
2. **Preserve color scheme** for brand consistency
3. **Use dark backgrounds** - logos designed for dark themes
4. **SVG preferred** for web use (scalable, small file size)
5. **PNG for compatibility** when SVG not supported

## Converting to PNG

If you need PNG versions:

```bash
# Using ImageMagick
convert -background none repo-icon.svg -resize 512x512 repo-icon.png
convert -background none social-preview.svg -resize 1280x640 social-preview.png

# Or use online tools:
# - https://cloudconvert.com/svg-to-png
# - https://svgtopng.com/
```

## How to Set GitHub Organization Profile

If you create a GitHub organization:

1. **Convert org-avatar.svg to PNG**:
   ```bash
   # Online: https://cloudconvert.com/svg-to-png
   # Or: magick org-avatar.svg -resize 400x400 org-avatar.png
   ```

2. **Set Organization Avatar**:
   - Go to: https://github.com/organizations/YOUR_ORG/settings/profile
   - Click "Upload new picture"
   - Upload `org-avatar.png` (170x170 minimum, 400x400 recommended)

3. **Set Organization Banner** (optional):
   - Same settings page
   - Upload `org-banner.png` (1200x300 recommended)

## Design Features

### Organization Logo Design Elements

- **"AV" Monogram**: Your initials in bold monospace font
- **Pipeline Icon**: Three vertical pipes representing CI/CD workflows
- **Security Shield**: Purple-pink gradient with checkmark
- **Animated Particles**: Data flow visualization (SVG only)
- **Tech Stack Badges**: Jenkins, Python, CLI
- **Color Scheme**:
  - Primary: Blue (#3b82f6) to Cyan (#06b6d4)
  - Accent: Purple (#8b5cf6) to Pink (#ec4899)
  - Background: Dark slate (#1e293b, #0f172a)

### Variations

- **org-logo.svg**: Full featured with animations, best for presentations
- **org-avatar.svg**: Clean, simple, perfect for profile pictures
- **org-banner.svg**: Wide format for headers and covers

## License

Same as parent project (MIT License).
