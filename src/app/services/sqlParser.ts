interface ParseResponse {
  sql: string;
  explanation: string;
}

/**
 * Simple API client to call backend parser
 */
export async function parseNaturalLanguageToSQL(
  naturalLanguage: string
): Promise<ParseResponse> {
  try {
    const response = await fetch('/api/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ naturalLanguage })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      sql: data.sql || "",
      explanation: data.explanation || "Generated SQL query"
    };
  } catch (error) {
    console.error('Parser error:', error);
    throw error;
  }
}
