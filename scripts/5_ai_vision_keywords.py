"""
Script 5: AI Vision Analysis for Concept Photos & Model Images
Uses GPT-4 Vision to extract descriptive keywords from images
"""

import sys
import subprocess
import os

# Check and install required packages
required_packages = {
    'pandas': 'pandas',
    'openai': 'openai',
    'requests': 'requests',
}

print("Checking required packages...")
for package, pip_name in required_packages.items():
    try:
        __import__(package)
        print(f"✓ {package} already installed")
    except ImportError:
        print(f"✗ {package} not found. Installing {pip_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--break-system-packages"])
        print(f"✓ {pip_name} installed successfully")

import pandas as pd
import json
import re
import time
from openai import OpenAI
import requests

print("\n" + "="*80)
print("SCRIPT 5: AI VISION KEYWORD EXTRACTION")
print("="*80 + "\n")

# Configuration
DATA_DIR = "data"
OUTPUT_DIR = "outputs/ai_vision_keywords"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# SETUP OPENAI CLIENT
# ============================================================================

# Check for API key
API_KEY = os.getenv('OPENAI_API_KEY')

if not API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY environment variable not set!")
    print("\nTo use this script, you need to:")
    print("1. Get an API key from https://platform.openai.com/api-keys")
    print("2. Set it as an environment variable:")
    print("   export OPENAI_API_KEY='your-api-key-here'")
    print("\nOr run this script with the key:")
    print("   OPENAI_API_KEY='your-key' python3 scripts/5_ai_vision_keywords.py")
    print("\n" + "="*80)
    sys.exit(1)

client = OpenAI(api_key=API_KEY)

print("✓ OpenAI client initialized\n")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_array_field(field_value):
    """Parse fields that are in {value1,value2} or array format"""
    if pd.isna(field_value):
        return []
    
    field_str = str(field_value).strip()
    if field_str == '{}' or field_str == '':
        return []
    
    field_str = field_str.strip('{}').strip('"')
    values = [v.strip().strip('"') for v in field_str.split(',')]
    
    return [v for v in values if v and v.startswith('http')]

def check_image_url(url):
    """Verify image URL is accessible"""
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def analyze_concept_photo(image_url):
    """Analyze concept photo and extract keywords about the product/concept"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this concept/product photo. Provide ONLY 3-7 descriptive keywords separated by commas. Focus on: product type, visual style, colors, mood, setting. Example: 'lips, pink, glossy, minimalist, close-up'"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_tokens=100
        )
        
        keywords = response.choices[0].message.content.strip()
        return keywords
    
    except Exception as e:
        print(f"   Error analyzing concept photo: {e}")
        return ""

def analyze_model_photo(image_url, model_name):
    """Analyze model photo and extract descriptive keywords about their look/vibe"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze this model photo of {model_name}. Provide ONLY 3-7 descriptive keywords about their appearance and vibe, separated by commas. Focus on: style, mood, aesthetic, features. Example: 'chic, minimal, elegant, natural, youthful'"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_tokens=100
        )
        
        keywords = response.choices[0].message.content.strip()
        return keywords
    
    except Exception as e:
        print(f"   Error analyzing model photo: {e}")
        return ""

# ============================================================================
# LOAD AND PROCESS DATA
# ============================================================================

print("Loading data...")
df = pd.read_csv(f"{DATA_DIR}/2025_Bookings.csv")
print(f"✓ Loaded {len(df)} bookings from {df['job_id'].nunique()} unique jobs\n")

# Sample a subset for analysis (full analysis would take too long/cost too much)
print("NOTE: Analyzing a sample of jobs to demonstrate the feature.")
print("For full analysis, remove the .head(10) limit in the code.\n")

sample_jobs = df['job_id'].dropna().unique()[:10]  # Analyze first 10 jobs
print(f"Analyzing {len(sample_jobs)} jobs as a sample...\n")

concept_keywords_data = []
model_keywords_data = []

