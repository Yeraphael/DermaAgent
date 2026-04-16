const path = require('path')
const { defineConfig } = require('vite')

const vueModule = require('@vitejs/plugin-vue')
const uniModule = require('@dcloudio/vite-plugin-uni')

function resolveFactory(moduleValue, packageName) {
  const factory = typeof moduleValue === 'function' ? moduleValue : moduleValue?.default
  if (typeof factory !== 'function') {
    throw new Error(`${packageName} did not expose a callable plugin factory`)
  }
  return factory
}

function isUniBuild() {
  return (
    process.argv.includes('uni') ||
    process.argv.includes('mp-weixin') ||
    Boolean(process.env.UNI_PLATFORM) ||
    Boolean(process.env.UNI_INPUT_DIR) ||
    Boolean(process.env.UNI_OUTPUT_DIR)
  )
}

const vue = resolveFactory(vueModule, '@vitejs/plugin-vue')
const uni = resolveFactory(uniModule, '@dcloudio/vite-plugin-uni')

module.exports = defineConfig(() => {
  if (isUniBuild()) {
    return {
      appType: 'custom',
      build: {
        rollupOptions: {
          input: path.resolve(__dirname, 'main.ts'),
        },
      },
      plugins: [uni()],
      server: {
        host: '127.0.0.1',
        port: 5174,
      },
    }
  }

  return {
    plugins: [vue()],
    server: {
      host: '127.0.0.1',
      port: 5174,
    },
  }
})
