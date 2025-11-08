import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

const DISALLOWED_PATTERNS = [
  /@tabler\/icons-react/,
  /tabler-icons-react/
]

const ALLOWED_EXTENSIONS = new Set([
  '.ts',
  '.tsx',
  '.js',
  '.jsx',
  '.mjs',
  '.cjs',
  '.json'
])

const IGNORED_DIRECTORIES = new Set([
  'node_modules',
  '.next',
  '.turbo',
  'coverage',
  '.git'
])

function shouldInspectFile(filePath: string): boolean {
  return ALLOWED_EXTENSIONS.has(path.extname(filePath))
}

function collectFiles(directory: string): string[] {
  const entries = fs.readdirSync(directory, { withFileTypes: true })
  const files: string[] = []

  for (const entry of entries) {
    if (IGNORED_DIRECTORIES.has(entry.name)) {
      continue
    }

    const entryPath = path.join(directory, entry.name)

    if (entry.isDirectory()) {
      files.push(...collectFiles(entryPath))
    } else if (entry.isFile() && shouldInspectFile(entryPath)) {
      files.push(entryPath)
    }
  }

  return files
}

describe('icon usage', () => {
  it('does not include Tabler icon imports', () => {
    const projectRoot = path.join(__dirname, '..')
    const testFilePath = __filename
    const filesToCheck = collectFiles(projectRoot).filter(
      (filePath) => filePath !== testFilePath
    )

    const violations: Array<{ file: string; pattern: RegExp }> = []

    for (const filePath of filesToCheck) {
      const content = fs.readFileSync(filePath, 'utf8')

      for (const pattern of DISALLOWED_PATTERNS) {
        if (pattern.test(content)) {
          violations.push({ file: path.relative(projectRoot, filePath), pattern })
        }
      }
    }

    if (violations.length > 0) {
      const formattedViolations = violations
        .map(({ file, pattern }) => `${file} (matched ${pattern})`)
        .join('\n')
      throw new Error(`Found ${violations.length} violation(s):\n${formattedViolations}`)
    }

    expect(violations).toHaveLength(0)
  })
})