for job_id in sample_jobs:
    print(f"\n{'='*60}")
    print(f"Processing Job #{job_id}")
    print('='*60)
    
    job_bookings = df[df['job_id'] == job_id]
    first_booking = job_bookings.iloc[0]
    
    brand_name = str(first_booking['brand_name']) if pd.notna(first_booking['brand_name']) else ''
    job_name = str(first_booking['job_name']) if pd.notna(first_booking['job_name']) else ''
    
    print(f"Brand: {brand_name}")
    print(f"Job: {job_name}\n")
    
    # Analyze concept photos
    concept_photos = parse_array_field(first_booking['concept_photos'])
    
    if concept_photos:
        print(f"📸 Analyzing {len(concept_photos)} concept photo(s)...")
        
        for i, photo_url in enumerate(concept_photos[:3], 1):  # Max 3 photos per job
            if check_image_url(photo_url):
                print(f"   [{i}/{len(concept_photos[:3])}] Analyzing concept photo...")
                keywords = analyze_concept_photo(photo_url)
                
                concept_keywords_data.append({
                    'job_id': int(job_id),
                    'brand_name': brand_name,
                    'job_name': job_name,
                    'photo_url': photo_url,
                    'keywords': keywords
                })
                
                print(f"   ✓ Keywords: {keywords}")
                time.sleep(0.5)  # Rate limiting
            else:
                print(f"   ⚠️  Photo {i} not accessible, skipping...")
    else:
        print("   No concept photos for this job")
    
    # Analyze model photos
    print(f"\n👤 Analyzing {len(job_bookings)} model(s)...")
    
    for idx, booking in job_bookings.iterrows():
        talent_name = str(booking['talent_name']) if pd.notna(booking['talent_name']) else 'Model'
        headshot = booking['headshot'] if pd.notna(booking['headshot']) else None
        
        if headshot and check_image_url(headshot):
            print(f"   Analyzing {talent_name}'s headshot...")
            keywords = analyze_model_photo(headshot, talent_name)
            
            model_keywords_data.append({
                'job_id': int(job_id),
                'brand_name': brand_name,
                'job_name': job_name,
                'talent_name': talent_name,
                'photo_url': headshot,
                'keywords': keywords
            })
            
            print(f"   ✓ Keywords: {keywords}")
            time.sleep(0.5)  # Rate limiting
        else:
            print(f"   ⚠️  {talent_name}: No accessible headshot, skipping...")

print(f"\n\n{'='*80}")
print("ANALYSIS COMPLETE!")
print('='*80 + "\n")

# ============================================================================
# EXPORT RESULTS
# ============================================================================

print("Exporting results...\n")

# Concept photo keywords
if concept_keywords_data:
    concept_df = pd.DataFrame(concept_keywords_data)
    concept_df.to_csv(f'{OUTPUT_DIR}/concept_photo_keywords.csv', index=False, encoding='utf-8-sig')
    print(f"✓ Saved: {OUTPUT_DIR}/concept_photo_keywords.csv")
    print(f"  ({len(concept_df)} concept photos analyzed)\n")
else:
    print("⚠️  No concept photos were analyzed\n")

# Model photo keywords
if model_keywords_data:
    model_df = pd.DataFrame(model_keywords_data)
    model_df.to_csv(f'{OUTPUT_DIR}/model_photo_keywords.csv', index=False, encoding='utf-8-sig')
    print(f"✓ Saved: {OUTPUT_DIR}/model_photo_keywords.csv")
    print(f"  ({len(model_df)} model photos analyzed)\n")
else:
    print("⚠️  No model photos were analyzed\n")

# ============================================================================
# GENERATE SUMMARY REPORT
# ============================================================================

print("Generating summary report...\n")

