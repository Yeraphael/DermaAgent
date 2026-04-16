#!/usr/bin/env node
// 强制 uni-app CLI 读取当前目录（而非默认的 src/）
process.env.UNI_INPUT_DIR = process.cwd()
process.env.UNI_OUTPUT_DIR = process.env.UNI_OUTPUT_DIR || (process.cwd() + '/dist/build/mp-weixin')
// 确保 Node 可以找到 monorepo root 的 node_modules
const path = require('path')
const Module = require('module')
const originalResolve = Module._resolveFilename
Module._resolveFilename = function(request, parent, isMain, options) {
  if (request.startsWith('@dcloudio/') || request === '@dcloudio/uni-cli-shared') {
    // 从 monorepo root 解析
    try {
      return originalResolve.call(this, request, {
        id: path.join(__dirname, 'node_modules/@dcloudio/vite-plugin-uni/package.json'),
        filename: path.join(__dirname, 'node_modules/@dcloudio/vite-plugin-uni/package.json'),
        paths: [path.join(__dirname, 'node_modules')]
      }, isMain)
    } catch {}
  }
  return originalResolve.call(this, request, parent, isMain, options)
}
require('@dcloudio/vite-plugin-uni/bin/uni.js')
