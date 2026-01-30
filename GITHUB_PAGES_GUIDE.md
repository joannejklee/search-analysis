# 🚀 Publishing to GitHub Pages - Step-by-Step Guide

## ✅ What's Already Done

- ✅ Git repository initialized
- ✅ All HTML reports copied to `docs/` folder
- ✅ Beautiful landing page created (`docs/index.html`)
- ✅ `.gitignore` configured (data files excluded)
- ✅ README.md created
- ✅ Initial commit created with all files

---

## 📋 Next Steps

### **Step 1: Create GitHub Repository**

1. Go to https://github.com
2. Click the **"+"** button (top right) → **"New repository"**
3. Fill in the details:
   - **Repository name**: `search_analysis` (or any name you prefer)
   - **Description**: "2025 Booking Analysis Reports"
   - **Visibility**: Choose **Private** or **Public**
     - ⚠️ **Private** = Only you and invited team members can see it
     - **Public** = Anyone can see it (but no sensitive data is included)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

---

### **Step 2: Connect Local Repository to GitHub**

GitHub will show you commands after creating the repo. Copy the repository URL (looks like `https://github.com/YOUR-USERNAME/search_analysis.git`)

Then run these commands in your terminal:

```bash
cd /Users/joannelee/Documents/search_analysis

# Add GitHub as remote
git remote add origin https://github.com/YOUR-USERNAME/search_analysis.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**Replace `YOUR-USERNAME` with your actual GitHub username!**

---

### **Step 3: Enable GitHub Pages**

1. Go to your repository on GitHub
2. Click **"Settings"** tab (top of the page)
3. Scroll down to **"Pages"** in the left sidebar (under "Code and automation")
4. Under **"Build and deployment"**:
   - **Source**: Select **"Deploy from a branch"**
   - **Branch**: Select **"main"** and **/docs** folder
   - Click **"Save"**

5. Wait 1-2 minutes for deployment

---

### **Step 4: Access Your Published Reports**

Your reports will be live at:

```
https://YOUR-USERNAME.github.io/search_analysis/
```

**Replace `YOUR-USERNAME` with your GitHub username!**

---

## 📊 Your Published Pages

Once live, you'll have:

1. **Landing Page**: `https://YOUR-USERNAME.github.io/search_analysis/`
   - Beautiful homepage with links to all 4 reports

2. **Patterns Report**: `https://YOUR-USERNAME.github.io/search_analysis/patterns_report.html`

3. **VOC Analysis**: `https://YOUR-USERNAME.github.io/search_analysis/voc_analysis_interactive.html`

4. **Vocabulary Report**: `https://YOUR-USERNAME.github.io/search_analysis/vocabulary_report.html`

5. **Visual Dashboard**: `https://YOUR-USERNAME.github.io/search_analysis/visual_dashboard.html`

---

## 👥 Sharing with Your Team

### For Private Repositories:

1. Go to your repository on GitHub
2. Click **"Settings"** → **"Collaborators"**
3. Click **"Add people"**
4. Enter their GitHub usernames or emails
5. Send them the link: `https://YOUR-USERNAME.github.io/search_analysis/`

### For Public Repositories:

Just send the link to anyone! No GitHub account needed to view.

---

## 🔄 Updating Reports

When you regenerate reports and want to update the published versions:

```bash
cd /Users/joannelee/Documents/search_analysis

# Copy updated HTML files
cp outputs/patterns/patterns_report.html docs/
cp outputs/voc_analysis_revised/voc_analysis_interactive.html docs/
cp outputs/vocabulary/vocabulary_report.html docs/
cp outputs/visual_dashboard/visual_dashboard.html docs/

# Commit and push
git add docs/
git commit -m "Update reports - $(date +%Y-%m-%d)"
git push origin main
```

Changes will be live in 1-2 minutes!

---

## 🔒 Security Notes

✅ **Safe to publish:**
- HTML reports (no raw data)
- Landing page
- Scripts (Python code)
- README and documentation

❌ **NOT published (protected by .gitignore):**
- `data/` folder (your CSV files)
- `outputs/` folder (except the docs we copied)
- Any `.csv` files

---

## 🐛 Troubleshooting

### Issue: "404 - Page not found"
**Solution**: 
- Make sure GitHub Pages is enabled with `/docs` folder
- Wait 2-3 minutes after enabling
- Check the URL matches your username

### Issue: "Reports look broken"
**Solution**:
- HTML files are self-contained, should work fine
- Check browser console for errors (F12)
- Make sure all 4 files + index.html are in `docs/`

### Issue: "Can't push to GitHub"
**Solution**:
```bash
# Check if remote is set correctly
git remote -v

# If needed, remove and re-add
git remote remove origin
git remote add origin https://github.com/YOUR-USERNAME/search_analysis.git
```

### Issue: "Repository is too large"
**Solution**:
- This shouldn't happen - we're only committing HTML and scripts
- Run: `du -sh .git` to check size
- Make sure `data/` folder is being ignored: `git status` should NOT show CSV files

---

## 💡 Pro Tips

### Custom Domain (Optional)
If you want a custom domain like `reports.yourcompany.com`:
1. Buy a domain
2. Add a `CNAME` file to `docs/` with your domain
3. Configure DNS settings
4. Update in GitHub Pages settings

### Analytics (Optional)
Add Google Analytics to track page views:
1. Get GA tracking code
2. Add to each HTML file's `<head>` section

### Password Protection (For Private Repos)
If repository is private:
- Only invited collaborators can access
- They need GitHub login to view
- Share individual report links directly

---

## ✅ Quick Checklist

- [ ] Created GitHub repository
- [ ] Connected local repo to GitHub
- [ ] Pushed code to GitHub
- [ ] Enabled GitHub Pages (Settings → Pages → /docs)
- [ ] Waited 2 minutes for deployment
- [ ] Visited landing page URL
- [ ] Shared link with team

---

## 📞 Need Help?

If you get stuck:
1. Check the GitHub Pages settings page - it shows build status
2. Look at the Actions tab in your repo for deployment logs
3. Verify all HTML files are in the `docs/` folder on GitHub

---

**Ready to publish? Follow Step 1 above!** 🚀

Your reports are prepared and ready to go live in just a few clicks.