html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI Vision Keywords Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f7fa;
            padding: 40px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            opacity: 0.9;
        }}
        
        .section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .job-entry {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .job-title {{
            font-weight: 700;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .job-subtitle {{
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        
        .photo-analysis {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .photo-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .photo-item img {{
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 4px;
            margin-bottom: 10px;
        }}
        
        .keywords {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
        }}
        
        .model-name {{
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat-box {{
            background: #f0f4ff;
            padding: 20px;
            border-radius: 8px;
            flex: 1;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 36px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Vision Keywords Report</h1>
        <p class="subtitle">Automated keyword extraction from concept photos and model images</p>
    </div>
    
    <div class="section">
        <h2>📊 Analysis Summary</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{len(sample_jobs)}</div>
                <div class="stat-label">Jobs Analyzed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(concept_keywords_data)}</div>
                <div class="stat-label">Concept Photos</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(model_keywords_data)}</div>
                <div class="stat-label">Model Photos</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>🎨 Concept Photo Keywords</h2>
"""

# Group concept keywords by job
if concept_keywords_data:
    concept_by_job = {}
    for item in concept_keywords_data:
        job_id = item['job_id']
        if job_id not in concept_by_job:
            concept_by_job[job_id] = {
                'brand': item['brand_name'],
                'job': item['job_name'],
                'photos': []
            }
        concept_by_job[job_id]['photos'].append(item)
    
    for job_id, data in concept_by_job.items():
        html_report += f"""
        <div class="job-entry">
            <div class="job-title">Job #{job_id}: {data['brand']}</div>
            <div class="job-subtitle">{data['job']}</div>
            <div class="photo-analysis">
"""
        for photo in data['photos']:
            html_report += f"""
                <div class="photo-item">
                    <img src="{photo['photo_url']}" loading="lazy">
                    <div class="keywords">{photo['keywords']}</div>
                </div>
"""
        html_report += """
            </div>
        </div>
"""
else:
    html_report += "<p>No concept photos were analyzed in this sample.</p>"

html_report += """
    </div>
    
    <div class="section">
        <h2>👤 Model Photo Keywords</h2>
"""

# Group model keywords by job
if model_keywords_data:
    model_by_job = {}
    for item in model_keywords_data:
        job_id = item['job_id']
        if job_id not in model_by_job:
            model_by_job[job_id] = {
                'brand': item['brand_name'],
                'job': item['job_name'],
                'models': []
            }
        model_by_job[job_id]['models'].append(item)
    
    for job_id, data in model_by_job.items():
        html_report += f"""
        <div class="job-entry">
            <div class="job-title">Job #{job_id}: {data['brand']}</div>
            <div class="job-subtitle">{data['job']}</div>
            <div class="photo-analysis">
"""
        for model in data['models']:
            html_report += f"""
                <div class="photo-item">
                    <div class="model-name">{model['talent_name']}</div>
                    <img src="{model['photo_url']}" loading="lazy">
                    <div class="keywords">{model['keywords']}</div>
                </div>
"""
        html_report += """
            </div>
        </div>
"""
else:
    html_report += "<p>No model photos were analyzed in this sample.</p>"

html_report += """
    </div>
    
    <div class="section">
        <h2>📁 Exported Files</h2>
        <ul>
            <li><strong>concept_photo_keywords.csv</strong> - Keywords for all concept photos</li>
            <li><strong>model_photo_keywords.csv</strong> - Keywords for all model photos</li>
        </ul>
        <p style="margin-top: 20px; color: #666;">
            <strong>Note:</strong> This analysis used OpenAI's GPT-4 Vision API. 
            To analyze more jobs, adjust the sample size in the script.
        </p>
    </div>
</body>
</html>
"""

with open(f'{OUTPUT_DIR}/ai_vision_report.html', 'w', encoding='utf-8') as f:
    f.write(html_report)

print(f"✓ Saved: {OUTPUT_DIR}/ai_vision_report.html\n")

print("="*80)
print("✅ AI VISION ANALYSIS COMPLETE!")
print("="*80)
print(f"\n📂 All outputs saved to: {OUTPUT_DIR}/")
print("🌐 Open 'ai_vision_report.html' to view the visual report!")
print("\n💡 This was a sample analysis of 10 jobs.")
print("   To analyze all jobs, edit line 151 in the script to remove .head(10)")
print("\n💰 Note: Full analysis costs ~$0.01-0.02 per image with GPT-4 Vision")
print("="*80 + "\n")
