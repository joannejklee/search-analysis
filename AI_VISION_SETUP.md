# AI Vision Keywords Setup Guide

## Overview
The AI Vision analysis script uses OpenAI's GPT-4 Vision to automatically extract descriptive keywords from:
- **Concept photos**: Product type, visual style, colors, mood (e.g., "lips, pink, glossy, minimalist")
- **Model images**: Appearance and vibe keywords (e.g., "chic, minimal, elegant, natural")

## Setup Instructions

### 1. Get an OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### 2. Set the API Key

**Option A: Environment Variable (Recommended)**
```bash
# Add to your ~/.zshrc or ~/.bash_profile
export OPENAI_API_KEY='sk-your-actual-key-here'

# Then reload:
source ~/.zshrc
```

**Option B: One-time Use**
```bash
OPENAI_API_KEY='sk-your-key' python3 scripts/5_ai_vision_keywords.py
```

### 3. Run the Script
```bash
cd /Users/joannelee/Documents/search_analysis
python3 scripts/5_ai_vision_keywords.py
```

## What It Does

### Sample Analysis (Default)
- Analyzes **first 10 jobs** as a demo
- Processes up to 3 concept photos per job
- Analyzes all model headshots in those jobs
- **Cost**: ~$0.50-1.00 for the sample

### Full Analysis
To analyze ALL 1,574 jobs:
1. Edit `scripts/5_ai_vision_keywords.py`
2. Find line 151: `sample_jobs = df['job_id'].dropna().unique()[:10]`
3. Change to: `sample_jobs = df['job_id'].dropna().unique()`
4. **Cost estimate**: ~$150-200 for all images (GPT-4 Vision costs ~$0.01-0.02 per image)

## Output Files

All saved to `outputs/ai_vision_keywords/`:

1. **concept_photo_keywords.csv**
   - Columns: job_id, brand_name, job_name, photo_url, keywords
   - One row per concept photo analyzed

2. **model_photo_keywords.csv**
   - Columns: job_id, brand_name, job_name, talent_name, photo_url, keywords
   - One row per model photo analyzed

3. **ai_vision_report.html**
   - Visual report showing photos with their AI-generated keywords
   - Interactive HTML format

## Example Output

### Concept Photo Keywords
```
Job 6890: 텐가(TENGA)
Photo: [lip product image]
Keywords: lips, pink, glossy, minimalist, close-up, beauty product
```

### Model Photo Keywords
```
Job 6890: 텐가(TENGA)
Model: Jane Doe
Keywords: chic, minimal, elegant, natural, youthful, professional
```

## Cost Management Tips

1. **Start with sample** (10 jobs) to test
2. **Increase gradually**: Try 50, then 100 jobs
3. **Monitor costs** at https://platform.openai.com/usage
4. **Set spending limits** in your OpenAI account settings

## Troubleshooting

**Error: "OPENAI_API_KEY environment variable not set"**
- Follow Step 2 above to set your API key

**Error: "Rate limit exceeded"**
- The script has built-in delays (0.5s between images)
- If still hitting limits, increase `time.sleep(0.5)` to `time.sleep(1.0)` on lines 184 and 218

**Error: "Photo not accessible"**
- Some image URLs may be expired or blocked
- The script skips inaccessible images automatically

## Integration with Dashboard

After running the AI vision analysis, you can:
1. Open `ai_vision_report.html` to see visual results
2. Use CSV files to analyze keyword patterns
3. Future enhancement: Integrate keywords directly into visual_dashboard.html

## Questions?

The AI vision analysis is completely optional but demonstrates the potential for:
- Automated content tagging
- Search/filter by visual attributes
- Trend analysis of concepts and model styles
- Better matching recommendations
