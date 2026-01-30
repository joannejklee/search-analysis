"""
Script 6: Consolidated PDF Report
Generates a professional PDF report summarizing all analyses
"""

import sys
import subprocess
import os

# Check and install required packages
required_packages = {
    'pandas': 'pandas',
    'matplotlib': 'matplotlib',
    'reportlab': 'reportlab',
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

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
from datetime import datetime
from collections import Counter
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, 
                                TableStyle, PageBreak, Image, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

print("\n" + "="*80)
print("SCRIPT 6: CONSOLIDATED PDF REPORT")
print("="*80 + "\n")

# Configuration
OUTPUT_DIR = "outputs/consolidated_report"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# LOAD ALL DATA
# ============================================================================

print("Loading data from all analyses...\n")

# 1. Bookings data
bookings_df = pd.read_csv("data/2025_Bookings.csv")
print(f"✓ Bookings: {len(bookings_df)} rows, {bookings_df['job_id'].nunique()} unique jobs")

# 2. VOC Analysis
try:
    voc_summary = pd.read_csv("outputs/voc_analysis_revised/voc_summary.csv")
    print(f"✓ VOC Analysis: {len(voc_summary)} themes identified")
    has_voc = True
except:
    print("⚠️  VOC analysis not found")
    has_voc = False

# 3. Vocabulary Analysis
try:
    vocab_translations = pd.read_csv("outputs/vocabulary/vocabulary_with_translations.csv")
    phrase_freq = pd.read_csv("outputs/vocabulary/phrase_frequency.csv")
    job_name_freq = pd.read_csv("outputs/vocabulary/job_name_frequency.csv")
    print(f"✓ Vocabulary Analysis: {len(vocab_translations)} jobs analyzed")
    has_vocab = True
except:
    print("⚠️  Vocabulary analysis not found")
    has_vocab = False

# 4. Keywords Analysis
try:
    keywords_summary = pd.read_csv("outputs/heuristic_keywords/keywords_summary.csv")
    print(f"✓ Keywords: {len(keywords_summary)} jobs with keywords")
    has_keywords = True
except:
    print("⚠️  Keywords analysis not found")
    has_keywords = False

# 5. Dashboard Stats
try:
    dashboard_stats = pd.read_csv("outputs/visual_dashboard/dashboard_statistics.csv")
    print(f"✓ Dashboard Statistics: {len(dashboard_stats)} metrics")
    has_dashboard = True
except:
    print("⚠️  Dashboard statistics not found")
    has_dashboard = False

print()

# ============================================================================
# CALCULATE KEY METRICS
# ============================================================================

print("Calculating key metrics...\n")

# Basic metrics
total_jobs = bookings_df['job_id'].nunique()
total_bookings = len(bookings_df)
total_models = bookings_df['talent_id'].nunique()
total_clients = bookings_df['client_id'].nunique()
total_brands = bookings_df['brand_name'].nunique()

# Region breakdown
region_counts = bookings_df['region'].value_counts()

# Shoot type analysis
shoot_types = []
for types in bookings_df['shoot_types'].dropna():
    shoot_types.extend(str(types).replace('{','').replace('}','').split(','))
shoot_type_counts = Counter([t.strip() for t in shoot_types if t.strip()])

# Monthly trends
bookings_df['start_date'] = pd.to_datetime(bookings_df['start_date_time'], errors='coerce')
bookings_df['month'] = bookings_df['start_date'].dt.to_period('M')
monthly_jobs = bookings_df.groupby('month')['job_id'].nunique()

# Price analysis
avg_price_client = bookings_df['price_client'].mean()
avg_price_talent = bookings_df['price_talent'].mean()

# Nationality breakdown
nationality_counts = bookings_df['talent_nationality'].value_counts().head(10)

print("✓ Metrics calculated\n")

# ============================================================================
# CREATE CHARTS
# ============================================================================

print("Generating charts...\n")

# Chart 1: Monthly Jobs Trend
fig1, ax1 = plt.subplots(figsize=(8, 4))
monthly_jobs.plot(kind='bar', ax=ax1, color='#667eea')
ax1.set_title('Jobs by Month (2025)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Month')
ax1.set_ylabel('Number of Jobs')
ax1.grid(axis='y', alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
chart1_path = f'{OUTPUT_DIR}/chart_monthly_jobs.png'
plt.savefig(chart1_path, dpi=150, bbox_inches='tight')
plt.close()

# Chart 2: Top Regions
fig2, ax2 = plt.subplots(figsize=(8, 4))
region_counts.head(10).plot(kind='barh', ax=ax2, color='#764ba2')
ax2.set_title('Top 10 Regions', fontsize=14, fontweight='bold')
ax2.set_xlabel('Number of Jobs')
ax2.grid(axis='x', alpha=0.3)
plt.tight_layout()
chart2_path = f'{OUTPUT_DIR}/chart_regions.png'
plt.savefig(chart2_path, dpi=150, bbox_inches='tight')
plt.close()

# Chart 3: Top Nationalities
fig3, ax3 = plt.subplots(figsize=(8, 4))
nationality_counts.plot(kind='barh', ax=ax3, color='#e91e63')
ax3.set_title('Top 10 Model Nationalities', fontsize=14, fontweight='bold')
ax3.set_xlabel('Number of Bookings')
ax3.grid(axis='x', alpha=0.3)
plt.tight_layout()
chart3_path = f'{OUTPUT_DIR}/chart_nationalities.png'
plt.savefig(chart3_path, dpi=150, bbox_inches='tight')
plt.close()

# Chart 4: Shoot Types
if shoot_type_counts:
    fig4, ax4 = plt.subplots(figsize=(6, 6))
    types_data = dict(list(shoot_type_counts.items())[:5])
    ax4.pie(types_data.values(), labels=types_data.keys(), autopct='%1.1f%%',
            colors=['#667eea', '#764ba2', '#e91e63', '#26a69a', '#ffa726'])
    ax4.set_title('Shoot Types Distribution', fontsize=14, fontweight='bold')
    plt.tight_layout()
    chart4_path = f'{OUTPUT_DIR}/chart_shoot_types.png'
    plt.savefig(chart4_path, dpi=150, bbox_inches='tight')
    plt.close()

# Chart 5: Top Keywords (if available)
if has_keywords:
    all_job_kw = []
    for kw_str in keywords_summary['job_keywords']:
        if pd.notna(kw_str):
            all_job_kw.extend([k.strip() for k in str(kw_str).split(',') if k.strip()])
    
    if all_job_kw:
        kw_counter = Counter(all_job_kw)
        top_kw = dict(kw_counter.most_common(10))
        
        fig5, ax5 = plt.subplots(figsize=(8, 4))
        plt.barh(list(top_kw.keys()), list(top_kw.values()), color='#26a69a')
        ax5.set_title('Top 10 Concept Keywords', fontsize=14, fontweight='bold')
        ax5.set_xlabel('Frequency')
        ax5.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        chart5_path = f'{OUTPUT_DIR}/chart_keywords.png'
        plt.savefig(chart5_path, dpi=150, bbox_inches='tight')
        plt.close()

print("✓ Charts generated\n")

# ============================================================================
# BUILD PDF REPORT
# ============================================================================

print("Building PDF report...\n")

pdf_path = f'{OUTPUT_DIR}/Consolidated_Report_{datetime.now().strftime("%Y%m%d")}.pdf'
doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                       topMargin=0.75*inch, bottomMargin=0.75*inch,
                       leftMargin=0.75*inch, rightMargin=0.75*inch)

# Styles
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#667eea'),
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

heading1_style = ParagraphStyle(
    'CustomHeading1',
    parent=styles['Heading1'],
    fontSize=16,
    textColor=colors.HexColor('#667eea'),
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold'
)

heading2_style = ParagraphStyle(
    'CustomHeading2',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=colors.HexColor('#764ba2'),
    spaceAfter=10,
    spaceBefore=10,
    fontName='Helvetica-Bold'
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=11,
    spaceAfter=12,
    leading=16
)

# Story (content elements)
story = []

# ============================================================================
# COVER PAGE
# ============================================================================

story.append(Spacer(1, 1.5*inch))
story.append(Paragraph("2025 Booking Analysis", title_style))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("Comprehensive Report", styles['Heading2']))
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", 
                      ParagraphStyle('date', parent=styles['Normal'], alignment=TA_CENTER)))
