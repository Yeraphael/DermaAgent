const { spawn } = require('node:child_process')
const path = require('node:path')

const bin = path.resolve(__dirname, '../node_modules/@esbuild/win32-x64/esbuild.exe')

const mode = process.argv[2] || 'direct'
const command = mode === 'cmd' ? 'cmd.exe' : bin
const args = mode === 'cmd' ? ['/c', bin, '--version'] : ['--version']

const child = spawn(command, args, {
  windowsHide: true,
  stdio: ['ignore', 'pipe', 'pipe'],
})

child.stdout.on('data', (chunk) => {
  process.stdout.write(chunk)
})

child.stderr.on('data', (chunk) => {
  process.stderr.write(chunk)
})

child.on('error', (error) => {
  console.error('SPAWN_ERROR', error)
  process.exit(1)
})

child.on('close', (code) => {
  console.log(`EXIT_CODE=${code}`)
  process.exit(code ?? 0)
})
