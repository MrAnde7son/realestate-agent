#!/usr/bin/env node

/**
 * Component Validation Script
 * Checks for missing UI components before development
 */

const fs = require('fs');
const path = require('path');

const UI_COMPONENTS_DIR = path.join(__dirname, '../realestate-broker-ui/components/ui');
const COMPONENTS_DIR = path.join(__dirname, '../realestate-broker-ui/components');

function getAvailableComponents() {
  const files = fs.readdirSync(UI_COMPONENTS_DIR);
  return files
    .filter(file => file.endsWith('.tsx') && !file.includes('.test.'))
    .map(file => file.replace('.tsx', ''))
    .map(name => {
      // Handle both PascalCase and camelCase
      const pascalCase = name.charAt(0).toUpperCase() + name.slice(1);
      const camelCase = name.charAt(0).toLowerCase() + name.slice(1);
      return [pascalCase, camelCase];
    })
    .flat();
}

function findComponentImports(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const importRegex = /import.*from\s+['"]@\/components\/ui\/([^'"]+)['"]/g;
  const imports = [];
  let match;
  
  while ((match = importRegex.exec(content)) !== null) {
    imports.push(match[1]);
  }
  
  return imports;
}

function validateComponents() {
  const availableComponents = getAvailableComponents();
  console.log('Available UI components:', availableComponents);
  
  // Find all component files
  const componentFiles = [];
  function walkDir(dir) {
    const files = fs.readdirSync(dir);
    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      if (stat.isDirectory()) {
        walkDir(filePath);
      } else if (file.endsWith('.tsx') && !file.includes('.test.')) {
        componentFiles.push(filePath);
      }
    });
  }
  
  walkDir(COMPONENTS_DIR);
  
  let hasErrors = false;
  
  componentFiles.forEach(file => {
    const imports = findComponentImports(file);
    imports.forEach(importName => {
      if (!availableComponents.includes(importName)) {
        console.error(`❌ Missing component: ${importName} in ${file}`);
        hasErrors = true;
      }
    });
  });
  
  if (!hasErrors) {
    console.log('✅ All component imports are valid');
  }
  
  return !hasErrors;
}

if (require.main === module) {
  const isValid = validateComponents();
  process.exit(isValid ? 0 : 1);
}

module.exports = { validateComponents, getAvailableComponents };