story.append(Spacer(1, 1*inch))

# Executive summary box
summary_data = [
    ['Total Jobs', str(total_jobs)],
    ['Total Bookings', str(total_bookings)],
    ['Unique Models', str(total_models)],
    ['Unique Clients', str(total_clients)],
    ['Unique Brands', str(total_brands)]
]

summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
summary_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4ff')),
    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 12),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#667eea')),
    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f0f4ff'), colors.white])
]))

story.append(summary_table)
story.append(PageBreak())

# ============================================================================
# SECTION 1: EXECUTIVE SUMMARY
# ============================================================================

story.append(Paragraph("Executive Summary", heading1_style))
story.append(Spacer(1, 0.2*inch))

summary_text = f"""
This comprehensive analysis covers {total_jobs} unique jobs and {total_bookings} total bookings 
processed in 2025. The analysis includes {total_models} unique models from various nationalities, 
working with {total_clients} clients across {total_brands} different brands.
<br/><br/>
The data reveals key trends in booking patterns, model preferences, regional distributions, 
and content themes that can inform strategic decision-making for future bookings and 
talent management.
"""

story.append(Paragraph(summary_text, body_style))
story.append(Spacer(1, 0.3*inch))

# Key Findings
story.append(Paragraph("Key Findings", heading2_style))

