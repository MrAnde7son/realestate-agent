import { NextResponse } from 'next/server';
import jsPDF from 'jspdf';
import fs from 'fs';
import path from 'path';
import { reports, type Report } from '@/lib/reports';
import { assets } from '@/lib/data';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET(req: Request) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/reports/`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      const backendReports = data.reports || [];
      return NextResponse.json({ reports: [...backendReports, ...reports] });
    }
  } catch (err) {
    console.error('Backend reports fetch failed:', err);
  }
  return NextResponse.json({ reports });
}

export async function DELETE(req: Request) {
  try {
    // Check if request has a body
    const contentType = req.headers.get('content-type');
    let reportId: number | null = null;
    
    if (contentType && contentType.includes('application/json')) {
      try {
        const body = await req.json();
        reportId = body.reportId;
      } catch (err) {
        console.error('Error parsing JSON body:', err);
        return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
      }
    } else {
      // Try to get reportId from URL params as fallback
      const url = new URL(req.url);
      reportId = url.searchParams.get('reportId') ? parseInt(url.searchParams.get('reportId')!) : null;
    }
    
    if (!reportId) {
      return NextResponse.json({ error: 'reportId required' }, { status: 400 });
    }

    console.log('Attempting to delete report:', reportId);

    // Try to connect to backend first
    try {
      const res = await fetch(`${BACKEND_URL}/api/reports/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reportId }),
      });
      
      console.log('Backend delete response status:', res.status);
      
      if (res.ok) {
        const data = await res.json();
        console.log('Backend delete success:', data);
        return NextResponse.json(data, { status: res.status });
      } else {
        // If backend doesn't have the report, try to delete from local reports
        console.log('Backend report not found, trying local deletion');
        const localReportIndex = reports.findIndex(r => r.id === reportId);
        if (localReportIndex !== -1) {
          // Remove from local reports
          const deletedReport = reports.splice(localReportIndex, 1)[0];
          console.log('Deleted local report:', deletedReport);
          return NextResponse.json({ 
            message: `Report ${reportId} deleted successfully from local storage`,
            deletedReport 
          }, { status: 200 });
        } else {
          // Report not found in either backend or local
          return NextResponse.json({ error: 'Report not found' }, { status: 404 });
        }
      }
          } catch (err) {
        console.error('Error connecting to backend for delete:', err);
        // If backend is unavailable, try local deletion
        console.log('Backend unavailable, trying local deletion');
        const localReportIndex = reports.findIndex(r => r.id === reportId);
        if (localReportIndex !== -1) {
          // Remove from local reports
          const deletedReport = reports.splice(localReportIndex, 1)[0];
          console.log('Deleted local report:', deletedReport);
          return NextResponse.json({ 
            message: `Report ${reportId} deleted successfully from local storage`,
            deletedReport 
          }, { status: 200 });
        } else {
          return NextResponse.json({ error: 'Report not found' }, { status: 404 });
        }
      }
  } catch (err) {
    console.error('Error in DELETE handler:', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(req: Request) {
  let assetId: number;
  
  // Parse request first
  try {
    const body = await req.json();
    assetId = Number(body.assetId);
    
    // Validate assetId
    if (!body.assetId || isNaN(assetId) || assetId <= 0) {
      return NextResponse.json({ error: 'Invalid assetId', details: 'assetId must be a positive number' }, { status: 400 });
    }
    
    console.log('Generating report for assetId:', assetId);
  } catch (err) {
    console.error('Error parsing request:', err);
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: 'Invalid request', details: errorMessage }, { status: 400 });
  }

  // Try to connect to backend first
  try {
    console.log('Attempting to connect to backend at:', BACKEND_URL);
    const res = await fetch(`${BACKEND_URL}/api/reports/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId }),
    });
    console.log('Backend response status:', res.status);
    if (res.ok) {
      const data = await res.json();
      console.log('Backend response data:', data);
      return NextResponse.json(data, { status: res.status });
          } else {
        console.error('Backend returned error status:', res.status);
        const errorText = await res.text();
        console.error('Backend error response:', errorText);
        
        // If backend fails, return the error instead of falling back to local generation
        // This ensures we get proper Hebrew support from the backend
        return NextResponse.json({ 
          error: 'Backend report generation failed', 
          details: errorText,
          suggestion: 'Please ensure the backend is running for proper Hebrew support'
        }, { status: res.status });
      }
      } catch (err) {
      console.error('Error connecting to backend:', err);
      // Only fall back to local generation if backend is completely unreachable
      console.log('Backend completely unreachable, falling back to local generation');
    }

  // Generate report locally as fallback
  try {
    console.log('Falling back to local asset data for assetId:', assetId);
    const asset = assets.find(l => l.id === assetId);
    if (!asset) {
      console.error('Asset not found in local data:', assetId);
      return NextResponse.json({ error: 'Asset not found' }, { status: 404 });
    }
    console.log('Found local asset:', asset.address);

    const id = reports.length + 1;
    const filename = `r${id}.pdf`; // Generate PDF reports
    console.log('Current working directory:', process.cwd());
    console.log('Attempting to create directory for reports');
    // Use absolute path to the reports directory
    const dir = '/Users/imizrahi/Documents/Git/realestate-agent/realestate-broker-ui/public/reports';
    console.log('Reports directory path:', dir);
    fs.mkdirSync(dir, { recursive: true });
    const filePath = path.join(dir, filename);
    console.log('File path:', filePath);

    // Create a rich PDF report with multiple pages (one per tab)
    const doc = new jsPDF();
    
    // Page 1: General Analysis
    doc.setFontSize(20);
    doc.text('Asset Report - General Analysis', 105, 30, { align: 'center' });
    
    // Asset Details Section
    doc.setFontSize(14);
    doc.text('Asset Details', 20, 60);
    doc.setFontSize(12);
    let y = 80;
    doc.text(`Address: ${asset.address}`, 20, y); y += 10;
    doc.text(`City: ${asset.city || 'N/A'}`, 20, y); y += 10;
    doc.text(`Neighborhood: ${asset.neighborhood || 'N/A'}`, 20, y); y += 10;
    doc.text(`Type: ${asset.type || 'N/A'}`, 20, y); y += 10;
    doc.text(`Price: ₪${asset.price?.toLocaleString('he-IL') || 'N/A'}`, 20, y); y += 10;
    doc.text(`Bedrooms: ${asset.bedrooms || 'N/A'}`, 20, y); y += 10;
    doc.text(`Bathrooms: ${asset.bathrooms || 'N/A'}`, 20, y); y += 10;
    doc.text(`Area: ${asset.netSqm || asset.area || 'N/A'} sqm`, 20, y); y += 10;
    doc.text(`Price per sqm: ₪${asset.pricePerSqm?.toLocaleString('he-IL') || 'N/A'}`, 20, y); y += 10;
    
    // Financial Analysis Section
    y += 20;
    doc.setFontSize(14);
    doc.text('Financial Analysis', 20, y); y += 15;
    doc.setFontSize(12);
    doc.text(`Model Price: ₪${asset.modelPrice?.toLocaleString('he-IL') || 'N/A'}`, 20, y); y += 10;
    doc.text(`Price Gap: ${asset.priceGapPct || 'N/A'}%`, 20, y); y += 10;
    doc.text(`Rent Estimate: ₪${asset.rentEstimate?.toLocaleString('he-IL') || 'N/A'}`, 20, y); y += 10;
    doc.text(`Annual Return: ${asset.capRatePct || 'N/A'}%`, 20, y); y += 10;
    doc.text(`Competition (1km): ${asset.competition1km || 'N/A'}`, 20, y); y += 10;
    
    // Investment Recommendation
    y += 20;
    doc.setFontSize(14);
    doc.text('Investment Recommendation', 20, y); y += 15;
    doc.setFontSize(12);
    const confidence = asset.confidencePct || 0;
    const capRate = asset.capRatePct || 0;
    const priceGap = asset.priceGapPct || 0;
    const overallScore = Math.round((confidence + (capRate * 20) + (priceGap < 0 ? 100 + priceGap : 100 - priceGap)) / 3);
    doc.text(`Overall Score: ${overallScore}/100`, 20, y); y += 10;
    
    let recommendation = 'Asset at fair market price';
    if (priceGap < -10) {
      recommendation = 'Asset at attractive price below market';
    } else if (priceGap > 10) {
      recommendation = 'Asset expensive relative to market';
    }
    doc.text(`Recommendation: ${recommendation}`, 20, y);
    
    // Page 2: Plans and Rights
    doc.addPage();
    doc.setFontSize(20);
    doc.text('Plans and Building Rights', 105, 30, { align: 'center' });
    
    y = 60;
    doc.setFontSize(14);
    doc.text('Local and Detailed Plans', 20, y); y += 15;
    doc.setFontSize(12);
    doc.text(`Current Plan: ${asset.program || 'N/A'}`, 20, y); y += 10;
    doc.text(`Zoning: ${asset.zoning || 'N/A'}`, 20, y); y += 10;
    doc.text(`Remaining Rights: +${asset.remainingRightsSqm || 'N/A'} sqm`, 20, y); y += 10;
    doc.text(`Main Building Rights: ${asset.netSqm || asset.area || 'N/A'} sqm`, 20, y); y += 10;
    
    y += 20;
    doc.setFontSize(14);
    doc.text('Building Rights Details', 20, y); y += 15;
    doc.setFontSize(12);
    doc.text(`Remaining Rights: ${asset.remainingRightsSqm || 'N/A'} sqm`, 20, y); y += 10;
    const rightsPercentage = asset.remainingRightsSqm && asset.netSqm ? Math.round((asset.remainingRightsSqm / asset.netSqm) * 100) : 0;
    doc.text(`Additional Rights Percentage: ${rightsPercentage}%`, 20, y); y += 10;
    const rightsValue = asset.pricePerSqm && asset.remainingRightsSqm ? Math.round((asset.pricePerSqm * asset.remainingRightsSqm * 0.7) / 1000) : 0;
    doc.text(`Estimated Rights Value: ₪${rightsValue}K`, 20, y);
    
    // Page 3: Environment
    doc.addPage();
    doc.setFontSize(20);
    doc.text('Environmental Information', 105, 30, { align: 'center' });
    
    y = 60;
    doc.setFontSize(14);
    doc.text('Environmental Data', 20, y); y += 15;
    doc.setFontSize(12);
    doc.text(`Noise Level: ${asset.noiseLevel || 'N/A'}/5`, 20, y); y += 10;
    doc.text(`Public Areas ≤300m: Yes`, 20, y); y += 10;
    doc.text(`Antenna Distance: 150m`, 20, y); y += 10;
    
    y += 20;
    doc.setFontSize(14);
    doc.text('Risk Factors', 20, y); y += 15;
    doc.setFontSize(12);
    if (asset.riskFlags && asset.riskFlags.length > 0) {
      asset.riskFlags.forEach(flag => {
        doc.text(`• ${flag}`, 20, y); y += 10;
      });
    } else {
      doc.text('No special risks', 20, y);
    }
    
    // Page 4: Documents and Summary
    doc.addPage();
    doc.setFontSize(20);
    doc.text('Documents and Summary', 105, 30, { align: 'center' });
    
    y = 60;
    doc.setFontSize(14);
    doc.text('Available Documents', 20, y); y += 15;
    doc.setFontSize(12);
    if (asset.documents && asset.documents.length > 0) {
      asset.documents.forEach(doc_item => {
        doc.text(`• ${doc_item.name} (${doc_item.type || 'N/A'})`, 20, y); y += 10;
      });
    } else {
      doc.text('No documents available', 20, y);
    }
    
    // Contact Info
    y += 20;
    doc.setFontSize(14);
    doc.text('Contact Information', 20, y); y += 15;
    doc.setFontSize(12);
    if (asset.contactInfo) {
      doc.text(`Agent: ${asset.contactInfo.agent}`, 20, y); y += 10;
      doc.text(`Phone: ${asset.contactInfo.phone}`, 20, y); y += 10;
      doc.text(`Email: ${asset.contactInfo.email}`, 20, y);
    } else {
      doc.text('N/A', 20, y);
    }
    
    // Footer
    doc.setFontSize(10);
    doc.text(`Report generated on: ${new Date().toLocaleString('he-IL')}`, 105, 280, { align: 'center' });
    
    // Save the PDF
    const pdfBuffer = doc.output('arraybuffer');
    fs.writeFileSync(filePath, Buffer.from(pdfBuffer));

    const report: Report = {
      id,
      assetId,
      address: asset.address,
      filename,
      createdAt: new Date().toISOString(),
    };
    reports.push(report);
    return NextResponse.json({ report }, { status: 201 });
  } catch (err) {
    console.error('Error in local fallback:', err);
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: 'Local report generation failed', details: errorMessage }, { status: 500 });
  }
}
