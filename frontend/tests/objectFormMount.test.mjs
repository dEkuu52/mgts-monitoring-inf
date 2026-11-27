import assert from 'node:assert/strict'
import test from 'node:test'
import { readFile } from 'node:fs/promises'
import { compileScript, parse } from '@vue/compiler-sfc'
import { transform } from 'esbuild'
import * as vue from 'vue'

const frontendRoot = new URL('../', import.meta.url)

async function compileObjectForm(mocks) {
  const source = await readFile(new URL('pages/admin/objects/action.vue', frontendRoot), 'utf8')
  const { descriptor, errors } = parse(source, { filename: 'objects-action.vue' })
  assert.deepEqual(errors, [])

  let code = compileScript(descriptor, { id: 'objects-action-mount-test', inlineTemplate: true }).content
  code = code.replace(/^import \{([^}]+)\} from ['"]vue['"];?\s*$/gm, (_match, bindings) => {
    const destructure = bindings.replace(/\s+as\s+/g, ': ')
    return `const { ${destructure} } = __vue`
  })
  code = code.replace(/^import \{([^}]+)\} from ['"](?:#vue-router|~\/services\/useRequest|~\/composables\/useNotifications)['"];?\s*$/gm, (_match, bindings) => {
    return `const { ${bindings} } = __mocks`
  })
  code = `const { computed, ref, onMounted, onBeforeUnmount } = __vue\nconst { useRouter, definePageMeta } = __mocks\n${code}`

  const compiled = await transform(code, { loader: 'ts', format: 'cjs' })
  const module = { exports: {} }
  new Function('module', 'exports', '__vue', '__mocks', compiled.code)(module, module.exports, vue, mocks)
  return module.exports.default
}

function makeRenderer() {
  const body = { type: 'body', children: [] }

  function insert(node, parent, anchor = null) {
    if (node.parent) remove(node)
    const children = parent.children ||= []
    const index = anchor ? children.indexOf(anchor) : -1
    if (index < 0) children.push(node)
    else children.splice(index, 0, node)
    node.parent = parent
  }

  function remove(node) {
    if (!node.parent) return
    const children = node.parent.children || []
    const index = children.indexOf(node)
    if (index >= 0) children.splice(index, 1)
    node.parent = null
  }

  return vue.createRenderer({
    createElement: type => ({ type, props: {}, children: [] }),
    createText: text => ({ type: '#text', text }),
    createComment: text => ({ type: '#comment', text }),
    setText: (node, text) => { node.text = text },
    setElementText: (node, text) => { node.children = [{ type: '#text', text, parent: node }] },
    patchProp: (node, key, _previous, next) => { node.props[key] = next },
    insert,
    remove,
    parentNode: node => node.parent,
    nextSibling: node => {
      const siblings = node.parent?.children || []
      return siblings[siblings.indexOf(node) + 1] || null
    },
    querySelector: selector => selector === 'body' ? body : null,
    insertStaticContent(content, parent, anchor) {
      const node = { type: '#static', text: content, children: [] }
      insert(node, parent, anchor)
      return [node, node]
    },
  })
}

function textContent(node) {
  return `${node.text || ''}${(node.children || []).map(textContent).join('')}`
}

function findNode(node, predicate) {
  if (predicate(node)) return node
  for (const child of node.children || []) {
    const match = findNode(child, predicate)
    if (match) return match
  }
  return null
}

async function mountObjectForm(query) {
  const requests = []
  const route = { query }
  const object = {
    id: 42,
    type: 'Опора освещения',
    external_id: 'EXT-42',
    place: 'ул. Примерная',
    lat: 55.7,
    lon: 37.6,
    status_id: 7,
  }
  const mocks = {
    definePageMeta() {},
    useRoute: () => route,
    useRouter: () => ({ push: async () => {}, replace: async () => {} }),
    useNotifications: () => ({ error() {}, success() {} }),
    useRequest: async (path) => {
      requests.push(path)
      if (path === '/api/statuses') return { data: [{ id: 7, type: 'Исправен' }] }
      if (path === '/api/infrastructure-objects/42') return { data: object }
      return { data: null }
    },
  }
  const component = await compileObjectForm(mocks)
  const renderer = makeRenderer()
  const app = renderer.createApp(component)
  const h = vue.h

  app.component('Toolbar', { setup: (_props, { slots }) => () => h('div', {}, [slots.start?.(), slots.end?.()]) })
  app.component('Button', { props: ['label'], setup: (props, { slots }) => () => h('button', {}, props.label || slots.default?.()) })
  app.component('Message', { setup: (_props, { slots }) => () => h('div', {}, slots.default?.()) })
  app.component('InputText', {
    props: ['id', 'modelValue', 'placeholder'],
    setup: props => () => h('input', { id: props.id, value: props.modelValue, placeholder: props.placeholder }),
  })
  app.component('Select', {
    props: ['inputId', 'modelValue'],
    setup: props => () => h('select', { id: props.inputId, value: props.modelValue }),
  })
  app.component('Image', { props: ['src', 'alt'], setup: props => () => h('img', { src: props.src, alt: props.alt }) })
  app.component('Tag', { props: ['value'], setup: props => () => h('span', {}, props.value) })

  const root = { type: 'root', children: [] }
  const previousWindow = globalThis.window
  globalThis.window = { addEventListener() {}, removeEventListener() {} }
  const restoreWindow = () => {
    if (previousWindow === undefined) delete globalThis.window
    else globalThis.window = previousWindow
  }
  try {
    app.mount(root)
    await new Promise(resolve => setImmediate(resolve))
    await vue.nextTick()
    return { app, root, requests, object, restoreWindow }
  } catch (error) {
    app.unmount()
    restoreWindow()
    throw error
  }
}

test('object create and edit forms mount and load their route data', async () => {
  const create = await mountObjectForm({})
  assert.match(textContent(create.root), /Добавить объект/)
  assert.deepEqual(create.requests, ['/api/statuses'])
  assert.ok(findNode(create.root, node => node.type === 'select' && node.props.id === 'object-status'))
  create.app.unmount()
  create.restoreWindow()

  const edit = await mountObjectForm({ id: '42' })
  assert.match(textContent(edit.root), /Объект №42/)
  assert.deepEqual(edit.requests, ['/api/statuses', '/api/infrastructure-objects/42'])
  assert.equal(findNode(edit.root, node => node.type === 'input' && node.props.id === 'object-type')?.props.value, 'Опора освещения')
  assert.equal(findNode(edit.root, node => node.type === 'input' && node.props.id === 'object-external-id')?.props.value, 'EXT-42')
  edit.app.unmount()
  edit.restoreWindow()
})