findings = [
    f"<b>Busiest Month:</b> {monthly_jobs.idxmax()} with {monthly_jobs.max()} jobs",
    f"<b>Primary Region:</b> {region_counts.index[0]} ({region_counts.iloc[0]} jobs)",
    f"<b>Most Common Nationality:</b> {nationality_counts.index[0]} ({nationality_counts.iloc[0]} bookings)",
    f"<b>Average Client Budget:</b> ₩{avg_price_client:,.0f}",
    f"<b>Average Talent Payment:</b> ₩{avg_price_talent:,.0f}"
]

for finding in findings:
    story.append(Paragraph(f"• {finding}", body_style))
    story.append(Spacer(1, 0.1*inch))

story.append(PageBreak())

# ============================================================================
# SECTION 2: BOOKING TRENDS
# ============================================================================

story.append(Paragraph("Booking Trends & Statistics", heading1_style))
story.append(Spacer(1, 0.2*inch))

# Monthly trends
story.append(Paragraph("Monthly Job Distribution", heading2_style))
story.append(Spacer(1, 0.1*inch))
story.append(Image(chart1_path, width=6*inch, height=3*inch))
story.append(Spacer(1, 0.2*inch))

trend_text = f"""
Job bookings showed varying patterns throughout 2025, with peak activity in 
{monthly_jobs.idxmax()}. The data shows a total of {total_jobs} jobs distributed 
across {len(monthly_jobs)} months.
"""
story.append(Paragraph(trend_text, body_style))
story.append(Spacer(1, 0.3*inch))

# Regional distribution
story.append(Paragraph("Regional Distribution", heading2_style))
story.append(Spacer(1, 0.1*inch))
story.append(Image(chart2_path, width=6*inch, height=3*inch))
story.append(Spacer(1, 0.2*inch))

regional_text = f"""
The platform serves multiple regions, with {region_counts.index[0]} being the dominant market. 
Regional diversity provides opportunities for localized content and targeted marketing strategies.
"""
story.append(Paragraph(regional_text, body_style))

story.append(PageBreak())

# ============================================================================
# SECTION 3: MODEL INSIGHTS
# ============================================================================

story.append(Paragraph("Model & Talent Insights", heading1_style))
story.append(Spacer(1, 0.2*inch))

# Nationality distribution
story.append(Paragraph("Model Nationalities", heading2_style))
story.append(Spacer(1, 0.1*inch))
story.append(Image(chart3_path, width=6*inch, height=3*inch))
story.append(Spacer(1, 0.2*inch))

nationality_text = f"""
The platform features diverse talent from {bookings_df['talent_nationality'].nunique()} different 
nationalities. {nationality_counts.index[0]} models represent the largest group with 
{nationality_counts.iloc[0]} bookings, followed by {nationality_counts.index[1]} with 
{nationality_counts.iloc[1]} bookings.
"""
story.append(Paragraph(nationality_text, body_style))
story.append(Spacer(1, 0.3*inch))

