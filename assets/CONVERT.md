# Converting SVG Assets to PNG

Since you need PNG files for GitHub, here are the easiest methods:

## Method 1: Online Converter (Recommended - Easiest)

### For repo-icon.svg → repo-icon.png
1. Visit: https://cloudconvert.com/svg-to-png
2. Upload `assets/repo-icon.svg`
3. Set options:
   - Width: 512px
   - Height: 512px
   - Quality: High
4. Download as `repo-icon.png`
5. Save to `assets/` directory

### For social-preview.svg → social-preview.png
1. Visit: https://cloudconvert.com/svg-to-png
2. Upload `assets/social-preview.svg`
3. Set options:
   - Width: 1280px
   - Height: 640px
   - Quality: High
4. Download as `social-preview.png`
5. Save to `assets/` directory

## Method 2: Using Homebrew + ImageMagick

If you want to do it locally:

```bash
# Install ImageMagick
brew install imagemagick

# Convert repo icon
magick assets/repo-icon.svg -resize 512x512 assets/repo-icon.png

# Convert social preview
magick assets/social-preview.svg -resize 1280x640 assets/social-preview.png
```

## Method 3: Using Inkscape (GUI)

1. Install Inkscape: https://inkscape.org/
2. Open the SVG file
3. File → Export PNG Image
4. Set dimensions (512x512 or 1280x640)
5. Export

## After Conversion

Once you have the PNG files:

```bash
# Add to git
git add assets/*.png

# Commit
git commit -m "feat: add PNG versions of logos for GitHub compatibility"

# Push
git push
```

## Upload to GitHub

1. Go to: https://github.com/avidala/jctl/settings
2. Scroll to "Social preview" section
3. Click "Edit" → "Upload an image"
4. Upload `assets/repo-icon.png` or `assets/social-preview.png`
5. Save changes

Your repository icon will immediately update!
