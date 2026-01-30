"""
Script 5: Heuristic Keyword Extraction (Privacy-Safe)
Extracts keywords from job text and model metadata without using external AI
"""

import sys
import os
import pandas as pd
import re
from collections import Counter

print("\n" + "="*80)
print("SCRIPT 5: HEURISTIC KEYWORD EXTRACTION")
print("="*80 + "\n")

# Configuration
DATA_DIR = "data"
OUTPUT_DIR = "outputs/heuristic_keywords"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# LOAD DATA
# ============================================================================

print("Loading data...")
bookings_df = pd.read_csv(f"{DATA_DIR}/2025_Bookings.csv")
style_tags_df = pd.read_csv(f"{DATA_DIR}/style_tags.csv")
model_profiles_df = pd.read_csv(f"{DATA_DIR}/model_profiles.csv")

print(f"✓ Bookings: {len(bookings_df)} rows, {bookings_df['job_id'].nunique()} unique jobs")
print(f"✓ Style tags: {len(style_tags_df)} rows, {style_tags_df['talentId'].nunique()} unique models")
print(f"✓ Model profiles: {len(model_profiles_df)} rows\n")

# ============================================================================
# KEYWORD EXTRACTION FUNCTIONS
# ============================================================================

# Korean to English keyword mapping for common job terms
JOB_KEYWORD_MAP = {
    # Shoot types
    '룩북': 'lookbook',
    '화보': 'editorial',
    '캠페인': 'campaign',
    '광고': 'advertisement',
    '영상': 'video',
    '필름': 'film',
    '촬영': 'photoshoot',
    '웨딩': 'bridal, wedding',
    '뷰티': 'beauty',
    '코스메틱': 'cosmetic',
    '패션': 'fashion',
    '스킨케어': 'skincare',
    '립': 'lip',
    '메이크업': 'makeup',
    '향수': 'perfume, fragrance',
    '주얼리': 'jewelry',
    '액세서리': 'accessory',
    '의류': 'apparel, clothing',
    '신발': 'footwear, shoes',
    '가방': 'bag',
    '시계': 'watch',
    
    # Styles
    '미니멀': 'minimal, minimalist',
    '심플': 'simple, clean',
    '모던': 'modern',
    '빈티지': 'vintage',
    '레트로': 'retro',
    '클래식': 'classic',
    '캐주얼': 'casual',
    '스트릿': 'street, streetwear',
    '럭셔리': 'luxury',
    '프리미엄': 'premium',
    '엘레강스': 'elegant, elegance',
    '시크': 'chic',
    '내추럴': 'natural',
    '유니크': 'unique',
    
    # Concepts
    '봄': 'spring',
    '여름': 'summer',
    '가을': 'fall, autumn',
    '겨울': 'winter',
    '신제품': 'new product, launch',
    '런칭': 'launch',
    '글로벌': 'global',
    '샘플': 'sample',
    '스튜디오': 'studio',
    '야외': 'outdoor',
    '실내': 'indoor',
    
    # Product types
    '립밤': 'lip balm',
    '립스틱': 'lipstick',
    '파운데이션': 'foundation',
    '크림': 'cream',
    '세럼': 'serum',
    '마스크': 'mask',
    '니트': 'knit, knitwear',
    '티셔츠': 'tshirt',
    '원피스': 'dress',
    '자켓': 'jacket',
    '코트': 'coat',
    '팬츠': 'pants',
    '스커트': 'skirt',
}

def extract_job_keywords(job_name, inquiry_text, shoot_types, shoot_locations):
    """Extract keywords from job information"""
    keywords = []
    
    # Combine all text
    combined_text = f"{job_name} {inquiry_text}".lower()
    
    # Extract keywords using mapping
    for korean, english in JOB_KEYWORD_MAP.items():
        if korean in combined_text:
            keywords.extend([k.strip() for k in english.split(',')])
    
    # Add shoot types
    if pd.notna(shoot_types):
        types = str(shoot_types).replace('{', '').replace('}', '').split(',')
        for t in types:
            t = t.strip()
            if t == 'photo':
                keywords.append('photography')
            elif t == 'video':
                keywords.append('video')
    
    # Add locations
    if pd.notna(shoot_locations):
        locs = str(shoot_locations).replace('{', '').replace('}', '').split(',')
        for loc in locs:
            loc = loc.strip()
            if loc in ['indoor', 'outdoor', 'studio']:
                keywords.append(loc)
    
    # Deduplicate while preserving order
    seen = set()
    unique_keywords = []
    for k in keywords:
        if k and k not in seen:
            seen.add(k)
            unique_keywords.append(k)
    
    return unique_keywords

