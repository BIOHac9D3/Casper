#!/usr/bin/env node
'use strict';

const { spawnSync } = require('node:child_process');
const { existsSync } = require('node:fs');
const { join } = require('node:path');

const root = __dirname;
const cliPath = join(root, 'cli.py');

if (!existsSync(cliPath)) {
  console.error('casper-node error: cli.py not found.');
  process.exit(1);
}

const args = process.argv.slice(2);
const py = process.env.PYTHON_BIN || 'python3';

const result = spawnSync(py, [cliPath, ...args], {
  cwd: root,
  stdio: 'inherit',
  env: process.env,
});

if (result.error) {
  console.error(`casper-node error: failed to execute ${py}.`);
  console.error('Tip: install Python 3.11+ and run `pip install -r requirements.txt`.');
  process.exit(1);
}

process.exit(result.status ?? 1);
