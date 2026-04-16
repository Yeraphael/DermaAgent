#!/usr/bin/env node
const fs = require('fs')
const path = require('path')
const { spawnSync } = require('child_process')

const MOBILE_USER_DIR = path.join(__dirname, 'apps/mobile-user')
const OUTPUT_DIR = path.join(MOBILE_USER_DIR, 'dist/build/mp-weixin')
const MANIFEST_PATH = path.join(MOBILE_USER_DIR, 'manifest.json')
const PROJECT_CONFIG_PATH = path.join(OUTPUT_DIR, 'project.config.json')
const PRIVATE_CONFIG_PATH = path.join(OUTPUT_DIR, 'project.private.config.json')
const H5_ENTRY_PATH = path.join(MOBILE_USER_DIR, 'index.html')
const H5_ENTRY_BACKUP_PATH = path.join(MOBILE_USER_DIR, '.index.html.h5-backup')
const uniBin = path.join(__dirname, 'node_modules/@dcloudio/vite-plugin-uni/bin/uni.js')
const args = process.argv.slice(2)

function ensureCleanOutput(cliArgs) {
  if (cliArgs[0] === 'build') {
    try {
      fs.rmSync(OUTPUT_DIR, { recursive: true, force: true })
    } catch (error) {
      if (error.code !== 'EBUSY' && error.code !== 'EPERM') {
        throw error
      }
      console.warn(`[uni-build-helper] Skip cleaning locked output directory: ${OUTPUT_DIR}`)
    }
  }
}

function resolveAppId() {
  try {
    const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'))
    const appid = manifest?.appid
    if (typeof appid === 'string' && appid.trim() && !appid.startsWith('__UNI__')) {
      return appid.trim()
    }
  } catch (error) {
    console.warn('[uni-build-helper] Unable to read manifest.json:', error.message)
  }
  return 'touristappid'
}

function writeWeChatProjectConfig() {
  if (!fs.existsSync(path.join(OUTPUT_DIR, 'app.json'))) {
    throw new Error('uni build did not generate app.json in dist/build/mp-weixin')
  }

  const projectConfig = {
    appid: resolveAppId(),
    projectname: 'DermaAgent',
    compileType: 'miniprogram',
    miniprogramRoot: './',
    srcMiniprogramRoot: './',
    setting: {
      es6: true,
      enhance: true,
      postcss: true,
      minified: true,
      urlCheck: false,
      minifyWXSS: true,
      minifyWXML: true,
      compileHotReLoad: false
    }
  }

  const privateConfig = {
    projectname: 'DermaAgent',
    compileType: 'miniprogram',
    setting: {
      urlCheck: false
    }
  }

  fs.mkdirSync(OUTPUT_DIR, { recursive: true })
  fs.writeFileSync(PROJECT_CONFIG_PATH, `${JSON.stringify(projectConfig, null, 2)}\n`)
  fs.writeFileSync(PRIVATE_CONFIG_PATH, `${JSON.stringify(privateConfig, null, 2)}\n`)

  const legacyHtmlPath = path.join(OUTPUT_DIR, 'index.html')
  if (fs.existsSync(legacyHtmlPath)) {
    try {
      fs.rmSync(legacyHtmlPath, { force: true })
    } catch (error) {
      if (error.code !== 'EBUSY' && error.code !== 'EPERM') {
        throw error
      }
      console.warn(`[uni-build-helper] Skip removing locked legacy file: ${legacyHtmlPath}`)
    }
  }
}

function shouldHideH5Entry(cliArgs) {
  return cliArgs.includes('mp-weixin')
}

function hideH5Entry() {
  if (!shouldHideH5Entry(args) || !fs.existsSync(H5_ENTRY_PATH)) {
    return () => {}
  }

  if (fs.existsSync(H5_ENTRY_BACKUP_PATH)) {
    fs.rmSync(H5_ENTRY_BACKUP_PATH, { force: true })
  }

  fs.renameSync(H5_ENTRY_PATH, H5_ENTRY_BACKUP_PATH)

  return () => {
    if (!fs.existsSync(H5_ENTRY_BACKUP_PATH)) {
      return
    }
    if (fs.existsSync(H5_ENTRY_PATH)) {
      fs.rmSync(H5_ENTRY_PATH, { force: true })
    }
    fs.renameSync(H5_ENTRY_BACKUP_PATH, H5_ENTRY_PATH)
  }
}

ensureCleanOutput(args)
const restoreH5Entry = hideH5Entry()

try {
  const result = spawnSync(process.execPath, [uniBin, ...args], {
    stdio: 'inherit',
    cwd: MOBILE_USER_DIR,
    env: {
      ...process.env,
      UNI_INPUT_DIR: MOBILE_USER_DIR,
      UNI_OUTPUT_DIR: OUTPUT_DIR
    }
  })

  if (result.status !== 0) {
    process.exit(result.status || 1)
  }

  if (args[0] === 'build') {
    writeWeChatProjectConfig()
  }
} finally {
  restoreH5Entry()
}
