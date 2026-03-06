import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
  try {
    const { naturalLanguage } = await request.json();

    if (!naturalLanguage || typeof naturalLanguage !== 'string') {
      return NextResponse.json(
        { error: 'Invalid input: naturalLanguage is required' },
        { status: 400 }
      );
    }

    // Path to Python script
    const pythonScript = path.join(process.cwd(), 'python', 'parser.py');

    // Execute Python script with natural language input
    const { stdout, stderr } = await execAsync(
      `python "${pythonScript}" "${naturalLanguage.replace(/"/g, '\\"')}"`,
      { 
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer
        timeout: 30000 // 30 second timeout
      }
    );

    if (stderr) {
      console.error('Python stderr:', stderr);
      return NextResponse.json(
        { error: 'Python script error: ' + stderr },
        { status: 500 }
      );
    }

    // Parse JSON output from Python
    const result = JSON.parse(stdout);

    return NextResponse.json(result);
  } catch (error: any) {
    console.error('API error:', error);
    return NextResponse.json(
      { 
        error: error.message || 'Failed to parse natural language to SQL',
        details: error.toString()
      },
      { status: 500 }
    );
  }
}