# Top models table
top_models = bookings_df.groupby(['talent_name', 'talent_nationality']).size().reset_index(name='bookings')
top_models = top_models.sort_values('bookings', ascending=False).head(10)

story.append(Paragraph("Top 10 Most Booked Models", heading2_style))
story.append(Spacer(1, 0.1*inch))

model_data = [['Rank', 'Model Name', 'Nationality', 'Bookings']]
for idx, row in top_models.iterrows():
    rank = len(model_data)
    model_data.append([str(rank), row['talent_name'], row['talent_nationality'], str(row['bookings'])])

model_table = Table(model_data, colWidths=[0.6*inch, 2.5*inch, 1.5*inch, 1*inch])
model_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
]))

story.append(model_table)
story.append(PageBreak())

# ============================================================================
# SECTION 4: CONTENT ANALYSIS
# ============================================================================

story.append(Paragraph("Content & Project Analysis", heading1_style))
story.append(Spacer(1, 0.2*inch))

# Shoot types
if shoot_type_counts:
    story.append(Paragraph("Shoot Type Distribution", heading2_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Image(chart4_path, width=5*inch, height=5*inch))
    story.append(Spacer(1, 0.2*inch))

# Top job names
if has_vocab:
    story.append(Paragraph("Most Common Project Types", heading2_style))
    story.append(Spacer(1, 0.1*inch))
    
    job_data = [['Rank', 'Job Type (Korean)', 'English Translation', 'Count']]
    for idx, row in job_name_freq.head(10).iterrows():
        korean_name = str(row['Job Name (Korean)']) if pd.notna(row['Job Name (Korean)']) else ''
        english_name = str(row['English Translation']) if pd.notna(row['English Translation']) else ''
        job_data.append([
            str(idx + 1),
            korean_name[:30],
            english_name[:30],
            str(row['Frequency'])
        ])
    
    job_table = Table(job_data, colWidths=[0.6*inch, 2*inch, 2*inch, 0.8*inch])
    job_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
    ]))
    
    story.append(job_table)
    story.append(Spacer(1, 0.3*inch))

story.append(PageBreak())

# ============================================================================
# SECTION 5: KEYWORD INSIGHTS
# ============================================================================