def clean_tag_name(tag):
    """Clean up tag names"""
    if pd.isna(tag):
        return ""
    
    tag = str(tag)
    # Remove (New) prefix
    tag = re.sub(r'\(New\)\s*', '', tag)
    # Remove Korean parts after English (e.g., "Active Wear 액티브웨어" -> "Active Wear")
    parts = tag.split()
    english_parts = []
    for part in parts:
        # Keep part if it's primarily English/Latin characters
        if re.search(r'[a-zA-Z]', part):
            english_parts.append(part)
    
    return ' '.join(english_parts).strip()

def get_model_keywords(talent_id, style_tags_df, model_profiles_df):
    """Extract keywords for a model from their tags and profile"""
    keywords = []
    
    # Get style tags
    model_tags = style_tags_df[style_tags_df['talentId'] == talent_id]
    for tag in model_tags['tagName'].unique():
        cleaned = clean_tag_name(tag)
        if cleaned:
            keywords.append(cleaned.lower())
    
    # Get profile attributes
    profile = model_profiles_df[model_profiles_df['id'] == talent_id]
    if not profile.empty:
        profile = profile.iloc[0]
        
        # Add physical attributes
        if pd.notna(profile['hair']) and profile['hair'] != '':
            hair = str(profile['hair']).replace('_', ' ')
            keywords.append(f"{hair} hair")
        
        if pd.notna(profile['eyes']) and profile['eyes'] != '':
            eyes = str(profile['eyes'])
            keywords.append(f"{eyes} eyes")
        
        if pd.notna(profile['gender']):
            keywords.append(str(profile['gender']))
        
        # Height category
        if pd.notna(profile['height']):
            height = float(profile['height'])
            if profile['gender'] == 'female':
                if height >= 175:
                    keywords.append('tall')
                elif height <= 165:
                    keywords.append('petite')
            elif profile['gender'] == 'male':
                if height >= 185:
                    keywords.append('tall')
    
    # Deduplicate
    return list(set([k for k in keywords if k]))

# ============================================================================
# PROCESS JOBS
# ============================================================================

print("Processing jobs and extracting keywords...\n")

results = []
job_count = 0

for job_id in bookings_df['job_id'].dropna().unique():
    job_bookings = bookings_df[bookings_df['job_id'] == job_id]
    first_booking = job_bookings.iloc[0]
    
    # Extract job keywords
    job_keywords = extract_job_keywords(
        str(first_booking['job_name']) if pd.notna(first_booking['job_name']) else '',
        str(first_booking['inquiry_text']) if pd.notna(first_booking['inquiry_text']) else '',
        first_booking['shoot_types'],
        first_booking['shoot_locations']
    )
    
    # Get model keywords for each model in this job
    model_keywords_list = []
    for idx, booking in job_bookings.iterrows():
        talent_id = booking['talent_id']
        if pd.notna(talent_id):
            talent_id = int(talent_id)
            model_kw = get_model_keywords(talent_id, style_tags_df, model_profiles_df)
            model_keywords_list.append({
                'talent_id': talent_id,
                'talent_name': str(booking['talent_name']) if pd.notna(booking['talent_name']) else '',
                'keywords': model_kw
            })
    
    # Aggregate model keywords (most common across all models in job)
    all_model_keywords = []
    for mkw in model_keywords_list:
        all_model_keywords.extend(mkw['keywords'])
    
    model_keyword_counts = Counter(all_model_keywords)
    top_model_keywords = [kw for kw, count in model_keyword_counts.most_common(10)]
    
    results.append({
        'job_id': int(job_id),
        'brand_name': str(first_booking['brand_name']) if pd.notna(first_booking['brand_name']) else '',
        'job_name': str(first_booking['job_name']) if pd.notna(first_booking['job_name']) else '',
        'job_keywords': ', '.join(job_keywords) if job_keywords else '',
        'model_keywords': ', '.join(top_model_keywords) if top_model_keywords else '',
        'num_models': len(model_keywords_list),
        'individual_model_keywords': str(model_keywords_list)  # Full detail for reference
    })
    
    job_count += 1
    if job_count % 100 == 0:
        print(f"  Processed {job_count} jobs...")

print(f"\n✓ Processed {job_count} jobs\n")

# ============================================================================
# EXPORT RESULTS
# ============================================================================

print("Exporting results...\n")

