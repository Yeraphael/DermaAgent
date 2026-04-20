#!/usr/bin/env node
const fs = require('fs')
const path = require('path')
const { spawnSync } = require('child_process')

const APP_DIR = __dirname
const INDEX_PATH = path.join(APP_DIR, 'index.html')
const BACKUP_PATH = path.join(APP_DIR, '.index.html.h5-backup')
const [command = 'dev', ...extraArgs] = process.argv.slice(2)

function resolveViteBin() {
  try {
    return require.resolve('vite/bin/vite.js', { paths: [APP_DIR] })
  } catch {
    return path.join(APP_DIR, '..', '..', 'node_modules', 'vite', 'bin', 'vite.js')
  }
}

function ensureH5Entry() {
  if (fs.existsSync(INDEX_PATH)) {
    return
  }

  if (!fs.existsSync(BACKUP_PATH)) {
    throw new Error(`Missing H5 entry file: ${INDEX_PATH}`)
  }

  fs.copyFileSync(BACKUP_PATH, INDEX_PATH)
  console.warn('[h5-entry-helper] Restored apps/mobile-user/index.html from .index.html.h5-backup')
}

function createH5Env() {
  const env = { ...process.env }

  Object.keys(env).forEach((key) => {
    if (key.startsWith('UNI_') || key === 'VITE_ROOT_DIR' || key === 'VITE_USER_NODE_ENV') {
      delete env[key]
    }
  })

  return env
}

function createViteArgs() {
  const viteArgs = [command]

  if (
    command === 'build' &&
    !extraArgs.includes('--outDir') &&
    !extraArgs.includes('--emptyOutDir')
  ) {
    // Keep H5 artifacts isolated from the mp-weixin output directory.
    viteArgs.push('--outDir', 'dist/h5', '--emptyOutDir', 'false')
  }

  return [...viteArgs, ...extraArgs]
}

const viteBin = resolveViteBin()
ensureH5Entry()

const result = spawnSync(process.execPath, [viteBin, ...createViteArgs()], {
  cwd: APP_DIR,
  env: createH5Env(),
  stdio: 'inherit',
})

if (result.error) {
  throw result.error
}

process.exit(result.status ?? 1)