if has_keywords:
    story.append(Paragraph("Keyword & Theme Analysis", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Concept keywords
    story.append(Paragraph("Top Concept Keywords", heading2_style))
    story.append(Spacer(1, 0.1*inch))
    
    if os.path.exists(f'{OUTPUT_DIR}/chart_keywords.png'):
        story.append(Image(f'{OUTPUT_DIR}/chart_keywords.png', width=6*inch, height=3*inch))
        story.append(Spacer(1, 0.2*inch))
    
    keyword_text = f"""
    Keyword analysis reveals the most common concepts and themes across all projects. 
    Photography-based projects dominate, with strong representation of beauty, fashion, 
    and commercial content. These insights help identify market trends and popular content categories.
    """
    story.append(Paragraph(keyword_text, body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Model keywords
    all_model_kw = []
    for kw_str in keywords_summary['model_keywords']:
        if pd.notna(kw_str):
            all_model_kw.extend([k.strip() for k in str(kw_str).split(',') if k.strip()])
    
    if all_model_kw:
        model_kw_counter = Counter(all_model_kw)
        top_model_kw = model_kw_counter.most_common(10)
        
        story.append(Paragraph("Top Model Attributes", heading2_style))
        story.append(Spacer(1, 0.1*inch))
        
        kw_data = [['Rank', 'Attribute', 'Frequency']]
        for idx, (kw, count) in enumerate(top_model_kw, 1):
            kw_data.append([str(idx), kw, str(count)])
        
        kw_table = Table(kw_data, colWidths=[0.8*inch, 3*inch, 1.2*inch])
        kw_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e91e63')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        
        story.append(kw_table)
    
    story.append(PageBreak())

# ============================================================================
# SECTION 6: VOC INSIGHTS
# ============================================================================

if has_voc:
    story.append(Paragraph("Voice of Customer Analysis", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    voc_text = f"""
    Analysis of customer feedback identified {len(voc_summary)} major themes from both clients 
    and models. These themes provide valuable insights into user experiences, pain points, 
    and satisfaction drivers.
    """
    story.append(Paragraph(voc_text, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Key Themes", heading2_style))
    story.append(Spacer(1, 0.1*inch))
    
    voc_data = [['Theme', 'Feedback Count', 'User Types']]
    for idx, row in voc_summary.head(10).iterrows():
        theme_name = str(row['Theme']) if pd.notna(row['Theme']) else 'Unknown'
        voc_data.append([
            theme_name[:40],
            str(row['Count']),
            'Mixed' if 'Both' in str(row) else 'Single'
        ])
    
    voc_table = Table(voc_data, colWidths=[3*inch, 1.2*inch, 1.2*inch])
    voc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#26a69a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
    ]))
    
    story.append(voc_table)
    story.append(PageBreak())

# ============================================================================
# SECTION 7: RECOMMENDATIONS
# ============================================================================

story.append(Paragraph("Strategic Recommendations", heading1_style))
story.append(Spacer(1, 0.2*inch))

recommendations = [
    ("<b>Talent Diversification:</b>", 
     f"With {nationality_counts.index[0]} models dominating ({nationality_counts.iloc[0]} bookings), "
     "consider expanding recruitment efforts in underrepresented nationalities to meet growing demand for diverse casting."),
    
    ("<b>Peak Period Planning:</b>", 
     f"The busiest month ({monthly_jobs.idxmax()}) saw {monthly_jobs.max()} jobs. Plan capacity and resource "
     "allocation accordingly for similar high-volume periods."),
    
    ("<b>Regional Expansion:</b>", 
     f"Strong concentration in {region_counts.index[0]} presents opportunity for geographic expansion "
     "to capture new markets and reduce regional dependency."),
    
    ("<b>Content Optimization:</b>", 
     "Photography-based projects are dominant. Develop specialized workflows and talent pools "
     "optimized for photo shoots to maximize efficiency."),
    
    ("<b>Model Development:</b>", 
     "Top-performing models drive significant repeat bookings. Invest in developing relationships "
     "with high-potential models and create incentive programs for consistent performers.")
]

for title, detail in recommendations:
    story.append(Paragraph(f"{title} {detail}", body_style))
    story.append(Spacer(1, 0.15*inch))

story.append(Spacer(1, 0.3*inch))

# ============================================================================
# FOOTER
# ============================================================================

story.append(PageBreak())
story.append(Spacer(1, 2*inch))
story.append(Paragraph("Data Sources & Methodology", heading2_style))
story.append(Spacer(1, 0.1*inch))

methodology_text = """
This report synthesizes data from multiple analysis modules:
<br/><br/>
• <b>Booking Data:</b> 2025_Bookings.csv containing job, model, and client information<br/>
• <b>VOC Analysis:</b> Thematic analysis of customer feedback<br/>
• <b>Vocabulary Analysis:</b> Text mining of inquiry content and project descriptions<br/>
• <b>Keyword Extraction:</b> Heuristic analysis of project concepts and model attributes<br/>
• <b>Visual Dashboard:</b> Interactive exploration platform for detailed job inspection<br/>
<br/>
All analyses were conducted using privacy-safe methodologies with no external data sharing.
Charts and tables were generated using Python (pandas, matplotlib) and compiled using ReportLab.
"""

story.append(Paragraph(methodology_text, body_style))
story.append(Spacer(1, 0.5*inch))

footer_text = f"""
<para align=center>
<font size=9 color="#999999">
Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
Confidential - For Internal Use Only
</font>
</para>
"""
story.append(Paragraph(footer_text, body_style))

# ============================================================================
# BUILD PDF
# ============================================================================

print("Compiling PDF document...")
doc.build(story)

print(f"✓ PDF report saved: {pdf_path}\n")

# ============================================================================
# SUMMARY
# ============================================================================

print("="*80)
print("✅ CONSOLIDATED REPORT COMPLETE!")
print("="*80 + "\n")

print(f"📄 PDF Report: {pdf_path}")
print(f"📊 Charts generated: {len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')])}")
print(f"📁 Output directory: {OUTPUT_DIR}/")

print("\n" + "="*80 + "\n")
