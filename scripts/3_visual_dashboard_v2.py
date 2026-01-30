"""
Script 3: Combined Visual Dashboard V2
Creates a horizontal table-based interactive dashboard with grouped jobs
"""

import sys
import subprocess
import os

# Check and install required packages
required_packages = {
    'pandas': 'pandas',
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

# Now import everything
import pandas as pd
import json
import re

print("\n" + "="*80)
print("SCRIPT 3: VISUAL DASHBOARD V2 - TABLE LAYOUT")
print("="*80 + "\n")

# Configuration
DATA_DIR = "data"
OUTPUT_DIR = "outputs/visual_dashboard"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read data
print("Loading data...")
df = pd.read_csv(f"{DATA_DIR}/2025_Bookings.csv")
print(f"✓ Loaded {len(df)} bookings from {df['job_id'].nunique()} unique jobs\n")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_array_field(field_value):
    """Parse fields that are in {value1,value2} or array format"""
    if pd.isna(field_value):
        return []
    
    field_str = str(field_value).strip()
    
    # Handle empty arrays
    if field_str == '{}' or field_str == '':
        return []
    
    # Remove curly braces and quotes
    field_str = field_str.strip('{}').strip('"')
    
    # Split by comma
    values = [v.strip().strip('"') for v in field_str.split(',')]
    
    return [v for v in values if v and v.startswith('http')]

def truncate_text(text, max_length=500):
    """Truncate text to max_length"""
    if pd.isna(text):
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

# ============================================================================
# PROCESS DATA BY JOB WITH GROUPING
# ============================================================================

print("Processing data by job...")
jobs_by_id = {}

for job_id in df['job_id'].dropna().unique():
    job_bookings = df[df['job_id'] == job_id]
    first_booking = job_bookings.iloc[0]
    
    # Parse concept photos
    concept_photos = parse_array_field(first_booking['concept_photos'])
    
    # Get all models
    models = []
    for idx, booking in job_bookings.iterrows():
        headshot = booking['headshot'] if pd.notna(booking['headshot']) else None
        thumbnails = parse_array_field(booking['thumbnails'])
        
        models.append({
            'talent_id': int(booking['talent_id']) if pd.notna(booking['talent_id']) else 0,
            'talent_name': str(booking['talent_name']) if pd.notna(booking['talent_name']) else '',
            'talent_nationality': str(booking['talent_nationality']) if pd.notna(booking['talent_nationality']) else '',
            'headshot': headshot,
            'thumbnails': thumbnails[:8] if thumbnails else []
        })
    
    inquiry_text = first_booking['inquiry_text']
    has_korean = bool(re.search('[ㄱ-ㅎㅏ-ㅣ가-힣]', str(inquiry_text))) if pd.notna(inquiry_text) else False
    
    jobs_by_id[int(job_id)] = {
        'job_id': int(job_id),
        'brand_name': str(first_booking['brand_name']) if pd.notna(first_booking['brand_name']) else '',
        'job_name': str(first_booking['job_name']) if pd.notna(first_booking['job_name']) else '',
        'inquiry_text': truncate_text(inquiry_text, 500),
        'inquiry_text_lang': 'Korean' if has_korean else 'English',
        'start_date': str(first_booking['start_date_time']) if pd.notna(first_booking['start_date_time']) else '',
        'shoot_hours': int(first_booking['shoot_hours']) if pd.notna(first_booking['shoot_hours']) else 0,
        'concept_photos': concept_photos,
        'models': models
    }

print(f"✓ Processed {len(jobs_by_id)} individual jobs\n")

# Group duplicate jobs
print("Grouping duplicate jobs...")
jobs_data = []
processed_ids = set()

for job_id in sorted(jobs_by_id.keys(), reverse=True):
    if job_id in processed_ids:
        continue
    
    current_job = jobs_by_id[job_id]
    
    # Find duplicates
    duplicate_jobs = [job_id]
    for other_id, other_job in jobs_by_id.items():
        if other_id != job_id and other_id not in processed_ids:
            if (other_job['brand_name'] == current_job['brand_name'] and
                other_job['job_name'] == current_job['job_name'] and
                other_job['start_date'] == current_job['start_date']):
                duplicate_jobs.append(other_id)
    
    processed_ids.update(duplicate_jobs)
    
    # Merge models and photos
    all_models = []
    all_concept_photos = list(current_job['concept_photos'])
    
    for dup_id in duplicate_jobs:
        dup_job = jobs_by_id[dup_id]
        all_models.extend(dup_job['models'])
        for photo in dup_job['concept_photos']:
            if photo not in all_concept_photos:
                all_concept_photos.append(photo)
    
    # Deduplicate models by talent_id
    unique_models = {}
    for model in all_models:
        tid = model['talent_id']
        if tid not in unique_models:
            unique_models[tid] = model
        else:
            for thumb in model['thumbnails']:
                if thumb not in unique_models[tid]['thumbnails']:
                    unique_models[tid]['thumbnails'].append(thumb)
    
    jobs_data.append({
        'job_ids': sorted(duplicate_jobs),
        'is_grouped': len(duplicate_jobs) > 1,
        'brand_name': current_job['brand_name'],
        'job_name': current_job['job_name'],
        'inquiry_text': current_job['inquiry_text'],
        'inquiry_text_lang': current_job['inquiry_text_lang'],
        'start_date': current_job['start_date'],
        'shoot_hours': current_job['shoot_hours'],
        'concept_photos': all_concept_photos,
        'models': list(unique_models.values()),
        'num_models': len(unique_models)
    })

print(f"✓ Grouped into {len(jobs_data)} unique jobs ({len(jobs_by_id) - len(jobs_data)} duplicates merged)\n")

# ============================================================================
# LOAD AND MERGE KEYWORDS & TRANSLATIONS
# ============================================================================

print("Loading heuristic keywords...")
keywords_file = "outputs/heuristic_keywords/keywords_summary.csv"

if os.path.exists(keywords_file):
    keywords_df = pd.read_csv(keywords_file)
    print(f"✓ Loaded keywords for {len(keywords_df)} jobs\n")
    
    # Create keyword lookup by job_id
    keywords_lookup = {}
    for idx, row in keywords_df.iterrows():
        keywords_lookup[row['job_id']] = {
            'job_keywords': row['job_keywords'] if pd.notna(row['job_keywords']) else '',
            'model_keywords': row['model_keywords'] if pd.notna(row['model_keywords']) else ''
        }
else:
    print("⚠️  Keywords file not found. Run 5_heuristic_keywords.py first.")
    print("   Dashboard will be generated without keywords.\n")
    keywords_lookup = {}

print("Loading translations...")
translations_file = "outputs/vocabulary/vocabulary_with_translations.csv"

if os.path.exists(translations_file):
    translations_df = pd.read_csv(translations_file)
    print(f"✓ Loaded translations for {len(translations_df)} jobs\n")
    
    # Create translations lookup by job_id
    translations_lookup = {}
    for idx, row in translations_df.iterrows():
        translations_lookup[row['job_id']] = {
            'inquiry_text_en': row['inquiry_text_en'] if pd.notna(row['inquiry_text_en']) else '',
            'brand_name_en': row['brand_name_en'] if pd.notna(row['brand_name_en']) else '',
            'job_name_en': row['job_name_en'] if pd.notna(row['job_name_en']) else ''
        }
else:
    print("⚠️  Translations file not found. Run 1_text_vocabulary.py first.")
    print("   Dashboard will be generated without English translations.\n")
    translations_lookup = {}

# Merge keywords and translations into jobs_data
print("Merging keywords and translations into job data...")
for job in jobs_data:
    # Get keywords and translations for first job_id (primary in group)
    primary_job_id = job['job_ids'][0]
    
    # Merge keywords
    if primary_job_id in keywords_lookup:
        job['job_keywords'] = keywords_lookup[primary_job_id]['job_keywords']
        job['model_keywords'] = keywords_lookup[primary_job_id]['model_keywords']
    else:
        job['job_keywords'] = ''
        job['model_keywords'] = ''
    
    # Merge translations
    if primary_job_id in translations_lookup:
        job['inquiry_text_en'] = translations_lookup[primary_job_id]['inquiry_text_en']
        job['brand_name_en'] = translations_lookup[primary_job_id]['brand_name_en']
        job['job_name_en'] = translations_lookup[primary_job_id]['job_name_en']
    else:
        job['inquiry_text_en'] = ''
        job['brand_name_en'] = ''
        job['job_name_en'] = ''
    
    # Add talent IDs for search
    job['talent_ids'] = [m['talent_id'] for m in job['models']]

print(f"✓ Data merged\n")

# ============================================================================
# GENERATE HTML DASHBOARD WITH TABLE LAYOUT
# ============================================================================

print("Generating HTML dashboard...")

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Visual Dashboard - Table View</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f7fa;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            opacity: 0.9;
        }}
        
        .controls {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .search-box input {{
            width: 100%;
            max-width: 500px;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .stats {{
            display: flex;
            gap: 15px;
            margin: 15px 0;
        }}
        
        .stat-badge {{
            background: #f0f4ff;
            padding: 10px 20px;
            border-radius: 6px;
            color: #667eea;
            font-weight: 600;
        }}
        
        .table-container {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            position: sticky;
            top: 0;
            background: #667eea;
            color: white;
            z-index: 10;
        }}
        
        th {{
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
            border-bottom: 2px solid #5568d3;
        }}
        
        td {{
            padding: 15px 10px;
            border-bottom: 1px solid #e0e0e0;
            vertical-align: top;
        }}
        
        tr:hover td {{
            background-color: #f8f9fa;
        }}
        
        /* Column 1: Job Info */
        .job-info {{
            min-width: 200px;
            max-width: 250px;
        }}
        
        .job-ids {{
            background: #667eea;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 8px;
        }}
        
        .job-ids.grouped {{
            background: #e91e63;
        }}
        
        .brand-name {{
            font-weight: 700;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .job-name {{
            font-size: 13px;
            color: #666;
            margin-bottom: 8px;
        }}
        
        .job-meta {{
            font-size: 12px;
            color: #999;
            line-height: 1.6;
        }}
        
        /* Column 2: Inquiry Text */
        .inquiry-cell {{
            min-width: 300px;
            max-width: 400px;
        }}
        
        .inquiry-text {{
            font-size: 13px;
            line-height: 1.6;
            color: #555;
            max-height: 150px;
            overflow-y: auto;
            margin-bottom: 10px;
        }}
        
        .inquiry-translation {{
            font-size: 13px;
            line-height: 1.6;
            color: #666;
            max-height: 150px;
            overflow-y: auto;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }}
        
        .text-label {{
            font-size: 11px;
            font-weight: 600;
            color: #999;
            margin-bottom: 5px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .lang-badge {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 8px;
            display: inline-block;
        }}
        
        /* Column 3: Concept Photos */
        .photos-cell {{
            min-width: 250px;
        }}
        
        .photos-scroll {{
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding-bottom: 5px;
        }}
        
        .photos-scroll::-webkit-scrollbar {{
            height: 6px;
        }}
        
        .photos-scroll::-webkit-scrollbar-thumb {{
            background: #ccc;
            border-radius: 3px;
        }}
        
        .concept-photo {{
            flex-shrink: 0;
            width: 120px;
            height: 120px;
            border-radius: 6px;
            overflow: hidden;
            background: #f0f0f0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .concept-photo img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        /* Column 4: Models */
        .models-cell {{
            min-width: 400px;
        }}
        
        .models-scroll {{
            display: flex;
            gap: 15px;
            overflow-x: auto;
            padding-bottom: 5px;
        }}
        
        .models-scroll::-webkit-scrollbar {{
            height: 6px;
        }}
        
        .models-scroll::-webkit-scrollbar-thumb {{
            background: #ccc;
            border-radius: 3px;
        }}
        
        .model-item {{
            flex-shrink: 0;
            width: 180px;
        }}
        
        .model-headshot {{
            width: 180px;
            height: 180px;
            border-radius: 6px;
            overflow: hidden;
            background: #f0f0f0;
            margin-bottom: 8px;
        }}
        
        .model-headshot img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .model-name {{
            font-weight: 600;
            font-size: 13px;
            margin-bottom: 4px;
            color: #333;
        }}
        
        .model-nationality {{
            font-size: 12px;
            color: #999;
            margin-bottom: 8px;
        }}
        
        .model-thumbnails {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }}
        
        .model-thumb {{
            width: 55px;
            height: 55px;
            border-radius: 4px;
            overflow: hidden;
            background: #f0f0f0;
        }}
        
        .model-thumb img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .no-content {{
            color: #999;
            font-size: 13px;
            font-style: italic;
        }}
        
        /* Keywords column */
        .keywords-cell {{
            min-width: 250px;
            max-width: 300px;
        }}
        
        .keywords-section {{
            margin-bottom: 12px;
        }}
        
        .keywords-label {{
            font-size: 11px;
            font-weight: 600;
            color: #666;
            margin-bottom: 5px;
            text-transform: uppercase;
        }}
        
        .keyword-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        
        .keyword-tag {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
        }}
        
        .keyword-tag.model {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin: 20px 0;
        }}
        
        .pagination button {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .pagination button:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}
        
        .pagination .page-info {{
            font-weight: 500;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Visual Dashboard - Table View</h1>
        <p class="subtitle">Concept Photos & Selected Models with Grouped Jobs</p>
    </div>
    
    <div class="controls">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search by job ID, brand, job name, talent ID, or keywords..." 
                   onkeyup="filterJobs()">
        </div>
        <div class="stats">
            <div class="stat-badge" id="totalJobs">Total: {len(jobs_data)} unique jobs</div>
            <div class="stat-badge" id="groupedJobs">{len([j for j in jobs_data if j['is_grouped']])} grouped</div>
            <div class="stat-badge" id="visibleJobs"></div>
        </div>
    </div>
    
    <div class="pagination">
        <button id="prevBtn" onclick="changePage(-1)">← Previous</button>
        <span class="page-info" id="pageInfo">Page 1 of 1</span>
        <button id="nextBtn" onclick="changePage(1)">Next →</button>
    </div>
    
    <div class="table-container">
        <table id="jobsTable">
            <thead>
                <tr>
                    <th>Job Info</th>
                    <th>Inquiry Text</th>
                    <th>Keywords</th>
                    <th>Concept Photos</th>
                    <th>Selected Models</th>
                </tr>
            </thead>
            <tbody id="tableBody">
            </tbody>
        </table>
    </div>
    
    <div class="pagination">
        <button id="prevBtn2" onclick="changePage(-1)">← Previous</button>
        <span class="page-info" id="pageInfo2">Page 1 of 1</span>
        <button id="nextBtn2" onclick="changePage(1)">Next →</button>
    </div>
    
    <script>
        const allJobs = {json.dumps(jobs_data, ensure_ascii=False)};
        let filteredJobs = allJobs;
        let currentPage = 1;
        const jobsPerPage = 20;
        
        function filterJobs() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            
            if (!searchTerm) {{
                filteredJobs = allJobs;
            }} else {{
                filteredJobs = allJobs.filter(job => 
                    job.job_ids.join(',').toLowerCase().includes(searchTerm) ||
                    job.brand_name.toLowerCase().includes(searchTerm) ||
                    job.job_name.toLowerCase().includes(searchTerm) ||
                    (job.inquiry_text && job.inquiry_text.toLowerCase().includes(searchTerm)) ||
                    (job.inquiry_text_en && job.inquiry_text_en.toLowerCase().includes(searchTerm)) ||
                    job.talent_ids.join(',').toLowerCase().includes(searchTerm) ||
                    (job.job_keywords && job.job_keywords.toLowerCase().includes(searchTerm)) ||
                    (job.model_keywords && job.model_keywords.toLowerCase().includes(searchTerm))
                );
            }}
            
            currentPage = 1;
            renderJobs();
        }}
        
        function renderJobs() {{
            const totalPages = Math.ceil(filteredJobs.length / jobsPerPage);
            const start = (currentPage - 1) * jobsPerPage;
            const end = start + jobsPerPage;
            const pageJobs = filteredJobs.slice(start, end);
            
            // Update pagination
            ['pageInfo', 'pageInfo2'].forEach(id => {{
                document.getElementById(id).textContent = `Page ${{currentPage}} of ${{totalPages || 1}}`;
            }});
            
            ['prevBtn', 'prevBtn2'].forEach(id => {{
                document.getElementById(id).disabled = currentPage === 1;
            }});
            
            ['nextBtn', 'nextBtn2'].forEach(id => {{
                document.getElementById(id).disabled = currentPage >= totalPages;
            }});
            
            document.getElementById('visibleJobs').textContent = `Showing: ${{filteredJobs.length}}`;
            
            // Render table rows
            const tbody = document.getElementById('tableBody');
            
            if (pageJobs.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:40px;">No jobs found matching your search.</td></tr>';
                return;
            }}
            
            tbody.innerHTML = pageJobs.map(job => `
                <tr>
                    <td class="job-info">
                        <div class="job-ids ${{job.is_grouped ? 'grouped' : ''}}">
                            ${{job.is_grouped ? 'Jobs: ' : 'Job '}}${{job.job_ids.join(', ')}}
                        </div>
                        <div class="brand-name">${{escapeHtml(job.brand_name)}}</div>
                        <div class="job-name">${{escapeHtml(job.job_name)}}</div>
                        <div class="job-meta">
                            📅 ${{job.start_date.split(' ')[0]}}<br>
                            ⏰ ${{job.shoot_hours}}h<br>
                            👥 ${{job.num_models}} model${{job.num_models > 1 ? 's' : ''}}
                        </div>
                    </td>
                    <td class="inquiry-cell">
                        ${{job.inquiry_text ? `
                            <div class="text-label">🇰🇷 Korean Original</div>
                            <div class="inquiry-text">${{escapeHtml(job.inquiry_text)}}</div>
                            ${{job.inquiry_text_en ? `
                                <div class="text-label">🇬🇧 English Translation</div>
                                <div class="inquiry-translation">${{escapeHtml(job.inquiry_text_en)}}</div>
                            ` : ''}}
                        ` : '<div class="no-content">No inquiry text</div>'}}
                    </td>
                    <td class="keywords-cell">
                        ${{job.job_keywords || job.model_keywords ? `
                            ${{job.job_keywords ? `
                                <div class="keywords-section">
                                    <div class="keywords-label">🎨 Concept</div>
                                    <div class="keyword-tags">
                                        ${{job.job_keywords.split(',').map(kw => 
                                            kw.trim() ? `<span class="keyword-tag">${{kw.trim()}}</span>` : ''
                                        ).join('')}}
                                    </div>
                                </div>
                            ` : ''}}
                            ${{job.model_keywords ? `
                                <div class="keywords-section">
                                    <div class="keywords-label">👤 Models</div>
                                    <div class="keyword-tags">
                                        ${{job.model_keywords.split(',').map(kw => 
                                            kw.trim() ? `<span class="keyword-tag model">${{kw.trim()}}</span>` : ''
                                        ).join('')}}
                                    </div>
                                </div>
                            ` : ''}}
                        ` : '<div class="no-content">No keywords</div>'}}
                    </td>
                    <td class="photos-cell">
                        ${{job.concept_photos.length > 0 ? `
                            <div class="photos-scroll">
                                ${{job.concept_photos.map(url => `
                                    <div class="concept-photo">
                                        <img src="${{url}}" loading="lazy" 
                                             onerror="this.parentElement.style.display='none'">
                                    </div>
                                `).join('')}}
                            </div>
                        ` : '<div class="no-content">No concept photos</div>'}}
                    </td>
                    <td class="models-cell">
                        ${{job.models.length > 0 ? `
                            <div class="models-scroll">
                                ${{job.models.map(model => `
                                    <div class="model-item">
                                        ${{model.headshot ? `
                                            <div class="model-headshot">
                                                <img src="${{model.headshot}}" loading="lazy"
                                                     onerror="this.parentElement.style.display='none'">
                                            </div>
                                        ` : ''}}
                                        <div class="model-name">${{escapeHtml(model.talent_name)}}</div>
                                        <div class="model-nationality">${{model.talent_nationality}}</div>
                                        ${{model.thumbnails.length > 0 ? `
                                            <div class="model-thumbnails">
                                                ${{model.thumbnails.map(url => `
                                                    <div class="model-thumb">
                                                        <img src="${{url}}" loading="lazy"
                                                             onerror="this.parentElement.style.display='none'">
                                                    </div>
                                                `).join('')}}
                                            </div>
                                        ` : ''}}
                                    </div>
                                `).join('')}}
                            </div>
                        ` : '<div class="no-content">No models</div>'}}
                    </td>
                </tr>
            `).join('');
        }}
        
        function changePage(delta) {{
            const totalPages = Math.ceil(filteredJobs.length / jobsPerPage);
            currentPage = Math.max(1, Math.min(currentPage + delta, totalPages));
            renderJobs();
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        // Initial render
        renderJobs();
    </script>
</body>
</html>
"""

# Write HTML file
with open(f'{OUTPUT_DIR}/visual_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Saved: {OUTPUT_DIR}/visual_dashboard.html\n")

# Export statistics
stats_df = pd.DataFrame([{
    'metric': 'Total Jobs',
    'value': len(jobs_data)
}, {
    'metric': 'Grouped Jobs',
    'value': len([j for j in jobs_data if j['is_grouped']])
}, {
    'metric': 'Individual Job IDs',
    'value': len(jobs_by_id)
}])

stats_df.to_csv(f'{OUTPUT_DIR}/dashboard_statistics.csv', index=False)
print(f"✓ Saved: {OUTPUT_DIR}/dashboard_statistics.csv\n")

print("="*80)
print("✅ VISUAL DASHBOARD V2 COMPLETE!")
print("="*80)
print(f"\n📂 Outputs saved to: {OUTPUT_DIR}/")
print("🌐 Open 'visual_dashboard.html' to view the table-based dashboard!")
print("\n" + "="*80 + "\n")