results_df = pd.DataFrame(results)
results_df.to_csv(f'{OUTPUT_DIR}/job_model_keywords.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/job_model_keywords.csv")
print(f"  ({len(results_df)} jobs with keywords)\n")

# Create a simplified version without individual model details
simple_df = results_df[['job_id', 'brand_name', 'job_name', 'job_keywords', 'model_keywords', 'num_models']]
simple_df.to_csv(f'{OUTPUT_DIR}/keywords_summary.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/keywords_summary.csv")
print(f"  (Simplified view)\n")

# ============================================================================
# GENERATE HTML REPORT
# ============================================================================

print("Generating HTML report...\n")

# Sample top jobs for display
sample_results = results[:50]

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Heuristic Keywords Report</title>
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
        
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-box {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            flex: 1;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
            vertical-align: top;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .job-id {{
            background: #667eea;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
        }}
        
        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        
        .keyword-tag {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        
        .keyword-tag.model {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        
        .search-box {{
            margin-bottom: 20px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏷️ Heuristic Keywords Report</h1>
        <p class="subtitle">Privacy-safe keyword extraction from job text and model metadata</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{len(results_df)}</div>
            <div class="stat-label">Total Jobs</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{len(results_df[results_df['job_keywords'] != ''])}</div>
            <div class="stat-label">Jobs with Keywords</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{results_df['num_models'].sum()}</div>
            <div class="stat-label">Total Models</div>
        </div>
    </div>
    
    <div class="section">
        <h2>🔍 Sample Results (Top 50 Jobs)</h2>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search by job ID, brand, or keywords..." onkeyup="filterTable()">
        </div>
        <table id="resultsTable">
            <thead>
                <tr>
                    <th>Job ID</th>
                    <th>Brand & Job Name</th>
                    <th>Concept Keywords</th>
                    <th>Model Keywords</th>
                    <th>Models</th>
                </tr>
            </thead>
            <tbody>
"""

for result in sample_results:
    job_kw_tags = ''.join([f'<span class="keyword-tag">{kw.strip()}</span>' 
                           for kw in result['job_keywords'].split(',') if kw.strip()])
    model_kw_tags = ''.join([f'<span class="keyword-tag model">{kw.strip()}</span>' 
                             for kw in result['model_keywords'].split(',') if kw.strip()])
    
    html_content += f"""
                <tr>
                    <td><span class="job-id">{result['job_id']}</span></td>
                    <td>
                        <strong>{result['brand_name']}</strong><br>
                        <span style="color: #666; font-size: 13px;">{result['job_name']}</span>
                    </td>
                    <td>
                        <div class="keywords">
                            {job_kw_tags if job_kw_tags else '<span style="color: #999;">No keywords</span>'}
                        </div>
                    </td>
                    <td>
                        <div class="keywords">
                            {model_kw_tags if model_kw_tags else '<span style="color: #999;">No keywords</span>'}
                        </div>
                    </td>
                    <td style="text-align: center;">{result['num_models']}</td>
                </tr>
"""

html_content += """
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>📁 Exported Files</h2>
        <ul>
            <li><strong>job_model_keywords.csv</strong> - Complete keywords for all jobs with detailed model info</li>
            <li><strong>keywords_summary.csv</strong> - Simplified view with just the key fields</li>
        </ul>
        <p style="margin-top: 20px; color: #666;">
            <strong>100% Privacy-Safe:</strong> All keywords extracted from existing text and metadata. 
            No images sent to any external services or AI models.
        </p>
    </div>
    
    <script>
        function filterTable() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const table = document.getElementById('resultsTable');
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            }
        }
    </script>
</body>
</html>
"""

with open(f'{OUTPUT_DIR}/keywords_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Saved: {OUTPUT_DIR}/keywords_report.html\n")

# ============================================================================
# STATISTICS
# ============================================================================

print("="*80)
print("KEYWORD STATISTICS")
print("="*80 + "\n")

# Job keyword frequency
all_job_keywords = []
for kw_str in results_df['job_keywords']:
    if kw_str:
        all_job_keywords.extend([k.strip() for k in str(kw_str).split(',') if k.strip()])

job_kw_counter = Counter(all_job_keywords)
print("📊 Top 15 Concept Keywords (from job text):")
for kw, count in job_kw_counter.most_common(15):
    print(f"   {kw:30s} - {count} jobs")

print()

# Model keyword frequency
all_model_keywords = []
for kw_str in results_df['model_keywords']:
    if kw_str:
        all_model_keywords.extend([k.strip() for k in str(kw_str).split(',') if k.strip()])

model_kw_counter = Counter(all_model_keywords)
print("👤 Top 15 Model Keywords (from style tags + profiles):")
for kw, count in model_kw_counter.most_common(15):
    print(f"   {kw:30s} - {count} jobs")

print("\n" + "="*80)
print("✅ HEURISTIC KEYWORD EXTRACTION COMPLETE!")
print("="*80)
print(f"\n📂 All outputs saved to: {OUTPUT_DIR}/")
print("🌐 Open 'keywords_report.html' to view the results!")
print("\n💚 100% privacy-safe - no images sent anywhere!")
print("="*80 + "\n")
