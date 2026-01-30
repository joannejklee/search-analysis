"""
Script 3: Combined Visual Dashboard
Creates an interactive dashboard showing concept photos and selected models per job
"""

import sys
import subprocess
import os

# Check and install required packages
required_packages = {
    'pandas': 'pandas',
    'jinja2': 'jinja2',
    'requests': 'requests',
    'PIL': 'Pillow'
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
from jinja2 import Template
import requests
from PIL import Image
from io import BytesIO
import base64

print("\n" + "="*80)
print("SCRIPT 3: COMBINED VISUAL DASHBOARD")
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

def truncate_text(text, max_length=200):
    """Truncate text to max_length"""
    if pd.isna(text):
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def validate_image_url(url):
    """Check if URL is valid and accessible"""
    if not url or not url.startswith('http'):
        return False
    try:
        response = requests.head(url, timeout=2)
        return response.status_code == 200
    except:
        return False

# ============================================================================
# PROCESS DATA BY JOB
# ============================================================================

print("Processing data by job...")
print("This may take a few minutes...\n")

# Group by job_id and aggregate, then group duplicate jobs
print("Step 1: Processing individual jobs...")
jobs_by_id = {}

for job_id in df['job_id'].dropna().unique():
    job_bookings = df[df['job_id'] == job_id]
    
    # Get job-level data (same for all bookings in a job)
    first_booking = job_bookings.iloc[0]
    
    # Parse concept photos (deduplicated per job)
    concept_photos = parse_array_field(first_booking['concept_photos'])
    
    # Get all models selected for this job
    models = []
    for idx, booking in job_bookings.iterrows():
        headshot = booking['headshot'] if pd.notna(booking['headshot']) else None
        thumbnails = parse_array_field(booking['thumbnails'])
        
        models.append({
            'booking_id': int(booking['booking_id']) if pd.notna(booking['booking_id']) else 0,
            'talent_id': int(booking['talent_id']) if pd.notna(booking['talent_id']) else 0,
            'talent_name': str(booking['talent_name']) if pd.notna(booking['talent_name']) else '',
            'talent_nationality': str(booking['talent_nationality']) if pd.notna(booking['talent_nationality']) else '',
            'talent_belong': str(booking['talent_belong']) if pd.notna(booking['talent_belong']) else '',
            'headshot': headshot,
            'thumbnails': thumbnails[:6] if thumbnails else []  # Limit to 6 thumbnails per model
        })
    
    # Detect language of inquiry text
    inquiry_text = first_booking['inquiry_text']
    has_korean = bool(re.search('[ㄱ-ㅎㅏ-ㅣ가-힣]', str(inquiry_text))) if pd.notna(inquiry_text) else False
    
    jobs_by_id[int(job_id)] = {
        'job_id': int(job_id),
        'brand_name': str(first_booking['brand_name']) if pd.notna(first_booking['brand_name']) else '',
        'job_name': str(first_booking['job_name']) if pd.notna(first_booking['job_name']) else '',
        'inquiry_text': truncate_text(inquiry_text, 500),
        'inquiry_text_full': str(inquiry_text) if pd.notna(inquiry_text) else '',
        'inquiry_text_lang': 'Korean' if has_korean else 'English',
        'region': str(first_booking['region']) if pd.notna(first_booking['region']) else '',
        'start_date': str(first_booking['start_date_time']) if pd.notna(first_booking['start_date_time']) else '',
        'shoot_hours': int(first_booking['shoot_hours']) if pd.notna(first_booking['shoot_hours']) else 0,
        'concept_photos': concept_photos,
        'models': models,
        'num_models': len(models)
    }

print(f"✓ Processed {len(jobs_by_id)} individual jobs\n")

# Step 2: Group duplicate jobs (same brand, job name, and datetime)
print("Step 2: Grouping duplicate jobs...")
jobs_data = []
processed_ids = set()

for job_id in sorted(jobs_by_id.keys(), reverse=True):
    if job_id in processed_ids:
        continue
    
    current_job = jobs_by_id[job_id]
    
    # Find other jobs with same brand, job name, and datetime
    duplicate_jobs = [job_id]
    for other_id, other_job in jobs_by_id.items():
        if other_id != job_id and other_id not in processed_ids:
            if (other_job['brand_name'] == current_job['brand_name'] and
                other_job['job_name'] == current_job['job_name'] and
                other_job['start_date'] == current_job['start_date']):
                duplicate_jobs.append(other_id)
    
    # Mark all as processed
    processed_ids.update(duplicate_jobs)
    
    # Merge all models and concept photos from duplicate jobs
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
            # Merge thumbnails
            for thumb in model['thumbnails']:
                if thumb not in unique_models[tid]['thumbnails']:
                    unique_models[tid]['thumbnails'].append(thumb)
    
    jobs_data.append({
        'job_ids': sorted(duplicate_jobs),
        'is_grouped': len(duplicate_jobs) > 1,
        'brand_name': current_job['brand_name'],
        'job_name': current_job['job_name'],
        'inquiry_text': current_job['inquiry_text'],
        'inquiry_text_full': current_job['inquiry_text_full'],
        'inquiry_text_lang': current_job['inquiry_text_lang'],
        'region': current_job['region'],
        'start_date': current_job['start_date'],
        'shoot_hours': current_job['shoot_hours'],
        'concept_photos': all_concept_photos,
        'models': list(unique_models.values()),
        'num_models': len(unique_models)
    })

print(f"✓ Grouped into {len(jobs_data)} unique jobs ({len(jobs_by_id) - len(jobs_data)} duplicates merged)\n")

# ============================================================================
# GENERATE HTML DASHBOARD
# ============================================================================

print("Generating HTML dashboard...")

html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Visual Dashboard - Concept Photos & Selected Models</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f8f9fa;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .subtitle {
            opacity: 0.9;
            font-size: 16px;
        }
        
        .controls {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .search-box {
            flex: 1;
            min-width: 250px;
        }
        
        .search-box input {
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-badge {
            background: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }
        
        .pagination button {
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .pagination button:hover:not(:disabled) {
            background: #667eea;
            color: white;
        }
        
        .pagination button:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }
        
        .pagination .page-info {
            font-weight: 500;
            color: #666;
        }
        
        .job-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: box-shadow 0.3s;
        }
        
        .job-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .job-header {
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        
        .job-id {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .brand-name {
            font-size: 24px;
            font-weight: 700;
            color: #333;
            margin-bottom: 5px;
        }
        
        .job-name {
            font-size: 18px;
            color: #666;
            margin-bottom: 10px;
        }
        
        .job-meta {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 14px;
            color: #999;
        }
        
        .job-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .inquiry-text {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }
        
        .inquiry-text .label {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .inquiry-text .text {
            color: #555;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        
        .lang-badge {
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin: 25px 0 15px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title::before {
            content: '';
            width: 4px;
            height: 24px;
            background: #667eea;
            border-radius: 2px;
        }
        
        .concept-photos {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .concept-photo {
            position: relative;
            padding-top: 100%;
            background: #f0f0f0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .concept-photo:hover {
            transform: scale(1.05);
        }
        
        .concept-photo img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .no-photos {
            background: #f0f0f0;
            padding: 40px;
            border-radius: 8px;
            text-align: center;
            color: #999;
            font-style: italic;
        }
        
        .models-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }
        
        .model-card {
            background: #fafafa;
            border-radius: 8px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            transition: border-color 0.3s;
        }
        
        .model-card:hover {
            border-color: #667eea;
        }
        
        .model-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .model-headshot {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #667eea;
            flex-shrink: 0;
        }
        
        .model-info {
            flex: 1;
        }
        
        .model-name {
            font-weight: 600;
            font-size: 16px;
            color: #333;
            margin-bottom: 5px;
        }
        
        .model-meta {
            font-size: 13px;
            color: #666;
        }
        
        .model-badge {
            display: inline-block;
            background: #e8eaf6;
            color: #5e35b1;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-top: 5px;
        }
        
        .model-thumbnails {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
        }
        
        .model-thumbnail {
            position: relative;
            padding-top: 133%;
            background: #e0e0e0;
            border-radius: 6px;
            overflow: hidden;
        }
        
        .model-thumbnail img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .no-results {
            text-align: center;
            padding: 60px;
            color: #999;
            font-size: 18px;
        }
        
        @media (max-width: 768px) {
            .concept-photos {
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            }
            
            .models-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Visual Dashboard</h1>
        <div class="subtitle">Concept Photos & Selected Models per Job</div>
    </div>
    
    <div class="stats">
        <div class="stat-badge">
            <div class="stat-number" id="total-jobs">{{ total_jobs }}</div>
            <div class="stat-label">Total Jobs</div>
        </div>
        <div class="stat-badge">
            <div class="stat-number" id="visible-jobs">{{ total_jobs }}</div>
            <div class="stat-label">Showing</div>
        </div>
    </div>
    
    <div class="controls">
        <div class="search-box">
            <input type="text" id="search-input" placeholder="🔍 Search by Job ID, Brand Name, or Job Name...">
        </div>
    </div>
    
    <div class="pagination" id="pagination-top">
        <button id="prev-btn-top">← Previous</button>
        <span class="page-info" id="page-info-top"></span>
        <button id="next-btn-top">Next →</button>
    </div>
    
    <div id="jobs-container"></div>
    
    <div class="pagination" id="pagination-bottom">
        <button id="prev-btn-bottom">← Previous</button>
        <span class="page-info" id="page-info-bottom"></span>
        <button id="next-btn-bottom">Next →</button>
    </div>
    
    <script>
        // Data
        const jobsData = {{ jobs_data_json }};
        
        // State
        let filteredJobs = [...jobsData];
        let currentPage = 1;
        const jobsPerPage = 20;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            renderJobs();
            setupEventListeners();
        });
        
        function setupEventListeners() {
            // Search
            document.getElementById('search-input').addEventListener('input', function(e) {
                const query = e.target.value.toLowerCase();
                filteredJobs = jobsData.filter(job => {
                    return job.job_id.toString().includes(query) ||
                           job.brand_name.toLowerCase().includes(query) ||
                           job.job_name.toLowerCase().includes(query);
                });
                currentPage = 1;
                renderJobs();
            });
            
            // Pagination buttons
            ['top', 'bottom'].forEach(position => {
                document.getElementById(`prev-btn-${position}`).addEventListener('click', () => {
                    if (currentPage > 1) {
                        currentPage--;
                        renderJobs();
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                });
                
                document.getElementById(`next-btn-${position}`).addEventListener('click', () => {
                    const totalPages = Math.ceil(filteredJobs.length / jobsPerPage);
                    if (currentPage < totalPages) {
                        currentPage++;
                        renderJobs();
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                });
            });
        }
        
        function renderJobs() {
            const startIdx = (currentPage - 1) * jobsPerPage;
            const endIdx = startIdx + jobsPerPage;
            const pageJobs = filteredJobs.slice(startIdx, endIdx);
            const totalPages = Math.ceil(filteredJobs.length / jobsPerPage);
            
            // Update stats
            document.getElementById('visible-jobs').textContent = filteredJobs.length;
            
            // Update pagination
            ['top', 'bottom'].forEach(position => {
                const pageInfo = document.getElementById(`page-info-${position}`);
                const prevBtn = document.getElementById(`prev-btn-${position}`);
                const nextBtn = document.getElementById(`next-btn-${position}`);
                
                pageInfo.textContent = `Page ${currentPage} of ${totalPages || 1}`;
                prevBtn.disabled = currentPage === 1;
                nextBtn.disabled = currentPage >= totalPages;
            });
            
            // Render jobs
            const container = document.getElementById('jobs-container');
            
            if (pageJobs.length === 0) {
                container.innerHTML = '<div class="no-results">No jobs found matching your search.</div>';
                return;
            }
            
            container.innerHTML = pageJobs.map(job => `
                <div class="job-card">
                    <div class="job-header">
                        <div class="job-id">Job #${job.job_id}</div>
                        <div class="brand-name">${escapeHtml(job.brand_name)}</div>
                        <div class="job-name">${escapeHtml(job.job_name)}</div>
                        <div class="job-meta">
                            <span>📍 ${job.region}</span>
                            <span>📅 ${job.start_date}</span>
                            <span>⏰ ${job.shoot_hours}h</span>
                            <span>👥 ${job.num_models} model${job.num_models > 1 ? 's' : ''}</span>
                        </div>
                    </div>
                    
                    ${job.inquiry_text ? `
                        <div class="inquiry-text">
                            <div class="label">
                                Inquiry Text
                                <span class="lang-badge">${job.inquiry_text_lang}</span>
                            </div>
                            <div class="text">${escapeHtml(job.inquiry_text)}</div>
                        </div>
                    ` : ''}
                    
                    <div class="section-title">🎨 Concept Photos</div>
                    ${job.concept_photos.length > 0 ? `
                        <div class="concept-photos">
                            ${job.concept_photos.map(url => `
                                <div class="concept-photo">
                                    <img src="${url}" alt="Concept photo" loading="lazy" 
                                         onerror="this.parentElement.style.display='none'">
                                </div>
                            `).join('')}
                        </div>
                    ` : '<div class="no-photos">No concept photos provided</div>'}
                    
                    <div class="section-title">👤 Selected Models (${job.num_models})</div>
                    <div class="models-grid">
                        ${job.models.map(model => `
                            <div class="model-card">
                                <div class="model-header">
                                    ${model.headshot ? `
                                        <img src="${model.headshot}" alt="${model.talent_name}" 
                                             class="model-headshot" loading="lazy"
                                             onerror="this.style.display='none'">
                                    ` : ''}
                                    <div class="model-info">
                                        <div class="model-name">${escapeHtml(model.talent_name)}</div>
                                        <div class="model-meta">
                                            ${model.talent_nationality}
                                        </div>
                                        <span class="model-badge">${model.talent_belong}</span>
                                    </div>
                                </div>
                                ${model.thumbnails.length > 0 ? `
                                    <div class="model-thumbnails">
                                        ${model.thumbnails.map(url => `
                                            <div class="model-thumbnail">
                                                <img src="${url}" alt="${model.talent_name}" loading="lazy"
                                                     onerror="this.parentElement.style.display='none'">
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""

# Prepare data for JavaScript
jobs_json = json.dumps(jobs_data, ensure_ascii=False)

# Render template
template = Template(html_template)
html_output = template.render(
    total_jobs=len(jobs_data),
    jobs_data_json=jobs_json
)

# Save HTML file
output_path = f'{OUTPUT_DIR}/visual_dashboard.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_output)

print(f"✓ Saved: {output_path}")

# ============================================================================
# GENERATE SUMMARY STATISTICS
# ============================================================================

print("\nGenerating summary statistics...")

summary_stats = {
    'total_jobs': len(jobs_data),
    'jobs_with_concept_photos': len([j for j in jobs_data if j['concept_photos']]),
    'jobs_without_concept_photos': len([j for j in jobs_data if not j['concept_photos']]),
    'total_models_selected': sum(j['num_models'] for j in jobs_data),
    'avg_models_per_job': sum(j['num_models'] for j in jobs_data) / len(jobs_data),
    'max_models_in_job': max(j['num_models'] for j in jobs_data),
    'min_models_in_job': min(j['num_models'] for j in jobs_data),
    'jobs_with_inquiry_text': len([j for j in jobs_data if j['inquiry_text']]),
}

# Save statistics
stats_df = pd.DataFrame([summary_stats])
stats_df.to_csv(f'{OUTPUT_DIR}/dashboard_statistics.csv', index=False)
print(f"✓ Saved: {OUTPUT_DIR}/dashboard_statistics.csv")

# ============================================================================
# EXPORT STRUCTURED DATA
# ============================================================================

print("\nExporting structured data...")

# Export job summary
job_summary = []
for job in jobs_data:
    job_summary.append({
        'job_id': job['job_id'],
        'brand_name': job['brand_name'],
        'job_name': job['job_name'],
        'num_concept_photos': len(job['concept_photos']),
        'num_models': job['num_models'],
        'region': job['region'],
        'start_date': job['start_date'],
        'shoot_hours': job['shoot_hours']
    })

pd.DataFrame(job_summary).to_csv(f'{OUTPUT_DIR}/jobs_summary.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/jobs_summary.csv")

# Export model selections
model_selections = []
for job in jobs_data:
    for model in job['models']:
        model_selections.append({
            'job_id': job['job_id'],
            'brand_name': job['brand_name'],
            'booking_id': model['booking_id'],
            'talent_id': model['talent_id'],
            'talent_name': model['talent_name'],
            'talent_nationality': model['talent_nationality'],
            'talent_belong': model['talent_belong'],
            'num_thumbnails': len(model['thumbnails'])
        })

pd.DataFrame(model_selections).to_csv(f'{OUTPUT_DIR}/model_selections.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/model_selections.csv")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("✅ SCRIPT 3 COMPLETE!")
print("="*80 + "\n")

print("📊 Summary:")
print(f"  • Processed {len(jobs_data)} jobs")
print(f"  • Jobs with concept photos: {summary_stats['jobs_with_concept_photos']}")
print(f"  • Jobs without concept photos: {summary_stats['jobs_without_concept_photos']}")
print(f"  • Total models selected: {summary_stats['total_models_selected']}")
print(f"  • Average models per job: {summary_stats['avg_models_per_job']:.1f}")
print(f"\n📁 All outputs saved to: {OUTPUT_DIR}/")
print(f"\n🌐 Open 'visual_dashboard.html' in your browser to view the interactive dashboard!")
print("\nFeatures:")
print("  • 🔍 Search by Job ID, Brand Name, or Job Name")
print("  • 📄 Paginated view (20 jobs per page)")
print("  • 🎨 Concept photos displayed as image gallery")
print("  • 👥 All selected models shown side-by-side")
print("  • 📸 Model headshots and portfolio thumbnails")
print("  • 💬 Inquiry text with language detection")
print("\n" + "="*80 + "\n")
