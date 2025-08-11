#!/usr/bin/env node
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createMcpServer, connectServer, setupGracefulShutdown, logEnvironmentInfo } from './src/server.js';

async function main() {
  try {
    // לוג מידע על הסביבה
    logEnvironmentInfo();
    
    // יצירת השרת עם כל הכלים
    const mcp = createMcpServer({
      name: "data-gov-il-js",
      version: "1.2.0",
      description: "MCP server for data.gov.il with advanced search capabilities"
    });
    
    // הגדרת טיפול נקי בסגירה
    setupGracefulShutdown(mcp);
    
    // חיבור ל-stdio transport
    const transport = new StdioServerTransport();
    await connectServer(mcp, transport);
    
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// הפעלת השרת
main().catch((error) => {
  console.error('❌ Server startup error:', error);
  process.exit(1);
});